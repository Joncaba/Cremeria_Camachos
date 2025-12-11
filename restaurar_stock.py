import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

# Restaurar a 0
cursor.execute('UPDATE productos SET stock = 0 WHERE codigo = "11111"')
conn.commit()

print('✅ Stock restaurado a 0 unidades (refleja las 3 ventas de 20 unidades ya registradas)')

# Verificar
cursor.execute('SELECT stock FROM productos WHERE codigo = "11111"')
stock = cursor.fetchone()[0]
print(f'Stock actual: {stock} unidades')

conn.close()
