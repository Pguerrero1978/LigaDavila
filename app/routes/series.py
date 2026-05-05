from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Serie

series_bp = Blueprint('series', __name__)


@series_bp.route('/')
@login_required
def index():
    series = Serie.query.order_by(Serie.año.desc(), Serie.nombre).all()
    return render_template('series/index.html', series=series)


@series_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        nombre = request.form.get('nombre', '').strip()
        año = request.form.get('año', type=int)
        categoria = request.form.get('categoria', '')

        if not codigo or not nombre or not año:
            flash('Código, nombre y año son obligatorios.', 'danger')
        elif Serie.query.filter_by(codigo=codigo).first():
            flash('El código de serie ya existe.', 'danger')
        else:
            serie = Serie(codigo=codigo, nombre=nombre, año=año, categoria=categoria)
            db.session.add(serie)
            db.session.commit()
            flash(f'Serie {nombre} creada.', 'success')
            return redirect(url_for('series.index'))

    from datetime import date
    return render_template('series/form.html', serie=None, año_actual=date.today().year)


@series_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    serie = Serie.query.get_or_404(id)
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        existente = Serie.query.filter_by(codigo=codigo).first()
        if existente and existente.id != serie.id:
            flash('Ese código ya está en uso.', 'danger')
        else:
            serie.codigo = codigo
            serie.nombre = request.form.get('nombre', '').strip()
            serie.año = request.form.get('año', type=int)
            serie.categoria = request.form.get('categoria', '')
            db.session.commit()
            flash('Serie actualizada.', 'success')
            return redirect(url_for('series.index'))
    from datetime import date
    return render_template('series/form.html', serie=serie, año_actual=date.today().year)


@series_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    serie = Serie.query.get_or_404(id)
    serie.activa = False
    db.session.commit()
    flash('Serie desactivada.', 'info')
    return redirect(url_for('series.index'))
