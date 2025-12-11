import sqlite3
import sys
sys.path.append('.')

try:
    from sync_manager import get_sync_manager
    
    # Obtener el producto actualizado
    conn = sqlite3.connect('pos_cremeria.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM productos WHERE codigo = '11111'")
    producto = cursor.fetchone()
    
    if producto:
        print("="*60)
        print("SINCRONIZANDO YOGURT 11111 A SUPABASE")
        print("="*60)
        
        producto_dict = {
            'codigo': producto[0],
            'nombre': producto[1],
            'precio_compra': producto[2],
            'precio_normal': producto[3],
            'precio_mayoreo_1': producto[4],
            'precio_mayoreo_2': producto[5],
            'precio_mayoreo_3': producto[6],
            'stock': producto[7],
            'tipo_venta': producto[8],
            'precio_por_kg': producto[9],
            'peso_unitario': producto[10],
            'stock_kg': producto[11],
            'stock_minimo': producto[12],
            'stock_minimo_kg': producto[13],
            'stock_maximo': producto[14],
            'stock_maximo_kg': producto[15],
            'categoria': producto[16]
        }
        
        print(f"\nProducto: {producto_dict['nombre']}")
        print(f"Stock local: {producto_dict['stock']} unidades")
        
        # Sincronizar
        sync_manager = get_sync_manager()
        
        if sync_manager.is_online():
            print("\n🔄 Sincronizando a Supabase...")
            exito, error = sync_manager.sync_producto_to_supabase(producto_dict)
            
            if exito:
                print("✅ Sincronización exitosa!")
                print(f"✅ Stock en Supabase actualizado a {producto_dict['stock']} unidades")
            else:
                print(f"❌ Error: {error}")
        else:
            print("❌ Sin conexión a Supabase")
    else:
        print("❌ Producto no encontrado")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
