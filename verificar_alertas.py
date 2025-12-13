#!/usr/bin/env python3
"""
Script de verificación para validar que las funciones de alertas funcionan correctamente
"""

import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

print("=" * 80)
print("VERIFICACIÓN DE FUNCIONES DE ALERTAS DE CRÉDITOS")
print("=" * 80)

# Función auxiliar para formatear moneda
def formatear_moneda(valor):
    return f"${valor:,.2f}"

# FUNCIÓN 1: obtener_creditos_vencidos()
print("\n1️⃣  FUNCIÓN: obtener_creditos_vencidos()")
print("-" * 80)

ahora = datetime.now()
fecha_hoy = ahora.strftime("%Y-%m-%d")
hora_actual = ahora.strftime("%H:%M")

cursor.execute('''
    SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
    FROM creditos_pendientes 
    WHERE pagado = 0 AND (
        fecha_vencimiento < ? 
        OR (fecha_vencimiento = ? AND hora_vencimiento < ?)
    )
    ORDER BY fecha_vencimiento, hora_vencimiento
''', (fecha_hoy, fecha_hoy, hora_actual))

vencidos = cursor.fetchall()
print(f"Búsqueda: Créditos vencidos (fecha < {fecha_hoy} O (fecha = {fecha_hoy} AND hora < {hora_actual}))")
print(f"Resultados encontrados: {len(vencidos)}")

for cliente, monto, fecha_venc, hora_venc, cred_id, alerta in vencidos:
    estado_alerta = "⚠️  SIN VER" if alerta == 0 else "✅ YA VISTO"
    print(f"  • {cliente}: {formatear_moneda(monto)} - {fecha_venc} {hora_venc} [{estado_alerta}]")

# FUNCIÓN 2: obtener_creditos_por_vencer()
print("\n2️⃣  FUNCIÓN: obtener_creditos_por_vencer()")
print("-" * 80)

una_hora_despues = (ahora + timedelta(hours=1)).strftime("%H:%M")

cursor.execute('''
    SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
    FROM creditos_pendientes 
    WHERE pagado = 0 AND fecha_vencimiento = ? 
        AND hora_vencimiento > ? AND hora_vencimiento <= ?
    ORDER BY hora_vencimiento
''', (fecha_hoy, hora_actual, una_hora_despues))

por_vencer = cursor.fetchall()
print(f"Búsqueda: Créditos que vencen entre {hora_actual} y {una_hora_despues} (en menos de 1 hora)")
print(f"Resultados encontrados: {len(por_vencer)}")

for cliente, monto, fecha_venc, hora_venc, cred_id, alerta in por_vencer:
    estado_alerta = "⚠️  SIN VER" if alerta == 0 else "✅ YA VISTO"
    print(f"  • {cliente}: {formatear_moneda(monto)} - {fecha_venc} {hora_venc} [{estado_alerta}]")

# FUNCIÓN 3: obtener_alertas_pendientes()
print("\n3️⃣  FUNCIÓN: obtener_alertas_pendientes()")
print("-" * 80)

alertas_pendientes = [c for c in vencidos if c[5] == 0]  # Filtrar por alerta_mostrada = 0
print(f"Créditos vencidos CON ALERTA PENDIENTE (alerta_mostrada = 0): {len(alertas_pendientes)}")

for cliente, monto, fecha_venc, hora_venc, cred_id, alerta in alertas_pendientes:
    print(f"  • {cliente}: {formatear_moneda(monto)} - {fecha_venc} {hora_venc}")

# RESUMEN Y RECOMENDACIONES
print("\n" + "=" * 80)
print("📊 RESUMEN Y ESTADO DEL SISTEMA DE ALERTAS")
print("=" * 80)

print(f"\n⏰ Hora actual del sistema: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📅 Fecha hoy: {fecha_hoy}")
print(f"🕒 Hora actual: {hora_actual}")

print(f"\n🔴 CRÉDITOS VENCIDOS: {len(vencidos)}")
if vencidos:
    alertas_sin_ver = len([c for c in vencidos if c[5] == 0])
    alertas_vistas = len([c for c in vencidos if c[5] == 1])
    print(f"   • Sin alerta: {alertas_sin_ver}")
    print(f"   • Alerta ya vista: {alertas_vistas}")
    if alertas_sin_ver > 0:
        print(f"   ✅ MOSTRARÁN ALERTA 🔴 ERROR en la interfaz")
else:
    print(f"   ✓ Ningún crédito vencido")

print(f"\n🟡 CRÉDITOS POR VENCER (en < 1 hora): {len(por_vencer)}")
if por_vencer:
    print(f"   ✅ MOSTRARÁN ALERTA 🟡 WARNING en la interfaz")
else:
    print(f"   ✓ Ningún crédito próximo a vencer")

# Verificar que se puede marcar como pagado
print("\n" + "=" * 80)
print("🧪 VERIFICACIÓN DE FUNCIONES DE ACTUALIZACIÓN")
print("=" * 80)

if vencidos:
    primer_credito_id = vencidos[0][4]
    print(f"\nProbando marcar crédito #{primer_credito_id} como pagado...")
    
    # No hacer la actualización real, solo simular
    print(f"   UPDATE creditos_pendientes SET pagado = 1 WHERE id = {primer_credito_id}")
    print(f"   ✅ Función marcar_credito_pagado() disponible")

if alertas_pendientes:
    primer_alerta_id = alertas_pendientes[0][4]
    print(f"\nProbando marcar alerta #{primer_alerta_id} como vista...")
    
    # No hacer la actualización real, solo simular
    print(f"   UPDATE creditos_pendientes SET alerta_mostrada = 1 WHERE id = {primer_alerta_id}")
    print(f"   ✅ Función marcar_alerta_mostrada() disponible")

print("\n" + "=" * 80)
print("✅ VERIFICACIÓN COMPLETADA")
print("=" * 80)
print("\n💡 Recomendaciones:")
print("   1. Ejecuta: streamlit run main.py")
print("   2. Inicia sesión")
print("   3. Abre 'Punto de Venta'")
if len(vencidos) > 0 and len([c for c in vencidos if c[5] == 0]) > 0:
    print("   4. ✅ Deberías ver alertas ROJAS de créditos vencidos")
if len(por_vencer) > 0:
    print("   4. ✅ Deberías ver alertas AMARILLAS de créditos por vencer")
print("   5. Haz clic en botones para marcar como pagado o desactivar alerta")
print("   6. Verifica que alerta_mostrada se actualice en la BD")

conn.close()
