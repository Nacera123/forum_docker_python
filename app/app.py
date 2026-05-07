import os
from flask import Flask, redirect, url_for
from flask_session import Session
import redis
from routes.auth import auth_bp
from routes.forums import forums_bp
from routes.posts import posts_bp

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(
    f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/{os.getenv('REDIS_DB', 1)}"
)
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 heures

Session(app)

# enregistrement des blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(forums_bp)
app.register_blueprint(posts_bp)

# supprimer login_required dupliqué des routes
@app.before_request
def require_login():
    from flask import request, session
    public_routes = ['auth.login', 'auth.register']
    if request.endpoint not in public_routes and 'username' not in session:
        return redirect(url_for('auth.login'))

@app.route('/')
def index():
    return redirect(url_for('forums.list_forums'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)