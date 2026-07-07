# CampusAI 校园达人 🎓

<div align="center">

**AI 驱动的校园时间管理平台** — 记录学习时间、追踪番茄钟、解锁成就、生成 AI 分析报告

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)]()
[![Flask](https://img.shields.io/badge/Flask-3.1-000?logo=flask&logoColor=white)]()
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20mode-003B57?logo=sqlite&logoColor=white)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![GitHub last commit](https://img.shields.io/github/last-commit/liburce0412-alt/322creating-big-program)]()
[![Code size](https://img.shields.io/github/languages/code-size/liburce0412-alt/322creating-big-program)]()

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [数据库设计](#数据库设计)
- [C 模块集成](#c-模块集成)
- [前端设计系统](#前端设计系统)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [测试](#测试)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 项目简介

CampusAI 校园达人是一个面向大学生的时间管理与学习效率提升平台。它结合了**柳比歇夫时间统计法**（时间记录）、**番茄工作法**（专注计时）、**游戏化成就系统**（勋章激励）和 **AI 分析报告**（DeepSeek 驱动），帮助用户深入了解自己的时间使用模式。

### 设计理念

- **记录即觉察** — 每一次时间记录都是一次自我认知
- **专注可量化** — 番茄钟让专注变成可追踪的数据
- **数据驱动成长** — AI 分析揭示时间黑洞和优化空间
- **性能优先** — 核心数据结构用 C 实现，Python subprocess 调用，兼顾开发效率和运行速度

---

## 功能特性

### 📝 时间记录（柳比歇夫法）

记录每天的活动时间，支持多维度分类和分析。

- **CRUD 操作** — 新增、编辑、删除、列表查询，支持分页
- **分类管理** — 学习/读书/运动/编程/娱乐/社交/工作/其他，颜色编码
- **关键词搜索** — 基于 KMP 算法的全文搜索（C 模块实现），降级到 SQL LIKE
- **撤销/重做** — 行级选中，撤销（删除）或重做（编辑），`created_at` 保持不变
- **实时统计** — 按类别汇总时长、按日期趋势、总记录数

### 🍅 番茄钟

内置番茄工作法计时器，支持多种专注时长。

- **三种模式** — 25 分钟（短专注）、50 分钟（标准）、90 分钟（深度）
- **连击追踪** — 自动计算连续打卡天数
- **经验系统** — 每次完成获得 50 经验值，升级解锁新功能
- **日/周统计** — 今日专注时长、本周趋势、总览

### 🏆 成就系统

游戏化徽章体系，激励持续使用。

| 徽章 | 触发条件 |
|------|---------|
| 🍅 初次专注 | 完成第一次番茄钟 |
| ⏰ 专注达人 | 累计 10 次番茄钟 |
| 🔥 专注大师 | 累计 50 次番茄钟 |
| 📝 初次记录 | 添加第一条时间记录 |
| 📊 时间管理者 | 累计 10 条时间记录 |
| ⭐ 见习达人 | 达到等级 5 |
| 🌟 校园达人 | 达到等级 10 |
| 🤖 AI 初体验 | 首次生成 AI 报告 |
| 📅 连续三天 | 连续 3 天使用番茄钟 |
| 🏆 一周全勤 | 连续 7 天使用番茄钟 |

### 🤖 AI 智能分析

调用 DeepSeek API 生成个性化时间管理报告。

- **模型选择** — DeepSeek / Gemini / Mock 模式
- **分析维度** — 时间概览、模式识别、优化建议、下周目标、鼓励寄语
- **历史报告** — 所有报告持久化存储，支持回顾
- **AI 对话** — 内置聊天助手，回答时间管理相关问题
- **API Key 管理** — 支持服务器预配置或用户手动输入保存

### ⚡ C 模块加速

核心数据结构和算法由 C 语言实现，通过 `subprocess` 调用 JSON 协议通信。

| 模块 | 用途 | 算法 |
|------|------|------|
| hash_table | 用户/记录快速查询 | 哈希表 |
| linked_list | AI 对话历史存储 | 双向链表 |
| queue | AI 请求排队 | FIFO 队列 |
| stack | 撤销/重做 | LIFO 栈 |
| kmp | 关键词搜索 | KMP 算法 |
| binary_search | 按时间排序 | 二分查找 |

所有 C 模块都有 Python fallback 实现，确保即使 C 编译失败，系统仍可正常运行。

### 🎨 响应式 UI

- **暖陶色主题** — `--primary: #D4785C`，避免蓝紫渐变
- **毛玻璃导航栏** — `backdrop-filter: blur(12px)` 毛玻璃效果
- **全设备适配** — 桌面/平板/手机三断点
- **微交互动效** — hover 上浮、聚焦光晕、toast 弹出动画
- **触摸友好** — 所有控件 `min-height: 44px`

---

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.14 | 主语言 |
| Flask | 3.1 | Web 框架 |
| Gunicorn | 26.0 | WSGI 服务器 |
| SQLite | 3.x | 数据库（WAL 模式） |
| PyJWT | 2.x | JWT 认证 |
| requests | 2.x | AI API 调用 |

### 前端

| 技术 | 说明 |
|------|------|
| 原生 HTML5 | 语义化标签 |
| CSS3 | 自定义属性（变量）、Grid/Flexbox、毛玻璃 |
| Vanilla JS | ES6+、async/await、fetch |
| Font Awesome | 6.0 图标库 |

### 基础设施

| 组件 | 说明 |
|------|------|
| Nginx | 反向代理 + 静态文件服务 |
| C (campus_lib) | 数据结构模块，subprocess 通信 |
| SQLite WAL | Write-Ahead Logging 支持并发读写 |

---

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                    用户浏览器                              │
│  (Chrome / Safari / Edge / 移动端)                       │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTPS :80
                         ▼
┌──────────────────────────────────────────────────────────┐
│                     Nginx                                 │
│  ├── 静态文件: /var/www/campus3ai.xyz/frontend/           │
│  └── 反向代理: /api/ → http://127.0.0.1:5000/             │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP :5000
                         ▼
┌──────────────────────────────────────────────────────────┐
│              Gunicorn + Flask (Python 3.14)               │
│                                                           │
│  app.py — 主入口 + 蓝图注册 + 错误处理                     │
│  ├── auth.py — JWT 生成/验证 + 密码哈希 + 经验值系统       │
│  ├── models.py — SQLite 初始化 + 6 张表 + 索引            │
│  ├── config.py — 密钥/API Key/经验值/成就定义              │
│  ├── routes/                                              │
│  │   ├── auth_routes.py     — 注册/登录                   │
│  │   ├── time_routes.py     — 时间记录 CRUD + 撤销/重做    │
│  │   ├── pomodoro_routes.py — 番茄钟 + 成就检测            │
│  │   ├── achievement_routes.py — 成就查询/用户信息         │
│  │   ├── ai_routes.py       — AI 报告/对话/模型列表       │
│  │   └── search_routes.py   — KMP 关键词搜索              │
│  └── c_bridge.py — C 模块桥接 (subprocess + JSON 协议)    │
└───────────┬──────────────────────────────┬────────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│    SQLite (WAL 模式)  │    │  C 模块 (campus_lib)          │
│  ├── users            │    │  ├── hash_table               │
│  ├── time_records     │    │  ├── linked_list              │
│  ├── pomodoro_sessions│    │  ├── queue                    │
│  ├── achievements     │    │  ├── stack                    │
│  ├── chat_history     │    │  ├── kmp                      │
│  └── ai_reports       │    │  └── binary_search            │
└──────────────────────┘    └──────────────────────────────┘
```

### 数据流

1. 用户操作 → 前端 fetch(`/api/...`) → Nginx → Gunicorn/Flask
2. Flask 验证 JWT (`Authorization: Bearer <token>`)
3. 业务逻辑 → SQLite 查询/写入
4. 可选: C 模块调用 (subprocess, JSON stdin/stdout)
5. JSON 响应 → Flask → Nginx → 前端渲染

### 请求/响应规范

- 认证: `Authorization: Bearer <token>` (JWT, 72h 过期)
- 请求体: `Content-Type: application/json`
- 响应格式: `{"key": value, ...}`
- 错误格式: `{"error": "描述信息"}`
- HTTP 状态码: 200(成功) / 201(创建) / 400(参数错误) / 401(未登录) / 404(不存在) / 409(冲突) / 500(服务器错误)

---

## 快速开始

### 环境要求

- Python 3.13+
- pip
- gcc / make（可选，编译 C 模块）
- Nginx（可选，生产部署）

### 1. 克隆仓库

```bash
git clone https://github.com/liburce0412-alt/322creating-big-program.git
cd 322creating-big-program
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

`requirements.txt` 包含:
```
flask          — Web 框架
flask-cors     — 跨域支持
pyjwt          — JWT 令牌
requests       — AI API HTTP 调用
gunicorn       — WSGI 服务器 (生产环境)
```

### 3. 启动开发服务器

```bash
python app.py
```

访问 `http://localhost:5000`，健康检查端点返回 `{"status":"ok","message":"CampusAI API is running"}`。

### 4. 编译 C 模块（可选）

```bash
cd ../c_lib
make clean && make
```

编译产物 `campus_lib` 位于 `c_lib/` 目录。如果跳过此步，系统自动使用 Python fallback。

### 5. 启动前端

前端是纯静态 HTML，直接用浏览器打开 `frontend/index.html` 即可。

生产环境推荐用 Nginx 提供静态文件服务（参考部署指南）。

### 6. 配置 DeepSeek API Key（可选）

```bash
# 方式一：环境变量（推荐）
export DEEPSEEK_API_KEY="sk-your-key-here"

# 方式二：直接修改 config.py
# DEEPSEEK_API_KEY = "sk-your-key-here"
```

---

## API 文档

### 认证相关

#### 注册

```http
POST /api/register
Content-Type: application/json

{"username": "zhangsan", "password": "123456"}
```

响应 `201`:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {"id": 1, "username": "zhangsan", "level": 1, "exp": 0}
}
```

#### 登录

```http
POST /api/login
Content-Type: application/json

{"username": "zhangsan", "password": "123456"}
```

响应 `200`:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {"id": 1, "username": "zhangsan", "level": 3, "exp": 120}
}
```

### 用户

#### 获取用户信息

```http
GET /api/user/profile
Authorization: Bearer <token>
```

响应 `200`:
```json
{
  "user_id": 1,
  "username": "zhangsan",
  "level": 3,
  "exp": 150,
  "exp_needed": 300,
  "exp_percent": 50.0,
  "today_focus_min": 75,
  "total_pomodoros": 12,
  "total_records": 25,
  "total_achievements": 3,
  "streak_days": 5,
  "created_at": "2026-07-03 14:00:00"
}
```

#### 获取成就列表

```http
GET /api/user/achievements
Authorization: Bearer <token>
```

### 时间记录

#### 新增记录

```http
POST /api/time-records
Authorization: Bearer <token>
Content-Type: application/json

{"category": "学习", "description": "复习高等数学", "duration_min": 90}
```

#### 获取记录列表

```http
GET /api/time-records?page=1&limit=20&category=学习
Authorization: Bearer <token>
```

#### 编辑记录（保留 created_at）

```http
PUT /api/time-records/1
Authorization: Bearer <token>
Content-Type: application/json

{"category": "运动", "description": "跑步 5 公里", "duration_min": 40}
```

#### 删除记录

```http
DELETE /api/time-records/1
Authorization: Bearer <token>
```

#### 撤销（删除选中记录）

```http
POST /api/time-records/undo
Authorization: Bearer <token>
```

#### 重做（编辑选中记录）

```http
POST /api/time-records/redo
Authorization: Bearer <token>
```

#### 获取统计

```http
GET /api/time-records/stats
Authorization: Bearer <token>
```

### 番茄钟

#### 完成一次番茄钟

```http
POST /api/pomodoro/complete
Authorization: Bearer <token>
Content-Type: application/json

{"duration_min": 25}
```

#### 番茄钟统计

```http
GET /api/pomodoro/stats
Authorization: Bearer <token>
```

#### 番茄钟历史

```http
GET /api/pomodoro/history?page=1&limit=20
Authorization: Bearer <token>
```

### AI 功能

#### 获取可用模型

```http
GET /api/ai/models
Authorization: Bearer <token>
```

#### 生成 AI 报告

```http
GET /api/ai/report?model=deepseek
Authorization: Bearer <token>
```

#### 获取历史报告

```http
GET /api/ai/reports
Authorization: Bearer <token>
```

#### AI 对话

```http
POST /api/ai/chat
Authorization: Bearer <token>
Content-Type: application/json

{"message": "帮我分析一下我的学习效率"}
```

### 搜索

#### 关键词搜索

```http
GET /api/search?q=高等数学
Authorization: Bearer <token>
```

### 系统

#### 健康检查

```http
GET /api/health
```

响应 `200`:
```json
{"status": "ok", "message": "CampusAI API is running"}
```

---

## 数据库设计

### ER 概览

```
users (1) ──< time_records (N)
users (1) ──< pomodoro_sessions (N)
users (1) ──< achievements (N)
users (1) ──< chat_history (N)
users (1) ──< ai_reports (N)
```

### 表结构

#### users

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 用户 ID |
| username | TEXT UNIQUE | 用户名 |
| password_hash | TEXT | SHA-256 哈希 |
| level | INTEGER DEFAULT 1 | 等级 |
| exp | INTEGER DEFAULT 0 | 经验值 |
| created_at | TIMESTAMP | 注册时间 |

#### time_records

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 记录 ID |
| user_id | INTEGER FK | 用户 |
| category | TEXT | 分类 |
| description | TEXT | 描述 |
| duration_min | INTEGER | 时长（分钟） |
| created_at | TIMESTAMP | 创建时间 |

索引: `(user_id)`, `(user_id, category)`, `(user_id, created_at)`

#### pomodoro_sessions

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 会话 ID |
| user_id | INTEGER FK | 用户 |
| duration_min | INTEGER | 时长 |
| exp_gained | INTEGER | 获得经验 |
| completed_at | TIMESTAMP | 完成时间 |

#### achievements

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 记录 ID |
| user_id | INTEGER FK | 用户 |
| badge_id | TEXT | 徽章 ID |
| unlocked_at | TIMESTAMP | 解锁时间 |

唯一约束: `(user_id, badge_id)`

#### chat_history

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 消息 ID |
| user_id | INTEGER FK | 用户 |
| role | TEXT | user / assistant |
| content | TEXT | 消息内容 |
| created_at | TIMESTAMP | 发送时间 |

#### ai_reports

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 报告 ID |
| user_id | INTEGER FK | 用户 |
| report_content | TEXT | 报告内容（Markdown） |
| model | TEXT | 生成模型 |
| created_at | TIMESTAMP | 生成时间 |

---

## C 模块集成

### 架构

CampusAI 的核心数据结构用 C 实现，通过 `subprocess` 调用可执行文件 `campus_lib`，使用 stdin/stdout JSON 协议通信。

```
Python ──JSON──→ [subprocess] ──→ C 可执行文件
Python ←─JSON── [subprocess] ←── C 可执行文件
```

### 通信协议

```json
// 请求格式
{"module": "linked_list", "action": "append", "data": {"role": "user", "content": "hello"}}

// 成功响应
{"status": "ok", "result": {"id": 1, "size": 1}}

// 错误响应
{"status": "error", "error": "missing 'module' field"}
```

### Python Fallback

每个 C 模块都有对应的 Python fallback 实现 (`c_bridge.py` 中的 `_python_fallback` 函数)。当 C 可执行文件不存在、不可执行、超时或返回错误时，自动降级到 Python 实现。

### 编译

```bash
cd c_lib
make clean && make
```

`Makefile` 编译所有 `.c` 文件并链接为单个可执行文件 `campus_lib`。

---

## 前端设计系统

### 色彩体系

```
--primary: #D4785C   暖陶色（主色，取代蓝色）
--primary-dark: #C06A4F
--primary-light: #FDF2EE
--accent: #E8B849    琥珀金（强调色）
--success: #7B9E6B   鼠尾草绿
--bg: #F8F6F4        暖灰白（背景）
--text: #2D2522      暖深灰（文字）
--border: #EDE8E4    暖灰（边框）
```

### 组件样式

| 组件 | 风格 |
|------|------|
| 导航栏 | 毛玻璃 `backdrop-filter: blur(12px)`，固定顶部 |
| 卡片 | 12px 圆角，暖调阴影 `rgba(45,37,34,0.06)` |
| 按钮 | 10px 圆角，hover 上浮 + 阴影 |
| 表单 | 聚焦 4px 光晕 `rgba(212,120,92,0.12)` |
| Toast | 顶部滑入，3 秒自动消失 |
| 表格 | 粘性表头，行 hover 高亮 |
| 徽章 | pill 风格，`border-radius: 20px` |

### 响应式断点

| 断点 | 说明 |
|------|------|
| < 600px | 移动端：抽屉菜单，全宽按钮，隐藏用户名 |
| 600-899px | 平板：双列网格 |
| ≥ 900px | 桌面：完整导航，三列网格 |

---

## 开发指南

### 代码结构

```
campus-ai/
├── backend/                # Flask 后端
│   ├── app.py             # 主入口
│   ├── auth.py            # JWT 认证 + 经验系统
│   ├── c_bridge.py        # C 模块桥接
│   ├── config.py          # 配置
│   ├── models.py          # 数据库模型
│   ├── routes/            # 路由
│   │   ├── achievement_routes.py
│   │   ├── ai_routes.py
│   │   ├── auth_routes.py
│   │   ├── pomodoro_routes.py
│   │   ├── search_routes.py
│   │   └── time_routes.py
│   └── tests/             # 测试
│       ├── smoke_test.py
│       └── run.sh
├── frontend/               # 静态前端
│   ├── css/style.css      # 暖陶色主题样式
│   ├── js/
│   │   ├── api.js         # API 封装
│   │   ├── auth.js        # 认证逻辑
│   │   └── utils.js       # 工具函数
│   ├── records.html       # 时间记录页
│   ├── ai-report.html     # AI 报告页
│   ├── dashboard.html     # 仪表盘
│   ├── stats.html         # 统计页
│   ├── pomodoro.html      # 番茄钟
│   ├── achievements.html  # 成就页
│   ├── login.html         # 登录
│   ├── register.html      # 注册
│   └── profile.html       # 个人中心
├── c_lib/                  # C 模块
│   ├── main.c            # 主入口 + JSON 解析
│   ├── hash_table.c/h    # 哈希表
│   ├── linked_list.c/h   # 双向链表
│   ├── queue.c/h         # 队列
│   ├── stack.c/h         # 栈
│   ├── kmp.c/h           # KMP 搜索
│   ├── binary_search.c/h # 二分查找
│   └── Makefile
├── brain/                  # 项目记忆
├── .gitignore
├── requirements.txt
└── run.bat
```

### 添加新 API

1. 在 `backend/routes/` 下创建新路由文件（如 `new_routes.py`）
2. 定义蓝图（Blueprint）和路由
3. 在 `backend/app.py` 中注册蓝图
4. 如有需要，在 `backend/models.py` 中添加数据库表
5. 在前端 `frontend/js/api.js` 中添加 API 调用方法
6. 运行 `python3 backend/tests/smoke_test.py` 验证

---

## 部署指南

### 服务器要求

- Alibaba Cloud Linux 3 / RHEL 8 / Ubuntu 22.04+
- Python 3.13+
- Nginx 1.20+
- 1 核 1G 以上（推荐 2 核 2G）

### Nginx 配置

```nginx
server {
    listen 80;
    server_name campus3ai.xyz;

    root /var/www/campus3ai.xyz/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Gunicorn 启动

```bash
cd /root/backend
python3 -m gunicorn -w 1 -b 0.0.0.0:5000 app:app \
    --error-logfile /var/log/campus3ai/error.log \
    --access-logfile /var/log/campus3ai/access.log \
    --log-level warning --daemon
```

---

## 测试

```bash
cd backend
python3 tests/smoke_test.py
```

烟雾测试覆盖:

1. ✅ 健康检查
2. ✅ 用户注册
3. ✅ 用户登录
4. ✅ 获取用户信息
5. ✅ 添加时间记录
6. ✅ 查看时间记录
7. ✅ 统计操作
8. ✅ 获取成就
9. ✅ 获取 AI 模型列表
10. ✅ 生成 AI 报告

---

## 贡献

欢迎提交 Pull Request！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

---

## 许可证

[MIT](LICENSE) © 2026 CampusAI Contributors

---

<div align="center">
  Made with ☕ and 🎓
</div>
