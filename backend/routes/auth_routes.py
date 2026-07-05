"""
auth_routes.py —— 用户注册登录 API
👤 李恩琪+余欣泽 负责填充

接口：
  POST /api/register  — 用户注册
  POST /api/login     — 用户登录
  GET  /api/users/me  — 获取个人信息
  PUT  /api/users/me  — 修改个人信息
  DELETE /api/users/me — 注销账号
  GET  /api/users/<id> — 获取指定用户公开信息
"""
from flask import Blueprint, request, jsonify, g
from auth import hash_password, generate_token, add_exp, login_required
from models import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
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
    existing = db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "用户名已被注册"}), 409

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
    """用户登录"""
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
            "exp": user["exp"]
        }
    })


@auth_bp.route("/users/me", methods=["GET"])
@login_required
def get_profile():
    """获取当前用户的个人信息"""
    db = get_db()
    user = db.execute(
        "SELECT id, username, level, exp, created_at FROM users WHERE id = ?",
        (g.user_id,)
    ).fetchone()
    db.close()
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify({"user": dict(user)})


@auth_bp.route("/users/me", methods=["PUT"])
@login_required
def update_profile():
    """修改个人信息（用户名/密码）"""
    data = request.get_json(silent=True) or {}
    new_username = (data.get("username") or "").strip()
    new_password = (data.get("password") or "").strip()

    if not new_username and not new_password:
        return jsonify({"error": "请提供要修改的用户名或密码"}), 400

    db = get_db()

    if new_username:
        if len(new_username) < 2 or len(new_username) > 32:
            db.close()
            return jsonify({"error": "用户名长度需在 2-32 个字符之间"}), 400
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (new_username, g.user_id)
        ).fetchone()
        if existing:
            db.close()
            return jsonify({"error": "用户名已被使用"}), 409
        db.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, g.user_id))

    if new_password:
        if len(new_password) < 6:
            db.close()
            return jsonify({"error": "密码长度至少 6 位"}), 400
        password_hash = hash_password(new_password)
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, g.user_id))

    db.commit()
    user = db.execute(
        "SELECT id, username, level, exp, created_at FROM users WHERE id = ?",
        (g.user_id,)
    ).fetchone()
    db.close()
    return jsonify({"message": "修改成功", "user": dict(user)})


@auth_bp.route("/users/me", methods=["DELETE"])
@login_required
def delete_account():
    """注销当前用户账号"""
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (g.user_id,))
    db.commit()
    db.close()
    return jsonify({"message": "账号已注销"})



@auth_bp.route("/users/lookup", methods=["GET"])
@login_required
def user_lookup():
    """快速查找用户（使用哈希表 C 模块缓存）"""
    keyword = (request.args.get("q") or "").strip()
    if not keyword:
        return jsonify({"error": "搜索关键词不能为空"}), 400
    from c_bridge import call_c_module
    db = get_db()
    users = db.execute(
        "SELECT id, username, level FROM users WHERE username LIKE ?",
        (f"%{keyword}%",)
    ).fetchall()
    db.close()
    call_c_module("hash_table", "insert", {
        "key": f"search:{keyword}",
        "value": {"results": [dict(u) for u in users], "count": len(users)}
    })
    return jsonify({"keyword": keyword, "results": [dict(u) for u in users], "count": len(users)})


@auth_bp.route("/users/<int:user_id>", methods=["GET"])
@login_required
def get_user_profile(user_id):
    """获取指定用户的公开信息"""
    db = get_db()
    user = db.execute(
        "SELECT id, username, level, exp, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    db.close()
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify({"user": dict(user)})
