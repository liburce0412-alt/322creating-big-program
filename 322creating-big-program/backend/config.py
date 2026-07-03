"""
Flask 应用配置
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'campus3ai-secret-key-2024')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-2024')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 小时

    # SQLite 数据库
    DATABASE = os.path.join(BASE_DIR, 'data', 'campus3ai.db')

    # C 模块路径
    C_LIB_DIR = os.path.join(os.path.dirname(BASE_DIR), 'c_lib')

    # AI 配置（模拟，实际项目可接真实 API）
    AI_ENABLED = True
    AI_MODEL = 'local-analyzer'

    # 番茄钟默认配置
    POMODORO_WORK_MINUTES = 25
    POMODORO_SHORT_BREAK_MINUTES = 5
    POMODORO_LONG_BREAK_MINUTES = 15
    POMODORO_LONG_BREAK_INTERVAL = 4  # 每 4 个番茄钟后长休息


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
