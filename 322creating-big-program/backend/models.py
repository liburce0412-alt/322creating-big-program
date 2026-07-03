"""
SQLite 数据库模型 — 建表与基础操作
"""
import sqlite3
import os
from datetime import datetime


def get_db_path():
    """获取数据库文件路径"""
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'campus3ai.db')


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化所有数据表"""
    conn = get_connection()
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 时间记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL DEFAULT '学习',
            description TEXT DEFAULT '',
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_minutes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 番茄钟会话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_name TEXT DEFAULT '',
            work_duration INTEGER DEFAULT 25,
            break_duration INTEGER DEFAULT 5,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP,
            paused_at TIMESTAMP,
            completed_at TIMESTAMP,
            total_focus_seconds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 成就表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            icon TEXT DEFAULT '🏆',
            category TEXT DEFAULT 'general',
            condition_type TEXT NOT NULL,
            condition_value INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户-成就关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
            UNIQUE(user_id, achievement_id)
        )
    ''')

    # AI 对话历史
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # AI 分析报告
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_type TEXT DEFAULT 'daily',
            period_start DATE,
            period_end DATE,
            content TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            suggestions TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


def seed_achievements():
    """初始化默认成就数据"""
    achievements = [
        ('first_pomodoro', '初次专注', '完成第一个番茄钟', '🍅', 'pomodoro', 'count', 1),
        ('pomodoro_10', '专注新手', '累计完成 10 个番茄钟', '🔥', 'pomodoro', 'count', 10),
        ('pomodoro_50', '专注达人', '累计完成 50 个番茄钟', '💪', 'pomodoro', 'count', 50),
        ('pomodoro_100', '专注大师', '累计完成 100 个番茄钟', '👑', 'pomodoro', 'count', 100),
        ('streak_3', '连续三天', '连续 3 天使用番茄钟', '📅', 'streak', 'days', 3),
        ('streak_7', '连续一周', '连续 7 天使用番茄钟', '🌟', 'streak', 'days', 7),
        ('streak_30', '月度之星', '连续 30 天使用番茄钟', '🏅', 'streak', 'days', 30),
        ('record_10h', '学习十小时', '累计记录 10 小时学习时间', '⏰', 'time', 'hours', 10),
        ('record_50h', '学习五十小时', '累计记录 50 小时学习时间', '📚', 'time', 'hours', 50),
        ('first_ai_report', '初次分析', '生成第一份 AI 学习报告', '🤖', 'ai', 'count', 1),
        ('all_stats', '数据控', '查看所有统计数据', '📊', 'general', 'count', 1),
        ('early_bird', '早起鸟', '在早上 6 点前完成一个番茄钟', '🌅', 'special', 'count', 1),
    ]
    conn = get_connection()
    for ach in achievements:
        try:
            conn.execute(
                'INSERT OR IGNORE INTO achievements (code, name, description, icon, category, condition_type, condition_value) VALUES (?,?,?,?,?,?,?)',
                ach
            )
        except Exception:
            pass
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    seed_achievements()
    print("数据库初始化完成！")
