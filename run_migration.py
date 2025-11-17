import sqlite3

def migrar_base_datos_completa():
    """Migración completa para productos con peso unitario y a granel"""
    conn = sqlite3.connect("pos_cremeria.db")
    cursor = conn.cursor()
    
    # Agregar todas las columnas necesarias
    cursor.execute("PRAGMA table_info(productos)")
    columns = [column[1] for column in cursor.fetchall()]
    
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
    
    # Actualizar ventas para peso
    cursor.execute("PRAGMA table_info(ventas)")
    ventas_columns = [column[1] for column in cursor.fetchall()]
    
    if 'peso_vendido' not in ventas_columns:
        cursor.execute("ALTER TABLE ventas ADD COLUMN peso_vendido REAL DEFAULT 0")
    if 'tipo_venta' not in ventas_columns:
        cursor.execute("ALTER TABLE ventas ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")
    
    conn.commit()
    conn.close()
    print("✅ Migración completada exitosamente")

if __name__ == "__main__":
    migrar_base_datos_completa()