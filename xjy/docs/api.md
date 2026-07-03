# 校园达人 CampusAI —— API 接口文档

> Base URL: `http://campus3ai.xyz/api`

---

## 1. 认证接口

### POST /api/register — 用户注册
```json
// Request
{ "username": "zhangsan", "password": "123456" }

// Response 201
{ "token": "eyJ...", "user": { "id": 1, "username": "zhangsan", "level": 1, "exp": 0 } }
```

### POST /api/login — 用户登录
```json
// Request
{ "username": "zhangsan", "password": "123456" }

// Response 200
{ "token": "eyJ...", "user": { "id": 1, "username": "zhangsan", "level": 3, "exp": 120 } }
```

> 所有需要认证的接口请在 Header 中携带 `Authorization: Bearer <token>`

---

## 2. 用户接口

### GET /api/user/profile — 获取用户信息
```
Headers: Authorization: Bearer <token>

Response:
{
  "user_id": 1, "username": "zhangsan",
  "level": 3, "exp": 120, "exp_needed": 300, "exp_percent": 40.0,
  "today_focus_min": 75, "total_pomodoros": 12,
  "total_records": 25, "total_achievements": 3,
  "streak_days": 5, "created_at": "2024-07-03 14:00:00"
}
```

### GET /api/user/achievements — 获取已解锁成就
### GET /api/user/achievements/all — 获取所有成就及解锁状态

---

## 3. 时间记录接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/time-records` | 新增时间记录 |
| GET | `/api/time-records` | 获取列表（?page=1&limit=20&category=学习） |
| DELETE | `/api/time-records/<id>` | 删除记录 |
| GET | `/api/time-records/stats` | 统计汇总 |
| POST | `/api/time-records/undo` | 撤销（C 模块栈） |
| POST | `/api/time-records/redo` | 重做（C 模块栈） |

---

## 4. 番茄钟接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/pomodoro/complete` | 完成番茄钟 `{"duration_min": 25}` |
| GET | `/api/pomodoro/history` | 历史记录 |
| GET | `/api/pomodoro/stats` | 统计数据 |

---

## 5. AI 分析接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai/models` | 获取可用模型列表 |
| GET | `/api/ai/report?model=deepseek` | 生成分析报告 |
| GET | `/api/ai/reports` | 历史报告列表 |
| GET | `/api/ai/reports/<id>` | 报告详情 |
| GET | `/api/ai/chat-history` | 对话历史（C 模块链表） |
| POST | `/api/ai/chat` | AI 对话 `{"message":"..."}` |

---

## 6. 搜索接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/search?q=关键词` | 搜索时间记录（C 模块 KMP） |

---

## 7. C 模块 JSON 协议

Python 通过 `subprocess` 调用编译好的 `campus_lib` 可执行文件。

### 输入格式（stdin）
```json
{ "module": "linked_list|queue|stack|kmp|hash_table|binary_search",
  "action": "操作名",
  "data": { ... }
}
```

### 输出格式（stdout）
```json
{ "status": "ok", "result": { ... } }
{ "status": "error", "error": "消息" }
```
