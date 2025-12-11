import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

print("="*60)
print("TODOS LOS PRODUCTOS DE UNIDAD:")
print("="*60)

cursor.execute("""
    SELECT codigo, nombre, stock, stock_minimo, tipo_venta
    FROM productos 
    WHERE tipo_venta = 'unidad' AND stock_minimo > 0
    ORDER BY nombre
""")

productos_unidad = cursor.fetchall()

for p in productos_unidad:
    cumple_bajo = p[2] <= (p[3] * 0.5)
    indicador = "⚠️ BAJO" if cumple_bajo else "✅ OK"
    print(f"\n{indicador} {p[1]} ({p[0]})")
    print(f"   Stock: {p[2]} unidades")
    print(f"   Mínimo: {p[3]} unidades")
    print(f"   50% del mínimo: {p[3] * 0.5} unidades")
    print(f"   ¿Stock <= 50% mínimo? {cumple_bajo}")

print("\n\n" + "="*60)
print("QUERY DE BAJO STOCK - SOLO UNIDADES:")
print("="*60)

cursor.execute("""
    SELECT codigo, nombre, stock, stock_minimo, tipo_venta
    FROM productos 
    WHERE tipo_venta = 'unidad' AND stock <= (stock_minimo * 0.5) AND stock_minimo > 0
    ORDER BY nombre
""")

bajo_unidad = cursor.fetchall()

if bajo_unidad:
    for p in bajo_unidad:
        print(f"\n- {p[1]} ({p[0]}): {p[2]} unid / Min: {p[3]} unid")
else:
    print("\n¡No hay productos de unidad con stock bajo!")

print("\n\n" + "="*60)
print("QUERY COMPLETA DE BAJO STOCK (GRANEL + UNIDAD):")
print("="*60)

cursor.execute("""
    SELECT codigo, nombre, stock, stock_minimo, stock_kg, stock_minimo_kg, tipo_venta
    FROM productos 
    WHERE (
        (tipo_venta = 'unidad' AND stock <= (stock_minimo * 0.5) AND stock_minimo > 0) OR
        (tipo_venta = 'granel' AND stock_kg <= (stock_minimo_kg * 0.5) AND stock_minimo_kg > 0)
    )
    ORDER BY nombre
""")

todos_bajo = cursor.fetchall()

if todos_bajo:
    for p in todos_bajo:
        if p[6] == 'granel':
            print(f"\n🥛 GRANEL: {p[1]} ({p[0]}): {p[4]} kg / Min: {p[5]} kg")
        else:
            print(f"\n📦 UNIDAD: {p[1]} ({p[0]}): {p[2]} unid / Min: {p[3]} unid")
else:
    print("\n¡No hay productos con stock bajo!")

conn.close()
