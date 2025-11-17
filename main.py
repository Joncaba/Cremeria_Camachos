import streamlit as st
import sqlite3
import hashlib

# Importar los módulos
import productos
import inventario
import ventas
import finanzas
import turnos
import pedidos
import usuarios
import config

# Obtener configuración desde secrets.toml
DB_PATH = config.get_db_path()

def hash_password(password):
    """Encriptar contraseña usando SHA-256 con salt"""
    salt = config.get_password_salt()
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verificar_credenciales(usuario, password):
    """Verificar credenciales de usuario"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        # Verificar qué columnas existen
        cursor.execute("PRAGMA table_info(usuarios_admin)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        # Construir query según columnas disponibles
        if 'nombre_completo' in columnas and 'rol' in columnas and 'activo' in columnas:
            cursor.execute("""
                SELECT usuario, nombre_completo, rol FROM usuarios_admin 
                WHERE usuario = ? AND password = ? AND activo = 1
            """, (usuario, password_hash))
        elif 'nombre_completo' in columnas and 'rol' in columnas:
            cursor.execute("""
                SELECT usuario, nombre_completo, rol FROM usuarios_admin 
                WHERE usuario = ? AND password = ?
            """, (usuario, password_hash))
        elif 'nombre_completo' in columnas:
            cursor.execute("""
                SELECT usuario, nombre_completo, 'admin' as rol FROM usuarios_admin 
                WHERE usuario = ? AND password = ?
            """, (usuario, password_hash))
        else:
            # Tabla antigua - solo verificar usuario y password
            cursor.execute("""
                SELECT usuario, usuario as nombre_completo, 'admin' as rol FROM usuarios_admin 
                WHERE usuario = ? AND password = ?
            """, (usuario, password_hash))
        
        resultado = cursor.fetchone()
        return resultado
    finally:
        conn.close()

def mostrar_login():
    """Pantalla de inicio de sesión"""
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 100px auto;
        padding: 40px;
        background-color: #f8f9fa;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🏪 Punto de Venta")
        st.subheader("Cremería")
        st.divider()
        
        with st.form("login_form"):
            st.write("**🔐 Iniciar Sesión**")
            
            usuario = st.text_input("👤 Usuario:", placeholder="Ingrese su usuario")
            password = st.text_input("🔒 Contraseña:", type="password", placeholder="Ingrese su contraseña")
            
            submit = st.form_submit_button("🚀 Ingresar", type="primary", width='stretch')
            
            if submit:
                if not usuario or not password:
                    st.error("❌ Por favor complete todos los campos")
                else:
                    resultado = verificar_credenciales(usuario.strip().lower(), password)
                    if resultado:
                        st.session_state.autenticado = True
                        st.session_state.usuario_actual = resultado[0]
                        st.session_state.nombre_completo = resultado[1]
                        st.session_state.rol_usuario = resultado[2]
                        
                        # Actualizar último acceso
                        usuarios.actualizar_ultimo_acceso(resultado[0])
                        
                        st.success(f"✅ Bienvenido, {resultado[1]}!")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")

def main():
    st.set_page_config(page_title="Punto de Venta - Cremería", layout="wide")
    
    # Crear tabla de usuarios si no existe
    usuarios.crear_tabla_usuarios()
    
    # Verificar autenticación
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    # Si no está autenticado, mostrar login
    if not st.session_state.autenticado:
        mostrar_login()
        return
    
    # Usuario autenticado - mostrar aplicación
    st.sidebar.title("Menú Principal")
    
    # Mostrar información del usuario en el sidebar
    st.sidebar.success(f"👤 **{st.session_state.nombre_completo}**")
    rol_emoji = "🔑" if st.session_state.rol_usuario == "admin" else "👤"
    st.sidebar.caption(f"{rol_emoji} {st.session_state.rol_usuario.upper()}")
    st.sidebar.divider()
    
    # Inicializar selección en session_state
    if 'pagina_seleccionada' not in st.session_state:
        st.session_state.pagina_seleccionada = "Punto de Venta"
    
    # Crear botones para navegación
    if st.sidebar.button("🏪 Punto de Venta", width='stretch'):
        st.session_state.pagina_seleccionada = "Punto de Venta"
    
    if st.sidebar.button("📦 Gestión de Productos", width='stretch'):
        st.session_state.pagina_seleccionada = "Gestión de Productos"
    
    if st.sidebar.button("📋 Inventario", width='stretch'):
        st.session_state.pagina_seleccionada = "Inventario"
    
    if st.sidebar.button("🛒 Pedidos y Reabastecimiento", width='stretch'):
        st.session_state.pagina_seleccionada = "Pedidos y Reabastecimiento"
    
    if st.sidebar.button("💰 Finanzas", width='stretch'):
        st.session_state.pagina_seleccionada = "Finanzas"
    
    if st.sidebar.button("👥 Turnos y Atención al Cliente", width='stretch'):
        st.session_state.pagina_seleccionada = "Turnos y Atención al Cliente"
    
    # Solo mostrar gestión de usuarios para administradores
    if st.session_state.rol_usuario == "admin":
        if st.sidebar.button("🔐 Gestión de Usuarios", width='stretch'):
            st.session_state.pagina_seleccionada = "Gestión de Usuarios"
    
    st.sidebar.divider()
    
    # Botón de cerrar sesión
    if st.sidebar.button("🚪 Cerrar Sesión", width='stretch', type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    seleccion = st.session_state.pagina_seleccionada

    if seleccion == "Punto de Venta":
        ventas.mostrar()
    elif seleccion == "Gestión de Productos":
        productos.mostrar()
    elif seleccion == "Inventario":
        inventario.mostrar()
    elif seleccion == "Pedidos y Reabastecimiento":
        pedidos.mostrar()
    elif seleccion == "Finanzas":
        finanzas.mostrar()
    elif seleccion == "Turnos y Atención al Cliente":
        turnos.mostrar()
    elif seleccion == "Gestión de Usuarios":
        usuarios.mostrar()

if __name__ == "__main__":
    main()