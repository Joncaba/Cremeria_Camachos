#!/usr/bin/env python3
"""
Script de prueba para verificar que ventas.py puede decodificar
códigos de báscula de 13 dígitos correctamente.

Formato de código: XXXXXXXYYZZZ
  - XXXXXXX (7 dígitos): código de producto en báscula
  - YY (2 dígitos): cantidad
  - ZZZZ (4 dígitos): control/descarte
"""

import sqlite3

DB_PATH = "pos_cremeria.db"

def obtener_producto_por_codigo(codigo):
    """Simular la función de ventas.py"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if not codigo:
        return None
    
    codigo_str = str(codigo).strip()
    
    # ESTRATEGIA 0: Si el código tiene 13 dígitos (ticket de báscula completo)
    if len(codigo_str) == 13 and codigo_str.isdigit():
        codigo_bascula = codigo_str[:7]
        
        # Buscar en tabla de mapeo
        cursor.execute("""
            SELECT p.* FROM productos p
            JOIN bascula_mapeo bm ON p.codigo = bm.producto_codigo
            WHERE bm.codigo_bascula = ?
        """, (codigo_bascula,))
        resultado = cursor.fetchone()
        if resultado:
            conn.close()
            return resultado
        
        # Si no existe mapeo, intentar búsqueda directa
        cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo_bascula,))
        resultado = cursor.fetchone()
        if resultado:
            conn.close()
            return resultado
        
        # Intentar búsqueda LIKE
        cursor.execute("SELECT * FROM productos WHERE codigo LIKE ?", (f"{codigo_bascula}%",))
        resultado = cursor.fetchone()
        if resultado:
            conn.close()
            return resultado
    
    # ESTRATEGIA 1: Búsqueda exacta
    cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo_str,))
    resultado = cursor.fetchone()
    if resultado:
        conn.close()
        return resultado
    
    conn.close()
    return None

# Pruebas con códigos del ticket
print("=" * 70)
print("PRUEBA DE DECODIFICACION DE TICKETS DE BASCULA")
print("=" * 70)
print()

test_casos = [
    {
        'codigo': '2080332010005',
        'esperado': 'MANTEQUILLA EUGENIA 1KG',
        'cantidad': 1,
    },
    {
        'codigo': '2000072010000',
        'esperado': 'JOCOQUE',
        'cantidad': 1,
    },
    {
        'codigo': '2000140010000',
        'esperado': 'Huevo Blanco',
        'cantidad': 1,
    },
]

print("Códigos a procesar:")
print()

todos_ok = True
for test in test_casos:
    codigo = test['codigo']
    esperado = test['esperado']
    cantidad = int(codigo[7:9])
    
    # Extraer información
    codigo_bascula = codigo[:7]
    cantidad_str = codigo[7:9]
    control = codigo[9:]
    
    print(f"Código: {codigo}")
    print(f"  - Código báscula: {codigo_bascula}")
    print(f"  - Cantidad: {cantidad_str} ({cantidad} unidades)")
    print(f"  - Control: {control}")
    
    # Buscar producto
    producto = obtener_producto_por_codigo(codigo)
    if producto:
        print(f"  - Encontrado: {producto['nombre']}")
        
        # Verificar
        if esperado.upper() in producto['nombre'].upper():
            print(f"  - Status: OK")
        else:
            print(f"  - Status: ERROR (esperado {esperado})")
            todos_ok = False
    else:
        print(f"  - Encontrado: NO ENCONTRADO")
        print(f"  - Status: ERROR")
        todos_ok = False
    
    print()

print("=" * 70)
if todos_ok:
    print("RESULTADO: TODAS LAS PRUEBAS PASADAS")
else:
    print("RESULTADO: ALGUNAS PRUEBAS FALLARON")
print("=" * 70)
