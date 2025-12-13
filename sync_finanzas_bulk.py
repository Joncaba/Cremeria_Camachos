import os
import sqlite3
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.environ.get("POS_DB_PATH", "pos_cremeria.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

TABLES = {
    "egresos_adicionales": "upsert_egreso_adicional",
    "ingresos_pasivos": "upsert_ingreso_pasivo",
    "caja_chica_movimientos": "upsert_caja_chica_movimiento",
    "ordenes_compra": "upsert_orden_compra",
}


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def load_rows(conn, table):
    cur = conn.cursor()
    cur.row_factory = dict_factory
    cur.execute(f"SELECT * FROM {table}")
    return cur.fetchall()


def ensure_env():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Define SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (o SUPABASE_KEY)")


def cast_row(row):
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def main():
    ensure_env()
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = sqlite3.connect(DB_PATH)
    try:
        total_sent = 0
        for table, rpc in TABLES.items():
            rows = load_rows(conn, table)
            print(f"{table}: {len(rows)} registros a enviar")
            for r in rows:
                payload_row = cast_row(r)
                # Evita fallo por FK de pedidos: si no existen en Supabase, no envíes pedido_id
                if table == "ordenes_compra":
                    # Si no hay pedidos sincronizados, nullear pedido_id para no romper FK
                    if "pedido_id" in payload_row:
                        payload_row["pedido_id"] = None
                payload = {"_row": payload_row}
                resp = client.rpc(rpc, payload).execute()
                # Supabase v2 returns an APIResponse object with .data and .error
                error = getattr(resp, "error", None)
                if error:
                    raise RuntimeError(f"Error en {rpc}: {error}")
                total_sent += 1
        print(f"Sincronización completa. Registros enviados: {total_sent}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
