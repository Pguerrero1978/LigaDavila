"""
Seed script - carga datos de demostración.
Ejecutar con: python seed.py
"""
from app import create_app, db
from app.models import Usuario, Serie, Equipo, Jugador, Partido, Actividad, Noticia
from datetime import date, time

app = create_app('development')

with app.app_context():
    print("⚽  Creando tablas...")
    db.create_all()

    if Usuario.query.count() > 0:
        print("⚠️  Ya existen datos. Omitiendo seed.")
        exit()

    # ── Admin ──
    admin = Usuario(username='admin', email='admin@liga.cl', es_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)

    # ── Series ──
    s1 = Serie(codigo='PA', nombre='Primera Adulta', año=2025, categoria='Adultos')
    s2 = Serie(codigo='SA', nombre='Segunda Adulta', año=2025, categoria='Adultos')
    s3 = Serie(codigo='S14', nombre='Sub-14', año=2025, categoria='Sub-14')
    db.session.add_all([s1, s2, s3])

    # ── Equipos ──
    e1 = Equipo(codigo='DEP01', nombre='Deportivo Norte', color='#e74c3c', delegado='Juan Pérez')
    e2 = Equipo(codigo='ATL02', nombre='Atlético Sur', color='#3498db', delegado='Pedro Gómez')
    e3 = Equipo(codigo='UNI03', nombre='Unión Central', color='#f39c12', delegado='Mario Silva')
    e4 = Equipo(codigo='EST04', nombre='Estrella FC', color='#9b59b6', delegado='Luis Torres')
    db.session.add_all([e1, e2, e3, e4])

    db.session.flush()

    # ── Jugadores ──
    jugadores_data = [
        ('12.345.678-9', 'Carlos Mendoza', date(1995, 3, 15), 'Delantero', s1.id, e1.id),
        ('11.222.333-4', 'Rodrigo Soto', date(1998, 7, 22), 'Mediocampista', s1.id, e1.id),
        ('9.876.543-2', 'Felipe Castro', date(1993, 11, 8), 'Defensa', s1.id, e1.id),
        ('13.456.789-K', 'Andrés Rojas', date(2000, 1, 30), 'Portero', s1.id, e1.id),
        ('14.567.890-1', 'Sebastián Mora', date(1997, 5, 12), 'Delantero', s1.id, e2.id),
        ('10.111.222-3', 'Diego Fuentes', date(1996, 9, 4), 'Mediocampista', s1.id, e2.id),
        ('15.678.901-2', 'Cristian Vega', date(1999, 2, 18), 'Defensa', s1.id, e2.id),
        ('8.765.432-1', 'Pablo Navarro', date(1994, 12, 25), 'Delantero', s1.id, e3.id),
        ('16.789.012-3', 'Ignacio Díaz', date(2001, 6, 7), 'Mediocampista', s1.id, e3.id),
        ('17.890.123-4', 'Mauricio León', date(1992, 8, 14), 'Portero', s1.id, e4.id),
    ]
    jugadores = []
    for rut, nombre, fnac, pos, sid, eid in jugadores_data:
        j = Jugador(rut=rut, nombre=nombre, fecha_nac=fnac, posicion=pos, serie_id=sid, equipo_id=eid)
        db.session.add(j)
        jugadores.append(j)

    db.session.flush()

    # ── Partidos ──
    p1 = Partido(serie_id=s1.id, local_id=e1.id, visita_id=e2.id,
                 fecha=date(2025, 4, 5), hora=time(10, 0), cancha='Estadio Municipal',
                 goles_local=3, goles_visita=1, estado='jugado', arbitro='Roberto Arce')
    p2 = Partido(serie_id=s1.id, local_id=e3.id, visita_id=e4.id,
                 fecha=date(2025, 4, 5), hora=time(12, 0), cancha='Cancha 2',
                 goles_local=0, goles_visita=2, estado='jugado')
    p3 = Partido(serie_id=s1.id, local_id=e2.id, visita_id=e3.id,
                 fecha=date(2025, 4, 12), hora=time(10, 0), cancha='Estadio Municipal',
                 estado='programado')
    p4 = Partido(serie_id=s1.id, local_id=e1.id, visita_id=e4.id,
                 fecha=date(2025, 4, 19), hora=time(11, 0), cancha='Estadio Municipal',
                 estado='programado')
    db.session.add_all([p1, p2, p3, p4])
    db.session.flush()

    # ── Actividades partido 1 ──
    acts = [
        Actividad(partido_id=p1.id, minuto=12, tipo='gol', jugador_id=jugadores[0].id, equipo_id=e1.id, descripcion='Remate de zurda'),
        Actividad(partido_id=p1.id, minuto=28, tipo='tarjeta_amarilla', jugador_id=jugadores[6].id, equipo_id=e2.id),
        Actividad(partido_id=p1.id, minuto=35, tipo='gol', jugador_id=jugadores[1].id, equipo_id=e1.id),
        Actividad(partido_id=p1.id, minuto=47, tipo='gol_penal', jugador_id=jugadores[4].id, equipo_id=e2.id),
        Actividad(partido_id=p1.id, minuto=61, tipo='gol', jugador_id=jugadores[0].id, equipo_id=e1.id, descripcion='Doblete'),
        Actividad(partido_id=p1.id, minuto=75, tipo='tarjeta_roja', jugador_id=jugadores[5].id, equipo_id=e2.id),
        Actividad(partido_id=p1.id, minuto=82, tipo='cambio', jugador_id=jugadores[2].id, equipo_id=e1.id),
        # Partido 2
        Actividad(partido_id=p2.id, minuto=22, tipo='gol', jugador_id=jugadores[8].id, equipo_id=e4.id),
        Actividad(partido_id=p2.id, minuto=55, tipo='gol', jugador_id=jugadores[8].id, equipo_id=e4.id, descripcion='Doblete'),
        Actividad(partido_id=p2.id, minuto=67, tipo='tarjeta_amarilla', jugador_id=jugadores[7].id, equipo_id=e3.id),
    ]
    db.session.add_all(acts)
    # ── Noticias de demo ──
    noticias_demo = [
        Noticia(
            titulo="Deportivo Norte golea 3-1 a Atlético Sur en partidazo",
            resumen="Carlos Mendoza firmó un doblete en el partido más emocionante de la jornada.",
            cuerpo="En un partido lleno de emociones, Deportivo Norte se impuso con autoridad ante Atlético Sur con un marcador de 3-1.\n\nCarlos Mendoza fue la figura del encuentro con dos anotaciones, mientras Rodrigo Soto cerró la cuenta en el segundo tiempo.\n\nAtlético Sur descontó con un gol de penal de Sebastián Mora en el minuto 47, pero no pudo revertir el resultado.",
            categoria="resultado", publicada=True, autor_id=admin.id
        ),
        Noticia(
            titulo="Fixture confirmado para la próxima jornada",
            resumen="Se anuncian los cruces de la segunda fecha de Primera Adulta.",
            cuerpo="La organización confirmó el fixture para la segunda fecha de la Serie Primera Adulta.\n\nAtlético Sur recibirá a Unión Central el próximo sábado a las 10:00 horas en el Estadio Municipal.\n\nLa segunda jornada promete gran nivel ya que todos los equipos buscan consolidarse en la tabla.",
            categoria="fixture", publicada=True, autor_id=admin.id
        ),
        Noticia(
            titulo="Reglamento disciplinario: tarjetas y suspensiones",
            resumen="Recordatorio sobre el sistema de acumulación de tarjetas vigente esta temporada.",
            cuerpo="La comisión disciplinaria recuerda que la acumulación de 3 tarjetas amarillas implica una fecha de suspensión automática.\n\nLas tarjetas rojas directas significan al menos una fecha de sanción, pudiendo ser ampliada según la gravedad de la infracción.",
            categoria="disciplina", publicada=True, autor_id=admin.id
        ),
    ]
    for n in noticias_demo:
        db.session.add(n)

    db.session.commit()

    print("✅  Datos de demostración cargados correctamente.")
    print("   Usuario: admin / Contraseña: admin123")
    print("   Ejecuta: flask run  o  python run.py")

# Correr solo si se llama directamente
if __name__ == '__main__':
    pass
