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
from auth_manager import verificar_sesion_admin, mostrar_formulario_login, iniciar_sesion, cerrar_sesion_admin

# Obtener configuración desde secrets.toml
DB_PATH = config.get_db_path()

# Inicializar adaptador de base de datos
db = get_db_adapter()

def main():
    st.set_page_config(page_title="Punto de Venta - Cremería", layout="wide")
    
    # Crear tabla de usuarios si no existe
    usuarios.crear_tabla_usuarios()
    
    # Verificar sesión administrativa usando auth_manager centralizado
    if not verificar_sesion_admin():
        # Mostrar formulario de login simplificado
        mostrar_formulario_login("PRINCIPAL")
        return
    
    # Usuario autenticado - mostrar aplicación
    st.sidebar.title("Menú Principal")
    
    # Mostrar información del usuario en el sidebar
    usuario_actual = st.session_state.get('usuario_admin', 'Admin')
    st.sidebar.success(f"👤 **{usuario_actual}**")
    
    # Obtener rol del usuario desde la base de datos
    from auth_manager import obtener_tiempo_restante
    db_adapter = get_db_adapter()
    usuario_data = db_adapter.obtener_usuario(usuario_actual)
    rol_usuario = usuario_data.get('rol', 'vendedor') if usuario_data else 'vendedor'
    
    # Mostrar rol
    rol_emoji = "🔑" if rol_usuario == "admin" else ("👔" if rol_usuario == "gerente" else "👤")
    st.sidebar.caption(f"{rol_emoji} Rol: **{rol_usuario.upper()}**")
    
    # Mostrar tiempo restante de sesión
    tiempo_restante = obtener_tiempo_restante()
    st.sidebar.caption(f"⏱️ {tiempo_restante}")
    
    st.sidebar.divider()
    
    # Inicializar selección en session_state
    if 'pagina_seleccionada' not in st.session_state:
        st.session_state.pagina_seleccionada = "Punto de Venta"
    
    # Determinar nivel de acceso según rol
    es_admin = rol_usuario == "admin"
    es_gerente = rol_usuario == "gerente"
    
    # Crear botones para navegación con restricciones según rol
    if st.sidebar.button("🏪 Punto de Venta", width='stretch'):
        st.session_state.pagina_seleccionada = "Punto de Venta"
    
    if st.sidebar.button("📋 Inventario", width='stretch'):
        st.session_state.pagina_seleccionada = "Inventario"
    
    # Gestión de Productos: Solo Admin y Gerente
    if es_admin or es_gerente:
        if st.sidebar.button("📦 Gestión de Productos", width='stretch'):
            st.session_state.pagina_seleccionada = "Gestión de Productos"
    
    # Pedidos: Solo Admin y Gerente
    if es_admin or es_gerente:
        if st.sidebar.button("🛒 Pedidos y Reabastecimiento", width='stretch'):
            st.session_state.pagina_seleccionada = "Pedidos y Reabastecimiento"
    
    # Botones solo para admin
    if es_admin:
        st.sidebar.divider()
        st.sidebar.markdown("**🔐 SECCIÓN ADMINISTRATIVA**")
        
        if st.sidebar.button("💰 Finanzas", width='stretch'):
            st.session_state.pagina_seleccionada = "Finanzas"
        
        if st.sidebar.button("👥 Turnos y Atención al Cliente", width='stretch'):
            st.session_state.pagina_seleccionada = "Turnos y Atención al Cliente"
        
        if st.sidebar.button("🔐 Gestión de Usuarios", width='stretch'):
            st.session_state.pagina_seleccionada = "Gestión de Usuarios"
    else:
        # Mostrar mensaje para usuarios no-admin
        st.sidebar.divider()
        if es_gerente:
            st.sidebar.info("ℹ️ Acceso Gerente - Módulos disponibles limitados")
        else:
            st.sidebar.info("ℹ️ Acceso limitado - Solo módulos: Punto de Venta e Inventario")
    
    st.sidebar.divider()
    
    # Botón de cerrar sesión
    if st.sidebar.button("🚪 Cerrar Sesión", width='stretch', type="secondary"):
        cerrar_sesion_admin()
        st.success("✅ Sesión cerrada exitosamente")
        st.rerun()
    
    seleccion = st.session_state.pagina_seleccionada

    if seleccion == "Punto de Venta":
        ventas.mostrar()
    elif seleccion == "Inventario":
        # Pasar parámetro para modo lectura si es vendedor
        modo_lectura = (rol_usuario == "vendedor")
        inventario.mostrar(modo_lectura=modo_lectura)
    elif seleccion == "Gestión de Productos":
        if es_admin or es_gerente:
            productos.mostrar()
        else:
            st.error("❌ No tiene permisos para acceder a este módulo")
    elif seleccion == "Pedidos y Reabastecimiento":
        if es_admin or es_gerente:
            pedidos.mostrar()
        else:
            st.error("❌ No tiene permisos para acceder a este módulo")
    elif seleccion == "Finanzas":
        if es_admin:
            finanzas.mostrar()
        else:
            st.error("❌ No tiene permisos para acceder a este módulo")
    elif seleccion == "Turnos y Atención al Cliente":
        if es_admin:
            turnos.mostrar()
        else:
            st.error("❌ No tiene permisos para acceder a este módulo")
    elif seleccion == "Gestión de Usuarios":
        if es_admin:
            usuarios.mostrar()
        else:
            st.error("❌ No tiene permisos para acceder a este módulo")

if __name__ == "__main__":
    main()