"""
成就系统 API 路由 — 丁超轶
提供成就列表、用户成就、成就检查等功能
"""
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, g
from models import get_connection
from auth import login_required

achievement_bp = Blueprint('achievement', __name__)


@achievement_bp.route('/list', methods=['GET'])
@login_required
def list_achievements():
    """获取所有成就定义 + 当前用户的解锁状态"""
    category = request.args.get('category', '')  # 可选筛选

    conn = get_connection()

    where = ''
    params = []
    if category:
        where = 'WHERE category=?'
        params = [category]

    achievements = conn.execute(
        f'SELECT * FROM achievements {where} ORDER BY category, id', params
    ).fetchall()

    # 获取用户已解锁的成就 ID
    user_ach_set = set()
    user_achs = conn.execute(
        'SELECT achievement_id, earned_at FROM user_achievements WHERE user_id=?',
        (g.current_user_id,)
    ).fetchall()
    for ua in user_achs:
        user_ach_set.add((ua['achievement_id'], ua['earned_at']))

    result = []
    for ach in achievements:
        earned_at = None
        for ach_id, ea in user_ach_set:
            if ach_id == ach['id']:
                earned_at = ea
                break
        d = dict(ach)
        d['unlocked'] = earned_at is not None
        d['earned_at'] = earned_at
        result.append(d)

    conn.close()

    # 按类别分组
    grouped = {}
    for item in result:
        cat = item['category']
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(item)

    return jsonify({
        'code': 200,
        'data': {
            'list': result,
            'grouped': grouped,
            'total': len(result),
            'unlocked_count': sum(1 for r in result if r['unlocked']),
        }
    })


@achievement_bp.route('/user', methods=['GET'])
@login_required
def user_achievements():
    """获取当前用户已解锁的成就"""
    conn = get_connection()

    user_achs = conn.execute(
        '''SELECT a.*, ua.earned_at
           FROM user_achievements ua
           JOIN achievements a ON a.id = ua.achievement_id
           WHERE ua.user_id = ?
           ORDER BY ua.earned_at DESC''',
        (g.current_user_id,)
    ).fetchall()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'list': [dict(a) for a in user_achs],
            'count': len(user_achs),
        }
    })


@achievement_bp.route('/check', methods=['POST'])
@login_required
def check_achievements():
    """手动触发成就检查（全面扫描）"""
    conn = get_connection()

    newly_unlocked = []

    # 1. 番茄钟类成就
    completed_pomodoros = conn.execute(
        'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed"',
        (g.current_user_id,)
    ).fetchone()['cnt']

    # 2. 时间记录成就
    total_minutes = conn.execute(
        'SELECT COALESCE(SUM(duration_minutes),0) as total FROM time_records WHERE user_id=?',
        (g.current_user_id,)
    ).fetchone()['total']
    total_hours = total_minutes / 60

    # 3. 连续打卡天数
    streak_rows = conn.execute(
        '''SELECT DISTINCT date(completed_at) as d
           FROM pomodoro_sessions
           WHERE user_id=? AND status="completed"
           ORDER BY d DESC LIMIT 60''',
        (g.current_user_id,)
    ).fetchall()
    streak = 0
    expected = date.today()
    for row in streak_rows:
        d = date.fromisoformat(row['d'])
        if d == expected:
            streak += 1
            expected = d - timedelta(days=1)
        elif d < expected:
            break

    # 4. AI 报告数
    ai_reports_count = conn.execute(
        'SELECT COUNT(*) as cnt FROM ai_reports WHERE user_id=?',
        (g.current_user_id,)
    ).fetchone()['cnt']

    # 检查成就条件
    all_achievements = conn.execute('SELECT * FROM achievements').fetchall()
    for ach in all_achievements:
        existing = conn.execute(
            'SELECT id FROM user_achievements WHERE user_id=? AND achievement_id=?',
            (g.current_user_id, ach['id'])
        ).fetchone()
        if existing:
            continue

        unlocked = False
        code = ach['code']

        # 番茄钟数量
        if code == 'first_pomodoro' and completed_pomodoros >= 1:
            unlocked = True
        elif code == 'pomodoro_10' and completed_pomodoros >= 10:
            unlocked = True
        elif code == 'pomodoro_50' and completed_pomodoros >= 50:
            unlocked = True
        elif code == 'pomodoro_100' and completed_pomodoros >= 100:
            unlocked = True

        # 连续天数
        elif code == 'streak_3' and streak >= 3:
            unlocked = True
        elif code == 'streak_7' and streak >= 7:
            unlocked = True
        elif code == 'streak_30' and streak >= 30:
            unlocked = True

        # 学习时间
        elif code == 'record_10h' and total_hours >= 10:
            unlocked = True
        elif code == 'record_50h' and total_hours >= 50:
            unlocked = True

        # AI
        elif code == 'first_ai_report' and ai_reports_count >= 1:
            unlocked = True

        # 早起鸟
        elif code == 'early_bird':
            early = conn.execute(
                '''SELECT id FROM pomodoro_sessions
                   WHERE user_id=? AND status="completed"
                   AND time(completed_at) < "06:00:00" LIMIT 1''',
                (g.current_user_id,)
            ).fetchone()
            unlocked = early is not None

        if unlocked:
            conn.execute(
                'INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?,?)',
                (g.current_user_id, ach['id'])
            )
            newly_unlocked.append({
                'id': ach['id'],
                'code': ach['code'],
                'name': ach['name'],
                'icon': ach['icon'],
                'description': ach['description'],
            })

    conn.commit()
    conn.close()

    return jsonify({
        'code': 200,
        'message': f'检查完成，新解锁 {len(newly_unlocked)} 个成就',
        'data': {
            'newly_unlocked': newly_unlocked,
            'current_stats': {
                'completed_pomodoros': completed_pomodoros,
                'total_hours': round(total_hours, 1),
                'streak_days': streak,
                'ai_reports': ai_reports_count,
            }
        }
    })


@achievement_bp.route('/stats', methods=['GET'])
@login_required
def achievement_stats():
    """成就总体统计"""
    conn = get_connection()

    total_achievements = conn.execute('SELECT COUNT(*) as cnt FROM achievements').fetchone()['cnt']
    unlocked_count = conn.execute(
        'SELECT COUNT(*) as cnt FROM user_achievements WHERE user_id=?',
        (g.current_user_id,)
    ).fetchone()['cnt']

    # 最近解锁的成就
    recent = conn.execute(
        '''SELECT a.*, ua.earned_at
           FROM user_achievements ua
           JOIN achievements a ON a.id = ua.achievement_id
           WHERE ua.user_id = ?
           ORDER BY ua.earned_at DESC LIMIT 5''',
        (g.current_user_id,)
    ).fetchall()

    # 按类别统计
    category_stats = conn.execute(
        '''SELECT a.category, COUNT(*) as total,
                  SUM(CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END) as unlocked
           FROM achievements a
           LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
           GROUP BY a.category''',
        (g.current_user_id,)
    ).fetchall()

    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'total': total_achievements,
            'unlocked': unlocked_count,
            'percentage': round(unlocked_count / total_achievements * 100, 1) if total_achievements > 0 else 0,
            'recent': [dict(r) for r in recent],
            'category_stats': [dict(c) for c in category_stats],
        }
    })
