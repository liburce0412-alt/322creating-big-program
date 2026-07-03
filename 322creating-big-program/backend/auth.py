"""
JWT 认证模块
"""
import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

from config import Config


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def create_token(user_id: int, username: str) -> str:
    """生成 JWT Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> dict:
    """解析 JWT Token"""
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        if not token:
            return jsonify({'code': 401, 'message': '请先登录'}), 401

        payload = decode_token(token)
        if payload is None:
            return jsonify({'code': 401, 'message': '登录已过期，请重新登录'}), 401

        g.current_user_id = payload['user_id']
        g.current_username = payload['username']
        return f(*args, **kwargs)
    return decorated
