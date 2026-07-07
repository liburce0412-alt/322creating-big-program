"""
config.py —— 校园达人 CampusAI 后端配置
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SQLite 数据库路径
DATABASE = os.path.join(BASE_DIR, "campus.db")

# JWT 密钥（生产环境应改为环境变量）
SECRET_KEY = os.environ.get("CAMPUS_SECRET", "campus-ai-secret-key-2024")

# JWT 过期时间（小时）
TOKEN_EXPIRE_HOURS = 72

# C 模块可执行文件路径
C_LIB_PATH = os.path.join(BASE_DIR, "..", "c_lib", "campus_lib")

# AI 模型 API 配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-22e545016e4f45a68bf5daa4d94f1c28")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 番茄钟配置
POMODORO_DURATIONS = {
    "short": 25,    # 25 分钟
    "normal": 50,   # 50 分钟
    "long": 90      # 90 分钟
}

# 经验值配置
EXP_PER_POMODORO = 50        # 每次番茄钟完成获得经验
EXP_PER_RECORD = 5           # 每次时间记录获得经验
LEVEL_UP_BASE = 200          # 初始升级所需经验（逐级递增 50%）

# 成就/勋章定义
BADGES = {
    "first_pomodoro": {
        "name": "🍅 初次专注",
        "description": "完成第一次番茄钟",
        "icon": "🍅"
    },
    "ten_pomodoros": {
        "name": "⏰ 专注达人",
        "description": "累计完成 10 次番茄钟",
        "icon": "⏰"
    },
    "fifty_pomodoros": {
        "name": "🔥 专注大师",
        "description": "累计完成 50 次番茄钟",
        "icon": "🔥"
    },
    "first_record": {
        "name": "📝 初次记录",
        "description": "添加第一条时间记录",
        "icon": "📝"
    },
    "ten_records": {
        "name": "📊 时间管理者",
        "description": "累计添加 10 条时间记录",
        "icon": "📊"
    },
    "level_5": {
        "name": "⭐ 见习达人",
        "description": "达到等级 5",
        "icon": "⭐"
    },
    "level_10": {
        "name": "🌟 校园达人",
        "description": "达到等级 10",
        "icon": "🌟"
    },
    "ai_first": {
        "name": "🤖 AI 初体验",
        "description": "首次生成 AI 分析报告",
        "icon": "🤖"
    },
    "three_day_streak": {
        "name": "📅 连续三天",
        "description": "连续 3 天使用番茄钟",
        "icon": "📅"
    },
    "seven_day_streak": {
        "name": "🏆 一周全勤",
        "description": "连续 7 天使用番茄钟",
        "icon": "🏆"
    }
}
