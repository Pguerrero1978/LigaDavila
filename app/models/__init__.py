from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# ─────────────────────────────────────────────
#  USUARIO (autenticación)
# ─────────────────────────────────────────────
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Usuario {self.username}>'


# ─────────────────────────────────────────────
#  SERIE
# ─────────────────────────────────────────────
class Serie(db.Model):
    __tablename__ = 'series'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    año = db.Column(db.Integer, nullable=False, default=date.today().year)
    categoria = db.Column(db.String(20))  # Sub-8, Sub-10, Adultos, etc.
    activa = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    jugadores = db.relationship('Jugador', backref='serie', lazy='dynamic')
    partidos = db.relationship('Partido', backref='serie', lazy='dynamic')

    @property
    def total_jugadores(self):
        return self.jugadores.count()

    @property
    def total_partidos(self):
        return self.partidos.count()

    @property
    def partidos_jugados(self):
        return self.partidos.filter_by(estado='jugado').count()

    def __repr__(self):
        return f'<Serie {self.codigo} - {self.nombre}>'


# ─────────────────────────────────────────────
#  EQUIPO
# ─────────────────────────────────────────────
class Equipo(db.Model):
    __tablename__ = 'equipos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default='#1a7a3c')
    delegado = db.Column(db.String(100))
    telefono_delegado = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    jugadores = db.relationship('Jugador', backref='equipo', lazy='dynamic')
    partidos_local = db.relationship('Partido', foreign_keys='Partido.local_id', backref='equipo_local', lazy='dynamic')
    partidos_visita = db.relationship('Partido', foreign_keys='Partido.visita_id', backref='equipo_visita', lazy='dynamic')

    @property
    def total_jugadores(self):
        return self.jugadores.count()

    def stats_en_serie(self, serie_id):
        """Calcula estadísticas del equipo en una serie específica."""
        partidos = Partido.query.filter(
            Partido.serie_id == serie_id,
            Partido.estado == 'jugado',
            db.or_(Partido.local_id == self.id, Partido.visita_id == self.id)
        ).all()

        stats = {'pj': 0, 'pg': 0, 'pe': 0, 'pp': 0, 'gf': 0, 'gc': 0, 'pts': 0}
        for p in partidos:
            stats['pj'] += 1
            if p.local_id == self.id:
                gf, gc = p.goles_local, p.goles_visita
            else:
                gf, gc = p.goles_visita, p.goles_local
            stats['gf'] += gf
            stats['gc'] += gc
            if gf > gc:
                stats['pg'] += 1
                stats['pts'] += 3
            elif gf == gc:
                stats['pe'] += 1
                stats['pts'] += 1
            else:
                stats['pp'] += 1
        stats['dg'] = stats['gf'] - stats['gc']
        return stats

    def __repr__(self):
        return f'<Equipo {self.codigo} - {self.nombre}>'


# ─────────────────────────────────────────────
#  JUGADOR
# ─────────────────────────────────────────────
class Jugador(db.Model):
    __tablename__ = 'jugadores'

    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(12), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_nac = db.Column(db.Date)
    posicion = db.Column(db.String(20))  # Portero, Defensa, Mediocampista, Delantero
    foto = db.Column(db.String(200))     # ruta relativa al archivo
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Claves foráneas
    serie_id = db.Column(db.Integer, db.ForeignKey('series.id'))
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id'))

    # Relaciones
    actividades = db.relationship('Actividad', backref='jugador', lazy='dynamic')

    @property
    def edad(self):
        if not self.fecha_nac:
            return None
        hoy = date.today()
        edad = hoy.year - self.fecha_nac.year
        if (hoy.month, hoy.day) < (self.fecha_nac.month, self.fecha_nac.day):
            edad -= 1
        return edad

    @property
    def iniciales(self):
        if not self.nombre:
            return '?'
        parts = self.nombre.strip().split()
        return (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper()

    @property
    def total_goles(self):
        return self.actividades.filter(
            Actividad.tipo.in_(['gol', 'gol_penal'])
        ).count()

    @property
    def total_amarillas(self):
        return self.actividades.filter_by(tipo='tarjeta_amarilla').count()

    @property
    def total_rojas(self):
        return self.actividades.filter_by(tipo='tarjeta_roja').count()

    def __repr__(self):
        return f'<Jugador {self.rut} - {self.nombre}>'


# ─────────────────────────────────────────────
#  PARTIDO
# ─────────────────────────────────────────────
class Partido(db.Model):
    __tablename__ = 'partidos'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time)
    cancha = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='programado')  # programado, jugado, suspendido
    goles_local = db.Column(db.Integer, default=0)
    goles_visita = db.Column(db.Integer, default=0)
    observaciones = db.Column(db.Text)
    arbitro = db.Column(db.String(100))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Claves foráneas
    serie_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)
    local_id = db.Column(db.Integer, db.ForeignKey('equipos.id'), nullable=False)
    visita_id = db.Column(db.Integer, db.ForeignKey('equipos.id'), nullable=False)

    # Relaciones
    actividades = db.relationship('Actividad', backref='partido', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def resultado(self):
        if self.estado == 'jugado':
            return f'{self.goles_local} - {self.goles_visita}'
        return 'vs'

    @property
    def ganador(self):
        if self.estado != 'jugado':
            return None
        if self.goles_local > self.goles_visita:
            return self.equipo_local
        elif self.goles_visita > self.goles_local:
            return self.equipo_visita
        return None  # empate

    @property
    def total_goles_partido(self):
        return (self.goles_local or 0) + (self.goles_visita or 0)

    def __repr__(self):
        return f'<Partido {self.equipo_local.nombre} vs {self.equipo_visita.nombre} - {self.fecha}>'


# ─────────────────────────────────────────────
#  ACTIVIDAD (eventos dentro de un partido)
# ─────────────────────────────────────────────
TIPOS_EVENTO = [
    ('gol', '⚽ Gol'),
    ('gol_penal', '⚽ Gol de penal'),
    ('tarjeta_amarilla', '🟨 Tarjeta amarilla'),
    ('tarjeta_roja', '🟥 Tarjeta roja'),
    ('cambio', '🔄 Cambio'),
    ('autogol', '🙈 Autogol'),
    ('otro', '📌 Otro'),
]


# ─────────────────────────────────────────────
#  NOTICIA
# ─────────────────────────────────────────────
class Noticia(db.Model):
    __tablename__ = 'noticias'

    id         = db.Column(db.Integer, primary_key=True)
    titulo     = db.Column(db.String(200), nullable=False)
    resumen    = db.Column(db.String(400))
    cuerpo     = db.Column(db.Text, nullable=False)
    imagen_url = db.Column(db.String(300))
    categoria  = db.Column(db.String(30), default='general')
    publicada  = db.Column(db.Boolean, default=False)
    creado_en  = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    autor = db.relationship('Usuario', backref='noticias')

    CATEGORIAS = {
        'general':        ('📰', 'General'),
        'resultado':      ('⚽', 'Resultado'),
        'fixture':        ('🗓️', 'Fixture'),
        'disciplina':     ('🟨', 'Disciplina'),
        'transferencia':  ('🔄', 'Transferencia'),
        'institucional':  ('🏛️', 'Institucional'),
    }

    @property
    def categoria_display(self):
        return self.CATEGORIAS.get(self.categoria, ('📰', self.categoria))

    def __repr__(self):
        return f'<Noticia {self.titulo[:40]}>'


class Actividad(db.Model):
    __tablename__ = 'actividades'

    id = db.Column(db.Integer, primary_key=True)
    minuto = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    descripcion = db.Column(db.String(200))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # Claves foráneas
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    jugador_id = db.Column(db.Integer, db.ForeignKey('jugadores.id'))
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id'))

    # Relación con equipo
    equipo = db.relationship('Equipo', backref='actividades')

    @property
    def icono(self):
        iconos = {
            'gol': '⚽', 'gol_penal': '⚽', 'tarjeta_amarilla': '🟨',
            'tarjeta_roja': '🟥', 'cambio': '🔄', 'autogol': '🙈', 'otro': '📌'
        }
        return iconos.get(self.tipo, '📌')

    @property
    def tipo_display(self):
        return dict(TIPOS_EVENTO).get(self.tipo, self.tipo)

    def __repr__(self):
        return f'<Actividad min{self.minuto} - {self.tipo}>'
