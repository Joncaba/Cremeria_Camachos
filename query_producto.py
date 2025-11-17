import sqlite3
db = 'pos_cremeria.db'
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute(\"SELECT codigo, stock, stock_maximo, ROUND(CASE WHEN tipo_venta='granel' THEN stock_kg*100.0/stock_maximo_kg ELSE stock*100.0/stock_maximo END,1) as porcentaje_stock FROM productos WHERE codigo=?\", ('20004010',))
row = cur.fetchone()
print(row)
conn.close()
