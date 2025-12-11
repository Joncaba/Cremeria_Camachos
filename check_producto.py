import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

# Buscar producto 11111
cursor.execute("SELECT codigo, nombre, tipo_venta, stock, stock_kg FROM productos WHERE codigo = '11111'")
result = cursor.fetchone()

if result:
    print(f"Código: {result[0]}")
    print(f"Nombre: {result[1]}")
    print(f"Tipo venta: {result[2]}")
    print(f"Stock (unidades): {result[3]}")
    print(f"Stock (kg): {result[4]}")
else:
    print("Producto no encontrado")
    # Buscar con LIKE
    cursor.execute("SELECT codigo, nombre, tipo_venta, stock, stock_kg FROM productos WHERE codigo LIKE '%1111%'")
    resultados = cursor.fetchall()
    if resultados:
        print("\nProductos encontrados con código similar:")
        for r in resultados:
            print(f"  {r[0]} - {r[1]} - Tipo: {r[2]} - Stock: {r[3]} unid, {r[4]} kg")

conn.close()
