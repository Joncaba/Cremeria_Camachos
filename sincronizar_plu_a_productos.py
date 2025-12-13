import sqlite3

DB_PATH = "pos_cremeria.db"

INSERT_SQL = """
INSERT INTO productos (
    codigo, numero_producto, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3,
    stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg,
    stock_minimo, stock_minimo_kg, stock_maximo, stock_maximo_kg, categoria
) VALUES (
    ?, ?, ?, 0, ?, 0, 0, 0,
    0, 'unidad', 0, 0, 0,
    0, 0, 30, 0, 'otros'
)
"""

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Ensure reference tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plu_catalogo'")
    if cur.fetchone() is None:
        print("Tabla plu_catalogo no existe. Ejecuta importar_itegra_plu.py primero.")
        return

    # Add numero_producto column if it doesn't exist
    try:
        cur.execute("PRAGMA table_info(productos)")
        columns = [col[1] for col in cur.fetchall()]
        if 'numero_producto' not in columns:
            print("Agregando columna numero_producto...")
            cur.execute("ALTER TABLE productos ADD COLUMN numero_producto INTEGER")
            conn.commit()
    except Exception as e:
        print(f"Nota: {e}")

    # Load existing product codes to avoid duplicates
    cur.execute("SELECT codigo FROM productos")
    existing = {row[0] for row in cur.fetchall()}

    # Build mapping from barcode to PLU
    cur.execute("SELECT codigo, plu FROM codigos_barras")
    barcode_to_plu = {row[0]: row[1] for row in cur.fetchall() if row[0]}

    # Iterate PLU catalog and insert missing
    cur.execute("SELECT plu, nombre, precio FROM plu_catalogo")
    inserted = 0
    for plu, nombre, precio in cur.fetchall():
        # Prefer barcode as codigo; fallback to just the PLU number
        barcode = None
        for code, p in barcode_to_plu.items():
            if p == plu:
                barcode = code
                break

        # codigo is the barcode or just the PLU number (no "PLU-" prefix)
        codigo = barcode if barcode else str(plu)
        
        if codigo in existing:
            continue

        cur.execute(INSERT_SQL, (
            codigo, plu, nombre, precio
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Productos insertados: {inserted}")

if __name__ == "__main__":
    main()
