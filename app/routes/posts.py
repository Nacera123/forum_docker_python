from flask import Blueprint, request, redirect, url_for, session, jsonify
from models.post import Post
from db import get_redis

posts_bp = Blueprint('posts', __name__)
r = get_redis()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@posts_bp.route('/forum/<fid>/post', methods=['POST'])
@login_required
def create_post(fid):
    content = request.form['content'].strip()

    if not content:
        return redirect(url_for('forums.forum_detail', fid=fid, from_post=True))

    Post(content=content, author=session['username'], forum_id=fid).save()
    return redirect(url_for('forums.forum_detail', fid=fid, from_post=True))

@posts_bp.route('/post/<pid>/like', methods=['POST'])
@login_required
def like_post(pid):
    liked = Post.like(pid, session['username'])
    likes = Post.get_likes(pid)
    return jsonify({'liked': liked, 'likes': likes})

@posts_bp.route('/forum/<fid>/notifications', methods=['GET'])
@login_required
def get_forum_notifications(fid):
    """Récupère les nouvelles notifications d'un forum via polling"""
    import json
    notifications = r.lrange(f"forum:{fid}:new_posts_queue", 0, -1)
    parsed_notifs = []
    for notif in notifications:
        try:
            parsed_notifs.append(json.loads(notif))
        except:
            pass
    return jsonify(parsed_notifs)