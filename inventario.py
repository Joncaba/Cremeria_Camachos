import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
import openpyxl
import hashlib
import time
import unicodedata
import re

DB_PATH = "pos_cremeria.db"

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
    # Se mantiene solo para compatibilidad
    pass

def hash_password(password):
    """Crear hash de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_credenciales(usuario, password):
    """Verificar si las credenciales son correctas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    password_hash = hash_password(password)
    try:
        cursor.execute(
            "SELECT id FROM usuarios_admin WHERE usuario = ? AND password = ?", 
            (usuario, password_hash)
        )
        resultado = cursor.fetchone()
        return resultado is not None
    except Exception as e:
        print(f"Error al verificar credenciales: {e}")
        return False
    finally:
        conn.close()

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
        <h2 style="color: #8e44ad; margin-bottom: 1rem;">🔐 ACCESO ADMINISTRATIVO - INVENTARIO</h2>
        <p style="color: #2c3e50; font-size: 1.1rem; margin-bottom: 0;">
            Para gestionar configuraciones de inventario se requiere autenticación de administrador
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form_inventario"):
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
                        st.session_state.admin_inventario_autenticado = True
                        st.session_state.usuario_admin_inventario = usuario
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
    return st.session_state.get('admin_inventario_autenticado', False)

def cerrar_sesion_admin():
    """Cerrar sesión administrativa"""
    if 'admin_inventario_autenticado' in st.session_state:
        del st.session_state.admin_inventario_autenticado
    if 'usuario_admin_inventario' in st.session_state:
        del st.session_state.usuario_admin_inventario

# Inicializar sistema de usuarios - DEPRECADO (ahora se usa usuarios.py)
# crear_tabla_usuarios()
# admin_creado = crear_admin_por_defecto()

def actualizar_base_datos_granel():
    """Migración para agregar soporte de productos a granel"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Agregar nuevas columnas para productos a granel
        cursor.execute("PRAGMA table_info(productos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'tipo_venta' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")
        if 'precio_por_kg' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN precio_por_kg REAL DEFAULT 0")
        if 'peso_unitario' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN peso_unitario REAL DEFAULT 0")
        if 'stock_kg' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN stock_kg REAL DEFAULT 0")
        if 'categoria' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'cremeria'")
        
        # Actualizar tabla de ventas
        cursor.execute("PRAGMA table_info(ventas)")
        ventas_columns = [column[1] for column in cursor.fetchall()]
        
        if 'peso_vendido' not in ventas_columns:
            cursor.execute("ALTER TABLE ventas ADD COLUMN peso_vendido REAL DEFAULT 0")
        if 'tipo_venta' not in ventas_columns:
            cursor.execute("ALTER TABLE ventas ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")
        
        conn.commit()
    except Exception as e:
        print(f"Error al actualizar base de datos granel: {e}")
        conn.rollback()
    finally:
        conn.close()

def crear_tabla_stock_minimo():
    """Crear tabla para almacenar stock mínimo si no existe"""
def crear_tabla_stock_minimo():
    """Crear tabla para almacenar stock mínimo si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Asegurar migración de granel
        actualizar_base_datos_granel()
        
        # Agregar columna stock_minimo si no existe
        cursor.execute("PRAGMA table_info(productos)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'stock_minimo' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN stock_minimo INTEGER DEFAULT 10")
            conn.commit()
        
        if 'stock_minimo_kg' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN stock_minimo_kg REAL DEFAULT 0")
            conn.commit()
        
        # Agregar columnas de stock_maximo
        if 'stock_maximo' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN stock_maximo INTEGER DEFAULT 0")
            conn.commit()
        
        if 'stock_maximo_kg' not in columns:
            cursor.execute("ALTER TABLE productos ADD COLUMN stock_maximo_kg REAL DEFAULT 0")
            conn.commit()
    except Exception as e:
        print(f"Error al crear tabla stock mínimo: {e}")
        conn.rollback()
    finally:
        conn.close()

def obtener_productos_stock_bajo():
    """Obtener productos con stock bajo (menos del 50% del stock mínimo)"""
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Asegurar que la columna existe
        crear_tabla_stock_minimo()
        
        # Porcentaje ahora se calcula respecto al stock_maximo (capacidad completa)
        # y la cantidad necesaria se calcula como (stock_maximo - stock) para rellenar a capacidad.
        query = """
        SELECT codigo, nombre, stock, stock_minimo, stock_kg, stock_minimo_kg, tipo_venta, categoria,
               CASE 
                   WHEN tipo_venta = 'granel' THEN 
                       CASE WHEN stock_maximo_kg > 0 THEN (stock_kg * 100.0 / stock_maximo_kg) ELSE 100 END
                   ELSE 
                       CASE WHEN stock_maximo > 0 THEN (stock * 100.0 / stock_maximo) ELSE 100 END
               END as porcentaje_stock,
               CASE 
                   WHEN tipo_venta = 'granel' THEN (stock_maximo_kg - stock_kg)
                   ELSE (stock_maximo - stock)
               END as cantidad_necesaria,
               precio_compra, precio_normal, precio_por_kg
        FROM productos 
        WHERE (
            (tipo_venta = 'unidad' AND stock <= (stock_minimo * 0.5) AND stock_minimo > 0) OR
            (tipo_venta = 'granel' AND stock_kg <= (stock_minimo_kg * 0.5) AND stock_minimo_kg > 0)
        )
        ORDER BY categoria, porcentaje_stock ASC
        """
        
        productos_bajo_stock = pd.read_sql_query(query, conn)
        return productos_bajo_stock
    except Exception as e:
        print(f"Error al obtener productos con stock bajo: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def actualizar_stock_minimo(codigo, nuevo_stock_minimo, nuevo_stock_minimo_kg=None):
    """Actualizar el stock mínimo de un producto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if nuevo_stock_minimo_kg is not None:
            cursor.execute("UPDATE productos SET stock_minimo = ?, stock_minimo_kg = ? WHERE codigo = ?", 
                          (nuevo_stock_minimo, nuevo_stock_minimo_kg, codigo))
        else:
            cursor.execute("UPDATE productos SET stock_minimo = ? WHERE codigo = ?", (nuevo_stock_minimo, codigo))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar stock mínimo: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def actualizar_stock_maximo(codigo, nuevo_stock_maximo, nuevo_stock_maximo_kg=None):
    """Actualizar el stock máximo de un producto"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if nuevo_stock_maximo_kg is not None:
            cursor.execute("UPDATE productos SET stock_maximo = ?, stock_maximo_kg = ? WHERE codigo = ?", 
                          (nuevo_stock_maximo, nuevo_stock_maximo_kg, codigo))
        else:
            cursor.execute("UPDATE productos SET stock_maximo = ? WHERE codigo = ?", (nuevo_stock_maximo, codigo))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar stock máximo: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def actualizar_stock_producto(codigo, nuevo_stock, nuevo_stock_kg=None):
    """Actualizar el stock actual de un producto (solo admins)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if nuevo_stock_kg is not None:
            cursor.execute("UPDATE productos SET stock = ?, stock_kg = ? WHERE codigo = ?", 
                          (nuevo_stock, nuevo_stock_kg, codigo))
        else:
            cursor.execute("UPDATE productos SET stock = ? WHERE codigo = ?", (nuevo_stock, codigo))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar stock: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def obtener_producto_individual(codigo):
    """Obtener información de un producto específico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
        producto = cursor.fetchone()
        
        if producto:
            # Obtener nombres de columnas
            cursor.execute("PRAGMA table_info(productos)")
            columnas = [col[1] for col in cursor.fetchall()]
            
            # Convertir a diccionario
            producto_dict = {}
            for i, valor in enumerate(producto):
                if i < len(columnas):
                    producto_dict[columnas[i]] = valor
            
            return producto_dict
        return None
    except Exception as e:
        print(f"Error al obtener producto: {e}")
        return None
    finally:
        conn.close()

def buscar_producto_por_codigo_o_nombre(busqueda, productos_df):
    """Buscar producto por código de barras o nombre (con autocompletado flexible)"""
    if not busqueda:
        return None
    
    busqueda_normalizada = normalizar_texto(busqueda)
    
    # Buscar por código exacto primero
    for idx, row in productos_df.iterrows():
        if normalizar_texto(row['codigo']) == busqueda_normalizada:
            return row
    
    # Buscar por nombre flexible (ignora acentos y case)
    for idx, row in productos_df.iterrows():
        if busqueda_flexible(busqueda, row['nombre']):
            return row
    
    return None

def obtener_sugerencias_productos(busqueda, productos_df, max_sugerencias=5):
    """Obtener sugerencias de productos basadas en la búsqueda flexible"""
    if not busqueda or len(busqueda) < 2:
        return []
    
    sugerencias = []
    productos_encontrados = set()
    
    # Buscar por código y nombre usando búsqueda flexible
    for _, producto in productos_df.iterrows():
        if len(sugerencias) >= max_sugerencias:
            break
        
        codigo = str(producto['codigo'])
        nombre = str(producto['nombre'])
        
        # Evitar duplicados
        if codigo in productos_encontrados:
            continue
        
        # Buscar en código o nombre con búsqueda flexible
        if (busqueda_flexible(busqueda, codigo) or 
            busqueda_flexible(busqueda, nombre)):
            
            tipo = "🏷️" if producto.get('tipo_venta', 'unidad') == 'unidad' else "⚖️"
            sugerencias.append(f"{tipo} {codigo} - {nombre}")
            productos_encontrados.add(codigo)
    
    return sugerencias

def mostrar_alertas_stock():
    """Mostrar alertas de productos con stock bajo"""
    productos_bajo_stock = obtener_productos_stock_bajo()
    
    if not productos_bajo_stock.empty:
        # Alerta crítica con animación
        st.markdown("""
        <div style="
            background-color: #ff6b6b; 
            color: white; 
            padding: 15px; 
            border-radius: 10px; 
            border: 3px solid #ff4757;
            margin: 10px 0;
            animation: pulse 2s infinite;
        ">
        <style>
        @keyframes pulse {{ 
            0% {{ box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(255, 107, 107, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }}
        }}
        </style>
        <h3>🚨 ALERTA: PRODUCTOS CON STOCK BAJO 🚨</h3>
        <p>Hay <strong>{}</strong> productos que necesitan reabastecimiento urgente</p>
        </div>
        """.format(len(productos_bajo_stock)), unsafe_allow_html=True)
        
        # Mostrar tabla de productos críticos
        st.dataframe(
            productos_bajo_stock,
            column_config={
                "codigo": "Código",
                "nombre": "Producto",
                "tipo_venta": st.column_config.SelectboxColumn("Tipo", options=["unidad", "granel"]),
                "stock": st.column_config.NumberColumn("Stock (Unidades)"),
                "stock_kg": st.column_config.NumberColumn("Stock (Kg)", format="%.2f kg"),
                "stock_minimo": st.column_config.NumberColumn("Stock Mín (Unidades)"),
                "stock_minimo_kg": st.column_config.NumberColumn("Stock Mín (Kg)", format="%.2f kg"),
                "porcentaje_stock": st.column_config.ProgressColumn(
                    "% Stock",
                    help="Porcentaje del stock actual vs stock máximo (100% = capacidad completa)",
                    min_value=0,
                    max_value=100,
                    format="%d%%"
                ),
                "cantidad_necesaria": st.column_config.NumberColumn("Cantidad Necesaria", format="%.2f"),
                "precio_compra": st.column_config.NumberColumn("Precio Compra", format="$%.2f"),
                "precio_normal": st.column_config.NumberColumn("Precio Venta", format="$%.2f"),
                "precio_por_kg": st.column_config.NumberColumn("Precio/Kg", format="$%.2f/kg")
            },
            hide_index=True,
            width="stretch"
        )
        
        # Botón para gestionar pedidos de reabastecimiento
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            st.markdown("---")
            if st.button("🛒 **IR A GESTIÓN DE PEDIDOS**", type="primary", width='stretch', key="ir_a_pedidos"):
                # Crear una alerta que se puede mostrar en el módulo de pedidos
                st.session_state.productos_para_pedido = productos_bajo_stock.to_dict('records')
                st.session_state.origen_pedido = 'inventario'
                
                st.success("✅ Productos transferidos al módulo de Pedidos")
                st.info("🎯 Ve al módulo 'Pedidos y Reabastecimiento' para crear los pedidos")
                time.sleep(2)
        
        return productos_bajo_stock
    else:
        st.success("✅ Todos los productos tienen stock suficiente")
        return pd.DataFrame()

def exportar_a_excel(productos_df, productos_bajo_stock_df):
    """Exportar datos a Excel con múltiples hojas"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja 1: Inventario completo
        productos_df.to_excel(writer, sheet_name='Inventario_Completo', index=False)
        
        # Hoja 2: Productos con stock bajo
        if not productos_bajo_stock_df.empty:
            productos_bajo_stock_df.to_excel(writer, sheet_name='Stock_Bajo_URGENTE', index=False)
            
            # Calcular totales para reabastecimiento
            resumen_compras = productos_bajo_stock_df.copy()
            resumen_compras['inversion_necesaria'] = resumen_compras['cantidad_necesaria'] * resumen_compras['precio_compra']
            resumen_compras['valor_venta_potencial'] = resumen_compras.apply(
                lambda row: row['cantidad_necesaria'] * (row['precio_por_kg'] if row['tipo_venta'] == 'granel' else row['precio_normal']), 
                axis=1
            )
            resumen_compras['ganancia_potencial'] = resumen_compras['valor_venta_potencial'] - resumen_compras['inversion_necesaria']
            
            # Hoja 3: Resumen financiero
            resumen_financiero = pd.DataFrame({
                'Concepto': [
                    'Total de productos con stock bajo',
                    'Productos por unidad',
                    'Productos a granel',
                    'Inversión total necesaria',
                    'Valor de venta potencial',
                    'Ganancia potencial estimada'
                ],
                'Valor': [
                    len(productos_bajo_stock_df),
                    len(productos_bajo_stock_df[productos_bajo_stock_df['tipo_venta'] == 'unidad']),
                    len(productos_bajo_stock_df[productos_bajo_stock_df['tipo_venta'] == 'granel']),
                    f"${resumen_compras['inversion_necesaria'].sum():.2f}",
                    f"${resumen_compras['valor_venta_potencial'].sum():.2f}",
                    f"${resumen_compras['ganancia_potencial'].sum():.2f}"
                ]
            })
            
            resumen_financiero.to_excel(writer, sheet_name='Resumen_Financiero', index=False)
            
            # Hoja 4: Lista de compras
            lista_compras = productos_bajo_stock_df[['codigo', 'nombre', 'tipo_venta', 'cantidad_necesaria', 'precio_compra']].copy()
            lista_compras['inversion_necesaria'] = lista_compras['cantidad_necesaria'] * lista_compras['precio_compra']
            lista_compras['unidad'] = lista_compras.apply(
                lambda row: 'Kg' if row['tipo_venta'] == 'granel' else 'Unidades', axis=1
            )
            lista_compras = lista_compras.rename(columns={
                'codigo': 'Código',
                'nombre': 'Producto',
                'tipo_venta': 'Tipo Venta',
                'cantidad_necesaria': 'Cantidad a Comprar',
                'precio_compra': 'Precio Unitario',
                'inversion_necesaria': 'Total por Producto',
                'unidad': 'Unidad'
            })
            lista_compras.to_excel(writer, sheet_name='Lista_de_Compras', index=False)
        
        # Configurar estilos para las hojas
        workbook = writer.book
        
        try:
            header_style = openpyxl.styles.NamedStyle(name="header")
            header_style.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            header_style.fill = openpyxl.styles.PatternFill("solid", fgColor="366092")
            
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for cell in worksheet[1]:  # Primera fila (headers)
                    cell.style = header_style
                
                # Ajustar ancho de columnas
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 5, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        except Exception as e:
            # Si hay error con los estilos, continuar sin ellos
            print(f"Advertencia: No se pudieron aplicar estilos: {e}")
    
    output.seek(0)
    return output

def mostrar():
    st.title("📦 Gestión de Inventario")
    
    # === CONTROL DE ACCESO ADMINISTRATIVO ===
    es_admin = verificar_sesion_admin()
    
    # Mostrar estado de sesión y controles
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        if es_admin:
            st.success(f"✅ **Modo Administrador** - Usuario: {st.session_state.get('usuario_admin_inventario', 'admin')} | Permisos de configuración activos")
        else:
            st.info("👀 **Modo Solo Lectura** - Inventario en modo consulta. Configuraciones restringidas.")
    
    with col_header2:
        if es_admin:
            if st.button("🚪 Cerrar Sesión", type="secondary", key="logout_inventario"):
                cerrar_sesion_admin()
                st.success("✅ Sesión cerrada exitosamente")
                time.sleep(1)
                st.rerun()
        else:
            if st.button("🔑 Acceso Admin", type="primary", key="login_inventario"):
                st.session_state.mostrar_login_inventario = True
                st.rerun()
    
    # Mostrar formulario de login si se solicita
    if not es_admin and st.session_state.get('mostrar_login_inventario', False):
        mostrar_formulario_login()
        st.markdown("---")
        
        # Botón para cancelar login
        col_cancel = st.columns([1, 2, 1])
        with col_cancel[1]:
            if st.button("❌ Cancelar Login", type="secondary", key="cancel_login_inventario"):
                st.session_state.mostrar_login_inventario = False
                st.rerun()
        
        # No mostrar el resto del contenido mientras se muestra el login
        return
    
    # Crear tabla de stock mínimo si no existe
    crear_tabla_stock_minimo()
    
    # IMPORTANTE: Forzar recarga de datos cada vez que se muestra la página
    # Esto asegura que siempre veamos los datos más recientes
    conn = sqlite3.connect(DB_PATH)
    try:
        productos_df = pd.read_sql_query("SELECT * FROM productos", conn)
    finally:
        conn.close()
    
    # Botón de recarga manual (por si acaso)
    col_refresh = st.columns([5, 1])
    with col_refresh[1]:
        if st.button("🔄 Refrescar", key="refresh_inventario"):
            st.rerun()
    
    # 1. Mostrar alertas de stock bajo
    st.subheader("🚨 Alertas de Stock")
    productos_bajo_stock = mostrar_alertas_stock()
    
    # Separador
    st.divider()
    
    # 2. Análisis Visual
    st.subheader("📊 Análisis Visual")
    
    if not productos_df.empty:
        col_grafico1, col_grafico2 = st.columns(2)
        
        with col_grafico1:
            # Gráfico de stock actual
            fig_stock = px.bar(
                productos_df.head(10), 
                x='nombre', 
                y='stock', 
                title='Stock Actual (Top 10 productos)',
                color='stock',
                color_continuous_scale='RdYlGn'
            )
            fig_stock.update_xaxes(tickangle=45)
            st.plotly_chart(fig_stock, width='stretch')
        
        with col_grafico2:
            # Gráfico de estado del stock
            if 'estado_stock' in productos_df.columns:
                # Calcular estado del stock para el gráfico
                def calcular_estado_stock(row):
                    if row.get('tipo_venta', 'unidad') == 'granel':
                        stock_actual = row.get('stock_kg', 0)
                        stock_min = row.get('stock_minimo_kg', 0)
                    else:
                        stock_actual = row.get('stock', 0)
                        stock_min = row.get('stock_minimo', 10)
                    
                    if stock_min > 0:
                        if stock_actual <= (stock_min * 0.5):
                            return '🔴 CRÍTICO'
                        elif stock_actual <= stock_min:
                            return '🟡 BAJO'
                        else:
                            return '🟢 NORMAL'
                    return '🟢 NORMAL'
                
                productos_df['estado_stock'] = productos_df.apply(calcular_estado_stock, axis=1)
                estado_counts = productos_df['estado_stock'].value_counts()
                
                if not estado_counts.empty:
                    fig_estados = px.pie(
                        values=estado_counts.values,
                        names=estado_counts.index,
                        title='Distribución del Estado del Stock',
                        color_discrete_map={
                            '🔴 CRÍTICO': '#ff4757',
                            '🟡 BAJO': '#ffa502',
                            '🟢 NORMAL': '#2ed573'
                        }
                    )
                    st.plotly_chart(fig_estados, width='stretch')
        
        # Gráfico adicional: Productos por tipo de venta
        col_grafico3, col_grafico4 = st.columns(2)
        
        with col_grafico3:
            if 'tipo_venta' in productos_df.columns:
                tipo_venta_counts = productos_df['tipo_venta'].value_counts()
                if not tipo_venta_counts.empty:
                    fig_tipos = px.bar(
                        x=tipo_venta_counts.index,
                        y=tipo_venta_counts.values,
                        title='Productos por Tipo de Venta',
                        labels={'x': 'Tipo de Venta', 'y': 'Cantidad de Productos'},
                        color=tipo_venta_counts.values,
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig_tipos, width='stretch')
        
        with col_grafico4:
            # Gráfico de valor del inventario por producto
            if 'precio_compra' in productos_df.columns:
                productos_df['valor_stock'] = productos_df['stock'] * productos_df['precio_compra']
                top_valor = productos_df.nlargest(10, 'valor_stock')
                
                if not top_valor.empty:
                    fig_valor = px.bar(
                        top_valor,
                        x='nombre',
                        y='valor_stock',
                        title='Top 10 - Valor del Stock por Producto',
                        labels={'valor_stock': 'Valor ($)', 'nombre': 'Producto'},
                        color='valor_stock',
                        color_continuous_scale='Blues'
                    )
                    fig_valor.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_valor, width='stretch')
    else:
        st.info("Agrega productos para ver análisis visual")
    
    # Separador
    st.divider()
    
    # 3. Inventario Actual
    st.subheader("📋 Inventario Actual")
    
    if not productos_df.empty:
        # Asegurar que las columnas de stock_maximo existan pero NO sobrescribir valores guardados
        # (No asignamos el stock actual como máximo automáticamente, eso causaba que el % siempre fuera 100%)
        if 'stock_maximo' not in productos_df.columns:
            productos_df['stock_maximo'] = 0
        if 'stock_maximo_kg' not in productos_df.columns:
            productos_df['stock_maximo_kg'] = 0
        
        # Agregar columnas de análisis
        def calcular_estado_stock(row):
            if row.get('tipo_venta', 'unidad') == 'granel':
                stock_actual = row.get('stock_kg', 0)
                stock_min = row.get('stock_minimo_kg', 0)
                stock_max = row.get('stock_maximo_kg', 0)
            else:
                stock_actual = row.get('stock', 0)
                stock_min = row.get('stock_minimo', 10)
                stock_max = row.get('stock_maximo', 0)
            
            if stock_max > 0:
                porcentaje = (stock_actual / stock_max) * 100
                # Calcular porcentaje mínimo
                porcentaje_min = (stock_min / stock_max) * 100 if stock_min > 0 else 20
                
                if porcentaje <= (porcentaje_min * 0.5):
                    return '🔴 CRÍTICO'
                elif porcentaje <= porcentaje_min:
                    return '🟡 BAJO'
                else:
                    return '🟢 NORMAL'
            
            # Si no hay stock máximo definido, usar lógica simple
            if stock_actual == 0:
                return '🔴 CRÍTICO'
            elif stock_min > 0 and stock_actual <= stock_min:
                return '🟡 BAJO'
            return '🟢 NORMAL'

        def calcular_porcentaje_stock(row):
            if row.get('tipo_venta', 'unidad') == 'granel':
                stock_actual = row.get('stock_kg', 0)
                stock_max = row.get('stock_maximo_kg', 0)
            else:
                stock_actual = row.get('stock', 0)
                stock_max = row.get('stock_maximo', 0)

            # Si hay un stock máximo definido, calcular porcentaje relativo a ese máximo
            if stock_max > 0:
                return ((stock_actual / stock_max) * 100)
            
            # Si no hay stock, retornar 0%
            return 0.0
        
        productos_df['estado_stock'] = productos_df.apply(calcular_estado_stock, axis=1)
        productos_df['porcentaje_stock'] = productos_df.apply(calcular_porcentaje_stock, axis=1).round(1)
        
        # Filtros para el inventario
        col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
        
        with col_filtro1:
            filtro_estado = st.selectbox(
                "🔍 Filtrar por estado:",
                ["Todos", "🔴 CRÍTICO", "🟡 BAJO", "🟢 NORMAL"],
                key="filtro_estado_inventario"
            )
        
        with col_filtro2:
            filtro_categoria = st.selectbox(
                "🏪 Filtrar por categoría:",
                ["Todas"] + (list(productos_df['categoria'].unique()) if 'categoria' in productos_df.columns else []),
                key="filtro_categoria_inventario",
                format_func=lambda x: {'Todas': 'Todas', 'cremeria': '🥛 Cremería', 'abarrotes': '🛒 Abarrotes', 'otros': '📦 Otros'}.get(x, x)
            )
        
        with col_filtro3:
            filtro_tipo = st.selectbox(
                "⚖️ Filtrar por tipo:",
                ["Todos", "unidad", "granel"],
                key="filtro_tipo_inventario"
            )
        
        with col_filtro4:
            ordenar_por = st.selectbox(
                "📊 Ordenar por:",
                ["nombre", "stock", "porcentaje_stock", "estado_stock", "precio_compra"],
                key="ordenar_inventario"
            )
        
        # Aplicar filtros
        df_filtrado = productos_df.copy()
        
        if filtro_estado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['estado_stock'] == filtro_estado]
        
        if filtro_categoria != "Todas" and 'categoria' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['categoria'] == filtro_categoria]
        
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tipo_venta'] == filtro_tipo]
        
        # Aplicar orden
        if ordenar_por == "porcentaje_stock":
            df_filtrado = df_filtrado.sort_values('porcentaje_stock', ascending=True)
        elif ordenar_por == "estado_stock":
            orden_estado = {'🔴 CRÍTICO': 0, '🟡 BAJO': 1, '🟢 NORMAL': 2}
            df_filtrado['orden_estado'] = df_filtrado['estado_stock'].map(orden_estado)
            df_filtrado = df_filtrado.sort_values('orden_estado')
            df_filtrado = df_filtrado.drop('orden_estado', axis=1)
        else:
            df_filtrado = df_filtrado.sort_values(ordenar_por, ascending=(ordenar_por != 'stock'))
        
        # Mostrar información de filtros aplicados
        st.info(f"📊 Mostrando {len(df_filtrado)} de {len(productos_df)} productos")
        
        # Agregar columnas calculadas para mejor visualización
        df_filtrado['stock_display'] = df_filtrado.apply(
            lambda row: f"{row['stock_kg']:.2f} kg" if row['tipo_venta'] == 'granel' else f"{row['stock']} unid.",
            axis=1
        )
        
        df_filtrado['stock_minimo_display'] = df_filtrado.apply(
            lambda row: f"{row['stock_minimo_kg']:.2f} kg" if row['tipo_venta'] == 'granel' else f"{row['stock_minimo']} unid.",
            axis=1
        )
        
        # Formatear categoría con iconos
        df_filtrado['categoria_display'] = df_filtrado['categoria'].map({
            'cremeria': '🥛 Cremería',
            'abarrotes': '🛒 Abarrotes',
            'otros': '📦 Otros'
        }).fillna('📦 Otros')
        
        # Formatear tipo de venta con iconos
        df_filtrado['tipo_display'] = df_filtrado['tipo_venta'].map({
            'unidad': '🏷️ Unidad',
            'granel': '⚖️ Granel'
        })
        
        # Crear DataFrame con el orden solicitado:
        # Código, Producto, Categoría, Tipo, Precio Venta, Stock, Stock Mín, % Stock, Estado, Mayoreos, Precio Compra
        df_display = df_filtrado[[
            'codigo', 'nombre', 'categoria_display', 'tipo_display',
            'precio_normal', 'stock_display', 'stock_minimo_display',
            'porcentaje_stock', 'estado_stock',
            'precio_mayoreo_1', 'precio_mayoreo_2', 'precio_mayoreo_3',
            'precio_compra'
        ]].copy()
        
        # Configuración de columnas
        column_config = {
            "codigo": st.column_config.TextColumn("Código", width="small"),
            "nombre": st.column_config.TextColumn("Producto", width="medium"),
            "categoria_display": st.column_config.TextColumn("🏪 Categoría", width="small"),
            "tipo_display": st.column_config.TextColumn("Tipo", width="small"),
            "precio_normal": st.column_config.NumberColumn("💵 Precio Venta", format="$%.2f", width="small"),
            "stock_display": st.column_config.TextColumn("📦 Stock", width="small", help="Stock actual según tipo de venta"),
            "stock_minimo_display": st.column_config.TextColumn("⚠️ Stock Mín", width="small", help="Stock mínimo según tipo de venta"),
            "porcentaje_stock": st.column_config.ProgressColumn(
                "% Stock",
                help="Porcentaje del stock actual vs stock máximo (100% = capacidad completa)",
                min_value=0,
                max_value=100,
                format="%.1f%%",
                width="small"
            ),
            "estado_stock": st.column_config.TextColumn("Estado", width="small"),
            "precio_mayoreo_1": st.column_config.NumberColumn("💼 Mayoreo 1", format="$%.2f", width="small"),
            "precio_mayoreo_2": st.column_config.NumberColumn("💼 Mayoreo 2", format="$%.2f", width="small"),
            "precio_mayoreo_3": st.column_config.NumberColumn("💼 Mayoreo 3", format="$%.2f", width="small"),
            "precio_compra": st.column_config.NumberColumn("💰 Precio Compra", format="$%.2f", width="small")
        }
        
        # Mostrar tabla ordenada
        st.dataframe(
            df_display,
            column_config=column_config,
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("No hay productos en el inventario")
    
    # Separador
    st.divider()
    
    # 4. Edición Completa de Productos (Solo admins)
    if es_admin:
        st.subheader("⚙️ Editar Productos del Inventario")
        expandir_config = True
    else:
        st.subheader("🔒 Editar Productos del Inventario (Requiere Admin)")
        expandir_config = False
    
    with st.expander("Editar cantidades, precios y configuración", expanded=expandir_config):
        if not es_admin:
            st.warning("⚠️ **Acceso Restringido** - Para editar productos necesitas iniciar sesión como administrador")
            st.info("Esta función permite editar stock actual, precios, stock mínimo y otros datos del inventario.")
        
        if not productos_df.empty and es_admin:
            st.info("⚠️ **Función de administrador:** Editar stock actual, precios y configuración de productos")
            
            # Búsqueda unificada de producto
            col_busq1, col_busq2 = st.columns([2, 1])
            
            with col_busq1:
                busqueda_unificada = st.text_input(
                    "🔍 Buscar producto:",
                    key="busqueda_unificada_inventario",
                    placeholder="Escribe el nombre del producto o escanea/escribe el código de barras...",
                    help="💡 Puedes buscar por nombre (ej: 'queso') o por código de barras (ej: '123456789')"
                )
            
            with col_busq2:
                st.write("**Opciones de búsqueda:**")
                st.caption("🏷️ Por nombre del producto")
                st.caption("📱 Por código de barras")
                st.caption("🔄 Automático según entrada")
            
            producto_info = None
            
            if busqueda_unificada and len(busqueda_unificada.strip()) >= 2:
                busqueda = busqueda_unificada.strip()
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                try:
                    # Intentar búsqueda por código de barras primero (búsqueda exacta)
                    cursor.execute("""
                        SELECT codigo, nombre, precio_normal as precio_venta, precio_compra, stock, 
                               stock_minimo, codigo as codigo_barras, 
                               CASE WHEN tipo_venta = 'granel' THEN 1 ELSE 0 END as es_granel, 
                               'General' as categoria, stock_maximo, stock_kg, stock_minimo_kg, stock_maximo_kg
                        FROM productos 
                        WHERE LOWER(codigo) = LOWER(?)
                    """, (busqueda,))
                    
                    resultado = cursor.fetchone()
                    
                    # Si no se encuentra por código, buscar por nombre (búsqueda parcial)
                    if not resultado:
                        cursor.execute("""
                            SELECT codigo, nombre, precio_normal as precio_venta, precio_compra, stock, 
                                   stock_minimo, codigo as codigo_barras, 
                                   CASE WHEN tipo_venta = 'granel' THEN 1 ELSE 0 END as es_granel,
                                   'General' as categoria, stock_maximo, stock_kg, stock_minimo_kg, stock_maximo_kg
                            FROM productos 
                            WHERE LOWER(nombre) LIKE LOWER(?) OR LOWER(nombre) = LOWER(?)
                            ORDER BY 
                                CASE 
                                    WHEN LOWER(nombre) = LOWER(?) THEN 1
                                    WHEN LOWER(nombre) LIKE LOWER(?) THEN 2
                                    ELSE 3
                                END
                            LIMIT 1
                        """, (f'%{busqueda}%', busqueda, busqueda, f'{busqueda}%'))
                        
                        resultado = cursor.fetchone()
                        
                        # Si hay múltiples coincidencias, mostrar sugerencias
                        if resultado:
                            cursor.execute("""
                                SELECT COUNT(*) 
                                FROM productos 
                                WHERE LOWER(nombre) LIKE LOWER(?)
                            """, (f'%{busqueda}%',))
                            
                            total_coincidencias = cursor.fetchone()[0]
                            
                            if total_coincidencias > 1:
                                # Mostrar otras opciones disponibles
                                cursor.execute("""
                                    SELECT nombre, codigo, 
                                           CASE WHEN tipo_venta = 'granel' THEN 1 ELSE 0 END as es_granel
                                    FROM productos 
                                    WHERE LOWER(nombre) LIKE LOWER(?)
                                    ORDER BY nombre
                                    LIMIT 5
                                """, (f'%{busqueda}%',))
                                
                                sugerencias = cursor.fetchall()
                                
                                st.info(f"🔍 Se encontraron {total_coincidencias} productos similares. Mostrando el más relevante:")
                                
                                with st.expander(f"Ver otras {len(sugerencias)-1} coincidencias", expanded=False):
                                    for sugerencia in sugerencias[1:]:  # Saltar el primero que ya se seleccionó
                                        icono = "⚖️" if sugerencia[2] else "📦"
                                        codigo_texto = f" (Código: {sugerencia[1]})" if sugerencia[1] else " (Sin código)"
                                        st.write(f"• {icono} **{sugerencia[0]}**{codigo_texto}")
                    
                    if resultado:
                        producto_info = {
                            'id': resultado[0],  # En este caso es el código
                            'codigo': resultado[0],
                            'nombre': resultado[1],
                            'precio_venta': resultado[2],
                            'precio_compra': resultado[3],
                            'stock': resultado[4],
                            'stock_minimo': resultado[5],
                            'codigo_barras': resultado[6],
                            'es_granel': bool(resultado[7]),
                            'categoria': resultado[8],
                            'stock_maximo': resultado[9] if len(resultado) > 9 else 0,
                            'stock_kg': resultado[10] if len(resultado) > 10 else 0,
                            'stock_minimo_kg': resultado[11] if len(resultado) > 11 else 0,
                            'stock_maximo_kg': resultado[12] if len(resultado) > 12 else 0
                        }
                        
                        # Indicar cómo se encontró el producto
                        if producto_info['codigo_barras'] and producto_info['codigo_barras'] == busqueda:
                            st.success(f"📱 **Encontrado por código de barras:** {producto_info['nombre']}")
                        else:
                            st.success(f"🏷️ **Encontrado por nombre:** {producto_info['nombre']}")
                            if producto_info['codigo_barras']:
                                st.caption(f"🔢 Código de barras: {producto_info['codigo_barras']}")
                    else:
                        st.error("❌ No se encontró ningún producto con esa búsqueda")
                        st.info("💡 **Sugerencias:**")
                        st.write("• Verifica que el código de barras sea correcto")
                        st.write("• Intenta con parte del nombre del producto")
                        st.write("• Revisa que el producto esté registrado en el sistema")
                        
                except Exception as e:
                    st.error(f"Error al buscar producto: {str(e)}")
                finally:
                    conn.close()
            
            # Mostrar formulario de edición completa si se encontró el producto
            if producto_info:
                st.success(f"✅ Producto encontrado: **{producto_info['nombre']}**")
                
                # Crear pestañas para diferentes tipos de edición
                tab1, tab2, tab3 = st.tabs(["📊 Stock y Cantidades", "💰 Precios", "⚙️ Configuración"])
                
                with tab1:
                    st.write("#### 📊 Gestión de Stock")
                    col1, col2, col3 = st.columns([2, 2, 2])
                    
                    with col1:
                        st.write("**Información Actual:**")
                        st.write(f"📦 Producto: {producto_info['nombre']}")
                        if producto_info['es_granel']:
                            st.write(f"📊 Stock actual: {producto_info['stock_kg']:.2f} kg")
                            st.write(f"⚠️ Stock mínimo: {producto_info['stock_minimo_kg']:.2f} kg")
                            st.write(f"� Stock máximo: {producto_info['stock_maximo_kg']:.2f} kg")
                            st.write("⚖️ Tipo: Por peso (granel)")
                        else:
                            st.write(f"📊 Stock actual: {producto_info['stock']} unid.")
                            st.write(f"⚠️ Stock mínimo: {producto_info['stock_minimo']} unid.")
                            st.write(f"📈 Stock máximo: {producto_info['stock_maximo']} unid.")
                            st.write("📦 Tipo: Por unidad")
                        st.write(f"🔢 Código: {producto_info['codigo_barras'] or 'Sin código'}")
                    
                    with col2:
                        st.write("**Editar Stock:**")
                        if producto_info['es_granel']:
                            nueva_cantidad = st.number_input(
                                "Nueva cantidad en stock (kg):",
                                min_value=0.0,
                                value=float(producto_info['stock_kg']),
                                step=0.1,
                                key="nueva_cantidad_stock_tab"
                            )
                            
                            nuevo_stock_minimo = st.number_input(
                                "Nuevo stock mínimo (kg):",
                                min_value=0.0,
                                value=float(producto_info['stock_minimo_kg']),
                                step=0.1,
                                key="nuevo_stock_minimo_tab"
                            )
                            
                            nuevo_stock_maximo = st.number_input(
                                "Nuevo stock máximo (kg):",
                                min_value=0.0,
                                value=float(max(producto_info['stock_maximo_kg'], producto_info['stock_kg'])),
                                step=0.1,
                                key="nuevo_stock_maximo_tab",
                                help="Stock máximo representa el 100% de capacidad"
                            )
                        else:
                            nueva_cantidad = st.number_input(
                                "Nueva cantidad en stock:",
                                min_value=0.0,
                                value=float(producto_info['stock']),
                                step=1.0,
                                key="nueva_cantidad_stock_tab"
                            )
                            
                            nuevo_stock_minimo = st.number_input(
                                "Nuevo stock mínimo:",
                                min_value=0.0,
                                value=float(producto_info['stock_minimo']),
                                step=1.0,
                                key="nuevo_stock_minimo_tab"
                            )
                            
                            nuevo_stock_maximo = st.number_input(
                                "Nuevo stock máximo:",
                                min_value=0.0,
                                value=float(max(producto_info['stock_maximo'], producto_info['stock'])),
                                step=1.0,
                                key="nuevo_stock_maximo_tab",
                                help="Stock máximo representa el 100% de capacidad"
                            )
                        
                        motivo_stock = st.selectbox(
                            "Motivo del cambio:",
                            [
                                "Inventario físico",
                                "Corrección de error",
                                "Producto dañado", 
                                "Merma natural",
                                "Reabastecimiento",
                                "Devolución cliente",
                                "Ajuste administrativo",
                                "Otro"
                            ],
                            key="motivo_stock_tab"
                        )
                    
                    with col3:
                        st.write("**Resumen de Cambios:**")
                        if producto_info['es_granel']:
                            diferencia_stock = nueva_cantidad - producto_info['stock_kg']
                            diferencia_minimo = nuevo_stock_minimo - producto_info['stock_minimo_kg']
                            diferencia_maximo = nuevo_stock_maximo - producto_info['stock_maximo_kg']
                        else:
                            diferencia_stock = nueva_cantidad - producto_info['stock']
                            diferencia_minimo = nuevo_stock_minimo - producto_info['stock_minimo']
                            diferencia_maximo = nuevo_stock_maximo - producto_info['stock_maximo']
                        
                        if diferencia_stock > 0:
                            st.success(f"📈 Stock: +{diferencia_stock:.2f}")
                        elif diferencia_stock < 0:
                            st.error(f"📉 Stock: {diferencia_stock:.2f}")
                        else:
                            st.info("➡️ Stock sin cambios")
                        
                        if diferencia_minimo != 0:
                            st.info(f"⚙️ Stock mínimo: {diferencia_minimo:+.2f}")
                        
                        if diferencia_maximo != 0:
                            st.info(f"📊 Stock máximo: {diferencia_maximo:+.2f}")
                        
                        # Calcular porcentaje
                        if nuevo_stock_maximo > 0:
                            porcentaje = (nueva_cantidad / nuevo_stock_maximo) * 100
                            st.metric("% de Capacidad", f"{porcentaje:.1f}%")
                        
                        # Alertas
                        if nueva_cantidad < nuevo_stock_minimo:
                            st.warning(f"⚠️ Quedará por debajo del stock mínimo")
                        
                        if nuevo_stock_minimo > nuevo_stock_maximo:
                            st.error(f"❌ Stock mínimo no puede ser mayor al máximo")
                        
                        if nueva_cantidad > nuevo_stock_maximo:
                            st.warning(f"⚠️ Stock excede la capacidad máxima")
                        
                        if st.button("💾 Actualizar Stock", type="primary", key="actualizar_stock_tab", width='stretch'):
                            try:
                                # Validar que mínimo <= máximo
                                if nuevo_stock_minimo > nuevo_stock_maximo:
                                    st.error("❌ El stock mínimo no puede ser mayor al máximo")
                                else:
                                    # Actualizar stock, stock mínimo y stock máximo
                                    if producto_info['es_granel']:
                                        success1 = actualizar_stock_producto(producto_info['codigo'], int(nueva_cantidad), nueva_cantidad)
                                        success2 = actualizar_stock_minimo(producto_info['codigo_barras'] or producto_info['nombre'], int(nuevo_stock_minimo), nuevo_stock_minimo)
                                        success3 = actualizar_stock_maximo(producto_info['codigo'], int(nuevo_stock_maximo), nuevo_stock_maximo)
                                    else:
                                        success1 = actualizar_stock_producto(producto_info['codigo'], int(nueva_cantidad))
                                        success2 = actualizar_stock_minimo(producto_info['codigo_barras'] or producto_info['nombre'], int(nuevo_stock_minimo), None)
                                        success3 = actualizar_stock_maximo(producto_info['codigo'], int(nuevo_stock_maximo), None)
                                    
                                    if success1 and success2 and success3:
                                        st.success("✅ Stock actualizado exitosamente")
                                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        if producto_info['es_granel']:
                                            log_cambio = f"{fecha_actual} - Stock de '{producto_info['nombre']}': {producto_info['stock_kg']:.2f} kg → {nueva_cantidad:.2f} kg. Stock mínimo: {producto_info['stock_minimo_kg']:.2f} → {nuevo_stock_minimo:.2f} kg. Stock máximo: {producto_info['stock_maximo_kg']:.2f} → {nuevo_stock_maximo:.2f} kg. Motivo: {motivo_stock}"
                                        else:
                                            log_cambio = f"{fecha_actual} - Stock de '{producto_info['nombre']}': {producto_info['stock']} → {int(nueva_cantidad)} unid. Stock mínimo: {producto_info['stock_minimo']} → {int(nuevo_stock_minimo)}. Stock máximo: {producto_info['stock_maximo']} → {int(nuevo_stock_maximo)}. Motivo: {motivo_stock}"
                                        st.text_area("📋 Log del cambio:", log_cambio, height=100, disabled=True)
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error("❌ Error al actualizar el stock")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                with tab2:
                    st.write("#### 💰 Gestión de Precios")
                    col1, col2, col3 = st.columns([2, 2, 2])
                    
                    with col1:
                        st.write("**Precios Actuales:**")
                        st.write(f"💰 Precio venta: ${producto_info['precio_venta']:.2f}")
                        st.write(f"🏷️ Precio compra: ${producto_info['precio_compra']:.2f}")
                        margen_actual = ((producto_info['precio_venta'] - producto_info['precio_compra']) / producto_info['precio_compra']) * 100
                        st.write(f"📊 Margen actual: {margen_actual:.1f}%")
                    
                    with col2:
                        st.write("**Nuevos Precios:**")
                        nuevo_precio_venta = st.number_input(
                            "Nuevo precio de venta:",
                            min_value=0.01,
                            value=float(producto_info['precio_venta']),
                            step=0.01,
                            key="nuevo_precio_venta_tab",
                            format="%.2f"
                        )
                        
                        nuevo_precio_compra = st.number_input(
                            "Nuevo precio de compra:",
                            min_value=0.01,
                            value=float(producto_info['precio_compra']),
                            step=0.01,
                            key="nuevo_precio_compra_tab",
                            format="%.2f"
                        )
                        
                        motivo_precio = st.selectbox(
                            "Motivo del cambio:",
                            [
                                "Actualización de proveedor",
                                "Ajuste de margen",
                                "Promoción especial",
                                "Corrección de precio",
                                "Inflación/Deflación",
                                "Competencia",
                                "Otro"
                            ],
                            key="motivo_precio_tab"
                        )
                    
                    with col3:
                        st.write("**Análisis de Precios:**")
                        nuevo_margen = ((nuevo_precio_venta - nuevo_precio_compra) / nuevo_precio_compra) * 100
                        st.write(f"📊 Nuevo margen: {nuevo_margen:.1f}%")
                        
                        if nuevo_margen < 10:
                            st.error("⚠️ Margen muy bajo (<10%)")
                        elif nuevo_margen < 20:
                            st.warning("⚠️ Margen bajo (<20%)")
                        else:
                            st.success("✅ Margen saludable")
                        
                        diferencia_venta = nuevo_precio_venta - producto_info['precio_venta']
                        diferencia_compra = nuevo_precio_compra - producto_info['precio_compra']
                        
                        if diferencia_venta != 0:
                            st.write(f"Venta: ${diferencia_venta:+.2f}")
                        if diferencia_compra != 0:
                            st.write(f"Compra: ${diferencia_compra:+.2f}")
                        
                        if st.button("💰 Actualizar Precios", type="primary", key="actualizar_precios_tab", width='stretch'):
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            
                            try:
                                cursor.execute("""
                                    UPDATE productos 
                                    SET precio_normal = ?, precio_compra = ?
                                    WHERE codigo = ?
                                """, (nuevo_precio_venta, nuevo_precio_compra, producto_info['codigo']))
                                
                                conn.commit()
                                
                                st.success("✅ Precios actualizados exitosamente")
                                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                log_cambio = f"{fecha_actual} - Precios de '{producto_info['nombre']}': Venta ${producto_info['precio_venta']:.2f} → ${nuevo_precio_venta:.2f}, Compra ${producto_info['precio_compra']:.2f} → ${nuevo_precio_compra:.2f}. Motivo: {motivo_precio}"
                                st.text_area("📋 Log del cambio:", log_cambio, height=80, disabled=True)
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                conn.rollback()
                            finally:
                                conn.close()
                
                with tab3:
                    st.write("#### ⚙️ Configuración del Producto")
                    col1, col2, col3 = st.columns([2, 2, 2])
                    
                    with col1:
                        st.write("**Configuración Actual:**")
                        st.write(f"🏷️ Nombre: {producto_info['nombre']}")
                        st.write(f"🔢 Código: {producto_info['codigo_barras'] or 'Sin código'}")
                        st.write(f"📂 Categoría: {producto_info['categoria']}")
                        st.write(f"⚖️ Es granel: {'Sí' if producto_info['es_granel'] else 'No'}")
                    
                    with col2:
                        st.write("**Editar Configuración:**")
                        nuevo_nombre = st.text_input(
                            "Nuevo nombre:",
                            value=producto_info['nombre'],
                            key="nuevo_nombre_tab"
                        )
                        
                        nuevo_codigo = st.text_input(
                            "Nuevo código de barras:",
                            value=producto_info['codigo_barras'] or "",
                            key="nuevo_codigo_tab"
                        )
                        
                        nueva_categoria = st.text_input(
                            "Nueva categoría:",
                            value=producto_info['categoria'],
                            key="nueva_categoria_tab"
                        )
                        
                        nuevo_es_granel = st.checkbox(
                            "Producto a granel",
                            value=producto_info['es_granel'],
                            key="nuevo_es_granel_tab"
                        )
                    
                    with col3:
                        st.write("**Cambios a Realizar:**")
                        
                        cambios = []
                        if nuevo_nombre != producto_info['nombre']:
                            cambios.append(f"Nombre: {producto_info['nombre']} → {nuevo_nombre}")
                        if nuevo_codigo != (producto_info['codigo_barras'] or ""):
                            cambios.append(f"Código: {producto_info['codigo_barras'] or 'Sin código'} → {nuevo_codigo or 'Sin código'}")
                        if nueva_categoria != producto_info['categoria']:
                            cambios.append(f"Categoría: {producto_info['categoria']} → {nueva_categoria}")
                        if nuevo_es_granel != producto_info['es_granel']:
                            cambios.append(f"Granel: {'Sí' if producto_info['es_granel'] else 'No'} → {'Sí' if nuevo_es_granel else 'No'}")
                        
                        if cambios:
                            for cambio in cambios:
                                st.write(f"• {cambio}")
                        else:
                            st.info("Sin cambios")
                        
                        if st.button("⚙️ Actualizar Configuración", type="primary", key="actualizar_config_tab", width='stretch'):
                            if cambios:
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                
                                try:
                                    # Solo actualizar nombre y tipo_venta (la tabla no tiene codigo_barras, categoria, es_granel separados)
                                    nuevo_tipo_venta = 'granel' if nuevo_es_granel else 'unidad'
                                    cursor.execute("""
                                        UPDATE productos 
                                        SET nombre = ?, tipo_venta = ?
                                        WHERE codigo = ?
                                    """, (nuevo_nombre, nuevo_tipo_venta, producto_info['codigo']))
                                    
                                    conn.commit()
                                    
                                    st.success("✅ Configuración actualizada exitosamente")
                                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    log_cambio = f"{fecha_actual} - Configuración de producto ID {producto_info['id']} actualizada. Cambios: {', '.join(cambios)}"
                                    st.text_area("📋 Log del cambio:", log_cambio, height=80, disabled=True)
                                    time.sleep(2)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                                    conn.rollback()
                                finally:
                                    conn.close()
                            else:
                                st.warning("⚠️ No hay cambios para aplicar")
            
            elif not busqueda_unificada or len(busqueda_unificada.strip()) < 2:
                st.info("👆 Escribe al menos 2 caracteres para buscar un producto")
                st.caption("💡 Puedes buscar por nombre del producto o escanear/escribir un código de barras")
                
        else:
            st.warning("⚠️ No hay productos registrados para editar")
            st.info("Primero agrega productos en la sección 'Gestión de Productos'")
    
    # Separador
    st.divider()
    
    # 5. Métricas importantes
    st.subheader("📈 Métricas del Inventario")
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    
    with col_met1:
        total_productos = len(productos_df)
        st.metric("Total Productos", total_productos)
    
    with col_met2:
        productos_criticos = len(productos_bajo_stock)
        st.metric("Productos Críticos", productos_criticos, delta=f"-{productos_criticos}" if productos_criticos > 0 else None)
    
    with col_met3:
        if not productos_df.empty:
            valor_inventario = (productos_df['stock'] * productos_df['precio_compra']).sum()
            st.metric("Valor Inventario", f"${valor_inventario:.2f}")
        else:
            st.metric("Valor Inventario", "$0.00")
    
    with col_met4:
        if not productos_bajo_stock.empty:
            inversion_necesaria = (productos_bajo_stock['cantidad_necesaria'] * productos_bajo_stock['precio_compra']).sum()
            st.metric("Inversión Necesaria", f"${inversion_necesaria:.2f}")
        else:
            st.metric("Inversión Necesaria", "$0.00")
    
    # Separador
    st.divider()
    
    # 6. Exportación
    st.subheader("📤 Exportar Datos")
    
    # Información sobre funciones de administrador
    if not es_admin:
        st.info("ℹ️ **Exportación disponible para todos** - Los reportes de inventario están disponibles en modo consulta")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        # Exportar CSV
        if not productos_df.empty:
            csv = productos_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📄 Descargar Inventario (CSV)", 
                data=csv, 
                file_name='inventario_completo.csv', 
                mime='text/csv'
            )
        else:
            st.info("No hay datos para exportar")
    
    with col_exp2:
        # Exportar Excel
        if not productos_df.empty:
            if st.button("📊 Generar Reporte Excel Completo"):
                try:
                    excel_buffer = exportar_a_excel(productos_df, productos_bajo_stock)
                    
                    st.download_button(
                        "📥 Descargar Reporte Excel",
                        data=excel_buffer,
                        file_name=f'reporte_inventario_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                except Exception as e:
                    st.error(f"Error al generar Excel: {e}")
        else:
            st.info("No hay datos para el reporte")
    
    # 7. Exportar solo productos con stock bajo
    if not productos_bajo_stock.empty:
        st.subheader("🛒 Lista de Compras Urgentes")
        
        # Resumen financiero de la lista de compras
        inversion_total = (productos_bajo_stock['cantidad_necesaria'] * productos_bajo_stock['precio_compra']).sum()
        productos_criticos = len(productos_bajo_stock)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("💰 Inversión Total Necesaria", f"${inversion_total:.2f}")
        with col_res2:
            st.metric("📦 Productos a Reabastecer", productos_criticos)
        
        # Exportar solo lista de compras
        lista_compras_csv = productos_bajo_stock.to_csv(index=False).encode('utf-8')
        st.download_button(
            "🛒 Descargar Lista de Compras (CSV)",
            data=lista_compras_csv,
            file_name=f'lista_compras_urgentes_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )