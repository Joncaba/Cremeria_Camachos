#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir la importación de productos desde archivo iTegra
Formato correcto: PLU, Código, Nombre, Tipo, Precio
"""

import sqlite3
import sys
import os

def parsear_linea_itegra(linea):
    """
    Parsea una línea del archivo iTegra
    Formato: "PLUs"[PLU]|1|0|[NOMBRE]||[CODIGO]|[TIPO]|0|[PRECIO]|...
    """
    if not linea.startswith('"PLUs"'):
        return None
    
    # Remover "PLUs" y parsear campos
    linea = linea.replace('"PLUs"', '', 1)
    campos = linea.split('|')
    
    if len(campos) < 10:
        return None
    
    try:
        plu = int(campos[0])  # Campo 0: PLU (numero_producto)
        nombre = campos[3].strip()  # Campo 3: Nombre
        codigo_str = campos[5].strip()  # Campo 5: Código
        tipo = campos[6].strip()  # Campo 6: Tipo (P=peso, N=número)
        precio = float(campos[8])  # Campo 8: Precio
        
        # Si el código está vacío, usar el PLU como código
        if not codigo_str:
            codigo_str = str(plu)
        
        # Determinar tipo_venta
        tipo_venta = 'kg' if tipo == 'P' else 'unidad'
        
        return {
            'numero_producto': plu,
            'codigo': codigo_str,
            'nombre': nombre,
            'tipo_venta': tipo_venta,
            'precio': precio
        }
    except (ValueError, IndexError) as e:
        print(f"Error parseando línea: {linea[:50]}... - {e}")
        return None

def corregir_base_datos(archivo_itegra, db_path='pos_cremeria.db'):
    """
    Actualiza la base de datos con los datos correctos del archivo iTegra
    """
    if not os.path.exists(archivo_itegra):
        print(f"❌ Error: No se encuentra el archivo {archivo_itegra}")
        return False
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encuentra la base de datos {db_path}")
        return False
    
    print("📂 Leyendo archivo iTegra...")
    productos_parseados = []
    
    with open(archivo_itegra, 'r', encoding='latin-1') as f:
        for linea in f:
            producto = parsear_linea_itegra(linea.strip())
            if producto:
                productos_parseados.append(producto)
    
    print(f"✅ Se encontraron {len(productos_parseados)} productos en el archivo")
    
    # Conectar a la base de datos
    print("\n🔄 Actualizando base de datos...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    actualizados = 0
    no_encontrados = 0
    errores = 0
    
    for prod in productos_parseados:
        try:
            # Buscar el producto por nombre (más confiable que por código incorrecto)
            cursor.execute("""
                SELECT codigo, numero_producto, nombre, precio_normal, tipo_venta 
                FROM productos 
                WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))
            """, (prod['nombre'],))
            
            resultado = cursor.fetchone()
            
            if resultado:
                codigo_actual, plu_actual, nombre_actual, precio_actual, tipo_actual = resultado
                
                # Actualizar con los valores correctos
                cursor.execute("""
                    UPDATE productos 
                    SET codigo = ?,
                        numero_producto = ?,
                        precio_normal = ?,
                        tipo_venta = ?
                    WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))
                """, (
                    prod['codigo'],
                    prod['numero_producto'],
                    prod['precio'],
                    prod['tipo_venta'],
                    prod['nombre']
                ))
                
                actualizados += 1
                
                # Mostrar cambios significativos
                if str(codigo_actual) != str(prod['codigo']) or plu_actual != prod['numero_producto']:
                    print(f"  ✏️  {prod['nombre'][:40]}")
                    if str(codigo_actual) != str(prod['codigo']):
                        print(f"      Código: {codigo_actual} → {prod['codigo']}")
                    if plu_actual != prod['numero_producto']:
                        print(f"      PLU: {plu_actual} → {prod['numero_producto']}")
            else:
                # Producto no existe, insertarlo
                cursor.execute("""
                    INSERT INTO productos (
                        codigo, numero_producto, nombre, precio_normal, tipo_venta,
                        categoria, stock, stock_kg, activo
                    ) VALUES (?, ?, ?, ?, ?, 'GENERAL', 0, 0, 1)
                """, (
                    prod['codigo'],
                    prod['numero_producto'],
                    prod['nombre'],
                    prod['precio'],
                    prod['tipo_venta']
                ))
                no_encontrados += 1
                print(f"  ➕ Insertado: {prod['nombre'][:40]} (PLU: {prod['numero_producto']})")
        
        except Exception as e:
            errores += 1
            print(f"  ❌ Error con {prod['nombre'][:40]}: {e}")
    
    # Guardar cambios
    conn.commit()
    conn.close()
    
    print(f"\n✅ Proceso completado:")
    print(f"   - Actualizados: {actualizados}")
    print(f"   - Insertados: {no_encontrados}")
    print(f"   - Errores: {errores}")
    
    return True

def mostrar_ejemplos_correccion(archivo_itegra, db_path='pos_cremeria.db'):
    """
    Muestra ejemplos de correcciones que se realizarán
    """
    print("🔍 Verificando ejemplos específicos...\n")
    
    # Ejemplos del usuario
    ejemplos = [
        ("CREMA CAMPBELL S CHAMPI�ON", 80236, "7501011312678"),
        ("JAM COR PIERNA", 1, "1")
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for nombre, plu_correcto, codigo_correcto in ejemplos:
        cursor.execute("""
            SELECT codigo, numero_producto, nombre, precio_normal 
            FROM productos 
            WHERE nombre LIKE ?
        """, (f"%{nombre[:20]}%",))
        
        resultado = cursor.fetchone()
        
        if resultado:
            codigo_actual, plu_actual, nombre_actual, precio_actual = resultado
            print(f"📦 {nombre_actual}")
            print(f"   Código actual: {codigo_actual} → Correcto: {codigo_correcto}")
            print(f"   PLU actual: {plu_actual} → Correcto: {plu_correcto}")
            print()
        else:
            print(f"⚠️  No se encontró producto con nombre similar a: {nombre}\n")
    
    conn.close()

if __name__ == "__main__":
    archivo = r"c:\Users\jo_na\Documents\2025_12_11.iTegra"
    db = r"pos_cremeria.db"
    
    print("=" * 60)
    print("🔧 CORRECCIÓN DE IMPORTACIÓN iTegra")
    print("=" * 60)
    
    # Mostrar estado actual
    mostrar_ejemplos_correccion(archivo, db)
    
    # Preguntar confirmación
    print("\n⚠️  Este script actualizará:")
    print("   - Códigos de productos")
    print("   - Números PLU")
    print("   - Precios")
    print("   - Tipos de venta (kg/unidad)")
    print("\n¿Desea continuar? (s/n): ", end="")
    
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        print("\n" + "=" * 60)
        corregir_base_datos(archivo, db)
        print("=" * 60)
    else:
        print("\n❌ Operación cancelada")
