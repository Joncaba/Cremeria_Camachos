import sqlite3

def fix_productos_module():
    """Arreglar módulo de productos con código completo"""
    
    # Crear conexión
    conn = sqlite3.connect("pos_cremeria.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Ejecutar migración
    cursor.execute("PRAGMA table_info(productos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Agregar campos faltantes
    if 'tipo_venta' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")
    if 'precio_por_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN precio_por_kg REAL DEFAULT 0")
    if 'peso_unitario' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN peso_unitario REAL DEFAULT 0")
    if 'stock_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN stock_kg REAL DEFAULT 0")
    if 'stock_minimo' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN stock_minimo INTEGER DEFAULT 10")
    if 'stock_minimo_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN stock_minimo_kg REAL DEFAULT 0")
    
    conn.commit()
    conn.close()
    print("✅ Base de datos actualizada")

if __name__ == "__main__":
    fix_productos_module()