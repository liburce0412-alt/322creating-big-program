from flask import Blueprint, request, jsonify
from auth import hash_password, create_token, login_required, verify_token
from models import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    db = get_db()
    try:
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
              (username, hash_password(password)))
        db.commit()
        user = db.execute('SELECT id, username FROM users WHERE username = ?', (username,)).fetchone()
        token = create_token(user['id'], user['username'])
        return jsonify({'token': token, 'user': {'id': user['id'], 'username': user['username']}}), 201
    except Exception as e:
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        db.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    db.close()
    if not user or user['password_hash'] != hash_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_token(user['id'], user['username'])
    return jsonify({'token': token, 'user': {'id': user['id'], 'username': user['username'], 'level': user['level'], 'exp': user['exp']}})

@auth_bp.route('/user/profile', methods=['GET'])
@login_required
def get_profile():
    db = get_db()
    user = db.execute('SELECT id, username, level, exp FROM users WHERE id = ?', (request.user_id,)).fetchone()
    db.close()
    return jsonify({'id': user['id'], 'username': user['username'], 'level': user['level'], 'exp': user['exp']})
