# ⚽ Liga Control — Sistema Completo de Liga Deportiva

Sistema web full-stack con **Flask + SQLAlchemy**. Incluye **Panel Admin** + **Portal Público**.

---

## URLs del sistema

### Portal Público (sin login requerido)
| URL | Descripción |
|-----|-------------|
| `/` | Portada: hero, últimos resultados, top goleadores, noticias |
| `/equipos` | Grid de todos los equipos |
| `/equipos/<id>` | Plantilla + estadísticas + últimos partidos del equipo |
| `/jugadores` | Grilla con filtros por equipo/serie/posición |
| `/jugadores/<id>` | Perfil completo + historial de eventos |
| `/partidos` | Lista de partidos con filtros |
| `/partidos/<id>` | Marcador grande + timeline de eventos |
| `/tabla` | Tabla de posiciones por serie |
| `/estadisticas` | Goleadores, tarjetas, goles por equipo |
| `/noticias` | Listado con paginación |
| `/noticias/<id>` | Artículo completo + noticias recientes |

### Panel Admin (requiere login)
| URL | Descripción |
|-----|-------------|
| `/login` | Inicio de sesión |
| `/admin` | Dashboard con estadísticas globales |
| `/admin/jugadores` | CRUD + foto upload |
| `/admin/series` | CRUD series |
| `/admin/equipos` | CRUD equipos |
| `/admin/partidos` | CRUD + resultados |
| `/admin/actividad/<id>` | Timeline de eventos por partido |
| `/admin/goleadores` | Rankings + tarjetas |
| `/admin/tabla` | Tabla de posiciones |
| `/admin/noticias` | CRUD noticias + publicar/despublicar |

---

## Instalación rápida

```bash
cd liga_app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
flask db init && flask db migrate -m "init" && flask db upgrade
python seed.py          # datos demo (admin/admin123)
python run.py           # http://localhost:5000
```

Portal público: **http://localhost:5000**
Admin: **http://localhost:5000/admin**

---

## Modelos de datos

```
Usuario → Serie → Partido → Actividad
                ↗         ↗
       Equipo → Jugador →
Noticia → Usuario
```

Tipos de evento en Actividad: `gol`, `gol_penal`, `tarjeta_amarilla`, `tarjeta_roja`, `cambio`, `autogol`, `otro`

---

## Producción

```bash
pip install gunicorn psycopg2-binary
# Editar .env: DATABASE_URL=postgresql://...
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```
