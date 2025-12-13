#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de alertas de créditos pendientes
Inserta créditos de prueba con diferentes estados:
1. Crédito VENCIDO (fecha pasada)
2. Crédito por vencer en 30 minutos
3. Crédito normal (vence en varios días)
"""

import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

print("=" * 70)
print("INSERTAR CRÉDITOS DE PRUEBA PARA ALERTAS")
print("=" * 70)

# Obtener fecha de hoy y ayer
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
fecha_manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# Hora actual
hora_actual = datetime.now().strftime("%H:%M")
hora_pasada = (datetime.now() - timedelta(hours=1)).strftime("%H:%M")  # Hace 1 hora
hora_proxima = (datetime.now() + timedelta(minutes=30)).strftime("%H:%M")  # En 30 minutos
hora_lejana = (datetime.now() + timedelta(hours=3)).strftime("%H:%M")  # En 3 horas

print(f"\nFecha hoy: {fecha_hoy}")
print(f"Fecha ayer: {fecha_ayer}")
print(f"Hora actual: {hora_actual}")
print(f"Hora pasada: {hora_pasada}")
print(f"Hora próxima (30 min): {hora_proxima}")

# Limpiar alertas previas de prueba
cursor.execute("DELETE FROM creditos_pendientes WHERE cliente LIKE 'PRUEBA_%'")
conn.commit()
print("\n✓ Limpias alertas de prueba anteriores")

# 1. CRÉDITO VENCIDO (ayer a las 15:00) - Debe mostrar alerta de VENCIDO
print("\n1️⃣  CRÉDITO VENCIDO (hace 1 día)")
cursor.execute('''
    INSERT INTO creditos_pendientes 
    (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, pagado, alerta_mostrada, venta_id)
    VALUES (?, ?, ?, ?, ?, 0, 0, NULL)
''', ('PRUEBA_VENCIDO_AYER', 500.00, fecha_ayer, fecha_ayer, '15:00'))
conn.commit()
print(f"   ✓ Cliente: PRUEBA_VENCIDO_AYER")
print(f"   ✓ Monto: 500.00")
print(f"   ✓ Vencimiento: {fecha_ayer} a las 15:00")
print(f"   ✓ Estado: VENCIDO (debe mostrar 🔴 ERROR)")

# 2. CRÉDITO VENCIDO HOY (con hora pasada) - Debe mostrar alerta de VENCIDO
print("\n2️⃣  CRÉDITO VENCIDO HOY (hace 1 hora)")
cursor.execute('''
    INSERT INTO creditos_pendientes 
    (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, pagado, alerta_mostrada, venta_id)
    VALUES (?, ?, ?, ?, ?, 0, 0, NULL)
''', ('PRUEBA_VENCIDO_HOY', 750.50, fecha_hoy, fecha_hoy, hora_pasada))
conn.commit()
print(f"   ✓ Cliente: PRUEBA_VENCIDO_HOY")
print(f"   ✓ Monto: 750.50")
print(f"   ✓ Vencimiento: {fecha_hoy} a las {hora_pasada}")
print(f"   ✓ Estado: VENCIDO (debe mostrar 🔴 ERROR)")

# 3. CRÉDITO POR VENCER EN 30 MINUTOS - Debe mostrar alerta de PRECAUCIÓN
print("\n3️⃣  CRÉDITO POR VENCER EN 30 MINUTOS")
cursor.execute('''
    INSERT INTO creditos_pendientes 
    (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, pagado, alerta_mostrada, venta_id)
    VALUES (?, ?, ?, ?, ?, 0, 0, NULL)
''', ('PRUEBA_POR_VENCER', 1200.00, fecha_hoy, fecha_hoy, hora_proxima))
conn.commit()
print(f"   ✓ Cliente: PRUEBA_POR_VENCER")
print(f"   ✓ Monto: 1200.00")
print(f"   ✓ Vencimiento: {fecha_hoy} a las {hora_proxima}")
print(f"   ✓ Estado: POR VENCER EN 30 MIN (debe mostrar 🟡 WARNING)")

# 4. CRÉDITO NORMAL (en 3 horas) - NO debe mostrar alerta
print("\n4️⃣  CRÉDITO NORMAL (en 3 horas)")
cursor.execute('''
    INSERT INTO creditos_pendientes 
    (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, pagado, alerta_mostrada, venta_id)
    VALUES (?, ?, ?, ?, ?, 0, 0, NULL)
''', ('PRUEBA_NORMAL', 300.00, fecha_hoy, fecha_hoy, hora_lejana))
conn.commit()
print(f"   ✓ Cliente: PRUEBA_NORMAL")
print(f"   ✓ Monto: 300.00")
print(f"   ✓ Vencimiento: {fecha_hoy} a las {hora_lejana}")
print(f"   ✓ Estado: NORMAL (no debe mostrar alerta)")

# 5. CRÉDITO FUTURO - NO debe mostrar alerta
print("\n5️⃣  CRÉDITO FUTURO (mañana)")
cursor.execute('''
    INSERT INTO creditos_pendientes 
    (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, pagado, alerta_mostrada, venta_id)
    VALUES (?, ?, ?, ?, ?, 0, 0, NULL)
''', ('PRUEBA_FUTURO', 450.00, fecha_hoy, fecha_manana, '15:00'))
conn.commit()
print(f"   ✓ Cliente: PRUEBA_FUTURO")
print(f"   ✓ Monto: 450.00")
print(f"   ✓ Vencimiento: {fecha_manana} a las 15:00")
print(f"   ✓ Estado: FUTURO (no debe mostrar alerta)")

# 6. CRÉDITO PAGADO - NO debe mostrar alerta
print("\n6️⃣  CRÉDITO VENCIDO PERO PAGADO (no debe alertar)")
cursor.execute('''
    INSERT INTO creditos_pendientes 
    (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, pagado, alerta_mostrada, venta_id)
    VALUES (?, ?, ?, ?, ?, 1, 0, NULL)
''', ('PRUEBA_PAGADO', 600.00, fecha_ayer, fecha_ayer, '15:00'))
conn.commit()
print(f"   ✓ Cliente: PRUEBA_PAGADO")
print(f"   ✓ Monto: 600.00")
print(f"   ✓ Vencimiento: {fecha_ayer} a las 15:00")
print(f"   ✓ Estado: PAGADO (no debe mostrar alerta)")

print("\n" + "=" * 70)
print("✓ DATOS DE PRUEBA INSERTADOS EXITOSAMENTE")
print("=" * 70)

# Mostrar resumen
print("\n📊 RESUMEN DE CRÉDITOS DE PRUEBA:")
cursor.execute("SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, pagado FROM creditos_pendientes WHERE cliente LIKE 'PRUEBA_%' ORDER BY fecha_vencimiento, hora_vencimiento")
resultados = cursor.fetchall()

for i, (cliente, monto, fecha_venc, hora_venc, pagado) in enumerate(resultados, 1):
    estado = "✅ PAGADO" if pagado else "⏳ PENDIENTE"
    print(f"{i}. {cliente}: ${monto:.2f} - {fecha_venc} {hora_venc} [{estado}]")

print("\n💡 Próximo paso:")
print("   1. Ejecuta: streamlit run main.py")
print("   2. Inicia sesión con admin/Creme$123")
print("   3. Abre 'Punto de Venta'")
print("   4. Deberías ver:")
print("      🔴 2 alertas de CRÉDITOS VENCIDOS (PRUEBA_VENCIDO_*)")
print("      🟡 1 alerta de CRÉDITO POR VENCER (PRUEBA_POR_VENCER)")
print("      ✓ 3 créditos sin alerta (PRUEBA_NORMAL, PRUEBA_FUTURO, PRUEBA_PAGADO)")

conn.close()
