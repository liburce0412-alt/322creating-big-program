# config.py — 配置文件（番茄钟组需要的配置项）
# 注：完整的 config.py 由李恩琪/余欣泽维护，这里只包含我们模块需要的配置

import os

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(os.path.dirname(BASE_DIR), 'campus_ai.db')

# Flask 密钥（JWT 签名用）
SECRET_KEY = 'campus-ai-secret-key-change-in-production'

# C 模块路径
C_LIB_DIR = os.path.join(os.path.dirname(BASE_DIR), 'c_lib')
C_LIB_EXECUTABLE = os.path.join(C_LIB_DIR, 'campus_lib')
QUEUE_DATA_FILE = os.path.join(C_LIB_DIR, 'queue_data.json')

# DeepSeek API
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'your-deepseek-api-key')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = 'deepseek-chat'

# C 模块可执行文件路径
C_LIB_PATH = os.path.join(BASE_DIR, "..", "c_lib", "campus_lib.exe")
# Gemini API (备用)
# Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'your-gemini-api-key')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent'
GEMINI_MODEL = 'gemini-pro'

# AI 请求超时（秒）
AI_REQUEST_TIMEOUT = 60
