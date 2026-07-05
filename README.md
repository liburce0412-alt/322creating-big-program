# CampusAI 校园达人 🎓

<div align="center">

**AI 驱动的校园时间管理平台** — 记录学习时间、番茄钟专注、AI 分析报告、C 模块加速

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python)]()
[![Flask](https://img.shields.io/badge/Flask-3.1-000?logo=flask)]()
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

</div>

## Features

📝 Time Records — Categorize, search (KMP), filter by date
🍅 Pomodoro Timer — 25/50/90 min sessions, streak tracking  
📊 Statistics — Category & daily distribution charts
🏆 Achievements — 10 badges, auto-unlock on milestones
🤖 AI Reports — DeepSeek-powered personalized analysis
⟲ Undo/Redo — Row selection, delete or edit with timestamp preservation
⚡ C Modules — Hash table, linked list, queue, stack, KMP, binary search

## Quick Start

git clone https://github.com/liburce0412-alt/322creating-big-program.git
cd 322creating-big-program/backend
pip install -r requirements.txt
python app.py

C module (optional): cd ../c_lib && make

## Architecture

Nginx → Gunicorn/Flask → SQLite (WAL mode)
  C modules called via subprocess (fallback to Python)
  Vanilla HTML/CSS/JS frontend

## API

POST /api/register          Register
POST /api/login             Login
GET  /api/time-records      List records
POST /api/time-records      Add record
PUT  /api/time-records/:id  Edit record
DEL  /api/time-records/:id  Delete record
POST /api/time-records/undo Undo
POST /api/time-records/redo Redo
GET  /api/ai/report         Generate AI report
GET  /api/search            Keyword search

Auth: Authorization: Bearer <token>

## License

MIT
