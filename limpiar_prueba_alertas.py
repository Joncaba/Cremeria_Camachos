#!/usr/bin/env python3
"""
Script para limpiar datos de prueba de créditos
Permite eliminar los créditos de prueba cuando no se necesiten más
"""

import sqlite3
import sys

conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

print("=" * 70)
print("LIMPIAR DATOS DE PRUEBA DE ALERTAS DE CRÉDITOS")
print("=" * 70)

# Contar créditos de prueba
cursor.execute("SELECT COUNT(*) FROM creditos_pendientes WHERE cliente LIKE 'PRUEBA_%'")
count = cursor.fetchone()[0]

print(f"\nEncontrados {count} créditos de prueba (PRUEBA_*)")

if count == 0:
    print("✓ No hay créditos de prueba para limpiar")
    sys.exit(0)

# Mostrar detalles
print("\nCréditos a eliminar:")
cursor.execute("SELECT id, cliente, monto, fecha_vencimiento, pagado FROM creditos_pendientes WHERE cliente LIKE 'PRUEBA_%' ORDER BY id")
for cred_id, cliente, monto, fecha, pagado in cursor.fetchall():
    estado = "✅ PAGADO" if pagado else "⏳ PENDIENTE"
    print(f"  #{cred_id}. {cliente}: ${monto:.2f} - {fecha} [{estado}]")

# Confirmar eliminación
print("\n⚠️  ¿Deseas eliminar estos créditos de prueba?")
respuesta = input("Escribe 'si' para confirmar: ").strip().lower()

if respuesta != 'si':
    print("✓ Operación cancelada")
    sys.exit(0)

# Eliminar
cursor.execute("DELETE FROM creditos_pendientes WHERE cliente LIKE 'PRUEBA_%'")
conn.commit()

print(f"\n✅ {count} créditos de prueba eliminados exitosamente")
print("✓ La BD está lista para datos reales")

conn.close()
