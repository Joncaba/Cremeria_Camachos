#!/usr/bin/env python3
"""
Crear mapeo de códigos de báscula a productos.

Los códigos que la báscula escanea (9 dígitos) deben mapearse a los productos
que tienes en la tabla 'productos'.

Este script crea una tabla auxiliar: bascula_mapeo
que vincula código de báscula con producto_codigo
"""

import sqlite3

DB_PATH = "pos_cremeria.db"

def crear_tabla_mapeo():
    """Crear tabla auxiliar de mapeo báscula -> producto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bascula_mapeo (
                codigo_bascula TEXT PRIMARY KEY,
                producto_codigo TEXT NOT NULL,
                nombre TEXT,
                FOREIGN KEY (producto_codigo) REFERENCES productos(codigo)
            )
        ''')
        
        conn.commit()
        print("✓ Tabla bascula_mapeo creada")
        
    except Exception as e:
        print(f"✗ Error creando tabla: {e}")
        conn.rollback()
    finally:
        conn.close()

def agregar_mapeo(codigo_bascula, producto_codigo, nombre=None):
    """Agregar un mapeo código de báscula -> producto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar que el producto existe
        cursor.execute("SELECT nombre FROM productos WHERE codigo = ?", (producto_codigo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"✗ Producto con codigo '{producto_codigo}' no existe")
            return False
        
        nombre_producto = resultado[0] if not nombre else nombre
        
        # Insertar o actualizar mapeo
        cursor.execute('''
            INSERT OR REPLACE INTO bascula_mapeo 
            (codigo_bascula, producto_codigo, nombre)
            VALUES (?, ?, ?)
        ''', (codigo_bascula, producto_codigo, nombre_producto))
        
        conn.commit()
        print(f"✓ Mapeo agregado: {codigo_bascula} -> {producto_codigo} ({nombre_producto})")
        return True
        
    except Exception as e:
        print(f"✗ Error al agregar mapeo: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def listar_mapeos():
    """Listar todos los mapeos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT codigo_bascula, producto_codigo, nombre FROM bascula_mapeo ORDER BY codigo_bascula")
        resultados = cursor.fetchall()
        
        if resultados:
            print("\nMAPEOS REGISTRADOS:")
            print("-" * 80)
            for codigo_bascula, producto_codigo, nombre in resultados:
                print(f"  {codigo_bascula:12} → {producto_codigo:15} ({nombre})")
        else:
            print("\nNo hay mapeos registrados")
            
    except Exception as e:
        print(f"✗ Error al listar mapeos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    # Crear tabla
    crear_tabla_mapeo()
    
    # Aquí debes agregar los mapeos reales de tu báscula
    # Uso: agregar_mapeo(codigo_bascula, producto_codigo, nombre_opcional)
    
    # Ejemplos (actualizar con tus datos reales):
    # agregar_mapeo("208033201", "140", "HUEVO BLANCO")
    # agregar_mapeo("200007200", "2", "JAM PIERNA DELEITE")
    # agregar_mapeo("200014001", "3", "JAM PIERN ANDALUCIA")
    
    # Ver mapeos
    listar_mapeos()
    
    print("\n" + "="*80)
    print("INSTRUCCIONES DE USO:")
    print("="*80)
    print()
    print("Para agregar un mapeo, ejecuta:")
    print("  python crear_mapeo_bascula.py <codigo_bascula> <producto_codigo>")
    print()
    print("Ejemplo:")
    print("  python crear_mapeo_bascula.py 208033201 140")
    print()
    print("Nota: Necesitas saber qué código de báscula corresponde a cada producto")
    print("      Pregunta al proveedor de la báscula o usa el debug del POS")
