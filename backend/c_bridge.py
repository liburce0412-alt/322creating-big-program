# c_bridge.py - Python??C????
import subprocess
import json
import os

C_LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'c_lib', 'campus_lib')

def call_c_module(command, data=None):
    if not os.path.exists(C_LIB_PATH):
        return {'error': 'C module not compiled. Run make in c_lib/'}
    try:
        proc = subprocess.run([C_LIB_PATH], input=json.dumps(data or {}), capture_output=True, text=True, timeout=5)
        return json.loads(proc.stdout)
    except Exception as e:
        return {'error': str(e)}

def linked_list_append(data):
    return call_c_module('linked_list_append', data)

def stack_push(data):
    return call_c_module('stack_push', data)

def stack_pop():
    return call_c_module('stack_pop')

def kmp_search(text, pattern):
    return call_c_module('kmp_search', {'text': text, 'pattern': pattern})

def hash_table_get(key):
    return call_c_module('hash_get', {'key': key})

def binary_search(sorted_list, target):
    return call_c_module('binary_search', {'list': sorted_list, 'target': target})
