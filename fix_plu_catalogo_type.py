#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corregir estructura de tabla plu_catalogo en Supabase
Cambiar tipo de dato de INTEGER a BIGINT para soportar valores grandes
"""

import os

def get_supabase_client():
    """Obtener cliente de Supabase"""
    try:
        import streamlit as st
        url = st.secrets.get("supabase", {}).get("url")
        key = st.secrets.get("supabase", {}).get("key")
    except:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("[ERROR] Credenciales de Supabase no configuradas")
        return None
    
    from supabase import create_client
    return create_client(url, key)

def main():
    print("\n" + "=" * 90)
    print("[CORRECCION] Estructura de tabla plu_catalogo")
    print("=" * 90)
    
    print("\n[PROBLEMA DETECTADO]")
    print("  - Campo 'plu' tiene valores hasta 13 dígitos (máximo: 8,850,201,379,625)")
    print("  - INTEGER PostgreSQL soporta hasta 9 dígitos (máximo: 2,147,483,647)")
    print("  - Solución: Cambiar a BIGINT (64 bits)")
    
    print("\n[OPCION 1] Si la tabla plu_catalogo ESTA VACIA en Supabase:")
    print("  Ejecuta en SQL Editor de Supabase:")
    print("""
    DROP TABLE IF EXISTS public.plu_catalogo;
    
    CREATE TABLE IF NOT EXISTS public.plu_catalogo (
        plu BIGINT PRIMARY KEY,
        nombre TEXT NOT NULL,
        precio DECIMAL(10,2) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    ALTER TABLE public.plu_catalogo ENABLE ROW LEVEL SECURITY;
    """)
    
    print("\n[OPCION 2] Si la tabla TIENE DATOS en Supabase:")
    print("  Ejecuta en SQL Editor (cuidado, modifica la tabla existente):")
    print("""
    ALTER TABLE public.plu_catalogo 
    DROP CONSTRAINT plu_catalogo_pkey;
    
    ALTER TABLE public.plu_catalogo 
    ALTER COLUMN plu TYPE BIGINT;
    
    ALTER TABLE public.plu_catalogo 
    ADD PRIMARY KEY (plu);
    """)
    
    print("\n[RECOMENDACION]")
    print("  1. Usa OPCION 1 (más seguro - recrear tabla)")
    print("  2. Luego ejecuta: python sync_all_to_supabase.py")
    print("  3. Verifica con: python validate_supabase_sync.py")
    
    # Obtener estadísticas de SQLite
    print("\n[ESTADISTICAS SQLite - plu_catalogo]")
    import sqlite3
    conn = sqlite3.connect("pos_cremeria.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM plu_catalogo")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(plu), MAX(plu) FROM plu_catalogo")
    min_plu, max_plu = cursor.fetchone()
    
    cursor.execute("SELECT plu FROM plu_catalogo WHERE plu > 2147483647")
    large_plus = cursor.fetchall()
    
    print(f"  Total registros: {count}")
    print(f"  PLU mínimo: {min_plu}")
    print(f"  PLU máximo: {max_plu}")
    print(f"  PLU > 2,147,483,647 (limite INTEGER): {len(large_plus)}")
    
    if large_plus:
        print(f"  Ejemplos de PLU grandes:")
        for plu in large_plus[:5]:
            cursor.execute("SELECT plu, nombre FROM plu_catalogo WHERE plu = ?", plu)
            row = cursor.fetchone()
            print(f"    - {row[0]} ({row[1][:50]})")
    
    conn.close()
    
    print("\n[SIGUIENTE PASO]")
    print("  1. Ejecuta la sentencia SQL (OPCION 1 recomendada)")
    print("  2. Espera confirmación de éxito")
    print("  3. Luego ejecuta nuevamente: python sync_all_to_supabase.py")
    
    print("\n" + "=" * 90 + "\n")

if __name__ == "__main__":
    main()
