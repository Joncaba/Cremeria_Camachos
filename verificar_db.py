import sqlite3
import pandas as pd

conn = sqlite3.connect("pos_cremeria.db")
df = pd.read_sql_query("SELECT codigo, nombre, tipo_venta, stock, stock_kg, precio_normal, precio_por_kg, precio_compra FROM productos WHERE codigo='200000300'", conn)
conn.close()

print("\n=== DATOS EN LA BASE DE DATOS ===")
print(df.to_string())
print("\n")
