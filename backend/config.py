# config.py —— 校园达人 CampusAI 后端配置
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库路径
DATABASE = os.path.join(BASE_DIR, "campus.db")
DATABASE_PATH = DATABASE

# JWT 密钥（生产环境应改为环境变量）
SECRET_KEY = os.environ.get("CAMPUS_SECRET", "campus-ai-secret-key-2024")

# JWT 过期时间（小时）
TOKEN_EXPIRE_HOURS = 72

# C 模块可执行文件路径
C_LIB_PATH = os.path.join(BASE_DIR, "..", "c_lib", "campus_lib")
C_LIB_DIR = os.path.join(os.path.dirname(BASE_DIR), "c_lib")
C_LIB_EXECUTABLE = os.path.join(C_LIB_DIR, "campus_lib")
QUEUE_DATA_FILE = os.path.join(C_LIB_DIR, "queue_data.json")

# AI 模型 API 配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-pro"

# AI 请求超时（秒）
AI_REQUEST_TIMEOUT = 60

# 番茄钟配置
POMODORO_DURATIONS = {"short": 25, "normal": 50, "long": 90}

# 经验值配置
EXP_PER_POMODORO = 50
EXP_PER_RECORD = 5
LEVEL_UP_BASE = 200

# 成就/勋章定义
BADGES = {
    "first_pomodoro": {"name": "🍅 初次专注", "description": "完成第一次番茄钟", "icon": "🍅"},
    "ten_pomodoros": {"name": "⏰ 专注达人", "description": "累计完成 10 次番茄钟", "icon": "⏰"},
    "fifty_pomodoros": {"name": "🔥 专注大师", "description": "累计完成 50 次番茄钟", "icon": "🔥"},
    "first_record": {"name": "📝 初次记录", "description": "添加第一条时间记录", "icon": "📝"},
    "ten_records": {"name": "📊 时间管理者", "description": "累计添加 10 条时间记录", "icon": "📊"},
    "level_5": {"name": "⭐ 见习达人", "description": "达到等级 5", "icon": "⭐"},
    "level_10": {"name": "🌟 校园达人", "description": "达到等级 10", "icon": "🌟"},
    "ai_first": {"name": "🤖 AI 初体验", "description": "首次生成 AI 分析报告", "icon": "🤖"},
    "three_day_streak": {"name": "📅 连续三天", "description": "连续 3 天使用番茄钟", "icon": "📅"},
    "seven_day_streak": {"name": "🏆 一周全勤", "description": "连续 7 天使用番茄钟", "icon": "🏆"}
}
