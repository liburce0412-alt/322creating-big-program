# === ??? + ??? ????? ===
from flask import Blueprint, request, jsonify
from auth import login_required
from models import get_db

pomodoro_bp = Blueprint('pomodoro', __name__)

@pomodoro_bp.route('/pomodoro/complete', methods=['POST'])
@login_required
def complete_pomodoro():
    data = request.get_json()
    duration = data.get('duration_min', 25)
    db = get_db()
    db.execute('INSERT INTO pomodoro_sessions (user_id, duration_min, exp_gained) VALUES (?, ?, ?)',
          (request.user_id, duration, 10))
    db.execute('UPDATE users SET exp = exp + 10 WHERE id = ?', (request.user_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Pomodoro completed!', 'exp_gained': 10}), 201

@pomodoro_bp.route('/pomodoro/history', methods=['GET'])
@login_required
def pomodoro_history():
    db = get_db()
    sessions = db.execute('SELECT * FROM pomodoro_sessions WHERE user_id = ? ORDER BY completed_at DESC LIMIT 50', (request.user_id,)).fetchall()
    db.close()
    return jsonify([dict(s) for s in sessions])

@pomodoro_bp.route('/pomodoro/today', methods=['GET'])
@login_required
def pomodoro_today():
    db = get_db()
    total = db.execute('SELECT COALESCE(SUM(duration_min), 0) FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = date('now')', (request.user_id,)).fetchone()[0]
    db.close()
    return jsonify({'total_minutes': total})

print('pomodoro_routes.py done')
