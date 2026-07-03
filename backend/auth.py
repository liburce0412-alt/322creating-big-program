import jwt
import datetime
from flask import request, jsonify
from functools import wraps
from config import JWT_SECRET_KEY, JWT_EXPIRATION_HOURS
import models
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
    except:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Unauthorized'}), 401
        request.user_id = payload['user_id']
        request.username = payload['username']
        return f(*args, **kwargs)
    return decorated
