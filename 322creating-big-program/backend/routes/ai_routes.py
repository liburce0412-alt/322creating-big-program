"""
AI 分析报告与聊天 API 路由 — 丁超轶
提供 AI 学习报告生成、对话、智能建议等功能
"""
import random
from datetime import date, datetime, timedelta
from flask import Blueprint, request, jsonify, g
from models import get_connection
from auth import login_required

ai_bp = Blueprint('ai', __name__)


# ==================== AI 学习报告 ====================

@ai_bp.route('/report/generate', methods=['POST'])
@login_required
def generate_report():
    """生成 AI 学习分析报告"""
    data = request.get_json() or {}
    report_type = data.get('type', 'daily')  # daily / weekly / monthly
    period_start = data.get('period_start', '')
    period_end = data.get('period_end', '')

    today = date.today()

    # 确定时间范围
    if report_type == 'daily':
        period_start = today.isoformat()
        period_end = today.isoformat()
    elif report_type == 'weekly':
        period_start = (today - timedelta(days=today.weekday())).isoformat()
        period_end = today.isoformat()
    elif report_type == 'monthly':
        period_start = today.replace(day=1).isoformat()
        period_end = today.isoformat()
    elif not period_start or not period_end:
        period_start = (today - timedelta(days=7)).isoformat()
        period_end = today.isoformat()

    conn = get_connection()

    # 收集该时间段内的数据
    pomodoro_data = conn.execute(
        '''SELECT COUNT(*) as total, COALESCE(SUM(total_focus_seconds),0) as focus_seconds
           FROM pomodoro_sessions
           WHERE user_id=? AND status="completed"
           AND date(completed_at) BETWEEN ? AND ?''',
        (g.current_user_id, period_start, period_end)
    ).fetchone()

    time_records = conn.execute(
        '''SELECT category, COALESCE(SUM(duration_minutes),0) as total_minutes
           FROM time_records
           WHERE user_id=? AND date(start_time) BETWEEN ? AND ?
           GROUP BY category
           ORDER BY total_minutes DESC''',
        (g.current_user_id, period_start, period_end)
    ).fetchall()

    total_focus_hours = round((pomodoro_data['focus_seconds'] or 0) / 3600, 1)
    completed_count = pomodoro_data['total'] or 0

    # 生成 AI 分析内容
    content = _generate_analysis_text(
        report_type, period_start, period_end,
        completed_count, total_focus_hours,
        [dict(r) for r in time_records]
    )

    # 计算综合评分 (0-100)
    score = _calculate_score(completed_count, total_focus_hours, report_type)

    # 生成建议
    suggestions = _generate_suggestions(completed_count, total_focus_hours,
                                        [dict(r) for r in time_records])

    # 保存报告
    cursor = conn.execute(
        '''INSERT INTO ai_reports (user_id, report_type, period_start, period_end, content, score, suggestions)
           VALUES (?,?,?,?,?,?,?)''',
        (g.current_user_id, report_type, period_start, period_end, content, score,
         ';'.join(suggestions))
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 触发成就检查
    from routes.pomodoro_routes import _check_pomodoro_achievements
    _check_pomodoro_achievements(g.current_user_id)

    return jsonify({
        'code': 200,
        'message': 'AI 报告已生成',
        'data': {
            'id': report_id,
            'type': report_type,
            'period_start': period_start,
            'period_end': period_end,
            'content': content,
            'score': score,
            'suggestions': suggestions,
            'stats': {
                'completed_pomodoros': completed_count,
                'total_focus_hours': total_focus_hours,
                'categories': [dict(r) for r in time_records],
            }
        }
    })


@ai_bp.route('/report/list', methods=['GET'])
@login_required
def list_reports():
    """获取 AI 报告历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    report_type = request.args.get('type', '')
    offset = (page - 1) * per_page

    conn = get_connection()
    where = 'WHERE user_id=?'
    params = [g.current_user_id]
    if report_type:
        where += ' AND report_type=?'
        params.append(report_type)

    total = conn.execute(
        f'SELECT COUNT(*) as cnt FROM ai_reports {where}', params
    ).fetchone()['cnt']

    reports = conn.execute(
        f'SELECT * FROM ai_reports {where} ORDER BY created_at DESC LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'list': [dict(r) for r in reports],
            'total': total,
            'page': page,
            'total_pages': (total + per_page - 1) // per_page,
        }
    })


@ai_bp.route('/report/<int:report_id>', methods=['GET'])
@login_required
def get_report(report_id):
    """获取单份 AI 报告详情"""
    conn = get_connection()
    report = conn.execute(
        'SELECT * FROM ai_reports WHERE id=? AND user_id=?',
        (report_id, g.current_user_id)
    ).fetchone()
    conn.close()

    if not report:
        return jsonify({'code': 404, 'message': '报告不存在'})

    return jsonify({'code': 200, 'data': dict(report)})


@ai_bp.route('/report/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """删除 AI 报告"""
    conn = get_connection()
    conn.execute(
        'DELETE FROM ai_reports WHERE id=? AND user_id=?',
        (report_id, g.current_user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'message': '报告已删除'})


# ==================== AI 对话 ====================

@ai_bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    """发送消息给 AI 助手"""
    data = request.get_json() or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'code': 400, 'message': '消息不能为空'})

    conn = get_connection()

    # 保存用户消息
    conn.execute(
        'INSERT INTO chat_history (user_id, role, content) VALUES (?,?,?)',
        (g.current_user_id, 'user', message)
    )

    # 获取最近对话历史（用于上下文）
    history = conn.execute(
        'SELECT role, content FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT 10',
        (g.current_user_id,)
    ).fetchall()

    # 生成 AI 回复（基于规则 + 数据的智能回复）
    reply = _generate_reply(message, history, g.current_user_id, conn)

    # 保存 AI 回复
    conn.execute(
        'INSERT INTO chat_history (user_id, role, content) VALUES (?,?,?)',
        (g.current_user_id, 'assistant', reply)
    )
    conn.commit()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'role': 'assistant',
            'content': reply,
        }
    })


@ai_bp.route('/chat/history', methods=['GET'])
@login_required
def chat_history():
    """获取对话历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    offset = (page - 1) * per_page

    conn = get_connection()
    total = conn.execute(
        'SELECT COUNT(*) as cnt FROM chat_history WHERE user_id=?',
        (g.current_user_id,)
    ).fetchone()['cnt']

    messages = conn.execute(
        'SELECT * FROM chat_history WHERE user_id=? ORDER BY id ASC LIMIT ? OFFSET ?',
        (g.current_user_id, per_page, offset)
    ).fetchall()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'list': [dict(m) for m in messages],
            'total': total,
        }
    })


@ai_bp.route('/chat/clear', methods=['DELETE'])
@login_required
def clear_chat():
    """清空对话历史"""
    conn = get_connection()
    conn.execute('DELETE FROM chat_history WHERE user_id=?', (g.current_user_id,))
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'message': '对话历史已清空'})


# ==================== AI 洞察 ====================

@ai_bp.route('/insights', methods=['GET'])
@login_required
def get_insights():
    """获取 AI 学习洞察和建议"""
    conn = get_connection()

    today = date.today()

    # 今日数据
    today_pomodoros = conn.execute(
        'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed" AND date(completed_at)=?',
        (g.current_user_id, today.isoformat())
    ).fetchone()['cnt']

    today_minutes = conn.execute(
        'SELECT COALESCE(SUM(duration_minutes),0) as total FROM time_records WHERE user_id=? AND date(start_time)=?',
        (g.current_user_id, today.isoformat())
    ).fetchone()['total']

    # 本周趋势
    week_start = today - timedelta(days=today.weekday())
    week_data = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        cnt = conn.execute(
            'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed" AND date(completed_at)=?',
            (g.current_user_id, d.isoformat())
        ).fetchone()['cnt']
        week_data.append({'date': d.isoformat(), 'day_name': _day_name_cn(d.weekday()), 'count': cnt})

    # 最佳时段分析
    hour_dist = conn.execute(
        '''SELECT CAST(strftime('%H', completed_at) AS INTEGER) as hour, COUNT(*) as cnt
           FROM pomodoro_sessions
           WHERE user_id=? AND status="completed"
           GROUP BY hour ORDER BY cnt DESC LIMIT 3''',
        (g.current_user_id,)
    ).fetchall()

    best_hours = [{'hour': f'{h["hour"]}:00-{h["hour"]+1}:00', 'count': h['cnt']} for h in hour_dist]

    conn.close()

    # 生成个性化建议
    tips = []
    if today_pomodoros == 0:
        tips.append('今天还没有完成番茄钟，现在是开始的好时机！')
    if today_pomodoros >= 4:
        tips.append('你已经完成了 4+ 个番茄钟，记得适当休息保护眼睛 👀')
    avg = sum(d['count'] for d in week_data) / 7
    if avg < 2:
        tips.append('本周日均番茄钟数偏低，尝试每天至少完成 2-3 个以保持节奏')
    if best_hours:
        tips.append(f'你的高效时段是 {best_hours[0]["hour"]}，可以把重要任务安排在这个时间段')

    return jsonify({
        'code': 200,
        'data': {
            'today': {
                'pomodoros': today_pomodoros,
                'total_minutes': today_minutes,
                'total_hours': round(today_minutes / 60, 1),
            },
            'week_trend': week_data,
            'best_hours': best_hours,
            'tips': tips,
        }
    })


# ==================== 辅助函数 ====================

def _generate_analysis_text(report_type, start, end, pomodoro_count, focus_hours, categories):
    """生成 AI 分析文本"""
    type_labels = {'daily': '日', 'weekly': '周', 'monthly': '月'}
    label = type_labels.get(report_type, '综合')

    if pomodoro_count == 0:
        return f"""
📊 **{label}学习报告** ({start} ~ {end})

本期没有记录到番茄钟数据。

💡 建议从每天 1-2 个番茄钟开始，逐步建立学习节奏。
        """.strip()

    cat_lines = ''
    for c in categories:
        cat_lines += f'- {c["category"]}: {c["total_minutes"]} 分钟\n'

    level = '优秀 🌟' if focus_hours >= 20 else ('良好 👍' if focus_hours >= 10 else '需努力 💪')

    return f"""
📊 **{label}学习报告** ({start} ~ {end})

**总体评价**: {level}

**关键数据**:
- 完成番茄钟: {pomodoro_count} 个
- 专注时长: {focus_hours} 小时
- 学习分类分布:
{cat_lines or '(暂无分类数据)'}

**AI 分析**:
{f'你在这段时间保持了 {focus_hours} 小时的深度专注，非常不错！' if focus_hours >= 15 else f'本周完成了 {pomodoro_count} 个番茄钟，继续保持节奏！' if pomodoro_count >= 5 else '学习节奏还可以加强，试着每天固定时间学习。'}
        """.strip()


def _calculate_score(pomodoro_count, focus_hours, report_type):
    """计算综合评分 0-100"""
    score = 50
    score += min(pomodoro_count * 2, 30)  # 番茄钟最多 +30
    score += min(int(focus_hours * 2), 20)  # 专注时长最多 +20
    return min(score, 100)


def _generate_suggestions(pomodoro_count, focus_hours, categories):
    """生成个性化建议"""
    suggestions = []
    if pomodoro_count < 5:
        suggestions.append('尝试使用番茄钟法：25 分钟专注 + 5 分钟休息')
    if focus_hours < 5:
        suggestions.append('建议每天至少投入 2 小时深度学习')
    if not categories:
        suggestions.append('给学习记录添加分类标签，方便追踪各科目投入')
    if pomodoro_count >= 20:
        suggestions.append('注意劳逸结合，保证充足睡眠')
    if len(suggestions) < 2:
        suggestions.append('保持当前节奏，你做得很好！')
    return suggestions


def _generate_reply(message, history, user_id, conn):
    """基于规则生成 AI 回复（实际项目可接入大模型 API）"""
    msg_lower = message.lower()

    # 学习/番茄钟相关
    if any(w in msg_lower for w in ['番茄', 'pomodoro', '专注', '计时']):
        today_count = conn.execute(
            'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed" AND date(completed_at)=?',
            (user_id, date.today().isoformat())
        ).fetchone()['cnt']
        return f"番茄钟是个很好的专注工具！🍅 你今天已经完成了 {today_count} 个番茄钟。建议每次专注 25 分钟，然后休息 5 分钟。需要我帮你开始一个番茄钟吗？"

    if any(w in msg_lower for w in ['成就', 'achievement', '徽章']):
        unlocked = conn.execute(
            'SELECT COUNT(*) as cnt FROM user_achievements WHERE user_id=?',
            (user_id,)
        ).fetchone()['cnt']
        total = conn.execute('SELECT COUNT(*) as cnt FROM achievements').fetchone()['cnt']
        return f"你已经解锁了 {unlocked}/{total} 个成就！🏆 继续完成任务来解锁更多成就吧。输入「查看成就」可以看到完整列表。"

    if any(w in msg_lower for w in ['报告', '分析', 'report', '统计']):
        return "我可以为你生成学习分析报告！📊 在 AI 报告页面，你可以选择日报、周报或月报，系统会根据你的学习数据自动生成分析和建议。"

    if any(w in msg_lower for w in ['你好', 'hello', 'hi', '嗨']):
        return f"你好！👋 我是你的学习助手。我可以帮你分析学习数据、提供建议、管理番茄钟。有什么可以帮你的吗？"

    if any(w in msg_lower for w in ['建议', '推荐', '怎么', '如何', 'suggest']):
        total_pomodoros = conn.execute(
            'SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id=? AND status="completed"',
            (user_id,)
        ).fetchone()['cnt']
        if total_pomodoros < 5:
            return "建议你从每天 2 个番茄钟开始，逐步建立学习节奏。选择一个固定的时间段（如上午 9-11 点），关闭手机通知，专注学习。📵"
        elif total_pomodoros < 20:
            return "你已经有不错的基础了！可以尝试增加每日番茄钟数量，或者调整单次专注时长到 45 分钟。也可以给不同的科目分配不同的时段。📚"
        else:
            return "你已经很厉害了！建议尝试「主题学习法」—— 把相关科目放在一起学，比如上午理科、下午文科。也要注意复习和总结哦。✨"

    if any(w in msg_lower for w in ['谢谢', 'thanks', '感谢']):
        return "不客气！😊 随时可以来找我。加油！"

    # 默认回复
    return "我理解你的问题了。作为你的学习助手，我建议你保持规律的作息和专注的学习习惯。你可以试试番茄钟功能，25 分钟专注 + 5 分钟休息的节奏很科学哦！🍅"


def _day_name_cn(weekday):
    """星期几转中文"""
    names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return names[weekday] if 0 <= weekday < 7 else ''
