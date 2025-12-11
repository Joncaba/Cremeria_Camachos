import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

# Obtener stock actual
cursor.execute("SELECT stock FROM productos WHERE codigo = '11111'")
stock_actual = cursor.fetchone()[0]

print(f"Stock actual: {stock_actual} unidades")
print(f"\nSe vendieron 20 unidades que no se restaron del stock")
print(f"Stock correcto debería ser: {stock_actual - 20} unidades")

respuesta = input("\n¿Deseas corregir el stock? (si/no): ")

if respuesta.lower() == 'si':
    nuevo_stock = stock_actual - 20
    cursor.execute("UPDATE productos SET stock = ? WHERE codigo = '11111'", (nuevo_stock,))
    conn.commit()
    print(f"\n✅ Stock actualizado a {nuevo_stock} unidades")
else:
    print("\nOperación cancelada")

conn.close()
