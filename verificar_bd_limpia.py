#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM creditos_pendientes WHERE cliente LIKE 'PRUEBA_%'")
prueba_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM creditos_pendientes")
total_count = cursor.fetchone()[0]

print(f"✅ Créditos PRUEBA_ restantes: {prueba_count}")
print(f"📊 Total de créditos en BD: {total_count}")

if prueba_count == 0:
    print("\n✓ BD limpia - Lista para usar")
else:
    print(f"\n⚠️  Aún hay {prueba_count} créditos de prueba")

conn.close()
