import sqlite3

# Simular una venta para ver si se actualiza el stock
conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

print("="*60)
print("TEST: Actualización manual de stock")
print("="*60)

# Ver stock actual
cursor.execute("SELECT stock FROM productos WHERE codigo = '11111'")
stock_antes = cursor.fetchone()[0]
print(f"\n1. Stock ANTES de la actualización: {stock_antes} unidades")

# Actualizar stock manualmente (restar 20)
nuevo_stock = stock_antes - 20
cursor.execute("UPDATE productos SET stock = ? WHERE codigo = '11111'", (nuevo_stock,))
conn.commit()

# Verificar cambio
cursor.execute("SELECT stock FROM productos WHERE codigo = '11111'")
stock_despues = cursor.fetchone()[0]
print(f"2. Stock DESPUÉS de la actualización: {stock_despues} unidades")
print(f"3. Cambio aplicado: {stock_despues - stock_antes} unidades")

# Esperar y verificar de nuevo
import time
print("\n⏳ Esperando 3 segundos...")
time.sleep(3)

cursor.execute("SELECT stock FROM productos WHERE codigo = '11111'")
stock_final = cursor.fetchone()[0]
print(f"4. Stock después de esperar: {stock_final} unidades")

if stock_final != stock_despues:
    print(f"\n⚠️ ¡ALERTA! El stock cambió de {stock_despues} a {stock_final}")
    print("Algo está restaurando el stock automáticamente")
else:
    print(f"\n✅ El stock se mantiene en {stock_final} unidades")

conn.close()
