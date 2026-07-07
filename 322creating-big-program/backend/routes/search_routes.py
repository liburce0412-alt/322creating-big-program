"""
search_routes.py —— 关键词搜索 API
👤 李恩琪+余欣泽 负责填充

接口：
  GET /api/search  — 关键词搜索时间记录（使用 C 模块 KMP 算法）
"""
from flask import Blueprint, request, jsonify, g
from auth import login_required
from models import get_db

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["GET"])
@login_required
def search_records():
    """
    关键词搜索时间记录

    查询参数：
        ?q=高数

    优先使用 C 模块 KMP 算法，fallback 到 SQL LIKE。

    返回：
        { "keyword": "高数", "count": 3, "results": [...] }
    """
    keyword = (request.args.get("q") or "").strip()

    if not keyword:
        return jsonify({"error": "搜索关键词不能为空"}), 400

    # 尝试 C 模块 KMP 搜索
    from c_bridge import call_c_module

    db = get_db()
    records = db.execute(
        """SELECT id, category, description, duration_min, created_at
           FROM time_records WHERE user_id = ?
           ORDER BY created_at DESC""",
        (g.user_id,)
    ).fetchall()
    db.close()

    records_list = [dict(r) for r in records]

    result = call_c_module("kmp", "search", {
        "keyword": keyword,
        "records": records_list
    })

    if result.get("status") == "ok" and result.get("result"):
        return jsonify({
            "keyword": keyword,
            "results": result["result"].get("matches", []),
            "source": "c_module_kmp"
        })

    # fallback: SQL LIKE
    db = get_db()
    matched = db.execute(
        """SELECT id, category, description, duration_min, created_at
           FROM time_records
           WHERE user_id = ? AND (description LIKE ? OR category LIKE ?)
           ORDER BY created_at DESC""",
        (g.user_id, f"%{keyword}%", f"%{keyword}%")
    ).fetchall()
    db.close()

    return jsonify({
        "keyword": keyword,
        "count": len(matched),
        "results": [dict(r) for r in matched],
        "source": "sql_like_fallback"
    })
