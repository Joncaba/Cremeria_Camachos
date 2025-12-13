#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generar políticas RLS correctas para Supabase
"""

def main():
    print("\n" + "=" * 90)
    print("[CONFIGURACION RLS] Row Level Security para Supabase")
    print("=" * 90)
    
    print("\n[PROBLEMA]")
    print("  RLS está habilitado pero no hay políticas de acceso")
    print("  Resultado: 'new row violates row-level security policy'")
    
    print("\n[SOLUCION]")
    print("  Ejecuta en SQL Editor de Supabase:\n")
    
    print("-- ============================================")
    print("-- POLITICAS RLS PARA plu_catalogo")
    print("-- ============================================")
    print()
    print("-- Opción 1: Deshabilitar RLS (más simple, menos seguro)")
    print("ALTER TABLE public.plu_catalogo DISABLE ROW LEVEL SECURITY;")
    print()
    print("-- Opción 2: Habilitar acceso público (recomendado)")
    print("ALTER TABLE public.plu_catalogo ENABLE ROW LEVEL SECURITY;")
    print()
    print("-- Permitir lectura a todos")
    print("CREATE POLICY \"Enable read access for all users\" ON public.plu_catalogo")
    print("    FOR SELECT USING (true);")
    print()
    print("-- Permitir inserción a usuarios autenticados")
    print("CREATE POLICY \"Enable insert for authenticated users\" ON public.plu_catalogo")
    print("    FOR INSERT WITH CHECK (true);")
    print()
    print("-- Permitir actualización a usuarios autenticados")
    print("CREATE POLICY \"Enable update for authenticated users\" ON public.plu_catalogo")
    print("    FOR UPDATE USING (true);")
    print()
    print("-- Permitir eliminación a usuarios autenticados")
    print("CREATE POLICY \"Enable delete for authenticated users\" ON public.plu_catalogo")
    print("    FOR DELETE USING (true);")
    print()
    
    print("\n-- ============================================")
    print("-- POLITICAS RLS PARA TODAS LAS TABLAS NUEVAS")
    print("-- ============================================")
    print()
    
    tablas = [
        'bascula_mapeo',
        'codigos_barras', 
        'pedidos_reabastecimiento',
        'usuarios_admin'
    ]
    
    for tabla in tablas:
        print(f"-- Tabla: {tabla}")
        print(f"ALTER TABLE public.{tabla} ENABLE ROW LEVEL SECURITY;")
        print(f"CREATE POLICY \"Enable all for authenticated users\" ON public.{tabla}")
        print(f"    FOR ALL USING (true);")
        print()
    
    print("\n[ALTERNATIVA SIMPLE - Deshabilitar RLS en todas]")
    print("-- Solo para desarrollo/testing:")
    print()
    for tabla in ['plu_catalogo'] + tablas:
        print(f"ALTER TABLE public.{tabla} DISABLE ROW LEVEL SECURITY;")
    
    print("\n\n[RECOMENDACION]")
    print("  Para desarrollo/testing rápido:")
    print("    - Usa la ALTERNATIVA SIMPLE (deshabilitar RLS)")
    print()
    print("  Para producción:")
    print("    - Usa las políticas específicas (más seguro)")
    print()
    print("  Después ejecuta:")
    print("    python sync_all_to_supabase.py")
    
    print("\n" + "=" * 90 + "\n")

if __name__ == "__main__":
    main()
