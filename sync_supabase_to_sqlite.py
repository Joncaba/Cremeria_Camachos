"""
Script de sincronización inversa: Supabase → SQLite
Trae cambios desde Supabase (ej: precios editados en la web) a la aplicación local
"""
import sqlite3
from datetime import datetime
import streamlit as st

try:
    from supabase_client import get_db as get_supabase_db
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

def sincronizar_productos_desde_supabase(sqlite_path="pos_cremeria.db", verbose=False):
    """
    Sincronizar cambios de productos desde Supabase a SQLite
    
    Esto permite que cambios hechos en Supabase (ej: cambiar precio)
    se reflejen automáticamente en el inventario local
    
    Args:
        sqlite_path: Ruta a la base de datos SQLite
        verbose: Si True, imprime detalles de la sincronización
    
    Returns:
        dict: {'success': int, 'failed': int, 'updated': int}
    """
    
    if not SUPABASE_AVAILABLE:
        return {'success': 0, 'failed': 0, 'updated': 0, 'error': 'Supabase no disponible'}
    
    try:
        # Conectar a Supabase
        supabase_db = get_supabase_db()
        
        # Obtener todos los productos de Supabase
        result = supabase_db.client.table('productos').select('*').execute()
        
        if not result.data:
            return {'success': 0, 'failed': 0, 'updated': 0, 'error': 'No hay productos en Supabase'}
        
        # Conectar a SQLite
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        success = 0
        updated = 0
        failed = 0
        
        for producto_supabase in result.data:
            try:
                codigo = producto_supabase.get('codigo')
                
                # Obtener producto actual de SQLite
                cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
                producto_sqlite = cursor.fetchone()
                
                if not producto_sqlite:
                    if verbose:
                        print(f"⚠️  Producto {codigo} no existe en SQLite, creando...")
                    # Insertar nuevo producto
                    cursor.execute('''
                        INSERT INTO productos 
                        (codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, 
                         precio_mayoreo_2, precio_mayoreo_3, stock, tipo_venta, 
                         precio_por_kg, peso_unitario, stock_kg, stock_minimo, 
                         stock_minimo_kg, stock_maximo, stock_maximo_kg, categoria, numero_producto)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        producto_supabase.get('codigo'),
                        producto_supabase.get('nombre'),
                        producto_supabase.get('precio_compra', 0),
                        producto_supabase.get('precio_normal', 0),
                        producto_supabase.get('precio_mayoreo_1', 0),
                        producto_supabase.get('precio_mayoreo_2'),
                        producto_supabase.get('precio_mayoreo_3'),
                        producto_supabase.get('stock', 0),
                        producto_supabase.get('tipo_venta', 'unidad'),
                        producto_supabase.get('precio_por_kg'),
                        producto_supabase.get('peso_unitario'),
                        producto_supabase.get('stock_kg'),
                        producto_supabase.get('stock_minimo', 10),
                        producto_supabase.get('stock_minimo_kg'),
                        producto_supabase.get('stock_maximo'),
                        producto_supabase.get('stock_maximo_kg'),
                        producto_supabase.get('categoria', 'cremeria'),
                        producto_supabase.get('numero_producto')
                    ))
                    success += 1
                    updated += 1
                else:
                    # Comparar y actualizar si hay cambios
                    cambios = {}
                    
                    # Campos a sincronizar
                    campos = [
                        'nombre', 'precio_compra', 'precio_normal', 'precio_mayoreo_1',
                        'precio_mayoreo_2', 'precio_mayoreo_3', 'stock', 'tipo_venta',
                        'precio_por_kg', 'peso_unitario', 'stock_kg', 'stock_minimo',
                        'stock_minimo_kg', 'stock_maximo', 'stock_maximo_kg', 'categoria',
                        'numero_producto'
                    ]
                    
                    for campo in campos:
                        valor_sqlite = producto_sqlite[campo]
                        valor_supabase = producto_supabase.get(campo)
                        
                        # Comparar valores (manejando None)
                        if valor_sqlite != valor_supabase and valor_supabase is not None:
                            cambios[campo] = {
                                'anterior': valor_sqlite,
                                'nuevo': valor_supabase
                            }
                    
                    if cambios:
                        # Actualizar producto
                        update_sql = "UPDATE productos SET "
                        params = []
                        campos_update = []
                        
                        for campo in cambios.keys():
                            campos_update.append(f"{campo} = ?")
                            params.append(cambios[campo]['nuevo'])
                        
                        update_sql += ", ".join(campos_update) + " WHERE codigo = ?"
                        params.append(codigo)
                        
                        cursor.execute(update_sql, params)
                        
                        if verbose:
                            print(f"✏️  Actualizado {codigo}: {cambios}")
                        
                        updated += 1
                        success += 1
                    else:
                        success += 1
                
            except Exception as e:
                print(f"❌ Error al sincronizar producto {codigo}: {e}")
                failed += 1
        
        conn.commit()
        conn.close()
        
        if verbose:
            print(f"\n✅ Sincronización completada:")
            print(f"   - Procesados: {success}")
            print(f"   - Actualizados: {updated}")
            print(f"   - Errores: {failed}")
        
        return {'success': success, 'failed': failed, 'updated': updated}
    
    except Exception as e:
        print(f"❌ Error fatal en sincronización: {e}")
        return {'success': 0, 'failed': 1, 'updated': 0, 'error': str(e)}


def auto_sync_inventario_on_load():
    """
    Llamar esta función al cargar inventario.py
    Sincroniza automáticamente cambios de Supabase sin mostrar mensajes
    """
    try:
        # Usar caché de Streamlit para evitar sincronizar en cada rerun
        if 'last_sync_time' not in st.session_state:
            st.session_state.last_sync_time = None
        
        from datetime import datetime, timedelta
        now = datetime.now()
        
        # Sincronizar si:
        # 1. Es la primera vez en esta sesión, O
        # 2. Han pasado más de 30 segundos desde la última sincronización
        should_sync = (
            st.session_state.last_sync_time is None or
            (now - st.session_state.last_sync_time).total_seconds() > 30
        )
        
        if should_sync:
            result = sincronizar_productos_desde_supabase(verbose=False)
            st.session_state.last_sync_time = now
            
            # Solo mostrar si hubo cambios
            if result.get('updated', 0) > 0:
                st.info(f"📥 Se sincronizaron {result['updated']} cambios desde Supabase")
            
            return result
        
        return {'success': 0, 'failed': 0, 'updated': 0}
    
    except Exception as e:
        # Silenciar errores en la sincronización automática
        return {'success': 0, 'failed': 0, 'updated': 0, 'error': str(e)}


if __name__ == "__main__":
    # Para prueba manual
    print("Sincronizando cambios de Supabase a SQLite...")
    resultado = sincronizar_productos_desde_supabase(verbose=True)
    print(f"\nResultado: {resultado}")
