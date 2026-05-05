from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Bienvenido, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    # Solo permitir registro si no hay usuarios aún (primer uso)
    if Usuario.query.count() > 0 and (not current_user.is_authenticated or not current_user.es_admin):
        flash('El registro está restringido. Contacta al administrador.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
        elif Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
        elif Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'danger')
        else:
            es_primero = Usuario.query.count() == 0
            user = Usuario(username=username, email=email, es_admin=es_primero)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Usuario creado correctamente. Inicia sesión.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/registro.html')
