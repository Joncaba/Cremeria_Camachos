#!/usr/bin/env python3
"""
Script de Diagnóstico: Verificar si un código/ticket será encontrado en ventas.py

Uso:
    python diagnosticar_busqueda.py 172
    python diagnosticar_busqueda.py 7501111021029
    python diagnosticar_busqueda.py 2080332010005
"""

import sqlite3
import sys

DB_PATH = "pos_cremeria.db"

def parsear_bascula(codigo_completo):
    """Parsear código de báscula (13 dígitos)"""
    if len(codigo_completo) != 13:
        return None
    
    codigo = codigo_completo[:9]
    peso_decagramos = int(codigo_completo[9:12])
    checksum = codigo_completo[12]
    
    return {
        'codigo_bascula': codigo,
        'peso_gramos': peso_decagramos * 10,
        'peso_kg': peso_decagramos / 100,
        'checksum': checksum
    }

def buscar_producto_simulado(codigo):
    """Simular la búsqueda de obtener_producto_por_codigo()"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    codigo_str = str(codigo).strip()
    resultados = {
        'entrada': codigo_str,
        'estrategia_exitosa': None,
        'producto': None,
        'intentos': []
    }
    
    # ESTRATEGIA 1: Búsqueda exacta por código
    cursor.execute("SELECT codigo, numero_producto, nombre FROM productos WHERE codigo = ?", (codigo_str,))
    resultado = cursor.fetchone()
    resultados['intentos'].append(f"1. Busqueda exacta: WHERE codigo = '{codigo_str}': {'[ENCONTRADO]' if resultado else '[No encontrado]'}")
    if resultado:
        resultados['estrategia_exitosa'] = 'Búsqueda exacta'
        resultados['producto'] = resultado
        conn.close()
        return resultados
    
    # ESTRATEGIA 2: Si es un número, buscar por numero_producto
    try:
        codigo_int = int(codigo_str)
        cursor.execute("SELECT codigo, numero_producto, nombre FROM productos WHERE numero_producto = ?", (codigo_int,))
        resultado = cursor.fetchone()
        resultados['intentos'].append(f"2. Busqueda por PLU: WHERE numero_producto = {codigo_int}: {'[ENCONTRADO]' if resultado else '[No encontrado]'}")
        if resultado:
            resultados['estrategia_exitosa'] = f'Búsqueda por PLU ({codigo_int})'
            resultados['producto'] = resultado
            conn.close()
            return resultados
    except ValueError:
        resultados['intentos'].append(f"2. Busqueda por PLU: No es numero entero")
    
    # ESTRATEGIA 3: Si son 9 dígitos (código de báscula), extraer PLU
    if len(codigo_str) == 9 and codigo_str.isdigit():
        resultados['intentos'].append(f"\n3. Deteccion de codigo de bascula (9 digitos):")
        
        ultimos_5 = codigo_str[-5:]
        ultimos_6 = codigo_str[-6:]
        ultimos_7 = codigo_str[-7:]
        
        for intento_str, nombre_intento in [
            (ultimos_7, f"ultimos 7 digitos ({ultimos_7})"),
            (ultimos_6, f"ultimos 6 digitos ({ultimos_6})"),
            (ultimos_5, f"ultimos 5 digitos ({ultimos_5})")
        ]:
            try:
                plu = int(intento_str)
                cursor.execute("SELECT codigo, numero_producto, nombre FROM productos WHERE numero_producto = ?", (plu,))
                resultado = cursor.fetchone()
                resultados['intentos'].append(f"      Intento PLU={plu} ({nombre_intento}): {'[ENCONTRADO]' if resultado else '[No encontrado]'}")
                if resultado:
                    resultados['estrategia_exitosa'] = f'Extraccion de bascula (PLU={plu})'
                    resultados['producto'] = resultado
                    conn.close()
                    return resultados
            except ValueError:
                pass
        
        # ESTRATEGIA 3B: Búsqueda LIKE para códigos de báscula
        resultados['intentos'].append(f"\n3B. Busqueda LIKE (bascula): codigo LIKE '{codigo_str}%':")
        cursor.execute("SELECT codigo, numero_producto, nombre FROM productos WHERE codigo LIKE ?", (f"{codigo_str}%",))
        resultado = cursor.fetchone()
        resultados['intentos'].append(f"      Resultado: {'[ENCONTRADO]' if resultado else '[No encontrado]'}")
        if resultado:
            resultados['estrategia_exitosa'] = f'Busqueda LIKE (primeros 9 digitos)'
            resultados['producto'] = resultado
            conn.close()
            return resultados
    
    # ESTRATEGIA 4: Búsqueda parcial
    if len(codigo_str) > 6:
        ultimos_6 = codigo_str[-6:]
        cursor.execute("SELECT codigo, numero_producto, nombre FROM productos WHERE codigo LIKE ?", (f"%{ultimos_6}",))
        resultado = cursor.fetchone()
        resultados['intentos'].append(f"\n4. Busqueda parcial: WHERE codigo LIKE '%{ultimos_6}: {'[ENCONTRADO]' if resultado else '[No encontrado]'}")
        if resultado:
            resultados['estrategia_exitosa'] = f'Búsqueda parcial (últimos 6 dígitos)'
            resultados['producto'] = resultado
            conn.close()
            return resultados
    
    conn.close()
    return resultados

def main():
    if len(sys.argv) < 2:
        print("Uso: python diagnosticar_busqueda.py <codigo>")
        print("\nEjemplos:")
        print("  python diagnosticar_busqueda.py 172")
        print("  python diagnosticar_busqueda.py 7501111021029")
        print("  python diagnosticar_busqueda.py 2080332010005")
        sys.exit(1)
    
    codigo_ingresado = sys.argv[1]
    
    print("="*80)
    print(f"DIAGNÓSTICO DE BÚSQUEDA: {codigo_ingresado}")
    print("="*80)
    print()
    
    # Verificar si es ticket de báscula
    bascula_info = parsear_bascula(codigo_ingresado)
    if bascula_info:
        print("TIPO DE ENTRADA: Ticket de Bascula (13 digitos)")
        print(f"   Codigo de bascula: {bascula_info['codigo_bascula']}")
        print(f"   Peso: {bascula_info['peso_gramos']}g ({bascula_info['peso_kg']}kg)")
        print(f"   Checksum: {bascula_info['checksum']}")
        print()
        print("Ahora buscando código de báscula...")
        print()
        resultados = buscar_producto_simulado(bascula_info['codigo_bascula'])
    else:
        print("TIPO DE ENTRADA: Codigo Simple")
        print()
        resultados = buscar_producto_simulado(codigo_ingresado)
    
    print("\nPROCESO DE BUSQUEDA:")
    print("-" * 80)
    for intento in resultados['intentos']:
        print(intento)
    
    print()
    print("RESULTADO FINAL:")
    print("-" * 80)
    
    if resultados['producto']:
        codigo, numero_producto, nombre = resultados['producto']
        print(f"EXITO: PRODUCTO ENCONTRADO")
        print(f"   Estrategia: {resultados['estrategia_exitosa']}")
        print(f"   Codigo: {codigo}")
        print(f"   PLU: {numero_producto}")
        print(f"   Nombre: {nombre}")
    else:
        print(f"ERROR: PRODUCTO NO ENCONTRADO")
        print()
        print("RECOMENDACIONES:")
        print("1. Verifica que el producto exista en la BD")
        print("2. Asegúrate que el código sea correcto")
        print("3. Para códigos de báscula, verifica que el PLU esté asignado")
        print()
        print("Opciones:")
        print("  a) Importar el producto: python sincronizar_plu_a_productos.py")
        print("  b) Verificar en BD: SELECT * FROM productos WHERE nombre LIKE '%...%'")
        print("  c) Asignar barcode: python agregar_codigo_barras.py <plu> <barcode>")

if __name__ == "__main__":
    main()
