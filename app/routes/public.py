from flask import Blueprint, render_template, abort, request
from app.models import (
    Jugador, Equipo, Serie, Partido, Actividad, Noticia
)
from app import db
from sqlalchemy import func, desc
from datetime import date

public_bp = Blueprint('public', __name__)


# ──────────────────────────────────────────────────────────
#  HOME
# ──────────────────────────────────────────────────────────
@public_bp.route('/')
def home():
    # Últimos 3 resultados
    ultimos = Partido.query.filter_by(estado='jugado')\
        .order_by(Partido.fecha.desc()).limit(3).all()

    # Próximos 3 partidos
    proximos = Partido.query.filter_by(estado='programado')\
        .filter(Partido.fecha >= date.today())\
        .order_by(Partido.fecha.asc()).limit(3).all()

    # Top 5 goleadores (global)
    top_goleadores = db.session.query(
        Jugador, func.count(Actividad.id).label('goles')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo.in_(['gol', 'gol_penal']))\
     .group_by(Jugador.id)\
     .order_by(desc('goles')).limit(5).all()

    # Estadísticas globales
    total_goles = db.session.query(
        func.count(Actividad.id)
    ).filter(Actividad.tipo.in_(['gol', 'gol_penal'])).scalar() or 0

    total_partidos = Partido.query.filter_by(estado='jugado').count()
    total_equipos  = Equipo.query.filter_by(activo=True).count()
    total_jugadores = Jugador.query.filter_by(activo=True).count()

    # Series activas
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()

    # Últimas noticias (3)
    noticias = Noticia.query.filter_by(publicada=True)\
        .order_by(Noticia.creado_en.desc()).limit(3).all()

    return render_template('public/home.html',
        ultimos=ultimos, proximos=proximos,
        top_goleadores=top_goleadores,
        total_goles=total_goles, total_partidos=total_partidos,
        total_equipos=total_equipos, total_jugadores=total_jugadores,
        series=series, noticias=noticias)


# ──────────────────────────────────────────────────────────
#  EQUIPOS
# ──────────────────────────────────────────────────────────
@public_bp.route('/equipos')
def equipos():
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()
    return render_template('public/equipos.html', equipos=equipos)


@public_bp.route('/equipos/<int:id>')
def equipo_detalle(id):
    equipo = Equipo.query.get_or_404(id)
    jugadores = Jugador.query.filter_by(equipo_id=id, activo=True)\
        .order_by(Jugador.posicion, Jugador.nombre).all()

    # Estadísticas del equipo (todos los partidos)
    partidos_local  = Partido.query.filter_by(local_id=id, estado='jugado').all()
    partidos_visita = Partido.query.filter_by(visita_id=id, estado='jugado').all()
    todos_partidos  = partidos_local + partidos_visita
    todos_partidos.sort(key=lambda p: p.fecha, reverse=True)

    pj = len(todos_partidos)
    pg = pe = pp = gf = gc = 0
    for p in todos_partidos:
        if p.local_id == id:
            f, c = p.goles_local, p.goles_visita
        else:
            f, c = p.goles_visita, p.goles_local
        gf += f; gc += c
        if f > c: pg += 1
        elif f == c: pe += 1
        else: pp += 1

    stats = dict(pj=pj, pg=pg, pe=pe, pp=pp, gf=gf, gc=gc,
                 pts=pg*3+pe, dg=gf-gc)

    # Goleadores del equipo
    goleadores_eq = db.session.query(
        Jugador, func.count(Actividad.id).label('goles')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo.in_(['gol', 'gol_penal']),
             Jugador.equipo_id == id)\
     .group_by(Jugador.id)\
     .order_by(desc('goles')).all()

    return render_template('public/equipo_detalle.html',
        equipo=equipo, jugadores=jugadores,
        todos_partidos=todos_partidos[:8],
        stats=stats, goleadores_eq=goleadores_eq)


# ──────────────────────────────────────────────────────────
#  JUGADORES
# ──────────────────────────────────────────────────────────
@public_bp.route('/jugadores')
def jugadores():
    equipo_id = request.args.get('equipo_id', type=int)
    serie_id  = request.args.get('serie_id', type=int)
    posicion  = request.args.get('posicion', '')
    q         = request.args.get('q', '').strip()

    query = Jugador.query.filter_by(activo=True)
    if equipo_id: query = query.filter_by(equipo_id=equipo_id)
    if serie_id:  query = query.filter_by(serie_id=serie_id)
    if posicion:  query = query.filter_by(posicion=posicion)
    if q:         query = query.filter(Jugador.nombre.ilike(f'%{q}%'))

    jugadores = query.order_by(Jugador.nombre).all()
    equipos   = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()
    series    = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()

    return render_template('public/jugadores.html',
        jugadores=jugadores, equipos=equipos, series=series,
        equipo_id=equipo_id, serie_id=serie_id,
        posicion=posicion, q=q)


@public_bp.route('/jugadores/<int:id>')
def jugador_detalle(id):
    jugador = Jugador.query.get_or_404(id)
    actividades = Actividad.query.filter_by(jugador_id=id)\
        .order_by(Actividad.creado_en.desc()).all()
    return render_template('public/jugador_detalle.html',
        jugador=jugador, actividades=actividades)


# ──────────────────────────────────────────────────────────
#  PARTIDOS
# ──────────────────────────────────────────────────────────
@public_bp.route('/partidos')
def partidos():
    serie_id = request.args.get('serie_id', type=int)
    estado   = request.args.get('estado', '')

    query = Partido.query
    if serie_id: query = query.filter_by(serie_id=serie_id)
    if estado:   query = query.filter_by(estado=estado)

    partidos = query.order_by(Partido.fecha.desc()).all()
    series   = Serie.query.filter_by(activa=True).all()

    return render_template('public/partidos.html',
        partidos=partidos, series=series,
        serie_id=serie_id, estado=estado)


@public_bp.route('/partidos/<int:id>')
def partido_detalle(id):
    partido     = Partido.query.get_or_404(id)
    actividades = partido.actividades.order_by(Actividad.minuto.asc()).all()

    # Estadísticas rápidas del partido
    goles_local   = [a for a in actividades if a.tipo in ('gol','gol_penal') and a.equipo_id == partido.local_id]
    goles_visita  = [a for a in actividades if a.tipo in ('gol','gol_penal') and a.equipo_id == partido.visita_id]
    amarillas     = [a for a in actividades if a.tipo == 'tarjeta_amarilla']
    rojas         = [a for a in actividades if a.tipo == 'tarjeta_roja']

    return render_template('public/partido_detalle.html',
        partido=partido, actividades=actividades,
        goles_local=goles_local, goles_visita=goles_visita,
        amarillas=amarillas, rojas=rojas)


# ──────────────────────────────────────────────────────────
#  TABLA DE POSICIONES
# ──────────────────────────────────────────────────────────
@public_bp.route('/tabla')
def tabla():
    serie_id = request.args.get('serie_id', type=int)
    series   = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()

    # Si no hay serie seleccionada, usar la primera disponible
    if not serie_id and series:
        serie_id = series[0].id

    serie = Serie.query.get(serie_id) if serie_id else None
    tabla_data = []

    if serie_id:
        equipos = Equipo.query.filter_by(activo=True).all()
        for eq in equipos:
            stats = eq.stats_en_serie(serie_id)
            if stats['pj'] > 0:
                stats['equipo'] = eq
                tabla_data.append(stats)
        tabla_data.sort(key=lambda x: (-x['pts'], -x['dg'], -x['gf']))

    return render_template('public/tabla.html',
        tabla=tabla_data, series=series,
        serie=serie, serie_id=serie_id)


# ──────────────────────────────────────────────────────────
#  ESTADÍSTICAS
# ──────────────────────────────────────────────────────────
@public_bp.route('/estadisticas')
def estadisticas():
    serie_id = request.args.get('serie_id', type=int)
    series   = Serie.query.filter_by(activa=True).all()

    pids_filter = None
    if serie_id:
        pids_filter = [p.id for p in Partido.query.filter_by(serie_id=serie_id).all()]

    def apply_partido_filter(q):
        if pids_filter is not None:
            return q.filter(Actividad.partido_id.in_(pids_filter))
        return q

    # Goleadores
    goleadores_q = db.session.query(
        Jugador, func.count(Actividad.id).label('cnt')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo.in_(['gol','gol_penal']))
    goleadores_q = apply_partido_filter(goleadores_q)
    goleadores = goleadores_q.group_by(Jugador.id).order_by(desc('cnt')).limit(15).all()

    # Asistencias (cambios como proxy si no hay asistencias)
    # Amarillas
    amarillas_q = db.session.query(
        Jugador, func.count(Actividad.id).label('cnt')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo == 'tarjeta_amarilla')
    amarillas_q = apply_partido_filter(amarillas_q)
    amarillas = amarillas_q.group_by(Jugador.id).order_by(desc('cnt')).limit(10).all()

    # Rojas
    rojas_q = db.session.query(
        Jugador, func.count(Actividad.id).label('cnt')
    ).join(Actividad, Actividad.jugador_id == Jugador.id)\
     .filter(Actividad.tipo == 'tarjeta_roja')
    rojas_q = apply_partido_filter(rojas_q)
    rojas = rojas_q.group_by(Jugador.id).order_by(desc('cnt')).limit(10).all()

    # Goles por equipo
    goles_eq_q = db.session.query(
        Equipo, func.count(Actividad.id).label('cnt')
    ).join(Actividad, Actividad.equipo_id == Equipo.id)\
     .filter(Actividad.tipo.in_(['gol','gol_penal']))
    goles_eq_q = apply_partido_filter(goles_eq_q)
    goles_equipo = goles_eq_q.group_by(Equipo.id).order_by(desc('cnt')).all()

    max_goles_eq = goles_equipo[0][1] if goles_equipo else 1

    # Globales
    total_goles     = sum(c for _, c in goles_equipo)
    total_amarillas = sum(c for _, c in amarillas)
    total_rojas     = sum(c for _, c in rojas)
    total_partidos  = Partido.query.filter_by(estado='jugado').count()
    promedio_goles  = round(total_goles / total_partidos, 1) if total_partidos else 0

    return render_template('public/estadisticas.html',
        goleadores=goleadores, amarillas=amarillas, rojas=rojas,
        goles_equipo=goles_equipo, max_goles_eq=max_goles_eq,
        total_goles=total_goles, total_amarillas=total_amarillas,
        total_rojas=total_rojas, promedio_goles=promedio_goles,
        series=series, serie_id=serie_id)


# ──────────────────────────────────────────────────────────
#  NOTICIAS
# ──────────────────────────────────────────────────────────
@public_bp.route('/noticias')
def noticias():
    page     = request.args.get('page', 1, type=int)
    noticias = Noticia.query.filter_by(publicada=True)\
        .order_by(Noticia.creado_en.desc())\
        .paginate(page=page, per_page=9, error_out=False)
    return render_template('public/noticias.html', noticias=noticias)


@public_bp.route('/noticias/<int:id>')
def noticia_detalle(id):
    noticia   = Noticia.query.get_or_404(id)
    if not noticia.publicada:
        abort(404)
    recientes = Noticia.query.filter_by(publicada=True)\
        .filter(Noticia.id != id)\
        .order_by(Noticia.creado_en.desc()).limit(4).all()
    return render_template('public/noticia_detalle.html',
        noticia=noticia, recientes=recientes)
