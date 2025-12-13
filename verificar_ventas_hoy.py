#!/usr/bin/env python3
import sqlite3
from datetime import datetime

conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

print("=" * 80)
print("TODAS LAS VENTAS - ÚLTIMAS 20")
print("=" * 80)

cursor.execute("SELECT id, fecha, total, tipo_pago FROM ventas ORDER BY id DESC LIMIT 20")
ventas = cursor.fetchall()

for venta in ventas:
    venta_id, fecha, total, tipo_pago = venta
    print(f"ID: {venta_id:4} | Fecha: {fecha:25} | Total: ${total:8.2f} | Pago: {tipo_pago}")

print("\n" + "=" * 80)
print("BÚSQUEDA POR HOY (2025-12-12)")
print("=" * 80)

cursor.execute("SELECT COUNT(*) FROM ventas WHERE fecha LIKE '2025-12-12%'")
resultado = cursor.fetchone()[0]
print(f"Ventas de hoy (LIKE '2025-12-12%'): {resultado}")

if resultado > 0:
    print("\nDetalle:")
    cursor.execute("SELECT id, fecha, total, tipo_pago FROM ventas WHERE fecha LIKE '2025-12-12%' ORDER BY id DESC")
    for venta in cursor.fetchall():
        venta_id, fecha, total, tipo_pago = venta
        print(f"  ID: {venta_id} | Fecha: {fecha} | Total: ${total:.2f} | Pago: {tipo_pago}")

conn.close()
