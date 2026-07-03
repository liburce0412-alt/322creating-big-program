"""
用户认证 API 路由 — 李恩琪 + 余欣泽
TODO: 实现注册、登录、获取用户信息等功能
"""
from flask import Blueprint, request, jsonify, g
from models import get_connection
from auth import hash_password, verify_password, create_token, login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not username or not email or not password:
        return jsonify({'code': 400, 'message': '用户名、邮箱和密码不能为空'})
    if len(password) < 6:
        return jsonify({'code': 400, 'message': '密码长度至少 6 位'})

    conn = get_connection()
    existing = conn.execute(
        'SELECT id FROM users WHERE username=? OR email=?',
        (username, email)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'code': 400, 'message': '用户名或邮箱已被注册'})

    conn.execute(
        'INSERT INTO users (username, email, password_hash) VALUES (?,?,?)',
        (username, email, hash_password(password))
    )
    conn.commit()
    conn.close()
    return jsonify({'code': 200, 'message': '注册成功！请登录'})


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'})

    conn = get_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username=? OR email=?',
        (username, username)
    ).fetchone()

    if not user or not verify_password(password, user['password_hash']):
        conn.close()
        return jsonify({'code': 401, 'message': '用户名或密码错误'})

    token = create_token(user['id'], user['username'])
    conn.close()
    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': token,
            'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
        }
    })


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_me():
    """获取当前用户信息"""
    conn = get_connection()
    user = conn.execute(
        'SELECT id, username, email, avatar, created_at FROM users WHERE id=?',
        (g.current_user_id,)
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'})

    return jsonify({'code': 200, 'data': dict(user)})


@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新个人信息 — TODO: 李恩琪+余欣泽 完善"""
    return jsonify({'code': 200, 'message': 'TODO: 完善个人信息更新'})
