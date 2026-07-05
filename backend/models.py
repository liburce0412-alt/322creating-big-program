# models.py — 数据库模型（番茄钟组需要的5张表 + 成就定义 + 经验/等级逻辑）
# 注：此文件是我们模块的最小依赖，完整的 models.py 由李恩琪/余欣泽维护

import sqlite3
from datetime import datetime
import config


# ============================================================
# 数据库连接
# ============================================================

def get_db():
    """获取数据库连接（row_factory 使得查询结果可以用 dict 风格访问）"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化数据库表（由 app.py 启动时调用一次）"""
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS time_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            duration_min INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            duration_min INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exp_gained INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, badge_id)
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS ai_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_content TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()


# ============================================================
# 经验值与等级系统
# ============================================================

def calculate_exp(duration_min: int) -> int:
    """
    根据番茄钟时长计算经验值
    - 25分钟: 25 EXP
    - 50分钟: 60 EXP（深度专注加成）
    - 90分钟: 120 EXP（马拉松加成）
    - 其他: 按分钟数 x1.0
    """
    if duration_min >= 90:
        return 120
    elif duration_min >= 50:
        return 60
    elif duration_min >= 25:
        return 25
    else:
        return duration_min


def calculate_level(exp: int) -> int:
    """
    经验值 → 等级换算
    level = floor(sqrt(exp / 100)) + 1
    Lv.1:    0 -   99 EXP
    Lv.2:  100 -  399 EXP
    Lv.3:  400 -  899 EXP
    Lv.4:  900 - 1599 EXP
    Lv.5: 1600 - 2499 EXP
    ...
    Lv.10: 8100 - 9999 EXP
    """
    import math
    if exp < 0:
        exp = 0
    return int(math.sqrt(exp / 100.0)) + 1


def exp_to_next_level(level: int) -> int:
    """返回升到下一级所需的总经验值"""
    return (level) * (level) * 100


# ============================================================
# 成就/勋章定义
# ============================================================

ACHIEVEMENT_DEFINITIONS = {
    'first_pomodoro': {
        'name': '初次专注',
        'description': '完成第1次番茄钟',
        'icon': '🍅',
    },
    'pomodoro_5': {
        'name': '专注新手',
        'description': '累计完成5次番茄钟',
        'icon': '⭐',
    },
    'pomodoro_10': {
        'name': '专注达人',
        'description': '累计完成10次番茄钟',
        'icon': '🌟',
    },
    'pomodoro_25': {
        'name': '专注大师',
        'description': '累计完成25次番茄钟',
        'icon': '💎',
    },
    'pomodoro_50': {
        'name': '专注传奇',
        'description': '累计完成50次番茄钟',
        'icon': '👑',
    },
    'focus_marathon': {
        'name': '马拉松专注',
        'description': '完成一次90分钟的番茄钟',
        'icon': '🏃',
    },
    'focus_master': {
        'name': '深度专注者',
        'description': '累计完成10次50分钟以上的番茄钟',
        'icon': '🧠',
    },
    'level_5': {
        'name': '成长之路',
        'description': '等级达到 Lv.5',
        'icon': '📈',
    },
    'level_10': {
        'name': '巅峰之路',
        'description': '等级达到 Lv.10',
        'icon': '🏆',
    },
    'early_bird': {
        'name': '早起鸟儿',
        'description': '在早上8:00之前完成一次番茄钟',
        'icon': '🌅',
    },
    'night_owl': {
        'name': '夜猫子',
        'description': '在晚上22:00之后完成一次番茄钟',
        'icon': '🦉',
    },
    'exp_1000': {
        'name': '经验积累者',
        'description': '累计获得1000点经验值',
        'icon': '📊',
    },
    'exp_5000': {
        'name': '经验收割机',
        'description': '累计获得5000点经验值',
        'icon': '🚀',
    },
}


# ============================================================
# 成就检查函数
# ============================================================

def check_achievements(user_id: int, conn) -> list:
    """
    检查用户是否满足新成就条件，返回新解锁的成就列表。
    该函数在每次番茄钟完成后调用。

    返回值: [{'badge_id': 'xxx', 'name': '...', 'description': '...', 'icon': '...'}, ...]
    """
    cursor = conn.cursor()

    # 获取已有成就
    existing = set(
        row['badge_id']
        for row in cursor.execute(
            "SELECT badge_id FROM achievements WHERE user_id = ?", (user_id,)
        ).fetchall()
    )

    # 获取用户当前状态
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return []

    total_pomodoros = cursor.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (user_id,)
    ).fetchone()['cnt']

    total_exp = user['exp']
    current_level = user['level']
    current_hour = datetime.now().hour

    # 检查长番茄钟
    long_pomodoros = cursor.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ? AND duration_min >= 50",
        (user_id,)
    ).fetchone()['cnt']

    has_marathon = cursor.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ? AND duration_min >= 90",
        (user_id,)
    ).fetchone()['cnt'] > 0

    # 检查各项成就条件
    conditions = {
        'first_pomodoro': total_pomodoros >= 1,
        'pomodoro_5': total_pomodoros >= 5,
        'pomodoro_10': total_pomodoros >= 10,
        'pomodoro_25': total_pomodoros >= 25,
        'pomodoro_50': total_pomodoros >= 50,
        'focus_marathon': has_marathon,
        'focus_master': long_pomodoros >= 10,
        'level_5': current_level >= 5,
        'level_10': current_level >= 10,
        'early_bird': current_hour < 8,
        'night_owl': current_hour >= 22,
        'exp_1000': total_exp >= 1000,
        'exp_5000': total_exp >= 5000,
    }

    # 筛选出新的成就
    new_achievements = []
    for badge_id, met in conditions.items():
        if met and badge_id not in existing:
            definition = ACHIEVEMENT_DEFINITIONS.get(badge_id, {})
            cursor.execute(
                "INSERT OR IGNORE INTO achievements (user_id, badge_id) VALUES (?, ?)",
                (user_id, badge_id)
            )
            new_achievements.append({
                'badge_id': badge_id,
                'name': definition.get('name', badge_id),
                'description': definition.get('description', ''),
                'icon': definition.get('icon', '🏅'),
            })

    conn.commit()
    return new_achievements


# ============================================================
# 便捷查询函数
# ============================================================

def get_user_pomodoro_count(user_id: int, conn) -> int:
    """获取用户总番茄钟次数"""
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    return row['cnt'] if row else 0


def get_user_achievements(user_id: int, conn) -> list:
    """获取用户所有已解锁的成就"""
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT badge_id, unlocked_at FROM achievements WHERE user_id = ? ORDER BY unlocked_at DESC",
        (user_id,)
    ).fetchall()
    result = []
    for row in rows:
        definition = ACHIEVEMENT_DEFINITIONS.get(row['badge_id'], {})
        result.append({
            'badge_id': row['badge_id'],
            'name': definition.get('name', row['badge_id']),
            'description': definition.get('description', ''),
            'icon': definition.get('icon', '🏅'),
            'unlocked_at': row['unlocked_at'],
        })
    return result
