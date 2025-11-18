"""
Script de prueba para verificar la conexión con Supabase
"""
from supabase import create_client
import os

def get_supabase_client():
    """Obtener cliente de Supabase desde archivo secrets.toml"""
    # Leer secrets.toml
    secrets_path = '.streamlit/secrets.toml'
    url = None
    key = None
    
    if os.path.exists(secrets_path):
        with open(secrets_path, 'r', encoding='utf-8') as f:
            in_supabase = False
            for line in f:
                line = line.strip()
                if '[supabase]' in line:
                    in_supabase = True
                elif line.startswith('[') and in_supabase:
                    break
                elif in_supabase:
                    if line.startswith('url'):
                        url = line.split('=')[1].strip().strip('"')
                    elif line.startswith('key'):
                        key = line.split('=')[1].strip().strip('"')
    
    if not url or not key:
        raise ValueError("No se encontraron credenciales de Supabase en secrets.toml")
    
    return create_client(url, key)

def test_conexion():
    """Probar conexión básica a Supabase"""
    print("🔄 Probando conexión con Supabase...")
    print("=" * 60)
    
    try:
        # Obtener cliente
        client = get_supabase_client()
        print("✅ Cliente de Supabase creado exitosamente")
        
        # Probar obtener productos
        print("\n📦 Obteniendo productos...")
        response = client.table('productos').select('*').execute()
        productos = response.data
        print(f"✅ {len(productos)} productos encontrados")
        
        if productos:
            print("\n📋 Primeros 3 productos:")
            for prod in productos[:3]:
                print(f"   - {prod['codigo']}: {prod['nombre']} (${prod['precio_normal']})")
        
        # Probar obtener usuarios
        print("\n👥 Obteniendo usuarios...")
        response = client.table('usuarios_admin').select('*').execute()
        usuarios = response.data
        print(f"✅ {len(usuarios)} usuarios encontrados")
        
        if usuarios:
            print("\n📋 Usuarios:")
            for user in usuarios:
                print(f"   - {user['usuario']}: {user['nombre_completo']} ({user['rol']})")
        
        # Probar obtener ventas
        print("\n💰 Obteniendo últimas ventas...")
        response = client.table('ventas').select('*').order('fecha', desc=True).limit(5).execute()
        ventas = response.data
        print(f"✅ {len(ventas)} ventas obtenidas")
        
        if ventas:
            print("\n📋 Últimas ventas:")
            for venta in ventas:
                print(f"   - ID {venta['id']}: ${venta['total']} - {venta['fecha']}")
        
        # Probar estadísticas
        print("\n📊 Calculando total de ventas...")
        response = client.table('ventas').select('total').execute()
        total = sum(v['total'] for v in response.data if v['total'])
        print(f"✅ Total de ventas: ${total:,.2f}")
        
        print("\n" + "=" * 60)
        print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("✅ Tu base de datos Supabase está funcionando correctamente")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en la conexión: {e}")
        print("\n💡 Verifica:")
        print("   1. Que las credenciales en secrets.toml sean correctas")
        print("   2. Que hayas ejecutado el script SQL en Supabase")
        print("   3. Que las tablas existan en tu base de datos")
        return False

if __name__ == "__main__":
    test_conexion()
