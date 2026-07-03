"""
ai_routes.py —— AI 分析 API
谢佳杨 负责

接口：
  GET  /api/ai/report         — 生成 AI 分析报告（调用 DeepSeek / Gemini）
  GET  /api/ai/reports        — 获取历史 AI 报告列表
  GET  /api/ai/reports/<id>   — 获取单份 AI 报告详情
  GET  /api/ai/chat-history   — 获取 AI 对话历史（通过 C 模块双向链表管理）
  POST /api/ai/chat           — 发送消息给 AI（对话功能）
  GET  /api/ai/models         — 获取可用的 AI 模型列表
"""
from flask import Blueprint, request, jsonify, g
from auth import login_required
from models import get_db
from config import DEEPSEEK_API_URL, DEEPSEEK_API_KEY, GEMINI_API_URL, GEMINI_API_KEY
from c_bridge import call_c_module
import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ai_bp = Blueprint("ai", __name__)


# ==================== 辅助函数 ====================

def _build_analysis_prompt(user_id: int, username: str) -> str:
    """
    根据用户的时间记录和番茄钟数据，构建分析报告的 prompt。
    从数据库提取统计数据，拼成自然语言。
    """
    db = get_db()

    # 时间记录总数
    total_records = db.execute(
        "SELECT COUNT(*) as cnt FROM time_records WHERE user_id = ?", (user_id,)
    ).fetchone()["cnt"]

    # 各类别时间分布
    categories = db.execute(
        """SELECT category, SUM(duration_min) as total_min, COUNT(*) as cnt
           FROM time_records WHERE user_id = ?
           GROUP BY category ORDER BY total_min DESC""",
        (user_id,)
    ).fetchall()

    # 番茄钟统计
    total_pomodoros = db.execute(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?", (user_id,)
    ).fetchone()["cnt"]
    total_focus_min = db.execute(
        "SELECT COALESCE(SUM(duration_min), 0) as total FROM pomodoro_sessions WHERE user_id = ?", (user_id,)
    ).fetchone()["total"]

    # 活跃天数
    active_days = db.execute(
        """SELECT COUNT(DISTINCT date(created_at)) as cnt
           FROM time_records WHERE user_id = ?""",
        (user_id,)
    ).fetchone()["cnt"]

    # 最近 7 天趋势
    recent = db.execute(
        """SELECT date(created_at) as day, SUM(duration_min) as total_min
           FROM time_records WHERE user_id = ?
           AND created_at >= date('now', '-7 days')
           GROUP BY date(created_at) ORDER BY day""",
        (user_id,)
    ).fetchall()

    db.close()

    # 构建 prompt
    cat_lines = "\n".join([
        f"  - {c['category']}: {c['total_min']} 分钟（{c['cnt']} 次）"
        for c in categories
    ]) if categories else "  （暂无记录）"

    recent_lines = "\n".join([
        f"  - {r['day']}: {r['total_min']} 分钟"
        for r in recent
    ]) if recent else "  （暂无记录）"

    prompt = f"""你是一位专业的时间管理教练，请根据以下用户的《校园达人》使用数据，生成一份个性化的时间分析报告。

## 用户 "{username}" 的数据

- 总时间记录数：{total_records} 条
- 总番茄钟次数：{total_pomodoros} 次
- 累计专注时长：{total_focus_min} 分钟
- 活跃天数：{active_days} 天

### 时间按类别分布：
{cat_lines}

### 最近 7 天趋势：
{recent_lines}

---

请生成一份包含以下内容的分析报告（Markdown 格式）：

1. **📊 时间使用概览**：总体评价用户的时间分配情况
2. **🔍 模式识别**：发现用户的时间使用规律和习惯
3. **💡 优化建议**：给出 3 条具体可操作的时间管理改进建议
4. **🎯 下周目标**：为用户设定 2-3 个合理的时间管理目标
5. **🌟 鼓励寄语**：给用户一句鼓励的话

请使用友好的语气，像一位贴心的学习伙伴。"""
    return prompt


def _call_deepseek(prompt: str) -> str:
    """调用 DeepSeek API 生成报告"""
    if not DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek API Key 未配置")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位专业的时间管理教练，名叫「校园达人AI助手」。请用中文回答，使用友好的语气。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }

    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_gemini(prompt: str) -> str:
    """调用 Gemini API 生成报告"""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API Key 未配置")

    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {"parts": [{"text": "你是一位专业的时间管理教练。请用中文回答。\n\n" + prompt}]}
        ]
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ==================== API 接口 ====================

@ai_bp.route("/ai/models", methods=["GET"])
def get_available_models():
    """获取可用的 AI 模型列表"""
    models = [
        {"id": "deepseek", "name": "DeepSeek", "icon": "🤖",
         "description": "DeepSeek-V3，高效且精准的AI模型",
         "available": bool(DEEPSEEK_API_KEY)},
        {"id": "gemini", "name": "Gemini", "icon": "🧠",
         "description": "Google Gemini Pro，全球领先的多模态模型",
         "available": bool(GEMINI_API_KEY)},
        {"id": "mock", "name": "演示模式", "icon": "📋",
         "description": "无需API Key，生成示例报告（答辩用）",
         "available": True},
    ]
    return jsonify({"models": models})


@ai_bp.route("/ai/report", methods=["GET"])
@login_required
def generate_report():
    """
    生成 AI 分析报告

    查询参数：
        ?model=deepseek   (可选，默认 deepseek，可选 gemini / mock)

    返回：
        {
            "report_id": 1,
            "model": "deepseek",
            "content": "## 📊 时间使用概览\n...",
            "generated_at": "2024-07-05 15:30:00"
        }
    """
    model_choice = request.args.get("model", "deepseek")

    # 构建分析 prompt
    prompt = _build_analysis_prompt(g.user_id, g.username)

    # 根据模型选择不同的生成方式
    content = ""
    try:
        if model_choice == "deepseek" and DEEPSEEK_API_KEY:
            content = _call_deepseek(prompt)
        elif model_choice == "gemini" and GEMINI_API_KEY:
            content = _call_gemini(prompt)
        elif model_choice == "mock":
            content = _generate_mock_report(g.username)
        else:
            # fallback 到 mock
            logger.warning(f"Model '{model_choice}' not available, using mock")
            content = _generate_mock_report(g.username)
            model_choice = "mock"
    except Exception as e:
        logger.error(f"AI API call failed: {e}")
        # 失败时也返回 mock 报告
        content = _generate_mock_report(g.username)
        model_choice = "mock"

    # 保存报告到数据库
    db = get_db()
    db.execute(
        "INSERT INTO ai_reports (user_id, report_content, model) VALUES (?, ?, ?)",
        (g.user_id, content, model_choice)
    )
    report_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 检测成就（首次使用 AI）
    from routes.pomodoro_routes import check_and_unlock_achievements
    new_achievements = check_and_unlock_achievements(g.user_id, db)

    db.commit()
    db.close()

    return jsonify({
        "report_id": report_id,
        "model": model_choice,
        "content": content,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "new_achievements": new_achievements
    })


@ai_bp.route("/ai/reports", methods=["GET"])
@login_required
def get_reports():
    """获取历史 AI 报告列表"""
    db = get_db()
    reports = db.execute(
        """SELECT id, model, substr(report_content, 1, 200) as preview, created_at
           FROM ai_reports WHERE user_id = ?
           ORDER BY created_at DESC LIMIT 20""",
        (g.user_id,)
    ).fetchall()
    db.close()
    return jsonify({"reports": [dict(r) for r in reports]})


@ai_bp.route("/ai/reports/<int:report_id>", methods=["GET"])
@login_required
def get_report_detail(report_id: int):
    """获取单份 AI 报告详情"""
    db = get_db()
    report = db.execute(
        "SELECT * FROM ai_reports WHERE id = ? AND user_id = ?",
        (report_id, g.user_id)
    ).fetchone()
    db.close()
    if not report:
        return jsonify({"error": "报告不存在"}), 404
    return jsonify(dict(report))


@ai_bp.route("/ai/chat-history", methods=["GET"])
@login_required
def get_chat_history():
    """
    获取 AI 对话历史

    通过 C 模块的双向链表管理对话记录。
    同时支持从数据库读取（fallback）。

    返回：
        {
            "messages": [
                {"id": 1, "role": "user", "content": "...", "created_at": "..."},
                ...
            ]
        }
    """
    # 优先从 C 模块获取
    result = call_c_module("linked_list", "to_array")
    if result.get("status") == "ok" and result.get("result"):
        c_messages = result["result"]
        if c_messages and len(c_messages) > 0:
            return jsonify({"messages": c_messages, "source": "c_module"})

    # fallback：从数据库读取
    db = get_db()
    messages = db.execute(
        """SELECT id, role, content, created_at
           FROM chat_history WHERE user_id = ?
           ORDER BY created_at ASC LIMIT 100""",
        (g.user_id,)
    ).fetchall()
    db.close()
    return jsonify({
        "messages": [dict(m) for m in messages],
        "source": "database"
    })


@ai_bp.route("/ai/chat", methods=["POST"])
@login_required
def chat_with_ai():
    """
    与 AI 对话（调用 DeepSeek）

    请求体 JSON：
        { "message": "你好，帮我分析一下..." }

    返回：
        { "reply": "...", "message_id": 123 }
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    # 保存用户消息到数据库
    db = get_db()
    db.execute(
        "INSERT INTO chat_history (user_id, role, content) VALUES (?, 'user', ?)",
        (g.user_id, user_message)
    )

    # 保存到 C 模块双向链表
    call_c_module("linked_list", "append", {
        "role": "user",
        "content": user_message,
        "timestamp": int(datetime.now().timestamp())
    })

    # 构建对话上下文
    recent = db.execute(
        """SELECT role, content FROM chat_history
           WHERE user_id = ? ORDER BY created_at DESC LIMIT 10""",
        (g.user_id,)
    ).fetchall()

    messages = [{"role": "system", "content": "你是一位贴心的校园学习助手，名叫「校园达人AI」。请用中文，语气友好、鼓励。"}]
    for msg in reversed(recent):
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 调用 AI
    reply = ""
    try:
        if DEEPSEEK_API_KEY:
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": messages, "temperature": 0.7, "max_tokens": 1024}
            resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"]
        else:
            reply = _mock_chat_reply(user_message)
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        reply = _mock_chat_reply(user_message)

    # 保存 AI 回复
    db.execute(
        "INSERT INTO chat_history (user_id, role, content) VALUES (?, 'assistant', ?)",
        (g.user_id, reply)
    )
    message_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.commit()
    db.close()

    # 同步到 C 模块链表
    call_c_module("linked_list", "append", {
        "role": "assistant",
        "content": reply,
        "timestamp": int(datetime.now().timestamp())
    })

    return jsonify({
        "reply": reply,
        "message_id": message_id
    })


# ==================== Mock 函数（演示用） ====================

def _generate_mock_report(username: str) -> str:
    """生成示例分析报告（无需 API Key，答辩演示用）"""
    return f"""## 📊 时间使用概览

{username} 同学，你好！根据你在校园达人上的使用数据，我看到你已经在时间管理方面迈出了重要的一步。

你的时间记录覆盖了多个类别，说明你的日常活动比较多元化。这是一个很好的开始！

---

## 🔍 模式识别

通过分析你的时间使用数据，我发现：

- **学习类活动**占据了主要时间，说明你对学业投入度很高
- **番茄钟的使用**帮助你保持了专注节奏，这是一个经过科学验证的高效方法
- **时间记录的习惯**正在逐步养成，坚持下去会看到更清晰的时间画像

---

## 💡 优化建议

1. **设定每日 MVP（最重要任务）**：每天开始前，先确定当天最重要的1-3件事，优先保证它们完成。这比试图完成所有事情要高效得多。

2. **利用碎片时间**：等车、排队、课间等碎片时间加起来可能有1-2小时/天。试试在这些时间处理小任务，比如背单词、复习笔记。

3. **建立「关机仪式」**：每天固定一个时间结束学习，花5分钟回顾今天完成了什么，写下明天的计划。这能帮你更好地「切换模式」并提高睡眠质量。

---

## 🎯 下周目标

- **目标1**：坚持每天至少完成 1 个番茄钟，给自己一个完整的 25 分钟专注时间
- **目标2**：在时间记录中尝试更细粒度的分类，帮助发现时间黑洞
- **目标3**：周末花10分钟回顾本周的时间统计报告，找到可以优化的地方

---

## 🌟 鼓励寄语

> "时间是最公平的，每个人每天都只有24小时。但如何使用这些时间，决定了你会成为什么样的人。你已经迈出了管理时间的第一步，坚持下去，你一定会成为更好的自己！💪"

---
*报告由 校园达人AI 自动生成*
"""


def _mock_chat_reply(user_message: str) -> str:
    """模拟 AI 对话回复（无需 API Key）"""
    keywords = {
        "时间": "时间管理的关键不是做更多事，而是做对的事。试试用「重要-紧急」四象限来区分任务优先级哦！📊",
        "专注": "提升专注力可以试试「番茄工作法」：25分钟专注 + 5分钟休息。你已经在用校园达人的番茄钟了，坚持下去！🍅",
        "学习": "学习效率 = 专注度 × 时间。与其低效学习3小时，不如高度专注1小时。记得用番茄钟来量化你的专注时光！📚",
        "目标": "设定目标时试试 SMART 原则：具体(Specific)、可衡量(Measurable)、可达成(Achievable)、相关(Relevant)、有时限(Time-bound)。🎯",
        "拖延": "拖延不是懒，往往是任务太大导致的焦虑。试试把大任务拆成小步骤，从最简单的开始，行动是战胜拖延最好的方式！💪",
        "习惯": "养成一个好习惯需要21天。先定一个小目标，比如每天记录时间连续7天，你就能看到明显的进步！📈",
        "休息": "好的休息是高效学习的一部分。试试「90分钟周期法则」：专注90分钟后休息15-20分钟。劳逸结合才能持久！😌",
    }

    for key, reply in keywords.items():
        if key in user_message:
            return reply

    return "你的问题很有价值！作为你的校园学习伙伴，我建议从记录时间开始 — 了解自己的时间都去哪了，是改善的第一步。有什么具体的方面想深入聊的吗？😊"
