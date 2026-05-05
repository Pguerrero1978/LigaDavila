from flask import Blueprint, render_template, request
from flask_login import login_required
from app import db
from app.models import Jugador, Actividad, Serie, Equipo, Partido
from sqlalchemy import func

goleadores_bp = Blueprint('goleadores', __name__)


@goleadores_bp.route('/')
@login_required
def index():
    serie_id = request.args.get('serie_id', type=int)
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()

    query = db.session.query(
        Jugador,
        func.count(Actividad.id).label('goles')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo.in_(['gol', 'gol_penal']))

    if serie_id:
        pids = [p.id for p in Partido.query.filter_by(serie_id=serie_id).all()]
        query = query.filter(Actividad.partido_id.in_(pids))

    goleadores = query.group_by(Jugador.id)\
        .order_by(func.count(Actividad.id).desc()).all()

    # Amarillas y rojas
    amarillas = db.session.query(
        Jugador, func.count(Actividad.id).label('cnt')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo == 'tarjeta_amarilla')\
     .group_by(Jugador.id)\
     .order_by(func.count(Actividad.id).desc()).limit(10).all()

    rojas = db.session.query(
        Jugador, func.count(Actividad.id).label('cnt')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo == 'tarjeta_roja')\
     .group_by(Jugador.id)\
     .order_by(func.count(Actividad.id).desc()).limit(10).all()

    # Goles por equipo
    goles_equipo_query = db.session.query(
        Equipo, func.count(Actividad.id).label('goles')
    ).join(Actividad, Actividad.equipo_id == Equipo.id)\
     .filter(Actividad.tipo.in_(['gol', 'gol_penal']))
    if serie_id:
        goles_equipo_query = goles_equipo_query.filter(Actividad.partido_id.in_(pids if serie_id else []))
    goles_equipo = goles_equipo_query.group_by(Equipo.id)\
        .order_by(func.count(Actividad.id).desc()).all()

    max_goles_eq = goles_equipo[0][1] if goles_equipo else 1

    return render_template('goleadores/index.html',
        goleadores=goleadores, amarillas=amarillas, rojas=rojas,
        goles_equipo=goles_equipo, max_goles_eq=max_goles_eq,
        series=series, serie_id=serie_id)


# ─────────────────────────────────────────────
#  TABLA DE POSICIONES
# ─────────────────────────────────────────────
tabla_bp = Blueprint('tabla', __name__)


@tabla_bp.route('/')
@login_required
def index():
    serie_id = request.args.get('serie_id', type=int)
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()
    serie = Serie.query.get(serie_id) if serie_id else None
    tabla = []

    if serie_id:
        equipos = Equipo.query.filter_by(activo=True).all()
        for eq in equipos:
            stats = eq.stats_en_serie(serie_id)
            if stats['pj'] > 0:
                stats['equipo'] = eq
                tabla.append(stats)

        tabla.sort(key=lambda x: (-x['pts'], -x['dg'], -x['gf']))

    return render_template('tabla/index.html',
        tabla=tabla, series=series, serie=serie, serie_id=serie_id)
