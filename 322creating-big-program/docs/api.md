# campus3ai API 文档

Base URL: `http://campus3ai.xyz/api`

## 认证相关 `/api/auth`

| 方法 | 路径 | 说明 | 负责 |
|------|------|------|------|
| POST | `/api/auth/register` | 用户注册 | 李恩琪+余欣泽 |
| POST | `/api/auth/login` | 用户登录 | 李恩琪+余欣泽 |
| GET | `/api/auth/me` | 获取当前用户信息 | 李恩琪+余欣泽 |
| PUT | `/api/auth/profile` | 更新个人信息 | 李恩琪+余欣泽 |

## 时间记录 `/api/time`

| 方法 | 路径 | 说明 | 负责 |
|------|------|------|------|
| POST | `/api/time/record` | 创建时间记录 | 李恩琪+余欣泽 |
| GET | `/api/time/records` | 获取记录列表 | 李恩琪+余欣泽 |
| PUT | `/api/time/record/<id>` | 更新记录 | 李恩琪+余欣泽 |
| DELETE | `/api/time/record/<id>` | 删除记录 | 李恩琪+余欣泽 |
| GET | `/api/time/stats` | 时间统计 | 李恩琪+余欣泽 |

## 番茄钟 `/api/pomodoro`

| 方法 | 路径 | 说明 | 负责 |
|------|------|------|------|
| POST | `/api/pomodoro/start` | 开始番茄钟 | 谢佳杨+丁超轶 |
| POST | `/api/pomodoro/pause/<id>` | 暂停 | 谢佳杨+丁超轶 |
| POST | `/api/pomodoro/resume/<id>` | 恢复 | 谢佳杨+丁超轶 |
| POST | `/api/pomodoro/complete/<id>` | 完成 | 谢佳杨+丁超轶 |
| POST | `/api/pomodoro/abandon/<id>` | 放弃 | 谢佳杨+丁超轶 |
| GET | `/api/pomodoro/current` | 当前进行中 | 谢佳杨+丁超轶 |
| GET | `/api/pomodoro/list` | 历史列表 | 谢佳杨+丁超轶 |
| GET | `/api/pomodoro/stats` | 统计 | 谢佳杨+丁超轶 |

## 成就系统 `/api/achievement`

| 方法 | 路径 | 说明 | 负责 |
|------|------|------|------|
| GET | `/api/achievement/list` | 所有成就+解锁状态 | 谢佳杨+丁超轶 |
| GET | `/api/achievement/user` | 用户已解锁成就 | 谢佳杨+丁超轶 |
| POST | `/api/achievement/check` | 触发成就检查 | 谢佳杨+丁超轶 |
| GET | `/api/achievement/stats` | 成就统计 | 谢佳杨+丁超轶 |

## AI 分析 `/api/ai`

| 方法 | 路径 | 说明 | 负责 |
|------|------|------|------|
| POST | `/api/ai/report/generate` | 生成 AI 报告 | 谢佳杨+丁超轶 |
| GET | `/api/ai/report/list` | 报告列表 | 谢佳杨+丁超轶 |
| GET | `/api/ai/report/<id>` | 报告详情 | 谢佳杨+丁超轶 |
| DELETE | `/api/ai/report/<id>` | 删除报告 | 谢佳杨+丁超轶 |
| POST | `/api/ai/chat/send` | 发送消息 | 谢佳杨+丁超轶 |
| GET | `/api/ai/chat/history` | 对话历史 | 谢佳杨+丁超轶 |
| DELETE | `/api/ai/chat/clear` | 清空对话 | 谢佳杨+丁超轶 |
| GET | `/api/ai/insights` | 学习洞察 | 谢佳杨+丁超轶 |

## 搜索 `/api/search`

| 方法 | 路径 | 说明 | 负责 |
|------|------|------|------|
| GET | `/api/search/records` | 搜索时间记录 | 李恩琪+余欣泽 |
| GET | `/api/search/pomodoro` | 搜索番茄钟 | 李恩琪+余欣泽 |

---

## 认证方式

所有需要登录的接口需在 Header 中携带：

```
Authorization: Bearer <token>
```

Token 通过 `/api/auth/login` 获取，有效期 1 小时。
