#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar estructura de Supabase vs SQLite
Identifica tablas y columnas que faltan para sincronizacion bidireccional
Utiliza configuracion desde secrets.toml o variables de entorno
"""

import sqlite3
import json
import os
from pathlib import Path
import sys

# Intentar cargar secrets desde streamlit
try:
    import streamlit as st
    secrets_available = True
    supabase_url = st.secrets.get("supabase", {}).get("url")
    supabase_key = st.secrets.get("supabase", {}).get("key")
except:
    secrets_available = False
    supabase_url = None
    supabase_key = None

# Fallback a variables de entorno
if not supabase_url:
    supabase_url = os.getenv("SUPABASE_URL")
if not supabase_key:
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

DB_PATH = "pos_cremeria.db"

def get_sqlite_structure():
    """Obtener estructura completa de SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener lista de tablas (excluir sqlite_sequence)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
        tables = [row[0] for row in cursor.fetchall()]
        
        structure = {}
        
        for table in tables:
            # Obtener informacion de columnas de cada tabla
            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()
            
            structure[table] = {
                'columns': {},
                'row_count': 0
            }
            
            for col_id, col_name, col_type, not_null, default_val, pk in columns_info:
                structure[table]['columns'][col_name] = {
                    'type': col_type,
                    'not_null': not_null,
                    'default': default_val,
                    'primary_key': pk
                }
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            structure[table]['row_count'] = cursor.fetchone()[0]
        
        return tables, structure
    
    finally:
        conn.close()

def get_supabase_structure():
    """Obtener estructura de Supabase"""
    try:
        from supabase import create_client
        
        if not supabase_url or not supabase_key:
            print("[ERROR] Credenciales de Supabase no configuradas")
            return None, None, None
        
        print(f"[OK] Conectando a Supabase: {supabase_url[:50]}...")
        
        # Crear cliente de Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Obtener lista de tablas que queremos verificar
        tables_to_check = [
            'productos',
            'ventas',
            'pedidos',
            'usuarios',
            'devoluciones',
            'egresos_adicionales',
            'pedidos_reabastecimiento',
            'ordenes_compra',
            'pedidos_items',
            'usuarios_admin',
            'turnos',
            'creditos_pendientes',
            'ingresos_pasivos',
            'codigos_barras',
            'plu_catalogo',
            'bascula_mapeo',
            'caja_chica_movimientos'
        ]
        
        supabase_tables = {}
        supabase_columns = {}
        
        for table in tables_to_check:
            try:
                # Intentar obtener 1 registro para verificar si existe
                response = supabase.table(table).select('*').limit(1).execute()
                supabase_tables[table] = True
                
                # Si tiene datos, obtener estructura
                if response.data and len(response.data) > 0:
                    first_record = response.data[0]
                    supabase_columns[table] = list(first_record.keys())
                    print(f"[EXISTE] Tabla '{table}' ({len(first_record.keys())} columnas)")
                else:
                    # Intentar obtener schema aunque este vacia
                    supabase_columns[table] = []
                    print(f"[EXISTE] Tabla '{table}' (vacia)")
                    
            except Exception as e:
                supabase_tables[table] = False
                print(f"[FALTA] Tabla '{table}': {str(e)[:80]}")
        
        return supabase, supabase_tables, supabase_columns
    
    except ImportError:
        print("[ERROR] El paquete 'supabase' no esta instalado")
        print("        Ejecuta: pip install supabase-py")
        return None, None, None
    except Exception as e:
        print(f"[ERROR] Error conectando a Supabase: {str(e)}")
        return None, None, None

def generate_report():
    """Generar reporte de validacion"""
    print("\n" + "=" * 90)
    print("[VALIDACION] Estructura de Base de Datos - SQLite vs Supabase")
    print("=" * 90)
    
    # 1. Obtener estructura SQLite
    print("\n[PASO 1] Analizando estructura SQLite...")
    sqlite_tables, sqlite_structure = get_sqlite_structure()
    
    print(f"\n[OK] Encontradas {len(sqlite_tables)} tablas en SQLite:")
    for table in sorted(sqlite_tables):
        col_count = len(sqlite_structure[table]['columns'])
        row_count = sqlite_structure[table]['row_count']
        print(f"     {table:35} ({col_count:2} columnas, {row_count:6} registros)")
    
    # 2. Verificar credenciales
    print("\n[PASO 2] Verificando credenciales de Supabase...")
    if not supabase_url or not supabase_key:
        print("[ERROR] Credenciales NO configuradas")
        print("\nOpciones:")
        print("  1. Crear archivo 'secrets.toml' en el directorio del proyecto:")
        print("     [supabase]")
        print("     url = 'https://tu-proyecto.supabase.co'")
        print("     key = 'tu-anon-key'")
        print("\n  2. O configurar variables de entorno:")
        print("     SET SUPABASE_URL=https://tu-proyecto.supabase.co")
        print("     SET SUPABASE_KEY=tu-anon-key")
        return
    
    print(f"[OK] Credenciales detectadas")
    
    # 3. Obtener estructura Supabase
    print("\n[PASO 3] Verificando tablas en Supabase...")
    supabase, supabase_tables, supabase_columns = get_supabase_structure()
    
    if not supabase_tables:
        print("\n[ERROR] No se pudo conectar a Supabase")
        return
    
    # 4. Comparar estructuras
    print("\n" + "=" * 90)
    print("[COMPARACION] Tablas: SQLite vs Supabase")
    print("=" * 90)
    
    tablas_faltantes = []
    tablas_en_supabase = []
    
    for table in sorted(sqlite_tables):
        if supabase_tables.get(table, False):
            tablas_en_supabase.append(table)
            col_count_sqlite = len(sqlite_structure[table]['columns'])
            col_count_supa = len(supabase_columns.get(table, []))
            
            if col_count_supa > 0:
                print(f"[OK] {table:35} (SQLite: {col_count_sqlite:2} cols, Supabase: {col_count_supa:2} cols)")
            else:
                print(f"[OK] {table:35} (vacia en Supabase)")
        else:
            tablas_faltantes.append(table)
            col_count = len(sqlite_structure[table]['columns'])
            print(f"[FALTA] {table:35} ({col_count} columnas en SQLite)")
    
    # 5. Detallar estructuras faltantes
    if tablas_faltantes:
        print("\n" + "=" * 90)
        print("[DETALLES] Tablas que faltan en Supabase")
        print("=" * 90)
        
        for table in tablas_faltantes:
            print(f"\nTabla: '{table}'")
            print(f"Registros en SQLite: {sqlite_structure[table]['row_count']}")
            print(f"Columnas ({len(sqlite_structure[table]['columns'])}):")
            
            for col_name, col_info in sqlite_structure[table]['columns'].items():
                pk_mark = " [PRIMARY KEY]" if col_info['primary_key'] else ""
                nullable = "NULL" if not col_info['not_null'] else "NOT NULL"
                print(f"  - {col_name:25} {col_info['type']:15} {nullable}{pk_mark}")
    
    # 6. Crear script SQL para Supabase
    if tablas_faltantes:
        print("\n" + "=" * 90)
        print("[SQL] Script para crear tablas faltantes en Supabase")
        print("=" * 90)
        print("\nEjecuta los siguientes comandos en SQL Editor de Supabase:\n")
        
        for table in tablas_faltantes:
            print(f"-- Tabla: {table}")
            print(f"CREATE TABLE IF NOT EXISTS public.{table} (")
            
            columns = sqlite_structure[table]['columns']
            col_list = []
            
            for col_name, col_info in columns.items():
                # Mapear tipos SQLite a PostgreSQL
                sqlite_type = col_info['type'].upper() if col_info['type'] else 'TEXT'
                
                if 'INT' in sqlite_type:
                    pg_type = 'INTEGER'
                elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type:
                    pg_type = 'DECIMAL(10,2)'
                elif 'BOOL' in sqlite_type:
                    pg_type = 'BOOLEAN'
                elif 'TEXT' in sqlite_type or 'CHAR' in sqlite_type or not sqlite_type:
                    pg_type = 'TEXT'
                elif 'TIMESTAMP' in sqlite_type or 'DATE' in sqlite_type:
                    pg_type = 'TIMESTAMP WITH TIME ZONE'
                else:
                    pg_type = 'TEXT'
                
                col_def = f"    {col_name} {pg_type}"
                
                if col_info['primary_key']:
                    col_def += " PRIMARY KEY"
                elif col_info['not_null']:
                    col_def += " NOT NULL"
                
                col_list.append(col_def)
            
            print(",\n".join(col_list))
            print(");\n")
    
    # 7. Resumen
    print("\n" + "=" * 90)
    print("[RESUMEN]")
    print("=" * 90)
    
    print(f"\nTablas SQLite:            {len(sqlite_tables)}")
    print(f"Tablas en Supabase:       {len(tablas_en_supabase)}")
    print(f"Tablas faltantes:         {len(tablas_faltantes)}")
    
    if tablas_faltantes:
        print(f"\n[PENDIENTE] Se requieren {len(tablas_faltantes)} acciones:")
        print("  1. Crear tablas en Supabase (ejecutar SQL arriba)")
        print("  2. Verificar tipos de datos")
        print("  3. Configurar RLS (Row Level Security)")
        print("  4. Sincronizar datos iniciales")
    else:
        print("\n[OK] Todas las tablas de SQLite existen en Supabase")
        print("     Puedes proceder con la sincronizacion bidireccional")
    
    # 8. Detalles de tabla productos
    print("\n" + "=" * 90)
    print("[COLUMNAS DETALLE] Tabla 'productos'")
    print("=" * 90)
    
    if 'productos' in sqlite_structure:
        print("\nEstructura en SQLite:")
        for col_name, col_info in sqlite_structure['productos']['columns'].items():
            pk = "[PK]" if col_info['primary_key'] else ""
            nn = "NOT NULL" if col_info['not_null'] else "NULL"
            print(f"  {col_name:25} {col_info['type']:15} {nn:10} {pk}")
        
        if 'productos' in supabase_columns and supabase_columns['productos']:
            print(f"\nColumnas en Supabase ({len(supabase_columns['productos'])}):")
            for col in sorted(supabase_columns['productos']):
                print(f"  - {col}")
    
    print("\n" + "=" * 90 + "\n")

if __name__ == "__main__":
    generate_report()
