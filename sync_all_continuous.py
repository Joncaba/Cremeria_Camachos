import os
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from supabase import create_client

DB_PATH = os.environ.get("DB_PATH", "pos_cremeria.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

POLL_INTERVAL_SECONDS = int(os.environ.get("SYNC_POLL_INTERVAL", "300"))  # default 5 minutes

TABLES_CONFIG = {
    # ventas: direct table upsert (fecha nullable in Supabase)
    "ventas": {
        "key": "id",
        "select": "SELECT id, NULLIF(fecha, '') as fecha, codigo, nombre, cantidad, precio_unitario, total, tipo_cliente, tipos_pago, monto_efectivo, monto_tarjeta, monto_transferencia, monto_credito, fecha_vencimiento_credito, hora_vencimiento_credito, cliente_credito, pagado, alerta_mostrada, peso_vendido, tipo_venta FROM ventas",
        "remote": "ventas",
    },
    # productos: inventory (normalize tipo_venta: kg→granel)
    "productos": {
        "key": "codigo",
        "select": "SELECT codigo, nombre, stock, stock_kg, stock_minimo, stock_minimo_kg, stock_maximo, stock_maximo_kg, CASE WHEN tipo_venta='kg' THEN 'granel' ELSE COALESCE(tipo_venta, 'unidad') END as tipo_venta, categoria, precio_compra, precio_normal, precio_por_kg FROM productos",
        "remote": "productos",
    },
    # pedidos: MUST sync before pedidos_items (due to FK)
    "pedidos": {
        "key": "id",
        "select": "SELECT id, fecha_pedido, fecha_entrega_esperada, estado, total_productos, total_costo, notas, creado_por, fecha_creacion, orden_compra_id FROM pedidos",
        "remote": "pedidos",
    },
    # pedidos_items: after pedidos
    "pedidos_items": {
        "key": "id",
        "select": "SELECT id, pedido_id, codigo_producto, nombre_producto, cantidad_solicitada, cantidad_recibida, precio_unitario, subtotal, proveedor, estado_item FROM pedidos_items",
        "remote": "pedidos_items",
    },
    # ordenes_compra
    "ordenes_compra": {
        "key": "id",
        "select": "SELECT id, pedido_id, fecha_creacion, total_orden, estado, fecha_pago, notas, creado_por FROM ordenes_compra",
        "remote": "ordenes_compra",
    },
    # usuarios_admin (table renamed to usuarios in Supabase)
    "usuarios_admin": {
        "key": "usuario",
        "select": "SELECT usuario, password, activo, rol, nombre_completo FROM usuarios_admin",
        "remote": "usuarios",
    },
    # devoluciones
    "devoluciones": {
        "key": "id",
        "select": "SELECT id, fecha, codigo_producto, nombre_producto, cantidad, unidad, precio, total, fuente, estado, notas, egreso_id FROM devoluciones",
        "remote": "devoluciones",
    },
    # caja chica
    "caja_chica_movimientos": {
        "key": "id",
        "select": "SELECT id, fecha, tipo, monto, descripcion, usuario, referencia_tipo, referencia_id FROM caja_chica_movimientos",
        "remote": "caja_chica_movimientos",
    },
    # ingresos/egresos adicionales
    "ingresos_pasivos": {
        "key": "id",
        "select": "SELECT id, fecha, descripcion, monto, observaciones, usuario, fuente FROM ingresos_pasivos",
        "remote": "ingresos_pasivos",
    },
    "egresos_adicionales": {
        "key": "id",
        "select": "SELECT id, fecha, tipo, descripcion, monto, observaciones, usuario, fuente FROM egresos_adicionales",
        "remote": "egresos_adicionales",
    },
}


def get_client():
    if not SUPABASE_URL or not SERVICE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment")
    return create_client(SUPABASE_URL, SERVICE_KEY)


def fetch_sqlite_rows(query: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def upsert_batch(client, table: str, rows: List[Dict[str, Any]], on_conflict: str) -> Dict[str, Any]:
    if not rows:
        return {"count": 0, "error": None}
    # Supabase Python v2: prefer table().upsert with on_conflict
    resp = client.table(table).upsert(rows, on_conflict=on_conflict).execute()
    return {"count": len(rows), "error": getattr(resp, "error", None)}


def sync_once():
    client = get_client()
    summary = {}
    # Sort to ensure pedidos syncs before pedidos_items (FK dependency)
    sorted_tables = sorted(TABLES_CONFIG.items(), key=lambda x: (0 if x[0] == "pedidos" else 1 if x[0] == "pedidos_items" else 2))
    for name, cfg in sorted_tables:
        try:
            local_rows = fetch_sqlite_rows(cfg["select"])
            # Normalize datetimes to ISO8601 strings
            for r in local_rows:
                for k, v in list(r.items()):
                    if isinstance(v, datetime):
                        r[k] = v.isoformat(timespec="seconds")
            result = upsert_batch(client, cfg["remote"], local_rows, on_conflict=cfg["key"])
            summary[name] = result
        except Exception as e:
            summary[name] = {"count": 0, "error": str(e)}
    return summary


def main():
    print(f"[sync] Starting continuous sync loop. DB={DB_PATH} interval={POLL_INTERVAL_SECONDS}s")
    while True:
        start = time.time()
        try:
            summary = sync_once()
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[sync] {ts} summary:")
            for k, v in summary.items():
                print(f"  - {k}: sent={v.get('count')} error={v.get('error')}")
        except Exception as e:
            print(f"[sync] Error: {e}")
        elapsed = time.time() - start
        sleep_for = max(1, POLL_INTERVAL_SECONDS - int(elapsed))
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
