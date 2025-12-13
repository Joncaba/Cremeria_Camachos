import sqlite3

DB_PATH = "pos_cremeria.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Delete products with PLU- prefix
cur.execute("DELETE FROM productos WHERE codigo LIKE 'PLU-%'")
affected = cur.rowcount

conn.commit()
conn.close()

print(f"Productos con prefijo PLU- eliminados: {affected}")
