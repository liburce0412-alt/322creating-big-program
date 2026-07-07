"""
app.py —— 校园达人 CampusAI Flask 主入口

启动方式：
    python app.py
    或
    flask run --host=0.0.0.0 --port=5000
"""
from flask import Flask, jsonify
from models import init_db

app = Flask(__name__)

# ---- 注册蓝图（Blueprint）----
from routes.auth_routes import auth_bp
from routes.time_routes import time_bp
from routes.pomodoro_routes import pomodoro_bp
from routes.achievement_routes import achievement_bp
from routes.ai_routes import ai_bp
from routes.search_routes import search_bp
from routes.admin_routes import admin_bp

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(time_bp, url_prefix="/api")
app.register_blueprint(pomodoro_bp, url_prefix="/api")
app.register_blueprint(achievement_bp, url_prefix="/api")
app.register_blueprint(ai_bp, url_prefix="/api")
app.register_blueprint(search_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api")

# 初始化数据库（gunicorn 加载时自动执行）
init_db()


@app.route("/api/health")
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "CampusAI API is running"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "接口不存在"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "服务器内部错误"}), 500


if __name__ == "__main__":
    # init_db() called at module level, not here
    print("🚀 CampusAI 后端启动中...")
    print("📍 访问地址: http://localhost:5000")
    print("❤️  健康检查: http://localhost:5000/api/health")
    app.run(host="0.0.0.0", port=5000, debug=True)
