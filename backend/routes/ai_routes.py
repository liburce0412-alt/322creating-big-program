# ai_routes.py - AI analysis (???+???)
from flask import Blueprint, request, jsonify
from auth import login_required
from models import get_db
from config import DEEPSEEK_API_URL, DEEPSEEK_API_KEY, GEMINI_API_URL, GEMINI_API_KEY
import requests
import json

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai/report', methods=['POST'])
@login_required
def generate_report():
    model = request.get_json().get('model', 'deepseek')
    db = get_db()
    records = db.execute('SELECT * FROM time_records WHERE user_id = ? ORDER BY created_at DESC LIMIT 100', (request.user_id,)).fetchall()
    db.close()
    if not records:
        return jsonify({'report': '????????????????'})
    records_data = [dict(r) for r in records]
    prompt = f'?????????????????????????(??)?{json.dumps(records_data, ensure_ascii=False)}'
    return jsonify({'report': 'AI?????? - ??config.py???API??????', 'records_count': len(records), 'model': model})
