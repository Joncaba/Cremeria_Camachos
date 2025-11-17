import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

# Ruta de la base de datos
DB_PATH = "pos_cremeria.db"

def hash_password(password):
    """Encriptar contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def crear_tabla_usuarios():
    """Crear tabla de usuarios si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios_admin'")
        tabla_existe = cursor.fetchone() is not None
        
        if tabla_existe:
            # Verificar si tiene todas las columnas necesarias
            cursor.execute("PRAGMA table_info(usuarios_admin)")
            columnas = [col[1] for col in cursor.fetchall()]
            
            # Migrar la tabla si faltan columnas
            if 'nombre_completo' not in columnas:
                print("Migrando tabla usuarios_admin...")
                # Agregar columnas faltantes
                if 'nombre_completo' not in columnas:
                    cursor.execute("ALTER TABLE usuarios_admin ADD COLUMN nombre_completo TEXT DEFAULT 'Usuario'")
                if 'rol' not in columnas:
                    cursor.execute("ALTER TABLE usuarios_admin ADD COLUMN rol TEXT DEFAULT 'usuario'")
                if 'activo' not in columnas:
                    cursor.execute("ALTER TABLE usuarios_admin ADD COLUMN activo INTEGER DEFAULT 1")
                if 'fecha_creacion' not in columnas:
                    cursor.execute("ALTER TABLE usuarios_admin ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                if 'ultimo_acceso' not in columnas:
                    cursor.execute("ALTER TABLE usuarios_admin ADD COLUMN ultimo_acceso TIMESTAMP")
                if 'creado_por' not in columnas:
                    cursor.execute("ALTER TABLE usuarios_admin ADD COLUMN creado_por TEXT DEFAULT 'Sistema'")
                
                # Actualizar usuarios existentes con nombre_completo
                cursor.execute("UPDATE usuarios_admin SET nombre_completo = 'Administrador Principal' WHERE usuario = 'admin' AND nombre_completo = 'Usuario'")
                
                print("Migración completada")
        else:
            # Crear tabla nueva
            cursor.execute('''
                CREATE TABLE usuarios_admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nombre_completo TEXT NOT NULL,
                    rol TEXT DEFAULT 'usuario',
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_acceso TIMESTAMP,
                    creado_por TEXT DEFAULT 'Sistema'
                )
            ''')
        
        # Verificar si existe el usuario admin por defecto
        cursor.execute("SELECT COUNT(*) FROM usuarios_admin WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Crear usuario admin por defecto
            password_hash = hash_password('admin123')
            cursor.execute('''
                INSERT INTO usuarios_admin (usuario, password, nombre_completo, rol, creado_por)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', password_hash, 'Administrador Principal', 'admin', 'Sistema'))
        else:
            # Asegurar que el admin tenga rol de admin
            cursor.execute("UPDATE usuarios_admin SET rol = 'admin' WHERE usuario = 'admin'")
            
        conn.commit()
    except Exception as e:
        print(f"Error al crear tabla de usuarios: {e}")
        conn.rollback()
    finally:
        conn.close()

def verificar_es_admin(usuario):
    """Verificar si un usuario tiene rol de administrador"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM usuarios_admin WHERE usuario = ? AND activo = 1", (usuario,))
        resultado = cursor.fetchone()
        return resultado and resultado[0] == 'admin'
    finally:
        conn.close()

def obtener_todos_usuarios():
    """Obtener lista de todos los usuarios"""
    conn = sqlite3.connect(DB_PATH)
    try:
        query = """
            SELECT id, usuario, nombre_completo, rol, activo, 
                   fecha_creacion, ultimo_acceso, creado_por
            FROM usuarios_admin
            ORDER BY fecha_creacion DESC
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def crear_usuario(usuario, password, nombre_completo, rol, creado_por):
    """Crear un nuevo usuario"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO usuarios_admin (usuario, password, nombre_completo, rol, creado_por)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario, password_hash, nombre_completo, rol, creado_por))
        
        conn.commit()
        return True, "Usuario creado exitosamente"
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya existe"
    except Exception as e:
        conn.rollback()
        return False, f"Error al crear usuario: {str(e)}"
    finally:
        conn.close()

def actualizar_password(usuario, nueva_password):
    """Actualizar contraseña de un usuario"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(nueva_password)
        cursor.execute('''
            UPDATE usuarios_admin 
            SET password = ?
            WHERE usuario = ?
        ''', (password_hash, usuario))
        
        conn.commit()
        return True, "Contraseña actualizada exitosamente"
    except Exception as e:
        conn.rollback()
        return False, f"Error al actualizar contraseña: {str(e)}"
    finally:
        conn.close()

def cambiar_estado_usuario(usuario, activo):
    """Activar o desactivar un usuario"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE usuarios_admin 
            SET activo = ?
            WHERE usuario = ?
        ''', (1 if activo else 0, usuario))
        
        conn.commit()
        estado = "activado" if activo else "desactivado"
        return True, f"Usuario {estado} exitosamente"
    except Exception as e:
        conn.rollback()
        return False, f"Error al cambiar estado: {str(e)}"
    finally:
        conn.close()

def eliminar_usuario(usuario):
    """Eliminar un usuario (solo si no es admin principal)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar que no sea el admin principal
        if usuario == 'admin':
            return False, "No se puede eliminar el usuario administrador principal"
        
        cursor.execute('DELETE FROM usuarios_admin WHERE usuario = ?', (usuario,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Usuario eliminado exitosamente"
        else:
            return False, "Usuario no encontrado"
    except Exception as e:
        conn.rollback()
        return False, f"Error al eliminar usuario: {str(e)}"
    finally:
        conn.close()

def actualizar_ultimo_acceso(usuario):
    """Actualizar timestamp del último acceso"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE usuarios_admin 
            SET ultimo_acceso = CURRENT_TIMESTAMP
            WHERE usuario = ?
        ''', (usuario,))
        conn.commit()
    except Exception as e:
        print(f"Error al actualizar último acceso: {e}")
        conn.rollback()
    finally:
        conn.close()

def mostrar():
    """Función principal del módulo de usuarios"""
    st.title("👥 Gestión de Usuarios")
    
    # Crear tabla si no existe
    crear_tabla_usuarios()
    
    # Verificar que el usuario actual sea administrador
    if 'usuario_actual' not in st.session_state:
        st.error("❌ Debe iniciar sesión para acceder a este módulo")
        return
    
    if not verificar_es_admin(st.session_state.usuario_actual):
        st.error("❌ No tiene permisos de administrador para acceder a este módulo")
        st.info("💡 Solo los usuarios con rol de administrador pueden gestionar usuarios")
        return
    
    # CSS personalizado para las tabs
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 0px 20px;
        background-color: #2c3e50;
        border-radius: 10px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #34495e;
        border-color: #2c3e50;
    }
    
    .stTabs [data-baseweb="tab"] p {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #ecf0f1 !important;
    }
    
    .stTabs [aria-selected="true"] p {
        color: #ffffff !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #34495e;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Tabs para organizar las funciones
    tab1, tab2, tab3 = st.tabs([
        "📋 **LISTA DE USUARIOS**",
        "➕ **CREAR USUARIO**",
        "🔧 **GESTIONAR USUARIOS**"
    ])
    
    with tab1:
        mostrar_lista_usuarios()
    
    with tab2:
        mostrar_crear_usuario()
    
    with tab3:
        mostrar_gestionar_usuarios()

def mostrar_lista_usuarios():
    """Mostrar lista de todos los usuarios"""
    st.subheader("📋 Lista de Usuarios del Sistema")
    
    df_usuarios = obtener_todos_usuarios()
    
    if df_usuarios.empty:
        st.info("No hay usuarios registrados en el sistema")
        return
    
    # Métricas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Usuarios", len(df_usuarios))
    
    with col2:
        usuarios_activos = len(df_usuarios[df_usuarios['activo'] == 1])
        st.metric("✅ Activos", usuarios_activos)
    
    with col3:
        usuarios_inactivos = len(df_usuarios[df_usuarios['activo'] == 0])
        st.metric("❌ Inactivos", usuarios_inactivos)
    
    with col4:
        admins = len(df_usuarios[df_usuarios['rol'] == 'admin'])
        st.metric("🔑 Administradores", admins)
    
    st.divider()
    
    # Filtros
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        filtro_estado = st.selectbox(
            "🔍 Filtrar por estado:",
            ["Todos", "Activos", "Inactivos"]
        )
    
    with col_filtro2:
        filtro_rol = st.selectbox(
            "🔍 Filtrar por rol:",
            ["Todos", "Administrador", "Usuario"]
        )
    
    # Aplicar filtros
    df_filtrado = df_usuarios.copy()
    
    if filtro_estado == "Activos":
        df_filtrado = df_filtrado[df_filtrado['activo'] == 1]
    elif filtro_estado == "Inactivos":
        df_filtrado = df_filtrado[df_filtrado['activo'] == 0]
    
    if filtro_rol == "Administrador":
        df_filtrado = df_filtrado[df_filtrado['rol'] == 'admin']
    elif filtro_rol == "Usuario":
        df_filtrado = df_filtrado[df_filtrado['rol'] == 'usuario']
    
    # Mostrar tabla
    st.subheader(f"📊 Usuarios Encontrados: {len(df_filtrado)}")
    
    # Formatear datos para mostrar
    df_display = df_filtrado.copy()
    df_display['activo'] = df_display['activo'].apply(lambda x: '✅ Activo' if x == 1 else '❌ Inactivo')
    df_display['rol'] = df_display['rol'].apply(lambda x: '🔑 Admin' if x == 'admin' else '👤 Usuario')
    
    # Formatear fechas
    if 'fecha_creacion' in df_display.columns:
        df_display['fecha_creacion'] = pd.to_datetime(df_display['fecha_creacion']).dt.strftime('%d/%m/%Y %H:%M')
    
    if 'ultimo_acceso' in df_display.columns:
        df_display['ultimo_acceso'] = pd.to_datetime(df_display['ultimo_acceso'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
        df_display['ultimo_acceso'] = df_display['ultimo_acceso'].fillna('Nunca')
    
    st.dataframe(
        df_display,
        column_config={
            "id": "🆔 ID",
            "usuario": "👤 Usuario",
            "nombre_completo": "📝 Nombre Completo",
            "rol": "🔐 Rol",
            "activo": "📊 Estado",
            "fecha_creacion": "📅 Fecha Creación",
            "ultimo_acceso": "🕐 Último Acceso",
            "creado_por": "👨‍💼 Creado Por"
        },
        hide_index=True,
        width='stretch'
    )

def mostrar_crear_usuario():
    """Formulario para crear nuevos usuarios"""
    st.subheader("➕ Crear Nuevo Usuario")
    
    with st.form("form_crear_usuario"):
        st.write("**📝 Información del Usuario**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_usuario = st.text_input(
                "👤 Nombre de Usuario:",
                placeholder="Ej: jperez",
                help="Nombre único para iniciar sesión (sin espacios)"
            )
            
            nuevo_nombre = st.text_input(
                "📝 Nombre Completo:",
                placeholder="Ej: Juan Pérez García",
                help="Nombre completo del usuario"
            )
        
        with col2:
            nuevo_password = st.text_input(
                "🔒 Contraseña:",
                type="password",
                placeholder="Mínimo 6 caracteres",
                help="Contraseña para iniciar sesión"
            )
            
            confirmar_password = st.text_input(
                "🔒 Confirmar Contraseña:",
                type="password",
                placeholder="Repetir la contraseña",
                help="Debe coincidir con la contraseña anterior"
            )
        
        nuevo_rol = st.selectbox(
            "🔐 Rol del Usuario:",
            ["usuario", "admin"],
            format_func=lambda x: "🔑 Administrador" if x == "admin" else "👤 Usuario Normal",
            help="Administrador: acceso completo | Usuario: acceso limitado"
        )
        
        st.divider()
        
        # Mostrar información sobre los roles
        if nuevo_rol == "admin":
            st.warning("⚠️ **Rol Administrador:** Tendrá acceso completo a todas las funciones, incluyendo gestión de usuarios")
        else:
            st.info("💡 **Rol Usuario:** Acceso a funciones de punto de venta e inventario, sin gestión de usuarios")
        
        submitted = st.form_submit_button("➕ Crear Usuario", type="primary", width='stretch')

        if submitted:
            # Validaciones
            errores = []
            
            if not nuevo_usuario or len(nuevo_usuario.strip()) < 3:
                errores.append("El nombre de usuario debe tener al menos 3 caracteres")
            
            if ' ' in nuevo_usuario:
                errores.append("El nombre de usuario no puede contener espacios")
            
            if not nuevo_nombre or len(nuevo_nombre.strip()) < 3:
                errores.append("El nombre completo debe tener al menos 3 caracteres")
            
            if not nuevo_password or len(nuevo_password) < 6:
                errores.append("La contraseña debe tener al menos 6 caracteres")
            
            if nuevo_password != confirmar_password:
                errores.append("Las contraseñas no coinciden")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                # Crear usuario
                exito, mensaje = crear_usuario(
                    nuevo_usuario.strip().lower(),
                    nuevo_password,
                    nuevo_nombre.strip(),
                    nuevo_rol,
                    st.session_state.usuario_actual
                )
                
                if exito:
                    st.success(f"✅ {mensaje}")
                    st.balloons()
                    
                    # Mostrar resumen
                    st.info(f"""
                    **📋 Resumen del Usuario Creado:**
                    - 👤 Usuario: {nuevo_usuario.strip().lower()}
                    - 📝 Nombre: {nuevo_nombre.strip()}
                    - 🔐 Rol: {'🔑 Administrador' if nuevo_rol == 'admin' else '👤 Usuario Normal'}
                    - 📅 Creado por: {st.session_state.usuario_actual}
                    """)
                    
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")

def mostrar_gestionar_usuarios():
    """Gestionar usuarios existentes: cambiar contraseña, activar/desactivar, eliminar"""
    st.subheader("🔧 Gestionar Usuarios")
    
    # Obtener lista de usuarios
    df_usuarios = obtener_todos_usuarios()
    
    if df_usuarios.empty:
        st.info("No hay usuarios para gestionar")
        return
    
    # Seleccionar usuario a gestionar
    usuarios_lista = df_usuarios['usuario'].tolist()
    
    usuario_seleccionado = st.selectbox(
        "👤 Seleccionar Usuario:",
        usuarios_lista,
        format_func=lambda x: f"{x} - {df_usuarios[df_usuarios['usuario'] == x]['nombre_completo'].values[0]}"
    )
    
    if usuario_seleccionado:
        # Obtener información del usuario
        info_usuario = df_usuarios[df_usuarios['usuario'] == usuario_seleccionado].iloc[0]
        
        # Mostrar información del usuario
        st.divider()
        st.subheader(f"📋 Información de: {info_usuario['nombre_completo']}")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.metric("👤 Usuario", info_usuario['usuario'])
            st.metric("🔐 Rol", "🔑 Admin" if info_usuario['rol'] == 'admin' else "👤 Usuario")
        
        with col_info2:
            estado = "✅ Activo" if info_usuario['activo'] == 1 else "❌ Inactivo"
            st.metric("📊 Estado", estado)
            fecha_creacion = pd.to_datetime(info_usuario['fecha_creacion']).strftime('%d/%m/%Y')
            st.metric("📅 Creado", fecha_creacion)
        
        with col_info3:
            st.metric("👨‍💼 Creado Por", info_usuario['creado_por'])
            if pd.notna(info_usuario['ultimo_acceso']):
                ultimo_acceso = pd.to_datetime(info_usuario['ultimo_acceso']).strftime('%d/%m/%Y')
                st.metric("🕐 Último Acceso", ultimo_acceso)
            else:
                st.metric("🕐 Último Acceso", "Nunca")
        
        st.divider()
        
        # Tabs para diferentes acciones
        tab_pass, tab_estado, tab_eliminar = st.tabs([
            "🔒 **Cambiar Contraseña**",
            "📊 **Cambiar Estado**",
            "🗑️ **Eliminar Usuario**"
        ])
        
        with tab_pass:
            mostrar_cambiar_password(usuario_seleccionado, info_usuario)
        
        with tab_estado:
            mostrar_cambiar_estado(usuario_seleccionado, info_usuario)
        
        with tab_eliminar:
            mostrar_eliminar_usuario(usuario_seleccionado, info_usuario)

def mostrar_cambiar_password(usuario, info_usuario):
    """Formulario para cambiar contraseña"""
    st.subheader(f"🔒 Cambiar Contraseña de: {info_usuario['nombre_completo']}")
    
    with st.form(f"form_cambiar_password_{usuario}"):
        nueva_password = st.text_input(
            "🔒 Nueva Contraseña:",
            type="password",
            placeholder="Mínimo 6 caracteres"
        )
        
        confirmar_nueva_password = st.text_input(
            "🔒 Confirmar Nueva Contraseña:",
            type="password",
            placeholder="Repetir la nueva contraseña"
        )
        
        submitted = st.form_submit_button("🔄 Cambiar Contraseña", type="primary", width='stretch')

        if submitted:
            if not nueva_password or len(nueva_password) < 6:
                st.error("❌ La contraseña debe tener al menos 6 caracteres")
            elif nueva_password != confirmar_nueva_password:
                st.error("❌ Las contraseñas no coinciden")
            else:
                exito, mensaje = actualizar_password(usuario, nueva_password)
                if exito:
                    st.success(f"✅ {mensaje}")
                    st.info(f"💡 La contraseña de **{info_usuario['nombre_completo']}** ha sido actualizada")
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")

def mostrar_cambiar_estado(usuario, info_usuario):
    """Cambiar estado activo/inactivo del usuario"""
    st.subheader(f"📊 Cambiar Estado de: {info_usuario['nombre_completo']}")
    
    estado_actual = info_usuario['activo'] == 1
    
    if estado_actual:
        st.success("✅ Estado Actual: **ACTIVO**")
        st.info("💡 El usuario puede iniciar sesión y usar el sistema")
    else:
        st.error("❌ Estado Actual: **INACTIVO**")
        st.warning("⚠️ El usuario NO puede iniciar sesión")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if estado_actual:
            if st.button("🚫 Desactivar Usuario", type="secondary", width='stretch'):
                if usuario == 'admin':
                    st.error("❌ No se puede desactivar el usuario administrador principal")
                else:
                    exito, mensaje = cambiar_estado_usuario(usuario, False)
                    if exito:
                        st.success(f"✅ {mensaje}")
                        st.rerun()
                    else:
                        st.error(f"❌ {mensaje}")
    
    with col2:
        if not estado_actual:
            if st.button("✅ Activar Usuario", type="primary", width='stretch'):
                exito, mensaje = cambiar_estado_usuario(usuario, True)
                if exito:
                    st.success(f"✅ {mensaje}")
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")

def mostrar_eliminar_usuario(usuario, info_usuario):
    """Eliminar usuario del sistema"""
    st.subheader(f"🗑️ Eliminar Usuario: {info_usuario['nombre_completo']}")
    
    if usuario == 'admin':
        st.error("❌ **No se puede eliminar el usuario administrador principal**")
        st.info("💡 El usuario 'admin' es necesario para el funcionamiento del sistema")
        return
    
    st.warning("⚠️ **ADVERTENCIA:** Esta acción es IRREVERSIBLE")
    st.error("❌ Se eliminará permanentemente el usuario y toda su información")
    
    st.divider()
    
    st.write("**📋 Datos que se eliminarán:**")
    st.write(f"- 👤 Usuario: **{info_usuario['usuario']}**")
    st.write(f"- 📝 Nombre: **{info_usuario['nombre_completo']}**")
    st.write(f"- 🔐 Rol: **{info_usuario['rol']}**")
    st.write(f"- 📅 Creado: **{pd.to_datetime(info_usuario['fecha_creacion']).strftime('%d/%m/%Y')}**")
    
    st.divider()
    
    # Confirmación de seguridad
    confirmacion = st.text_input(
        "✍️ Para confirmar, escribe el nombre de usuario a eliminar:",
        placeholder=f"Escribe: {usuario}"
    )
    
    if st.button("🗑️ ELIMINAR USUARIO", type="secondary", width='stretch'):
        if confirmacion != usuario:
            st.error(f"❌ Debe escribir exactamente '{usuario}' para confirmar la eliminación")
        else:
            exito, mensaje = eliminar_usuario(usuario)
            if exito:
                st.success(f"✅ {mensaje}")
                st.info(f"💡 El usuario **{info_usuario['nombre_completo']}** ha sido eliminado del sistema")
                import time
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ {mensaje}")
