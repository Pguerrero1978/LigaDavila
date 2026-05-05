from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Partido, Serie, Equipo
from datetime import date

partidos_bp = Blueprint('partidos', __name__)


@partidos_bp.route('/')
@login_required
def index():
    serie_id = request.args.get('serie_id', type=int)
    estado = request.args.get('estado', '')

    query = Partido.query
    if serie_id:
        query = query.filter_by(serie_id=serie_id)
    if estado:
        query = query.filter_by(estado=estado)

    partidos = query.order_by(Partido.fecha.desc()).all()
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()

    return render_template('partidos/index.html',
        partidos=partidos, series=series, serie_id=serie_id, estado=estado)


@partidos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()

    if request.method == 'POST':
        serie_id = request.form.get('serie_id', type=int)
        local_id = request.form.get('local_id', type=int)
        visita_id = request.form.get('visita_id', type=int)
        fecha_str = request.form.get('fecha', '')
        hora_str = request.form.get('hora', '')
        cancha = request.form.get('cancha', '').strip()
        arbitro = request.form.get('arbitro', '').strip()
        obs = request.form.get('observaciones', '').strip()
        gl_str = request.form.get('goles_local', '')
        gv_str = request.form.get('goles_visita', '')

        if not serie_id or not local_id or not visita_id or not fecha_str:
            flash('Serie, equipos y fecha son obligatorios.', 'danger')
        elif local_id == visita_id:
            flash('El equipo local y visita no pueden ser el mismo.', 'danger')
        else:
            from datetime import time
            fecha = date.fromisoformat(fecha_str)
            hora = None
            if hora_str:
                try:
                    h, m = hora_str.split(':')
                    hora = time(int(h), int(m))
                except Exception:
                    pass

            goles_local = int(gl_str) if gl_str.strip() != '' else 0
            goles_visita = int(gv_str) if gv_str.strip() != '' else 0
            estado = 'jugado' if (gl_str.strip() != '' and gv_str.strip() != '') else 'programado'

            partido = Partido(
                serie_id=serie_id, local_id=local_id, visita_id=visita_id,
                fecha=fecha, hora=hora, cancha=cancha, arbitro=arbitro,
                observaciones=obs, goles_local=goles_local, goles_visita=goles_visita,
                estado=estado
            )
            db.session.add(partido)
            db.session.commit()
            flash('Partido registrado.', 'success')
            return redirect(url_for('partidos.index'))

    return render_template('partidos/form.html', series=series, equipos=equipos, partido=None)


@partidos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    partido = Partido.query.get_or_404(id)
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()

    if request.method == 'POST':
        from datetime import time
        partido.serie_id = request.form.get('serie_id', type=int)
        partido.local_id = request.form.get('local_id', type=int)
        partido.visita_id = request.form.get('visita_id', type=int)
        partido.cancha = request.form.get('cancha', '').strip()
        partido.arbitro = request.form.get('arbitro', '').strip()
        partido.observaciones = request.form.get('observaciones', '').strip()

        fecha_str = request.form.get('fecha', '')
        if fecha_str:
            partido.fecha = date.fromisoformat(fecha_str)

        hora_str = request.form.get('hora', '')
        if hora_str:
            try:
                h, m = hora_str.split(':')
                partido.hora = time(int(h), int(m))
            except Exception:
                pass

        gl_str = request.form.get('goles_local', '')
        gv_str = request.form.get('goles_visita', '')
        if gl_str.strip() != '' and gv_str.strip() != '':
            partido.goles_local = int(gl_str)
            partido.goles_visita = int(gv_str)
            partido.estado = 'jugado'
        else:
            partido.estado = request.form.get('estado', 'programado')

        db.session.commit()
        flash('Partido actualizado.', 'success')
        return redirect(url_for('partidos.index'))

    return render_template('partidos/form.html', series=series, equipos=equipos, partido=partido)


@partidos_bp.route('/<int:id>')
@login_required
def detalle(id):
    partido = Partido.query.get_or_404(id)
    actividades = partido.actividades.order_by(db.text('minuto asc')).all()
    return render_template('partidos/detalle.html', partido=partido, actividades=actividades)


@partidos_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    partido = Partido.query.get_or_404(id)
    db.session.delete(partido)
    db.session.commit()
    flash('Partido eliminado.', 'info')
    return redirect(url_for('partidos.index'))
