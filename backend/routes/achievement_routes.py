# achievement_routes.py - 成就系统 (谢佳杨+丁超轶)
from flask import Blueprint, jsonify
from auth import login_required
from models import get_db

achievement_bp = Blueprint('achievement', __name__)
BADGES = {
7day: 连续7天专注, zen: 禅定模式, master: 时间掌控者}

@achievement_bp.route('/user/achievements', methods=['GET'])
@login_required
def get_achievements():
    db = get_db()
    earned = [r['badge_id'] for r in db.execute('SELECT badge_id FROM achievements WHERE user_id = ?', (request.user_id,)).fetchall()]
    db.close()
    all_badges = [{
badge_id: k, name: v, earned: k in earned} for k, v in BADGES.items()]
    return jsonify(all_badges)
