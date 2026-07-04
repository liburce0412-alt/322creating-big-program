"""
pomodoro_routes.py —— 番茄钟 API
谢佳杨 负责

接口：
  POST /api/pomodoro/complete  — 完成一次番茄钟（加经验 + 触发成就检测）
  GET  /api/pomodoro/history   — 获取番茄钟历史记录
  GET  /api/pomodoro/stats     — 番茄钟统计数据
"""
from flask import Blueprint, request, jsonify, g
from auth import login_required, add_exp
from models import get_db
from config import EXP_PER_POMODORO, BADGES
from datetime import datetime, timedelta

pomodoro_bp = Blueprint("pomodoro", __name__)


def check_and_unlock_achievements(user_id: int, db) -> list:
    """
    检查并解锁新成就，返回本次新解锁的成就列表。
    在每次番茄钟完成、时间记录添加等操作后调用。
    """
    newly_unlocked = []

    # 统计用户各项数据
    pomo_count = db.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (user_id,)
    ).fetchone()["cnt"]

    record_count = db.execute(
        "SELECT COUNT(*) as cnt FROM time_records WHERE user_id = ?",
        (user_id,)
    ).fetchone()["cnt"]

    user = db.execute("SELECT level FROM users WHERE id = ?", (user_id,)).fetchone()
    current_level = user["level"] if user else 1

    ai_report_count = db.execute(
        "SELECT COUNT(*) as cnt FROM ai_reports WHERE user_id = ?",
        (user_id,)
    ).fetchone()["cnt"]

    # 检查连续打卡天数
    streak = _calculate_streak(user_id, db)

    # 成就检测规则
    rules = {
        "first_pomodoro": pomo_count >= 1,
        "ten_pomodoros": pomo_count >= 10,
        "fifty_pomodoros": pomo_count >= 50,
        "first_record": record_count >= 1,
        "ten_records": record_count >= 10,
        "level_5": current_level >= 5,
        "level_10": current_level >= 10,
        "ai_first": ai_report_count >= 1,
        "three_day_streak": streak >= 3,
        "seven_day_streak": streak >= 7,
    }

    for badge_id, condition in rules.items():
        if not condition:
            continue
        # 检查是否已解锁
        existing = db.execute(
            "SELECT id FROM achievements WHERE user_id = ? AND badge_id = ?",
            (user_id, badge_id)
        ).fetchone()
        if existing:
            continue
        # 解锁新成就！
        db.execute(
            "INSERT INTO achievements (user_id, badge_id) VALUES (?, ?)",
            (user_id, badge_id)
        )
        badge_info = BADGES.get(badge_id, {"name": badge_id, "icon": "🎖️", "description": ""})
        newly_unlocked.append({
            "badge_id": badge_id,
            "name": badge_info["name"],
            "icon": badge_info["icon"],
            "description": badge_info["description"]
        })

    if newly_unlocked:
        db.commit()
    return newly_unlocked


def _calculate_streak(user_id: int, db) -> int:
    """计算连续使用天数（从今天往回数）"""
    today = datetime.now().strftime("%Y-%m-%d")
    streak = 0
    for i in range(365):  # 最多回溯一年
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        has_activity = db.execute(
            """SELECT COUNT(*) as cnt FROM pomodoro_sessions
               WHERE user_id = ? AND date(completed_at) = ?""",
            (user_id, day)
        ).fetchone()["cnt"]
        if has_activity > 0:
            streak += 1
        elif i > 0:  # 今天可以没有记录，但从昨天开始必须连续
            break
        # i == 0 (今天) 没有记录不打断 streak 的计算起点
    return streak


# ==================== API 接口 ====================

@pomodoro_bp.route("/pomodoro/complete", methods=["POST"])
@login_required
def complete_pomodoro():
    """
    完成一次番茄钟

    请求体 JSON：
        { "duration_min": 25 }

    返回：
        {
            "session_id": 123,
            "exp_gained": 50,
            "level_up": false,
            "new_level": 3,
            "new_exp": 100,
            "new_achievements": [...]
        }
    """
    data = request.get_json(silent=True) or {}
    duration = data.get("duration_min", 25)

    # 验证时长
    if duration not in [25, 50, 90]:
        return jsonify({"error": "无效的番茄钟时长，支持 25/50/90 分钟"}), 400

    db = get_db()

    # 记录番茄钟会话
    db.execute(
        "INSERT INTO pomodoro_sessions (user_id, duration_min, exp_gained) VALUES (?, ?, ?)",
        (g.user_id, duration, EXP_PER_POMODORO)
    )
    session_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.commit()

    # 加经验值
    exp_result = add_exp(g.user_id, EXP_PER_POMODORO)

    # 检测成就
    new_achievements = check_and_unlock_achievements(g.user_id, db)

    db.commit()
    db.close()

    return jsonify({
        "session_id": session_id,
        "duration_min": duration,
        "exp_gained": EXP_PER_POMODORO,
        "level_up": exp_result["level_up"],
        "new_level": exp_result["new_level"],
        "new_exp": exp_result["exp"],
        "new_achievements": new_achievements
    }), 201


@pomodoro_bp.route("/pomodoro/history", methods=["GET"])
@login_required
def get_pomodoro_history():
    """
    获取番茄钟历史记录

    查询参数：
        ?page=1&limit=20

    返回：
        {
            "total": 50,
            "page": 1,
            "sessions": [...]
        }
    """
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    offset = (page - 1) * limit

    db = get_db()

    total = db.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    sessions = db.execute(
        """SELECT id, duration_min, exp_gained, completed_at
           FROM pomodoro_sessions
           WHERE user_id = ?
           ORDER BY completed_at DESC
           LIMIT ? OFFSET ?""",
        (g.user_id, limit, offset)
    ).fetchall()

    db.close()

    return jsonify({
        "total": total,
        "page": page,
        "limit": limit,
        "sessions": [dict(s) for s in sessions]
    })


@pomodoro_bp.route("/pomodoro/stats", methods=["GET"])
@login_required
def get_pomodoro_stats():
    """
    获取番茄钟统计数据

    返回：
        {
            "total_sessions": 42,
            "total_minutes": 1050,
            "today_sessions": 3,
            "today_minutes": 75,
            "streak_days": 5,
            "weekly_sessions": [{"date":"...","count":3}, ...]
        }
    """
    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    # 总计
    total_sessions = db.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    total_minutes = db.execute(
        "SELECT COALESCE(SUM(duration_min), 0) as total FROM pomodoro_sessions WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["total"]

    # 今日
    today_sessions = db.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = ?",
        (g.user_id, today)
    ).fetchone()["cnt"]

    today_minutes = db.execute(
        "SELECT COALESCE(SUM(duration_min), 0) as total FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = ?",
        (g.user_id, today)
    ).fetchone()["total"]

    # 连续打卡天数
    streak = _calculate_streak(g.user_id, db)

    # 最近 7 天每日统计
    weekly = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        count = db.execute(
            "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = ?",
            (g.user_id, day)
        ).fetchone()["cnt"]
        weekly.append({"date": day, "count": count})

    db.close()

    return jsonify({
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "today_sessions": today_sessions,
        "today_minutes": today_minutes,
        "streak_days": streak,
        "weekly_sessions": weekly
    })
