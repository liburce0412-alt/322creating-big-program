"""
Flask 主入口 — 注册所有蓝图
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from models import init_db, seed_achievements


def create_app(config_name='default'):
    """应用工厂"""
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # 跨域支持
    CORS(app, supports_credentials=True)

    # 初始化数据库
    with app.app_context():
        init_db()
        seed_achievements()

    # ========== 注册蓝图 ==========
    from routes.auth_routes import auth_bp
    from routes.time_routes import time_bp
    from routes.pomodoro_routes import pomodoro_bp
    from routes.achievement_routes import achievement_bp
    from routes.ai_routes import ai_bp
    from routes.search_routes import search_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(time_bp, url_prefix='/api/time')
    app.register_blueprint(pomodoro_bp, url_prefix='/api/pomodoro')
    app.register_blueprint(achievement_bp, url_prefix='/api/achievement')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(search_bp, url_prefix='/api/search')

    # ========== 全局错误处理 ==========
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'code': 404, 'message': '接口不存在'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

    # 健康检查
    @app.route('/api/health')
    def health():
        return jsonify({'code': 200, 'message': 'OK', 'service': 'campus3ai'})

    return app


if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)
