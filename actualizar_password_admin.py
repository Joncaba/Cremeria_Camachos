"""
Script para actualizar la contraseña del administrador en Supabase
"""
import config
import hashlib
from supabase_client import get_db

# Configuración
USUARIO = "admin"
NUEVA_PASSWORD = "Creme$123"

def hash_password(password):
    """Encriptar contraseña usando SHA-256 con salt"""
    salt = config.get_password_salt()
    return hashlib.sha256((password + salt).encode()).hexdigest()

def actualizar_password():
    """Actualizar password en Supabase"""
    db = get_db()
    
    # Calcular nuevo hash
    nuevo_hash = hash_password(NUEVA_PASSWORD)
    
    print(f"Usuario: {USUARIO}")
    print(f"Contraseña: {NUEVA_PASSWORD}")
    print(f"Salt: {config.get_password_salt()}")
    print(f"Hash nuevo: {nuevo_hash}")
    print("\nActualizando en Supabase...")
    
    try:
        # Actualizar en Supabase
        resultado = db.client.table("usuarios_admin").update({
            "password": nuevo_hash
        }).eq("usuario", USUARIO).execute()
        
        if resultado.data:
            print(f"✅ Contraseña actualizada exitosamente")
            print(f"   Usuario: {resultado.data[0]['usuario']}")
            print(f"   Nombre: {resultado.data[0]['nombre_completo']}")
            
            # Verificar que quedó bien
            usuario_verificado = db.obtener_usuario(USUARIO)
            if usuario_verificado and usuario_verificado['password'] == nuevo_hash:
                print(f"\n✅ VERIFICACIÓN EXITOSA")
                print(f"   Ahora puedes iniciar sesión con:")
                print(f"   Usuario: {USUARIO}")
                print(f"   Contraseña: {NUEVA_PASSWORD}")
            else:
                print(f"\n❌ Error en verificación")
        else:
            print(f"❌ No se pudo actualizar. Usuario no encontrado.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    actualizar_password()
