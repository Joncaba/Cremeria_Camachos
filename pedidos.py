import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time
import hashlib
import unicodedata
import re

# Importar sistema unificado de autenticación
from db_adapter import get_db_adapter
import config
from sync_manager import get_sync_manager

DB_PATH = "pos_cremeria.db"

# Inicializar adaptador de base de datos y sync manager
db = get_db_adapter()
sync = get_sync_manager()

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

def hash_password(password):
    """Crear hash de la contraseña usando salt del config"""
    salt = config.get_password_salt()
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verificar_credenciales(usuario, password):
    """Verificar si las credenciales son correctas usando el sistema unificado"""
    try:
        # Calcular hash de la contraseña ingresada
        password_hash = hash_password(password)
        
        # Obtener usuario de la base de datos
        usuario_db = db.obtener_usuario(usuario)
        
        if usuario_db and usuario_db.get('password') == password_hash:
            return True
        
        return False
    except Exception as e:
        print(f"Error al verificar credenciales: {e}")
        return False

def verificar_sesion_admin():
    """Verificar si hay una sesión administrativa activa"""
    return st.session_state.get('admin_pedidos_autenticado', False)

def cerrar_sesion_admin():
    """Cerrar sesión administrativa"""
    if 'admin_pedidos_autenticado' in st.session_state:
        del st.session_state.admin_pedidos_autenticado
    if 'usuario_admin_pedidos' in st.session_state:
        del st.session_state.usuario_admin_pedidos

# === GESTIÓN DE PEDIDOS Y CHECKLIST ===

def crear_tabla_pedidos():
    """Crear tabla de pedidos/checklist si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos_reabastecimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto TEXT NOT NULL,
            nombre_producto TEXT NOT NULL,
            cantidad_solicitada REAL NOT NULL,
            cantidad_recibida REAL DEFAULT 0,
            precio_unitario REAL NOT NULL,
            costo_total REAL NOT NULL,
            proveedor TEXT DEFAULT '',
            fecha_pedido TEXT NOT NULL,
            fecha_entrega_esperada TEXT,
            fecha_entrega_real TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            completado INTEGER DEFAULT 0,
            notas TEXT DEFAULT '',
            creado_por TEXT NOT NULL,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(codigo_producto) REFERENCES productos(codigo)
        )
    ''')
    
    conn.commit()
    conn.close()

def obtener_productos_bajo_stock():
    """Obtener productos con stock bajo que necesitan reabastecimiento"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT codigo, nombre, stock, stock_minimo, stock_kg, stock_minimo_kg, 
           stock_maximo, stock_maximo_kg, tipo_venta,
           precio_compra, precio_normal, precio_por_kg, categoria,
           CASE 
               WHEN tipo_venta = 'granel' THEN 
                   CASE WHEN stock_minimo_kg > 0 THEN CAST((stock_kg * 100.0 / stock_minimo_kg) AS INTEGER) ELSE 100 END
               ELSE 
                   CASE WHEN stock_minimo > 0 THEN CAST((stock * 100.0 / stock_minimo) AS INTEGER) ELSE 100 END
           END as porcentaje_stock,
           CASE 
               WHEN tipo_venta = 'granel' THEN ROUND((stock_minimo_kg - stock_kg), 2)
               ELSE (stock_minimo - stock)
           END as cantidad_necesaria,
           CASE 
               WHEN tipo_venta = 'granel' THEN 
                   ROUND(CASE WHEN stock_maximo_kg > 0 THEN stock_maximo_kg ELSE stock_minimo_kg * 2 END - stock_kg, 2)
               ELSE 
                   (CASE WHEN stock_maximo > 0 THEN stock_maximo ELSE stock_minimo * 2 END - stock)
           END as cantidad_hasta_maximo
    FROM productos 
    WHERE (
        (tipo_venta = 'unidad' AND stock <= (stock_minimo * 0.5) AND stock_minimo > 0) OR
        (tipo_venta = 'granel' AND stock_kg <= (stock_minimo_kg * 0.5) AND stock_minimo_kg > 0)
    )
    ORDER BY categoria, porcentaje_stock ASC
    """
    
    productos_bajo_stock = pd.read_sql_query(query, conn)
    conn.close()
    
    return productos_bajo_stock

def agregar_producto_a_pedido(codigo_producto, nombre_producto, cantidad_solicitada, precio_unitario, proveedor="", fecha_entrega_esperada="", notas="", creado_por="admin"):
    """Agregar un producto al pedido de reabastecimiento"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    fecha_pedido = datetime.now().strftime("%Y-%m-%d")
    costo_total = cantidad_solicitada * precio_unitario
    
    cursor.execute('''
        INSERT INTO pedidos_reabastecimiento 
        (codigo_producto, nombre_producto, cantidad_solicitada, precio_unitario, costo_total, 
         proveedor, fecha_pedido, fecha_entrega_esperada, notas, creado_por)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (codigo_producto, nombre_producto, cantidad_solicitada, precio_unitario, costo_total,
          proveedor, fecha_pedido, fecha_entrega_esperada, notas, creado_por))
    
    conn.commit()
    conn.close()
    return True

def obtener_pedidos_activos():
    """Obtener todos los pedidos activos (no completados)"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT id, codigo_producto, nombre_producto, cantidad_solicitada, cantidad_recibida,
           precio_unitario, costo_total, proveedor, fecha_pedido, fecha_entrega_esperada,
           fecha_entrega_real, estado, completado, notas, creado_por
    FROM pedidos_reabastecimiento 
    ORDER BY 
        CASE 
            WHEN completado = 1 THEN 1 
            ELSE 0 
        END,
        fecha_pedido DESC
    """
    
    pedidos = pd.read_sql_query(query, conn)
    conn.close()
    return pedidos

def actualizar_estado_pedido(pedido_id, cantidad_recibida=None, completado=None, estado=None, fecha_entrega_real=None, notas=None):
    """Actualizar el estado de un pedido"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if cantidad_recibida is not None:
        updates.append("cantidad_recibida = ?")
        values.append(cantidad_recibida)
    
    if completado is not None:
        updates.append("completado = ?")
        values.append(completado)
    
    if estado is not None:
        updates.append("estado = ?")
        values.append(estado)
    
    if fecha_entrega_real is not None:
        updates.append("fecha_entrega_real = ?")
        values.append(fecha_entrega_real)
    
    if notas is not None:
        updates.append("notas = ?")
        values.append(notas)
    
    if updates:
        values.append(pedido_id)
        query = f"UPDATE pedidos_reabastecimiento SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

def eliminar_pedido(pedido_id):
    """Eliminar un pedido del sistema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pedidos_reabastecimiento WHERE id = ?", (pedido_id,))
    conn.commit()
    conn.close()
    return True

def actualizar_stock_desde_pedido(codigo_producto, cantidad_recibida):
    """Actualizar el stock del producto cuando llega el pedido"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar tipo de producto
    cursor.execute("SELECT tipo_venta, stock, stock_kg FROM productos WHERE codigo = ?", (codigo_producto,))
    producto = cursor.fetchone()
    
    if producto:
        tipo_venta, stock_actual, stock_kg_actual = producto
        
        if tipo_venta == 'granel':
            nuevo_stock_kg = (stock_kg_actual or 0) + cantidad_recibida
            cursor.execute("UPDATE productos SET stock_kg = ? WHERE codigo = ?", (nuevo_stock_kg, codigo_producto))
        else:
            nuevo_stock = (stock_actual or 0) + int(cantidad_recibida)
            cursor.execute("UPDATE productos SET stock = ? WHERE codigo = ?", (nuevo_stock, codigo_producto))
        
        conn.commit()
    
    conn.close()
    return True

def mostrar():
    st.title("🛒 Gestión de Pedidos y Reabastecimiento")
    
    # Sincronizar datos desde Supabase al inicio (solo si hay conexión)
    if sync.is_online():
        with st.spinner('🔄 Sincronizando datos desde Supabase...'):
            resultado = sync.sync_all_productos_from_supabase()
            if resultado.get('success', 0) > 0:
                st.toast(f"✅ {resultado['success']} productos sincronizados desde la nube")
    
    # Verificar si hay productos transferidos desde inventario
    if st.session_state.get('productos_para_pedido') and st.session_state.get('origen_pedido') == 'inventario':
        productos_transferidos = st.session_state.productos_para_pedido
        st.success(f"✅ **{len(productos_transferidos)} productos** transferidos desde Inventario")
        st.info("🎯 Los productos con stock bajo están preseleccionados en la pestaña 'Productos con Stock Bajo'")
        
        # Limpiar la sesión después de mostrar el mensaje
        if st.button("✅ Entendido", type="secondary"):
            del st.session_state.productos_para_pedido
            del st.session_state.origen_pedido
            st.rerun()
    
    # Inicializar sistema - DEPRECADO (usuarios ahora en usuarios.py)
    # crear_tabla_usuarios()
    # admin_creado = crear_admin_por_defecto()
    crear_tabla_pedidos()
    
    # === CONTROL DE ACCESO ===
    es_admin = verificar_sesion_admin()
    
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        if es_admin:
            st.success(f"✅ **Modo Administrador** - Usuario: {st.session_state.get('usuario_admin_pedidos', 'admin')} | Gestión completa de pedidos")
        else:
            st.info("👀 **Modo Solo Lectura** - Consulta de pedidos. Gestión restringida.")
    
    with col_header2:
        if es_admin:
            if st.button("🚪 Cerrar Sesión", type="secondary", key="logout_pedidos"):
                cerrar_sesion_admin()
                st.success("✅ Sesión cerrada exitosamente")
                time.sleep(1)
                st.rerun()
        else:
            if st.button("🔑 Acceso Admin", type="primary", key="login_pedidos"):
                st.session_state.mostrar_login_pedidos = True
                st.rerun()
    
    # Mostrar formulario de login si se solicita
    if not es_admin and st.session_state.get('mostrar_login_pedidos', False):
        st.markdown("---")
        st.subheader("🔐 Acceso Administrativo")
        
        with st.form("login_form_pedidos"):
            col1, col2 = st.columns(2)
            with col1:
                usuario = st.text_input("👤 Usuario:", placeholder="admin", key="usuario_pedidos_form")
            with col2:
                password = st.text_input("🔑 Contraseña:", type="password", key="password_pedidos_form")
            
            col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
            with col_submit2:
                submitted = st.form_submit_button("🔓 INICIAR SESIÓN", type="primary", use_container_width=True)
            
            if submitted:
                if usuario and password:
                    if verificar_credenciales(usuario, password):
                        st.session_state.admin_pedidos_autenticado = True
                        st.session_state.usuario_admin_pedidos = usuario
                        st.session_state.mostrar_login_pedidos = False
                        st.success("✅ ¡Acceso concedido! Redirigiendo...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas. Usuario: 'admin' | Contraseña: 'Creme$123'")
                else:
                    st.warning("⚠️ Por favor completa ambos campos")
        
        # Botón para cancelar login
        col_cancel = st.columns([1, 2, 1])
        with col_cancel[1]:
            if st.button("❌ Cancelar Login", type="secondary", key="cancel_login_pedidos"):
                st.session_state.mostrar_login_pedidos = False
                st.rerun()
        
        st.markdown("---")
        
        # No mostrar el resto del contenido mientras se muestra el login
        return
    
    st.divider()
    
    # === PESTAÑAS PRINCIPALES ===
    tab1, tab2, tab3 = st.tabs(["🚨 Productos con Stock Bajo", "📝 Gestionar Pedidos", "📊 Resumen y Estadísticas"])
    
    with tab1:
        st.subheader("🚨 Productos que Necesitan Reabastecimiento")
        
        productos_bajo_stock = obtener_productos_bajo_stock()
        
        if not productos_bajo_stock.empty:
            st.warning(f"⚠️ **{len(productos_bajo_stock)} productos** necesitan reabastecimiento urgente")
            
            # Organizar productos por categoría
            if 'categoria' in productos_bajo_stock.columns:
                categorias_disponibles = productos_bajo_stock['categoria'].unique()
                
                # Mapeo de categorías con iconos
                categoria_info = {
                    'cremeria': {'icon': '🥛', 'name': 'Cremería', 'color': '#2196f3'},
                    'abarrotes': {'icon': '🛒', 'name': 'Abarrotes', 'color': '#ff9800'},
                    'otros': {'icon': '📦', 'name': 'Otros', 'color': '#9c27b0'}
                }
                
                # Crear pestañas por categoría
                tabs_categorias = []
                for categoria in sorted(categorias_disponibles):
                    info = categoria_info.get(categoria, {'icon': '📦', 'name': categoria.title(), 'color': '#9c27b0'})
                    tabs_categorias.append(f"{info['icon']} {info['name']}")
                
                tab_cats = st.tabs(tabs_categorias)
                
                productos_seleccionados = []
                
                for i, categoria in enumerate(sorted(categorias_disponibles)):
                    with tab_cats[i]:
                        productos_categoria = productos_bajo_stock[productos_bajo_stock['categoria'] == categoria]
                        info = categoria_info.get(categoria, {'icon': '📦', 'name': categoria.title(), 'color': '#9c27b0'})
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, {info['color']}20 0%, {info['color']}10 100%); 
                                    padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; 
                                    border: 2px solid {info['color']}40;">
                            <h4 style="color: {info['color']}; margin: 0;">
                                {info['icon']} {info['name']} - {len(productos_categoria)} productos críticos
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Mostrar productos de esta categoría
                        for idx, producto in productos_categoria.iterrows():
                            col_check, col_info, col_cantidad, col_proveedor = st.columns([1, 4, 2, 2])
                            
                            with col_check:
                                seleccionado = st.checkbox(
                                    "Seleccionar",
                                    key=f"select_producto_{producto['codigo']}_{categoria}",
                                    label_visibility="collapsed"
                                )
                            
                            with col_info:
                                tipo_icono = "⚖️" if producto['tipo_venta'] == 'granel' else "📦"
                                estado_color = "🔴" if producto['porcentaje_stock'] < 25 else "🟡"
                                
                                # Mostrar información según tipo de venta
                                if producto['tipo_venta'] == 'granel':
                                    stock_actual = producto['stock_kg']
                                    stock_min = producto['stock_minimo_kg']
                                    stock_max = producto.get('stock_maximo_kg', stock_min * 2)
                                    unidad = "kg"
                                else:
                                    stock_actual = producto['stock']
                                    stock_min = producto['stock_minimo']
                                    stock_max = producto.get('stock_maximo', stock_min * 2)
                                    unidad = "unid."
                                
                                cantidad_hasta_maximo = producto.get('cantidad_hasta_maximo', 0)
                                
                                st.markdown(f"""
                                **{tipo_icono} {producto['nombre']}** {estado_color}  
                                📊 Stock: {stock_actual:.1f} {unidad} | Mín: {stock_min:.1f} {unidad} | Máx: {stock_max:.1f} {unidad}  
                                📦 Para mínimo: **{producto['cantidad_necesaria']:.1f} {unidad}** | Para máximo: **{cantidad_hasta_maximo:.1f} {unidad}**  
                                💰 Precio: ${producto['precio_compra']:.2f}
                                """)
                            
                            with col_cantidad:
                                if seleccionado:
                                    cantidad_pedido = st.number_input(
                                        "Cantidad a pedir:",
                                        min_value=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                        value=float(producto['cantidad_necesaria']) * 2,  # Sugerir el doble de lo necesario
                                        step=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                        key=f"cantidad_{producto['codigo']}_{categoria}",
                                        format="%.1f" if producto['tipo_venta'] == 'granel' else "%.0f"
                                    )
                                else:
                                    cantidad_pedido = 0
                            
                            with col_proveedor:
                                if seleccionado:
                                    proveedor = st.text_input(
                                        "Proveedor:",
                                        key=f"proveedor_{producto['codigo']}_{categoria}",
                                        placeholder="Nombre del proveedor"
                                    )
                                else:
                                    proveedor = ""
                            
                            if seleccionado and cantidad_pedido > 0:
                                productos_seleccionados.append({
                                    'codigo': producto['codigo'],
                                    'nombre': producto['nombre'],
                                    'cantidad': cantidad_pedido,
                                    'precio': producto['precio_compra'],
                                    'proveedor': proveedor,
                                    'tipo_venta': producto['tipo_venta'],
                                    'categoria': categoria
                                })
                            
                            st.divider()
            else:
                # Si no hay columna categoria, mostrar todos juntos como antes
                st.write("#### Selecciona los productos para agregar al pedido:")
                productos_seleccionados = []
                
                for idx, producto in productos_bajo_stock.iterrows():
                    col_check, col_info, col_cantidad, col_proveedor = st.columns([1, 4, 2, 2])
                    
                    with col_check:
                        seleccionado = st.checkbox(
                            "Seleccionar",
                            key=f"select_producto_{producto['codigo']}",
                            label_visibility="collapsed"
                        )
                    
                    with col_info:
                        tipo_icono = "⚖️" if producto['tipo_venta'] == 'granel' else "📦"
                        estado_color = "🔴" if producto['porcentaje_stock'] < 25 else "🟡"
                        
                        # Mostrar información según tipo de venta
                        if producto['tipo_venta'] == 'granel':
                            stock_actual = producto['stock_kg']
                            stock_min = producto['stock_minimo_kg']
                            stock_max = producto.get('stock_maximo_kg', stock_min * 2)
                            unidad = "kg"
                        else:
                            stock_actual = producto['stock']
                            stock_min = producto['stock_minimo']
                            stock_max = producto.get('stock_maximo', stock_min * 2)
                            unidad = "unid."
                        
                        cantidad_hasta_maximo = producto.get('cantidad_hasta_maximo', 0)
                        
                        st.markdown(f"""
                        **{tipo_icono} {producto['nombre']}** {estado_color}  
                        📊 Stock: {stock_actual:.1f} {unidad} | Mín: {stock_min:.1f} {unidad} | Máx: {stock_max:.1f} {unidad}  
                        📦 Para mínimo: **{producto['cantidad_necesaria']:.1f} {unidad}** | Para máximo: **{cantidad_hasta_maximo:.1f} {unidad}**  
                        💰 Precio: ${producto['precio_compra']:.2f}
                        """)
                    
                    with col_cantidad:
                        if seleccionado:
                            cantidad_pedido = st.number_input(
                                "Cantidad a pedir:",
                                min_value=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                value=float(producto['cantidad_necesaria']) * 2,
                                step=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                key=f"cantidad_{producto['codigo']}",
                                format="%.1f" if producto['tipo_venta'] == 'granel' else "%.0f"
                            )
                        else:
                            cantidad_pedido = 0
                    
                    with col_proveedor:
                        if seleccionado:
                            proveedor = st.text_input(
                                "Proveedor:",
                                key=f"proveedor_{producto['codigo']}",
                                placeholder="Nombre del proveedor"
                            )
                        else:
                            proveedor = ""
                    
                    if seleccionado and cantidad_pedido > 0:
                        productos_seleccionados.append({
                            'codigo': producto['codigo'],
                            'nombre': producto['nombre'],
                            'cantidad': cantidad_pedido,
                            'precio': producto['precio_compra'],
                            'proveedor': proveedor,
                            'tipo_venta': producto['tipo_venta']
                        })
                    
                    st.divider()
            
            # Botón para agregar productos seleccionados al pedido
            if productos_seleccionados and es_admin:
                st.write("#### Resumen de productos seleccionados:")
                
                total_costo = 0
                for prod in productos_seleccionados:
                    costo_producto = prod['cantidad'] * prod['precio']
                    total_costo += costo_producto
                    unidad = "Kg" if prod['tipo_venta'] == 'granel' else "unidades"
                    st.write(f"• **{prod['nombre']}**: {prod['cantidad']:.1f} {unidad} - ${costo_producto:.2f}")
                
                st.metric("💰 Costo Total del Pedido", f"${total_costo:.2f}")
                
                col_fecha, col_notas = st.columns(2)
                with col_fecha:
                    fecha_entrega = st.date_input(
                        "📅 Fecha de entrega esperada:",
                        value=datetime.now() + timedelta(days=7)
                    )
                
                with col_notas:
                    notas_generales = st.text_area(
                        "📝 Notas del pedido:",
                        placeholder="Observaciones adicionales..."
                    )
                
                if st.button("✅ Crear Pedido de Reabastecimiento", type="primary", width='stretch'):
                    try:
                        for prod in productos_seleccionados:
                            agregar_producto_a_pedido(
                                codigo_producto=prod['codigo'],
                                nombre_producto=prod['nombre'],
                                cantidad_solicitada=prod['cantidad'],
                                precio_unitario=prod['precio'],
                                proveedor=prod['proveedor'],
                                fecha_entrega_esperada=fecha_entrega.strftime("%Y-%m-%d"),
                                notas=notas_generales,
                                creado_por=st.session_state.get('usuario_admin_pedidos', 'admin')
                            )
                        
                        st.success(f"✅ Pedido creado exitosamente con {len(productos_seleccionados)} productos")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error al crear el pedido: {str(e)}")
            
            elif productos_seleccionados and not es_admin:
                st.error("🔒 Se requieren permisos de administrador para crear pedidos")
        
        else:
            st.success("✅ Todos los productos tienen stock suficiente")
            st.info("🎉 No hay productos que necesiten reabastecimiento en este momento")
    
    with tab2:
        st.subheader("📝 Gestión de Pedidos de Reabastecimiento")
        
        pedidos_df = obtener_pedidos_activos()
        
        if not pedidos_df.empty:
            # Filtros
            col_filtro1, col_filtro2 = st.columns(2)
            
            with col_filtro1:
                filtro_estado = st.selectbox(
                    "Filtrar por estado:",
                    ["Todos", "PENDIENTE", "EN_TRANSITO", "RECIBIDO", "COMPLETADO"],
                    key="filtro_estado_pedidos"
                )
            
            with col_filtro2:
                mostrar_completados = st.checkbox("Mostrar pedidos completados", value=False)
            
            # Aplicar filtros
            df_filtrado = pedidos_df.copy()
            
            if filtro_estado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
            
            if not mostrar_completados:
                df_filtrado = df_filtrado[df_filtrado['completado'] == 0]
            
            st.info(f"📊 Mostrando {len(df_filtrado)} de {len(pedidos_df)} pedidos")
            
            # Mostrar pedidos con controles
            for idx, pedido in df_filtrado.iterrows():
                with st.container():
                    col_info, col_acciones = st.columns([3, 1])
                    
                    with col_info:
                        # Estado visual del pedido
                        estado_color = {
                            'PENDIENTE': '🟡',
                            'EN_TRANSITO': '🔵', 
                            'RECIBIDO': '🟢',
                            'COMPLETADO': '✅'
                        }.get(pedido['estado'], '⚪')
                        
                        completado_texto = "✅ COMPLETADO" if pedido['completado'] else "⏳ PENDIENTE"
                        
                        st.markdown(f"""
                        ### {estado_color} {pedido['nombre_producto']} - {completado_texto}
                        
                        **📋 Detalles del Pedido:**
                        - 🔢 Código: `{pedido['codigo_producto']}`
                        - 📦 Cantidad solicitada: {pedido['cantidad_solicitada']} 
                        - 📦 Cantidad recibida: {pedido['cantidad_recibida']}
                        - 💰 Precio unitario: ${pedido['precio_unitario']:.2f}
                        - 💵 Costo total: ${pedido['costo_total']:.2f}
                        - 🏪 Proveedor: {pedido['proveedor'] or 'No especificado'}
                        - 📅 Fecha pedido: {pedido['fecha_pedido']}
                        - 🚚 Entrega esperada: {pedido['fecha_entrega_esperada'] or 'No especificada'}
                        - 📝 Estado: **{pedido['estado']}**
                        """)
                        
                        if pedido['notas']:
                            st.write(f"📝 **Notas:** {pedido['notas']}")
                    
                    with col_acciones:
                        if es_admin and not pedido['completado']:
                            st.write("**Acciones:**")
                            
                            # Actualizar cantidad recibida
                            nueva_cantidad = st.number_input(
                                "Cantidad recibida:",
                                min_value=0.0,
                                value=float(pedido['cantidad_recibida']),
                                step=0.1,
                                key=f"cantidad_recibida_{pedido['id']}"
                            )
                            
                            # Actualizar estado
                            nuevo_estado = st.selectbox(
                                "Estado:",
                                ["PENDIENTE", "EN_TRANSITO", "RECIBIDO"],
                                index=["PENDIENTE", "EN_TRANSITO", "RECIBIDO"].index(pedido['estado']) if pedido['estado'] in ["PENDIENTE", "EN_TRANSITO", "RECIBIDO"] else 0,
                                key=f"estado_{pedido['id']}"
                            )
                            
                            # Checkbox para marcar como completado
                            marcar_completado = st.checkbox(
                                "✅ Marcar como completado",
                                key=f"completado_{pedido['id']}"
                            )
                            
                            # Botón para actualizar
                            if st.button(f"💾 Actualizar", key=f"actualizar_{pedido['id']}", type="primary"):
                                try:
                                    fecha_entrega_real = datetime.now().strftime("%Y-%m-%d") if marcar_completado else None
                                    
                                    actualizar_estado_pedido(
                                        pedido_id=pedido['id'],
                                        cantidad_recibida=nueva_cantidad,
                                        completado=1 if marcar_completado else 0,
                                        estado=nuevo_estado,
                                        fecha_entrega_real=fecha_entrega_real
                                    )
                                    
                                    # Si está completado y se recibió mercancía, actualizar stock
                                    if marcar_completado and nueva_cantidad > 0:
                                        actualizar_stock_desde_pedido(pedido['codigo_producto'], nueva_cantidad)
                                        st.success(f"✅ Pedido completado y stock actualizado (+{nueva_cantidad})")
                                    else:
                                        st.success("✅ Pedido actualizado exitosamente")
                                    
                                    time.sleep(1)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al actualizar: {str(e)}")
                            
                            # Botón para eliminar
                            if st.button(f"🗑️ Eliminar", key=f"eliminar_{pedido['id']}", type="secondary"):
                                if st.button(f"⚠️ Confirmar eliminación", key=f"confirmar_eliminar_{pedido['id']}", type="secondary"):
                                    try:
                                        eliminar_pedido(pedido['id'])
                                        st.success("✅ Pedido eliminado exitosamente")
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error al eliminar: {str(e)}")
                        
                        elif not es_admin:
                            st.info("🔒 Modo solo lectura")
                        else:
                            st.success("✅ Completado")
                
                st.divider()
        
        else:
            st.info("📋 No hay pedidos registrados")
            st.write("💡 Ve a la pestaña 'Productos con Stock Bajo' para crear nuevos pedidos de reabastecimiento")
    
    with tab3:
        st.subheader("📊 Resumen y Estadísticas")
        
        pedidos_df = obtener_pedidos_activos()
        productos_bajo_stock = obtener_productos_bajo_stock()
        
        # Métricas generales
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        
        with col_met1:
            total_pedidos = len(pedidos_df)
            st.metric("📝 Total Pedidos", total_pedidos)
        
        with col_met2:
            pedidos_pendientes = len(pedidos_df[pedidos_df['completado'] == 0]) if not pedidos_df.empty else 0
            st.metric("⏳ Pedidos Pendientes", pedidos_pendientes)
        
        with col_met3:
            productos_criticos = len(productos_bajo_stock)
            st.metric("🚨 Productos Críticos", productos_criticos)
        
        with col_met4:
            if not pedidos_df.empty:
                inversion_total = pedidos_df[pedidos_df['completado'] == 0]['costo_total'].sum()
                st.metric("💰 Inversión Pedidos", f"${inversion_total:.2f}")
            else:
                st.metric("💰 Inversión Pedidos", "$0.00")
        
        # Nueva fila de métricas para reabastecimiento
        st.divider()
        st.write("### 💵 Inversión para Reabastecimiento Completo")
        
        col_inv1, col_inv2, col_inv3 = st.columns(3)
        
        with col_inv1:
            if not productos_bajo_stock.empty:
                # Calcular inversión necesaria para alcanzar stock mínimo
                inversion_minimo = (productos_bajo_stock['cantidad_necesaria'] * productos_bajo_stock['precio_compra']).sum()
                st.metric(
                    "📊 Hasta Stock Mínimo", 
                    f"${inversion_minimo:.2f}",
                    help="Inversión necesaria para que todos los productos alcancen su stock mínimo"
                )
            else:
                st.metric("📊 Hasta Stock Mínimo", "$0.00")
        
        with col_inv2:
            if not productos_bajo_stock.empty and 'cantidad_hasta_maximo' in productos_bajo_stock.columns:
                # Calcular inversión necesaria para alcanzar stock máximo
                inversion_maximo = (productos_bajo_stock['cantidad_hasta_maximo'] * productos_bajo_stock['precio_compra']).sum()
                st.metric(
                    "🎯 Hasta Stock Máximo", 
                    f"${inversion_maximo:.2f}",
                    help="Inversión necesaria para que todos los productos alcancen su stock máximo (capacidad completa)"
                )
            else:
                st.metric("🎯 Hasta Stock Máximo", "$0.00")
        
        with col_inv3:
            if not productos_bajo_stock.empty and 'cantidad_hasta_maximo' in productos_bajo_stock.columns:
                # Calcular diferencia de inversión
                inversion_minimo = (productos_bajo_stock['cantidad_necesaria'] * productos_bajo_stock['precio_compra']).sum()
                inversion_maximo = (productos_bajo_stock['cantidad_hasta_maximo'] * productos_bajo_stock['precio_compra']).sum()
                diferencia = inversion_maximo - inversion_minimo
                st.metric(
                    "💎 Inversión Adicional", 
                    f"${diferencia:.2f}",
                    help="Diferencia entre alcanzar stock mínimo vs stock máximo"
                )
            else:
                st.metric("💎 Inversión Adicional", "$0.00")
        
        # Exportar datos
        st.divider()
        st.subheader("📤 Exportar Datos")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            if not pedidos_df.empty:
                csv_pedidos = pedidos_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📄 Descargar Pedidos (CSV)",
                    data=csv_pedidos,
                    file_name=f'pedidos_reabastecimiento_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv'
                )
        
        with col_exp2:
            if not productos_bajo_stock.empty:
                csv_stock_bajo = productos_bajo_stock.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📄 Descargar Stock Bajo (CSV)",
                    data=csv_stock_bajo,
                    file_name=f'productos_stock_bajo_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv'
                )
        
        # Mostrar información adicional
        if not pedidos_df.empty:
            st.write("### 📈 Estadísticas Detalladas")
            
            # Estados de pedidos
            if 'estado' in pedidos_df.columns:
                estados_count = pedidos_df['estado'].value_counts()
                st.write("**Distribución por Estado:**")
                for estado, count in estados_count.items():
                    st.write(f"• {estado}: {count} pedidos")
            
            # Proveedores más utilizados
            if 'proveedor' in pedidos_df.columns:
                proveedores = pedidos_df[pedidos_df['proveedor'] != '']['proveedor'].value_counts().head(5)
                if not proveedores.empty:
                    st.write("**Top 5 Proveedores:**")
                    for proveedor, count in proveedores.items():
                        st.write(f"• {proveedor}: {count} pedidos")