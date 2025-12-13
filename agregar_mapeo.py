#!/usr/bin/env python3
"""
Utilidad para mapear códigos de báscula a productos.

Uso:
  python agregar_mapeo.py <codigo_bascula> <nombre_producto>
  
  Ejemplos:
  python agregar_mapeo.py 2080332 "MANTEQUILLA EUGENIA 1KG"
  python agregar_mapeo.py 2000072 JOCOQUE
  
El script buscará automáticamente el producto en la base de datos
y creará el mapeo.
"""

import sqlite3
import sys

DB_PATH = "pos_cremeria.db"

def buscar_producto_por_nombre(nombre):
    """Buscar producto por nombre en la BD"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT codigo, numero_producto, nombre FROM productos
        WHERE nombre LIKE ?
        ORDER BY nombre
    """, (f"%{nombre}%",))
    
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def agregar_mapeo(codigo_bascula, producto_codigo, nombre_producto):
    """Agregar un nuevo mapeo a la tabla bascula_mapeo"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar que el producto existe
        cursor.execute("SELECT nombre FROM productos WHERE codigo = ?", (producto_codigo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"Error: No existe producto con codigo '{producto_codigo}' en la BD")
            return False
        
        # Verificar que no existe mapeo duplicado
        cursor.execute("SELECT * FROM bascula_mapeo WHERE codigo_bascula = ?", (codigo_bascula,))
        if cursor.fetchone():
            print(f"Error: Ya existe mapeo para codigo bascula '{codigo_bascula}'")
            return False
        
        # Insertar mapeo
        cursor.execute("""
            INSERT INTO bascula_mapeo (codigo_bascula, producto_codigo, nombre)
            VALUES (?, ?, ?)
        """, (codigo_bascula, producto_codigo, nombre_producto))
        
        conn.commit()
        print(f"Mapeo creado exitosamente:")
        print(f"  Codigo bascula: {codigo_bascula}")
        print(f"  Codigo producto: {producto_codigo}")
        print(f"  Nombre: {nombre_producto}")
        return True
        
    except Exception as e:
        print(f"Error al crear mapeo: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nOpciones:")
        print("  python agregar_mapeo.py buscar NOMBRE")
        print("    Buscar productos por nombre\n")
        print("  python agregar_mapeo.py mapear COD_BASCULA COD_PRODUCTO NOMBRE")
        print("    Crear mapeo entre codigo bascula y producto\n")
        print("Ejemplos:")
        print("  python agregar_mapeo.py buscar mantequilla")
        print("  python agregar_mapeo.py mapear 2080332 7501111021029 'MANTEQUILLA EUGENIA 1KG'")
        sys.exit(1)
    
    comando = sys.argv[1].lower()
    
    if comando == "buscar" and len(sys.argv) >= 3:
        nombre = " ".join(sys.argv[2:])
        print(f"\nBuscando productos con nombre: '{nombre}'\n")
        
        resultados = buscar_producto_por_nombre(nombre)
        
        if resultados:
            print("Productos encontrados:")
            print("-" * 80)
            print(f"{'Codigo':20} {'PLU':10} {'Nombre':50}")
            print("-" * 80)
            for r in resultados:
                plu = str(r[1]) if r[1] else "N/A"
                print(f"{r[0]:20} {plu:10} {r[2][:48]:50}")
            print("-" * 80)
            print(f"\nUsa 'python agregar_mapeo.py mapear <COD_BASCULA> <CODIGO> <NOMBRE>'")
        else:
            print(f"No se encontraron productos con nombre: '{nombre}'")
    
    elif comando == "mapear" and len(sys.argv) >= 5:
        codigo_bascula = sys.argv[2]
        producto_codigo = sys.argv[3]
        nombre_producto = " ".join(sys.argv[4:])
        
        agregar_mapeo(codigo_bascula, producto_codigo, nombre_producto)
    
    else:
        print(f"Comando desconocido o parametros faltantes: {comando}")
        sys.exit(1)
