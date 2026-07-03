# === ??? + ??? ?? ===
from flask import Blueprint, request, jsonify
from auth import login_required
from models import get_db

search_bp = Blueprint('search', __name__)

# ????? - ?? C ?? KMP ??
@search_bp.route('/search', methods=['GET'])
@login_required
def search_records():
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify([])
    db = get_db()
    records = db.execute('SELECT * FROM time_records WHERE user_id = ? AND (description LIKE ? OR category LIKE ?) ORDER BY created_at DESC', (request.user_id, f'%{keyword}%', f'%{keyword}%')).fetchall()
    db.close()
    return jsonify([dict(r) for r in records])
