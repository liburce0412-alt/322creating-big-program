"""
c_bridge.py —— Python 调用 C 模块的桥接接口

通过 subprocess 调用编译好的 C 可执行文件 `campus_lib`，
使用 stdin/stdout JSON 协议通信。

用法：
    from c_bridge import call_c_module

    result = call_c_module("linked_list", "append", {"role": "user", "content": "hello"})
    # result = {"id": 1, "size": 1, "message": "message appended"}
"""

import subprocess
import json
import os
import logging
from config import C_LIB_PATH

logger = logging.getLogger(__name__)


 def call_c_module(module: str, action: str, data: dict = None) -> dict:
    """
    调用 C 模块。

    参数：
        module: 模块名 ("linked_list" | "queue" | "stack" | "kmp" | "hash_table" | "binary_search")
        action: 操作名
        data:   传递给模块的数据（dict 或 list）

    返回：
        dict，格式 {"status": "ok", "result": ...} 或 {"status": "error", "error": "..."}
    """
    # 构建请求 JSON
    request = {
        "module": module,
        "action": action,
        "data": data if data is not None else {}
    }
    request_json = json.dumps(request, ensure_ascii=False)

    # 检查 C 模块是否存在
    if not os.path.exists(C_LIB_PATH):
        logger.warning(f"C module not found at {C_LIB_PATH}, using Python fallback")
        return _python_fallback(module, action, data)

    try:
        # 调用 C 可执行文件
        proc = subprocess.run(
            [C_LIB_PATH],
            input=request_json,
            capture_output=True,
            text=True,
            timeout=10,             # 10 秒超时
            encoding='utf-8'
        )

        if proc.returncode != 0:
            logger.error(f"C module error (returncode={proc.returncode}): {proc.stderr}")
            return {"status": "error", "error": f"C module exited with code {proc.returncode}"}

        # 解析 C 模块的 JSON 输出
        response = json.loads(proc.stdout.strip())
        return response

    except subprocess.TimeoutExpired:
        logger.error(f"C module timeout: {module}.{action}")
        return {"status": "error", "error": "C module timed out"}
    except json.JSONDecodeError as e:
        logger.error(f"C module returned invalid JSON: {e}")
        logger.error(f"Raw output: {proc.stdout[:500] if 'proc' in dir() else 'N/A'}")
        return {"status": "error", "error": "C module returned invalid JSON"}
    except FileNotFoundError:
        logger.warning("C module executable not found, using Python fallback")
        return _python_fallback(module, action, data)
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

    # ---- 其他模块（暂未实现 fallback）----
    return {"status": "error", "error": f"Module '{module}' not available (no C binary and no Python fallback)"}


# ==================== Python Fallback 实现 ====================

# 内存中的简易存储（仅供 fallback 使用）
_fb_linked_list = []    # list of dict
_fb_queue = []          # list of dict


def _linked_list_fallback(action: str, data: dict) -> dict:
    """双向链表的 Python fallback"""
    global _fb_linked_list

    if action == "append":
        node = {
            "id": len(_fb_linked_list) + 1,
            "role": data.get("role", "user"),
            "content": data.get("content", ""),
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
        _fb_linked_list = list(data) if isinstance(data, list) else data.get("messages", [])
        return {"status": "ok", "result": {"imported": len(_fb_linked_list)}}

    if action == "clear":
        _fb_linked_list.clear()
        return {"status": "ok", "result": {"cleared": True}}

    if action == "size":
        return {"status": "ok", "result": {"size": len(_fb_linked_list)}}

    return {"status": "error", "error": f"Unknown linked_list action: {action}"}


def _queue_fallback(action: str, data: dict) -> dict:
    """队列的 Python fallback"""
    global _fb_queue

    if action == "enqueue":
        item = {
            "request_id": data.get("request_id", ""),
            "model": data.get("model", "deepseek"),
            "prompt_hash": data.get("prompt_hash", ""),
            "priority": data.get("priority", 0),
            "enqueued_at": data.get("timestamp", 0)
        }
        _fb_queue.append(item)
        return {"status": "ok", "result": {"enqueued": True, "size": len(_fb_queue)}}

    if action == "dequeue":
        if not _fb_queue:
            return {"status": "ok", "result": {"dequeued": False, "error": "queue is empty"}}
        item = _fb_queue.pop(0)
        return {"status": "ok", "result": {"dequeued": True, "item": item}}

    if action == "peek":
        if not _fb_queue:
            return {"status": "ok", "result": {"found": False}}
        return {"status": "ok", "result": {"found": True, "item": _fb_queue[0]}}

    if action == "size":
        return {"status": "ok", "result": {"size": len(_fb_queue)}}

    if action == "is_empty":
        return {"status": "ok", "result": {"is_empty": len(_fb_queue) == 0}}

    if action == "clear":
        _fb_queue.clear()
        return {"status": "ok", "result": {"cleared": True, "size": 0}}

    return {"status": "error", "error": f"Unknown queue action: {action}"}


def _binary_search_fallback(action: str, data: dict) -> dict:
    """二分查找的 Python fallback"""
    import bisect

    if action == "search_by_time":
        records = data.get("records", [])
        target = data.get("target", 0)
        if not records:
            return {"status": "ok", "result": {"found": False}}
        timestamps = [r.get("timestamp", 0) for r in records]
        idx = bisect.bisect_left(timestamps, target)
        if idx < len(timestamps) and timestamps[idx] == target:
            return {"status": "ok", "result": {"found": True, "index": idx, "record": records[idx]}}
        return {"status": "ok", "result": {"found": False}}

    if action == "search_by_id":
        records = data.get("records", [])
        target_id = data.get("target_id", -1)
        ids = [r.get("id", -1) for r in records]
        idx = bisect.bisect_left(ids, target_id)
        if idx < len(ids) and ids[idx] == target_id:
            return {"status": "ok", "result": {"found": True, "index": idx, "record": records[idx]}}
        return {"status": "ok", "result": {"found": False}}

    if action == "range_search":
        records = data.get("records", [])
        start = data.get("start", 0)
        end = data.get("end", 0)
        if not records:
            return {"status": "ok", "result": {"count": 0, "records": []}}
        timestamps = [r.get("timestamp", 0) for r in records]
        lo = bisect.bisect_left(timestamps, start)
        hi = bisect.bisect_right(timestamps, end)
        matched = records[lo:hi]
        return {"status": "ok", "result": {"count": len(matched), "records": matched}}

    if action == "is_sorted":
        records = data.get("records", [])
        ts = [r.get("timestamp", 0) for r in records]
        sorted_flag = all(ts[i] <= ts[i+1] for i in range(len(ts)-1))
        return {"status": "ok", "result": {"sorted": sorted_flag, "count": len(records)}}

    return {"status": "error", "error": f"Unknown binary_search action: {action}"}
