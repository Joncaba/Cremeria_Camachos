import sqlite3
import pandas as pd

DB_PATH = "pos_cremeria.db"

def setup_stock_minimo():
    """Establecer stock mínimo de 20 para todos los productos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Leer todos los productos
        productos_df = pd.read_sql_query("SELECT codigo, nombre, tipo_venta FROM productos", conn)
        
        print(f"Total productos a procesar: {len(productos_df)}")
        print()
        
        actualizado = 0
        errores = 0
        
        for _, row in productos_df.iterrows():
            try:
                codigo = row['codigo']
                tipo_venta = row['tipo_venta']
                
                if tipo_venta in ['granel', 'kg']:
                    # Para productos a granel: stock_minimo_kg = 20
                    cursor.execute(
                        "UPDATE productos SET stock_minimo_kg = ? WHERE codigo = ?",
                        (20.0, codigo)
                    )
                    print(f"✓ {codigo:5} | {row['nombre'][:40]:40} | 🎯 Stock Mín: 20.00 kg")
                else:
                    # Para productos por unidad: stock_minimo = 20
                    cursor.execute(
                        "UPDATE productos SET stock_minimo = ? WHERE codigo = ?",
                        (20, codigo)
                    )
                    print(f"✓ {codigo:5} | {row['nombre'][:40]:40} | 🎯 Stock Mín: 20 unid.")
                
                actualizado += 1
                    
            except Exception as e:
                errores += 1
                print(f"✗ Error actualizando {row['codigo']}: {e}")
        
        conn.commit()
        
        print()
        print("=" * 80)
        print(f"✅ PROCESO COMPLETADO")
        print(f"   Productos actualizados: {actualizado}")
        print(f"   Errores encontrados: {errores}")
        print("=" * 80)
        print()
        
        # Verificación: mostrar algunos ejemplos
        print("📊 EJEMPLOS DE CONFIGURACIÓN:")
        print()
        
        verificacion_df = pd.read_sql_query("""
            SELECT 
                codigo,
                nombre,
                tipo_venta,
                stock_minimo,
                stock_minimo_kg,
                CASE 
                    WHEN tipo_venta IN ('granel', 'kg') THEN CONCAT(stock_minimo_kg, ' kg')
                    ELSE CONCAT(stock_minimo, ' unid.')
                END as stock_minimo_display
            FROM productos
            LIMIT 15
        """, conn)
        
        for _, row in verificacion_df.iterrows():
            tipo = "⚖️" if row['tipo_venta'] in ['granel', 'kg'] else "🏷️"
            print(f"  {tipo} {row['codigo']:5} | {row['nombre'][:30]:30} | Stock Mín: {row['stock_minimo_display']:15}")
        
        print()
        
        # Estadísticas finales
        stats_unidad = pd.read_sql_query("""
            SELECT COUNT(*) as total
            FROM productos
            WHERE tipo_venta NOT IN ('granel', 'kg')
        """, conn)
        
        stats_granel = pd.read_sql_query("""
            SELECT COUNT(*) as total
            FROM productos
            WHERE tipo_venta IN ('granel', 'kg')
        """, conn)
        
        print("📈 ESTADÍSTICAS:")
        print(f"   Productos por unidad (stock_minimo = 20 unid.): {stats_unidad.iloc[0]['total']}")
        print(f"   Productos a granel (stock_minimo_kg = 20 kg): {stats_granel.iloc[0]['total']}")
        print()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n🔧 CONFIGURADOR DE STOCK MÍNIMO")
    print("=" * 80)
    print("Este script va a:")
    print("  • Establecer stock_minimo = 20 unidades para productos por unidad")
    print("  • Establecer stock_minimo_kg = 20 kg para productos a granel")
    print("=" * 80)
    print()
    
    setup_stock_minimo()
