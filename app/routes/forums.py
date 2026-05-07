from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.forum import Forum
from models.post import Post

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
    sort_order = request.args.get('sort', 'desc')  # 'asc' ou 'desc'
    forums = Forum.all(sort=sort_order)
    
    # Ajouter le nombre de posts non lus pour chaque forum
    for forum in forums:
        forum['unread_count'] = Post.get_unread_count(forum['id'], session['username'])
    
    return render_template('forums.html', forums=forums, user=session['username'], sort_order=sort_order)

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
    
    from_post = request.args.get('from_post', False)
    if not from_post:
        Forum.increment_visite(fid)
        forum['nb_visite'] = int(forum['nb_visite']) + 1

    posts = Post.find_by_forum(fid)
    for post in posts:
        post['liked'] = Post.is_liked_by(post['id'], session['username'])
    
    # Marquer les posts comme lus
    Post.mark_forum_as_read(fid, session['username'])

    return render_template('forum.html', forum=forum, fid=fid, posts=posts, user=session['username'])