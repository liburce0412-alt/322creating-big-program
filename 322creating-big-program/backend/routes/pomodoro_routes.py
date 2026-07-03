"""
番茄钟 API 路由 — 丁超轶
提供番茄钟的启动、暂停、恢复、完成、统计等功能
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify, g
from models import get_connection
from auth import login_required

pomodoro_bp = Blueprint('pomodoro', __name__)

# 默认配置
DEFAULT_WORK = 25       # 分钟
DEFAULT_SHORT_BREAK = 5
DEFAULT_LONG_BREAK = 15
LONG_BREAK_INTERVAL = 4


# ==================== 番茄钟 CRUD ====================

@pomodoro_bp.route('/start', methods=['POST'])
@login_required
def start_pomodoro():
    """开始一个新的番茄钟"""
    data = request.get_json() or {}
    task_name = data.get('task_name', '未命名任务')
    work_duration = data.get('work_duration', DEFAULT_WORK)
    break_duration = data.get('break_duration', DEFAULT_SHORT_BREAK)

    conn = get_connection()

    # 检查是否有正在进行的番茄钟
    active = conn.execute(
        'SELECT id FROM pomodoro_sessions WHERE user_id=? AND status IN ("running","paused")',
        (g.current_user_id,)
    ).fetchone()
    if active:
        conn.close()
        return jsonify({'code': 400, 'message': '已有进行中的番茄钟，请先完成或放弃'})

    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        '''INSERT INTO pomodoro_sessions
           (user_id, task_name, work_duration, break_duration, status, started_at)
           VALUES (?,?,?,?,'running',?)''',
        (g.current_user_id, task_name, work_duration, break_duration, now)
    )
    session_id = cursor.lastrowid
    conn.commit()

    # 获取今日已完成数，判断是否长休息
    today_count = conn.execute(
        'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed" AND date(completed_at)=?',
        (g.current_user_id, date.today().isoformat())
    ).fetchone()['cnt']

    suggested_break = DEFAULT_LONG_BREAK if (today_count + 1) % LONG_BREAK_INTERVAL == 0 else break_duration

    session = {
        'id': session_id,
        'task_name': task_name,
        'work_duration': work_duration,
        'break_duration': suggested_break,
        'status': 'running',
        'started_at': now,
    }
    conn.close()
    return jsonify({'code': 200, 'message': '番茄钟已开始', 'data': session})


@pomodoro_bp.route('/pause/<int:session_id>', methods=['POST'])
@login_required
def pause_pomodoro(session_id):
    """暂停番茄钟"""
    conn = get_connection()
    session = conn.execute(
        'SELECT * FROM pomodoro_sessions WHERE id=? AND user_id=?',
        (session_id, g.current_user_id)
    ).fetchone()

    if not session:
        conn.close()
        return jsonify({'code': 404, 'message': '番茄钟不存在'})
    if session['status'] != 'running':
        conn.close()
        return jsonify({'code': 400, 'message': f'当前状态为 {session["status"]}，无法暂停'})

    now = datetime.utcnow().isoformat()
    started = datetime.fromisoformat(session['started_at'])
    focus_seconds = int((datetime.utcnow() - started).total_seconds())

    conn.execute(
        'UPDATE pomodoro_sessions SET status="paused", paused_at=?, total_focus_seconds=total_focus_seconds+? WHERE id=?',
        (now, focus_seconds, session_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'message': '番茄钟已暂停', 'data': {'paused_at': now, 'focus_seconds': focus_seconds}})


@pomodoro_bp.route('/resume/<int:session_id>', methods=['POST'])
@login_required
def resume_pomodoro(session_id):
    """恢复番茄钟"""
    conn = get_connection()
    session = conn.execute(
        'SELECT * FROM pomodoro_sessions WHERE id=? AND user_id=?',
        (session_id, g.current_user_id)
    ).fetchone()

    if not session:
        conn.close()
        return jsonify({'code': 404, 'message': '番茄钟不存在'})
    if session['status'] != 'paused':
        conn.close()
        return jsonify({'code': 400, 'message': f'当前状态为 {session["status"]}，无法恢复'})

    now = datetime.utcnow().isoformat()
    conn.execute(
        'UPDATE pomodoro_sessions SET status="running", started_at=? WHERE id=?',
        (now, session_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'message': '番茄钟已恢复', 'data': {'resumed_at': now}})


@pomodoro_bp.route('/complete/<int:session_id>', methods=['POST'])
@login_required
def complete_pomodoro(session_id):
    """完成番茄钟"""
    conn = get_connection()
    session = conn.execute(
        'SELECT * FROM pomodoro_sessions WHERE id=? AND user_id=?',
        (session_id, g.current_user_id)
    ).fetchone()

    if not session:
        conn.close()
        return jsonify({'code': 404, 'message': '番茄钟不存在'})
    if session['status'] not in ('running', 'paused'):
        conn.close()
        return jsonify({'code': 400, 'message': f'番茄钟已结束，无需重复完成'})

    now = datetime.utcnow().isoformat()
    conn.execute(
        'UPDATE pomodoro_sessions SET status="completed", completed_at=? WHERE id=?',
        (now, session_id)
    )

    # 自动创建一条时间记录
    conn.execute(
        '''INSERT INTO time_records (user_id, category, description, start_time, end_time, duration_minutes)
           VALUES (?,?,?,?,?,?)''',
        (g.current_user_id, '番茄钟', session['task_name'],
         session['started_at'], now, session['work_duration'])
    )

    conn.commit()
    conn.close()

    # 检查是否解锁新成就
    _check_pomodoro_achievements(g.current_user_id)

    return jsonify({
        'code': 200,
        'message': '番茄钟已完成！休息一下吧 🎉',
        'data': {'completed_at': now, 'work_duration': session['work_duration']}
    })


@pomodoro_bp.route('/abandon/<int:session_id>', methods=['POST'])
@login_required
def abandon_pomodoro(session_id):
    """放弃番茄钟"""
    conn = get_connection()
    session = conn.execute(
        'SELECT * FROM pomodoro_sessions WHERE id=? AND user_id=?',
        (session_id, g.current_user_id)
    ).fetchone()

    if not session:
        conn.close()
        return jsonify({'code': 404, 'message': '番茄钟不存在'})

    conn.execute(
        'UPDATE pomodoro_sessions SET status="abandoned" WHERE id=?',
        (session_id,)
    )
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'message': '番茄钟已放弃'})


# ==================== 番茄钟查询 ====================

@pomodoro_bp.route('/current', methods=['GET'])
@login_required
def current_session():
    """获取当前进行中的番茄钟"""
    conn = get_connection()
    session = conn.execute(
        'SELECT * FROM pomodoro_sessions WHERE user_id=? AND status IN ("running","paused") ORDER BY id DESC LIMIT 1',
        (g.current_user_id,)
    ).fetchone()
    conn.close()

    if not session:
        return jsonify({'code': 200, 'data': None, 'message': '当前无进行中的番茄钟'})

    return jsonify({'code': 200, 'data': dict(session)})


@pomodoro_bp.route('/list', methods=['GET'])
@login_required
def list_sessions():
    """获取番茄钟历史列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')  # 可选筛选: completed, abandoned, running, paused
    offset = (page - 1) * per_page

    conn = get_connection()
    where_clause = 'WHERE user_id=?'
    params = [g.current_user_id]
    if status:
        where_clause += ' AND status=?'
        params.append(status)

    total = conn.execute(
        f'SELECT COUNT(*) as cnt FROM pomodoro_sessions {where_clause}', params
    ).fetchone()['cnt']

    sessions = conn.execute(
        f'SELECT * FROM pomodoro_sessions {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'list': [dict(s) for s in sessions],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        }
    })


@pomodoro_bp.route('/stats', methods=['GET'])
@login_required
def pomodoro_stats():
    """番茄钟统计数据"""
    conn = get_connection()

    user_id = g.current_user_id

    # 总完成数
    total_completed = conn.execute(
        'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed"',
        (user_id,)
    ).fetchone()['cnt']

    # 今日完成数
    today_completed = conn.execute(
        'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed" AND date(completed_at)=?',
        (user_id, date.today().isoformat())
    ).fetchone()['cnt']

    # 本周完成数
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_completed = conn.execute(
        'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed" AND date(completed_at)>=?',
        (user_id, week_start.isoformat())
    ).fetchone()['cnt']

    # 总专注时间（秒）
    total_focus = conn.execute(
        'SELECT COALESCE(SUM(total_focus_seconds),0) as total FROM pomodoro_sessions WHERE user_id=? AND status="completed"',
        (user_id,)
    ).fetchone()['total']

    # 连续打卡天数
    streak = _calculate_streak(conn, user_id)

    # 每日完成趋势（近 7 天）
    daily_trend = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        cnt = conn.execute(
            'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed" AND date(completed_at)=?',
            (user_id, d.isoformat())
        ).fetchone()['cnt']
        daily_trend.append({'date': d.isoformat(), 'count': cnt})

    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'total_completed': total_completed,
            'today_completed': today_completed,
            'week_completed': week_completed,
            'total_focus_seconds': total_focus,
            'total_focus_hours': round(total_focus / 3600, 1),
            'current_streak_days': streak,
            'daily_trend': daily_trend,
        }
    })


@pomodoro_bp.route('/settings', methods=['GET', 'PUT'])
@login_required
def pomodoro_settings():
    """获取/更新番茄钟设置（存储在用户配置中，简化版用返回值）"""
    if request.method == 'GET':
        return jsonify({
            'code': 200,
            'data': {
                'work_duration': DEFAULT_WORK,
                'short_break_duration': DEFAULT_SHORT_BREAK,
                'long_break_duration': DEFAULT_LONG_BREAK,
                'long_break_interval': LONG_BREAK_INTERVAL,
            }
        })
    else:
        # PUT: 目前仅返回成功（完整实现应持久化到用户配置表）
        return jsonify({'code': 200, 'message': '设置已更新（当前版本使用默认值）'})


# ==================== 辅助函数 ====================

def _calculate_streak(conn, user_id) -> int:
    """计算连续打卡天数"""
    rows = conn.execute(
        '''SELECT DISTINCT date(completed_at) as d
           FROM pomodoro_sessions
           WHERE user_id=? AND status="completed"
           ORDER BY d DESC LIMIT 60''',
        (user_id,)
    ).fetchall()

    if not rows:
        return 0

    streak = 0
    today = date.today()
    expected = today

    for row in rows:
        d = date.fromisoformat(row['d'])
        if d == expected:
            streak += 1
            expected = d - timedelta(days=1)
        elif d < expected:
            break

    return streak


def _check_pomodoro_achievements(user_id: int):
    """检查并解锁番茄钟相关成就"""
    conn = get_connection()

    # 获取已完成番茄钟数
    completed_count = conn.execute(
        'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed"',
        (user_id,)
    ).fetchone()['cnt']

    # 获取所有番茄钟类成就
    achievements = conn.execute(
        "SELECT * FROM achievements WHERE category IN ('pomodoro','streak','special')"
    ).fetchall()

    for ach in achievements:
        # 检查是否已解锁
        existing = conn.execute(
            'SELECT id FROM user_achievements WHERE user_id=? AND achievement_id=?',
            (user_id, ach['id'])
        ).fetchone()
        if existing:
            continue

        unlocked = False
        if ach['code'] == 'first_pomodoro' and completed_count >= 1:
            unlocked = True
        elif ach['code'] == 'pomodoro_10' and completed_count >= 10:
            unlocked = True
        elif ach['code'] == 'pomodoro_50' and completed_count >= 50:
            unlocked = True
        elif ach['code'] == 'pomodoro_100' and completed_count >= 100:
            unlocked = True
        elif ach['code'] == 'early_bird':
            # 检查是否在早上6点前完成过番茄钟
            early = conn.execute(
                '''SELECT id FROM pomodoro_sessions
                   WHERE user_id=? AND status="completed"
                   AND time(completed_at) < "06:00:00" LIMIT 1''',
                (user_id,)
            ).fetchone()
            unlocked = early is not None
        elif ach['condition_type'] == 'streak':
            streak = _calculate_streak(conn, user_id)
            if ach['code'] == 'streak_3' and streak >= 3:
                unlocked = True
            elif ach['code'] == 'streak_7' and streak >= 7:
                unlocked = True
            elif ach['code'] == 'streak_30' and streak >= 30:
                unlocked = True

        if unlocked:
            conn.execute(
                'INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?,?)',
                (user_id, ach['id'])
            )

    conn.commit()
    conn.close()
