"""
migrate_data.py
───────────────
Transfiere todos los datos de SQLite (instance/liga.db) a PostgreSQL.
Maneja automáticamente la conversión de tipos SQLite → PostgreSQL:
  - Boolean: 0/1 → False/True
  - None: se preserva como NULL

Uso:
    1. Crea las tablas: flask db upgrade
    2. Ejecuta:        python migrate_data.py
"""

import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'liga.db')

_pg_url = os.environ.get('DATABASE_URL', '')
if _pg_url.startswith('postgres://'):
    _pg_url = _pg_url.replace('postgres://', 'postgresql://', 1)

# Orden respetando foreign keys
TABLAS_ORDEN = [
    'usuarios',
    'series',
    'equipos',
    'jugadores',
    'noticias',
    'partidos',
    'actividades',
]

# Columnas Boolean por tabla — SQLite las guarda como 0/1
COLUMNAS_BOOLEAN = {
    'usuarios':    ['es_admin'],
    'series':      ['activa'],
    'equipos':     ['activo'],
    'jugadores':   ['activo'],
    'noticias':    ['publicada'],
    'partidos':    [],
    'actividades': [],
}


def convertir_fila(cols, row, tabla):
    """Convierte tipos SQLite incompatibles con PostgreSQL."""
    bool_cols = set(COLUMNAS_BOOLEAN.get(tabla, []))
    result = {}
    for col, val in zip(cols, row):
        if col in bool_cols and val is not None:
            result[col] = bool(val)   # 0 → False, 1 → True
        else:
            result[col] = val
    return result


def migrar():
    print(f"📂 SQLite  : {SQLITE_PATH}")
    print(f"🐘 PostgreSQL: {_pg_url.split('@')[-1]}\n")

    if not os.path.exists(SQLITE_PATH):
        print(f"❌ No se encontró {SQLITE_PATH}")
        return

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    cur = sqlite_conn.cursor()
    pg_engine = create_engine(_pg_url)

    total_filas = 0

    with pg_engine.begin() as pg_conn:
        # Desactivar FK checks durante la carga
        pg_conn.execute(text("SET session_replication_role = 'replica'"))

        for tabla in TABLAS_ORDEN:
            try:
                cur.execute(f"SELECT * FROM {tabla}")
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()

                if not rows:
                    print(f"  ⚪ {tabla:<15} vacía, se omite")
                    continue

                insert_sql = text(
                    f"INSERT INTO {tabla} ({', '.join(cols)}) "
                    f"VALUES ({', '.join(':' + c for c in cols)}) "
                    f"ON CONFLICT DO NOTHING"
                )

                filas_convertidas = [convertir_fila(cols, row, tabla) for row in rows]
                pg_conn.execute(insert_sql, filas_convertidas)

                # Sincronizar secuencia SERIAL para que el próximo INSERT no colisione
                pg_conn.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                    f"COALESCE(MAX(id), 1)) FROM {tabla}"
                ))

                total_filas += len(rows)
                print(f"  ✅ {tabla:<15} {len(rows):>4} filas migradas")

            except Exception as e:
                print(f"  ❌ {tabla:<15} ERROR → {e}")

        # Reactivar FK checks
        pg_conn.execute(text("SET session_replication_role = 'origin'"))

    sqlite_conn.close()
    print(f"\n🎉 Migración completada — {total_filas} filas en total.")


if __name__ == '__main__':
    migrar()
