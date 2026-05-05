from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Actividad, Partido, Jugador, Equipo, TIPOS_EVENTO

actividad_bp = Blueprint('actividad', __name__)


@actividad_bp.route('/<int:partido_id>', methods=['GET', 'POST'])
@login_required
def index(partido_id):
    partido = Partido.query.get_or_404(partido_id)
    actividades = partido.actividades.order_by(Actividad.minuto.asc()).all()

    jugadores_local = Jugador.query.filter_by(equipo_id=partido.local_id, activo=True).all()
    jugadores_visita = Jugador.query.filter_by(equipo_id=partido.visita_id, activo=True).all()
    todos_jugadores = jugadores_local + jugadores_visita

    if request.method == 'POST':
        minuto = request.form.get('minuto', type=int)
        tipo = request.form.get('tipo', '')
        jugador_id = request.form.get('jugador_id') or None
        equipo_id = request.form.get('equipo_id') or None
        descripcion = request.form.get('descripcion', '').strip()

        if not minuto or not tipo:
            flash('Minuto y tipo de evento son obligatorios.', 'danger')
        else:
            act = Actividad(
                partido_id=partido_id, minuto=minuto, tipo=tipo,
                jugador_id=jugador_id, equipo_id=equipo_id, descripcion=descripcion
            )
            db.session.add(act)
            db.session.commit()
            flash('Evento registrado.', 'success')
        return redirect(url_for('actividad.index', partido_id=partido_id))

    return render_template('actividad/index.html',
        partido=partido, actividades=actividades,
        todos_jugadores=todos_jugadores,
        jugadores_local=jugadores_local, jugadores_visita=jugadores_visita,
        tipos_evento=TIPOS_EVENTO)


@actividad_bp.route('/<int:partido_id>/eliminar/<int:act_id>', methods=['POST'])
@login_required
def eliminar(partido_id, act_id):
    act = Actividad.query.get_or_404(act_id)
    db.session.delete(act)
    db.session.commit()
    flash('Evento eliminado.', 'info')
    return redirect(url_for('actividad.index', partido_id=partido_id))
