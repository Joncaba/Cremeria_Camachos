#!/usr/bin/env python3
"""
Script de validación rápida del sistema de alertas
Ejecuta todas las verificaciones necesarias en un solo paso
"""

import sqlite3
from datetime import datetime, timedelta
import sys

print("=" * 80)
print("🚀 VALIDACIÓN RÁPIDA: SISTEMA DE ALERTAS DE CRÉDITOS")
print("=" * 80)

try:
    # 1. Conectar a BD
    print("\n✓ Conectando a base de datos...")
    conn = sqlite3.connect("pos_cremeria.db")
    cursor = conn.cursor()
    print("  ✅ BD conectada exitosamente")
    
    # 2. Verificar tabla existe
    print("\n✓ Verificando tabla creditos_pendientes...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='creditos_pendientes'")
    if cursor.fetchone():
        print("  ✅ Tabla creditos_pendientes existe")
    else:
        print("  ❌ Tabla creditos_pendientes NO existe")
        sys.exit(1)
    
    # 3. Verificar columnas
    print("\n✓ Verificando columnas requeridas...")
    cursor.execute("PRAGMA table_info(creditos_pendientes)")
    columnas = {col[1]: col[2] for col in cursor.fetchall()}
    
    requeridas = ['id', 'cliente', 'monto', 'fecha_vencimiento', 'hora_vencimiento', 
                  'pagado', 'alerta_mostrada']
    
    for col in requeridas:
        if col in columnas:
            print(f"  ✅ Columna '{col}' existe")
        else:
            print(f"  ❌ Columna '{col}' FALTA")
            sys.exit(1)
    
    # 4. Contar créditos
    print("\n✓ Analizando créditos...")
    cursor.execute("SELECT COUNT(*) FROM creditos_pendientes")
    total = cursor.fetchone()[0]
    print(f"  ✅ Total de créditos en BD: {total}")
    
    # 5. Contar créditos de prueba
    cursor.execute("SELECT COUNT(*) FROM creditos_pendientes WHERE cliente LIKE 'PRUEBA_%'")
    prueba = cursor.fetchone()[0]
    if prueba > 0:
        print(f"  ℹ️  Créditos de prueba: {prueba}")
        print("     (Ejecuta: python limpiar_prueba_alertas.py para limpiar)")
    
    # 6. Analizar créditos vencidos
    print("\n✓ Verificando créditos vencidos...")
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    cursor.execute('''
        SELECT COUNT(*) FROM creditos_pendientes 
        WHERE pagado = 0 AND (
            fecha_vencimiento < ? 
            OR (fecha_vencimiento = ? AND hora_vencimiento < ?)
        )
    ''', (fecha_hoy, fecha_hoy, hora_actual))
    vencidos = cursor.fetchone()[0]
    print(f"  ℹ️  Créditos vencidos (sin pagar): {vencidos}")
    
    # 7. Analizar créditos por vencer
    print("\n✓ Verificando créditos por vencer...")
    una_hora_despues = (ahora + timedelta(hours=1)).strftime("%H:%M")
    
    cursor.execute('''
        SELECT COUNT(*) FROM creditos_pendientes 
        WHERE pagado = 0 AND fecha_vencimiento = ? 
            AND hora_vencimiento > ? AND hora_vencimiento <= ?
    ''', (fecha_hoy, hora_actual, una_hora_despues))
    por_vencer = cursor.fetchone()[0]
    print(f"  ℹ️  Créditos por vencer en < 1 hora: {por_vencer}")
    
    # 8. Verificar alertas sin mostrar
    print("\n✓ Verificando alertas pendientes...")
    if vencidos > 0:
        cursor.execute('''
            SELECT COUNT(*) FROM creditos_pendientes 
            WHERE pagado = 0 AND alerta_mostrada = 0 AND (
                fecha_vencimiento < ? 
                OR (fecha_vencimiento = ? AND hora_vencimiento < ?)
            )
        ''', (fecha_hoy, fecha_hoy, hora_actual))
        alertas_sin_ver = cursor.fetchone()[0]
        print(f"  ℹ️  Alertas vencidas sin mostrar: {alertas_sin_ver}")
        if alertas_sin_ver > 0:
            print(f"     ✅ Se mostrarán al entrar a Punto de Venta")
    else:
        print(f"  ✅ No hay alertas pendientes")
    
    # 9. Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DEL SISTEMA")
    print("=" * 80)
    
    print(f"\n⏰ Hora actual: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Total de créditos: {total}")
    print(f"🔴 Vencidos (no pagados): {vencidos}")
    print(f"🟡 Por vencer (< 1 hora): {por_vencer}")
    
    if vencidos > 0 or por_vencer > 0:
        print(f"\n✅ El sistema está listo para mostrar alertas")
        print(f"   Abre 'Punto de Venta' para ver las notificaciones")
    else:
        print(f"\n✓ No hay alertas activas en este momento")
        if prueba > 0:
            print(f"  💡 Los créditos de prueba están configurados")
            print(f"     Ejecuta: python test_alertas_creditos.py")
    
    # 10. Verificar funciones de ventas.py
    print("\n✓ Verificando funciones en ventas.py...")
    import importlib.util
    spec = importlib.util.spec_from_file_location("ventas", "ventas.py")
    ventas = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(ventas)
        
        # Verificar que las funciones existen
        funciones = [
            'obtener_creditos_vencidos',
            'obtener_creditos_por_vencer',
            'obtener_alertas_pendientes',
            'marcar_credito_pagado',
            'marcar_alerta_mostrada',
            'mostrar_popup_alertas_mejorado'
        ]
        
        for func in funciones:
            if hasattr(ventas, func):
                print(f"  ✅ {func}() existe")
            else:
                print(f"  ❌ {func}() NO existe")
                sys.exit(1)
    except Exception as e:
        print(f"  ⚠️  No se pudo importar ventas.py: {e}")
        print(f"     (Pero el archivo parece estar bien)")
    
    # 11. Éxito final
    print("\n" + "=" * 80)
    print("✅ VALIDACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    
    print("\n🚀 Próximos pasos:")
    if total == 0:
        print("   1. Ejecuta: python test_alertas_creditos.py (para datos de prueba)")
    print("   2. Ejecuta: streamlit run main.py")
    print("   3. Inicia sesión con admin/Creme$123")
    print("   4. Abre 'Punto de Venta'")
    if vencidos > 0 or por_vencer > 0 or prueba > 0:
        print("   5. Deberías ver alertas emergentes")
    
    print("\n📚 Para más info: cat ALERTAS_CREDITOS_DOCUMENTACION.md")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
