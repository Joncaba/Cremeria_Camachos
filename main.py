import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta
import json
import uuid

# Importar los módulos
import productos
import inventario
import ventas
import finanzas
import turnos
import pedidos
import usuarios
import config
from db_adapter import get_db_adapter

# Obtener configuración desde secrets.toml
DB_PATH = config.get_db_path()

# Inicializar adaptador de base de datos
db = get_db_adapter()

# Archivo para almacenar sesiones activas (persistente entre reloads)
SESSIONS_FILE = "active_sessions.json"

def cargar_sesiones_activas():
    """Cargar sesiones activas desde archivo"""
    try:
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_sesiones_activas(sesiones):
    """Guardar sesiones activas en archivo"""
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sesiones, f)
    except Exception as e:
        print(f"Error al guardar sesiones: {e}")

def crear_token_sesion(usuario_data):
    """Crear token único para la sesión"""
    token = str(uuid.uuid4())
    sesiones = cargar_sesiones_activas()
    
    # Limpiar sesiones expiradas
    ahora = datetime.now().isoformat()
    sesiones_validas = {}
    for tok, data in sesiones.items():
        expira = datetime.fromisoformat(data['expira'])
        if expira > datetime.now():
            sesiones_validas[tok] = data
    
    # Agregar nueva sesión
    sesiones_validas[token] = {
        'usuario': usuario_data[0],
        'nombre_completo': usuario_data[1],
        'rol': usuario_data[2],
        'creada': datetime.now().isoformat(),
        'expira': (datetime.now() + timedelta(hours=12)).isoformat()
    }
    
    guardar_sesiones_activas(sesiones_validas)
    return token

def validar_token_sesion(token):
    """Validar si un token de sesión es válido"""
    if not token:
        return None
    
    sesiones = cargar_sesiones_activas()
    if token not in sesiones:
        return None
    
    data = sesiones[token]
    expira = datetime.fromisoformat(data['expira'])
    
    if expira < datetime.now():
        # Sesión expirada, eliminar
        del sesiones[token]
        guardar_sesiones_activas(sesiones)
        return None
    
    return data

def eliminar_token_sesion(token):
    """Eliminar token de sesión al cerrar sesión"""
    if not token:
        return
    
    sesiones = cargar_sesiones_activas()
    if token in sesiones:
        del sesiones[token]
        guardar_sesiones_activas(sesiones)

def hash_password(password):
    """Encriptar contraseña usando SHA-256 con salt"""
    salt = config.get_password_salt()
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verificar_credenciales(usuario, password):
    """Verificar credenciales de usuario"""
    password_hash = hash_password(password)
    
    try:
        user = db.obtener_usuario(usuario)
        if user and user.get('password') == password_hash:
            # Verificar si está activo (si existe el campo)
            if 'activo' in user and user['activo'] == 0:
                return None
            
            return (
                user.get('usuario'),
                user.get('nombre_completo', usuario),
                user.get('rol', 'admin')
            )
        return None
    except Exception as e:
        print(f"Error al verificar credenciales: {e}")
        return None

def verificar_sesion_activa():
    """Verificar si hay una sesión activa y no ha expirado (12 horas)"""
    # Primero intentar recuperar sesión desde query parameters
    query_params = st.query_params
    token = query_params.get('session_token', None)
    
    if token:
        # Validar token desde archivo persistente
        session_data = validar_token_sesion(token)
        if session_data:
            # Restaurar sesión en session_state
            st.session_state.autenticado = True
            st.session_state.usuario_actual = session_data['usuario']
            st.session_state.nombre_completo = session_data['nombre_completo']
            st.session_state.rol_usuario = session_data['rol']
            st.session_state.session_token = token
            st.session_state.login_timestamp = datetime.fromisoformat(session_data['creada'])
            return True
    
    # Si no hay token válido en URL, verificar session_state tradicional
    if not st.session_state.get('autenticado', False):
        return False
    
    # Verificar si existe timestamp de sesión
    session_timestamp = st.session_state.get('login_timestamp', None)
    if session_timestamp is None:
        # Si no hay timestamp, crear uno ahora (para sesiones antiguas)
        st.session_state.login_timestamp = datetime.now()
        return True
    
    # Verificar si han pasado más de 12 horas
    tiempo_transcurrido = datetime.now() - session_timestamp
    if tiempo_transcurrido > timedelta(hours=12):
        # Sesión expirada, cerrar automáticamente
        cerrar_sesion()
        return False
    
    return True

def cerrar_sesion():
    """Cerrar sesión del usuario"""
    # Eliminar token de sesión persistente
    token = st.session_state.get('session_token', None)
    if token:
        eliminar_token_sesion(token)
    
    # Limpiar query parameters
    st.query_params.clear()
    
    keys_to_delete = [
        'autenticado',
        'usuario_actual',
        'nombre_completo',
        'rol_usuario',
        'login_timestamp',
        'pagina_seleccionada',
        'session_token'
    ]
    
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]

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
            password = st.text_input("🔒 Contraseña:", type="password")
            
            submit = st.form_submit_button("🚀 Ingresar", type="primary", width='stretch')
            
            if submit:
                if not usuario or not password:
                    st.error("❌ Por favor complete todos los campos")
                else:
                    resultado = verificar_credenciales(usuario.strip().lower(), password)
                    if resultado:
                        # Crear token de sesión persistente
                        token = crear_token_sesion(resultado)
                        
                        # Guardar en session_state
                        st.session_state.autenticado = True
                        st.session_state.usuario_actual = resultado[0]
                        st.session_state.nombre_completo = resultado[1]
                        st.session_state.rol_usuario = resultado[2]
                        st.session_state.login_timestamp = datetime.now()
                        st.session_state.session_token = token
                        
                        # Agregar token a query parameters para persistencia
                        st.query_params['session_token'] = token
                        
                        # Actualizar último acceso
                        usuarios.actualizar_ultimo_acceso(resultado[0])
                        
                        st.success(f"✅ Bienvenido, {resultado[1]}! Sesión válida por 12 horas.")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")

def main():
    st.set_page_config(page_title="Punto de Venta - Cremería", layout="wide")
    
    # Crear tabla de usuarios si no existe
    usuarios.crear_tabla_usuarios()
    
    # Verificar sesión activa (con validación de 12 horas)
    if not verificar_sesion_activa():
        mostrar_login()
        return
    
    # Usuario autenticado - mostrar aplicación
    st.sidebar.title("Menú Principal")
    
    # Mostrar información del usuario en el sidebar con tiempo restante
    st.sidebar.success(f"👤 **{st.session_state.nombre_completo}**")
    rol_emoji = "🔑" if st.session_state.rol_usuario == "admin" else "👤"
    st.sidebar.caption(f"{rol_emoji} {st.session_state.rol_usuario.upper()}")
    
    # Mostrar tiempo restante de sesión
    session_timestamp = st.session_state.get('login_timestamp', datetime.now())
    tiempo_transcurrido = datetime.now() - session_timestamp
    tiempo_restante = timedelta(hours=12) - tiempo_transcurrido
    horas_restantes = int(tiempo_restante.total_seconds() // 3600)
    minutos_restantes = int((tiempo_restante.total_seconds() % 3600) // 60)
    st.sidebar.caption(f"⏱️ Sesión: {horas_restantes}h {minutos_restantes}m restantes")
    
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
        cerrar_sesion()
        st.success("✅ Sesión cerrada exitosamente")
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