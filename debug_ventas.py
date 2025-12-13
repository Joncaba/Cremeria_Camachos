#!/usr/bin/env python3
import sqlite3
from datetime import datetime

conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

# Ver estructura de tabla ventas
print("=" * 80)
print("ESTRUCTURA DE TABLA VENTAS")
print("=" * 80)
cursor.execute("PRAGMA table_info(ventas)")
columnas = cursor.fetchall()
for col in columnas:
    print(f"  {col[1]:20} {col[2]:15}")

# Ver fechas únicas en ventas (últimas 10)
print("\n" + "=" * 80)
print("ÚLTIMAS 10 VENTAS - FECHAS REGISTRADAS")
print("=" * 80)

# Intentar diferentes nombres de columna de fecha
for col_name in ['fecha', 'fecha_venta', 'fecha_local', 'created_at', 'fecha_creacion']:
    try:
        cursor.execute(f"SELECT {col_name} FROM ventas LIMIT 5")
        fechas = cursor.fetchall()
        if fechas:
            print(f"\n✅ Columna: {col_name}")
            for f in fechas:
                print(f"   {f[0]}")
            break
    except:
        continue

# Ver hoy en formato actual
print("\n" + "=" * 80)
print("HOY (según sistema)")
print("=" * 80)
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
print(f"Buscando ventas con fecha = '{fecha_hoy}'")

# Intentar consulta
cursor.execute("SELECT COUNT(*) FROM ventas WHERE fecha = ? OR fecha_local LIKE ?", (fecha_hoy, f"{fecha_hoy}%"))
resultado = cursor.fetchone()
print(f"Ventas encontradas: {resultado[0]}")

# Ver todas las ventas
print("\n" + "=" * 80)
print("TODAS LAS VENTAS EN BD")
print("=" * 80)
cursor.execute("SELECT COUNT(*) FROM ventas")
total = cursor.fetchone()[0]
print(f"Total de ventas: {total}")

if total > 0:
    cursor.execute("SELECT id, fecha FROM ventas ORDER BY id DESC LIMIT 10")
    for row in cursor.fetchall():
        print(f"  ID: {row[0]}, Fecha: {row[1]}")

conn.close()
