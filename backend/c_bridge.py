# c_bridge.py — Python 调用 C 模块的桥接接口
# 通过 subprocess 运行编译好的 C 可执行文件，stdin/stdout 传递 JSON

import subprocess
import json
import os
import config


def call_c_module(module_name: str, json_input: dict) -> dict:
    """
    调用 C 模块并返回 JSON 结果。

    参数:
        module_name: C 模块名（如 "queue", "stack", "kmp" 等）
        json_input: 要传递给 C 模块的 JSON 数据（dict）

    返回:
        C 模块 stdout 输出的 JSON 解析后的 dict

    工作流程:
        1. 将 json_input 序列化为 JSON 字符串
        2. 通过 subprocess 运行 C 可执行文件
        3. 将 JSON 字符串写入 stdin
        4. 从 stdout 读取 JSON 响应
        5. 解析并返回

    C 模块约定:
        - 第一个命令行参数是模块名
        - 从 stdin 读取一行 JSON 作为输入
        - 向 stdout 输出一行 JSON 作为结果
        - 向 stderr 输出调试日志
        - 返回码 0 = 成功，非 0 = 错误
    """
    executable = config.C_LIB_EXECUTABLE

    if not os.path.exists(executable):
        return {
            'status': 'error',
            'message': f'C 模块可执行文件不存在: {executable}。请先运行 make 编译。'
        }

    json_str = json.dumps(json_input, ensure_ascii=False)

    try:
        proc = subprocess.run(
            [executable, module_name],
            input=json_str,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=config.C_LIB_DIR,
        )

        if proc.returncode != 0:
            return {
                'status': 'error',
                'message': f'C 模块返回错误 (code={proc.returncode}): {proc.stderr.strip()}'
            }

        if not proc.stdout.strip():
            return {
                'status': 'error',
                'message': 'C 模块没有返回任何输出'
            }

        try:
            result = json.loads(proc.stdout.strip())
            return result
        except json.JSONDecodeError as e:
            return {
                'status': 'error',
                'message': f'C 模块返回了无效的 JSON: {e}',
                'raw_output': proc.stdout.strip(),
            }

    except subprocess.TimeoutExpired:
        return {
            'status': 'error',
            'message': f'C 模块 ({module_name}) 执行超时（10秒）'
        }
    except FileNotFoundError:
        return {
            'status': 'error',
            'message': f'无法找到 C 模块可执行文件: {executable}'
        }
    except Exception as e:
        logger.error(f"Unexpected error calling C module: {e}")
        return {"status": "error", "error": str(e)}


def _python_fallback(module: str, action: str, data: dict) -> dict:
    """
    Python 版本的兜底实现（当 C 模块不可用时自动切换）。
    确保即使 C 编译有问题，后端也能正常运行和调试。
    """
    data = data or {}

    # ---- linked_list fallback ----
    if module == "linked_list":
        return _linked_list_fallback(action, data)

    # ---- queue fallback ----
    if module == "queue":
        return _queue_fallback(action, data)

    # ---- binary_search fallback ----
    if module == "binary_search":
        return _binary_search_fallback(action, data)

    # ---- stack fallback ----
    if module == "stack":
        return _stack_fallback(action, data)

    # ---- kmp fallback ----
    if module == "kmp":
        return _kmp_fallback(action, data)

    # ---- hash_table fallback ----
    if module == "hash_table":
        return _hash_table_fallback(action, data)

    # ---- 其他模块（暂未实现 fallback）----
    return {"status": "error", "error": f"Module '{module}' not available (no C binary and no Python fallback)"}


# ==================== Python Fallback 实现 ====================

# 内存中的简易存储（仅供 fallback 使用）
_fb_linked_list = []    # list of dict
_fb_queue = []          # list of dict


def _hash_table_fallback(action: str, data: dict) -> dict:
    """哈希表的 Python fallback（快速检索用户/记录）"""
    global _fb_hash_table

    if action == "insert":
        key = str(data.get("key", ""))
        value = data.get("value", {})
        _fb_hash_table[key] = value
        return {"status": "ok", "result": {"inserted": True, "size": len(_fb_hash_table)}}

    if action == "search":
        key = str(data.get("key", ""))
        if key in _fb_hash_table:
            return {"status": "ok", "result": {"found": True, "value": _fb_hash_table[key]}}
        return {"status": "ok", "result": {"found": False}}

    if action == "delete":
        key = str(data.get("key", ""))
        if key in _fb_hash_table:
            del _fb_hash_table[key]
            return {"status": "ok", "result": {"deleted": True, "size": len(_fb_hash_table)}}
        return {"status": "ok", "result": {"deleted": False}}

    if action == "size":
        return {"status": "ok", "result": {"size": len(_fb_hash_table)}}

    if action == "clear":
        _fb_hash_table.clear()
        return {"status": "ok", "result": {"cleared": True, "size": 0}}

    if action == "keys":
        return {"status": "ok", "result": {"keys": list(_fb_hash_table.keys())}}

    if action == "bulk_insert":
        items = data if isinstance(data, list) else data.get("items", [])
        count = 0
        for item in items:
            k = str(item.get("key", ""))
            v = item.get("value", {})
            if k:
                _fb_hash_table[k] = v
                count += 1
        return {"status": "ok", "result": {"inserted": count, "size": len(_fb_hash_table)}}

    return {"status": "error", "error": f"Unknown hash_table action: {action}"}


_fb_hash_table = {}


def _linked_list_fallback(action: str, data: dict) -> dict:
    """双向链表的 Python fallback"""
    global _fb_linked_list

    if action == "append":
        node = {
            "id": len(_fb_linked_list) + 1,
            "role": data.get("role", "user"),
            "content": data.get("content", ""),
            "timestamp": data.get("timestamp", 0)
            "timestamp": data.get("timestamp", 0)
        }
        _fb_linked_list.append(node)
        return {"status": "ok", "result": {"id": node["id"], "size": len(_fb_linked_list)}}

    if action == "prepend":
        node = {
            "id": len(_fb_linked_list) + 1,
            "role": data.get("role", "user"),
            "content": data.get("content", ""),
            "timestamp": data.get("timestamp", 0)
        }
        _fb_linked_list.insert(0, node)
        return {"status": "ok", "result": {"id": node["id"], "size": len(_fb_linked_list)}}

    if action == "delete":
        target_id = data.get("id", -1)
        for i, n in enumerate(_fb_linked_list):
            if n["id"] == target_id:
                del _fb_linked_list[i]
                return {"status": "ok", "result": {"deleted": True, "id": target_id}}
        return {"status": "ok", "result": {"deleted": False, "id": target_id}}

    if action == "find":
        target_id = data.get("id", -1)
        for n in _fb_linked_list:
            if n["id"] == target_id:
                return {"status": "ok", "result": {"found": True, **n}}
        return {"status": "ok", "result": {"found": False}}

    if action == "to_array":
        return {"status": "ok", "result": list(_fb_linked_list)}

    if action == "from_array":
        items = data if isinstance(data, list) else data.get("messages", [])
        _fb_linked_list = list(items)
        return {"status": "ok", "result": {"imported": len(_fb_linked_list)}}

    if action == "clear":
        _fb_linked_list.clear()
        return {"status": "ok", "result": {"cleared": True}}

    if action == "size":
        return {"status": "ok", "result": {"size": len(_fb_linked_list)}}

    return {"status": "error", "error": f"Unknown linked_list action: {action}"}




# ============================================================
# 便捷封装：C 队列操作
# ============================================================

def queue_enqueue(data: dict) -> dict:
    """将 AI 请求加入队列"""
    return call_c_module('queue', {
        'command': 'enqueue',
        'data': json.dumps(data, ensure_ascii=False)
    })


def queue_dequeue() -> dict:
    """从队列中取出下一个 AI 请求"""
    return call_c_module('queue', {'command': 'dequeue'})


def queue_peek() -> dict:
    """查看队首请求（不移除）"""
    return call_c_module('queue', {'command': 'peek'})


def queue_size() -> int:
    """获取队列当前长度"""
    result = call_c_module('queue', {'command': 'size'})
    return result.get('result', 0) if result.get('status') == 'ok' else 0


def queue_is_empty() -> bool:
    """检查队列是否为空"""
    result = call_c_module('queue', {'command': 'is_empty'})
    return result.get('result', True) if result.get('status') == 'ok' else True


def queue_clear() -> dict:
    """清空队列"""
    return call_c_module('queue', {'command': 'clear'})
