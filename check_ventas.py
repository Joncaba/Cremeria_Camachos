import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

# Ver últimas ventas del producto 11111
print("=== ÚLTIMAS VENTAS DEL YOGURT 11111 ===\n")
cursor.execute("""
    SELECT fecha, cantidad, precio_unitario, total, tipo_venta, peso_vendido
    FROM ventas 
    WHERE codigo = '11111' 
    ORDER BY fecha DESC 
    LIMIT 5
""")

ventas = cursor.fetchall()
if ventas:
    for v in ventas:
        print(f"Fecha: {v[0]}")
        print(f"  Cantidad: {v[1]}")
        print(f"  Precio unitario: ${v[2]:.2f}")
        print(f"  Total: ${v[3]:.2f}")
        print(f"  Tipo venta: {v[4]}")
        print(f"  Peso vendido: {v[5]}")
        print()
else:
    print("No hay ventas registradas")

# Ver stock actual
cursor.execute("SELECT stock, stock_kg FROM productos WHERE codigo = '11111'")
stock = cursor.fetchone()
print(f"\n=== STOCK ACTUAL ===")
print(f"Stock unidades: {stock[0]}")
print(f"Stock kg: {stock[1]}")

conn.close()
