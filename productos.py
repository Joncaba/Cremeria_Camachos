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
    """Crear tabla de usuarios administradores si no existe - DEPRECADA"""
    # Esta función ahora está en usuarios.py
    # Se mantiene solo para compatibilidad, pero ya no crea la tabla
    pass

def hash_password(password):
    """Crear hash de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_credenciales(usuario, password):
    """Verificar si las credenciales son correctas"""
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id FROM usuarios_admin WHERE usuario = ? AND password = ?", 
        (usuario, password_hash)
    )
    return cursor.fetchone() is not None

def crear_admin_por_defecto():
    """Crear usuario administrador por defecto si no existe - DEPRECADA"""
    # Esta función ahora está en usuarios.py
    # Se mantiene solo para compatibilidad
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

# Inicializar sistema de usuarios - DEPRECADO (ahora se usa usuarios.py)
# crear_tabla_usuarios()
# admin_creado = crear_admin_por_defecto()

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
                    stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, categoria, codigo_original=None):
    """Agregar o actualizar producto con soporte para granel y peso unitario"""
    
    # DEBUG: Imprimir valores recibidos
    print(f"\nDEBUG agregar_producto() - Valores recibidos:")
    print(f"  Código: {codigo}")
    print(f"  Nombre: {nombre}")
    print(f"  Tipo venta: {tipo_venta}")
    print(f"  Stock (unidades): {stock}")
    print(f"  Stock (kg): {stock_kg}")
    print(f"  Stock mínimo (unidades): {stock_minimo}")
    print(f"  Stock mínimo (kg): {stock_minimo_kg}")
    print(f"  Precio por kg: {precio_por_kg}")
    print(f"  Categoría: {categoria}")
    print(f"  Código original: {codigo_original}")
    
    # Si hay un código original y es diferente al nuevo, eliminar el registro antiguo
    if codigo_original and codigo_original != codigo:
        print(f"  > Eliminando registro antiguo con código: {codigo_original}")
        cursor.execute("DELETE FROM productos WHERE codigo = ?", (codigo_original,))
    
    print(f"  > Ejecutando INSERT OR REPLACE...")
    cursor.execute('''
        INSERT OR REPLACE INTO productos 
        (codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3, 
         stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, categoria) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3, 
          stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, categoria))
    
    print(f"  > Haciendo commit...")
    conn.commit()
    # Forzar flush al disco
    cursor.execute("PRAGMA wal_checkpoint(FULL)")
    print(f"  > ✅ Producto guardado exitosamente\n")

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
        
        # INICIALIZAR DIRECTAMENTE LOS KEYS DE LOS INPUTS CON LOS VALORES CARGADOS
        # Esto asegura que los inputs muestren los valores correctos en modo edición
        st.session_state['codigo_input'] = st.session_state.form_data['codigo']
        st.session_state['nombre_input'] = st.session_state.form_data['nombre']
        st.session_state['precio_compra_input'] = st.session_state.form_data['precio_compra']
        st.session_state['precio_normal_input'] = st.session_state.form_data['precio_normal']
        st.session_state['precio_por_kg_input'] = st.session_state.form_data['precio_por_kg']
        st.session_state['peso_unitario_input'] = st.session_state.form_data['peso_unitario']
        st.session_state['stock_input'] = st.session_state.form_data['stock']
        st.session_state['stock_kg_input'] = st.session_state.form_data['stock_kg']
        st.session_state['stock_minimo_input'] = st.session_state.form_data['stock_minimo']
        st.session_state['stock_minimo_kg_input'] = st.session_state.form_data['stock_minimo_kg']
        st.session_state['precio_mayoreo_1_input'] = st.session_state.form_data['precio_mayoreo_1']
        st.session_state['precio_mayoreo_2_input'] = st.session_state.form_data['precio_mayoreo_2']
        st.session_state['precio_mayoreo_3_input'] = st.session_state.form_data['precio_mayoreo_3']
        
        # IMPORTANTE: Limpiar el key del selector de tipo de venta para que tome el nuevo valor
        if 'tipo_venta_selector_principal' in st.session_state:
            del st.session_state['tipo_venta_selector_principal']
        
        # IMPORTANTE: Limpiar el key del selector de categoría para que tome el nuevo valor
        if 'categoria_selector_principal' in st.session_state:
            del st.session_state['categoria_selector_principal']
        
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
            'stock_minimo': 0,
            'stock_minimo_kg': 0.0,
            'stock_kg': 0.0,
            'modo_edicion': False,
            'producto_original': ''
        }
    
    # Inicializar los keys de los inputs si no existen (para evitar errores en primera renderización)
    if 'codigo_input' not in st.session_state:
        st.session_state['codigo_input'] = st.session_state.form_data.get('codigo', '')
    if 'nombre_input' not in st.session_state:
        st.session_state['nombre_input'] = st.session_state.form_data.get('nombre', '')
    if 'precio_compra_input' not in st.session_state:
        st.session_state['precio_compra_input'] = st.session_state.form_data.get('precio_compra', 0)
    if 'precio_normal_input' not in st.session_state:
        st.session_state['precio_normal_input'] = st.session_state.form_data.get('precio_normal', 0)
    if 'precio_por_kg_input' not in st.session_state:
        st.session_state['precio_por_kg_input'] = st.session_state.form_data.get('precio_por_kg', 0.0)
    if 'peso_unitario_input' not in st.session_state:
        st.session_state['peso_unitario_input'] = st.session_state.form_data.get('peso_unitario', 0.0)
    if 'stock_input' not in st.session_state:
        st.session_state['stock_input'] = st.session_state.form_data.get('stock', 0)
    if 'stock_kg_input' not in st.session_state:
        st.session_state['stock_kg_input'] = st.session_state.form_data.get('stock_kg', 0.0)
    if 'stock_minimo_input' not in st.session_state:
        st.session_state['stock_minimo_input'] = st.session_state.form_data.get('stock_minimo', 10)
    if 'stock_minimo_kg_input' not in st.session_state:
        st.session_state['stock_minimo_kg_input'] = st.session_state.form_data.get('stock_minimo_kg', 0.0)
    if 'precio_mayoreo_1_input' not in st.session_state:
        st.session_state['precio_mayoreo_1_input'] = st.session_state.form_data.get('precio_mayoreo_1', 0)
    if 'precio_mayoreo_2_input' not in st.session_state:
        st.session_state['precio_mayoreo_2_input'] = st.session_state.form_data.get('precio_mayoreo_2', 0)
    if 'precio_mayoreo_3_input' not in st.session_state:
        st.session_state['precio_mayoreo_3_input'] = st.session_state.form_data.get('precio_mayoreo_3', 0)
    
    # Variables para controlar la recarga
    if 'producto_cargado' not in st.session_state:
        st.session_state.producto_cargado = False
    
    # Variable para controlar cuando se limpia el formulario
    if 'limpiar_formulario_flag' not in st.session_state:
        st.session_state.limpiar_formulario_flag = False
    
    # Si se activó el flag de limpieza, ejecutar limpieza y desactivar flag
    if st.session_state.limpiar_formulario_flag:
        st.session_state.limpiar_formulario_flag = False
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
        
        # También inicializar los keys de los inputs con valores limpios
        st.session_state['codigo_input'] = ''
        st.session_state['nombre_input'] = ''
        st.session_state['precio_compra_input'] = 0
        st.session_state['precio_normal_input'] = 0
        st.session_state['precio_por_kg_input'] = 0.0
        st.session_state['peso_unitario_input'] = 0.0
        st.session_state['stock_input'] = 0
        st.session_state['stock_kg_input'] = 0.0
        st.session_state['stock_minimo_input'] = 10
        st.session_state['stock_minimo_kg_input'] = 0.0
        st.session_state['precio_mayoreo_1_input'] = 0
        st.session_state['precio_mayoreo_2_input'] = 0
        st.session_state['precio_mayoreo_3_input'] = 0
    
    # Función para limpiar formulario
    def limpiar_formulario():
        # Limpiar todas las keys de inputs que pueden mantener valores en caché
        keys_a_limpiar = [
            "codigo_input",
            "nombre_input",
            "precio_compra_input", 
            "precio_normal_input", 
            "precio_por_kg_input",
            "peso_unitario_input",
            "stock_input",
            "stock_minimo_input",
            "stock_kg_input",
            "stock_minimo_kg_input",
            "precio_mayoreo_1_input",
            "precio_mayoreo_2_input",
            "precio_mayoreo_3_input",
            "tipo_venta_selector_principal",
            "categoria_selector_principal",
            "producto_selector_busqueda"  # Agregar el selectbox de búsqueda
        ]
        for key in keys_a_limpiar:
            if key in st.session_state:
                del st.session_state[key]
        
        # Activar flag para limpiar en el siguiente ciclo
        st.session_state.limpiar_formulario_flag = True

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
            help="Selecciona un producto para editarlo (🏷️=Unidad | ⚖️=Granel)",
            key="producto_selector_busqueda"
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
        
        # DEBUG: Verificar valor en form_data
        tipo_venta_actual = st.session_state.form_data['tipo_venta']
        print(f"DEBUG - Tipo de venta en form_data: '{tipo_venta_actual}'")
        
        # Selector de tipo de venta FUERA del formulario para detectar cambios
        tipo_venta_index = 0 if tipo_venta_actual == 'unidad' else 1
        print(f"DEBUG - Índice calculado: {tipo_venta_index} (0=unidad, 1=granel)")
        
        # IMPORTANTE: No usar key cuando estamos en modo edición para forzar actualización
        if st.session_state.form_data['modo_edicion']:
            tipo_venta_seleccionado = st.selectbox(
                "Tipo de Venta:",
                ["unidad", "granel"],
                index=tipo_venta_index,
                help="Unidad: se vende por piezas | Granel: se vende por peso",
                disabled=not es_admin  # Solo deshabilitar si no es admin
            )
        else:
            tipo_venta_seleccionado = st.selectbox(
                "Tipo de Venta:",
                ["unidad", "granel"],
                index=tipo_venta_index,
                help="Unidad: se vende por piezas | Granel: se vende por peso",
                disabled=not es_admin,  # Solo deshabilitar si no es admin
                key="tipo_venta_selector_principal"
            )
        
        # Mostrar mensaje para usuarios no admin
        if not es_admin:
            st.info("ℹ️ Tipo de venta en modo solo lectura - Se requiere acceso de administrador para modificar")
        
        # DEBUG: Verificar valor seleccionado
        print(f"DEBUG - Tipo de venta seleccionado en selectbox: '{tipo_venta_seleccionado}'")
        
        # *** DETECTAR CAMBIO Y ACTUALIZAR AUTOMÁTICAMENTE ***
        if tipo_venta_seleccionado != st.session_state.form_data['tipo_venta'] and es_admin:
            print(f"DEBUG - CAMBIO DETECTADO: '{st.session_state.form_data['tipo_venta']}' -> '{tipo_venta_seleccionado}'")
            st.session_state.form_data['tipo_venta'] = tipo_venta_seleccionado
            
            # Auto-calcular precio por kg si se cambia a granel
            if tipo_venta_seleccionado == "granel":
                precio_compra = st.session_state.form_data.get('precio_compra', 0)
                if precio_compra > 0 and st.session_state.form_data['precio_por_kg'] == 0:
                    precio_sugerido = precio_compra * 1.35  # 35% de margen
                    st.session_state.form_data['precio_por_kg'] = precio_sugerido
                    st.success(f"✅ Cambiado a GRANEL - Precio por Kg auto-calculado: ${precio_sugerido:.2f}")
                else:
                    st.success("✅ Cambiado a GRANEL - Configura precio por kilogramo y peso unitario")
            else:
                st.success("✅ Cambiado a UNIDAD - Configura precio por pieza")
                
            st.rerun()
        
        # Información visual del tipo seleccionado
        if tipo_venta_seleccionado == "unidad":
            st.markdown("""
            <div class="tipo-venta-info info-unidad">
                🏷️ <strong>Producto por Unidad:</strong> Se vende por piezas individuales
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="tipo-venta-info info-granel">
                ⚖️ <strong>Producto a Granel:</strong> Se vende por peso (Kg)
            </div>
            """, unsafe_allow_html=True)

    # *** SELECTOR DE CATEGORÍA FUERA DEL FORMULARIO ***
    col_categoria_pre = st.columns([1, 2, 1])
    with col_categoria_pre[1]:
        st.markdown("### 🏪 Paso 2: Selecciona la Categoría del Producto")
        
        # Selector de categoría FUERA del formulario para detectar cambios
        opciones_categoria = ['cremeria', 'abarrotes', 'otros']
        categoria_index = opciones_categoria.index(st.session_state.form_data['categoria']) if st.session_state.form_data['categoria'] in opciones_categoria else 0
        
        # IMPORTANTE: No usar key cuando estamos en modo edición para forzar actualización
        if st.session_state.form_data['modo_edicion']:
            categoria_seleccionada = st.selectbox(
                "Categoría del Producto:",
                opciones_categoria,
                index=categoria_index,
                format_func=lambda x: {'cremeria': '🥛 Cremería', 'abarrotes': '🛒 Abarrotes', 'otros': '📦 Otros'}[x],
                help="Selecciona la categoría del producto para mejor organización",
                disabled=not es_admin  # Solo admins pueden cambiar categoría
            )
        else:
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
            categoria_nombres = {'cremeria': 'Cremería', 'abarrotes': 'Abarrotes', 'otros': 'Otros'}
            st.success(f"✅ Categoría cambiada a: {categoria_nombres[categoria_seleccionada]}")
            st.rerun()
        
        # Información visual de la categoría seleccionada
        if categoria_seleccionada == "cremeria":
            st.markdown("""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                        color: #1565c0; padding: 0.8rem; border-radius: 0.5rem; 
                        text-align: center; font-weight: bold; border: 2px solid #2196f3;">
                🥛 <strong>Productos de Cremería:</strong> Lácteos, quesos, yogurts, etc.
            </div>
            """, unsafe_allow_html=True)
        elif categoria_seleccionada == "abarrotes":
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffcc80 100%); 
                        color: #e65100; padding: 0.8rem; border-radius: 0.5rem; 
                        text-align: center; font-weight: bold; border: 2px solid #ff9800;">
                🛒 <strong>Productos de Abarrotes:</strong> Cereales, enlatados, productos secos, etc.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f3e5f5 0%, #ce93d8 100%); 
                        color: #6a1b9a; padding: 0.8rem; border-radius: 0.5rem; 
                        text-align: center; font-weight: bold; border: 2px solid #9c27b0;">
                📦 <strong>Otros Productos:</strong> Productos diversos no clasificados
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Información del Producto
    if es_admin:
        st.markdown("### 📝 Información del Producto")
    else:
        st.markdown("### 📋 Solo Lectura")
        st.warning("⚠️ Se requiere acceso de administrador para editar")



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
            # Campo código - usar key sin value (Streamlit usará el valor del session_state[key])
            codigo = st.text_input(
                "📦 Código de Barras", 
                help="Código único del producto",
                disabled=not es_admin,
                key="codigo_input"
            )
            
            nombre = st.text_input(
                "🏷️ Nombre del Producto",
                disabled=not es_admin,
                key="nombre_input"
            )
        
        with col_basico2:
            # Precio de compra solo para productos por unidad
            if tipo_venta == "unidad":
                precio_compra = st.number_input(
                    "💰 Precio de Compra", 
                    min_value=0, 
                    step=1,
                    help="Precio al que compraste el producto",
                    disabled=not es_admin,
                    key="precio_compra_input"
                )
            else:
                # Para productos a granel, el precio de compra se maneja más abajo
                precio_compra = st.session_state.form_data.get('precio_compra', 0.0)
            
            # Mostrar el tipo seleccionado (solo lectura)
            st.text_input(
                "⚖️ Tipo de Venta Seleccionado:",
                value=f"{'🏷️ Por Unidad' if tipo_venta == 'unidad' else '⚖️ A Granel'}",
                disabled=True,
                help="Para cambiar, usa el selector de arriba"
            )
        
        # CONFIGURACIÓN CONDICIONAL SEGÚN TIPO DE VENTA - RESPUESTA INMEDIATA
        if tipo_venta == "unidad":
            # PRODUCTOS POR UNIDAD
            precio_normal = st.number_input(
                "💸 Precio de Venta por Unidad", 
                min_value=0, 
                step=1,
                disabled=not es_admin,
                key="precio_normal_input"
            )
            
            # Validación simple
            precio_compra = st.session_state.get('precio_compra_input', 0)
            if precio_compra > 0 and precio_normal > 0 and precio_normal <= precio_compra:
                st.error("🚨 Precio ≤ costo")
            
            peso_unitario = 0.0
            precio_por_kg = 0.0
            
        else:
            # PRODUCTOS A GRANEL
            col_granel1, col_granel2 = st.columns(2)
            
            with col_granel1:
                precio_compra_kg = st.number_input(
                    "💰 Precio Compra por Kg", 
                    min_value=0.0,
                    step=1.00,
                    disabled=not es_admin,
                    key="precio_compra_input"
                )
            
            with col_granel2:
                precio_por_kg = st.number_input(
                    "💵 Precio Venta por Kg", 
                    min_value=0.0,
                    step=1.00,
                    disabled=not es_admin,
                    key="precio_por_kg_input"
                )
                
                if precio_compra_kg > 0 and precio_por_kg > 0 and precio_por_kg <= precio_compra_kg:
                    st.error("🚨 Precio ≤ costo")
            
            # CONFIGURAR PRECIOS PARA PRODUCTOS A GRANEL
            precio_compra = precio_compra_kg
            precio_normal = precio_por_kg
            peso_unitario = 0.0

        # SECCIÓN UNIVERSAL DE PRECIOS DE MAYOREO (Para ambos tipos de producto)
        st.write(f"**💼 Precios de Mayoreo{' por Kg' if tipo_venta == 'granel' else ''}:**")
        
        # Calcular valores sugeridos basados en el precio de venta actual
        precio_base = precio_por_kg if tipo_venta == 'granel' else precio_normal
        
        # Calcular precios sugeridos con descuentos (5%, 8%, 10%)
        if precio_base > 0:
            if tipo_venta == 'granel':
                sugerido_1 = round(precio_base * 0.95, 2)  # 5% descuento
                sugerido_2 = round(precio_base * 0.92, 2)  # 8% descuento  
                sugerido_3 = round(precio_base * 0.90, 2)  # 10% descuento
            else:
                sugerido_1 = int(precio_base * 0.95)  # 5% descuento
                sugerido_2 = int(precio_base * 0.92)  # 8% descuento
                sugerido_3 = int(precio_base * 0.90)  # 10% descuento
        else:
            sugerido_1 = sugerido_2 = sugerido_3 = 0
        
        # Auto-actualizar session_state con precios sugeridos
        # SIEMPRE recalcular en base al precio de venta actual
        if precio_base > 0:
            # Actualizar tanto en form_data como en los inputs directamente
            st.session_state.form_data['precio_mayoreo_1'] = sugerido_1
            st.session_state.form_data['precio_mayoreo_2'] = sugerido_2
            st.session_state.form_data['precio_mayoreo_3'] = sugerido_3
            
            # También actualizar los keys de los inputs para que se reflejen en el formulario
            st.session_state['precio_mayoreo_1_input'] = sugerido_1
            st.session_state['precio_mayoreo_2_input'] = sugerido_2
            st.session_state['precio_mayoreo_3_input'] = sugerido_3
        
        col_mayoreo1, col_mayoreo2, col_mayoreo3 = st.columns(3)
        
        with col_mayoreo1:
            precio_mayoreo_1 = st.number_input(
                f"💼 Mayoreo 1 (5% desc.){' (Kg)' if tipo_venta == 'granel' else ''}",
                min_value=0.0 if tipo_venta == 'granel' else 0,
                step=1.00 if tipo_venta == 'granel' else 1,
                disabled=not es_admin,
                help=f"Auto-llenado con 5% desc.: ${sugerido_1}" if precio_base > 0 else "Ingresa precio de mayoreo manualmente",
                key="precio_mayoreo_1_input"
            )
        
        with col_mayoreo2:
            precio_mayoreo_2 = st.number_input(
                f"💼 Mayoreo 2 (8% desc.){' (Kg)' if tipo_venta == 'granel' else ''}",
                min_value=0.0 if tipo_venta == 'granel' else 0,
                step=1.00 if tipo_venta == 'granel' else 1,
                disabled=not es_admin,
                help=f"Auto-llenado con 8% desc.: ${sugerido_2}" if precio_base > 0 else "Ingresa precio de mayoreo manualmente",
                key="precio_mayoreo_2_input"
            )
        
        with col_mayoreo3:
            precio_mayoreo_3 = st.number_input(
                f"💼 Mayoreo 3 (10% desc.){' (Kg)' if tipo_venta == 'granel' else ''}",
                min_value=0.0 if tipo_venta == 'granel' else 0,
                step=1.00 if tipo_venta == 'granel' else 1,
                disabled=not es_admin,
                help=f"Auto-llenado con 10% desc.: ${sugerido_3}" if precio_base > 0 else "Ingresa precio de mayoreo manualmente",
                key="precio_mayoreo_3_input"
            )
        
        # Mostrar auto-llenado en tiempo real cuando hay precio base
        # Detectar automáticamente si debe mostrar el botón (usando session_state y valores actuales)
        precio_base_session = st.session_state.form_data.get('precio_normal', 0) if tipo_venta == 'unidad' else st.session_state.form_data.get('precio_por_kg', 0)
        mostrar_auto_fill = (precio_base > 0 or precio_base_session > 0) and es_admin
        
        # FORZAR ACTUALIZACIÓN INMEDIATA DE SESSION_STATE CUANDO HAY VALORES EN LOS INPUTS
        if es_admin and not st.session_state.form_data['modo_edicion']:
            if tipo_venta == 'granel' and precio_por_kg > 0:
                st.session_state.form_data['precio_por_kg'] = precio_por_kg
                precio_base_session = precio_por_kg
                mostrar_auto_fill = True
            elif tipo_venta == 'unidad' and precio_normal > 0:
                st.session_state.form_data['precio_normal'] = precio_normal
                precio_base_session = precio_normal
                mostrar_auto_fill = True
        
        # Inicializar flag de re-aplicación de precios
        reaplicar_precios_flag = False
        
        # Inicializar variables de precios sugeridos (fuera del bloque condicional)
        sugerido_mostrar_1 = 0
        sugerido_mostrar_2 = 0
        sugerido_mostrar_3 = 0
        
        if mostrar_auto_fill:
            st.info(f"� **Precios sugeridos:** Mayoreo 1: ${sugerido_1} | Mayoreo 2: ${sugerido_2} | Mayoreo 3: ${sugerido_3}")
            
            # Calcular precios sugeridos en tiempo real usando el precio más actualizado
            precio_para_mostrar = max(precio_base, precio_base_session)
            
            # Debug: mostrar información detallada para solucionar problemas
            st.caption(f"🔍 Debug: Precio base: ${precio_base} | Session: ${precio_base_session} | Tipo: {tipo_venta} | Usando: ${precio_para_mostrar}")
            
            # IMPORTANTE: Asegurar que siempre usemos el valor del input si está disponible
            if tipo_venta == 'granel' and precio_por_kg > 0:
                precio_para_mostrar = precio_por_kg
                st.session_state.form_data['precio_por_kg'] = precio_por_kg
            elif tipo_venta == 'unidad' and precio_normal > 0:
                precio_para_mostrar = precio_normal  
                st.session_state.form_data['precio_normal'] = precio_normal
            
            if tipo_venta == 'granel':
                sugerido_mostrar_1 = round(precio_para_mostrar * 0.95, 2)
                sugerido_mostrar_2 = round(precio_para_mostrar * 0.92, 2)
                sugerido_mostrar_3 = round(precio_para_mostrar * 0.90, 2)
            else:
                sugerido_mostrar_1 = round(precio_para_mostrar * 0.95, 2)
                sugerido_mostrar_2 = round(precio_para_mostrar * 0.92, 2)
                sugerido_mostrar_3 = round(precio_para_mostrar * 0.90, 2)
            
            # Mostrar precios calculados
            st.success(f"✅ **Precios calculados:** Mayoreo 1: ${sugerido_mostrar_1} | Mayoreo 2: ${sugerido_mostrar_2} | Mayoreo 3: ${sugerido_mostrar_3}")
        elif es_admin:
            st.info("💡 **Ingresa un precio de venta** para activar el cálculo automático de precios de mayoreo")

        # CONFIGURACIÓN DE INVENTARIO
        st.subheader("📦 Configuración de Inventario")
        
        col_inv1, col_inv2 = st.columns(2)
        
        with col_inv1:
            if tipo_venta != "granel":
                stock = st.number_input(
                    "📦 Stock Inicial (unidades)", 
                    min_value=0, 
                    step=1,
                    disabled=not es_admin,
                    key="stock_input"
                )
                
                stock_minimo = st.number_input(
                    "⚠️ Stock Mínimo (unidades)", 
                    min_value=0, 
                    step=1,
                    disabled=not es_admin,
                    key="stock_minimo_input"
                )
            else:
                # Para productos a granel, mantener el stock en unidades si existe
                stock = st.session_state.form_data.get('stock', 0)
                stock_minimo = st.session_state.form_data.get('stock_minimo', 0)
        
        with col_inv2:
            if tipo_venta == "granel":
                stock_kg = st.number_input(
                    "⚖️ Stock (Kg)", 
                    min_value=0.0, 
                    step=1.0, 
                    format="%.3f",
                    disabled=not es_admin,
                    key="stock_kg_input"
                )
                
                stock_minimo_kg = st.number_input(
                    "⚠️ Stock Mínimo (Kg)", 
                    min_value=0.0, 
                    step=1.0, 
                    format="%.3f",
                    disabled=not es_admin,
                    key="stock_minimo_kg_input"
                )
            else:
                # Para productos por unidad, mantener el stock en kg si existe
                stock_kg = st.session_state.form_data.get('stock_kg', 0.0)
                stock_minimo_kg = st.session_state.form_data.get('stock_minimo_kg', 0.0)
        
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
        
        # DEBUG: Verificar estado del botón
        print(f"\n=== DEBUG BOTÓN ===")
        print(f"submit_button presionado: {submit_button}")
        print(f"es_admin: {es_admin}")
        print(f"Ambos TRUE: {submit_button and es_admin}")
        
        # PROCESAR CUANDO SE ENVÍA EL FORMULARIO (Solo admins)
        if submit_button and es_admin:
            print(f"\n>>> ENTRANDO AL BLOQUE DE PROCESAMIENTO <<<\n")
            
            # Leer valores básicos desde session_state (los keys del formulario)
            codigo = st.session_state.get('codigo_input', '')
            nombre = st.session_state.get('nombre_input', '')
            precio_compra = st.session_state.get('precio_compra_input', 0)
            precio_mayoreo_1 = st.session_state.get('precio_mayoreo_1_input', 0)
            precio_mayoreo_2 = st.session_state.get('precio_mayoreo_2_input', 0)
            precio_mayoreo_3 = st.session_state.get('precio_mayoreo_3_input', 0)
            
            # IMPORTANTE: Leer tipo_venta y categoria del form_data actualizado
            tipo_venta_submit = st.session_state.form_data['tipo_venta']
            categoria = st.session_state.form_data['categoria']
            
            # Leer valores según tipo de venta
            if tipo_venta_submit == "unidad":
                precio_normal = st.session_state.get('precio_normal_input', 0)
                stock = st.session_state.get('stock_input', 0)
                stock_minimo = st.session_state.get('stock_minimo_input', 10)
                stock_kg = 0.0
                stock_minimo_kg = 0.0
                peso_unitario = 0.0
                precio_por_kg = 0.0
            else:  # granel
                precio_por_kg = st.session_state.get('precio_por_kg_input', 0.0)
                # IMPORTANTE: Para productos a granel, precio_normal debe ser igual a precio_por_kg
                # Esto permite que ambos campos muestren el mismo valor de venta
                precio_normal = precio_por_kg
                stock = 0
                stock_minimo = 0
                stock_kg = st.session_state.get('stock_kg_input', 0.0)
                stock_minimo_kg = st.session_state.get('stock_minimo_kg_input', 0.0)
                peso_unitario = 0.0
            
            # DEBUG: Imprimir valores antes de guardar
            print(f"DEBUG SUBMIT - Producto: {nombre}")
            print(f"  Tipo venta: {tipo_venta_submit}")
            print(f"  Stock (unidades): {stock}")
            print(f"  Stock (kg): {stock_kg}")
            print(f"  Stock mínimo (unidades): {stock_minimo}")
            print(f"  Stock mínimo (kg): {stock_minimo_kg}")
            print(f"  Categoria: {categoria}")
            
            # Validaciones básicas
            if not codigo or not nombre:
                st.error("❌ El código y nombre son obligatorios")
            elif precio_compra <= 0:
                st.error("❌ El precio de compra debe ser mayor a 0")
            elif tipo_venta_submit == "unidad" and precio_normal <= 0:
                st.error("❌ El precio normal debe ser mayor a 0 para productos por unidad")
            elif tipo_venta_submit == "granel" and precio_por_kg <= 0:
                st.error("❌ El precio por Kg debe ser mayor a 0 para productos a granel")
            
            # *** VALIDACIONES DE MÁRGEN Y PRECIOS ANTES DE GUARDAR ***
            
            # Validar precios críticos (impedir guardado)
            elif tipo_venta_submit == "unidad" and precio_normal <= precio_compra:
                st.error("🚨 **ERROR CRÍTICO:** El precio de venta es menor o igual al precio de compra. ¡No se puede guardar el producto con pérdidas!")
                st.error(f"💸 Precio de compra: ${precio_compra:.2f} | Precio de venta: ${precio_normal:.2f}")
                st.error("🔒 **Solución:** Aumenta el precio de venta por encima de ${:.2f}".format(precio_compra))
                
            elif tipo_venta_submit == "granel" and precio_por_kg <= precio_compra:
                st.error("🚨 **ERROR CRÍTICO:** El precio por Kg es menor o igual al precio de compra. ¡No se puede guardar el producto con pérdidas!")
                st.error(f"💸 Precio de compra: ${precio_compra:.2f} | Precio por Kg: ${precio_por_kg:.2f}")
                st.error("🔒 **Solución:** Aumenta el precio por Kg por encima de ${:.2f}".format(precio_compra))
            
            # Si pasa todas las validaciones críticas, proceder a guardar
            else:
                # Verificar margen para productos por unidad (advertencia pero no bloquea)
                if tipo_venta_submit == "unidad" and precio_compra > 0 and precio_normal > precio_compra:
                    margen_verificacion = ((precio_normal - precio_compra) / precio_compra * 100)
                    if margen_verificacion < 10:
                        st.warning("⚠️ **ADVERTENCIA DE MARGEN BAJO**")
                        st.warning(f"📉 Margen actual: {margen_verificacion:.1f}% (Recomendado: mínimo 10%)")
                        st.info("ℹ️ El producto se guardará, pero considera aumentar el precio para mejor rentabilidad.")
                        
                        # Mostrar sugerencia de precio
                        precio_sugerido = precio_compra * 1.10  # 10% de margen
                        st.info(f"💡 **Sugerencia:** Precio mínimo recomendado: ${precio_sugerido:.2f}")
                
                # Verificar margen para productos a granel (advertencia pero no bloquea)
                if tipo_venta_submit == "granel" and precio_compra > 0 and precio_por_kg > precio_compra:
                    margen_verificacion = ((precio_por_kg - precio_compra) / precio_compra * 100)
                    if margen_verificacion < 10:
                        st.warning("⚠️ **ADVERTENCIA DE MARGEN BAJO**")
                        st.warning(f"📉 Margen actual: {margen_verificacion:.1f}% (Recomendado: mínimo 10%)")
                        st.info("ℹ️ El producto se guardará, pero considera aumentar el precio para mejor rentabilidad.")
                        
                        # Mostrar sugerencia de precio
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
                    
                    # Agregar o actualizar producto (usar tipo_venta_submit)
                    codigo_original = st.session_state.form_data.get('producto_original', None) if st.session_state.form_data['modo_edicion'] else None
                    
                    agregar_producto(
                        codigo, nombre, precio_compra, precio_normal, 
                        precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3,
                        stock, tipo_venta_submit, precio_por_kg, peso_unitario, 
                        stock_kg, stock_minimo, stock_minimo_kg, categoria, codigo_original
                    )
                    
                    # IMPORTANTE: Limpiar TODOS los cachés de Streamlit para que otras páginas vean los cambios
                    st.cache_data.clear()
                    
                    # Mensaje de éxito
                    if st.session_state.form_data['modo_edicion']:
                        st.success(f"✅ Producto actualizado exitosamente: {nombre}")
                        st.info("� Los cambios se han guardado. Puedes continuar editando o buscar otro producto.")
                        # NO recargamos, mantenemos los valores que el usuario acaba de guardar
                        # Los valores ya están en form_data y en los inputs
                    else:
                        st.success(f"✅ Producto agregado exitosamente: {nombre}")
                        # Solo limpiar formulario cuando se agrega un producto nuevo
                        time.sleep(2)
                        limpiar_formulario()
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al guardar el producto: {e}")
                    import traceback
                    st.error(f"Detalles del error: {traceback.format_exc()}")

    # SECCIÓN DE LISTADO DE PRODUCTOS
    st.markdown("---")
    
    # Header con título y botón de refrescar
    col_header_lista1, col_header_lista2 = st.columns([4, 1])
    
    with col_header_lista1:
        st.subheader("📋 Lista de Productos")
    
    with col_header_lista2:
        if st.button("🔄 Refrescar Lista", key="refresh_productos", help="Actualizar datos desde la base de datos"):
            # Limpiar caché y forzar recarga
            st.cache_data.clear()
            st.rerun()
    
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
            
            # Crear columna de stock unificada
            df_filtrado['stock_display'] = df_filtrado.apply(
                lambda row: f"{row['stock_kg']:.2f} kg" if row['tipo_venta'] == 'granel' else f"{row['stock']} unid.",
                axis=1
            )
            
            # Crear DataFrame para mostrar con el orden solicitado:
            # Producto, Categoría, Tipo, Precio Normal, Stock, Precios Mayoreo, Precio Compra
            if es_admin:
                # Vista de administrador: muestra precio de compra
                df_display = df_filtrado[[
                    'codigo', 'nombre', 'categoria', 'tipo_venta', 
                    'precio_normal', 'stock_display',
                    'precio_mayoreo_1', 'precio_mayoreo_2', 'precio_mayoreo_3',
                    'precio_compra'
                ]].copy()
                st.info("👑 **Vista de Administrador:** Se muestran todos los precios incluyendo compra")
            else:
                # Vista de usuario: oculta precio de compra
                df_display = df_filtrado[[
                    'codigo', 'nombre', 'categoria', 'tipo_venta', 
                    'precio_normal', 'stock_display',
                    'precio_mayoreo_1', 'precio_mayoreo_2', 'precio_mayoreo_3'
                ]].copy()
                st.info("👤 **Vista de Usuario:** Precios de compra ocultos")
            
            # Formatear categoría con iconos
            df_display['categoria'] = df_display['categoria'].map({
                'cremeria': '🥛 Cremería',
                'abarrotes': '🛒 Abarrotes',
                'otros': '📦 Otros'
            }).fillna('📦 Otros')
            
            # Formatear tipo de venta con iconos
            df_display['tipo_venta'] = df_display['tipo_venta'].map({
                'unidad': '🏷️ Unidad',
                'granel': '⚖️ Granel'
            })
            
            # Configuración de columnas
            column_config = {
                "codigo": st.column_config.TextColumn("Código", width="small"),
                "nombre": st.column_config.TextColumn("Producto", width="medium"),
                "categoria": st.column_config.TextColumn("🏪 Categoría", width="medium"),
                "tipo_venta": st.column_config.TextColumn("Tipo", width="small"),
                "precio_normal": st.column_config.NumberColumn("💵 Precio Venta", format="$%.2f", width="small"),
                "stock_display": st.column_config.TextColumn("📦 Stock", width="small"),
                "precio_mayoreo_1": st.column_config.NumberColumn("💼 Mayoreo 1", format="$%.2f", width="small"),
                "precio_mayoreo_2": st.column_config.NumberColumn("💼 Mayoreo 2", format="$%.2f", width="small"),
                "precio_mayoreo_3": st.column_config.NumberColumn("💼 Mayoreo 3", format="$%.2f", width="small"),
            }
            
            # Agregar precio de compra solo si es admin
            if es_admin:
                column_config["precio_compra"] = st.column_config.NumberColumn("💰 Precio Compra", format="$%.2f", width="small")
            
            # Mostrar tabla
            st.dataframe(
                df_display,
                width='stretch',
                hide_index=True,
                column_config=column_config
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
                    # Inicializar estado de confirmación si no existe
                    if 'confirmar_eliminacion' not in st.session_state:
                        st.session_state.confirmar_eliminacion = False
                    if 'producto_a_eliminar' not in st.session_state:
                        st.session_state.producto_a_eliminar = ""
                    
                    codigo_eliminar = st.selectbox(
                        "Selecciona producto para eliminar:",
                        [""] + list(df_filtrado['codigo'].astype(str)),
                        format_func=lambda x: f"{x} - {df_filtrado[df_filtrado['codigo'] == x]['nombre'].iloc[0]}" if x and x in df_filtrado['codigo'].values else "Seleccionar...",
                        key="select_eliminar"
                    )
                    
                    # Si no hay confirmación pendiente, mostrar botón de eliminar
                    if not st.session_state.confirmar_eliminacion:
                        if st.button("🗑️ Eliminar Seleccionado", disabled=not codigo_eliminar, type="secondary"):
                            if codigo_eliminar:
                                # Activar modo confirmación
                                st.session_state.confirmar_eliminacion = True
                                st.session_state.producto_a_eliminar = codigo_eliminar
                                st.rerun()
                    
                    # Si hay confirmación pendiente, mostrar opciones de confirmación
                    if st.session_state.confirmar_eliminacion:
                        producto_nombre = df_filtrado[df_filtrado['codigo'] == st.session_state.producto_a_eliminar]['nombre'].iloc[0] if st.session_state.producto_a_eliminar in df_filtrado['codigo'].values else "Desconocido"
                        
                        st.warning(f"⚠️ ¿Confirmas eliminar: **{st.session_state.producto_a_eliminar} - {producto_nombre}**?")
                        
                        col_conf1, col_conf2 = st.columns(2)
                        
                        with col_conf1:
                            if st.button("✅ Sí, Eliminar", type="primary", key="confirmar_si"):
                                try:
                                    eliminar_producto(st.session_state.producto_a_eliminar)
                                    st.success(f"✅ Producto {st.session_state.producto_a_eliminar} eliminado exitosamente")
                                    
                                    # Limpiar estado de confirmación
                                    st.session_state.confirmar_eliminacion = False
                                    st.session_state.producto_a_eliminar = ""
                                    
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al eliminar: {e}")
                                    # Limpiar estado de confirmación en caso de error
                                    st.session_state.confirmar_eliminacion = False
                                    st.session_state.producto_a_eliminar = ""
                        
                        with col_conf2:
                            if st.button("❌ Cancelar", type="secondary", key="confirmar_no"):
                                # Limpiar estado de confirmación
                                st.session_state.confirmar_eliminacion = False
                                st.session_state.producto_a_eliminar = ""
                                st.rerun()
                
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
