from flask import Blueprint, request, jsonify
from auth import login_required
from models import get_db

time_bp = Blueprint('time', __name__)

# === ??? + ??? ????? ===

@time_bp.route('/time-records', methods=['GET', 'POST'])
@login_required
def handle_records():
    db = get_db()
    if request.method == 'POST':
        data = request.get_json()
        db.execute('INSERT INTO time_records (user_id, category, description, duration_min) VALUES (?, ?, ?, ?)',
              (request.user_id, data['category'], data.get('description', ''), data['duration_min']))
        db.commit()
        record_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.close()
        return jsonify({'id': record_id, 'message': 'Record created'}), 201
    records = db.execute('SELECT * FROM time_records WHERE user_id = ? ORDER BY created_at DESC', (request.user_id,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in records])

# ??/?? - ?? C ?????
@time_bp.route('/time-records/undo', methods=['POST'])
@login_required
def undo_record():
    return jsonify({'message': 'Undo - to be implemented with C stack module'})

@time_bp.route('/time-records/redo', methods=['POST'])
@login_required
def redo_record():
    return jsonify({'message': 'Redo - to be implemented with C stack module'})
