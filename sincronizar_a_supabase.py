#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para sincronizar productos de SQLite local a Supabase
"""

import sqlite3
import os
import tomli
from supabase import create_client, Client

# Cargar configuración desde secrets.toml
secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
with open(secrets_path, 'rb') as f:
    secrets = tomli.load(f)

# Configuración
SUPABASE_URL = secrets['supabase']['url']
SUPABASE_KEY = secrets['supabase']['key']
DB_LOCAL = 'pos_cremeria.db'

def sincronizar_productos():
    """Sincronizar productos de SQLite a Supabase"""
    
    print("=" * 70)
    print("SINCRONIZACION DE PRODUCTOS: SQLite -> Supabase")
    print("=" * 70)
    
    # Conectar a SQLite
    print("\n1. Conectando a base de datos local...")
    conn_local = sqlite3.connect(DB_LOCAL)
    cursor = conn_local.cursor()
    
    # Contar productos locales
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_local = cursor.fetchone()[0]
    print(f"   Productos en SQLite: {total_local}")
    
    # Conectar a Supabase
    print("\n2. Conectando a Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Verificar productos en Supabase
    response = supabase.table('productos').select('codigo', count='exact').execute()
    total_supabase = response.count if hasattr(response, 'count') else len(response.data)
    print(f"   Productos en Supabase: {total_supabase}")
    
    # Obtener todos los productos de SQLite
    print("\n3. Obteniendo productos de SQLite...")
    cursor.execute("""
        SELECT codigo, numero_producto, nombre, precio_compra, precio_normal, 
               precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3,
               stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg,
               stock_minimo, stock_minimo_kg, stock_maximo, stock_maximo_kg,
               categoria
        FROM productos
    """)
    
    productos_local = cursor.fetchall()
    print(f"   Productos obtenidos: {len(productos_local)}")
    
    # Sincronizar cada producto
    print("\n4. Sincronizando productos...")
    insertados = 0
    actualizados = 0
    errores = 0
    
    for producto in productos_local:
        codigo = producto[0]
        
        try:
            # Preparar datos
            producto_data = {
                'codigo': producto[0],
                'numero_producto': producto[1],
                'nombre': producto[2],
                'precio_compra': float(producto[3]) if producto[3] else 0.0,
                'precio_normal': float(producto[4]) if producto[4] else 0.0,
                'precio_mayoreo_1': float(producto[5]) if producto[5] else 0.0,
                'precio_mayoreo_2': float(producto[6]) if producto[6] else 0.0,
                'precio_mayoreo_3': float(producto[7]) if producto[7] else 0.0,
                'stock': int(producto[8]) if producto[8] else 0,
                'tipo_venta': producto[9] or 'unidad',
                'precio_por_kg': float(producto[10]) if producto[10] else 0.0,
                'peso_unitario': float(producto[11]) if producto[11] else 0.0,
                'stock_kg': float(producto[12]) if producto[12] else 0.0,
                'stock_minimo': int(producto[13]) if producto[13] else 0,
                'stock_minimo_kg': float(producto[14]) if producto[14] else 0.0,
                'stock_maximo': int(producto[15]) if producto[15] else 0,
                'stock_maximo_kg': float(producto[16]) if producto[16] else 0.0,
                'categoria': producto[17] or 'otros'
            }
            
            # Verificar si existe en Supabase
            existing = supabase.table('productos').select('codigo').eq('codigo', codigo).execute()
            
            if existing.data and len(existing.data) > 0:
                # Actualizar
                supabase.table('productos').update(producto_data).eq('codigo', codigo).execute()
                actualizados += 1
                if actualizados % 50 == 0:
                    print(f"   Actualizados: {actualizados}...")
            else:
                # Insertar
                supabase.table('productos').insert(producto_data).execute()
                insertados += 1
                if insertados % 50 == 0:
                    print(f"   Insertados: {insertados}...")
                    
        except Exception as e:
            errores += 1
            print(f"   ERROR con {codigo}: {e}")
    
    conn_local.close()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN DE SINCRONIZACION")
    print("=" * 70)
    print(f"  Insertados: {insertados}")
    print(f"  Actualizados: {actualizados}")
    print(f"  Errores: {errores}")
    print(f"  Total procesados: {len(productos_local)}")
    
    # Verificar total final en Supabase
    response_final = supabase.table('productos').select('codigo', count='exact').execute()
    total_final = response_final.count if hasattr(response_final, 'count') else len(response_final.data)
    print(f"\n  Total en Supabase ahora: {total_final}")
    
    print("\n" + "=" * 70)
    print("SINCRONIZACION COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    sincronizar_productos()
