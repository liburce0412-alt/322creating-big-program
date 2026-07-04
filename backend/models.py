"""
models.py —— SQLite 数据库模型定义 & 初始化
"""
import sqlite3
import os
from config import DATABASE


def get_db():
    """获取数据库连接（开启 WAL 模式 + 外键约束）"""
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row      # 查询结果可用 dict-like 访问
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库：创建所有表（如果不存在）"""
    conn = get_db()
    cursor = conn.cursor()

    # ========== 用户表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password_hash TEXT   NOT NULL,
            level       INTEGER DEFAULT 1,
            exp         INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========== 时间记录表 ==========
    # 柳比歇夫时间统计法的核心数据
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT,
            duration_min INTEGER NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ========== 番茄钟完成记录表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            duration_min INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exp_gained  INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ========== 成就/勋章表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            badge_id    TEXT    NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, badge_id)
        )
    """)

    # ========== AI 对话历史表（双向链表结构） ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            role        TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ========== AI 分析报告表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            report_content TEXT NOT NULL,
            model       TEXT    DEFAULT 'deepseek',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_records_user ON time_records(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_records_category ON time_records(user_id, category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_records_date ON time_records(user_id, created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pomodoro_user ON pomodoro_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id)")

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully.")


if __name__ == "__main__":
    # 直接运行则初始化数据库
    init_db()
