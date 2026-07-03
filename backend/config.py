import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'campus.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWT_SECRET_KEY = 'campus-ai-secret-key-2026'
JWT_EXPIRATION_HOURS = 24
DEEPSEEK_API_KEY = ''
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
GEMINI_API_KEY = ''
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
