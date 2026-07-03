"""
auth.py —— JWT 用户登录认证
"""
import jwt
import hashlib
import datetime
from functools import wraps
from flask import request, jsonify, g
from config import SECRET_KEY, TOKEN_EXPIRE_HOURS
from models import get_db


def hash_password(password: str) -> str:
    """对密码进行 SHA-256 哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def generate_token(user_id: int, username: str) -> str:
    """生成 JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.now(datetime.timezone.utc) +
               datetime.timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.datetime.now(datetime.timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """验证 JWT token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(f):
    """装饰器：要求请求头携带有效的 Authorization: Bearer <token>"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if not token:
            return jsonify({"error": "未登录，请先登录"}), 401

        payload = verify_token(token)
        if payload is None:
            return jsonify({"error": "登录已过期，请重新登录"}), 401

        # 存入 Flask g（请求上下文）
        g.user_id = payload["user_id"]
        g.username = payload["username"]
        return f(*args, **kwargs)
    return decorated


def get_user_by_id(user_id: int) -> dict | None:
    """通过 ID 获取用户信息"""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    if user:
        return dict(user)
    return None


def add_exp(user_id: int, amount: int) -> dict:
    """给用户增加经验值，返回 {level_up: bool, new_level: int, exp: int}"""
    db = get_db()
    user = db.execute("SELECT level, exp FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        db.close()
        return {"level_up": False, "new_level": 1, "exp": 0}

    level = user["level"]
    exp = user["exp"] + amount
    level_up = False

    # 检查升级：每级所需经验 = LEVEL_UP_BASE * 1.5^(level-1)
    from config import LEVEL_UP_BASE
    needed = int(LEVEL_UP_BASE * (1.5 ** (level - 1)))
    while exp >= needed:
        exp -= needed
        level += 1
        level_up = True
        needed = int(LEVEL_UP_BASE * (1.5 ** (level - 1)))

    db.execute("UPDATE users SET level = ?, exp = ? WHERE id = ?", (level, exp, user_id))
    db.commit()
    db.close()

    return {
        "level_up": level_up,
        "new_level": level,
        "exp": exp,
        "needed_for_next": needed
    }
