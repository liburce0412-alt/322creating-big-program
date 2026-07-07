"""
auth_routes.py —— 用户注册登录 API
👤 李恩琪+余欣泽 负责填充

接口：
  POST /api/register  — 用户注册
  POST /api/login     — 用户登录
"""
from flask import Blueprint, request, jsonify
from auth import hash_password, generate_token, add_exp
from models import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    用户注册

    请求体 JSON：
        { "username": "zhangsan", "password": "123456" }

    返回：
        { "token": "...", "user": { "id": 1, "username": "zhangsan", "level": 1, "exp": 0, "is_admin": 0 } }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400
    if len(username) < 2 or len(username) > 32:
        return jsonify({"error": "用户名长度需在 2-32 个字符之间"}), 400
    if len(password) < 6:
        return jsonify({"error": "密码长度至少 6 位"}), 400

    db = get_db()

    # 检查用户名是否已存在
    existing = db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "用户名已被注册"}), 409

    # 创建用户
    password_hash = hash_password(password)
    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.commit()
    db.close()

    token = generate_token(user_id, username)

    return jsonify({
        "token": token,
        "user": {
            "id": user_id,
            "username": username,
            "level": 1,
            "exp": 0
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    用户登录

    请求体 JSON：
        { "username": "zhangsan", "password": "123456" }

    返回：
        { "token": "...", "user": { "id": 1, "username": "zhangsan", "level": 3, "exp": 120 } }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if not user:
        db.close()
        return jsonify({"error": "用户名或密码错误"}), 401

    if user["password_hash"] != hash_password(password):
        db.close()
        return jsonify({"error": "用户名或密码错误"}), 401

    db.close()

    token = generate_token(user["id"], user["username"])

    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "level": user["level"],
            "exp": user["exp"],
            "is_admin": user["is_admin"]
        }
    })
