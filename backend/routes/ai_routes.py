# ai_routes.py — AI 分析 API 路由
# 负责：GET /api/ai/report         — 生成 AI 分析报告（DeepSeek / Gemini）
#       GET /api/ai/chat-history   — 获取对话历史（C 双向链表存储）
#       POST /api/ai/queue-status  — 查看 AI 请求队列状态

import json
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g

import config
from models import get_db
from c_bridge import (
    queue_enqueue, queue_dequeue, queue_peek,
    queue_size, queue_is_empty, queue_clear,
    call_c_module
)

ai_bp = Blueprint('ai', __name__)


# ============================================================
# 辅助函数
# ============================================================

def _get_current_user_id():
    """获取当前用户 ID（同 pomodoro_routes.py 中的实现）"""
    if hasattr(g, 'user_id') and g.user_id:
        return g.user_id
    import jwt
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            return payload.get('user_id')
        except Exception:
            return None
    return None


def _fetch_user_context(user_id: int) -> dict:
    """
    获取用户的时间数据上下文（用于构建 AI 提示词）。
    返回最近 7 天的时间记录和番茄钟数据。
    """
    conn = get_db()
    cursor = conn.cursor()

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    # 时间记录汇总
    time_records = cursor.execute(
        "SELECT category, SUM(duration_min) as total_min, COUNT(*) as count "
        "FROM time_records WHERE user_id = ? AND created_at >= ? "
        "GROUP BY category ORDER BY total_min DESC",
        (user_id, seven_days_ago)
    ).fetchall()

    # 番茄钟汇总
    pomodoro_stats = cursor.execute(
        "SELECT COUNT(*) as total, SUM(duration_min) as total_min, "
        "AVG(duration_min) as avg_min "
        "FROM pomodoro_sessions WHERE user_id = ? AND completed_at >= ?",
        (user_id, seven_days_ago)
    ).fetchone()

    # 每日番茄钟趋势
    daily_pomodoros = cursor.execute(
        "SELECT DATE(completed_at) as date, COUNT(*) as count, "
        "SUM(duration_min) as total_min "
        "FROM pomodoro_sessions WHERE user_id = ? AND completed_at >= ? "
        "GROUP BY DATE(completed_at) ORDER BY date",
        (user_id, seven_days_ago)
    ).fetchall()

    # 用户信息
    user = cursor.execute(
        "SELECT username, level, exp FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    conn.close()

    return {
        'username': user['username'] if user else '未知',
        'level': user['level'] if user else 1,
        'exp': user['exp'] if user else 0,
        'time_records': [dict(r) for r in time_records],
        'pomodoro_stats': dict(pomodoro_stats) if pomodoro_stats else {},
        'daily_pomodoros': [dict(d) for d in daily_pomodoros],
    }


def _build_analysis_prompt(context: dict) -> str:
    """
    根据用户数据构建 AI 分析提示词。
    """
    username = context['username']
    level = context['level']
    exp = context['exp']

    time_records_str = '\n'.join(
        f"- {r['category']}: {r['total_min']} 分钟（{r['count']}次）"
        for r in context['time_records']
    ) if context['time_records'] else '（暂无时间记录数据）'

    pomo = context['pomodoro_stats']
    pomo_str = (
        f"总计 {pomo.get('total', 0)} 次番茄钟，"
        f"累计 {pomo.get('total_min', 0)} 分钟，"
        f"平均每次 {pomo.get('avg_min', 0):.0f} 分钟"
    ) if pomo else '（暂无番茄钟数据）'

    daily_str = '\n'.join(
        f"- {d['date']}: {d['count']} 次番茄钟，共 {d['total_min']} 分钟"
        for d in context['daily_pomodoros']
    ) if context['daily_pomodoros'] else '（暂无每日数据）'

    prompt = f"""你是一个时间管理分析助手。请根据以下用户数据，生成一份简洁的时间管理分析报告。

【用户信息】
- 用户名: {username}
- 等级: Lv.{level}
- 总经验值: {exp}

【近7天时间分配】
{time_records_str}

【番茄钟统计】
{pomo_str}

【每日番茄钟趋势】
{daily_str}

请从以下几个方面给出分析（总计 200-400 字）：
1. 时间分配是否合理？有哪些可以优化的地方？
2. 专注趋势如何？番茄钟使用习惯评价。
3. 给出 2-3 条具体的改进建议。
4. 一句鼓励的话。

请用中文输出，语气友好、鼓励为主。"""
    return prompt


# ============================================================
# 调用 DeepSeek API
# ============================================================

def call_deepseek_api(prompt: str) -> dict:
    """
    调用 DeepSeek API 生成分析报告。

    参数:
        prompt: 分析提示词

    返回:
        {"status": "ok", "content": "...", "model": "deepseek-chat"}
        或 {"status": "error", "message": "..."}
    """
    headers = {
        'Authorization': f'Bearer {config.DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': config.DEEPSEEK_MODEL,
        'messages': [
            {
                'role': 'system',
                'content': '你是一个专业的时间管理分析助手，擅长通过数据给出友好的建议。'
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ],
        'temperature': 0.7,
        'max_tokens': 1024,
        'stream': False,
    }

    try:
        resp = requests.post(
            config.DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=config.AI_REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            content = data['choices'][0]['message']['content']
            return {
                'status': 'ok',
                'content': content,
                'model': config.DEEPSEEK_MODEL,
            }
        else:
            return {
                'status': 'error',
                'message': f'DeepSeek API 返回错误 ({resp.status_code}): {resp.text[:500]}'
            }
    except requests.exceptions.Timeout:
        return {'status': 'error', 'message': 'DeepSeek API 请求超时'}
    except requests.exceptions.ConnectionError:
        return {'status': 'error', 'message': '无法连接到 DeepSeek API，请检查网络'}
    except Exception as e:
        return {'status': 'error', 'message': f'DeepSeek API 调用异常: {str(e)}'}


# ============================================================
# 调用 Gemini API
# ============================================================

def call_gemini_api(prompt: str) -> dict:
    """
    调用 Google Gemini API 生成分析报告（备用模型）。

    参数:
        prompt: 分析提示词

    返回:
        {"status": "ok", "content": "...", "model": "gemini-pro"}
        或 {"status": "error", "message": "..."}
    """
    url = f'{config.GEMINI_API_URL}?key={config.GEMINI_API_KEY}'
    payload = {
        'contents': [
            {
                'parts': [
                    {
                        'text': (
                            '你是一个专业的时间管理分析助手，擅长通过数据给出友好的建议。\n\n'
                            + prompt
                        )
                    }
                ]
            }
        ],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 1024,
        },
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            timeout=config.AI_REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Gemini 响应格式与 DeepSeek 不同，需要适配
            candidates = data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                text = ''.join(p.get('text', '') for p in parts)
                return {
                    'status': 'ok',
                    'content': text,
                    'model': config.GEMINI_MODEL,
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Gemini API 返回了空的响应内容'
                }
        elif resp.status_code == 429:
            return {'status': 'error', 'message': 'Gemini API 配额已用完，请稍后再试'}
        else:
            return {
                'status': 'error',
                'message': f'Gemini API 返回错误 ({resp.status_code}): {resp.text[:500]}'
            }
    except requests.exceptions.Timeout:
        return {'status': 'error', 'message': 'Gemini API 请求超时'}
    except requests.exceptions.ConnectionError:
        return {'status': 'error', 'message': '无法连接到 Gemini API，请检查网络'}
    except Exception as e:
        return {'status': 'error', 'message': f'Gemini API 调用异常: {str(e)}'}


# ============================================================
# 统一的 AI 调用入口（带模型选择 + 队列管理）
# ============================================================

def call_ai_model(prompt: str, model: str = 'deepseek') -> dict:
    """
    统一的 AI 模型调用入口。

    参数:
        prompt: 分析提示词
        model: 模型选择 — "deepseek"（默认）或 "gemini"（备用）

    返回:
        {"status": "ok", "content": "...", "model": "..."}
        如果首选模型失败且为 deepseek，会自动尝试 gemini 作为 fallback。
    """
    # 首选模型
    if model == 'deepseek':
        result = call_deepseek_api(prompt)
        if result['status'] == 'ok':
            return result
        # DeepSeek 失败 → 自动切换到 Gemini 作为备用
        fallback_result = call_gemini_api(prompt)
        if fallback_result['status'] == 'ok':
            fallback_result['fallback'] = True
            fallback_result['fallback_reason'] = result.get('message', 'DeepSeek 不可用')
            return fallback_result
        # 两个都失败了
        return {
            'status': 'error',
            'message': f'所有 AI 模型均不可用。DeepSeek: {result.get("message")}; Gemini: {fallback_result.get("message")}'
        }

    elif model == 'gemini':
        result = call_gemini_api(prompt)
        if result['status'] == 'ok':
            return result
        # Gemini 失败 → 自动切换到 DeepSeek
        fallback_result = call_deepseek_api(prompt)
        if fallback_result['status'] == 'ok':
            fallback_result['fallback'] = True
            fallback_result['fallback_reason'] = result.get('message', 'Gemini 不可用')
            return fallback_result
        return {
            'status': 'error',
            'message': f'所有 AI 模型均不可用。Gemini: {result.get("message")}; DeepSeek: {fallback_result.get("message")}'
        }

    else:
        return {'status': 'error', 'message': f'不支持的模型: {model}。支持: deepseek, gemini'}


# ============================================================
# 通过 C 队列模块管理 AI 请求
# ============================================================

def process_ai_queue() -> dict:
    """
    处理 AI 请求队列：从 C 队列模块中逐条取出请求并调用 AI。
    每次调用最多处理 1 条（避免单次请求超时）。

    队列中的每项格式:
        {"user_id": 1, "prompt": "...", "model": "deepseek"}

    返回:
        {"status": "ok", "processed": 1, "results": [...]}
        或 {"status": "ok", "processed": 0, "message": "队列为空"}
    """
    if queue_is_empty():
        return {'status': 'ok', 'processed': 0, 'message': '队列为空'}

    # 从 C 队列中取出一个请求
    result = queue_dequeue()
    if result.get('status') != 'ok' or not result.get('result'):
        return {'status': 'error', 'message': '从队列取数据失败'}

    try:
        item = json.loads(result['result']) if isinstance(result['result'], str) else result['result']
    except (json.JSONDecodeError, TypeError):
        return {'status': 'error', 'message': '队列中的数据格式错误'}

    user_id = item.get('user_id')
    prompt = item.get('prompt', '')
    model = item.get('model', 'deepseek')

    # 调用 AI
    ai_result = call_ai_model(prompt, model)

    # 保存到数据库
    if ai_result.get('status') == 'ok' and user_id:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO ai_reports (user_id, report_content, model) VALUES (?, ?, ?)",
                (user_id, ai_result['content'], ai_result.get('model', model))
            )
            # 同时写入 chat_history（供 C 双向链表查询）
            conn.execute(
                "INSERT INTO chat_history (user_id, role, content) VALUES (?, 'assistant', ?)",
                (user_id, ai_result['content'])
            )
            conn.commit()
        except Exception as e:
            pass  # 保存失败不影响返回结果
        finally:
            conn.close()

    return {
        'status': 'ok',
        'processed': 1,
        'results': [ai_result],
        'remaining_in_queue': queue_size(),
    }


# ============================================================
# GET /api/ai/report — 生成 AI 分析报告（核心接口）
# ============================================================

@ai_bp.route('/api/ai/report', methods=['GET'])
def generate_ai_report():
    """
    为当前用户生成 AI 时间管理分析报告。

    查询参数:
        model — 模型选择: "deepseek"（默认）或 "gemini"

    响应:
        {
            "status": "ok",
            "report": {
                "content": "AI 分析内容...",
                "model": "deepseek-chat",
                "generated_at": "2025-07-05 15:00:00"
            }
        }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    model = request.args.get('model', 'deepseek').lower()
    if model not in ('deepseek', 'gemini'):
        return jsonify({'status': 'error', 'message': 'model 参数只能为 deepseek 或 gemini'}), 400

    # 1. 获取用户数据并构建提示词
    context = _fetch_user_context(user_id)
    prompt = _build_analysis_prompt(context)

    # 2. 将请求加入 C 队列（排队管理）
    queue_item = {
        'user_id': user_id,
        'prompt': prompt,
        'model': model,
    }
    enqueue_result = queue_enqueue(queue_item)

    # 3. 立即处理队列（取出并调用 AI）
    process_result = process_ai_queue()

    # 4. 返回结果
    if process_result.get('status') != 'ok':
        return jsonify({'status': 'error', 'message': process_result.get('message', 'AI 处理失败')}), 500

    results = process_result.get('results', [])
    if not results:
        return jsonify({'status': 'error', 'message': '未能生成报告'}), 500

    ai_output = results[0]

    if ai_output.get('status') != 'ok':
        return jsonify({
            'status': 'error',
            'message': ai_output.get('message', 'AI 调用失败'),
        }), 500

    # 5. 保存到数据库
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO ai_reports (user_id, report_content, model) VALUES (?, ?, ?)",
            (user_id, ai_output['content'], ai_output.get('model', model))
        )
        conn.commit()
        report_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'保存报告失败: {str(e)}'}), 500
    finally:
        conn.close()

    return jsonify({
        'status': 'ok',
        'report': {
            'id': report_id,
            'content': ai_output['content'],
            'model': ai_output.get('model', model),
            'fallback': ai_output.get('fallback', False),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    })


# ============================================================
# GET /api/ai/chat-history — AI 对话历史（C 双向链表存储）
# ============================================================

@ai_bp.route('/api/ai/chat-history', methods=['GET'])
def get_chat_history():
    """
    获取当前用户的 AI 对话历史。

    查询参数:
        limit  — 返回条数（默认 20）
        offset — 偏移量（默认 0）

    说明:
        对话历史在数据库中以 chat_history 表存储（按时间排序即为链表顺序）。
        前端可以请求 C 模块的 linked_list 来以双向链表结构遍历，
        也可以用本接口直接分页查询。

    响应:
        {
            "status": "ok",
            "total": 50,
            "messages": [
                {"id": 1, "role": "user", "content": "...", "created_at": "..."},
                {"id": 2, "role": "assistant", "content": "...", "created_at": "..."},
                ...
            ],
            "linked_list_view": { ... }   // 可选：C 双向链表视角
        }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    use_linked_list = request.args.get('linked_list', '0') == '1'

    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    conn = get_db()
    cursor = conn.cursor()

    try:
        total = cursor.execute(
            "SELECT COUNT(*) as cnt FROM chat_history WHERE user_id = ?",
            (user_id,)
        ).fetchone()['cnt']

        rows = cursor.execute(
            "SELECT id, role, content, created_at FROM chat_history "
            "WHERE user_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        ).fetchall()

        messages = [dict(row) for row in rows]

        response_data = {
            'status': 'ok',
            'total': total,
            'limit': limit,
            'offset': offset,
            'messages': messages,
        }

        # 如果请求链表视图，通过 C 模块获取链表结构
        if use_linked_list:
            linked_result = call_c_module('linked_list', {
                'command': 'to_array',
                'user_id': user_id,
            })
            response_data['linked_list_view'] = linked_result

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()


# ============================================================
# POST /api/ai/chat — 发送消息给 AI（对话接口）
# ============================================================

@ai_bp.route('/api/ai/chat', methods=['POST'])
def chat_with_ai():
    """
    与 AI 对话（用于 AI 报告页面的交互式问答）。

    请求体:
        {
            "message": "如何提高我的专注力？",
            "model": "deepseek"   // 可选，默认 deepseek
        }

    响应:
        {
            "status": "ok",
            "reply": "AI 回复内容...",
            "model": "deepseek-chat"
        }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    data = request.get_json(silent=True) or {}
    user_message = data.get('message', '').strip()
    model = data.get('model', 'deepseek').lower()

    if not user_message:
        return jsonify({'status': 'error', 'message': '请提供 message'}), 400
    if model not in ('deepseek', 'gemini'):
        return jsonify({'status': 'error', 'message': 'model 参数只能为 deepseek 或 gemini'}), 400

    # 1. 保存用户消息到 chat_history
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, user_message)
        )
        conn.commit()
    except Exception as e:
        pass
    finally:
        conn.close()

    # 2. 获取最近的对话上下文（最近 10 条）
    conn = get_db()
    cursor = conn.cursor()
    recent = cursor.execute(
        "SELECT role, content FROM chat_history WHERE user_id = ? "
        "ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()
    conn.close()

    # 构建对话消息列表
    messages = [
        {'role': 'system', 'content': '你是一个友好的时间管理助手，帮助用户提升效率、养成好习惯。请用中文回答。'}
    ]
    for msg in reversed(recent):
        messages.append({'role': msg['role'], 'content': msg['content']})

    # 3. 入队 + 调用 AI
    prompt_for_ai = json.dumps(messages, ensure_ascii=False)
    queue_item = {
        'user_id': user_id,
        'prompt': user_message,
        'model': model,
        'context': prompt_for_ai,  # 带上下文的完整提示词
    }
    queue_enqueue(queue_item)

    # 直接调用 AI（对话场景不适合排队等待）
    # 构建完整上下文提示词
    context_str = '\n'.join(
        f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in messages
    )
    ai_result = call_ai_model(
        f"以下是对话历史：\n{context_str}\n\n请根据以上对话历史，回答用户最后的问题。保持友好、简洁。",
        model
    )

    if ai_result.get('status') != 'ok':
        return jsonify({
            'status': 'error',
            'message': ai_result.get('message', 'AI 调用失败')
        }), 500

    # 4. 保存 AI 回复
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, 'assistant', ?)",
            (user_id, ai_result['content'])
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

    return jsonify({
        'status': 'ok',
        'reply': ai_result['content'],
        'model': ai_result.get('model', model),
        'fallback': ai_result.get('fallback', False),
    })


# ============================================================
# GET /api/ai/queue-status — 查看队列状态
# ============================================================

@ai_bp.route('/api/ai/queue-status', methods=['GET'])
def ai_queue_status():
    """查看当前 AI 请求队列的状态。"""
    size = queue_size()
    is_empty = queue_is_empty()

    status_data = {
        'status': 'ok',
        'queue_size': size,
        'is_empty': is_empty,
    }

    if not is_empty:
        peek_result = queue_peek()
        status_data['next_request'] = peek_result.get('result') if peek_result.get('status') == 'ok' else None

    return jsonify(status_data)
