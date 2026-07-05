"""
time_routes.py —— 时间记录 CRUD + 统计 API
👤 李恩琪+余欣泽 负责填充

接口：
  POST   /api/time-records        — 新增时间记录
  GET    /api/time-records        — 获取时间记录列表（分页、筛选）
  DELETE /api/time-records/<id>   — 删除记录
  GET    /api/time-records/stats  — 时间统计汇总
  POST   /api/time-records/undo   — 撤销（栈）
  POST   /api/time-records/redo   — 重做（栈）
"""
from flask import Blueprint, request, jsonify, g
from auth import login_required
from models import get_db

time_bp = Blueprint("time", __name__)

# 撤销/重做栈（内存中，gunicorn -w 1 单进程安全）
_undo_stack = []
_redo_stack = []


@time_bp.route("/time-records", methods=["POST"])
@login_required
def add_time_record():
    """
    新增时间记录

    请求体 JSON：
        { "category": "学习", "description": "复习高数", "duration_min": 90 }

    返回：
        { "id": 1, "message": "记录添加成功" }
    """
    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip()
    description = (data.get("description") or "").strip()
    duration_min = data.get("duration_min", 0)

    if not category:
        return jsonify({"error": "类别不能为空"}), 400
    if duration_min <= 0:
        return jsonify({"error": "时长必须大于 0"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO time_records (user_id, category, description, duration_min) VALUES (?, ?, ?, ?)",
        (g.user_id, category, description, duration_min)
    )
    record_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    # 推入撤销栈
    _undo_stack.append({
        "id": record_id,
        "user_id": g.user_id,
        "category": category,
        "description": description,
        "duration_min": duration_min
    })

    # 添加经验
    from auth import add_exp
    from config import EXP_PER_RECORD
    add_exp(g.user_id, EXP_PER_RECORD, db)

    # 检查成就
    from routes.pomodoro_routes import check_and_unlock_achievements
    new_achievements = check_and_unlock_achievements(g.user_id, db)

    db.commit()
    db.close()

    return jsonify({
        "id": record_id,
        "message": "记录添加成功",
        "new_achievements": new_achievements
    }), 201


@time_bp.route("/time-records", methods=["GET"])
@login_required
def get_time_records():
    """
    获取时间记录列表

    查询参数：
        ?page=1&limit=20&category=学习

    返回：
        { "total": 50, "page": 1, "records": [...] }
    """
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    category = request.args.get("category", "").strip()
    offset = (page - 1) * limit

    db = get_db()

    if category:
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM time_records WHERE user_id = ? AND category = ?",
            (g.user_id, category)
        ).fetchone()["cnt"]
        records = db.execute(
            """SELECT * FROM time_records
               WHERE user_id = ? AND category = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (g.user_id, category, limit, offset)
        ).fetchall()
    else:
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM time_records WHERE user_id = ?",
            (g.user_id,)
        ).fetchone()["cnt"]
        records = db.execute(
            """SELECT * FROM time_records
               WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (g.user_id, limit, offset)
        ).fetchall()

    db.close()

    return jsonify({
        "total": total,
        "page": page,
        "limit": limit,
        "records": [dict(r) for r in records]
    })


@time_bp.route("/time-records/<int:record_id>", methods=["PUT"])
@login_required
def update_time_record(record_id):
    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip()
    description = (data.get("description") or "").strip()
    duration_min = data.get("duration_min", 0)
    if not category:
        return jsonify({"error": "\u7c7b\u522b\u4e0d\u80fd\u4e3a\u7a7a"}), 400
    if duration_min <= 0:
        return jsonify({"error": "\u65f6\u957f\u5fc5\u987b\u5927\u4e8e 0"}), 400
    db = get_db()
    record = db.execute("SELECT id FROM time_records WHERE id = ? AND user_id = ?", (record_id, g.user_id)).fetchone()
    if not record:
        db.close()
        return jsonify({"error": "\u8bb0\u5f55\u4e0d\u5b58\u5728"}), 404
    db.execute("UPDATE time_records SET category = ?, description = ?, duration_min = ? WHERE id = ? AND user_id = ?",
               (category, description, duration_min, record_id, g.user_id))
    db.commit()
    db.close()
    return jsonify({"message": "\u8bb0\u5f55\u5df2\u66f4\u65b0", "id": record_id})


@time_bp.route("/time-records/<int:record_id>", methods=["DELETE"])
@login_required
def delete_time_record(record_id):
    """删除时间记录"""
    db = get_db()
    record = db.execute(
        "SELECT id FROM time_records WHERE id = ? AND user_id = ?",
        (record_id, g.user_id)
    ).fetchone()
    if not record:
        db.close()
        return jsonify({"error": "记录不存在"}), 404

    db.execute("DELETE FROM time_records WHERE id = ?", (record_id,))
    db.commit()
    db.close()
    return jsonify({"message": "记录已删除", "id": record_id})


@time_bp.route("/time-records/stats", methods=["GET"])
@login_required
def get_time_stats():
    """
    时间统计汇总

    返回：
        {
            "total_minutes": 1200,
            "total_records": 50,
            "by_category": [{"category":"学习","total_min":800,"count":20}, ...],
            "by_date": [{"date":"2024-07-04","total_min":200}, ...]
        }
    """
    db = get_db()

    total_minutes = db.execute(
        "SELECT COALESCE(SUM(duration_min), 0) as total FROM time_records WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["total"]

    total_records = db.execute(
        "SELECT COUNT(*) as cnt FROM time_records WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    by_category = db.execute(
        """SELECT category, SUM(duration_min) as total_min, COUNT(*) as count
           FROM time_records WHERE user_id = ?
           GROUP BY category ORDER BY total_min DESC""",
        (g.user_id,)
    ).fetchall()

    by_date = db.execute(
        """SELECT date(created_at) as date, SUM(duration_min) as total_min
           FROM time_records WHERE user_id = ?
           GROUP BY date(created_at) ORDER BY date DESC LIMIT 30""",
        (g.user_id,)
    ).fetchall()

    db.close()

    return jsonify({
        "total_minutes": total_minutes,
        "total_records": total_records,
        "by_category": [dict(r) for r in by_category],
        "by_date": [dict(r) for r in by_date]
    })


@time_bp.route("/time-records/undo", methods=["POST"])
@login_required
def undo_record():
    """
    撤销最近的时间记录（使用 C 模块栈管理）
    👤 李恩琪+余欣泽：对接 C 模块 stack
    """
    from c_bridge import call_c_module
    result = call_c_module("stack", "pop")
    if result.get("status") == "ok":
        return jsonify({"message": "撤销成功", "record": result.get("result")})
    return jsonify({"error": "没有可撤销的记录"}), 400


@time_bp.route("/time-records/redo", methods=["POST"])
@login_required
def redo_record():
    """
    重做刚才撤销的记录
    👤 李恩琪+余欣泽：对接 C 模块 stack
    """
    from c_bridge import call_c_module
    result = call_c_module("stack", "redo_pop")
    if result.get("status") == "ok":
        return jsonify({"message": "重做成功", "record": result.get("result")})
    return jsonify({"error": "没有可重做的记录"}), 400
