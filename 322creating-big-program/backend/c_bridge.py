"""
Python 调用 C 模块的桥接接口
通过 subprocess 执行编译好的 C 程序，stdin 传入 JSON，stdout 读取结果
"""
import subprocess
import json
import os
from config import Config


class CBridgeError(Exception):
    """C 模块调用异常"""
    pass


def _get_binary_path() -> str:
    """获取 C 模块可执行文件路径"""
    binary = os.path.join(Config.C_LIB_DIR, 'main')
    if os.name == 'nt':
        binary += '.exe'
    return binary


def call_c_module(module: str, action: str, data: dict = None) -> dict:
    """
    调用 C 模块

    Args:
        module: 模块名 (linked_list, stack, queue, kmp, hash_table, binary_search)
        action: 操作名
        data: 传入的数据

    Returns:
        C 模块返回的结果字典
    """
    binary = _get_binary_path()

    if not os.path.exists(binary):
        return {
            'success': False,
            'error': f'C 模块未编译，请先运行 make。预期路径: {binary}',
        }

    payload = json.dumps({
        'module': module,
        'action': action,
        'data': data or {},
    })

    try:
        proc = subprocess.run(
            [binary],
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Config.C_LIB_DIR,
        )
        if proc.returncode != 0:
            return {'success': False, 'error': proc.stderr.strip()}

        return json.loads(proc.stdout.strip())
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'C 模块执行超时'}
    except json.JSONDecodeError:
        return {'success': False, 'error': 'C 模块返回数据格式错误'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ========== 高层封装（供路由使用） ==========

def kmp_search(text: str, pattern: str) -> list:
    """KMP 字符串匹配搜索"""
    result = call_c_module('kmp', 'search', {'text': text, 'pattern': pattern})
    if result.get('success'):
        return result.get('matches', [])
    return []


def hash_table_operations():
    """哈希表操作（供搜索路由使用）"""
    pass


def linked_list_sort(data: list) -> list:
    """链表排序"""
    result = call_c_module('linked_list', 'sort', {'data': data})
    if result.get('success'):
        return result.get('sorted', data)
    return data


def binary_search_item(arr: list, target) -> int:
    """二分查找"""
    result = call_c_module('binary_search', 'search', {'array': arr, 'target': target})
    if result.get('success'):
        return result.get('index', -1)
    return -1
