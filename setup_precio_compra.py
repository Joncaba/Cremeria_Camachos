import sqlite3
import pandas as pd

DB_PATH = "pos_cremeria.db"

def setup_precio_compra():
    """Configurar precio_compra como precio_normal con 8% de descuento"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Leer todos los productos
        productos_df = pd.read_sql_query("SELECT codigo, nombre, precio_normal FROM productos", conn)
        
        print(f"Total productos a procesar: {len(productos_df)}")
        print()
        
        # Calcular precio_compra como precio_normal - 8%
        productos_df['precio_compra'] = productos_df['precio_normal'] * 0.92  # Reducción del 8%
        
        # Actualizar cada producto
        actualizado = 0
        errores = 0
        
        for _, row in productos_df.iterrows():
            try:
                precio_compra = round(row['precio_compra'], 2)
                cursor.execute(
                    "UPDATE productos SET precio_compra = ? WHERE codigo = ?",
                    (precio_compra, row['codigo'])
                )
                actualizado += 1
                
                # Mostrar progreso cada 50 productos
                if actualizado % 50 == 0:
                    print(f"✓ {actualizado} productos actualizados...")
                    
            except Exception as e:
                errores += 1
                print(f"✗ Error actualizando {row['codigo']} ({row['nombre']}): {e}")
        
        conn.commit()
        
        print()
        print("=" * 60)
        print(f"✅ PROCESO COMPLETADO")
        print(f"   Productos actualizados: {actualizado}")
        print(f"   Errores encontrados: {errores}")
        print("=" * 60)
        print()
        
        # Verificación: mostrar algunos ejemplos
        print("📊 EJEMPLOS DE CONVERSIÓN:")
        print()
        ejemplos = productos_df.head(10)
        for _, row in ejemplos.iterrows():
            precio_compra = round(row['precio_compra'], 2)
            descuento = round(row['precio_normal'] - precio_compra, 2)
            print(f"  {row['codigo']:5} | {row['nombre'][:30]:30} | Normal: ${row['precio_normal']:8.2f} → Compra: ${precio_compra:8.2f} (Desc: ${descuento:.2f})")
        
        print()
        
        # Estadísticas finales
        stats_df = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total,
                MIN(precio_compra) as minimo,
                MAX(precio_compra) as maximo,
                AVG(precio_compra) as promedio
            FROM productos
            WHERE precio_compra > 0
        """, conn)
        
        print("📈 ESTADÍSTICAS DE PRECIOS:")
        stats = stats_df.iloc[0]
        print(f"   Total con precio: {int(stats['total'])}")
        print(f"   Precio mínimo: ${stats['minimo']:.2f}")
        print(f"   Precio máximo: ${stats['maximo']:.2f}")
        print(f"   Precio promedio: ${stats['promedio']:.2f}")
        print()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n🔧 CONFIGURADOR DE PRECIOS DE COMPRA")
    print("=" * 60)
    print("Este script va a:")
    print("  • Calcular precio_compra = precio_normal × 0.92 (8% descuento)")
    print("  • Actualizar todos los productos en la BD")
    print("=" * 60)
    print()
    
    # Ejecutar directamente sin confirmación
    setup_precio_compra()
