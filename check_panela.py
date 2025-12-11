import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

# Buscar Queso Panela
cursor.execute("""
    SELECT codigo, nombre, stock, stock_minimo, stock_kg, stock_minimo_kg, 
           stock_maximo, stock_maximo_kg, tipo_venta
    FROM productos 
    WHERE codigo LIKE '%Panela%' OR nombre LIKE '%Panela%'
""")

productos = cursor.fetchall()

if productos:
    for p in productos:
        print(f"\n{'='*60}")
        print(f"Código: {p[0]}")
        print(f"Nombre: {p[1]}")
        print(f"Stock (unidades): {p[2]}")
        print(f"Stock mínimo (unidades): {p[3]}")
        print(f"Stock (kg): {p[4]}")
        print(f"Stock mínimo (kg): {p[5]}")
        print(f"Stock máximo (unidades): {p[6]}")
        print(f"Stock máximo (kg): {p[7]}")
        print(f"Tipo venta: {p[8]}")
        
        # Verificar condición de stock bajo
        if p[8] == 'granel':
            porcentaje = (p[4] * 100.0 / p[5]) if p[5] > 0 else 100
            cumple_condicion = p[4] <= (p[5] * 0.5) and p[5] > 0
            print(f"\n📊 GRANEL:")
            print(f"   Porcentaje stock: {porcentaje:.1f}%")
            print(f"   Stock actual ({p[4]} kg) <= Mínimo*0.5 ({p[5]*0.5} kg): {cumple_condicion}")
        else:
            porcentaje = (p[2] * 100.0 / p[3]) if p[3] > 0 else 100
            cumple_condicion = p[2] <= (p[3] * 0.5) and p[3] > 0
            print(f"\n📊 UNIDAD:")
            print(f"   Porcentaje stock: {porcentaje:.1f}%")
            print(f"   Stock actual ({p[2]} unid) <= Mínimo*0.5 ({p[3]*0.5} unid): {cumple_condicion}")
        
        print(f"\n✅ ¿Aparece en lista de bajo stock? {cumple_condicion}")
else:
    print("No se encontró Queso Panela")

# Ahora ejecutar la query completa de bajo stock
print("\n\n" + "="*60)
print("PRODUCTOS EN LISTA DE BAJO STOCK:")
print("="*60)

cursor.execute("""
    SELECT codigo, nombre, stock, stock_minimo, stock_kg, stock_minimo_kg, tipo_venta,
           CASE 
               WHEN tipo_venta = 'granel' THEN 
                   CASE WHEN stock_minimo_kg > 0 THEN CAST((stock_kg * 100.0 / stock_minimo_kg) AS INTEGER) ELSE 100 END
               ELSE 
                   CASE WHEN stock_minimo > 0 THEN CAST((stock * 100.0 / stock_minimo) AS INTEGER) ELSE 100 END
           END as porcentaje_stock
    FROM productos 
    WHERE (
        (tipo_venta = 'unidad' AND stock <= (stock_minimo * 0.5) AND stock_minimo > 0) OR
        (tipo_venta = 'granel' AND stock_kg <= (stock_minimo_kg * 0.5) AND stock_minimo_kg > 0)
    )
    ORDER BY porcentaje_stock ASC
""")

bajo_stock = cursor.fetchall()

if bajo_stock:
    for p in bajo_stock:
        tipo = "kg" if p[6] == 'granel' else "unid"
        stock_actual = p[4] if p[6] == 'granel' else p[2]
        stock_min = p[5] if p[6] == 'granel' else p[3]
        print(f"\n- {p[1]} ({p[0]}): {stock_actual} {tipo} / Min: {stock_min} {tipo} | {p[7]}%")
else:
    print("\n¡No hay productos con stock bajo!")

conn.close()
