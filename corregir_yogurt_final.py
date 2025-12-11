import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

# Ver stock actual
cursor.execute('SELECT stock FROM productos WHERE codigo = "11111"')
stock_actual = cursor.fetchone()[0]
print(f'Stock actual: {stock_actual} unidades')

# Calcular stock correcto
ventas_sin_reflejar = 3 * 20  # 3 ventas de 20 unidades cada una
stock_correcto = stock_actual - ventas_sin_reflejar

print(f'3 ventas de 20 unidades cada una = {ventas_sin_reflejar} unidades')
print(f'Stock correcto debería ser: {stock_correcto} unidades')

# Actualizar
cursor.execute('UPDATE productos SET stock = ? WHERE codigo = "11111"', (stock_correcto,))
conn.commit()

print(f'\n✅ Stock actualizado a {stock_correcto} unidades')

# Verificar
cursor.execute('SELECT stock FROM productos WHERE codigo = "11111"')
stock_verificado = cursor.fetchone()[0]
print(f'✅ Stock verificado: {stock_verificado} unidades')

conn.close()
