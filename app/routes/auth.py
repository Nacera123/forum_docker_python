from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            flash('Tous les champs sont requis.', 'error')
            return render_template('auth.html', mode='register')

        if User.exists(username):
            flash('Nom d\'utilisateur déjà pris.', 'error')
            return render_template('auth.html', mode='register')

        User(username, password).save()
        session['username'] = username
        return redirect(url_for('forums.list_forums'))

    return render_template('auth.html', mode='register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not User.verify_password(username, password):
            flash('Identifiants incorrects.', 'error')
            return render_template('auth.html', mode='login')

        session['username'] = username
        return redirect(url_for('forums.list_forums'))

    return render_template('auth.html', mode='login')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))