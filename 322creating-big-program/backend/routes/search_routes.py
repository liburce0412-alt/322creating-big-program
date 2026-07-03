"""
搜索 API 路由 — 李恩琪 + 余欣泽
TODO: 实现基于 C 模块（KMP、哈希表）的全文搜索功能
"""
from flask import Blueprint, request, jsonify, g
from models import get_connection
from auth import login_required
from c_bridge import kmp_search, hash_table_operations

search_bp = Blueprint('search', __name__)


@search_bp.route('/records', methods=['GET'])
@login_required
def search_records():
    """搜索时间记录"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'code': 400, 'message': '搜索关键词不能为空'})

    conn = get_connection()
    records = conn.execute(
        '''SELECT * FROM time_records
           WHERE user_id=? AND (description LIKE ? OR category LIKE ?)
           ORDER BY start_time DESC LIMIT 50''',
        (g.current_user_id, f'%{q}%', f'%{q}%')
    ).fetchall()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'keyword': q,
            'list': [dict(r) for r in records],
            'total': len(records),
        }
    })


@search_bp.route('/pomodoro', methods=['GET'])
@login_required
def search_pomodoro():
    """搜索番茄钟记录 — TODO: 使用 KMP 算法"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'code': 400, 'message': '搜索关键词不能为空'})

    conn = get_connection()
    sessions = conn.execute(
        '''SELECT * FROM pomodoro_sessions
           WHERE user_id=? AND task_name LIKE ?
           ORDER BY id DESC LIMIT 50''',
        (g.current_user_id, f'%{q}%')
    ).fetchall()
    conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'keyword': q,
            'list': [dict(s) for s in sessions],
            'total': len(sessions),
        }
    })
