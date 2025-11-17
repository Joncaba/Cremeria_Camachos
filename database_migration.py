import sqlite3

def actualizar_base_datos_granel():
    """Migración para agregar soporte de productos a granel"""
    conn = sqlite3.connect("pos_cremeria.db")
    cursor = conn.cursor()
    
    # Agregar nuevas columnas para productos a granel
    cursor.execute("PRAGMA table_info(productos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'tipo_venta' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")  # 'unidad' o 'granel'
    
    if 'precio_por_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN precio_por_kg REAL DEFAULT 0")
    
    if 'peso_unitario' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN peso_unitario REAL DEFAULT 0")  # peso promedio por unidad
    
    if 'stock_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN stock_kg REAL DEFAULT 0")  # stock en kg para productos a granel
    
    # Actualizar tabla de ventas para manejar peso
    cursor.execute("PRAGMA table_info(ventas)")
    ventas_columns = [column[1] for column in cursor.fetchall()]
    
    if 'peso_vendido' not in ventas_columns:
        cursor.execute("ALTER TABLE ventas ADD COLUMN peso_vendido REAL DEFAULT 0")
    
    if 'tipo_venta' not in ventas_columns:
        cursor.execute("ALTER TABLE ventas ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")
    
    conn.commit()
    conn.close()

# Ejecutar la migración
if __name__ == "__main__":
    actualizar_base_datos_granel()
    print("Base de datos actualizada para soportar productos a granel")