from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Equipo

equipos_bp = Blueprint('equipos', __name__)


@equipos_bp.route('/')
@login_required
def index():
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()
    return render_template('equipos/index.html', equipos=equipos)


@equipos_bp.route('/nuevo', methods=['GET', 'POST'])
@equipos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def form(id=None):
    equipo = Equipo.query.get_or_404(id) if id else None

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        nombre = request.form.get('nombre', '').strip()
        color = request.form.get('color', '#1a7a3c')
        delegado = request.form.get('delegado', '').strip()
        telefono = request.form.get('telefono_delegado', '').strip()

        if not codigo or not nombre:
            flash('Código y nombre son obligatorios.', 'danger')
        else:
            existente = Equipo.query.filter_by(codigo=codigo).first()
            if existente and (not equipo or existente.id != equipo.id):
                flash('El código de equipo ya existe.', 'danger')
            else:
                if equipo:
                    equipo.codigo = codigo
                    equipo.nombre = nombre
                    equipo.color = color
                    equipo.delegado = delegado
                    equipo.telefono_delegado = telefono
                    flash('Equipo actualizado.', 'success')
                else:
                    equipo = Equipo(codigo=codigo, nombre=nombre, color=color,
                                   delegado=delegado, telefono_delegado=telefono)
                    db.session.add(equipo)
                    flash(f'Equipo {nombre} creado.', 'success')
                db.session.commit()
                return redirect(url_for('equipos.index'))

    return render_template('equipos/form.html', equipo=equipo)


@equipos_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    equipo = Equipo.query.get_or_404(id)
    equipo.activo = False
    db.session.commit()
    flash(f'Equipo {equipo.nombre} desactivado.', 'info')
    return redirect(url_for('equipos.index'))
