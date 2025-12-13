#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para normalizar tipo_venta de 'granel' a 'kg' en Supabase
"""

import os
import tomli
from supabase import create_client, Client

# Cargar configuración desde secrets.toml
secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
with open(secrets_path, 'rb') as f:
    secrets = tomli.load(f)

# Configuración de Supabase
SUPABASE_URL = secrets['supabase']['url']
SUPABASE_KEY = secrets['supabase']['key']

def actualizar_supabase():
    """Actualizar tipo_venta en Supabase"""
    try:
        print("=" * 60)
        print("ACTUALIZANDO SUPABASE")
        print("=" * 60)
        
        # Conectar a Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Verificar productos con 'granel'
        response = supabase.table('productos').select('codigo, nombre, tipo_venta').eq('tipo_venta', 'granel').execute()
        
        productos_granel = response.data if response.data else []
        
        print(f"\nProductos con tipo_venta = 'granel': {len(productos_granel)}")
        
        if productos_granel:
            print("\nActualizando productos:")
            actualizados = 0
            
            for producto in productos_granel:
                try:
                    supabase.table('productos').update({
                        'tipo_venta': 'kg'
                    }).eq('codigo', producto['codigo']).execute()
                    
                    print(f"  OK - {producto['codigo']} - {producto['nombre'][:50]}")
                    actualizados += 1
                except Exception as e:
                    print(f"  ERROR - {producto['codigo']}: {e}")
            
            print(f"\nTotal actualizados: {actualizados}/{len(productos_granel)}")
        else:
            print("\nOK - No hay productos con 'granel', todos estan correctos")
        
        # Verificar estadísticas finales
        print("\n" + "=" * 60)
        print("ESTADISTICAS FINALES EN SUPABASE")
        print("=" * 60)
        
        for tipo in ['kg', 'unidad', 'granel']:
            response = supabase.table('productos').select('codigo', count='exact').eq('tipo_venta', tipo).execute()
            count = response.count if hasattr(response, 'count') else 0
            if count > 0 or tipo in ['kg', 'unidad']:
                print(f"  {tipo}: {count} productos")
        
        print("\n" + "=" * 60)
        print("PROCESO COMPLETADO")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    actualizar_supabase()
