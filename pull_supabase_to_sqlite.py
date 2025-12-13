"""
Pull sync desde Supabase hacia SQLite.

Estrategia actual (tabla productos):
- Supabase gana siempre; si existe `updated_at` en ambos lados, solo se aplica cuando Supabase es más reciente.
- Se insertan/reemplazan únicamente las columnas que existen en SQLite para evitar fallos por esquemas distintos.

Uso manual:
    python pull_supabase_to_sqlite.py

Extensión a otras tablas:
- Agrega una entrada en TABLE_CONFIG con `name`, `pk` y opcional `updated_at_field`.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase_client import get_db

SQLITE_PATH = "pos_cremeria.db"


TABLE_CONFIG = [
    {
        "name": "productos",
        "pk": "codigo",
        # Si la tabla tiene columna updated_at en ambos lados, se usa para decidir
        "updated_at_field": "updated_at",
        # Valores por defecto para columnas NOT NULL cuando Supabase envía NULL
        "defaults": {
            "precio_mayoreo_1": 0,
            "precio_mayoreo_2": 0,
            "precio_mayoreo_3": 0,
        },
        # Columnas que deben conservar el valor local si Supabase manda NULL/None
        "preserve_if_none": [
            "numero_producto",  # PLU
        ],
    },
    # Agrega más tablas aquí si las quieres sincronizar en pull.
]


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Normalizar sufijo Z a offset válido
        cleaned = value.replace("Z", "+00:00") if isinstance(value, str) else value
        return datetime.fromisoformat(cleaned)
    except Exception:
        return None


def _get_sqlite_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def _should_apply_remote(cfg: Dict[str, Any], remote_row: Dict[str, Any], local_row: Optional[sqlite3.Row]) -> bool:
    if local_row is None:
        return True  # No existe localmente

    updated_field = cfg.get("updated_at_field")
    if not updated_field:
        return True  # Sin campo de versionado, gana Supabase

    # Si falta el campo en alguno, gana Supabase para simplificar
    if updated_field not in remote_row:
        return False
    if updated_field not in local_row.keys():
        return True

    remote_dt = _parse_dt(remote_row.get(updated_field))
    local_dt = _parse_dt(local_row[updated_field])

    if not remote_dt or not local_dt:
        return True  # Si no se pueden comparar, aplica remoto

    return remote_dt >= local_dt


def sync_table(cfg: Dict[str, Any], conn: sqlite3.Connection, supabase_db) -> Dict[str, int]:
    table = cfg["name"]
    pk = cfg["pk"]
    stats = {"applied": 0, "skipped": 0, "errors": 0}

    # Obtener filas de Supabase
    remote_rows = supabase_db.client.table(table).select("*").execute().data or []

    # Columnas disponibles en SQLite para filtrar
    sqlite_columns = _get_sqlite_columns(conn, table)
    if pk not in sqlite_columns:
        raise RuntimeError(f"La tabla {table} en SQLite no tiene la PK {pk}")

    cur = conn.cursor()

    for remote in remote_rows:
        try:
            pk_value = remote.get(pk)
            if pk_value is None:
                stats["skipped"] += 1
                continue

            cur.execute(f"SELECT * FROM {table} WHERE {pk} = ?", (pk_value,))
            local_row = cur.fetchone()

            if not _should_apply_remote(cfg, remote, local_row):
                stats["skipped"] += 1
                continue

            # Filtrar columnas que existan en SQLite
            payload = {col: remote.get(col) for col in sqlite_columns if col in remote}

            # Aplicar defaults para columnas NOT NULL cuando venga None o falte
            defaults = cfg.get("defaults", {})
            for col, default in defaults.items():
                if col not in sqlite_columns:
                    continue
                if col not in payload or payload[col] is None:
                    payload[col] = default

            # Conservar valores locales para ciertas columnas si vienen como None
            preserve_cols = cfg.get("preserve_if_none", [])
            if preserve_cols and local_row is not None:
                for col in preserve_cols:
                    if col not in sqlite_columns:
                        continue
                    if col not in payload or payload[col] is None:
                        payload[col] = local_row[col]

            if not payload:
                stats["skipped"] += 1
                continue

            columns = list(payload.keys())
            placeholders = ", ".join(["?"] * len(columns))
            sql = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            cur.execute(sql, tuple(payload[col] for col in columns))
            stats["applied"] += 1
        except Exception as exc:  # noqa: BLE001
            print(f"Error aplicando fila en {table}: {exc}")
            stats["errors"] += 1

    conn.commit()
    return stats


def main():
    supabase_db = get_db()
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row

    overall = {}
    for cfg in TABLE_CONFIG:
        try:
            stats = sync_table(cfg, conn, supabase_db)
            overall[cfg["name"]] = stats
        except Exception as exc:  # noqa: BLE001
            overall[cfg["name"]] = {"applied": 0, "skipped": 0, "errors": 1, "error": str(exc)}

    conn.close()

    print("Resumen pull Supabase -> SQLite:")
    for table, stats in overall.items():
        print(f"- {table}: {stats}")


if __name__ == "__main__":
    main()