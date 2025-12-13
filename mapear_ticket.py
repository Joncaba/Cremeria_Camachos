#!/usr/bin/env python3
"""
Asistente para mapear códigos de báscula a productos.

El ticket contiene estos códigos:
  - 208033201 → ?
  - 200007200 → ?
  - 200014001 → 20001400 (HUEVO BLANCO) ✓

Este script te ayuda a identificar el resto.
"""

import sqlite3
import sys

DB_PATH = "pos_cremeria.db"

def buscar_producto(codigo_o_texto):
    """Buscar un producto por código o nombre"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Si es un número, buscar por código
    if codigo_o_texto.isdigit():
        cursor.execute("""
            SELECT codigo, numero_producto, nombre FROM productos 
            WHERE codigo LIKE ? OR codigo = ?
            ORDER BY codigo
            LIMIT 10
        """, (f"{codigo_o_texto}%", codigo_o_texto))
    else:
        # Si es texto, buscar en nombre
        cursor.execute("""
            SELECT codigo, numero_producto, nombre FROM productos 
            WHERE nombre LIKE ?
            ORDER BY nombre
            LIMIT 10
        """, (f"%{codigo_o_texto}%",))
    
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def mapear_codigo(codigo_bascula, producto_codigo):
    """Mapear un código de báscula a un producto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar que el producto existe
        cursor.execute("SELECT nombre FROM productos WHERE codigo = ?", (producto_codigo,))
        producto = cursor.fetchone()
        
        if not producto:
            print(f"Error: No existe producto con codigo '{producto_codigo}'")
            return False
        
        # Verificar que no existe mapeo duplicado
        cursor.execute("SELECT * FROM bascula_mapeo WHERE codigo_bascula = ?", (codigo_bascula,))
        if cursor.fetchone():
            print(f"Advertencia: Ya existe mapeo para {codigo_bascula}")
            return False
        
        # Insertar mapeo
        cursor.execute("""
            INSERT INTO bascula_mapeo (codigo_bascula, producto_codigo, nombre)
            VALUES (?, ?, ?)
        """, (codigo_bascula, producto_codigo, producto[0]))
        
        conn.commit()
        print(f"Mapeo creado: {codigo_bascula} -> {producto_codigo} ({producto[0]})")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def listar_mapeos():
    """Listar todos los mapeos existentes"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT codigo_bascula, producto_codigo, nombre FROM bascula_mapeo ORDER BY codigo_bascula")
    mapeos = cursor.fetchall()
    conn.close()
    
    if mapeos:
        print("\nMapeos existentes:")
        for m in mapeos:
            print(f"  {m[0]} -> {m[1]} ({m[2]})")
    else:
        print("No hay mapeos registrados")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso:")
        print("  python mapear_ticket.py buscar TEXTO     - Buscar producto por nombre/codigo")
        print("  python mapear_ticket.py mapear COD PROD   - Mapear codigo_bascula a producto")
        print("  python mapear_ticket.py listar            - Listar todos los mapeos")
        print("\nEjemplos:")
        print("  python mapear_ticket.py buscar MANTEQUILLA")
        print("  python mapear_ticket.py buscar 172")
        print("  python mapear_ticket.py mapear 208033201 172")
        print("  python mapear_ticket.py listar")
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "buscar" and len(sys.argv) >= 3:
        texto = " ".join(sys.argv[2:])
        resultados = buscar_producto(texto)
        
        if resultados:
            print(f"\nProductos encontrados para '{texto}':")
            for r in resultados:
                print(f"  codigo={r[0]:15} nombre={r[2]}")
        else:
            print(f"No se encontraron productos para '{texto}'")
    
    elif cmd == "mapear" and len(sys.argv) >= 4:
        codigo_bascula = sys.argv[2]
        producto_codigo = sys.argv[3]
        mapear_codigo(codigo_bascula, producto_codigo)
    
    elif cmd == "listar":
        listar_mapeos()
    
    else:
        print(f"Comando desconocido: {cmd}")
        sys.exit(1)
