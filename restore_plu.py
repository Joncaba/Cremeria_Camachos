#!/usr/bin/env python3
"""
Script para restaurar PLU de productos desde archivo iTegra
"""
import sqlite3
import re
from pathlib import Path

DB_PATH = "pos_cremeria.db"
ITEGRA_FILE = "2025_12_11.iTegra"

def parse_itegra_file(filepath):
    """Extrae PLU y nombres de productos del archivo iTegra"""
    plu_dict = {}
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Buscar líneas que contengan PLU
            if '"PLUs"' in line:
                # Formato: "PLUs"[índice]|[depto]|[tipo]|[nombre]||[plu]|...
                # Extraer la parte después de "PLUs"
                if '"PLUs"' in line:
                    # Buscar el patrón: "PLUs"número|...|nombre||plu
                    match = re.search(r'"PLUs"(\d+)\|(\d+)\|(\d+)\|([^|]+)\|\|(\d+)', line)
                    if match:
                        try:
                            idx = int(match.group(1))
                            nombre = match.group(4).strip()
                            plu = int(match.group(5))
                            
                            # Algunos PLU pueden ser códigos de barras largos, usar solo si es número corto
                            if nombre and plu > 0 and plu < 100000:  # PLU típicamente < 100000
                                plu_dict[plu] = nombre
                        except (ValueError, IndexError):
                            pass
    
    return plu_dict

def match_product_to_plu(nombre_itegra, producto_db):
    """
    Intenta hacer match entre un producto de iTunes y la BD
    Retorna el PLU si encuentra coincidencia
    """
    # Normalizar nombres
    nombre_itegra_norm = nombre_itegra.upper().strip()
    nombre_db_norm = producto_db.upper().strip()
    
    # Match exacto
    if nombre_itegra_norm == nombre_db_norm:
        return True
    
    # Match parcial (al menos 80% de similitud en palabras)
    words_itegra = set(nombre_itegra_norm.split())
    words_db = set(nombre_db_norm.split())
    
    if words_itegra and words_db:
        intersection = len(words_itegra & words_db)
        max_words = max(len(words_itegra), len(words_db))
        similarity = intersection / max_words if max_words > 0 else 0
        
        if similarity >= 0.6:  # Al menos 60% de palabras coinciden
            return True
    
    return False

def restore_plu():
    """Restaura PLU de productos desde archivo iTegra"""
    
    # 1. Parsear archivo iTegra
    print("📂 Leyendo archivo iTegra...")
    itegra_path = Path(ITEGRA_FILE)
    
    if not itegra_path.exists():
        print(f"❌ Archivo no encontrado: {ITEGRA_FILE}")
        return False
    
    plu_data = parse_itegra_file(ITEGRA_FILE)
    print(f"✅ Se encontraron {len(plu_data)} PLU en el archivo iTegra\n")
    
    if not plu_data:
        print("❌ No se pudieron extraer PLU del archivo")
        return False
    
    # 2. Conectar a la base de datos
    print("🔄 Conectando a la base de datos...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 3. Obtener lista de productos
        cursor.execute("SELECT codigo, nombre FROM productos ORDER BY nombre")
        productos_db = cursor.fetchall()
        
        print(f"📦 Se encontraron {len(productos_db)} productos en la BD\n")
        
        # 4. Intentar hacer match
        updated = 0
        not_matched = []
        
        print("🔍 Buscando coincidencias...\n")
        
        for plu, nombre_itegra in sorted(plu_data.items()):
            matched = False
            
            for codigo, nombre_db in productos_db:
                if match_product_to_plu(nombre_itegra, nombre_db):
                    # Actualizar el PLU
                    cursor.execute(
                        "UPDATE productos SET numero_producto = ? WHERE codigo = ?",
                        (plu, codigo)
                    )
                    print(f"✅ PLU {plu}: {nombre_db[:40]}")
                    updated += 1
                    matched = True
                    break
            
            if not matched:
                not_matched.append((plu, nombre_itegra))
        
        # 5. Mostrar resultados
        print(f"\n{'='*60}")
        print(f"✅ RESULTADOS:")
        print(f"   • Productos actualizados: {updated}")
        print(f"   • Productos sin coincidencia: {len(not_matched)}")
        print(f"{'='*60}\n")
        
        # Mostrar productos sin match
        if not_matched:
            print("⚠️  PRODUCTOS SIN COINCIDENCIA EN LA BD:")
            for plu, nombre in not_matched[:20]:  # Mostrar primeros 20
                print(f"   PLU {plu}: {nombre[:40]}")
            
            if len(not_matched) > 20:
                print(f"   ... y {len(not_matched) - 20} más")
        
        # Guardar cambios
        if updated > 0:
            conn.commit()
            print(f"\n✅ Se guardaron {updated} actualizaciones en la base de datos")
            return True
        else:
            print("\n⚠️  No se realizaron actualizaciones")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔢 RESTAURADOR DE PLU - iTegra")
    print("="*60 + "\n")
    
    success = restore_plu()
    
    if success:
        print("\n✅ Proceso completado exitosamente")
    else:
        print("\n❌ Proceso completado con errores")
