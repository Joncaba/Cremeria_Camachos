import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

print("="*60)
print("TRIGGERS EN LA BASE DE DATOS:")
print("="*60)

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger'")
triggers = cursor.fetchall()

if triggers:
    for trigger in triggers:
        print(f"\n📌 Trigger: {trigger[0]}")
        print(f"SQL:\n{trigger[1]}\n")
else:
    print("\n✅ No hay triggers definidos")

print("\n" + "="*60)
print("HISTORIAL DE CAMBIOS EN YOGURT 11111:")
print("="*60)

# Ver últimas ventas
cursor.execute("""
    SELECT id, fecha, cantidad, total, tipo_venta 
    FROM ventas 
    WHERE codigo = '11111' 
    ORDER BY fecha DESC 
    LIMIT 5
""")

ventas = cursor.fetchall()
if ventas:
    print("\n📋 Últimas 5 ventas:")
    for v in ventas:
        print(f"  ID: {v[0]} | Fecha: {v[1]} | Cantidad: {v[2]} | Total: ${v[3]:.2f} | Tipo: {v[4]}")
else:
    print("\n❌ No hay ventas registradas")

# Stock actual
cursor.execute("SELECT stock, stock_kg, tipo_venta FROM productos WHERE codigo = '11111'")
prod = cursor.fetchone()
if prod:
    print(f"\n📦 Stock actual:")
    print(f"  Stock (unidades): {prod[0]}")
    print(f"  Stock (kg): {prod[1]}")
    print(f"  Tipo venta: {prod[2]}")

conn.close()
