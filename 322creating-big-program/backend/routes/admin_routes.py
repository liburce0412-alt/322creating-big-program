"""
admin_routes.py —— \u7ba1\u7406\u5458\u540e\u53f0 API
"""
from flask import Blueprint, request, jsonify, g
from auth import login_required, admin_required
from models import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/users", methods=["GET"])
@login_required
@admin_required
def get_admin_users():
    """\u83b7\u53d6\u6240\u6709\u7528\u6237\u5217\u8868\uff08\u5305\u542b\u7edf\u8ba1\uff09"""
    db = get_db()
    users = db.execute("""
        SELECT u.id, u.username, u.level, u.exp, u.is_admin, u.created_at,
               (SELECT COUNT(*) FROM time_records WHERE user_id = u.id) as record_count,
               (SELECT COUNT(*) FROM pomodoro_sessions WHERE user_id = u.id) as pomodoro_count
        FROM users u ORDER BY u.id
    """).fetchall()

    total = db.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    admins = db.execute("SELECT COUNT(*) as c FROM users WHERE is_admin = 1").fetchone()["c"]
    total_records = db.execute("SELECT COUNT(*) as c FROM time_records").fetchone()["c"]
    db.close()

    return jsonify({
        "users": [dict(u) for u in users],
        "stats": {
            "total_users": total,
            "total_admins": admins,
            "total_records": total_records
        }
    })


@admin_bp.route("/admin/users/<int:user_id>/promote", methods=["POST"])
@login_required
@admin_required
def promote_admin(user_id):
    db = get_db()
    db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    return jsonify({"message": "\u5df2\u8bbe\u4e3a\u7ba1\u7406\u5458"})


@admin_bp.route("/admin/users/<int:user_id>/demote", methods=["POST"])
@login_required
@admin_required
def demote_admin(user_id):
    if user_id == g.user_id:
        return jsonify({"error": "\u4e0d\u80fd\u53d6\u6d88\u81ea\u5df1\u7684\u7ba1\u7406\u5458\u8d44\u683c"}), 400
    db = get_db()
    db.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    return jsonify({"message": "\u5df2\u53d6\u6d88\u7ba1\u7406\u5458"})


@admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == g.user_id:
        return jsonify({"error": "\u4e0d\u80fd\u5220\u9664\u81ea\u5df1"}), 400
    db = get_db()
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    return jsonify({"message": "\u7528\u6237\u5df2\u5220\u9664"})
