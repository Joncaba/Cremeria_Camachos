#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import sys

print("=" * 70)
print("VERIFICACION DE SINCRONIZACION CON SUPABASE")
print("=" * 70)

try:
    # 1. Verificar si sync_manager existe
    print("\n[PASO 1] Verificando sync_manager...")
    try:
        from sync_manager import get_sync_manager
        print("[OK] sync_manager importado exitosamente")
        
        # Intentar obtener instancia
        sync_manager = get_sync_manager()
        print("[OK] Instancia de sync_manager obtenida")
        
        # Verificar conexion
        if sync_manager.is_online():
            print("[OK] Conexion ONLINE con Supabase")
        else:
            print("[WARNING] Conexion OFFLINE - No hay conexion con Supabase")
            
    except ImportError as e:
        print(f"[ERROR] No se puede importar sync_manager: {e}")
        print("[INFO] La sincronizacion con Supabase no esta disponible")
    except Exception as e:
        print(f"[ERROR] Error con sync_manager: {e}")

    # 2. Verificar BD local
    print("\n[PASO 2] Verificando base de datos local...")
    conn = sqlite3.connect("pos_cremeria.db")
    cursor = conn.cursor()
    
    # Contar productos
    cursor.execute("SELECT COUNT(*) FROM productos")
    num_productos = cursor.fetchone()[0]
    print(f"[OK] Productos en BD local: {num_productos}")
    
    # Contar ventas
    cursor.execute("SELECT COUNT(*) FROM ventas")
    num_ventas = cursor.fetchone()[0]
    print(f"[OK] Ventas en BD local: {num_ventas}")
    
    # Contar usuarios
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    num_usuarios = cursor.fetchone()[0]
    print(f"[OK] Usuarios en BD local: {num_usuarios}")
    
    # Contar creditos
    cursor.execute("SELECT COUNT(*) FROM creditos_pendientes")
    num_creditos = cursor.fetchone()[0]
    print(f"[OK] Creditos pendientes en BD local: {num_creditos}")
    
    conn.close()
    
    # 3. Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE LA BD")
    print("=" * 70)
    print(f"Productos:         {num_productos}")
    print(f"Ventas registradas: {num_ventas}")
    print(f"Usuarios:          {num_usuarios}")
    print(f"Creditos:          {num_creditos}")
    print("=" * 70)
    
    # 4. Informacion de respaldo
    print("\n[INFO] RESPALDO EN SUPABASE:")
    print("-------")
    print("La sincronizacion automática está configurada para:")
    print("  - Sincronizar cada venta registrada")
    print("  - Actualizar stock cuando se vende un producto")
    print("  - Registrar cambios en creditos")
    print("")
    print("Si la conexion esta ONLINE, los cambios se sincronizan automaticamente.")
    print("Si la conexion esta OFFLINE, se sincronizaran cuando vuelva a haber conexion.")
    
except Exception as e:
    print(f"\n[ERROR CRITICO] {e}")
    sys.exit(1)

print("\n[OK] Verificacion completada\n")
