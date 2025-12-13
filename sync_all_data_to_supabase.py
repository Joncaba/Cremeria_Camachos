#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizar TODOS los datos de SQLite a Supabase
Incluye todas las tablas con registros
"""

import sqlite3
import sys

DB_PATH = "pos_cremeria.db"

def get_supabase_client():
    """Obtener cliente de Supabase"""
    try:
        import streamlit as st
        url = st.secrets.get("supabase", {}).get("url")
        key = st.secrets.get("supabase", {}).get("key")
    except:
        import os
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("[ERROR] Credenciales de Supabase no configuradas")
        return None
    
    from supabase import create_client
    return create_client(url, key)

def read_sqlite_data(table_name):
    """Leer datos de una tabla SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"  [ERROR] Error leyendo tabla {table_name}: {e}")
        return []
    finally:
        conn.close()

def sync_table_to_supabase(supabase_client, table_name, data):
    """Sincronizar tabla a Supabase"""
    if not data:
        print(f"  [INFO] Tabla vacia en SQLite, omitiendo...")
        return True, 0
    
    try:
        # Hacer upsert de los datos en lotes de 100
        batch_size = 100
        total_synced = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            response = supabase_client.table(table_name).upsert(batch).execute()
            
            if response.data:
                total_synced += len(response.data)
            else:
                total_synced += len(batch)
        
        print(f"  [OK] {total_synced} registros sincronizados")
        return True, total_synced
            
    except Exception as e:
        error_msg = str(e)[:200]
        print(f"  [ERROR] {error_msg}")
        return False, 0

def main():
    print("\n" + "=" * 90)
    print("[SINCRONIZACION COMPLETA] Todos los datos de SQLite a Supabase")
    print("=" * 90)
    
    # TODAS las tablas a sincronizar
    todas_las_tablas = [
        'productos',
        'ventas',
        'pedidos',
        'usuarios',
        'devoluciones',
        'egresos_adicionales',
        'ingresos_pasivos',
        'ordenes_compra',
        'pedidos_items',
        'pedidos_reabastecimiento',
        'plu_catalogo',
        'usuarios_admin',
        'turnos',
        'creditos_pendientes',
        'codigos_barras',
        'bascula_mapeo',
        'caja_chica_movimientos'
    ]
    
    # Conectar a Supabase
    print("\n[PASO 1] Conectando a Supabase...")
    supabase = get_supabase_client()
    
    if not supabase:
        print("[ERROR] No se pudo conectar a Supabase")
        return False
    
    print("[OK] Conectado a Supabase")
    
    # Obtener estadísticas de SQLite
    print("\n[PASO 2] Analizando datos en SQLite...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_registros_sqlite = 0
    tablas_con_datos = []
    
    for tabla in todas_las_tablas:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            total_registros_sqlite += count
            if count > 0:
                tablas_con_datos.append((tabla, count))
                print(f"  {tabla:35} {count:6} registros")
        except Exception as e:
            print(f"  {tabla:35} [ERROR: {str(e)[:50]}]")
    
    conn.close()
    
    print(f"\n[RESUMEN] Total de registros a sincronizar: {total_registros_sqlite}")
    print(f"[RESUMEN] Tablas con datos: {len(tablas_con_datos)}")
    
    # Confirmar
    print("\n" + "=" * 90)
    respuesta = input("¿Continuar con la sincronización? (s/n): ").lower()
    if respuesta != 's':
        print("[CANCELADO] Sincronización cancelada por el usuario")
        return False
    
    # Sincronizar cada tabla
    print("\n[PASO 3] Sincronizando tablas...")
    
    resultados = {
        'exitosas': [],
        'fallidas': [],
        'total_registros': 0
    }
    
    for tabla, count in tablas_con_datos:
        print(f"\n{'='*50}")
        print(f"Tabla: {tabla} ({count} registros)")
        print(f"{'='*50}")
        
        # Leer datos de SQLite
        print(f"[LECTURA] Leyendo datos...")
        datos = read_sqlite_data(tabla)
        
        if not datos:
            print(f"  [SKIP] No hay datos para sincronizar")
            continue
        
        print(f"  [OK] {len(datos)} registros leidos")
        
        # Sincronizar a Supabase
        print(f"[SYNC] Sincronizando a Supabase...")
        success, synced_count = sync_table_to_supabase(supabase, tabla, datos)
        
        if success:
            resultados['exitosas'].append(tabla)
            resultados['total_registros'] += synced_count
        else:
            resultados['fallidas'].append(tabla)
    
    # Resumen final
    print("\n" + "=" * 90)
    print("[RESUMEN FINAL]")
    print("=" * 90)
    
    print(f"\nTablas sincronizadas exitosamente: {len(resultados['exitosas'])}/{len(tablas_con_datos)}")
    for tabla in resultados['exitosas']:
        print(f"  ✅ {tabla}")
    
    if resultados['fallidas']:
        print(f"\nTablas con errores: {len(resultados['fallidas'])}")
        for tabla in resultados['fallidas']:
            print(f"  ❌ {tabla}")
    
    print(f"\n📊 ESTADISTICAS:")
    print(f"  Total registros en SQLite:    {total_registros_sqlite:,}")
    print(f"  Total registros sincronizados: {resultados['total_registros']:,}")
    print(f"  Cobertura: {(resultados['total_registros']/total_registros_sqlite*100):.1f}%")
    
    # Siguiente paso
    print("\n" + "=" * 90)
    print("[SIGUIENTE PASO]")
    print("=" * 90)
    
    if not resultados['fallidas']:
        print("\n✅ SINCRONIZACION COMPLETA")
        print("\nTu base de datos está 100% sincronizada!")
        print("\nPuedes:")
        print("  1. Verificar datos en Supabase (Table Editor)")
        print("  2. Probar cambios en tu app Streamlit")
        print("  3. Los cambios se sincronizarán automáticamente")
    else:
        print("\n⚠️ Hubo errores en algunas tablas")
        print("\nRevisa los errores arriba y:")
        print("  1. Verifica la estructura de las tablas en Supabase")
        print("  2. Asegúrate de que RLS esté configurado correctamente")
        print("  3. Intenta sincronizar las tablas fallidas individualmente")
    
    print("\n" + "=" * 90 + "\n")
    
    return len(resultados['fallidas']) == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELADO] Sincronización interrumpida por el usuario")
        sys.exit(1)
