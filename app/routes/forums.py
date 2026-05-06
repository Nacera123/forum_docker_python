from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.forum import Forum

forums_bp = Blueprint('forums', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@forums_bp.route('/forums')
@login_required
def list_forums():
    forums = Forum.all()
    return render_template('forums.html', forums=forums, user=session['username'])

@forums_bp.route('/forum/new', methods=['POST'])
@login_required
def create_forum():
    name = request.form['name'].strip()

    if not name:
        flash('Le nom du forum est requis.', 'error')
        return redirect(url_for('forums.list_forums'))

    Forum(name=name, creator=session['username']).save()
    return redirect(url_for('forums.list_forums'))

@forums_bp.route('/forum/<fid>')
@login_required
def forum_detail(fid):
    forum = Forum.find(fid)

    if not forum:
        flash('Forum introuvable.', 'error')
        return redirect(url_for('forums.list_forums'))

    Forum.increment_visite(fid)
    forum['nb_visite'] = int(forum['nb_visite']) + 1

    from models.post import Post
    posts = Post.find_by_forum(fid)
    for post in posts:
        post['liked'] = Post.is_liked_by(post['id'], session['username'])

    return render_template('forum.html', forum=forum, fid=fid, posts=posts, user=session['username'])