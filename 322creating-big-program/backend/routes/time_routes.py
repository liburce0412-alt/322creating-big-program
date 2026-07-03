"""
时间记录 API 路由 — 李恩琪 + 余欣泽
TODO: 实现时间记录的增删改查、分类统计等功能
"""
from flask import Blueprint, request, jsonify, g
from models import get_connection
from auth import login_required

time_bp = Blueprint('time', __name__)


@time_bp.route('/record', methods=['POST'])
@login_required
def create_record():
    """创建时间记录"""
    data = request.get_json() or {}
    category = data.get('category', '学习')
    description = data.get('description', '')
    start_time = data.get('start_time', '')
    end_time = data.get('end_time', '')
    duration = data.get('duration_minutes', 0)

    if not start_time:
        return jsonify({'code': 400, 'message': '开始时间不能为空'})

    conn = get_connection()
    cursor = conn.execute(
        '''INSERT INTO time_records (user_id, category, description, start_time, end_time, duration_minutes)
           VALUES (?,?,?,?,?,?)''',
        (g.current_user_id, category, description, start_time, end_time, duration)
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()

    return jsonify({'code': 200, 'message': '记录已创建', 'data': {'id': record_id}})


@time_bp.route('/records', methods=['GET'])
@login_required
def list_records():
    """获取时间记录列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '')
    offset = (page - 1) * per_page

    conn = get_connection()
    where = 'WHERE user_id=?'
    params = [g.current_user_id]
    if category:
        where += ' AND category=?'
        params.append(category)

    total = conn.execute(
        f'SELECT COUNT(*) as cnt FROM time_records {where}', params
    ).fetchone()['cnt']

    records = conn.execute(
        f'SELECT * FROM time_records {where} ORDER BY start_time DESC LIMIT ? OFFSET ?',
        params + [per_page, offset]
    ).fetchall()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'list': [dict(r) for r in records],
            'total': total,
            'page': page,
            'total_pages': (total + per_page - 1) // per_page,
        }
    })


@time_bp.route('/record/<int:record_id>', methods=['PUT'])
@login_required
def update_record(record_id):
    """更新时间记录 — TODO"""
    return jsonify({'code': 200, 'message': 'TODO: 完善时间记录更新'})


@time_bp.route('/record/<int:record_id>', methods=['DELETE'])
@login_required
def delete_record(record_id):
    """删除时间记录"""
    conn = get_connection()
    conn.execute(
        'DELETE FROM time_records WHERE id=? AND user_id=?',
        (record_id, g.current_user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'message': '记录已删除'})


@time_bp.route('/stats', methods=['GET'])
@login_required
def time_stats():
    """时间统计概览"""
    conn = get_connection()
    # 总时长
    total = conn.execute(
        'SELECT COALESCE(SUM(duration_minutes),0) as total FROM time_records WHERE user_id=?',
        (g.current_user_id,)
    ).fetchone()['total']

    # 按分类统计
    by_category = conn.execute(
        'SELECT category, COALESCE(SUM(duration_minutes),0) as total_minutes, COUNT(*) as count FROM time_records WHERE user_id=? GROUP BY category',
        (g.current_user_id,)
    ).fetchall()

    conn.close()
    return jsonify({
        'code': 200,
        'data': {
            'total_minutes': total,
            'total_hours': round(total / 60, 1),
            'by_category': [dict(c) for c in by_category],
        }
    })
