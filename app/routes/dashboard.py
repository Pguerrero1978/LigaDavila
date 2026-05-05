from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Jugador, Equipo, Serie, Partido, Actividad
from app import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    # Estadísticas generales
    total_jugadores = Jugador.query.filter_by(activo=True).count()
    total_equipos = Equipo.query.filter_by(activo=True).count()
    total_series = Serie.query.filter_by(activa=True).count()
    partidos_jugados = Partido.query.filter_by(estado='jugado').count()
    partidos_programados = Partido.query.filter_by(estado='programado').count()

    # Total goles
    total_goles = db.session.query(func.sum(Partido.goles_local + Partido.goles_visita))\
        .filter_by(estado='jugado').scalar() or 0

    # Últimos 5 partidos jugados
    ultimos_partidos = Partido.query\
        .filter_by(estado='jugado')\
        .order_by(Partido.fecha.desc())\
        .limit(5).all()

    # Próximos partidos
    from datetime import date
    proximos_partidos = Partido.query\
        .filter_by(estado='programado')\
        .filter(Partido.fecha >= date.today())\
        .order_by(Partido.fecha.asc())\
        .limit(5).all()

    # Top 7 goleadores
    goleadores = db.session.query(
        Jugador,
        func.count(Actividad.id).label('goles')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo.in_(['gol', 'gol_penal']))\
     .group_by(Jugador.id)\
     .order_by(func.count(Actividad.id).desc())\
     .limit(7).all()

    # Equipos más activos (más partidos)
    equipos_activos = db.session.query(
        Equipo,
        func.count(Partido.id).label('total')
    ).join(Partido, db.or_(Partido.local_id == Equipo.id, Partido.visita_id == Equipo.id))\
     .filter(Partido.estado == 'jugado')\
     .group_by(Equipo.id)\
     .order_by(func.count(Partido.id).desc())\
     .limit(5).all()

    return render_template('dashboard.html',
        total_jugadores=total_jugadores,
        total_equipos=total_equipos,
        total_series=total_series,
        partidos_jugados=partidos_jugados,
        partidos_programados=partidos_programados,
        total_goles=total_goles,
        ultimos_partidos=ultimos_partidos,
        proximos_partidos=proximos_partidos,
        goleadores=goleadores,
        equipos_activos=equipos_activos,
    )
