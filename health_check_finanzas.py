import os
from supabase import create_client
from dotenv import load_dotenv

EXPECTED = {
    "egresos_adicionales": 6,
    "ingresos_pasivos": 2,
    "caja_chica_movimientos": 1,
    "ordenes_compra": 3,
}

QUERIES = {
    "egresos_adicionales": "SELECT COUNT(*) AS count FROM public.egresos_adicionales",
    "ingresos_pasivos": "SELECT COUNT(*) AS count FROM public.ingresos_pasivos",
    "caja_chica_movimientos": "SELECT COUNT(*) AS count FROM public.caja_chica_movimientos",
    "ordenes_compra": "SELECT COUNT(*) AS count FROM public.ordenes_compra",
}


def main():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY/KEY en entorno/.env")

    client = create_client(url, key)

    ok = True
    for name, sql in QUERIES.items():
        resp = client.postgrest.rpc("exec_sql", {"sql": sql}).execute() if False else None  # placeholder if RPC exists
        # Como no tenemos RPC genérico, usamos client.table with count via select('*', count='exact') no aplica; hacemos REST query directo
        data = client.table(name).select("id", count="exact").execute()
        count = getattr(data, "count", None)
        print(f"{name}: {count}")
        expected = EXPECTED.get(name)
        if expected is not None and count is not None:
            if count < expected:
                ok = False
                print(f"ALERTA: {name} bajó de {expected} a {count}")
    if not ok:
        # Exit code non-zero to signal scheduler/log watchers
        raise SystemExit(1)


if __name__ == "__main__":
    main()
