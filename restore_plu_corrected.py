#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para recuperar PLU correctamente desde archivo iTegra
El PLU es el PRIMER número después de "PLUs"
"""

import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher

# Ruta a la base de datos
DB_PATH = "pos_cremeria.db"
ITEGRA_FILE = "2025_12_11.iTegra"

def parse_itegra_file(file_path):
    """
    Extraer PLU del archivo iTegra.
    El PLU es el PRIMER número después de "PLUs"
    
    Formato: "PLUs"[PLU]|[depto]|[tipo]|[nombre]||[codigo_barras]|...
    Ejemplo: "PLUs"1|1|0|JAM COR PIERNA||1|P|...
    Ejemplo: "PLUs"80374|1|0|ACEITE CAPULLO 845ML||7502223772588|N|...
    """
    plu_data = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Buscar líneas que contengan "PLUs"
                if '"PLUs"' in line:
                    # Extraer el PLU (primer número después de "PLUs")
                    match = re.search(r'"PLUs"(\d+)\|', line)
                    if match:
                        plu = int(match.group(1))
                        
                        # Extraer el nombre del producto (3er campo después de "PLUs")
                        # Formato: "PLUs"[plu]|[depto]|[tipo]|[nombre]||...
                        parts = line.split('|')
                        if len(parts) >= 4:
                            # El nombre es el 4to campo (índice 3)
                            # Pero primero hay que remover el "PLUs"[plu] del primer campo
                            nombre = parts[3].strip()
                            
                            # Extraer código de barras (después de ||)
                            codigo_match = re.search(r'\|\|(\d+)\|', line)
                            codigo_barras = codigo_match.group(1) if codigo_match else None
                            
                            if nombre and plu > 0:
                                plu_data[plu] = {
                                    'nombre': nombre,
                                    'codigo_barras': codigo_barras,
                                    'plu': plu
                                }
    
    except FileNotFoundError:
        print(f"[ERROR] Archivo no encontrado: {file_path}")
        return {}
    except Exception as e:
        print(f"[ERROR] Leyendo archivo: {e}")
        return {}
    
    return plu_data

def calculate_similarity(s1, s2):
    """Calcular similitud entre dos strings"""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def normalizar_texto(texto):
    """Normalizar texto para comparación"""
    if not texto:
        return ""
    texto = str(texto).lower()
    # Remover caracteres especiales
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    # Remover espacios extra
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def match_plu_to_products(plu_data):
    """
    Relacionar PLU del iTegra con productos en la base de datos.
    Usar similitud de nombres para encontrar coincidencias.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener todos los productos
        cursor.execute("SELECT codigo, nombre, numero_producto FROM productos ORDER BY codigo")
        productos = cursor.fetchall()
        
        print(f"\n[STATS] Base de datos tiene {len(productos)} productos")
        print(f"[STATS] iTegra tiene {len(plu_data)} registros PLU\n")
        
        matches = []
        no_matches = []
        
        for codigo, nombre, numero_producto_actual in productos:
            nombre_norm = normalizar_texto(nombre)
            best_match = None
            best_similarity = 0
            
            # Buscar el mejor PLU que coincida con este producto
            for plu, plu_info in plu_data.items():
                plu_nombre_norm = normalizar_texto(plu_info['nombre'])
                similarity = calculate_similarity(nombre_norm, plu_nombre_norm)
                
                # Aceptar coincidencias con similitud > 60%
                if similarity > best_similarity and similarity > 0.6:
                    best_similarity = similarity
                    best_match = plu
            
            if best_match:
                matches.append({
                    'codigo': codigo,
                    'nombre': nombre,
                    'plu': best_match,
                    'plu_nombre': plu_data[best_match]['nombre'],
                    'similarity': best_similarity
                })
            else:
                no_matches.append({
                    'codigo': codigo,
                    'nombre': nombre,
                    'plu_actual': numero_producto_actual
                })
        
        conn.close()
        return matches, no_matches
    
    except Exception as e:
        print(f"[ERROR] Consultando base de datos: {e}")
        conn.close()
        return [], []

def update_database(matches):
    """Actualizar la base de datos con los PLU encontrados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        updated_count = 0
        
        for match in matches:
            cursor.execute(
                "UPDATE productos SET numero_producto = ? WHERE codigo = ?",
                (match['plu'], match['codigo'])
            )
            updated_count += 1
        
        conn.close()
        print(f"[OK] {updated_count} productos actualizados en la base de datos")
        return updated_count
    
    except Exception as e:
        print(f"[ERROR] Actualizando base de datos: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def main():
    print("=" * 70)
    print("[RECUPERACION DE PLU DESDE ARCHIVO iTEGRA]")
    print("=" * 70)
    
    # 1. Extraer PLU del archivo iTegra
    print(f"\n[1] Leyendo archivo iTegra: {ITEGRA_FILE}")
    plu_data = parse_itegra_file(ITEGRA_FILE)
    
    if not plu_data:
        print("[ERROR] No se encontro ningun PLU en el archivo iTegra")
        return
    
    print(f"[OK] Se encontraron {len(plu_data)} registros PLU en el archivo iTegra")
    
    # Mostrar algunos ejemplos
    print("\n[EJEMPLOS] PLU encontrados:")
    for i, (plu, info) in enumerate(list(plu_data.items())[:5]):
        print(f"   PLU {plu}: {info['nombre']} (codigo barras: {info['codigo_barras']})")
    if len(plu_data) > 5:
        print(f"   ... y {len(plu_data) - 5} mas")
    
    # 2. Relacionar con productos en la base de datos
    print(f"\n[2] Relacionando PLU con productos en la base de datos...")
    matches, no_matches = match_plu_to_products(plu_data)
    
    print(f"\n[RESULTADOS] Correspondencia encontrada:")
    print(f"   [OK] Coincidencias encontradas: {len(matches)}")
    print(f"   [FALTA] Sin coincidencia: {len(no_matches)}")
    print(f"   [TASA] Exito: {len(matches) / (len(matches) + len(no_matches)) * 100:.1f}%")
    
    # Mostrar algunos matches
    if matches:
        print(f"\n[PRIMEROS 10] Matches encontrados:")
        for match in matches[:10]:
            print(f"   {match['nombre']:40} -> PLU {match['plu']:5} ({match['similarity']*100:5.1f}% similitud)")
    
    # Mostrar algunos no-matches
    if no_matches:
        print(f"\n[SIN PLU] Productos sin correspondencia ({len(no_matches)} total):")
        for product in no_matches[:10]:
            print(f"   {product['nombre']:40} (actual PLU: {product['plu_actual']})")
        if len(no_matches) > 10:
            print(f"   ... y {len(no_matches) - 10} mas")
    
    # 3. Actualizar base de datos
    print(f"\n[3] Actualizando base de datos...")
    updated = update_database(matches)
    
    # 4. Mostrar estadísticas finales
    print(f"\n{'=' * 70}")
    print(f"[LISTO] PROCESO COMPLETADO EXITOSAMENTE")
    print(f"{'=' * 70}")
    print(f"   [OK] Actualizados: {updated} productos")
    print(f"   [FALTA] Sin PLU: {len(no_matches)} productos")
    
    # Mostrar estadísticas de cobertura
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM productos WHERE numero_producto > 0")
    with_plu = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM productos")
    total = cursor.fetchone()[0]
    conn.close()
    
    coverage = with_plu / total * 100 if total > 0 else 0
    print(f"   [COBERTURA] PLU: {with_plu}/{total} ({coverage:.1f}%)")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    main()
