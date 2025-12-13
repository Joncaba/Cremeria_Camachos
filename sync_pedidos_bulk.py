import os
import sqlite3
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.environ.get("POS_DB_PATH", "pos_cremeria.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

TABLE = "pedidos"
RPC = "upsert_pedido"  # Debe existir en Supabase; si no, se usará inserción directa


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def load_rows(conn):
    cur = conn.cursor()
    cur.row_factory = dict_factory
    cur.execute(f"SELECT * FROM {TABLE}")
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


def upsert_via_rpc(client, row):
    payload = {"_row": cast_row(row)}
    resp = client.rpc(RPC, payload).execute()
    error = getattr(resp, "error", None)
    if error:
        raise RuntimeError(f"Error RPC {RPC}: {error}")


def upsert_direct(client, row):
    # Inserción directa en tabla pedidos si no hay RPC
    data = cast_row(row)
    # Usa upsert por id
    resp = client.table("pedidos").upsert(data, on_conflict="id").execute()
    error = getattr(resp, "error", None)
    if error:
        raise RuntimeError(f"Error upsert directo pedidos: {error}")


def main():
    ensure_env()
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = load_rows(conn)
        print(f"pedidos: {len(rows)} registros a enviar")
        # Detecta si existe RPC consultando el schema (best-effort): si falla, usa directo
        use_rpc = True
        try:
            test = client.rpc(RPC, {"_row": {"id": 0}}).execute()
            # No importa que falle por datos; si no existe, dará error de rutina
        except Exception:
            use_rpc = False
            print("RPC upsert_pedido no disponible; usando upsert directo")

        sent = 0
        for r in rows:
            if use_rpc:
                upsert_via_rpc(client, r)
            else:
                upsert_direct(client, r)
            sent += 1
        print(f"Sincronización de pedidos completa. Enviados: {sent}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
