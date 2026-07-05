# -*- coding: utf-8 -*-
"""
烟雾测试 — CampusAI 后端关键接口验证
运行方式: python3 smoke_test.py
"""

import urllib.request
import json
import sys
import time
import random
import string

BASE = 'http://127.0.0.1:5000/api'

passed = 0
failed = 0
test_user = ''.join(random.choices(string.ascii_lowercase, k=6))
test_pass = 'testpass123'

def check(name, ok, detail=''):
    global passed, failed
    if ok:
        passed += 1
        print(f'  \u2713 {name}')
    else:
        failed += 1
        print(f'  \u2717 {name}: {detail}')

def api(method, path, data=None, token=None):
    url = BASE + path
    h = {'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.status, json.loads(resp.read())
    except urllib.request.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as e:
        return -1, str(e)

print('')
print('========== CampusAI \u70df\u96fe\u6d4b\u8bd5 ==========')
print('')

# 1. Health check
status, body = api('GET', '/health')
check('\u5065\u5eb7\u68c0\u67e5', status == 200, str(body))

# 2. Register
rnd = ''.join(random.choices(string.digits, k=3))
uname = 'smoketest_' + rnd
data = {'username': uname, 'password': test_pass}
status, body = api('POST', '/register', data)
check('\u7528\u6237\u6ce8\u518c', status in (201, 409),
      str(body.get('error', '')))

# 3. Login
status, body = api('POST', '/login', data)
token = body.get('token', '')
check('\u7528\u6237\u767b\u5f55', status == 200 and bool(token),
      'status=' + str(status))

# 4. Get profile
status, body = api('GET', '/user/profile', token=token)
check('\u83b7\u53d6\u7528\u6237\u4fe1\u606f', status == 200,
      str(body.get('error', '')))

# 5. Add time record
data2 = {'category': '\u5b66\u4e60', 'description': '\u70df\u96fe\u6d4b\u8bd5\u8bb0\u5f55',
         'duration_min': 25}
status, body = api('POST', '/time-records', data2, token)
check('\u6dfb\u52a0\u65f6\u95f4\u8bb0\u5f55', status == 201,
      str(body.get('error', '')))

# 6. Get time records list
status, body = api('GET', '/time-records', token=token)
check('\u67e5\u770b\u65f6\u95f4\u8bb0\u5f55', status == 200 and body.get('total', 0) > 0,
      'count=' + str(body.get('total', 0)))

# 7. Get stats
status, body = api('GET', '/time-records/stats', token=token)
check('\u7edf\u8ba1\u64cd\u4f5c', status == 200,
      'total_min=' + str(body.get('total_minutes', '?')))

# 8. Get all achievements
status, body = api('GET', '/user/achievements', token=token)
check('\u83b7\u53d6\u6210\u5c31', status == 200,
      'count=' + str(body.get('total_unlocked', 0)))

# 9. Get AI models
status, body = api('GET', '/ai/models', token=token)
models_ok = status == 200 and len(body.get('models', [])) > 0
check('\u83b7\u53d6 AI \u6a21\u578b\u5217\u8868', models_ok,
      'models=' + str(len(body.get('models', []))))

# 10. Generate AI report (mock mode)
status, body = api('GET', '/ai/report?model=mock', token=token)
check('\u751f\u6210 AI \u62a5\u544a', status == 200 and body.get('report_id'),
      'report_id=' + str(body.get('report_id', 'N/A')))

# Summary
print('')
print('=' * 42)
print(f'\u901a\u8fc7: {passed}  |  \u5931\u8d25: {failed}  |  \u603b\u8ba1: {passed + failed}')
print('=' * 42)

# Exit code
sys.exit(0 if failed == 0 else 1)
