"""
app.py —— 校园达人 CampusAI Flask 主入口

启动方式：
    python app.py
    或
    flask run --host=0.0.0.0 --port=5000
"""
import os
from flask import Flask, jsonify, send_from_directory, request, redirect

app = Flask(__name__, static_folder=None)

# ---- 前端静态文件目录 ----
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

# ---- 注册蓝图（Blueprint）----
from routes.auth_routes import auth_bp
from routes.time_routes import time_bp
from routes.pomodoro_routes import pomodoro_bp
from routes.achievement_routes import achievement_bp
from routes.ai_routes import ai_bp
from routes.search_routes import search_bp

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(time_bp, url_prefix="/api")
app.register_blueprint(pomodoro_bp, url_prefix="/api")
app.register_blueprint(achievement_bp, url_prefix="/api")
app.register_blueprint(ai_bp, url_prefix="/api")
app.register_blueprint(search_bp, url_prefix="/api")


# ---- 前端页面路由（让 Flask 直接 serve HTML/CSS/JS）----
@app.route("/")
def index():
    """默认首页 → 重定向到登录页"""
    return redirect("/login.html")


@app.route("/<path:filename>")
def serve_frontend(filename):
    """Serve 前端静态文件（HTML, CSS, JS, 图片等）"""
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/api/health")
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "CampusAI API is running"})


@app.errorhandler(404)
def not_found(e):
    # 对于 API 路径返回 JSON 错误
    if request.path.startswith("/api/"):
        return jsonify({"error": "接口不存在"}), 404
    # 对于其他路径尝试返回 404.html，否则返回 JSON
    return jsonify({"error": "页面不存在"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "服务器内部错误"}), 500


if __name__ == "__main__":
    # 设置输出编码为 UTF-8（解决 Windows GBK 编码问题）
    import sys
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

    # 首次运行时初始化数据库
    from models import init_db
    init_db()
    print("=" * 50)
    print("[CampusAI] 后端启动中...")
    print("[CampusAI] 前端页面: http://localhost:5000")
    print("[CampusAI] 登录页面: http://localhost:5000/login.html")
    print("[CampusAI] 健康检查: http://localhost:5000/api/health")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
