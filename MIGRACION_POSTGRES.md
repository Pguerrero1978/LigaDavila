# Migración SQLite → PostgreSQL

## Qué cambió en el proyecto

| Archivo | Cambio |
|---|---|
| `requirements.txt` | Se agregó `psycopg2-binary==2.9.9` |
| `config.py` | Nueva URL PostgreSQL + pool de conexiones + fix para Railway |
| `.env` | `DATABASE_URL` apunta a PostgreSQL |
| `migrate_data.py` | Script nuevo para transferir datos existentes |

> **Los modelos, rutas y templates NO se modificaron** — SQLAlchemy abstrae las diferencias.

---

## Pasos de migración

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Crear la base de datos en PostgreSQL
```sql
-- En psql o cualquier cliente PostgreSQL:
CREATE DATABASE liga_db;
```

### 3. Configurar .env
Edita `.env` y reemplaza la URL con tus datos reales:
```
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/liga_db
```

### 4. Crear las tablas en PostgreSQL
```bash
flask db upgrade
```
Esto aplica la migración existente (`0b456127f6e3_init.py`) sobre PostgreSQL.

### 5. Migrar datos existentes (opcional)
Si tienes datos en SQLite que quieres conservar:
```bash
python migrate_data.py
```

### 6. Verificar
```bash
flask run
```

---

## Por plataforma

### Railway
Railway entrega una variable `DATABASE_URL` automáticamente.
El `config.py` ya maneja el prefijo `postgres://` → `postgresql://`.
Solo agrega la variable de entorno en el panel de Railway.

### Supabase
```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
```

### Render
Render también entrega `DATABASE_URL` automáticamente en el panel.

### Local con Docker
```bash
docker run -d \
  --name liga_postgres \
  -e POSTGRES_PASSWORD=mipassword \
  -e POSTGRES_DB=liga_db \
  -p 5432:5432 \
  postgres:16-alpine
```
Luego: `DATABASE_URL=postgresql://postgres:mipassword@localhost:5432/liga_db`

---

## Diferencias SQLite vs PostgreSQL a tener en cuenta

- **LIKE**: En PostgreSQL es case-sensitive. Si usas búsquedas, cambia a `ILIKE`.
- **Boolean**: PostgreSQL usa `TRUE/FALSE`, SQLite usaba `1/0` — SQLAlchemy lo maneja automáticamente.
- **Fechas**: Sin cambios, SQLAlchemy las serializa igual.
- **Concurrencia**: PostgreSQL maneja múltiples conexiones simultáneas — listo para producción.
