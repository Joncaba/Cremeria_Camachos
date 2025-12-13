"""
Gestor centralizado de autenticación con sesión persistente de 12 horas
Todos los módulos deben usar este sistema para mantener consistencia
"""

import streamlit as st
import hashlib
from datetime import datetime, timedelta
import os
import json
import sqlite3
from db_adapter import get_db_adapter

# Inicializar adaptador de base de datos
db_auth = get_db_adapter()

# Salt para contraseñas (el mismo que usamos para crear admin)
PASSWORD_SALT = os.getenv("PASSWORD_SALT", "default-salt")

# Archivo para almacenar sesiones persistentes
SESSIONS_DB = "sessiones.db"

def _inicializar_sesiones_db():
    """Inicializar base de datos de sesiones"""
    conn = sqlite3.connect(SESSIONS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesiones (
            token TEXT PRIMARY KEY,
            usuario TEXT NOT NULL,
            inicio DATETIME NOT NULL,
            expira DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def _limpiar_sesiones_expiradas():
    """Eliminar sesiones expiradas"""
    try:
        conn = sqlite3.connect(SESSIONS_DB)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sesiones WHERE expira < ?', (datetime.now(),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al limpiar sesiones: {e}")

def _crear_token_sesion(usuario):
    """Crear token de sesión persistente"""
    _inicializar_sesiones_db()
    
    token = hashlib.sha256(f"{usuario}{datetime.now().isoformat()}".encode()).hexdigest()
    inicio = datetime.now()
    expira = inicio + timedelta(hours=12)
    
    try:
        conn = sqlite3.connect(SESSIONS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sesiones (token, usuario, inicio, expira)
            VALUES (?, ?, ?, ?)
        ''', (token, usuario, inicio, expira))
        conn.commit()
        conn.close()
        return token
    except Exception as e:
        print(f"Error al crear token: {e}")
        return None

def _validar_token_sesion(token):
    """Validar token de sesión"""
    if not token:
        return None
    
    _limpiar_sesiones_expiradas()
    
    try:
        conn = sqlite3.connect(SESSIONS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT usuario, expira FROM sesiones 
            WHERE token = ? AND expira > ?
        ''', (token, datetime.now()))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'usuario': resultado[0],
                'expira': resultado[1]
            }
        return None
    except Exception as e:
        print(f"Error al validar token: {e}")
        return None

def _eliminar_token_sesion(token):
    """Eliminar token de sesión"""
    try:
        conn = sqlite3.connect(SESSIONS_DB)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sesiones WHERE token = ?', (token,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al eliminar token: {e}")

def hash_password(password):
    """Crear hash de la contraseña con salt"""
    return hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest()

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
    # Crear token persistente
    token = _crear_token_sesion(usuario)
    
    # Guardar en session_state
    st.session_state.admin_autenticado = True
    st.session_state.usuario_admin = usuario
    st.session_state.session_token = token
    st.session_state.session_timestamp = datetime.now()
    
    # Guardar token en query parameters para persistencia
    st.query_params['session_token'] = token
    
    # Sincronizar usuario con Supabase
    try:
        from sync_manager import get_sync_manager
        sync_manager = get_sync_manager()
        
        # Obtener datos del usuario
        user_data = db_auth.obtener_usuario(usuario)
        if user_data:
            sync_manager.sync_usuario_to_supabase(user_data)
    except Exception as e:
        print(f"No se pudo sincronizar usuario con Supabase: {e}")

def verificar_sesion_admin():
    """Verificar si hay una sesión administrativa activa y no ha expirado (12 horas)"""
    # Primero intentar recuperar sesión desde token persistente (via query params)
    token = st.query_params.get('session_token', None)
    
    if token:
        session_data = _validar_token_sesion(token)
        if session_data:
            # Restaurar sesión en session_state
            st.session_state.admin_autenticado = True
            st.session_state.usuario_admin = session_data['usuario']
            st.session_state.session_token = token
            st.session_state.session_timestamp = datetime.now()
            return True
    
    # Si no hay token válido en URL, verificar session_state
    if not st.session_state.get('admin_autenticado', False):
        return False
    
    # Verificar si existe timestamp de sesión
    session_timestamp = st.session_state.get('session_timestamp', None)
    if session_timestamp is None:
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
    # Eliminar token persistente
    token = st.session_state.get('session_token', None)
    if token:
        _eliminar_token_sesion(token)
    
    # Limpiar query parameters
    st.query_params.clear()
    
    # Limpiar session_state
    keys_to_delete = [
        'admin_autenticado',
        'usuario_admin',
        'session_timestamp',
        'session_token',
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
    """Obtener tiempo restante de la sesión en formato texto"""
    token = st.session_state.get('session_token', None)
    if not token:
        return "Sin sesión activa"
    
    session_data = _validar_token_sesion(token)
    if not session_data:
        return "Sesión expirada"
    
    expira = datetime.fromisoformat(session_data['expira'])
    tiempo_restante = expira - datetime.now()
    
    if tiempo_restante.total_seconds() <= 0:
        return "Sesión expirada"
    
    horas_restantes = int(tiempo_restante.total_seconds() // 3600)
    minutos_restantes = int((tiempo_restante.total_seconds() % 3600) // 60)
    
    return f"Sesión: {horas_restantes}h {minutos_restantes}m restantes"

def mostrar_formulario_login(titulo_modulo=""):
    """Mostrar formulario de login unificado - Versión simplificada"""
    
    st.title("🏪 Punto de Venta")
    st.subheader("Cremería")
    st.divider()
    
    # Generar key único basado en el módulo
    form_key = f"login_form_{titulo_modulo.lower().replace(' ', '_')}" if titulo_modulo else "login_form"
    
    with st.form(form_key):
        st.write("**🔐 Iniciar Sesión**")
        
        usuario = st.text_input("👤 Usuario:", placeholder="Ingrese su usuario")
        password = st.text_input("🔑 Contraseña:", type="password")
        
        submit_login = st.form_submit_button("✔️ Ingresar", type="primary", use_container_width=True)
        
        if submit_login:
            if usuario and password:
                if verificar_credenciales(usuario, password):
                    iniciar_sesion(usuario)
                    st.success("✅ ¡Acceso concedido! Sesión válida por 12 horas.")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos.")
            else:
                st.warning("⚠️ Por favor ingresa usuario y contraseña.")
