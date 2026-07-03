# app.py - Flask main entry
from flask import Flask, send_from_directory
from flask_cors import CORS
from models import init_db
import os

app = Flask(__name__, static_folder=None)
CORS(app)
app.config.from_pyfile('config.py')

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    file_path = os.path.join('../frontend', path)
    if os.path.isfile(file_path):
        return send_from_directory('../frontend', path)
    return send_from_directory('../frontend', 'index.html')

# Import and register blueprints
from routes.auth_routes import auth_bp
from routes.time_routes import time_bp
from routes.pomodoro_routes import pomodoro_bp
from routes.achievement_routes import achievement_bp
from routes.ai_routes import ai_bp
from routes.search_routes import search_bp

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(time_bp, url_prefix='/api')
app.register_blueprint(pomodoro_bp, url_prefix='/api')
app.register_blueprint(achievement_bp, url_prefix='/api')
app.register_blueprint(ai_bp, url_prefix='/api')
app.register_blueprint(search_bp, url_prefix='/api')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
