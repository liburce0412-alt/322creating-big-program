"""
achievement_routes.py —— 成就系统 API
谢佳杨 负责

接口：
  GET /api/user/achievements       — 获取用户已解锁的成就列表
  GET /api/user/achievements/all   — 获取所有成就及解锁状态
  GET /api/user/profile            — 获取用户完整信息（等级、经验、成就数）
"""
from flask import Blueprint, jsonify, g
from auth import login_required
from models import get_db
from config import BADGES, LEVEL_UP_BASE

achievement_bp = Blueprint("achievement", __name__)


@achievement_bp.route("/user/achievements", methods=["GET"])
@login_required
def get_user_achievements():
    """
    获取当前用户已解锁的成就

    返回：
        {
            "user_id": 1,
            "achievements": [
                {
                    "badge_id": "first_pomodoro",
                    "name": "🍅 初次专注",
                    "icon": "🍅",
                    "description": "完成第一次番茄钟",
                    "unlocked_at": "2024-07-04 10:30:00"
                },
                ...
            ]
        }
    """
    db = get_db()
    rows = db.execute(
        """SELECT badge_id, unlocked_at
           FROM achievements
           WHERE user_id = ?
           ORDER BY unlocked_at DESC""",
        (g.user_id,)
    ).fetchall()
    db.close()

    achievements = []
    for row in rows:
        badge = BADGES.get(row["badge_id"], {
            "name": row["badge_id"],
            "icon": "🎖️",
            "description": ""
        })
        achievements.append({
            "badge_id": row["badge_id"],
            "name": badge["name"],
            "icon": badge["icon"],
            "description": badge["description"],
            "unlocked_at": row["unlocked_at"]
        })

    return jsonify({
        "user_id": g.user_id,
        "achievements": achievements,
        "total_unlocked": len(achievements),
        "total_badges": len(BADGES)
    })


@achievement_bp.route("/user/achievements/all", methods=["GET"])
@login_required
def get_all_achievements():
    """
    获取所有成就定义 + 当前用户的解锁状态

    返回：
        {
            "badges": [
                {
                    "badge_id": "first_pomodoro",
                    "name": "🍅 初次专注",
                    "icon": "🍅",
                    "description": "完成第一次番茄钟",
                    "unlocked": true,
                    "unlocked_at": "2024-07-04 10:30:00"
                },
                ...
            ]
        }
    """
    db = get_db()
    unlocked_rows = db.execute(
        "SELECT badge_id, unlocked_at FROM achievements WHERE user_id = ?",
        (g.user_id,)
    ).fetchall()
    db.close()

    unlocked_map = {row["badge_id"]: row["unlocked_at"] for row in unlocked_rows}

    all_badges = []
    for badge_id, badge_info in BADGES.items():
        all_badges.append({
            "badge_id": badge_id,
            "name": badge_info["name"],
            "icon": badge_info["icon"],
            "description": badge_info["description"],
            "unlocked": badge_id in unlocked_map,
            "unlocked_at": unlocked_map.get(badge_id)
        })

    return jsonify({"badges": all_badges, "total": len(all_badges)})


@achievement_bp.route("/user/profile", methods=["GET"])
@login_required
def get_user_profile():
    """
    获取用户完整信息（等级、经验值、成就数、记录数等）

    返回：
        {
            "user_id": 1,
            "username": "zhangsan",
            "level": 5,
            "exp": 150,
            "exp_needed": 300,
            "exp_percent": 50.0,
            "total_pomodoros": 12,
            "total_records": 25,
            "total_achievements": 3,
            "streak_days": 5,
            "created_at": "2024-07-03 14:00:00"
        }
    """
    db = get_db()

    user = db.execute(
        "SELECT id, username, level, exp, is_admin, created_at FROM users WHERE id = ?",
        (g.user_id,)
    ).fetchone()

    if not user:
        db.close()
        return jsonify({"error": "用户不存在"}), 404

    # 升级所需经验
    level = user["level"]
    import math
    exp_needed = int(LEVEL_UP_BASE * (1.5 ** (level - 1)))
    exp_percent = round(user["exp"] / exp_needed * 100, 1) if exp_needed > 0 else 100

    # 统计数据
    total_pomodoros = db.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    total_records = db.execute(
        "SELECT COUNT(*) as cnt FROM time_records WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    total_achievements = db.execute(
        "SELECT COUNT(*) as cnt FROM achievements WHERE user_id = ?",
        (g.user_id,)
    ).fetchone()["cnt"]

    # 连续打卡天数
    from routes.pomodoro_routes import _calculate_streak
    streak = _calculate_streak(g.user_id, db)

    # 今日番茄钟
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    today_focus_min = db.execute(
        "SELECT COALESCE(SUM(duration_min), 0) as total FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = ?",
        (g.user_id, today)
    ).fetchone()["total"]

    db.close()

    return jsonify({
        "user_id": user["id"],
        "username": user["username"],
        "level": level,
        "exp": user["exp"],
        "exp_needed": exp_needed,
        "exp_percent": exp_percent,
        "is_admin": user["is_admin"],
        "today_focus_min": today_focus_min,
        "total_pomodoros": total_pomodoros,
        "total_records": total_records,
        "total_achievements": total_achievements,
        "streak_days": streak,
        "created_at": user["created_at"]
    })
