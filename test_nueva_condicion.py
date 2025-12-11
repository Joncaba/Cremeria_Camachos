import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

print("="*60)
print("PRODUCTOS CON STOCK <= MÍNIMO (NUEVA CONDICIÓN):")
print("="*60)

cursor.execute("""
    SELECT codigo, nombre, stock, stock_minimo, stock_kg, stock_minimo_kg, tipo_venta
    FROM productos 
    WHERE (
        (tipo_venta = 'unidad' AND stock <= stock_minimo AND stock_minimo > 0) OR
        (tipo_venta = 'granel' AND stock_kg <= stock_minimo_kg AND stock_minimo_kg > 0)
    )
    ORDER BY nombre
""")

productos = cursor.fetchall()

if productos:
    print(f"\n✅ Se encontraron {len(productos)} productos:\n")
    for p in productos:
        if p[6] == 'granel':
            print(f"🥛 GRANEL: {p[1]} ({p[0]})")
            print(f"   Stock: {p[4]} kg / Mínimo: {p[5]} kg")
        else:
            print(f"📦 UNIDAD: {p[1]} ({p[0]})")
            print(f"   Stock: {p[2]} unid / Mínimo: {p[3]} unid")
        print()
else:
    print("\n❌ No hay productos con stock bajo")

conn.close()
