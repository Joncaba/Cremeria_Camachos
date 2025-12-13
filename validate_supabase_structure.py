#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar estructura de Supabase vs SQLite
Identifica tablas y columnas que faltan para sincronizacion bidireccional
"""

import sqlite3
import json
from pathlib import Path

# Rutas
DB_PATH = "pos_cremeria.db"

def get_sqlite_structure():
    """Obtener estructura completa de SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener lista de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
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
        from sync_manager import get_sync_manager
        sync = get_sync_manager()
        
        # Intentar obtener estructura desde Supabase
        supabase_structure = {}
        
        # Conectar a Supabase directamente
        from supabase import create_client
        import os
        
        # Leer credenciales
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("[ADVERTENCIA] Variables de entorno SUPABASE_URL o SUPABASE_KEY no configuradas")
            return None, None
        
        # Crear cliente de Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Obtener lista de tablas
        # En Supabase no hay una forma directa de listar tablas via API, 
        # asi que verificaremos las principales
        tables_to_check = [
            'productos',
            'ventas',
            'pedidos',
            'usuarios',
            'devoluciones',
            'egresos_adicionales',
            'movimientos_caja',
            'inventario_logs'
        ]
        
        supabase_tables = {}
        
        for table in tables_to_check:
            try:
                # Intentar obtener 1 registro para verificar si existe
                response = supabase.table(table).select('*').limit(1).execute()
                
                if response.data or len(response.data) == 0:  # La tabla existe aunque este vacia
                    supabase_tables[table] = True
                    print(f"[OK] Tabla '{table}' existe en Supabase")
            except Exception as e:
                print(f"[FALTA] Tabla '{table}' no existe en Supabase: {str(e)[:100]}")
                supabase_tables[table] = False
        
        return supabase, supabase_tables
    
    except ImportError:
        print("[ERROR] No se puede importar supabase o sync_manager")
        return None, None
    except Exception as e:
        print(f"[ERROR] Error conectando a Supabase: {str(e)}")
        return None, None

def generate_report():
    """Generar reporte de validacion"""
    print("\n" + "=" * 80)
    print("[VALIDACION] Estructura de Base de Datos - SQLite vs Supabase")
    print("=" * 80)
    
    # 1. Obtener estructura SQLite
    print("\n[1] Analizando estructura SQLite...")
    sqlite_tables, sqlite_structure = get_sqlite_structure()
    
    print(f"[OK] Encontradas {len(sqlite_tables)} tablas en SQLite:")
    for table in sqlite_tables:
        col_count = len(sqlite_structure[table]['columns'])
        row_count = sqlite_structure[table]['row_count']
        print(f"     - {table:30} ({col_count:2} columnas, {row_count:6} registros)")
    
    # 2. Obtener estructura Supabase
    print("\n[2] Verificando tablas en Supabase...")
    supabase, supabase_tables = get_supabase_structure()
    
    if not supabase_tables:
        print("[ERROR] No se pudo conectar a Supabase")
        print("[INSTRUCCION] Verifica que:")
        print("  1. Las variables de entorno SUPABASE_URL y SUPABASE_KEY estan configuradas")
        print("  2. Tienes conectividad a internet")
        print("  3. Tu proyecto Supabase esta activo")
        return
    
    print(f"\n[OK] Verificadas tablas en Supabase:")
    for table, exists in supabase_tables.items():
        status = "[EXISTE]" if exists else "[FALTA]"
        print(f"     {status} {table}")
    
    # 3. Comparar estructuras
    print("\n" + "=" * 80)
    print("[COMPARACION] Tablas en SQLite vs Supabase")
    print("=" * 80)
    
    tablas_faltantes = []
    tablas_en_supabase = []
    
    for table in sqlite_tables:
        if supabase_tables.get(table, False):
            tablas_en_supabase.append(table)
            print(f"[OK] {table:30} EXISTE en ambas bases de datos")
        else:
            tablas_faltantes.append(table)
            col_count = len(sqlite_structure[table]['columns'])
            print(f"[FALTA] {table:30} NO EXISTE en Supabase ({col_count} columnas en SQLite)")
    
    # 4. Detallar estructuras faltantes
    if tablas_faltantes:
        print("\n" + "=" * 80)
        print("[DETALLES] Tablas que faltan en Supabase")
        print("=" * 80)
        
        for table in tablas_faltantes:
            print(f"\nTabla: {table}")
            print(f"Registros en SQLite: {sqlite_structure[table]['row_count']}")
            print(f"Columnas ({len(sqlite_structure[table]['columns'])}):")
            
            for col_name, col_info in sqlite_structure[table]['columns'].items():
                pk_mark = " [PRIMARY KEY]" if col_info['primary_key'] else ""
                nullable = "NULL" if not col_info['not_null'] else "NOT NULL"
                print(f"  - {col_name:25} {col_info['type']:15} {nullable}{pk_mark}")
    
    # 5. Crear script SQL para Supabase
    print("\n" + "=" * 80)
    print("[SQL] Script para crear tablas faltantes en Supabase")
    print("=" * 80)
    
    if tablas_faltantes:
        print("\nEjecuta los siguientes comandos en la consola SQL de Supabase:\n")
        
        for table in tablas_faltantes:
            print(f"-- Tabla: {table}")
            print(f"CREATE TABLE IF NOT EXISTS {table} (")
            
            columns = sqlite_structure[table]['columns']
            col_list = []
            
            for col_name, col_info in columns.items():
                # Mapear tipos SQLite a PostgreSQL
                sqlite_type = col_info['type'].upper()
                
                if 'INT' in sqlite_type:
                    pg_type = 'INTEGER'
                elif 'REAL' in sqlite_type or 'FLOAT' in sqlite_type:
                    pg_type = 'DECIMAL(10,2)'
                elif 'BOOL' in sqlite_type:
                    pg_type = 'BOOLEAN'
                elif 'TEXT' in sqlite_type or 'CHAR' in sqlite_type:
                    pg_type = 'TEXT'
                elif 'TIMESTAMP' in sqlite_type or 'DATE' in sqlite_type:
                    pg_type = 'TIMESTAMP WITH TIME ZONE'
                else:
                    pg_type = 'TEXT'
                
                col_def = f"  {col_name} {pg_type}"
                
                if col_info['primary_key']:
                    col_def += " PRIMARY KEY"
                
                if col_info['not_null']:
                    col_def += " NOT NULL"
                elif col_info['default']:
                    col_def += f" DEFAULT {col_info['default']}"
                
                col_list.append(col_def)
            
            print(",\n".join(col_list))
            print(");\n")
    else:
        print("\n[OK] Todas las tablas de SQLite existen en Supabase")
    
    # 6. Resumen y recomendaciones
    print("\n" + "=" * 80)
    print("[RESUMEN]")
    print("=" * 80)
    
    print(f"\nTablas SQLite:        {len(sqlite_tables)}")
    print(f"Tablas en Supabase:   {len(tablas_en_supabase)}")
    print(f"Tablas faltantes:     {len(tablas_faltantes)}")
    
    if tablas_faltantes:
        print("\n[ACCIONES REQUERIDAS]")
        print(f"1. Crear {len(tablas_faltantes)} tabla(s) en Supabase (ver script SQL arriba)")
        print("2. Ejecutar sincronizacion inicial para copiar datos desde SQLite")
        print("3. Verificar que los tipos de datos sean correctos")
        print("4. Configurar permisos RLS (Row Level Security) en Supabase")
        print("5. Habilitar sincronizacion bidireccional")
    else:
        print("\n[OK] Estructura sincronizada correctamente")
        print("Puedes proceder con la sincronizacion bidireccional")
    
    # 7. Detalles de columnas especificas
    print("\n" + "=" * 80)
    print("[COLUMNAS] Productos - Detalles de estructura")
    print("=" * 80)
    
    if 'productos' in sqlite_structure:
        print("\nColumnas en tabla 'productos' (SQLite):")
        for col_name, col_info in sqlite_structure['productos']['columns'].items():
            print(f"  {col_name:25} {col_info['type']:15} PK={col_info['primary_key']} NOT_NULL={col_info['not_null']}")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    generate_report()
