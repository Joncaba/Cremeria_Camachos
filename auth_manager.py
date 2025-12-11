"""
Gestor centralizado de autenticación con sesión persistente de 12 horas
Todos los módulos deben usar este sistema para mantener consistencia
"""

import streamlit as st
import hashlib
from datetime import datetime, timedelta
import config
from db_adapter import get_db_adapter

# Inicializar adaptador de base de datos
db_auth = get_db_adapter()

def hash_password(password):
    """Crear hash de la contraseña con salt"""
    salt = config.get_password_salt()
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verificar_credenciales(usuario, password):
    """Verificar si las credenciales son correctas"""
    password_hash = hash_password(password)
    try:
        user = db_auth.obtener_usuario(usuario)
        if user and user.get('password') == password_hash:
            # Verificar si está activo
            if 'activo' in user and user['activo'] == 0:
                return False
            return True
        return False
    except Exception as e:
        print(f"Error al verificar credenciales: {e}")
        return False

def iniciar_sesion(usuario):
    """Iniciar sesión administrativa global (12 horas de duración)"""
    st.session_state.admin_autenticado = True
    st.session_state.usuario_admin = usuario
    st.session_state.session_timestamp = datetime.now()

def verificar_sesion_admin():
    """Verificar si hay una sesión administrativa activa y no ha expirado (12 horas)"""
    if not st.session_state.get('admin_autenticado', False):
        return False
    
    # Verificar si existe timestamp de sesión
    session_timestamp = st.session_state.get('session_timestamp', None)
    if session_timestamp is None:
        # Si no hay timestamp, crear uno ahora (para sesiones antiguas)
        st.session_state.session_timestamp = datetime.now()
        return True
    
    # Verificar si han pasado más de 12 horas
    tiempo_transcurrido = datetime.now() - session_timestamp
    if tiempo_transcurrido > timedelta(hours=12):
        # Sesión expirada, cerrar automáticamente
        cerrar_sesion_admin()
        return False
    
    return True

def cerrar_sesion_admin():
    """Cerrar sesión administrativa global"""
    keys_to_delete = [
        'admin_autenticado',
        'usuario_admin',
        'session_timestamp',
        # Claves antiguas de módulos específicos (por compatibilidad)
        'admin_pedidos_autenticado',
        'usuario_admin_pedidos',
        'admin_inventario_autenticado',
        'usuario_admin_inventario'
    ]
    
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]

def obtener_tiempo_restante():
    """Obtener tiempo restante de la sesión en formato (horas, minutos)"""
    session_timestamp = st.session_state.get('session_timestamp', datetime.now())
    tiempo_transcurrido = datetime.now() - session_timestamp
    tiempo_restante = timedelta(hours=12) - tiempo_transcurrido
    
    horas_restantes = int(tiempo_restante.total_seconds() // 3600)
    minutos_restantes = int((tiempo_restante.total_seconds() % 3600) // 60)
    
    return horas_restantes, minutos_restantes

def mostrar_formulario_login(titulo_modulo=""):
    """Mostrar formulario de login unificado"""
    titulo = f"🔐 ACCESO ADMINISTRATIVO{' - ' + titulo_modulo if titulo_modulo else ''}"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); 
                padding: 2rem; border-radius: 15px; text-align: center; margin: 1rem 0;">
        <h2 style="color: #8e44ad; margin-bottom: 1rem;">{titulo}</h2>
        <p style="color: #2c3e50; font-size: 1.1rem; margin-bottom: 0;">
            Se requiere autenticación de administrador. La sesión durará 12 horas.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Generar key único basado en el módulo
    form_key = f"login_form_{titulo_modulo.lower().replace(' ', '_')}" if titulo_modulo else "login_form"
    
    with st.form(form_key):
        col_login1, col_login2, col_login3 = st.columns([1, 2, 1])
        
        with col_login2:
            usuario = st.text_input("👤 Usuario:", placeholder="Ingresa tu usuario")
            password = st.text_input("🔑 Contraseña:", type="password")
            
            col_btn_login = st.columns([1, 2, 1])
            with col_btn_login[1]:
                submit_login = st.form_submit_button("🔓 INICIAR SESIÓN", type="primary")
            
            if submit_login:
                if usuario and password:
                    if verificar_credenciales(usuario, password):
                        iniciar_sesion(usuario)
                        st.success("✅ ¡Acceso concedido! Sesión válida por 12 horas.")
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas. Inténtalo de nuevo.")
                else:
                    st.warning("⚠️ Por favor, completa ambos campos.")
