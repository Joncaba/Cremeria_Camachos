import streamlit as st
import sqlite3
import pandas as pd
import time
import hashlib
import unicodedata
import re

conn = sqlite3.connect("pos_cremeria.db", check_same_thread=False)
cursor = conn.cursor()

# === UTILIDADES DE BÚSQUEDA ===

def normalizar_texto(texto):
    """Normalizar texto para búsquedas case-insensitive y sin acentos"""
    if not texto:
        return ""
    
    # Convertir a minúsculas
    texto = str(texto).lower()
    
    # Remover acentos y caracteres especiales
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    
    # Remover espacios extra
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def busqueda_flexible(texto_busqueda, texto_objetivo):
    """Realizar búsqueda flexible case-insensitive y sin acentos"""
    if not texto_busqueda or not texto_objetivo:
        return False
    
    busqueda_norm = normalizar_texto(texto_busqueda)
    objetivo_norm = normalizar_texto(texto_objetivo)
    
    return busqueda_norm in objetivo_norm

# === SISTEMA DE AUTENTICACIÓN PARA ADMINISTRACIÓN ===

def crear_tabla_usuarios():
    """Crear tabla de usuarios administradores si no existe"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nivel TEXT DEFAULT 'admin',
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

def hash_password(password):
    """Crear hash de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_credenciales(usuario, password):
    """Verificar si las credenciales son correctas"""
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id FROM usuarios_admin WHERE usuario = ? AND password_hash = ?", 
        (usuario, password_hash)
    )
    return cursor.fetchone() is not None

def crear_admin_por_defecto():
    """Crear usuario administrador por defecto si no existe"""
    cursor.execute("SELECT COUNT(*) FROM usuarios_admin")
    if cursor.fetchone()[0] == 0:
        # Crear admin por defecto: usuario="admin", password="cremeria123"
        usuario_default = "admin"
        password_default = "cremeria123"
        password_hash = hash_password(password_default)
        
        cursor.execute(
            "INSERT INTO usuarios_admin (usuario, password_hash) VALUES (?, ?)",
            (usuario_default, password_hash)
        )
        conn.commit()
        return True
    return False

def mostrar_formulario_login():
    """Mostrar formulario de login para administradores"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); 
                padding: 2rem; border-radius: 15px; text-align: center; margin: 1rem 0;">
        <h2 style="color: #8e44ad; margin-bottom: 1rem;">🔐 ACCESO ADMINISTRATIVO</h2>
        <p style="color: #2c3e50; font-size: 1.1rem; margin-bottom: 0;">
            Para editar productos se requiere autenticación de administrador
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        col_login1, col_login2, col_login3 = st.columns([1, 2, 1])
        
        with col_login2:
            usuario = st.text_input("👤 Usuario:", placeholder="Ingresa tu usuario")
            password = st.text_input("🔑 Contraseña:", type="password", placeholder="Ingresa tu contraseña")
            
            col_btn_login = st.columns([1, 2, 1])
            with col_btn_login[1]:
                submit_login = st.form_submit_button("🔓 INICIAR SESIÓN", type="primary")
            
            if submit_login:
                if usuario and password:
                    if verificar_credenciales(usuario, password):
                        st.session_state.admin_autenticado = True
                        st.session_state.usuario_admin = usuario
                        st.success("✅ ¡Acceso concedido! Redirigiendo...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas. Inténtalo de nuevo.")
                        st.info("💡 **Credenciales por defecto:** Usuario: `admin` | Contraseña: `cremeria123`")
                else:
                    st.warning("⚠️ Por favor, completa ambos campos.")

def verificar_sesion_admin():
    """Verificar si hay una sesión administrativa activa"""
    return st.session_state.get('admin_autenticado', False)

def cerrar_sesion_admin():
    """Cerrar sesión administrativa"""
    if 'admin_autenticado' in st.session_state:
        del st.session_state.admin_autenticado
    if 'usuario_admin' in st.session_state:
        del st.session_state.usuario_admin

# Inicializar sistema de usuarios
crear_tabla_usuarios()
admin_creado = crear_admin_por_defecto()

# Ejecutar migración para soporte de productos a granel
def actualizar_base_datos_productos_granel():
    """Migración para agregar soporte de productos a granel y peso unitario"""
    cursor.execute("PRAGMA table_info(productos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Agregar campos para productos a granel y peso unitario
    if 'tipo_venta' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")
    if 'precio_por_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN precio_por_kg REAL DEFAULT 0")
    if 'peso_unitario' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN peso_unitario REAL DEFAULT 0")
    if 'stock_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN stock_kg REAL DEFAULT 0")
    if 'stock_minimo' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN stock_minimo INTEGER DEFAULT 10")
    if 'stock_minimo_kg' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN stock_minimo_kg REAL DEFAULT 0")
    if 'categoria' not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'cremeria'")
    
    conn.commit()

# Ejecutar migración
actualizar_base_datos_productos_granel()

# Crear tabla base si no existe
cursor.execute('''
CREATE TABLE IF NOT EXISTS productos (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio_compra REAL NOT NULL,
    precio_normal REAL NOT NULL,
    precio_mayoreo_1 REAL NOT NULL,
    precio_mayoreo_2 REAL NOT NULL,
    precio_mayoreo_3 REAL NOT NULL,
    stock INTEGER NOT NULL,
    tipo_venta TEXT DEFAULT 'unidad',
    precio_por_kg REAL DEFAULT 0,
    peso_unitario REAL DEFAULT 0,
    stock_kg REAL DEFAULT 0,
    stock_minimo INTEGER DEFAULT 10,
    stock_minimo_kg REAL DEFAULT 0,
    categoria TEXT DEFAULT 'cremeria'
)
''')

# Migrar tabla existente para agregar nuevos campos
cursor.execute("PRAGMA table_info(productos)")
columns = [column[1] for column in cursor.fetchall()]

# Agregar precio_compra si no existe
if 'precio_compra' not in columns:
    cursor.execute("ALTER TABLE productos ADD COLUMN precio_compra REAL DEFAULT 0")

# Renombrar precio_mayoreo a precio_mayoreo_1 si existe el campo antiguo
if 'precio_mayoreo' in columns and 'precio_mayoreo_1' not in columns:
    cursor.execute("ALTER TABLE productos RENAME COLUMN precio_mayoreo TO precio_mayoreo_1")

# Agregar nuevos campos de mayoreo si no existen
if 'precio_mayoreo_2' not in columns:
    cursor.execute("ALTER TABLE productos ADD COLUMN precio_mayoreo_2 REAL DEFAULT 0")
if 'precio_mayoreo_3' not in columns:
    cursor.execute("ALTER TABLE productos ADD COLUMN precio_mayoreo_3 REAL DEFAULT 0")

conn.commit()

def agregar_producto(codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3, 
                    stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, categoria):
    """Agregar o actualizar producto con soporte para granel y peso unitario"""
    cursor.execute('''
        INSERT OR REPLACE INTO productos 
        (codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3, 
         stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, categoria) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3, 
          stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, categoria))
    conn.commit()

def eliminar_producto(codigo):
    cursor.execute("DELETE FROM productos WHERE codigo = ?", (codigo,))
    conn.commit()

def obtener_productos():
    df = pd.read_sql_query("SELECT * FROM productos", conn)
    if len(df) > 0:
        # Calcular ganancias estimadas para todos los tipos de precio
        df['ganancia_normal'] = df['precio_normal'] - df['precio_compra']
        df['ganancia_mayoreo_1'] = df['precio_mayoreo_1'] - df['precio_compra']
        df['ganancia_mayoreo_2'] = df['precio_mayoreo_2'] - df['precio_compra']
        df['ganancia_mayoreo_3'] = df['precio_mayoreo_3'] - df['precio_compra']
        
        # Calcular márgenes en porcentaje (evitar división por cero)
        df['margen_normal_%'] = ((df['precio_normal'] - df['precio_compra']) / df['precio_compra'].replace(0, 1) * 100).round(2)
        df['margen_mayoreo_1_%'] = ((df['precio_mayoreo_1'] - df['precio_compra']) / df['precio_compra'].replace(0, 1) * 100).round(2)
        df['margen_mayoreo_2_%'] = ((df['precio_mayoreo_2'] - df['precio_compra']) / df['precio_compra'].replace(0, 1) * 100).round(2)
        df['margen_mayoreo_3_%'] = ((df['precio_mayoreo_3'] - df['precio_compra']) / df['precio_compra'].replace(0, 1) * 100).round(2)
        
        # Calcular costo por Kg para productos por unidad con peso
        df['costo_por_kg'] = df.apply(
            lambda row: row['precio_compra'] / row['peso_unitario'] if row.get('peso_unitario', 0) > 0 else 0, 
            axis=1
        ).round(2)
        
        # Calcular valor del inventario según tipo
        df['valor_inventario_compra'] = df.apply(
            lambda row: (row['stock_kg'] * row['precio_compra']) if row.get('tipo_venta') == 'granel' 
                       else (row['stock'] * row['precio_compra']), 
            axis=1
        )
        
        df['valor_inventario_venta'] = df.apply(
            lambda row: (row['stock_kg'] * row['precio_por_kg']) if row.get('tipo_venta') == 'granel' 
                       else (row['stock'] * row['precio_normal']), 
            axis=1
        )
    return df

def calcular_precio_por_kg_sugerido(precio_compra, peso_unitario, margen_deseado=30):
    """Calcular precio por Kg sugerido basado en el peso unitario y margen"""
    if peso_unitario > 0:
        costo_por_kg = precio_compra / peso_unitario
        return costo_por_kg * (1 + margen_deseado / 100)
    return 0

def buscar_producto_por_codigo(codigo):
    """Buscar producto por código de barras o nombre (case-insensitive)"""
    try:
        # Primero buscar por código exacto
        cursor.execute("SELECT * FROM productos WHERE LOWER(codigo) = LOWER(?)", (codigo,))
        resultado = cursor.fetchone()
        
        # Si no se encuentra por código, buscar por nombre
        if not resultado:
            cursor.execute("""
                SELECT * FROM productos 
                WHERE LOWER(nombre) LIKE LOWER(?)
                ORDER BY 
                    CASE 
                        WHEN LOWER(nombre) = LOWER(?) THEN 1
                        WHEN LOWER(nombre) LIKE LOWER(?) THEN 2
                        ELSE 3
                    END
                LIMIT 1
            """, (f"%{codigo}%", codigo, f"{codigo}%"))
            resultado = cursor.fetchone()
        
        return resultado
    except Exception as e:
        print(f"Error al buscar producto: {e}")
        return None

def obtener_todos_los_productos():
    """Obtener lista de todos los productos para autocompletado"""
    try:
        cursor.execute("SELECT codigo, nombre, tipo_venta FROM productos ORDER BY nombre")
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []

def obtener_estructura_tabla():
    """Obtener la estructura real de la tabla productos"""
    try:
        cursor.execute("PRAGMA table_info(productos)")
        columnas = cursor.fetchall()
        return [col[1] for col in columnas]  # Retornar solo los nombres
    except Exception as e:
        return []

def cargar_datos_producto_con_estructura(codigo_producto):
    """Cargar datos de producto usando la estructura real de la tabla"""
    try:
        # Obtener estructura real de la tabla
        columnas = obtener_estructura_tabla()
        
        # Hacer query específico
        cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo_producto,))
        producto_data = cursor.fetchone()
        
        if not producto_data:
            return False
        
        # Crear diccionario con nombres de columnas
        producto_dict = {}
        for i, valor in enumerate(producto_data):
            if i < len(columnas):
                producto_dict[columnas[i]] = valor
        
        # Debug: verificar datos cargados
        print(f"DEBUG - Cargando producto {codigo_producto}:")
        print(f"  Precio normal RAW: {producto_dict.get('precio_normal')} (tipo: {type(producto_dict.get('precio_normal'))})")
        print(f"  Precio compra RAW: {producto_dict.get('precio_compra')} (tipo: {type(producto_dict.get('precio_compra'))})")
        print(f"  Stock RAW: {producto_dict.get('stock')} (tipo: {type(producto_dict.get('stock'))})")
        print(f"  Columnas disponibles: {list(producto_dict.keys())}")
        
        # Función auxiliar para convertir valores de forma segura
        def convertir_float_seguro(valor, default=0.0):
            if valor is None:
                return default
            if isinstance(valor, (int, float)):
                return float(valor)
            if isinstance(valor, str):
                try:
                    return float(valor) if valor.strip() else default
                except (ValueError, TypeError):
                    return default
            return default
        
        def convertir_int_seguro(valor, default=0):
            if valor is None:
                return default
            try:
                return int(valor)
            except (ValueError, TypeError):
                return default
        
        # Mapear a session_state usando nombres de columnas (mantener valores actuales)
        st.session_state.form_data = {
            'codigo': str(producto_dict.get('codigo', '')),
            'nombre': str(producto_dict.get('nombre', '')),
            'precio_compra': convertir_float_seguro(producto_dict.get('precio_compra')),
            'precio_normal': convertir_float_seguro(producto_dict.get('precio_normal')),
            'precio_mayoreo_1': convertir_float_seguro(producto_dict.get('precio_mayoreo_1')),
            'precio_mayoreo_2': convertir_float_seguro(producto_dict.get('precio_mayoreo_2')),
            'precio_mayoreo_3': convertir_float_seguro(producto_dict.get('precio_mayoreo_3')),
            'stock': convertir_int_seguro(producto_dict.get('stock')),
            'tipo_venta': str(producto_dict.get('tipo_venta', 'unidad')),
            'categoria': str(producto_dict.get('categoria', 'cremeria')),
            'precio_por_kg': convertir_float_seguro(producto_dict.get('precio_por_kg')),
            'peso_unitario': convertir_float_seguro(producto_dict.get('peso_unitario')),
            'stock_kg': convertir_float_seguro(producto_dict.get('stock_kg')),
            'stock_minimo': convertir_int_seguro(producto_dict.get('stock_minimo'), 10),
            'stock_minimo_kg': convertir_float_seguro(producto_dict.get('stock_minimo_kg')),
            'modo_edicion': True,
            'producto_original': str(producto_dict.get('codigo', ''))
        }
        
        # FORZAR LIMPIEZA DE CACHE DE STREAMLIT PARA MODO EDICIÓN
        # Limpiar cualquier key de input que pueda interferir con los valores cargados
        keys_form_input = [
            "precio_compra_input", 
            "precio_normal_input", 
            "precio_por_kg_input",
            "peso_unitario_input",
            "stock_input",
            "stock_minimo_input",
            "tipo_venta_selector_principal",
            "categoria_selector_principal"
        ]
        
        for key in keys_form_input:
            if key in st.session_state:
                del st.session_state[key]
        
        # Debug: verificar datos mapeados
        print(f"DEBUG - Datos mapeados al session_state:")
        print(f"  Precio normal: {st.session_state.form_data['precio_normal']}")
        print(f"  Precio compra: {st.session_state.form_data['precio_compra']}")
        print(f"  Stock: {st.session_state.form_data['stock']}")
        print(f"  Tipo venta: {st.session_state.form_data['tipo_venta']}")
        print(f"  Categoría: {st.session_state.form_data['categoria']}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error al cargar producto: {e}")
        return False

def mostrar():
    st.title("🏪 Gestión de Productos")
    
    # === CONTROL DE ACCESO ADMINISTRATIVO ===
    es_admin = verificar_sesion_admin()
    
    # Mostrar estado de sesión y controles
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        if es_admin:
            st.success(f"✅ **Modo Administrador** - Usuario: {st.session_state.get('usuario_admin', 'admin')} | Permisos de edición activos")
        else:
            st.info("👀 **Modo Solo Lectura** - Los productos se muestran en modo consulta únicamente")
    
    with col_header2:
        if es_admin:
            if st.button("🚪 Cerrar Sesión", type="secondary"):
                cerrar_sesion_admin()
                st.success("✅ Sesión cerrada exitosamente")
                time.sleep(1)
                st.rerun()
        else:
            if st.button("🔑 Iniciar Sesión Admin", type="primary"):
                st.session_state.mostrar_login = True
                st.rerun()
    
    # Mostrar formulario de login si se solicita
    if not es_admin and st.session_state.get('mostrar_login', False):
        mostrar_formulario_login()
        st.markdown("---")
        
        # Botón para cancelar login
        col_cancel = st.columns([1, 2, 1])
        with col_cancel[1]:
            if st.button("❌ Cancelar Login", type="secondary"):
                st.session_state.mostrar_login = False
                st.rerun()
        
        # No mostrar el resto del contenido mientras se muestra el login
        return
    
    # Información sobre credenciales por defecto (solo si no es admin)
    if not es_admin and admin_creado:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                    padding: 1rem; border-radius: 10px; margin: 1rem 0; 
                    border-left: 5px solid #28a745;">
            <h4 style="color: #155724; margin-bottom: 0.5rem;">🔑 Credenciales de Administrador por Defecto:</h4>
            <p style="color: #155724; margin: 0;">
                <strong>Usuario:</strong> <code>admin</code><br>
                <strong>Contraseña:</strong> <code>cremeria123</code>
            </p>
        </div>
        """, unsafe_allow_html=True)

    # CSS para cambio automático
    st.markdown("""
    <style>
    .tipo-venta-info {
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        font-weight: bold;
        text-align: center;
    }
    .info-unidad {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #1565c0;
        border: 2px solid #2196f3;
    }
    .info-granel {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        color: #2e7d32;
        border: 2px solid #4caf50;
    }
    </style>
    """, unsafe_allow_html=True)

    # Inicializar session_state para mantener valores del formulario
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'codigo': '',
            'nombre': '',
            'precio_compra': 0.0,
            'tipo_venta': 'unidad',
            'categoria': 'cremeria',
            'precio_normal': 0.0,
            'precio_mayoreo_1': 0.0,
            'precio_mayoreo_2': 0.0,
            'precio_mayoreo_3': 0.0,
            'peso_unitario': 0.0,
            'precio_por_kg': 0.0,
            'stock': 0,
            'stock_minimo': 10,
            'stock_minimo_kg': 0.0,
            'stock_kg': 0.0,
            'modo_edicion': False,
            'producto_original': ''
        }
    
    # Variables para controlar la recarga
    if 'producto_cargado' not in st.session_state:
        st.session_state.producto_cargado = False
    
    # Función para limpiar formulario
    def limpiar_formulario():
        st.session_state.form_data = {
            'codigo': '',
            'nombre': '',
            'precio_compra': 0.0,
            'tipo_venta': 'unidad',
            'categoria': 'cremeria',
            'precio_normal': 0.0,
            'precio_mayoreo_1': 0.0,
            'precio_mayoreo_2': 0.0,
            'precio_mayoreo_3': 0.0,
            'peso_unitario': 0.0,
            'precio_por_kg': 0.0,
            'stock': 0,
            'stock_minimo': 10,
            'stock_minimo_kg': 0.0,
            'stock_kg': 0.0,
            'modo_edicion': False,
            'producto_original': ''
        }
        st.session_state.producto_cargado = False

    # SECCIÓN DE BÚSQUEDA Y AUTOCOMPLETADO (Solo admins pueden editar)
    if es_admin:
        st.subheader("🔍 Buscar Producto para Editar")
    else:
        st.subheader("🔍 Buscar Producto (Solo Consulta)")
    
    # Obtener lista de productos para autocompletado
    productos_lista = obtener_todos_los_productos()
    opciones_productos = ["Seleccionar producto..."] + [f"{prod[0]} - {prod[1]} ({'🏷️' if prod[2] == 'unidad' else '⚖️'})" for prod in productos_lista]
    
    col_buscar1, col_buscar2 = st.columns(2)
    
    with col_buscar1:
        # Usar el índice para mantener la selección
        indice_seleccionado = 0
        if st.session_state.form_data['modo_edicion'] and st.session_state.form_data['codigo']:
            # Buscar el índice del producto actual
            for i, opcion in enumerate(opciones_productos):
                if st.session_state.form_data['codigo'] in opcion:
                    indice_seleccionado = i
                    break
        
        producto_seleccionado = st.selectbox(
            "🔍 Seleccionar producto existente:",
            opciones_productos,
            index=indice_seleccionado,
            help="Selecciona un producto para editarlo (🏷️=Unidad | ⚖️=Granel)"
        )
        
        # Procesar selección
        if producto_seleccionado and producto_seleccionado != "Seleccionar producto...":
            codigo_seleccionado = producto_seleccionado.split(" - ")[0]
            
            # Solo cargar si es diferente al actual o no hay producto cargado
            if (not st.session_state.producto_cargado or 
                st.session_state.form_data['codigo'] != codigo_seleccionado):
                
                if cargar_datos_producto_con_estructura(codigo_seleccionado):
                    st.session_state.producto_cargado = True
                    if es_admin:
                        st.success(f"✅ Producto cargado para edición: {st.session_state.form_data['nombre']}")
                        st.info(f"💰 Precios cargados - Normal: ${st.session_state.form_data['precio_normal']:.2f}, Compra: ${st.session_state.form_data['precio_compra']:.2f}")
                        
                        # Limpiar TODOS los keys de input que pueden interferir con la carga de datos
                        keys_a_limpiar = [
                            "precio_compra_input", 
                            "precio_normal_input", 
                            "precio_por_kg_input",
                            "peso_unitario_input",
                            "stock_input",
                            "stock_minimo_input"
                        ]
                        for key in keys_a_limpiar:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.info(f"📋 Producto cargado (solo lectura): {st.session_state.form_data['nombre']}")
                else:
                    st.error("❌ Error al cargar el producto seleccionado")
    
    with col_buscar2:
        if es_admin:
            if st.button("🆕 Nuevo Producto", type="secondary"):
                limpiar_formulario()
                st.success("🆕 Formulario limpio para nuevo producto")
                st.rerun()
        else:
            if st.button("🔒 Nuevo Producto (Requiere Admin)", type="secondary", disabled=True):
                pass
            st.caption("⚠️ Función disponible solo para administradores")

    # Mostrar modo actual
    if st.session_state.form_data['modo_edicion']:
        st.info(f"✏️ **MODO EDICIÓN** - Editando: {st.session_state.form_data['nombre']} (Código: {st.session_state.form_data['codigo']})")
        
        # Mostrar datos cargados para verificar
        with st.expander("📋 Datos cargados del producto", expanded=True):
            col_debug1, col_debug2 = st.columns(2)
            with col_debug1:
                st.write(f"**Código:** {st.session_state.form_data['codigo']}")
                st.write(f"**Nombre:** {st.session_state.form_data['nombre']}")
                st.write(f"**Tipo:** {st.session_state.form_data['tipo_venta']}")
                st.write(f"**Precio compra:** ${st.session_state.form_data['precio_compra']:.2f}")
            with col_debug2:
                st.write(f"**Precio normal:** ${st.session_state.form_data['precio_normal']:.2f}")
                st.write(f"**Stock:** {st.session_state.form_data['stock']} unidades")
                if st.session_state.form_data['tipo_venta'] == 'granel':
                    st.write(f"**Peso unitario:** {st.session_state.form_data['peso_unitario']:.3f} Kg")
                    st.write(f"**Precio por Kg:** ${st.session_state.form_data['precio_por_kg']:.2f}")
    else:
        st.info("🆕 **MODO CREACIÓN** - Agregando nuevo producto")

    st.subheader("➕ Agregar / Editar Producto")
    
    # *** SELECTOR DE TIPO DE VENTA FUERA DEL FORMULARIO ***
    col_tipo_venta_pre = st.columns([1, 2, 1])
    with col_tipo_venta_pre[1]:
        st.markdown("### ⚖️ Paso 1: Selecciona el Tipo de Venta")
        
        # Selector de tipo de venta FUERA del formulario para detectar cambios
        tipo_venta_index = 0 if st.session_state.form_data['tipo_venta'] == 'unidad' else 1
        tipo_venta_seleccionado = st.selectbox(
            "Tipo de Venta:",
            ["unidad", "granel"],
            index=tipo_venta_index,
            help="Unidad: se vende por piezas | Granel: se vende por peso",
            disabled=st.session_state.form_data['modo_edicion'] or not es_admin,  # Deshabilitar si no es admin o está en edición
            key="tipo_venta_selector_principal"
        )
        
        # Mostrar mensaje para usuarios no admin
        if not es_admin:
            st.info("ℹ️ Tipo de venta en modo solo lectura - Se requiere acceso de administrador para modificar")
        
        # *** DETECTAR CAMBIO Y ACTUALIZAR AUTOMÁTICAMENTE ***
        if tipo_venta_seleccionado != st.session_state.form_data['tipo_venta'] and es_admin:
            st.session_state.form_data['tipo_venta'] = tipo_venta_seleccionado
            

                
            st.rerun()
        


    # *** SELECTOR DE CATEGORÍA FUERA DEL FORMULARIO ***
    col_categoria_pre = st.columns([1, 2, 1])
    with col_categoria_pre[1]:
        st.markdown("### 🏪 Paso 2: Selecciona la Categoría del Producto")
        
        # Selector de categoría FUERA del formulario para detectar cambios
        opciones_categoria = ['cremeria', 'abarrotes', 'otros']
        categoria_index = opciones_categoria.index(st.session_state.form_data['categoria']) if st.session_state.form_data['categoria'] in opciones_categoria else 0
        categoria_seleccionada = st.selectbox(
            "Categoría del Producto:",
            opciones_categoria,
            index=categoria_index,
            format_func=lambda x: {'cremeria': '🥛 Cremería', 'abarrotes': '🛒 Abarrotes', 'otros': '📦 Otros'}[x],
            help="Selecciona la categoría del producto para mejor organización",
            disabled=not es_admin,  # Solo admins pueden cambiar categoría
            key="categoria_selector_principal"
        )
        
        # Mostrar mensaje para usuarios no admin
        if not es_admin:
            st.info("ℹ️ Categoría en modo solo lectura - Se requiere acceso de administrador para modificar")
        
        # *** DETECTAR CAMBIO Y ACTUALIZAR AUTOMÁTICAMENTE ***
        if categoria_seleccionada != st.session_state.form_data['categoria'] and es_admin:
            st.session_state.form_data['categoria'] = categoria_seleccionada
            st.rerun()

    st.markdown("---")
    

    
    # === CONTROL DE ACCESO PARA EDICIÓN ===
    if es_admin:
        st.markdown("### 📝 Paso 3: Completa la Información del Producto")
    else:
        st.markdown("### 📋 Información del Producto (Solo Lectura)")
        st.warning("⚠️ **Modo Solo Lectura** - Para editar productos necesitas iniciar sesión como administrador")



    # VERIFICACIÓN FINAL ANTES DEL FORMULARIO
    def verificar_y_sincronizar_valores():
        """Verificar que los valores del session_state estén correctamente disponibles para el formulario"""
        if st.session_state.form_data['modo_edicion']:
            # Si estamos en modo edición, asegurar que los valores no sean 0 cuando deberían tener datos
            if st.session_state.form_data['codigo'] and not st.session_state.form_data['nombre']:
                st.error("❌ Error: Datos del producto no cargados correctamente. Selecciona el producto nuevamente.")
                return False
        return True
    
    # Ejecutar verificación
    if not verificar_y_sincronizar_valores():
        st.stop()
    
    # Formulario principal - USAR VALORES DEL SESSION STATE
    with st.form("form_producto", clear_on_submit=False):
        # Usar el tipo de venta del session_state (ya actualizado arriba)
        tipo_venta = st.session_state.form_data['tipo_venta']
        categoria = st.session_state.form_data['categoria']
        
        col_basico1, col_basico2 = st.columns(2)
        
        with col_basico1:
            # Campo código - usar valor del session state
            codigo = st.text_input(
                "📦 Código de Barras", 
                value=st.session_state.form_data['codigo'],
                help="Código único del producto",
                disabled=st.session_state.form_data['modo_edicion'] or not es_admin  # Deshabilitar si no es admin o está en edición
            )
            
            nombre = st.text_input(
                "🏷️ Nombre del Producto",
                value=st.session_state.form_data['nombre'],
                disabled=not es_admin
            )
        
        with col_basico2:
            # El label del precio de compra cambia según el tipo de producto
            if st.session_state.form_data['tipo_venta'] == 'granel':
                precio_compra_label = "💰 Precio de Compra por Kg"
                precio_compra_help = "Precio al que compras cada kilogramo del producto"
            else:
                precio_compra_label = "💰 Precio de Compra por Unidad"
                precio_compra_help = "Precio al que compraste cada unidad del producto"
                
            precio_compra = st.number_input(
                precio_compra_label, 
                min_value=0.0, 
                step=0.01,
                value=float(st.session_state.form_data.get('precio_compra', 0.0)),
                help=precio_compra_help,
                disabled=not es_admin
            )
            
            # Sincronizar con session_state para mantener el valor
            if precio_compra != st.session_state.form_data['precio_compra']:
                st.session_state.form_data['precio_compra'] = precio_compra
            
            # Mostrar el tipo seleccionado (solo lectura)
            st.text_input(
                "⚖️ Tipo de Venta Seleccionado:",
                value=f"{'🏷️ Por Unidad' if tipo_venta == 'unidad' else '⚖️ A Granel'}",
                disabled=True,
                help="Para cambiar, usa el selector de arriba"
            )
        
        # CONFIGURACIÓN CONDICIONAL SEGÚN TIPO DE VENTA - RESPUESTA INMEDIATA
        if tipo_venta == "unidad":
            st.subheader("💵 Configuración de Precios por Unidad")
            
            col_precio_unit = st.columns(2)
            with col_precio_unit[0]:
                precio_normal = st.number_input(
                    "💰 Precio Normal", 
                    min_value=0.0, 
                    step=0.01,
                    value=float(st.session_state.form_data.get('precio_normal', 0.0)),
                    disabled=not es_admin
                )
                
                # Alertas de precio
                if precio_compra > 0 and precio_normal > 0:
                    margen = ((precio_normal - precio_compra) / precio_compra * 100)
                    if precio_normal <= precio_compra:
                        st.error("🚨 Precio ≤ costo. ¡Pérdidas!")
                    elif margen < 10:
                        st.warning(f"⚠️ Margen bajo: {margen:.1f}%")
                    

                if precio_compra > 0:
                    st.write("**� Guía de precios sugeridos:**")

                    

                    

            
            with col_precio_unit[1]:

                precio_mayoreo_1 = st.number_input(
                    "💼 Mayoreo Tipo 1", 
                    min_value=0.0, 
                    step=0.01,
                    value=float(st.session_state.form_data.get('precio_mayoreo_1', 0.0)),
                    disabled=not es_admin
                )
                precio_mayoreo_2 = st.number_input(
                    "💼 Mayoreo Tipo 2", 
                    min_value=0.0, 
                    step=0.01,
                    value=float(st.session_state.form_data.get('precio_mayoreo_2', 0.0)),
                    disabled=not es_admin
                )
                precio_mayoreo_3 = st.number_input(
                    "💼 Mayoreo Tipo 3", 
                    min_value=0.0, 
                    step=0.01,
                    value=float(st.session_state.form_data.get('precio_mayoreo_3', 0.0)),
                    disabled=not es_admin
                )
                

            
            # Validación de mayoreos
            if precio_compra > 0:
                for i, (nombre, precio) in enumerate([("Tipo 1", precio_mayoreo_1), ("Tipo 2", precio_mayoreo_2), ("Tipo 3", precio_mayoreo_3)]):
                    if precio > 0:
                        margen = ((precio - precio_compra) / precio_compra * 100)
                        if precio <= precio_compra:
                            st.error(f"🚨 {nombre}: ¡Pérdidas!")
                        elif margen < 5:
                            st.warning(f"⚠️ {nombre}: Margen bajo ({margen:.1f}%)")
                        else:
                            st.success(f"✅ {nombre}: Margen {margen:.1f}%")
            
            peso_unitario = 0.0
            precio_por_kg = 0.0
            
        else:
            # PRODUCTOS A GRANEL - MOSTRAR INMEDIATAMENTE
            st.subheader("⚖️ Configuración para Producto a Granel")
            

            
            col_granel1, col_granel2 = st.columns(2)
            
            with col_granel1:
                st.write("**Información de Peso:**")
                peso_unitario = st.number_input(
                    "⚖️ Peso por Unidad (Kg)", 
                    min_value=0.0,
                    step=0.001, 
                    format="%.3f",
                    value=float(st.session_state.form_data['peso_unitario']),
                    help="Peso de cada unidad para calcular inventario total",
                    disabled=not es_admin
                )
                

            
            with col_granel2:
                
                precio_por_kg = st.number_input(
                    "⚖️ Precio de Venta por Kg", 
                    min_value=0.0,
                    step=0.01,
                    value=float(st.session_state.form_data.get('precio_por_kg', 0.0)),
                    help="Precio de venta por kilogramo",
                    disabled=not es_admin
                )
                
                # Alerta simple
                if precio_por_kg > 0 and precio_compra > 0 and precio_por_kg <= precio_compra:
                    st.error("� Precio ≤ costo")
                

                
                # Guía de márgenes rápidos para granel
                if precio_compra > 0:
                    st.write("**� Guía de precios sugeridos:**")
                    col_margen_granel = st.columns(4)
                    margenes = [25, 30, 35, 40]
                    
                    for i, margen in enumerate(margenes):
                        with col_margen_granel[i]:
                            # Cálculo directo: precio compra por kg + margen (SIN dividir por peso)
                            precio_venta_sugerido = precio_compra * (1 + margen / 100)
                            st.info(f"**{margen}%**\n${precio_venta_sugerido:.2f}/Kg")
                    
                    st.caption(f"💡 **Cálculo directo:** ${precio_compra:.2f}/Kg (compra) + margen = precio de venta sugerido")
                
                # *** ALERTAS DE VALIDACIÓN DE PRECIOS PARA GRANEL ***
                # Comparación directa: precio compra/kg vs precio venta/kg
                if precio_compra > 0 and precio_por_kg > 0:
                    margen_granel = ((precio_por_kg - precio_compra) / precio_compra * 100)
                    
                    with alert_granel_container.container():
                        # Alertas simples y directas (comparación directa por kg)
                        if precio_por_kg <= precio_compra:
                            st.error("🚨 **¡ALERTA CRÍTICA!** El precio de venta por Kg es menor o igual al precio de compra por Kg. ¡Tendrás pérdidas!")
                        elif margen_granel < 10:
                            st.warning("⚠️ **¡MARGEN BAJO!** El margen de ganancia es menor al 10%. Se recomienda revisar el precio.")
            
            # Mostrar precios de mayoreo automáticos para granel
            if precio_por_kg > 0:

            
            # CONFIGURAR PRECIOS PARA PRODUCTOS A GRANEL
            precio_normal = precio_por_kg
            precio_mayoreo_1 = precio_por_kg * 0.95 if precio_por_kg > 0 else 0
            precio_mayoreo_2 = precio_por_kg * 0.90 if precio_por_kg > 0 else 0
            precio_mayoreo_3 = precio_por_kg * 0.85 if precio_por_kg > 0 else 0

        # CONFIGURACIÓN DE INVENTARIO
        st.subheader("📦 Configuración de Inventario")
        
        col_inv1, col_inv2 = st.columns(2)
        
        with col_inv1:
            stock = st.number_input(
                "📦 Stock Inicial (unidades)", 
                min_value=0, 
                step=1,
                value=int(st.session_state.form_data['stock']),
                disabled=not es_admin
            )
            
            stock_minimo = st.number_input(
                "⚠️ Stock Mínimo (unidades)", 
                min_value=0, 
                step=1,
                value=int(st.session_state.form_data['stock_minimo']),
                disabled=not es_admin
            )
        
        with col_inv2:
            if tipo_venta == "granel":
                # Calcular stock_kg automáticamente si hay peso_unitario
                if peso_unitario > 0:
                    stock_kg_calculado = stock * peso_unitario
                    st.info(f"📊 **Stock calculado:** {stock_kg_calculado:.3f} Kg")
                    stock_kg = stock_kg_calculado
                else:
                    stock_kg = st.number_input(
                        "⚖️ Stock en Kilogramos", 
                        min_value=0.0, 
                        step=0.001, 
                        format="%.3f",
                        value=float(st.session_state.form_data['stock_kg']),
                        disabled=not es_admin
                    )
                
                stock_minimo_kg = st.number_input(
                    "⚠️ Stock Mínimo (Kg)", 
                    min_value=0.0, 
                    step=0.001, 
                    format="%.3f",
                    value=float(st.session_state.form_data['stock_minimo_kg']),
                    disabled=not es_admin
                )
            else:
                stock_kg = 0.0
                stock_minimo_kg = 0.0
                st.info("ℹ️ Los productos por unidad no requieren configuración de peso")

        # BOTÓN DE SUBMIT (OBLIGATORIO PARA FORMULARIOS)
        st.markdown("---")
        col_submit = st.columns([1, 2, 1])
        with col_submit[1]:
            if es_admin:
                submit_button = st.form_submit_button(
                    label=f"{'✏️ Actualizar Producto' if st.session_state.form_data['modo_edicion'] else '➕ Agregar Producto'}", 
                    type="primary",
                    width='stretch'
                )
            else:
                submit_button = st.form_submit_button(
                    label="🔒 Solo Lectura - Requiere Permisos Admin", 
                    type="secondary",
                    disabled=True,
                    width='stretch'
                )
                st.caption("⚠️ Para editar productos necesitas iniciar sesión como administrador")
        
        # PROCESAR CUANDO SE ENVÍA EL FORMULARIO (Solo admins)
        if submit_button and es_admin:
            # Validaciones básicas
            if not codigo or not nombre:
                st.error("❌ El código y nombre son obligatorios")
            elif precio_compra <= 0:
                st.error("❌ El precio de compra debe ser mayor a 0")
            elif tipo_venta == "unidad" and precio_normal <= 0:
                st.error("❌ El precio normal debe ser mayor a 0 para productos por unidad")
            elif tipo_venta == "granel" and precio_por_kg <= 0:
                st.error("❌ El precio por Kg debe ser mayor a 0 para productos a granel")
            elif tipo_venta == "granel" and peso_unitario <= 0:
                st.error("❌ El peso por unidad debe ser mayor a 0 para productos a granel")
            
            # *** VALIDACIONES DE MÁRGEN Y PRECIOS ANTES DE GUARDAR ***
            
            # Validar precios críticos (impedir guardado)
            elif tipo_venta == "unidad" and precio_normal <= precio_compra:
                st.error("🚨 **ERROR CRÍTICO:** El precio de venta es menor o igual al precio de compra. ¡No se puede guardar el producto con pérdidas!")
                st.error(f"💸 Precio de compra: ${precio_compra:.2f} | Precio de venta: ${precio_normal:.2f}")
                st.error("🔒 **Solución:** Aumenta el precio de venta por encima de ${:.2f}".format(precio_compra))
                
            elif tipo_venta == "granel" and precio_por_kg <= precio_compra:
                st.error("🚨 **ERROR CRÍTICO:** El precio por Kg es menor o igual al precio de compra. ¡No se puede guardar el producto con pérdidas!")
                st.error(f"💸 Precio de compra: ${precio_compra:.2f} | Precio por Kg: ${precio_por_kg:.2f}")
                st.error("🔒 **Solución:** Aumenta el precio por Kg por encima de ${:.2f}".format(precio_compra))
            
            # Si pasa todas las validaciones críticas, proceder a guardar
            else:
                # Verificar margen para productos por unidad (advertencia pero no bloquea)
                if tipo_venta == "unidad" and precio_compra > 0 and precio_normal > precio_compra:
                    margen_verificacion = ((precio_normal - precio_compra) / precio_compra * 100)
                    if margen_verificacion < 10:
                        st.warning("⚠️ **ADVERTENCIA DE MARGEN BAJO**")
                        st.warning(f"📉 Margen actual: {margen_verificacion:.1f}% (Recomendado: mínimo 10%)")
                        st.info("ℹ️ El producto se guardará, pero considera aumentar el precio para mejor rentabilidad.")
                        
                        # Mostrar sugerencia de precio
                        precio_sugerido = precio_compra * 1.10  # 10% de margen
                        st.info(f"💡 **Sugerencia:** Precio mínimo recomendado: ${precio_sugerido:.2f}")
                
                # Verificar margen para productos a granel (comparación directa por kg)
                if tipo_venta == "granel" and precio_compra > 0 and precio_por_kg > precio_compra:
                    margen_verificacion = ((precio_por_kg - precio_compra) / precio_compra * 100)
                    if margen_verificacion < 10:
                        st.warning("⚠️ **ADVERTENCIA DE MARGEN BAJO POR KG**")
                        st.warning(f"📉 Margen actual: {margen_verificacion:.1f}% (Recomendado: mínimo 10%)")
                        st.info(f"🔍 Compras a ${precio_compra:.2f}/Kg → Vendes a ${precio_por_kg:.2f}/Kg")
                        st.info("ℹ️ El producto se guardará, pero considera aumentar el precio para mejor rentabilidad.")
                        
                        # Mostrar sugerencia de precio por kg
                        precio_kg_sugerido = precio_compra * 1.10  # 10% de margen
                        st.info(f"💡 **Sugerencia:** Precio mínimo recomendado: ${precio_kg_sugerido:.2f}/Kg")
                
                # Proceder a guardar el producto
                try:
                    # Verificar si el código ya existe (solo para productos nuevos)
                    if not st.session_state.form_data['modo_edicion']:
                        cursor.execute("SELECT codigo FROM productos WHERE codigo = ?", (codigo,))
                        if cursor.fetchone():
                            st.error(f"❌ Ya existe un producto con el código: {codigo}")
                            st.stop()
                    
                    # Agregar o actualizar producto
                    agregar_producto(
                        codigo, nombre, precio_compra, precio_normal, 
                        precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3,
                        stock, tipo_venta, precio_por_kg, peso_unitario, 
                        stock_kg, stock_minimo, stock_minimo_kg, categoria
                    )
                    
                    # Mensaje de éxito
                    if st.session_state.form_data['modo_edicion']:
                        st.success(f"✅ Producto actualizado exitosamente: {nombre}")
                    else:
                        st.success(f"✅ Producto agregado exitosamente: {nombre}")
                    
                    # Limpiar formulario después del éxito
                    time.sleep(2)
                    limpiar_formulario()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al guardar el producto: {e}")



    # SECCIÓN DE LISTADO DE PRODUCTOS
    st.markdown("---")
    st.subheader("📋 Lista de Productos")
    
    df = obtener_productos()
    
    if len(df) > 0:
        # Filtros
        col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
        
        with col_filtro1:
            filtro_nombre = st.text_input("🔍 Buscar por nombre", placeholder="Escriba parte del nombre...")
        
        with col_filtro2:
            tipos_disponibles = ["Todos"] + list(df['tipo_venta'].unique())
            filtro_tipo = st.selectbox("📦 Filtrar por tipo", tipos_disponibles)
        
        with col_filtro3:
            categorias_disponibles = ["Todas"] + list(df['categoria'].unique()) if 'categoria' in df.columns else ["Todas"]
            filtro_categoria = st.selectbox("🏪 Filtrar por categoría", categorias_disponibles,
                format_func=lambda x: {'Todas': 'Todas', 'cremeria': '🥛 Cremería', 'abarrotes': '🛒 Abarrotes', 'otros': '📦 Otros'}.get(x, x))
        
        with col_filtro4:
            filtro_stock_bajo = st.checkbox("⚠️ Solo stock bajo")
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if filtro_nombre:
            # Usar búsqueda flexible que ignora acentos y case
            mask_flexible = df_filtrado['nombre'].apply(lambda x: busqueda_flexible(filtro_nombre, x))
            df_filtrado = df_filtrado[mask_flexible]
        
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tipo_venta'] == filtro_tipo]
        
        if filtro_categoria != "Todas" and 'categoria' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['categoria'] == filtro_categoria]
        
        if filtro_stock_bajo:
            df_filtrado = df_filtrado[
                (df_filtrado['stock'] <= df_filtrado['stock_minimo']) |
                (df_filtrado['stock_kg'] <= df_filtrado['stock_minimo_kg'])
            ]
        
        # Mostrar productos
        if len(df_filtrado) > 0:
            st.info(f"📊 Mostrando {len(df_filtrado)} de {len(df)} productos")
            
            # Configurar columnas base según permisos de administrador
            if es_admin:
                columnas_mostrar = ['codigo', 'nombre', 'categoria', 'tipo_venta', 'precio_compra', 'stock']
                st.info("👑 **Vista de Administrador:** Se muestran precios de compra")
            else:
                columnas_mostrar = ['codigo', 'nombre', 'categoria', 'tipo_venta', 'stock']
                st.info("👤 **Vista de Usuario:** Precios de compra ocultos (solo para administradores)")
            
            # Agregar columnas específicas por tipo
            for idx, row in df_filtrado.iterrows():
                if row['tipo_venta'] == 'granel':
                    if 'precio_por_kg' not in columnas_mostrar:
                        columnas_mostrar.extend(['precio_por_kg', 'peso_unitario', 'stock_kg'])
                else:
                    if 'precio_normal' not in columnas_mostrar:
                        columnas_mostrar.extend(['precio_normal', 'precio_mayoreo_1'])
                break
            
            # Preparar DataFrame para mostrar con iconos de categoría
            df_display = df_filtrado[columnas_mostrar].copy()
            if 'categoria' in df_display.columns:
                df_display['categoria'] = df_display['categoria'].map({
                    'cremeria': '🥛 Cremería',
                    'abarrotes': '🛒 Abarrotes',
                    'otros': '📦 Otros'
                }).fillna('📦 Otros')
            
            # Mostrar tabla
            st.dataframe(
                df_display.round(2),
                width='stretch',
                hide_index=True,
                column_config={
                    "categoria": st.column_config.TextColumn("🏪 Categoría", width="medium"),
                    "tipo_venta": st.column_config.TextColumn("📦 Tipo", width="small"),
                    "codigo": st.column_config.TextColumn("Código", width="medium"),
                    "nombre": st.column_config.TextColumn("Producto", width="large")
                }
            )
            
            # Botones de acción (Solo admins pueden editar/eliminar)
            if es_admin:
                st.subheader("🛠️ Acciones de Administrador")
            else:
                st.subheader("👀 Acciones (Solo Lectura)")
            
            col_accion1, col_accion2 = st.columns(2)
            
            with col_accion1:
                if es_admin:
                    codigo_editar = st.selectbox(
                        "Selecciona producto para editar:",
                        [""] + list(df_filtrado['codigo'].astype(str)),
                        format_func=lambda x: f"{x} - {df_filtrado[df_filtrado['codigo'] == x]['nombre'].iloc[0]}" if x and x in df_filtrado['codigo'].values else "Seleccionar..."
                    )
                    
                    if st.button("✏️ Editar Seleccionado", disabled=not codigo_editar):
                        if cargar_datos_producto_con_estructura(codigo_editar):
                            st.success(f"✅ Producto cargado para edición: {st.session_state.form_data['nombre']}")
                            st.rerun()
                else:
                    st.selectbox(
                        "🔒 Editar producto (Requiere Admin):",
                        ["Función deshabilitada"],
                        disabled=True
                    )
                    if st.button("🔒 Editar (Requiere Admin)", disabled=True, type="secondary"):
                        pass
                    st.caption("⚠️ Función disponible solo para administradores")
            
            with col_accion2:
                if es_admin:
                    codigo_eliminar = st.selectbox(
                        "Selecciona producto para eliminar:",
                        [""] + list(df_filtrado['codigo'].astype(str)),
                        format_func=lambda x: f"{x} - {df_filtrado[df_filtrado['codigo'] == x]['nombre'].iloc[0]}" if x and x in df_filtrado['codigo'].values else "Seleccionar...",
                        key="select_eliminar"
                    )
                    
                    if st.button("🗑️ Eliminar Seleccionado", disabled=not codigo_eliminar, type="secondary"):
                        if st.button(f"⚠️ Confirmar eliminación de {codigo_eliminar}", type="secondary", key="confirmar_eliminar"):
                            try:
                                eliminar_producto(codigo_eliminar)
                                st.success(f"✅ Producto {codigo_eliminar} eliminado exitosamente")
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al eliminar: {e}")
                else:
                    st.selectbox(
                        "🔒 Eliminar producto (Requiere Admin):",
                        ["Función deshabilitada"],
                        disabled=True,
                        key="select_eliminar_disabled"
                    )
                    if st.button("🔒 Eliminar (Requiere Admin)", disabled=True, type="secondary"):
                        pass
                    st.caption("⚠️ Función disponible solo para administradores")
        else:
            st.warning("⚠️ No se encontraron productos con los filtros aplicados")
    else:
        st.info("📦 No hay productos registrados. ¡Agrega el primero!")