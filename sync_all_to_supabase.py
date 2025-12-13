#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para sincronizar datos de SQLite a Supabase
Copia los datos de las tablas faltantes desde SQLite hacia Supabase
"""

import sqlite3
import json
from pathlib import Path
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
        print(f"[ERROR] Error leyendo tabla {table_name}: {e}")
        return []
    finally:
        conn.close()

def sync_table_to_supabase(supabase_client, table_name, data):
    """Sincronizar tabla a Supabase"""
    if not data:
        print(f"[INFO] Tabla {table_name} esta vacia, omitiendo...")
        return True, 0
    
    try:
        print(f"\n[SYNC] Sincronizando {table_name}...")
        print(f"  Registros a sincronizar: {len(data)}")
        
        # Hacer upsert de los datos
        response = supabase_client.table(table_name).upsert(data).execute()
        
        if response.data:
            print(f"  [OK] {len(response.data)} registros sincronizados")
            return True, len(response.data)
        else:
            print(f"  [OK] Sincronización completada")
            return True, len(data)
            
    except Exception as e:
        print(f"  [ERROR] {str(e)[:200]}")
        return False, 0

def main():
    print("\n" + "=" * 90)
    print("[SINCRONIZACION] Tablas de SQLite a Supabase")
    print("=" * 90)
    
    # Tablas que necesitan sincronización
    tablas_a_sincronizar = [
        'bascula_mapeo',
        'codigos_barras',
        'pedidos_reabastecimiento',
        'plu_catalogo',
        'usuarios_admin'
    ]
    
    # Obtener cliente de Supabase
    print("\n[PASO 1] Conectando a Supabase...")
    supabase = get_supabase_client()
    
    if not supabase:
        print("[ERROR] No se pudo conectar a Supabase")
        return False
    
    print("[OK] Conectado a Supabase")
    
    # Sincronizar cada tabla
    print("\n[PASO 2] Sincronizando tablas...")
    
    resultados = {
        'exitosas': [],
        'fallidas': [],
        'total_registros': 0
    }
    
    for tabla in tablas_a_sincronizar:
        print(f"\n{'='*50}")
        print(f"Tabla: {tabla}")
        print(f"{'='*50}")
        
        # Leer datos de SQLite
        print(f"[LECTURA] Leyendo datos de SQLite...")
        datos = read_sqlite_data(tabla)
        
        if datos:
            print(f"[OK] {len(datos)} registros leidos")
        else:
            print(f"[INFO] Tabla vacia en SQLite")
            continue
        
        # Sincronizar a Supabase
        success, count = sync_table_to_supabase(supabase, tabla, datos)
        
        if success:
            resultados['exitosas'].append(tabla)
            resultados['total_registros'] += count
        else:
            resultados['fallidas'].append(tabla)
    
    # Resumen
    print("\n" + "=" * 90)
    print("[RESUMEN]")
    print("=" * 90)
    
    print(f"\nTablas sincronizadas exitosamente: {len(resultados['exitosas'])}")
    for tabla in resultados['exitosas']:
        print(f"  ✅ {tabla}")
    
    if resultados['fallidas']:
        print(f"\nTablas con errores: {len(resultados['fallidas'])}")
        for tabla in resultados['fallidas']:
            print(f"  ❌ {tabla}")
    
    print(f"\nTotal de registros sincronizados: {resultados['total_registros']}")
    
    # Instrucciones finales
    print("\n" + "=" * 90)
    print("[SIGUIENTE PASO]")
    print("=" * 90)
    
    if not resultados['fallidas']:
        print("\n✅ Sincronización completada exitosamente")
        print("\nAhora debes:")
        print("  1. Verificar que los datos esten en Supabase")
        print("  2. Ejecutar: python validate_supabase_sync.py")
        print("  3. Habilitar RLS en Supabase si no lo has hecho")
        print("  4. Probar la sincronización bidireccional")
    else:
        print("\n⚠️ Hubo errores durante la sincronización")
        print("\nVerifica que:")
        print("  1. Las tablas existen en Supabase")
        print("  2. RLS esta habilitado correctamente")
        print("  3. Tienes permisos de escritura")
    
    print("\n" + "=" * 90 + "\n")
    
    return len(resultados['fallidas']) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
