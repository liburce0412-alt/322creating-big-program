# pomodoro_routes.py — 番茄钟 API 路由
# 负责：POST /api/pomodoro/complete（核心：加经验值 + 解锁勋章）
#       GET  /api/pomodoro/history（历史记录）

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from models import (
    get_db, calculate_exp, calculate_level,
    check_achievements, get_user_pomodoro_count,
    get_user_achievements, ACHIEVEMENT_DEFINITIONS
)

pomodoro_bp = Blueprint('pomodoro', __name__)


# ============================================================
# 辅助：从请求中获取当前用户（依赖 auth.py 的 JWT 中间件设置 g.user_id）
# ============================================================

def _get_current_user_id():
    """
    获取当前登录用户的 ID。
    依赖 auth.py 中的 @login_required 装饰器在 g.user_id 中设置。
    如果 auth 模块尚未实现，则从 Authorization header 手动解析。
    """
    # 优先从 Flask g 对象获取（auth 中间件设置的）
    if hasattr(g, 'user_id') and g.user_id:
        return g.user_id

    # 退化：直接从 header 解析 JWT payload（临时方案）
    import jwt
    import config
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            return payload.get('user_id')
        except Exception:
            return None
    return None


# ============================================================
# POST /api/pomodoro/complete — 完成番茄钟
# ============================================================




# ---- 辅助函数（由 achievement_routes 和 time_routes 调用）----

def check_and_unlock_achievements(user_id: int, db) -> list:
    """检查并解锁新成就，返回本次新解锁的成就列表"""
    newly_unlocked = []
    from config import BADGES

    pomo_count = db.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (user_id,)
    ).fetchone()["cnt"]

    record_count = db.execute(
        "SELECT COUNT(*) as cnt FROM time_records WHERE user_id = ?",
        (user_id,)
    ).fetchone()["cnt"]

    level_row = db.execute(
        "SELECT level FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    level = level_row["level"] if level_row else 1

    achievements_to_check = {
        "first_pomodoro": pomo_count >= 1,
        "ten_pomodoros": pomo_count >= 10,
        "fifty_pomodoros": pomo_count >= 50,
        "first_record": record_count >= 1,
        "ten_records": record_count >= 10,
    }
    # Level-based achievements
    if level >= 5:  achievements_to_check["level_5"] = True
    if level >= 10: achievements_to_check["level_10"] = True
    # Streak achievements (check streak first)
    if _calculate_streak(user_id, db) >= 3:  achievements_to_check["three_day_streak"] = True
    if _calculate_streak(user_id, db) >= 7:  achievements_to_check["seven_day_streak"] = True

    for badge_id, unlocked in achievements_to_check.items():
        if unlocked and badge_id in BADGES:
            existing = db.execute(
                "SELECT id FROM achievements WHERE user_id = ? AND badge_id = ?",
                (user_id, badge_id)
            ).fetchone()
            if not existing:
                db.execute(
                    "INSERT INTO achievements (user_id, badge_id) VALUES (?, ?)",
                    (user_id, badge_id)
                )
                from config import BADGES as B
                badge_info = B.get(badge_id, {"name": badge_id, "icon": "\U0001f3c6"})
                newly_unlocked.append({
                    "badge_id": badge_id,
                    "name": badge_info["name"],
                    "icon": badge_info["icon"],
                    "description": badge_info.get("description", "")
                })

    return newly_unlocked


def _calculate_streak(user_id: int, db) -> int:
    """计算连续使用天数（从今天往回数）"""
    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    streak = 0
    for i in range(365):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = ?",
            (user_id, day)
        ).fetchone()
        cnt = row["cnt"] if row else 0
        if cnt > 0:
            streak += 1
        else:
            break
    return streak


@pomodoro_bp.route('/api/pomodoro/complete', methods=['POST'])
def complete_pomodoro():
    """
    完成一个番茄钟，记录并发放经验和成就。

    请求体 (JSON):
        {
            "duration_min": 25   // 番茄钟时长（分钟）
        }

    响应 (JSON):
        {
            "status": "ok",
            "session_id": 1,
            "exp_gained": 25,
            "total_exp": 125,
            "level_up": false,
            "current_level": 2,
            "exp_to_next": 275,
            "new_achievements": [
                {
                    "badge_id": "first_pomodoro",
                    "name": "初次专注",
                    "description": "完成第1次番茄钟",
                    "icon": "🍅"
                }
            ]
        }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    data = request.get_json(silent=True) or {}
    duration_min = data.get('duration_min', 0)

    # 参数校验
    if not isinstance(duration_min, (int, float)) or duration_min <= 0:
        return jsonify({'status': 'error', 'message': '请提供有效的 duration_min（分钟数）'}), 400

    duration_min = int(duration_min)

    # 记录番茄钟会话
    db.execute(
        "INSERT INTO pomodoro_sessions (user_id, duration_min, exp_gained) VALUES (?, ?, ?)",
        (g.user_id, duration, EXP_PER_POMODORO)
    )
    session_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.commit()

    try:
        # 1. 计算本次番茄钟获得的经验值
        exp_gained = calculate_exp(duration_min)

        # 2. 写入 pomodoro_sessions 表
        cursor.execute(
            "INSERT INTO pomodoro_sessions (user_id, duration_min, exp_gained) VALUES (?, ?, ?)",
            (user_id, duration_min, exp_gained)
        )
        session_id = cursor.lastrowid

        # 3. 更新用户经验值
        cursor.execute("UPDATE users SET exp = exp + ? WHERE id = ?", (exp_gained, user_id))

        # 4. 重新计算等级
        user = cursor.execute("SELECT exp, level FROM users WHERE id = ?", (user_id,)).fetchone()
        old_level = user['level']
        new_level = calculate_level(user['exp'])

        level_up = new_level > old_level
        if level_up:
            cursor.execute("UPDATE users SET level = ? WHERE id = ?", (new_level, user_id))

        conn.commit()

        # 5. 检查并解锁新成就
        new_achievements = check_achievements(user_id, conn)

        # 6. 重新读取用户最终状态
        user = cursor.execute("SELECT exp, level FROM users WHERE id = ?", (user_id,)).fetchone()
        exp_to_next = (user['level']) * (user['level']) * 100 - user['exp']

        return jsonify({
            'status': 'ok',
            'session_id': session_id,
            'exp_gained': exp_gained,
            'total_exp': user['exp'],
            'level_up': level_up,
            'current_level': user['level'],
            'exp_to_next': max(0, exp_to_next),
            'new_achievements': new_achievements,
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500
    finally:
        conn.close()


# ============================================================
# GET /api/pomodoro/history — 番茄钟历史
# ============================================================

@pomodoro_bp.route('/api/pomodoro/history', methods=['GET'])
def pomodoro_history():
    """
    获取当前用户的番茄钟历史记录。

    查询参数:
        limit  — 返回条数（默认 20）
        offset — 偏移量（默认 0）

    响应:
        {
            "status": "ok",
            "total": 42,
            "sessions": [
                {
                    "id": 1,
                    "duration_min": 25,
                    "exp_gained": 25,
                    "completed_at": "2025-07-05 14:30:00"
                },
                ...
            ]
        }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    # 参数安全限制
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    conn = get_db()
    cursor = conn.cursor()

    try:
        total = cursor.execute(
            "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
            (user_id,)
        ).fetchone()['cnt']

        rows = cursor.execute(
            "SELECT id, duration_min, exp_gained, completed_at "
            "FROM pomodoro_sessions WHERE user_id = ? "
            "ORDER BY completed_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        ).fetchall()

        sessions = [dict(row) for row in rows]

        return jsonify({
            'status': 'ok',
            'total': total,
            'limit': limit,
            'offset': offset,
            'sessions': sessions,
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()


# ============================================================
# GET /api/user/achievements — 获取用户已解锁成就
# ============================================================

@pomodoro_bp.route('/api/user/achievements', methods=['GET'])
def user_achievements():
    """
    获取当前用户的所有已解锁成就 + 全部成就列表（含未解锁状态）。

    响应:
        {
            "status": "ok",
            "unlocked_count": 3,
            "total_count": 13,
            "achievements": [
                {
                    "badge_id": "first_pomodoro",
                    "name": "初次专注",
                    "description": "完成第1次番茄钟",
                    "icon": "🍅",
                    "unlocked": true,
                    "unlocked_at": "2025-07-05 14:30:00"
                },
                {
                    "badge_id": "pomodoro_5",
                    "name": "专注新手",
                    "description": "累计完成5次番茄钟",
                    "icon": "⭐",
                    "unlocked": false,
                    "unlocked_at": null
                },
                ...
            ]
        }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    conn = get_db()

    try:
        unlocked = get_user_achievements(user_id, conn)
        unlocked_ids = {a['badge_id'] for a in unlocked}
        unlocked_map = {a['badge_id']: a['unlocked_at'] for a in unlocked}

        # 构建完整成就列表（含未解锁的）
        all_achievements = []
        for badge_id, definition in ACHIEVEMENT_DEFINITIONS.items():
            all_achievements.append({
                'badge_id': badge_id,
                'name': definition['name'],
                'description': definition['description'],
                'icon': definition['icon'],
                'unlocked': badge_id in unlocked_ids,
                'unlocked_at': unlocked_map.get(badge_id, None),
            })

        return jsonify({
            'status': 'ok',
            'unlocked_count': len(unlocked),
            'total_count': len(ACHIEVEMENT_DEFINITIONS),
            'achievements': all_achievements,
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()
