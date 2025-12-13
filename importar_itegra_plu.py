import sqlite3
import sys
from pathlib import Path

DB_PATH = "pos_cremeria.db"

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS codigos_barras (
    codigo TEXT PRIMARY KEY,         -- Código de barras escaneable
    plu INTEGER,                     -- Número PLU del producto
    nombre TEXT NOT NULL,            -- Nombre del producto
    precio REAL NOT NULL             -- Precio base del iTegra
);

CREATE TABLE IF NOT EXISTS plu_catalogo (
    plu INTEGER PRIMARY KEY,         -- Número PLU
    nombre TEXT NOT NULL,            -- Nombre del producto
    precio REAL NOT NULL             -- Precio base
);
"""

def ensure_table(conn: sqlite3.Connection):
    # Execute multiple statements safely
    for stmt in TABLE_SQL.strip().split(";"):
        s = stmt.strip()
        if not s:
            continue
        conn.execute(s + ";")
    conn.commit()

def parse_itegra_line(line: str):
    """Parse a single iTegra PLUs line.

    iTegra format example (fields separated by |):
    "PLUs"1|1|0|JAM COR PIERNA||1|P|0|209.00|...
    
    Structure:
    [0] "PLUs"<id>
    [1] Section ID
    [2] Unknown
    [3] Product Name
    [4] Barcode (often empty)
    [5] PLU number (the actual product PLU)
    [6] Type (P/N)
    [7] Unknown
    [8] Price (regular sale price)

    Returns: (plu:int, codigo_barra:str|None, nombre:str, precio:float)
    """
    parts = line.strip().split("|")
    if not parts or not parts[0].startswith('"PLUs"'):
        return None

    try:
        # PLU is at position [5] - this is the actual product PLU number
        plu = int(parts[5]) if len(parts) > 5 and parts[5].strip() else None
    except Exception:
        plu = None

    nombre = parts[3].strip() if len(parts) > 3 else ""

    # Barcode field at position [4] (usually empty in this dataset)
    codigo_barra = parts[4].strip() if len(parts) > 4 and parts[4].strip() != "" else None

    # Price: regular price at position [8]
    try:
        precio = float(parts[8]) if len(parts) > 8 and parts[8] != "" else 0.0
    except Exception:
        precio = 0.0

    if not nombre or plu is None:
        return None

    return plu, codigo_barra, nombre, precio

def import_itegra(file_path: Path):
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_table(conn)

        inserted = 0
        updated = 0
        plu_ins = 0
        plu_upd = 0
        with file_path.open("r", encoding="latin-1", errors="ignore") as f:
            for line in f:
                if '"PLUs"' not in line:
                    continue

                parsed = parse_itegra_line(line)
                if not parsed:
                    continue

                plu, codigo_barra, nombre, precio = parsed

                # Always upsert PLU catalog (nombre, precio)
                cur = conn.cursor()
                if plu is not None:
                    cur.execute("SELECT plu FROM plu_catalogo WHERE plu = ?", (plu,))
                    if cur.fetchone() is not None:
                        cur.execute(
                            "UPDATE plu_catalogo SET nombre = ?, precio = ? WHERE plu = ?",
                            (nombre, precio, plu)
                        )
                        plu_upd += 1
                    else:
                        cur.execute(
                            "INSERT INTO plu_catalogo (plu, nombre, precio) VALUES (?, ?, ?)",
                            (plu, nombre, precio)
                        )
                        plu_ins += 1

                # Upsert barcode mapping only if we have a barcode
                if codigo_barra:
                    cur.execute(
                        "SELECT codigo FROM codigos_barras WHERE codigo = ?",
                        (codigo_barra,)
                    )
                    exists = cur.fetchone() is not None

                    if exists:
                        cur.execute(
                            "UPDATE codigos_barras SET plu = ?, nombre = ?, precio = ? WHERE codigo = ?",
                            (plu, nombre, precio, codigo_barra)
                        )
                        updated += 1
                    else:
                        cur.execute(
                            "INSERT INTO codigos_barras (codigo, plu, nombre, precio) VALUES (?, ?, ?, ?)",
                            (codigo_barra, plu, nombre, precio)
                        )
                        inserted += 1

        conn.commit()
        return inserted, updated, plu_ins, plu_upd
    finally:
        conn.close()

def main():
    if len(sys.argv) < 2:
        print("Uso: python importar_itegra_plu.py <ruta_archivo.iTegra>")
        sys.exit(1)
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Archivo no encontrado: {file_path}")
        sys.exit(1)
    ins, upd, plu_ins, plu_upd = import_itegra(file_path)
    print(f"Importación completada: codigos {ins} nuevos, {upd} actualizados | PLUs {plu_ins} nuevos, {plu_upd} actualizados")

if __name__ == "__main__":
    main()
