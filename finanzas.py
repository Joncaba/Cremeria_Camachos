import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import time
from sync_manager import get_sync_manager

# Inicializar gestor de sincronización
sync = get_sync_manager()

# Ruta de la base de datos
DB_PATH = "pos_cremeria.db"

# Crear tablas para egresos e ingresos adicionales
def crear_tablas_finanzas():
    """Crear tablas para gestión financiera completa"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Tabla para egresos adicionales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS egresos_adicionales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL,
                observaciones TEXT,
                usuario TEXT DEFAULT 'Sistema'
            )
        ''')
        
        # Tabla para ingresos pasivos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingresos_pasivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL,
                observaciones TEXT,
                usuario TEXT DEFAULT 'Sistema'
            )
        ''')
        
        conn.commit()
    except Exception as e:
        print(f"Error al crear tablas de finanzas: {e}")
        conn.rollback()
    finally:
        conn.close()

def mostrar():
    st.title("📊 Reportes Financieros")
    
    # Crear tablas si no existen
    crear_tablas_finanzas()
    
    # Sincronizar datos desde Supabase al inicio (solo si hay conexión)
    if sync.is_online():
        with st.spinner('🔄 Sincronizando datos desde Supabase...'):
            resultado_ordenes = sync.sync_ordenes_compra_from_supabase()
            
            if resultado_ordenes.get('success', 0) > 0:
                st.toast(f"✅ {resultado_ordenes['success']} órdenes de compra sincronizadas")

    # CSS personalizado para agrandar tabs con fondo negro y letras blancas/negras
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
        color: white !important;
    }
    
    .stTabs [data-baseweb="tab"] p {
        font-size: 18px !important;
        font-weight: bold !important;
        margin: 0;
        line-height: 1.2;
        color: #ecf0f1 !important;
    }
    
    .stTabs [aria-selected="true"] p {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) p {
        color: #bdc3c7 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #34495e;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stTabs [data-baseweb="tab"]:hover p {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Crear tabs para organizar mejor la información con iconos más grandes
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 **RESUMEN GENERAL**", 
        "🗓️ **VENTAS POR DÍA**", 
        "📋 **LISTADO DE VENTAS**", 
        "💰 **GESTIÓN FINANCIERA**",
        "💾 **EXPORTAR REPORTES**"
    ])
    
    with tab1:
        mostrar_resumen_general()
    
    with tab2:
        mostrar_ventas_por_dia()
    
    with tab3:
        mostrar_listado_ventas()
    
    with tab4:
        mostrar_gestion_financiera()
    
    with tab5:
        mostrar_exportar_reportes()

def mostrar_gestion_financiera():
    st.subheader("💰 Gestión Financiera Completa")
    
    # CSS personalizado para sub-tabs con tema oscuro
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0px 15px;
        background-color: #34495e;
        border-radius: 8px;
        border: 1px solid #2c3e50;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #e74c3c;
        border-color: #c0392b;
        color: white !important;
    }
    
    .stTabs [data-baseweb="tab"] p {
        font-size: 16px !important;
        font-weight: 600 !important;
        margin: 0;
        line-height: 1.2;
        color: #ecf0f1 !important;
    }
    
    .stTabs [aria-selected="true"] p {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) p {
        color: #bdc3c7 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e74c3c;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .stTabs [data-baseweb="tab"]:hover p {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sub-tabs para organizar la gestión financiera con iconos más grandes
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "📊 **RESUMEN FINANCIERO**",
        "📉 **REGISTRAR EGRESOS**", 
        "📈 **REGISTRAR INGRESOS**",
        "📋 **HISTORIAL FINANCIERO**"
    ])
    
    with subtab1:
        mostrar_resumen_financiero_completo()
    
    with subtab2:
        mostrar_registro_egresos()
    
    with subtab3:
        mostrar_registro_ingresos()
    
    with subtab4:
        mostrar_historial_financiero()

def mostrar_resumen_financiero_completo():
    st.subheader("📊 Resumen Financiero Completo")
    
    # Selector de período
    col_periodo1, col_periodo2, col_periodo3 = st.columns(3)
    
    with col_periodo1:
        fecha_desde_fin = st.date_input(
            "📅 Desde:", 
            value=date.today().replace(day=1),
            key="fecha_desde_financiero"
        )
    
    with col_periodo2:
        fecha_hasta_fin = st.date_input(
            "📅 Hasta:", 
            value=date.today(),
            key="fecha_hasta_financiero"
        )
    
    with col_periodo3:
        periodo_str = f"{fecha_desde_fin.strftime('%d/%m/%Y')} - {fecha_hasta_fin.strftime('%d/%m/%Y')}"
        st.info(f"📊 **Período:** {periodo_str}")
    
    # Obtener datos del período
    fecha_desde_str = fecha_desde_fin.strftime('%Y-%m-%d')
    fecha_hasta_str = fecha_hasta_fin.strftime('%Y-%m-%d')
    
    # INGRESOS
    st.subheader("💚 INGRESOS")
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Ingresos por ventas
        ventas_query = """
            SELECT SUM(total) as total_ventas
            FROM ventas 
            WHERE DATE(fecha) BETWEEN ? AND ?
        """
        result_ventas = conn.execute(ventas_query, (fecha_desde_str, fecha_hasta_str)).fetchone()
        ingresos_ventas = float(result_ventas[0]) if result_ventas[0] else 0.0
        
        # Debug: mostrar cuántas ventas se encontraron
        debug_query = f"SELECT COUNT(*) as cantidad FROM ventas WHERE DATE(fecha) BETWEEN '{fecha_desde_str}' AND '{fecha_hasta_str}'"
        debug_result = conn.execute(debug_query).fetchone()
        
        # Ingresos pasivos
        ingresos_pasivos_query = """
            SELECT SUM(monto) as total_pasivos
            FROM ingresos_pasivos 
            WHERE DATE(fecha) BETWEEN ? AND ?
        """
        result_pasivos = conn.execute(ingresos_pasivos_query, (fecha_desde_str, fecha_hasta_str)).fetchone()
        ingresos_pasivos_total = float(result_pasivos[0]) if result_pasivos[0] else 0.0
        
        # Egresos adicionales por tipo
        egresos_query = """
            SELECT tipo, SUM(monto) as total_tipo
            FROM egresos_adicionales 
            WHERE DATE(fecha) BETWEEN ? AND ?
            GROUP BY tipo
        """
        egresos_df = pd.read_sql_query(egresos_query, conn, params=(fecha_desde_str, fecha_hasta_str))
    finally:
        conn.close()
    
    # Total ingresos
    total_ingresos = ingresos_ventas + ingresos_pasivos_total
    
    col_ing1, col_ing2, col_ing3 = st.columns(3)
    
    with col_ing1:
        st.metric("🛒 Ingresos por Ventas", f"${ingresos_ventas:,.2f}")
    
    with col_ing2:
        st.metric("💎 Ingresos Pasivos", f"${ingresos_pasivos_total:,.2f}")
    
    with col_ing3:
        st.metric("💚 **TOTAL INGRESOS**", f"${total_ingresos:,.2f}")
    
    # Debug info
    with st.expander("🔍 Información de Debug"):
        st.write(f"**Período consultado:** {fecha_desde_str} a {fecha_hasta_str}")
        st.write(f"**Ventas encontradas:** {debug_result[0]} registros")
        st.write(f"**Total de ventas:** ${ingresos_ventas:,.2f}")
        
        # Mostrar todas las ventas del período para verificar
        conn = sqlite3.connect(DB_PATH)
        try:
            ventas_debug = pd.read_sql_query(
                f"SELECT fecha, codigo, nombre, total FROM ventas WHERE DATE(fecha) BETWEEN '{fecha_desde_str}' AND '{fecha_hasta_str}' ORDER BY fecha DESC",
                conn
            )
            if not ventas_debug.empty:
                st.write(f"**Listado de {len(ventas_debug)} ventas:**")
                st.dataframe(ventas_debug, use_container_width=True)
            else:
                st.warning("No se encontraron ventas en el período seleccionado")
        finally:
            conn.close()
    
    st.divider()
    
    # EGRESOS
    st.subheader("❤️ EGRESOS")
    
    if not egresos_df.empty:
        col_egr_count = len(egresos_df)
        if col_egr_count > 0:
            cols_egresos = st.columns(min(col_egr_count, 4))  # Máximo 4 columnas
            
            total_egresos_adicionales = 0
            for i, (_, egreso) in enumerate(egresos_df.iterrows()):
                if i < 4:  # Mostrar solo los primeros 4
                    with cols_egresos[i]:
                        icono = {
                            "Servicios": "⚡",
                            "Agua": "💧",
                            "Internet": "🌐",
                            "Luz": "💡",
                            "Otros": "📝"
                        }.get(egreso['tipo'], "💸")
                        
                        st.metric(f"{icono} {egreso['tipo']}", f"${egreso['total_tipo']:,.2f}")
                
                total_egresos_adicionales += egreso['total_tipo']
            
            # Si hay más de 4 tipos, mostrar el resto
            if col_egr_count > 4:
                with st.expander(f"Ver {col_egr_count - 4} tipos adicionales de egresos"):
                    for i, (_, egreso) in enumerate(egresos_df.iterrows()):
                        if i >= 4:
                            icono = {
                                "Servicios": "⚡",
                                "Agua": "💧", 
                                "Internet": "🌐",
                                "Luz": "💡",
                                "Otros": "📝"
                            }.get(egreso['tipo'], "💸")
                            st.write(f"{icono} **{egreso['tipo']}:** ${egreso['total_tipo']:,.2f}")
    else:
        total_egresos_adicionales = 0.0
        st.info("No hay egresos registrados en este período")
    
    # Estimación de costo de mercancía (60% de ventas por defecto)
    costo_mercancia_estimado = ingresos_ventas * 0.6
    
    col_egr_total1, col_egr_total2, col_egr_total3 = st.columns(3)
    
    with col_egr_total1:
        st.metric("📦 Costo Mercancía (Est.)", f"${costo_mercancia_estimado:,.2f}")
    
    with col_egr_total2:
        st.metric("💸 Egresos Adicionales", f"${total_egresos_adicionales:,.2f}")
    
    with col_egr_total3:
        total_egresos = costo_mercancia_estimado + total_egresos_adicionales
        st.metric("❤️ **TOTAL EGRESOS**", f"${total_egresos:,.2f}")
    
    st.divider()
    
    # BALANCE FINAL
    st.subheader("⚖️ BALANCE FINAL")
    
    utilidad_neta = total_ingresos - total_egresos
    margen_utilidad = (utilidad_neta / total_ingresos * 100) if total_ingresos > 0 else 0
    
    col_bal1, col_bal2, col_bal3 = st.columns(3)
    
    with col_bal1:
        color_utilidad = "normal" if utilidad_neta >= 0 else "inverse"
        delta_utilidad = f"+${utilidad_neta:,.2f}" if utilidad_neta >= 0 else f"-${abs(utilidad_neta):,.2f}"
        st.metric(
            "💰 Utilidad Neta", 
            f"${utilidad_neta:,.2f}",
            delta=delta_utilidad,
            delta_color=color_utilidad
        )
    
    with col_bal2:
        st.metric("📊 Margen de Utilidad", f"{margen_utilidad:.1f}%")
    
    with col_bal3:
        estado_financiero = "🟢 SALUDABLE" if utilidad_neta >= 0 else "🔴 DÉFICIT"
        st.metric("📈 Estado", estado_financiero)
    
    # Gráficos financieros
    if total_ingresos > 0 or total_egresos > 0:
        st.divider()
        st.subheader("📊 Análisis Visual")
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            # Gráfico de ingresos vs egresos
            fig_balance = px.bar(
                x=['Ingresos', 'Egresos'],
                y=[total_ingresos, total_egresos],
                title='Comparativo Ingresos vs Egresos',
                color=['Ingresos', 'Egresos'],
                color_discrete_map={'Ingresos': '#2ecc71', 'Egresos': '#e74c3c'}
            )
            fig_balance.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_balance, width='stretch')
        
        with col_graf2:
            # Gráfico de composición de egresos
            if not egresos_df.empty:
                egresos_plot = egresos_df.copy()
                # Agregar costo de mercancía
                nuevo_row = pd.DataFrame({
                    'tipo': ['Costo Mercancía'],
                    'total_tipo': [costo_mercancia_estimado]
                })
                egresos_plot = pd.concat([egresos_plot, nuevo_row], ignore_index=True)
                
                fig_egresos = px.pie(
                    egresos_plot,
                    values='total_tipo',
                    names='tipo',
                    title='Composición de Egresos'
                )
                fig_egresos.update_layout(height=400)
                st.plotly_chart(fig_egresos, use_container_width=True)

def mostrar_registro_egresos():
    st.subheader("📉 Registrar Egresos")
    
    # Sub-tabs para egresos manuales y órdenes de compra
    subtab_egr1, subtab_egr2 = st.tabs(["💸 Egresos Manuales", "🧾 Órdenes de Compra"])
    
    with subtab_egr1:
        mostrar_egresos_manuales()
    
    with subtab_egr2:
        mostrar_ordenes_compra()

def mostrar_egresos_manuales():
    """Formulario para registrar egresos manuales"""
    col_egr1, col_egr2 = st.columns([2, 1])
    
    with col_egr1:
        # Formulario para registrar egreso
        with st.form("form_egresos"):
            st.write("**📝 Nuevo Egreso**")
            
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                tipo_egreso = st.selectbox(
                    "💸 Tipo de Egreso:",
                    ["Luz", "Agua", "Internet", "Servicios", "Otros"],
                    help="Selecciona el tipo de gasto"
                )
                
                monto_egreso = st.number_input(
                    "💰 Monto:",
                    min_value=0.01,
                    step=0.01,
                    help="Cantidad del gasto en pesos"
                )
            
            with col_form2:
                fecha_egreso = st.date_input(
                    "📅 Fecha:",
                    value=date.today(),
                    help="Fecha en que se realizó el gasto"
                )
                
                descripcion_egreso = st.text_input(
                    "📋 Descripción:",
                    placeholder="Ej: Recibo de luz del mes de octubre",
                    help="Descripción detallada del gasto"
                )
            
            observaciones_egreso = st.text_area(
                "📝 Observaciones (opcional):",
                placeholder="Información adicional sobre este egreso...",
                height=80
            )
            
            submitted_egreso = st.form_submit_button("💾 Registrar Egreso", type="primary")
            
            if submitted_egreso and descripcion_egreso and monto_egreso > 0:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                try:
                    fecha_egreso_str = fecha_egreso.strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        INSERT INTO egresos_adicionales (fecha, tipo, descripcion, monto, observaciones)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (fecha_egreso_str, tipo_egreso, descripcion_egreso, monto_egreso, observaciones_egreso))
                    
                    egreso_id = cursor.lastrowid
                    conn.commit()
                    
                    # Sincronizar a Supabase automáticamente
                    if sync.is_online():
                        try:
                            cursor.execute("SELECT * FROM egresos_adicionales WHERE id = ?", (egreso_id,))
                            egreso = cursor.fetchone()
                            if egreso:
                                egreso_dict = {
                                    'id': egreso[0],
                                    'fecha': egreso[1],
                                    'tipo': egreso[2],
                                    'descripcion': egreso[3],
                                    'monto': egreso[4],
                                    'observaciones': egreso[5],
                                    'usuario': egreso[6] if len(egreso) > 6 else 'Sistema'
                                }
                                sync.sync_egreso_to_supabase(egreso_dict)
                        except Exception as sync_error:
                            print(f"Error en sincronización: {sync_error}")
                    
                    st.success(f"✅ Egreso registrado: {tipo_egreso} - ${monto_egreso:.2f}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al registrar egreso: {str(e)}")
                    conn.rollback()
                finally:
                    conn.close()
            
            elif submitted_egreso:
                if not descripcion_egreso:
                    st.error("❌ La descripción es obligatoria")
                if monto_egreso <= 0:
                    st.error("❌ El monto debe ser mayor a 0")
    
    with col_egr2:
        # Resumen de egresos del mes actual
        st.write("**📊 Egresos del Mes Actual**")
        
        conn = sqlite3.connect(DB_PATH)
        try:
            primer_dia_mes = date.today().replace(day=1)
            egresos_mes_query = """
                SELECT tipo, SUM(monto) as total
                FROM egresos_adicionales 
                WHERE DATE(fecha) >= ?
                GROUP BY tipo
                ORDER BY total DESC
            """
            
            egresos_mes_df = pd.read_sql_query(
                egresos_mes_query, 
                conn, 
                params=[primer_dia_mes.strftime('%Y-%m-%d')]
            )
        finally:
            conn.close()
        
        if not egresos_mes_df.empty:
            total_mes = egresos_mes_df['total'].sum()
            st.metric("💸 Total del Mes", f"${total_mes:.2f}")
            
            for _, egreso in egresos_mes_df.iterrows():
                porcentaje = (egreso['total'] / total_mes) * 100
                st.write(f"• **{egreso['tipo']}:** ${egreso['total']:.2f} ({porcentaje:.1f}%)")
        else:
            st.info("No hay egresos registrados este mes")
    
    # Tabla de egresos recientes
    st.divider()
    st.subheader("📋 Egresos Recientes")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        egresos_recientes_query = """
            SELECT fecha, tipo, descripcion, monto, observaciones
            FROM egresos_adicionales 
            ORDER BY fecha DESC 
            LIMIT 10
        """
        
        egresos_recientes_df = pd.read_sql_query(egresos_recientes_query, conn)
    finally:
        conn.close()
    
    if not egresos_recientes_df.empty:
        # Formatear fecha para mejor visualización
        egresos_recientes_df['fecha'] = pd.to_datetime(egresos_recientes_df['fecha']).dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(
            egresos_recientes_df,
            column_config={
                "fecha": "📅 Fecha",
                "tipo": "💸 Tipo",
                "descripcion": "📋 Descripción",
                "monto": st.column_config.NumberColumn("💰 Monto", format="$%.2f"),
                "observaciones": "📝 Observaciones"
            },
            hide_index=True,
            width='stretch'
        )
    else:
        st.info("No hay egresos registrados")

def mostrar_ordenes_compra():
    """Mostrar órdenes de compra pendientes de pago"""
    st.write("### 🧾 Órdenes de Compra")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        # Obtener órdenes de compra con información de pedidos
        ordenes_query = """
            SELECT 
                oc.id, 
                oc.fecha_creacion, 
                oc.total_orden, 
                oc.estado, 
                oc.fecha_pago, 
                oc.notas,
                oc.pedido_id,
                p.fecha_pedido,
                p.fecha_entrega_esperada
            FROM ordenes_compra oc
            LEFT JOIN pedidos p ON oc.pedido_id = p.id
            ORDER BY 
                CASE WHEN oc.estado = 'PENDIENTE' THEN 0 ELSE 1 END,
                oc.fecha_creacion DESC
        """
        ordenes_df = pd.read_sql_query(ordenes_query, conn)
    finally:
        conn.close()
    
    if ordenes_df.empty:
        st.info("📋 No hay órdenes de compra registradas")
        return
    
    # Filtros
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        mostrar_pagadas = st.checkbox("Mostrar órdenes pagadas", value=False, key="mostrar_ordenes_pagadas")
    
    with col_filtro2:
        if not mostrar_pagadas:
            ordenes_pendientes = len(ordenes_df[ordenes_df['estado'] == 'PENDIENTE'])
            st.metric("⏳ Órdenes Pendientes", ordenes_pendientes)
    
    # Filtrar por estado
    if not mostrar_pagadas:
        ordenes_df = ordenes_df[ordenes_df['estado'] == 'PENDIENTE']
    
    # Mostrar órdenes
    for _, orden in ordenes_df.iterrows():
        with st.expander(
            f"{'🟡' if orden['estado'] == 'PENDIENTE' else '✅'} Orden #{orden['id']} - ${orden['total_orden']:.2f} - {orden['estado']}",
            expanded=(orden['estado'] == 'PENDIENTE')
        ):
            col_orden1, col_orden2 = st.columns([2, 1])
            
            with col_orden1:
                st.write(f"**📅 Fecha creación:** {pd.to_datetime(orden['fecha_creacion']).strftime('%d/%m/%Y %H:%M')}")
                
                if orden['fecha_pedido']:
                    st.write(f"**📝 Fecha del pedido:** {orden['fecha_pedido']}")
                
                if orden['fecha_entrega_esperada']:
                    st.write(f"**🚚 Entrega esperada:** {orden['fecha_entrega_esperada']}")
                
                st.write(f"**💰 Total orden:** ${orden['total_orden']:.2f}")
                st.write(f"**📊 Estado:** {orden['estado']}")
                
                if orden['fecha_pago']:
                    st.write(f"**✅ Fecha pago:** {orden['fecha_pago']}")
                
                st.divider()
                
                # Obtener productos de esta orden usando pedido_id
                productos_orden = pd.DataFrame()
                if orden['pedido_id']:
                    conn = sqlite3.connect(DB_PATH)
                    try:
                        productos_query = """
                            SELECT 
                                nombre_producto, 
                                cantidad_recibida as cantidad, 
                                precio_unitario, 
                                subtotal,
                                proveedor
                            FROM pedidos_items
                            WHERE pedido_id = ?
                            ORDER BY nombre_producto
                        """
                        productos_orden = pd.read_sql_query(productos_query, conn, params=[orden['pedido_id']])
                    except Exception as e:
                        st.error(f"Error al obtener productos: {str(e)}")
                    finally:
                        conn.close()
                
                if not productos_orden.empty:
                    st.write("**📦 Productos en esta orden:**")
                    
                    # Mostrar tabla detallada
                    df_display = productos_orden.copy()
                    st.dataframe(
                        df_display,
                        column_config={
                            "nombre_producto": "🛍️ Producto",
                            "cantidad": st.column_config.NumberColumn("📊 Cantidad", format="%.2f"),
                            "precio_unitario": st.column_config.NumberColumn("💲 Precio Unit.", format="$%.2f"),
                            "subtotal": st.column_config.NumberColumn("💰 Subtotal", format="$%.2f"),
                            "proveedor": "🏪 Proveedor"
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=200
                    )
                    
                    # Resumen de productos
                    total_productos = len(productos_orden)
                    cantidad_total = productos_orden['cantidad'].sum()
                    st.markdown(f"""
                    ---
                    **📦 Resumen:**
                    - **Número de productos:** {total_productos}
                    - **Cantidad total:** {cantidad_total:.2f}
                    - **Costo total:** ${orden['total_orden']:.2f}
                    """)
                elif orden['pedido_id']:
                    st.warning("⚠️ No se encontraron productos para esta orden")
            
            with col_orden2:
                if orden['estado'] == 'PENDIENTE':
                    st.write("**⚙️ Acciones:**")
                    
                    # Botón para marcar como pagada
                    if st.button(f"✅ Marcar como Pagada", key=f"pagar_orden_{orden['id']}", type="primary", use_container_width=True):
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        
                        try:
                            fecha_pago = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Obtener número de productos para la observación
                            num_productos = len(productos_orden) if not productos_orden.empty else 0
                            
                            # Actualizar orden de compra
                            cursor.execute("""
                                UPDATE ordenes_compra 
                                SET estado = 'PAGADA', fecha_pago = ?
                                WHERE id = ?
                            """, (fecha_pago, orden['id']))
                            
                            # Registrar en egresos adicionales
                            cursor.execute("""
                                INSERT INTO egresos_adicionales (fecha, tipo, descripcion, monto, observaciones)
                                VALUES (?, 'Compra de Mercancía', ?, ?, ?)
                            """, (
                                fecha_pago,
                                f"Orden de Compra #{orden['id']}",
                                orden['total_orden'],
                                f"Pago de orden de compra con {num_productos} productos"
                            ))
                            
                            egreso_id = cursor.lastrowid
                            
                            # Marcar el pedido asociado como COMPLETADO
                            cursor.execute("""
                                UPDATE pedidos 
                                SET estado = 'COMPLETADO'
                                WHERE orden_compra_id = ?
                            """, (orden['id'],))
                            
                            conn.commit()
                            
                            # Sincronizar con Supabase
                            if sync.is_online():
                                # Sincronizar la orden actualizada
                                conn_temp = sqlite3.connect(DB_PATH)
                                conn_temp.row_factory = sqlite3.Row
                                cursor_temp = conn_temp.cursor()
                                cursor_temp.execute("SELECT * FROM ordenes_compra WHERE id = ?", (orden['id'],))
                                orden_actualizada = cursor_temp.fetchone()
                                conn_temp.close()
                                
                                if orden_actualizada:
                                    exito, error = sync.sync_orden_compra_to_supabase(dict(orden_actualizada))
                                    if exito:
                                        st.toast("☁️ Orden sincronizada con Supabase")
                                
                                # Sincronizar el pedido asociado (ahora COMPLETADO)
                                cursor_temp = conn_temp.cursor()
                                cursor_temp.execute("SELECT * FROM pedidos WHERE orden_compra_id = ?", (orden['id'],))
                                pedido_actualizado = cursor_temp.fetchone()
                                if pedido_actualizado:
                                    sync.sync_pedido_to_supabase(dict(pedido_actualizado))
                                
                                # Sincronizar el egreso creado
                                cursor.execute("SELECT * FROM egresos_adicionales WHERE id = ?", (egreso_id,))
                                egreso = cursor.fetchone()
                                if egreso:
                                    egreso_dict = {
                                        'id': egreso[0], 'fecha': egreso[1], 'tipo': egreso[2],
                                        'descripcion': egreso[3], 'monto': egreso[4],
                                        'observaciones': egreso[5], 'usuario': egreso[6] if len(egreso) > 6 else 'Sistema'
                                    }
                                    sync.sync_egreso_to_supabase(egreso_dict)
                            
                            st.success(f"✅ Orden #{orden['id']} marcada como pagada, registrada en egresos y pedido completado")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                            
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ Error: {str(e)}")
                        finally:
                            conn.close()
                    
                    # Campo para notas
                    notas_orden = st.text_area(
                        "📝 Notas:",
                        value=orden['notas'] if orden['notas'] else "",
                        key=f"notas_orden_{orden['id']}",
                        height=80
                    )
                    
                    if st.button(f"💾 Guardar Notas", key=f"guardar_notas_{orden['id']}", use_container_width=True):
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        
                        try:
                            cursor.execute("""
                                UPDATE ordenes_compra 
                                SET notas = ?
                                WHERE id = ?
                            """, (notas_orden, orden['id']))
                            
                            conn.commit()
                            
                            # Sincronizar con Supabase
                            if sync.is_online():
                                conn_temp = sqlite3.connect(DB_PATH)
                                conn_temp.row_factory = sqlite3.Row
                                cursor_temp = conn_temp.cursor()
                                cursor_temp.execute("SELECT * FROM ordenes_compra WHERE id = ?", (orden['id'],))
                                orden_actualizada = cursor_temp.fetchone()
                                conn_temp.close()
                                
                                if orden_actualizada:
                                    exito, error = sync.sync_orden_compra_to_supabase(dict(orden_actualizada))
                                    if exito:
                                        st.toast("☁️ Notas sincronizadas con Supabase")
                            
                            st.success("✅ Notas guardadas")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                        finally:
                            conn.close()
                else:
                    st.success("✅ Orden pagada")
                    if orden['notas']:
                        st.info(f"📝 Notas: {orden['notas']}")

def mostrar_registro_ingresos():
    st.subheader("📈 Registrar Ingresos Pasivos")
    
    col_ing1, col_ing2 = st.columns([2, 1])
    
    with col_ing1:
        # Formulario para registrar ingreso pasivo
        with st.form("form_ingresos"):
            st.write("**📝 Nuevo Ingreso Pasivo**")
            
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                descripcion_ingreso = st.text_input(
                    "📋 Descripción:",
                    placeholder="Ej: Renta de local, Dividendos, Intereses...",
                    help="Descripción del tipo de ingreso pasivo"
                )
                
                monto_ingreso = st.number_input(
                    "💰 Monto:",
                    min_value=0.01,
                    step=0.01,
                    help="Cantidad del ingreso en pesos"
                )
            
            with col_form2:
                fecha_ingreso = st.date_input(
                    "📅 Fecha:",
                    value=date.today(),
                    help="Fecha en que se recibió el ingreso"
                )
            
            observaciones_ingreso = st.text_area(
                "📝 Observaciones (opcional):",
                placeholder="Información adicional sobre este ingreso...",
                height=80
            )
            
            submitted_ingreso = st.form_submit_button("💾 Registrar Ingreso", type="primary")
            
            if submitted_ingreso and descripcion_ingreso and monto_ingreso > 0:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                try:
                    fecha_ingreso_str = fecha_ingreso.strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        INSERT INTO ingresos_pasivos (fecha, descripcion, monto, observaciones)
                        VALUES (?, ?, ?, ?)
                    ''', (fecha_ingreso_str, descripcion_ingreso, monto_ingreso, observaciones_ingreso))
                    
                    ingreso_id = cursor.lastrowid
                    conn.commit()
                    
                    # Sincronizar a Supabase automáticamente
                    if sync.is_online():
                        try:
                            cursor.execute("SELECT * FROM ingresos_pasivos WHERE id = ?", (ingreso_id,))
                            ingreso = cursor.fetchone()
                            if ingreso:
                                ingreso_dict = {
                                    'id': ingreso[0],
                                    'fecha': ingreso[1],
                                    'descripcion': ingreso[2],
                                    'monto': ingreso[3],
                                    'observaciones': ingreso[4],
                                    'usuario': ingreso[5] if len(ingreso) > 5 else 'Sistema'
                                }
                                sync.sync_ingreso_to_supabase(ingreso_dict)
                        except Exception as sync_error:
                            print(f"Error en sincronización: {sync_error}")
                    
                    st.success(f"✅ Ingreso registrado: {descripcion_ingreso} - ${monto_ingreso:.2f}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al registrar ingreso: {str(e)}")
                    conn.rollback()
                finally:
                    conn.close()
            
            elif submitted_ingreso:
                if not descripcion_ingreso:
                    st.error("❌ La descripción es obligatoria")
                if monto_ingreso <= 0:
                    st.error("❌ El monto debe ser mayor a 0")
    
    with col_ing2:
        # Resumen de ingresos del mes actual
        st.write("**📊 Ingresos del Mes Actual**")
        
        conn = sqlite3.connect(DB_PATH)
        try:
            primer_dia_mes = date.today().replace(day=1)
            ingresos_mes_query = """
                SELECT SUM(monto) as total_mes, COUNT(*) as cantidad
                FROM ingresos_pasivos 
                WHERE DATE(fecha) >= ?
            """
            
            result_ingresos_mes = conn.execute(
                ingresos_mes_query, 
                [primer_dia_mes.strftime('%Y-%m-%d')]
            ).fetchone()
        finally:
            conn.close()
        
        if result_ingresos_mes and result_ingresos_mes[0]:
            total_ingresos_mes = result_ingresos_mes[0]
            cantidad_ingresos = result_ingresos_mes[1]
            
            st.metric("💎 Total del Mes", f"${total_ingresos_mes:.2f}")
            st.metric("📊 Cantidad", f"{cantidad_ingresos} ingresos")
        else:
            st.info("No hay ingresos pasivos este mes")
    
    # Tabla de ingresos recientes
    st.divider()
    st.subheader("📋 Ingresos Recientes")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        ingresos_recientes_query = """
            SELECT fecha, descripcion, monto, observaciones
            FROM ingresos_pasivos 
            ORDER BY fecha DESC 
            LIMIT 10
        """
        
        ingresos_recientes_df = pd.read_sql_query(ingresos_recientes_query, conn)
    finally:
        conn.close()
    
    if not ingresos_recientes_df.empty:
        # Formatear fecha para mejor visualización
        ingresos_recientes_df['fecha'] = pd.to_datetime(ingresos_recientes_df['fecha']).dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(
            ingresos_recientes_df,
            column_config={
                "fecha": "📅 Fecha",
                "descripcion": "📋 Descripción",
                "monto": st.column_config.NumberColumn("💰 Monto", format="$%.2f"),
                "observaciones": "📝 Observaciones"
            },
            hide_index=True,
            width='stretch'
        )
    else:
        st.info("No hay ingresos pasivos registrados")

def mostrar_historial_financiero():
    st.subheader("📋 Historial Financiero Completo")
    
    # Filtros para el historial
    col_hist1, col_hist2, col_hist3 = st.columns(3)
    
    with col_hist1:
        fecha_desde_hist = st.date_input(
            "📅 Desde:", 
            value=date.today().replace(day=1),
            key="fecha_desde_historial"
        )
    
    with col_hist2:
        fecha_hasta_hist = st.date_input(
            "📅 Hasta:", 
            value=date.today(),
            key="fecha_hasta_historial"
        )
    
    with col_hist3:
        tipo_movimiento = st.selectbox(
            "🔍 Tipo:",
            ["Todos", "Ingresos Pasivos", "Egresos"]
        )
    
    fecha_desde_hist_str = fecha_desde_hist.strftime('%Y-%m-%d')
    fecha_hasta_hist_str = fecha_hasta_hist.strftime('%Y-%m-%d')
    
    # Obtener historial según filtros
    movimientos = []
    
    conn = sqlite3.connect(DB_PATH)
    try:
        if tipo_movimiento in ["Todos", "Ingresos Pasivos"]:
            # Obtener ingresos pasivos
            ingresos_query = """
                SELECT fecha, 'Ingreso Pasivo' as tipo, descripcion, monto, observaciones
                FROM ingresos_pasivos 
                WHERE DATE(fecha) BETWEEN ? AND ?
            """
            ingresos_df = pd.read_sql_query(ingresos_query, conn, params=(fecha_desde_hist_str, fecha_hasta_hist_str))
            if not ingresos_df.empty:
                movimientos.append(ingresos_df)
        
        if tipo_movimiento in ["Todos", "Egresos"]:
            # Obtener egresos
            egresos_query = """
                SELECT fecha, CONCAT('Egreso - ', tipo) as tipo, descripcion, -monto as monto, observaciones
                FROM egresos_adicionales 
                WHERE DATE(fecha) BETWEEN ? AND ?
            """
            egresos_df = pd.read_sql_query(egresos_query, conn, params=(fecha_desde_hist_str, fecha_hasta_hist_str))
            if not egresos_df.empty:
                movimientos.append(egresos_df)
    finally:
        conn.close()
    
    # Combinar y mostrar movimientos
    if movimientos:
        historial_df = pd.concat(movimientos, ignore_index=True)
        historial_df = historial_df.sort_values('fecha', ascending=False)
        
        # Calcular balance acumulado
        historial_df['balance_acumulado'] = historial_df['monto'].cumsum()
        
        # Mostrar resumen
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        
        with col_res1:
            total_movimientos = len(historial_df)
            st.metric("📊 Total Movimientos", total_movimientos)
        
        with col_res2:
            ingresos_total = historial_df[historial_df['monto'] > 0]['monto'].sum()
            st.metric("📈 Ingresos", f"${ingresos_total:.2f}")
        
        with col_res3:
            egresos_total = abs(historial_df[historial_df['monto'] < 0]['monto'].sum())
            st.metric("📉 Egresos", f"${egresos_total:.2f}")
        
        with col_res4:
            balance_neto = ingresos_total - egresos_total
            st.metric("⚖️ Balance", f"${balance_neto:.2f}")
        
        # Formatear tabla para mostrar
        historial_display = historial_df.copy()
        historial_display['fecha'] = pd.to_datetime(historial_display['fecha']).dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(
            historial_display,
            column_config={
                "fecha": "📅 Fecha",
                "tipo": "🔖 Tipo",
                "descripcion": "📋 Descripción",
                "monto": st.column_config.NumberColumn("💰 Monto", format="$%.2f"),
                "balance_acumulado": st.column_config.NumberColumn("⚖️ Balance Acum.", format="$%.2f"),
                "observaciones": "📝 Observaciones"
            },
            hide_index=True,
            width='stretch'
        )
        
        # Gráfico de evolución del balance
        if len(historial_df) > 1:
            st.divider()
            st.subheader("📊 Evolución del Balance")
            
            # Ordenar por fecha para el gráfico
            historial_grafico = historial_df.sort_values('fecha')
            
            fig_balance = px.line(
                historial_grafico,
                x='fecha',
                y='balance_acumulado',
                title='Evolución del Balance Financiero',
                markers=True,
                labels={'balance_acumulado': 'Balance ($)', 'fecha': 'Fecha'}
            )
            fig_balance.update_layout(height=400)
            st.plotly_chart(fig_balance, use_container_width=True)
    else:
        st.info("No hay movimientos financieros en el período seleccionado")

def mostrar_resumen_general():
    st.subheader("📈 Resumen General")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        ventas_df = pd.read_sql_query("SELECT * FROM ventas", conn)
        productos_df = pd.read_sql_query("SELECT * FROM productos", conn)
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return
    finally:
        conn.close()

    if ventas_df.empty:
        st.warning("No hay datos de ventas disponibles.")
        return

    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ingresos_totales = ventas_df['total'].sum()
        st.metric("💰 Ingresos Totales", f"${ingresos_totales:,.2f}")
    
    with col2:
        # Contar ventas por ticket (cada ticket agrupa varias filas/items)
        try:
            ticket_count = ventas_df['fecha'].nunique()
        except Exception:
            ticket_count = len(ventas_df)
        st.metric("🛒 Total Ventas", ticket_count)
    
    with col3:
        # Calcular ingresos del día actual
        hoy = date.today().strftime('%Y-%m-%d')
        ventas_hoy = ventas_df[ventas_df['fecha'].str.contains(hoy, na=False)]
        ingresos_hoy = ventas_hoy['total'].sum() if not ventas_hoy.empty else 0
        st.metric("📅 Ingresos Hoy", f"${ingresos_hoy:,.2f}")
    
    with col4:
        # Calcular ventas del mes actual
        mes_actual = date.today().strftime('%Y-%m')
        ventas_mes = ventas_df[ventas_df['fecha'].str.contains(mes_actual, na=False)]
        ingresos_mes = ventas_mes['total'].sum() if not ventas_mes.empty else 0
        st.metric("📊 Ingresos del Mes", f"${ingresos_mes:,.2f}")

    st.divider()

    # Gráficos de análisis
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        # Gráfico de productos más vendidos
        st.subheader("🏆 Productos más vendidos")
        if not ventas_df.empty:
            top_productos = ventas_df.groupby('nombre').agg({
                'cantidad': 'sum',
                'total': 'sum'
            }).reset_index()
            top_productos = top_productos.sort_values('cantidad', ascending=False).head(10)
            
            if not top_productos.empty:
                fig_top = px.bar(
                    top_productos, 
                    x='cantidad', 
                    y='nombre', 
                    orientation='h',
                    title='Top 10 Productos por Cantidad Vendida',
                    labels={'cantidad': 'Cantidad Vendida', 'nombre': 'Producto'},
                    color='cantidad',
                    color_continuous_scale='viridis'
                )
                fig_top.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("No hay datos suficientes para el gráfico")
        else:
            st.info("No hay ventas registradas")
    
    with col_graf2:
        # Gráfico de ventas por tipo de cliente
        st.subheader("👥 Ventas por Tipo de Cliente")
        if not ventas_df.empty and 'tipo_cliente' in ventas_df.columns:
            ventas_cliente = ventas_df.groupby('tipo_cliente')['total'].sum().reset_index()
            
            if not ventas_cliente.empty:
                fig_cliente = px.pie(
                    ventas_cliente,
                    values='total',
                    names='tipo_cliente',
                    title='Distribución de Ventas por Tipo de Cliente',
                    color_discrete_map={
                        'Normal': '#3498db',
                        'Mayoreo': '#e74c3c'
                    }
                )
                fig_cliente.update_traces(textposition='inside', textinfo='percent+label')
                fig_cliente.update_layout(height=400)
                st.plotly_chart(fig_cliente, use_container_width=True)
            else:
                st.info("No hay datos de tipos de cliente")
        else:
            st.info("No hay datos de tipos de cliente disponibles")

    # Análisis de métodos de pago
    st.divider()
    st.subheader("💳 Análisis de Métodos de Pago")
    
    if not ventas_df.empty:
        col_pago1, col_pago2 = st.columns(2)
        
        with col_pago1:
            # Calcular totales por método de pago
            metodos_pago = {
                'Efectivo': ventas_df['monto_efectivo'].sum() if 'monto_efectivo' in ventas_df.columns else 0,
                'Tarjeta': ventas_df['monto_tarjeta'].sum() if 'monto_tarjeta' in ventas_df.columns else 0,
                'Transferencia': ventas_df['monto_transferencia'].sum() if 'monto_transferencia' in ventas_df.columns else 0,
                'Crédito': ventas_df['monto_credito'].sum() if 'monto_credito' in ventas_df.columns else 0
            }
            
            # Filtrar métodos con monto > 0
            metodos_activos = {k: v for k, v in metodos_pago.items() if v > 0}
            
            if metodos_activos:
                # Mostrar métricas
                st.write("**💰 Totales por Método:**")
                for metodo, monto in metodos_activos.items():
                    icono = {'Efectivo': '💵', 'Tarjeta': '💳', 'Transferencia': '📱', 'Crédito': '📋'}.get(metodo, '💰')
                    st.metric(f"{icono} {metodo}", f"${monto:,.2f}")
            else:
                st.info("No hay datos de métodos de pago")
        
        with col_pago2:
            # Gráfico de distribución de métodos de pago
            if metodos_activos:
                df_metodos = pd.DataFrame(list(metodos_activos.items()), columns=['Método', 'Monto'])
                
                fig_metodos = px.pie(
                    df_metodos,
                    values='Monto',
                    names='Método',
                    title='Distribución por Método de Pago',
                    color_discrete_map={
                        'Efectivo': '#27ae60',
                        'Tarjeta': '#3498db',
                        'Transferencia': '#e67e22',
                        'Crédito': '#e74c3c'
                    }
                )
                fig_metodos.update_traces(textposition='inside', textinfo='percent+label')
                fig_metodos.update_layout(height=400)
                st.plotly_chart(fig_metodos, use_container_width=True)

    # Tendencias de ventas por fecha
    st.divider()
    st.subheader("📈 Tendencia de Ventas")
    
    if not ventas_df.empty and len(ventas_df) > 1:
        try:
            # Convertir fecha y agrupar por día
            ventas_df['fecha_solo'] = pd.to_datetime(ventas_df['fecha']).dt.date
            ventas_por_dia = ventas_df.groupby('fecha_solo').agg({
                'total': 'sum',
                'id': 'count'  # Contar número de ventas
            }).reset_index()
            ventas_por_dia.columns = ['fecha', 'total_ventas', 'num_transacciones']
            
            # Ordenar por fecha y tomar los últimos 30 días
            ventas_por_dia = ventas_por_dia.sort_values('fecha').tail(30)
            
            if len(ventas_por_dia) > 1:
                col_tend1, col_tend2 = st.columns(2)
                
                with col_tend1:
                    # Gráfico de ingresos por día
                    fig_tendencia = px.line(
                        ventas_por_dia,
                        x='fecha',
                        y='total_ventas',
                        title='Evolución de Ingresos Diarios (Últimos 30 días)',
                        markers=True,
                        labels={'total_ventas': 'Ingresos ($)', 'fecha': 'Fecha'}
                    )
                    fig_tendencia.update_layout(height=400)
                    st.plotly_chart(fig_tendencia, use_container_width=True)
                
                with col_tend2:
                    # Gráfico de número de transacciones por día
                    fig_transacciones = px.bar(
                        ventas_por_dia.tail(15),  # Últimos 15 días para mejor visualización
                        x='fecha',
                        y='num_transacciones',
                        title='Número de Transacciones por Día (Últimos 15 días)',
                        labels={'num_transacciones': 'Número de Ventas', 'fecha': 'Fecha'},
                        color='num_transacciones',
                        color_continuous_scale='blues'
                    )
                    fig_transacciones.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_transacciones, use_container_width=True)
                
                # Estadísticas de tendencia
                col_est1, col_est2, col_est3 = st.columns(3)
                
                with col_est1:
                    promedio_diario = ventas_por_dia['total_ventas'].mean()
                    st.metric("📊 Promedio Diario", f"${promedio_diario:.2f}")
                
                with col_est2:
                    mejor_dia = ventas_por_dia.loc[ventas_por_dia['total_ventas'].idxmax()]
                    st.metric("🏆 Mejor Día", f"${mejor_dia['total_ventas']:.2f}")
                    st.caption(f"📅 {mejor_dia['fecha']}")
                
                with col_est3:
                    promedio_transacciones = ventas_por_dia['num_transacciones'].mean()
                    st.metric("🛒 Prom. Transacciones/día", f"{promedio_transacciones:.1f}")
            
        except Exception as e:
            st.error(f"Error al procesar tendencias: {str(e)}")
            st.info("Intenta con más datos de ventas para ver las tendencias")

    # Resumen de inventario (si hay datos de productos)
    if not productos_df.empty:
        st.divider()
        st.subheader("📦 Resumen de Inventario")
        
        col_inv1, col_inv2, col_inv3, col_inv4 = st.columns(4)
        
        with col_inv1:
            total_productos = len(productos_df)
            st.metric("📋 Total Productos", total_productos)
        
        with col_inv2:
            try:
                # Asegurar que todos los campos numéricos sean del tipo correcto
                productos_df['precio_normal'] = pd.to_numeric(productos_df['precio_normal'], errors='coerce').fillna(0)
                productos_df['stock'] = pd.to_numeric(productos_df['stock'], errors='coerce').fillna(0)
                productos_df['stock_kg'] = pd.to_numeric(productos_df['stock_kg'], errors='coerce').fillna(0)
                
                # Calcular valor considerando productos por unidad y por granel
                productos_df['valor_actual'] = productos_df.apply(
                    lambda row: (float(row['stock_kg']) * float(row['precio_normal'])) if row['tipo_venta'] in ['granel', 'kg'] 
                               else (float(row['stock']) * float(row['precio_normal'])),
                    axis=1
                )
                valor_inventario = productos_df['valor_actual'].sum()
                st.metric("💰 Valor Inventario", f"${valor_inventario:,.2f}", 
                         help="Valor total del stock actual (cantidad × precio de venta)")
            except:
                st.metric("💰 Valor Inventario", "N/A")
        
        with col_inv3:
            try:
                # Asegurar conversión de tipos para stock_minimo
                productos_df['stock_minimo'] = pd.to_numeric(productos_df['stock_minimo'], errors='coerce').fillna(0)
                productos_df['stock_minimo_kg'] = pd.to_numeric(productos_df['stock_minimo_kg'], errors='coerce').fillna(0)
                
                # Contar productos con stock bajo según su tipo de venta
                productos_bajo_stock = len(productos_df[
                    ((productos_df['tipo_venta'] == 'unidad') & (productos_df['stock'] <= productos_df['stock_minimo']) & (productos_df['stock_minimo'] > 0)) |
                    ((productos_df['tipo_venta'].isin(['granel', 'kg'])) & (productos_df['stock_kg'] <= productos_df['stock_minimo_kg']) & (productos_df['stock_minimo_kg'] > 0))
                ])
                st.metric("⚠️ Stock Bajo", productos_bajo_stock, 
                         help="Productos con stock actual menor o igual al stock mínimo configurado")
            except:
                st.metric("⚠️ Stock Bajo", "N/A")
        
        with col_inv4:
            try:
                # Calcular ganancia potencial si se vende todo el inventario actual
                # Ganancia = (precio_normal - precio_compra) × cantidad_actual
                productos_df['precio_compra'] = pd.to_numeric(productos_df['precio_compra'], errors='coerce').fillna(0)
                productos_df['precio_normal'] = pd.to_numeric(productos_df['precio_normal'], errors='coerce').fillna(0)
                productos_df['stock'] = pd.to_numeric(productos_df['stock'], errors='coerce').fillna(0)
                productos_df['stock_kg'] = pd.to_numeric(productos_df['stock_kg'], errors='coerce').fillna(0)
                
                productos_df['ganancia_unitaria'] = productos_df['precio_normal'] - productos_df['precio_compra']
                productos_df['ganancia_total'] = productos_df.apply(
                    lambda row: (float(row['stock_kg']) * float(row['ganancia_unitaria'])) if row['tipo_venta'] in ['granel', 'kg'] 
                               else (float(row['stock']) * float(row['ganancia_unitaria'])),
                    axis=1
                )
                ganancia_inventario = productos_df['ganancia_total'].sum()
                st.metric("💵 Ganancia Potencial", f"${ganancia_inventario:,.2f}", 
                         help="Ganancia total si se vende todo el inventario actual")
            except:
                st.metric("💵 Ganancia Potencial", "N/A")

def mostrar_ventas_por_dia():
    st.subheader("🗓️ Ventas por Día")
    
    # Selector de fecha
    col_fecha1, col_fecha2 = st.columns(2)
    
    with col_fecha1:
        fecha_desde = st.date_input(
            "Desde:", 
            value=date.today().replace(day=1),  # Primer día del mes actual
            key="fecha_desde"
        )
    
    with col_fecha2:
        fecha_hasta = st.date_input(
            "Hasta:", 
            value=date.today(),
            key="fecha_hasta"
        )
    
    # Consultar ventas por día
    query = """
        SELECT 
            DATE(fecha) as dia,
            COUNT(DISTINCT fecha) as num_ventas,
            SUM(total) as total_dia,
            SUM(monto_efectivo) as efectivo,
            SUM(monto_tarjeta) as tarjeta,
            SUM(monto_transferencia) as transferencia,
            SUM(monto_credito) as credito
        FROM ventas 
        WHERE DATE(fecha) BETWEEN ? AND ?
        GROUP BY DATE(fecha)
        ORDER BY DATE(fecha) DESC
    """
    
    conn = sqlite3.connect(DB_PATH)
    try:
        ventas_dia_df = pd.read_sql_query(
            query, 
            conn, 
            params=[fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d')]
        )
    except Exception as e:
        st.error(f"Error al consultar ventas: {str(e)}")
        return
    finally:
        conn.close()
    
    if ventas_dia_df.empty:
        st.info("No hay ventas en el rango de fechas seleccionado.")
        return
    
    # Mostrar resumen del período
    col_resumen1, col_resumen2, col_resumen3, col_resumen4 = st.columns(4)
    
    with col_resumen1:
        st.metric("📅 Días con ventas", len(ventas_dia_df))
    
    with col_resumen2:
        st.metric("🛒 Total ventas", ventas_dia_df['num_ventas'].sum())
    
    with col_resumen3:
        st.metric("💰 Total período", f"${ventas_dia_df['total_dia'].sum():.2f}")
    
    with col_resumen4:
        promedio_dia = ventas_dia_df['total_dia'].mean()
        st.metric("📊 Promedio/día", f"${promedio_dia:.2f}")
    
    # Gráfico de ventas por día
    if len(ventas_dia_df) > 1:
        fig_ventas_dia = px.line(
            ventas_dia_df, 
            x='dia', 
            y='total_dia',
            title='Evolución de Ventas por Día',
            markers=True,
            labels={'total_dia': 'Total ($)', 'dia': 'Fecha'}
        )
    else:
        # Con un solo punto mostramos una barra para evitar línea degenerada
        fig_ventas_dia = px.bar(
            ventas_dia_df,
            x='dia',
            y='total_dia',
            title='Ventas del Día',
            labels={'total_dia': 'Total ($)', 'dia': 'Fecha'},
            color='total_dia',
            color_continuous_scale='Blues'
        )
        fig_ventas_dia.update_layout(showlegend=False)

    fig_ventas_dia.update_layout(height=400)
    st.plotly_chart(fig_ventas_dia, use_container_width=True)
    
    # Tabla detallada por día
    st.subheader("📋 Detalle por Día")
    
    # Formatear la tabla para mejor presentación
    ventas_dia_display = ventas_dia_df.copy()
    ventas_dia_display['dia'] = pd.to_datetime(ventas_dia_display['dia']).dt.strftime('%d/%m/%Y')
    ventas_dia_display['total_dia'] = ventas_dia_display['total_dia'].apply(lambda x: f"${x:.2f}")
    ventas_dia_display['efectivo'] = ventas_dia_display['efectivo'].apply(lambda x: f"${x:.2f}")
    ventas_dia_display['tarjeta'] = ventas_dia_display['tarjeta'].apply(lambda x: f"${x:.2f}")
    ventas_dia_display['transferencia'] = ventas_dia_display['transferencia'].apply(lambda x: f"${x:.2f}")
    ventas_dia_display['credito'] = ventas_dia_display['credito'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(
        ventas_dia_display,
        column_config={
            "dia": "📅 Fecha",
            "num_ventas": "🛒 # Ventas",
            "total_dia": "💰 Total",
            "efectivo": "💵 Efectivo",
            "tarjeta": "💳 Tarjeta",
            "transferencia": "📱 Transferencia",
            "credito": "📋 Crédito"
        },
        hide_index=True,
        width='stretch'
    )

def mostrar_listado_ventas():
    st.subheader("📋 Listado Detallado de Ventas")
    
    # Filtros
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        fecha_venta = st.date_input("📅 Seleccionar día:", value=date.today())
    
    with col_filtro2:
        # Obtener tipos de pago únicos
        conn = sqlite3.connect(DB_PATH)
        try:
            tipos_pago_query = "SELECT DISTINCT tipos_pago FROM ventas WHERE tipos_pago IS NOT NULL AND tipos_pago != ''"
            tipos_pago_df = pd.read_sql_query(tipos_pago_query, conn)
            tipos_pago_lista = ["Todos"] + tipos_pago_df['tipos_pago'].tolist()
        except:
            tipos_pago_lista = ["Todos"]
        finally:
            conn.close()
        
        filtro_pago = st.selectbox("💳 Filtrar por tipo de pago:", tipos_pago_lista)
    
    with col_filtro3:
        # Obtener tipos de cliente únicos
        conn = sqlite3.connect(DB_PATH)
        try:
            tipos_cliente_query = "SELECT DISTINCT tipo_cliente FROM ventas WHERE tipo_cliente IS NOT NULL"
            tipos_cliente_df = pd.read_sql_query(tipos_cliente_query, conn)
            tipos_cliente_lista = ["Todos"] + tipos_cliente_df['tipo_cliente'].tolist()
        except:
            tipos_cliente_lista = ["Todos", "Normal", "Mayoreo"]
        finally:
            conn.close()
        
        filtro_cliente = st.selectbox("👤 Filtrar por tipo de cliente:", tipos_cliente_lista)
    
    # Construir query con filtros
    query = """
        SELECT 
            id,
            fecha,
            codigo,
            nombre,
            cantidad,
            precio_unitario,
            total,
            tipo_cliente,
            tipos_pago,
            monto_efectivo,
            monto_tarjeta,
            monto_transferencia,
            monto_credito,
            cliente_credito
        FROM ventas 
        WHERE DATE(fecha) = ?
    """
    params = [fecha_venta.strftime('%Y-%m-%d')]
    
    if filtro_pago != "Todos":
        query += " AND tipos_pago = ?"
        params.append(filtro_pago)
    
    if filtro_cliente != "Todos":
        query += " AND tipo_cliente = ?"
        params.append(filtro_cliente)
    
    query += " ORDER BY fecha DESC"
    
    conn = sqlite3.connect(DB_PATH)
    try:
        ventas_detalle_df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"Error al consultar ventas: {str(e)}")
        return
    finally:
        conn.close()
    
    if ventas_detalle_df.empty:
        st.info("No hay ventas para los filtros seleccionados.")
        return
    
    # **PAGINACIÓN**
    # total_ventas (rows) mantiene la paginación por filas, pero mostrar_ventas mostrará
    # un contador de ventas por ticket (tickets) usando la columna 'fecha' como agrupador.
    total_ventas = len(ventas_detalle_df)
    try:
        ticket_count = ventas_detalle_df['fecha'].nunique()
    except Exception:
        ticket_count = total_ventas
    ventas_por_pagina = 20
    total_paginas = (total_ventas - 1) // ventas_por_pagina + 1
    
    # Mostrar resumen del día seleccionado
    col_resumen1, col_resumen2, col_resumen3, col_resumen4 = st.columns(4)
    
    with col_resumen1:
        # Mostrar la cantidad de ventas como número de tickets (no filas/items)
        st.metric("🛒 Ventas del día", ticket_count)
    
    with col_resumen2:
        st.metric("💰 Total del día", f"${ventas_detalle_df['total'].sum():.2f}")
    
    with col_resumen3:
        productos_unicos = ventas_detalle_df['codigo'].nunique()
        st.metric("📦 Productos diferentes", productos_unicos)
    
    with col_resumen4:
        st.metric("📄 Total páginas", total_paginas)
    
    # **SELECTOR DE PÁGINA**
    if total_paginas > 1:
        st.divider()
        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
        
        with col_pag2:
            pagina_actual = st.selectbox(
                f"📄 Página (mostrando {ventas_por_pagina} ventas por página):",
                range(1, total_paginas + 1),
                key="pagina_selector"
            )
        
        # Calcular índices para la página actual
        inicio = (pagina_actual - 1) * ventas_por_pagina
        fin = min(inicio + ventas_por_pagina, total_ventas)
        
        # Filtrar ventas para la página actual
        ventas_pagina_df = ventas_detalle_df.iloc[inicio:fin]
        st.info(f"📊 Mostrando filas {inicio + 1} - {fin} de {total_ventas} — {ticket_count} tickets")
    else:
        ventas_pagina_df = ventas_detalle_df
        pagina_actual = 1
        st.info(f"📊 Mostrando {ticket_count} ventas (tickets) — {total_ventas} filas en esta página")
    
    st.divider()
    
    # **SECCIÓN PARA MODIFICAR MÉTODOS DE PAGO**
    st.subheader("✏️ Modificar Método de Pago")
    st.write("💡 **Tip:** Los montos deben sumar exactamente el total de la venta para poder actualizar.")
    
    # Mostrar tabla editable para las ventas de la página actual (agrupadas por ticket/fecha)
    grouped = list(ventas_pagina_df.groupby('fecha', sort=False))
    for idx, (fecha_ticket, group) in enumerate(grouped):
        # Usar el menor id del grupo como identificador estable para keys/UI
        min_id = int(group['id'].min()) if 'id' in group.columns else idx + 1
    # Resumen del ticket
        nombres = group['nombre'].tolist()
        if len(nombres) == 1:
            display_name = nombres[0]
        else:
            display_name = f"{nombres[0]} (+{len(nombres)-1} más)"

        total_ticket = float(group['total'].sum())
        tipos_pago = group.iloc[0].get('tipos_pago', 'N/A') if not group.empty else 'N/A'

        # Widget keys and pending-action keys (to avoid modifying widget-backed session_state after widget instantiation)
        ef_key = f"efectivo_{min_id}_{pagina_actual}"
        tar_key = f"tarjeta_{min_id}_{pagina_actual}"
        trans_key = f"transferencia_{min_id}_{pagina_actual}"
        cred_key = f"credito_{min_id}_{pagina_actual}"

        pending_auto = f"pending_auto_{min_id}_{pagina_actual}"
        pending_reset = f"pending_reset_{min_id}_{pagina_actual}"
        pending_restore = f"pending_restore_{min_id}_{pagina_actual}"

        # If there are pending actions from a previous click, materialize them into the widget keys
        if pending_auto in st.session_state:
            # pending_auto holds a numeric value for efectivo
            st.session_state[ef_key] = st.session_state.pop(pending_auto)

        if pending_reset in st.session_state:
            vals = st.session_state.pop(pending_reset)
            # vals is a tuple (ef, tar, trans, cred)
            st.session_state[ef_key] = vals[0]
            st.session_state[tar_key] = vals[1]
            st.session_state[trans_key] = vals[2]
            st.session_state[cred_key] = vals[3]

        if pending_restore in st.session_state:
            # Recompute initial values from the group and restore
            st.session_state.pop(pending_restore)
            st.session_state[ef_key] = round(float(group['monto_efectivo'].fillna(0).sum()), 2)
            st.session_state[tar_key] = round(float(group['monto_tarjeta'].fillna(0).sum()), 2)
            st.session_state[trans_key] = round(float(group['monto_transferencia'].fillna(0).sum()), 2)
            st.session_state[cred_key] = round(float(group['monto_credito'].fillna(0).sum()), 2)

        # Clamp any existing session_state values for these keys to the ticket total to avoid ValueAboveMaxError
        # (Do this before creating number_input widgets)
        try:
            total_ticket_clamp = round(float(group['total'].sum()), 2)
        except Exception:
            total_ticket_clamp = 0.0

        for k in (ef_key, tar_key, trans_key, cred_key):
            if k in st.session_state:
                try:
                    val = float(st.session_state.get(k, 0.0))
                except Exception:
                    val = 0.0
                # clamp to [0, total_ticket_clamp]
                if val > total_ticket_clamp:
                    st.session_state[k] = round(total_ticket_clamp, 2)
                elif val < 0:
                    st.session_state[k] = 0.0

        with st.expander(f"🛒 Venta #{min_id} - {display_name} - ${total_ticket:.2f} ({tipos_pago})"):
            col_info, col_edit = st.columns([2, 1])

            with col_info:
                st.write(f"**📅 Fecha:** {pd.to_datetime(fecha_ticket).strftime('%d/%m/%Y %H:%M')}")
                # Detallar los ítems del ticket
                for _, row in group.iterrows():
                    st.write(f"**📦 Producto:** {row['codigo']} - {row['nombre']}")
                    st.write(f"**📊 Cantidad:** {row['cantidad']} × ${row['precio_unitario']:.2f} = ${row['total']:.2f}")
                st.write(f"**👤 Cliente:** {group.iloc[0].get('tipo_cliente', 'N/A')}")

                if group.iloc[0].get('cliente_credito') and str(group.iloc[0]['cliente_credito']).strip():
                    st.write(f"**📋 Cliente Crédito:** {group.iloc[0]['cliente_credito']}")

                # Mostrar distribución actual de pagos (sumada por ticket)
                st.write("**💳 Distribución actual:**")
                distribuciones = []
                efectivo_sum = float(group['monto_efectivo'].fillna(0).sum())
                tarjeta_sum = float(group['monto_tarjeta'].fillna(0).sum())
                transferencia_sum = float(group['monto_transferencia'].fillna(0).sum())
                credito_sum = float(group['monto_credito'].fillna(0).sum())

                if efectivo_sum > 0:
                    distribuciones.append(f"  • Efectivo: ${efectivo_sum:.2f}")
                if tarjeta_sum > 0:
                    distribuciones.append(f"  • Tarjeta: ${tarjeta_sum:.2f}")
                if transferencia_sum > 0:
                    distribuciones.append(f"  • Transferencia: ${transferencia_sum:.2f}")
                if credito_sum > 0:
                    distribuciones.append(f"  • Crédito: ${credito_sum:.2f}")

                if distribuciones:
                    for dist in distribuciones:
                        st.write(dist)
                else:
                    st.write("  • No hay distribución registrada")

            with col_edit:
                st.write("**🔧 Nuevo Método de Pago:**")
                st.write(f"**Total a distribuir: ${total_ticket:.2f}**")

                # Inicializar valores por defecto con validación de límites (usando sumas del ticket)
                total_venta = round(total_ticket, 2)

                # Clamp individual sums so they don't exceed the widget max (total_venta)
                monto_efectivo_inicial = min(round(efectivo_sum, 2), total_venta)
                monto_tarjeta_inicial = min(round(tarjeta_sum, 2), total_venta)
                monto_transferencia_inicial = min(round(transferencia_sum, 2), total_venta)
                monto_credito_inicial = min(round(credito_sum, 2), total_venta)

                # If the combined initial sums are inconsistent, default to 100% efectivo
                suma_inicial = monto_efectivo_inicial + monto_tarjeta_inicial + monto_transferencia_inicial + monto_credito_inicial
                if abs(suma_inicial - total_venta) > 0.01:
                    # prefer to default to all efectivo to avoid values > max
                    monto_efectivo_inicial = total_venta
                    monto_tarjeta_inicial = 0.0
                    monto_transferencia_inicial = 0.0
                    monto_credito_inicial = 0.0

                # Ensure session_state has sensible defaults BEFORE creating widgets
                st.session_state.setdefault(ef_key, round(monto_efectivo_inicial, 2))
                st.session_state.setdefault(tar_key, round(monto_tarjeta_inicial, 2))
                st.session_state.setdefault(trans_key, round(monto_transferencia_inicial, 2))
                st.session_state.setdefault(cred_key, round(monto_credito_inicial, 2))

                # Inputs para nuevos montos con validación mejorada
                col_input1, col_input2 = st.columns(2)
                
                with col_input1:
                    nuevo_efectivo = st.number_input(
                        "💵 Efectivo:", 
                        min_value=0.0, 
                        max_value=total_venta,
                        step=0.01, 
                        key=ef_key,
                        help=f"Máximo: ${total_venta:.2f}"
                    )
                    
                    nuevo_transferencia = st.number_input(
                        "📱 Transferencia:", 
                        min_value=0.0, 
                        max_value=total_venta,
                        step=0.01, 
                        key=trans_key,
                        help=f"Máximo: ${total_venta:.2f}"
                    )
                
                with col_input2:
                    nuevo_tarjeta = st.number_input(
                        "💳 Tarjeta:", 
                        min_value=0.0, 
                        max_value=total_venta,
                        step=0.01, 
                        key=tar_key,
                        help=f"Máximo: ${total_venta:.2f}"
                    )
                    
                    nuevo_credito = st.number_input(
                        "📋 Crédito:", 
                        min_value=0.0, 
                        max_value=total_venta,
                        step=0.01, 
                        key=cred_key,
                        help=f"Máximo: ${total_venta:.2f}"
                    )
                
                # Validar que la suma coincida con el total
                suma_nueva = nuevo_efectivo + nuevo_tarjeta + nuevo_transferencia + nuevo_credito
                diferencia = abs(suma_nueva - total_venta)
                
                # Mostrar estado de la validación con colores mejorados
                col_val1, col_val2 = st.columns(2)
                
                with col_val1:
                    st.write(f"**💰 Total venta:** ${total_venta:.2f}")
                    st.write(f"**🧮 Suma actual:** ${suma_nueva:.2f}")
                
                with col_val2:
                    if diferencia > 0.01:
                        st.error(f"⚠️ **Diferencia:** ${diferencia:.2f}")
                        st.error("❌ **Los montos deben sumar exactamente el total**")
                    else:
                        st.success("✅ **Suma correcta**")
                
                # Botón de auto-ajuste si hay diferencia
                if diferencia > 0.01:
                    col_auto1, col_auto2 = st.columns(2)
                    
                    with col_auto1:
                        if st.button(
                            "🔧 Auto-ajustar al Efectivo", 
                            key=f"auto_efectivo_{min_id}_{pagina_actual}",
                            help="Asignar toda la diferencia al efectivo"
                        ):
                            diferencia_restante = total_venta - (nuevo_tarjeta + nuevo_transferencia + nuevo_credito)
                            if diferencia_restante >= 0:
                                # Set a pending flag (not the widget key) and rerun; the pending flag will be applied
                                st.session_state[f"pending_auto_{min_id}_{pagina_actual}"] = round(diferencia_restante, 2)
                                st.info(f"💡 Ajustando efectivo a ${diferencia_restante:.2f}")
                                st.rerun()
                    
                    with col_auto2:
                        if st.button(
                            "🔄 Resetear a 100% Efectivo", 
                            key=f"reset_efectivo_{min_id}_{pagina_actual}",
                            help="Poner todo el monto en efectivo"
                        ):
                            # Set a pending reset tuple and rerun; the pending will be applied before widgets are created
                            st.session_state[f"pending_reset_{min_id}_{pagina_actual}"] = (
                                round(total_venta, 2), 0.0, 0.0, 0.0
                            )
                            st.info("💡 Configurando 100% efectivo")
                            st.rerun()
                
                # Botones de acción principales
                st.divider()
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    # Botón para actualizar
                    button_disabled = diferencia > 0.01
                    button_type = "primary" if not button_disabled else "secondary"
                    button_text = "💾 Actualizar" if not button_disabled else "❌ Corrige la suma"

                    if st.button(
                        button_text,
                        key=f"update_{min_id}_{pagina_actual}",
                        disabled=button_disabled,
                        type=button_type,
                    ):
                        # Construir nuevo string de tipos de pago
                        nuevos_tipos = []
                        if nuevo_efectivo > 0:
                            nuevos_tipos.append("Efectivo")
                        if nuevo_tarjeta > 0:
                            nuevos_tipos.append("Tarjeta")
                        if nuevo_transferencia > 0:
                            nuevos_tipos.append("Transferencia")
                        if nuevo_credito > 0:
                            nuevos_tipos.append("Crédito")

                        nuevo_tipos_pago = ", ".join(nuevos_tipos) if nuevos_tipos else "Sin especificar"

                        # Actualizar en la base de datos (por fecha/ticket)
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()

                        try:
                            cursor.execute("""
                                UPDATE ventas 
                                SET monto_efectivo = ?, 
                                    monto_tarjeta = ?, 
                                    monto_transferencia = ?, 
                                    monto_credito = ?,
                                    tipos_pago = ?
                                WHERE fecha = ?
                            """, (nuevo_efectivo, nuevo_tarjeta, nuevo_transferencia, nuevo_credito, nuevo_tipos_pago, fecha_ticket))

                            conn.commit()

                            # Mostrar mensaje de éxito con detalles
                            st.success(f"✅ Venta (ticket) #{min_id} actualizada correctamente")

                            with st.container():
                                st.info("**🔄 Cambios aplicados:**")
                                col_cambio1, col_cambio2 = st.columns(2)

                                with col_cambio1:
                                    if nuevo_efectivo > 0:
                                        st.write(f"💵 Efectivo: ${nuevo_efectivo:.2f}")
                                    if nuevo_tarjeta > 0:
                                        st.write(f"💳 Tarjeta: ${nuevo_tarjeta:.2f}")

                                with col_cambio2:
                                    if nuevo_transferencia > 0:
                                        st.write(f"📱 Transferencia: ${nuevo_transferencia:.2f}")
                                    if nuevo_credito > 0:
                                        st.write(f"📋 Crédito: ${nuevo_credito:.2f}")

                                st.write(f"**💳 Tipo de pago actualizado:** {nuevo_tipos_pago}")

                            # Esperar 2 segundos y recargar
                            import time
                            time.sleep(2)
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Error al actualizar: {str(e)}")
                            st.error("🔍 **Detalles del error:** Verifique que los datos sean válidos")
                            conn.rollback()
                        finally:
                            conn.close()
                
                with col_btn2:
                    # Botón para resetear a valores originales
                    if st.button(
                        f"🔄 Restaurar Valores", 
                        key=f"reset_{min_id}_{pagina_actual}",
                        help="Restaurar a los valores guardados en la base de datos"
                    ):
                        # Set a pending restore flag and rerun; on next run we'll recompute and restore
                        st.session_state[f"pending_restore_{min_id}_{pagina_actual}"] = True
                        st.info("🔄 Restaurando valores originales...")
                        import time
                        time.sleep(0.2)
                        st.rerun()
    
    # **TABLA RESUMEN DE LA PÁGINA ACTUAL**
    st.divider()
    st.subheader("📊 Resumen de Ventas (Página Actual)")
    
    # Preparar datos para mostrar
    ventas_display = ventas_pagina_df.copy()
    ventas_display['fecha'] = pd.to_datetime(ventas_display['fecha']).dt.strftime('%H:%M')
    ventas_display = ventas_display[['id', 'fecha', 'codigo', 'nombre', 'cantidad', 'total', 'tipos_pago', 'tipo_cliente']]
    
    st.dataframe(
        ventas_display,
        column_config={
            "id": "🆔 ID",
            "fecha": "🕐 Hora",
            "codigo": "📦 Código",
            "nombre": "📋 Producto",
            "cantidad": "📊 Cant.",
            "total": st.column_config.NumberColumn("💰 Total", format="$%.2f"),
            "tipos_pago": "💳 Pago",
            "tipo_cliente": "👤 Cliente"
        },
        hide_index=True,
        width='stretch'
    )
    
    # **RESUMEN TOTAL DEL DÍA (todas las páginas)**
    if total_paginas > 1:
        st.divider()
        st.subheader("📈 Resumen Total del Día")
        
        # Calcular totales por método de pago del día completo
        total_efectivo = ventas_detalle_df['monto_efectivo'].fillna(0).sum()
        total_tarjeta = ventas_detalle_df['monto_tarjeta'].fillna(0).sum()
        total_transferencia = ventas_detalle_df['monto_transferencia'].fillna(0).sum()
        total_credito = ventas_detalle_df['monto_credito'].fillna(0).sum()
        
        col_total1, col_total2, col_total3, col_total4 = st.columns(4)
        
        with col_total1:
            st.metric("💵 Total Efectivo", f"${total_efectivo:.2f}")
        
        with col_total2:
            st.metric("💳 Total Tarjeta", f"${total_tarjeta:.2f}")
        
        with col_total3:
            st.metric("📱 Total Transferencia", f"${total_transferencia:.2f}")
        
        with col_total4:
            st.metric("📋 Total Crédito", f"${total_credito:.2f}")

def mostrar_exportar_reportes():
    st.subheader("💾 Exportar Reportes")
    
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        st.write("**📊 Exportar Ventas Completas**")
        conn = sqlite3.connect(DB_PATH)
        try:
            ventas_df = pd.read_sql_query("SELECT * FROM ventas ORDER BY fecha DESC", conn)
            if not ventas_df.empty:
                csv_completo = ventas_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Descargar Todas las Ventas (CSV)", 
                    data=csv_completo, 
                    file_name=f"ventas_completas_{datetime.now().strftime('%Y%m%d')}.csv", 
                    mime='text/csv'
                )
            else:
                st.info("No hay datos para exportar")
        except Exception as e:
            st.error(f"Error al exportar: {str(e)}")
        finally:
            conn.close()
    
    with col_export2:
        st.write("**📅 Exportar Ventas por Fecha**")
        fecha_export = st.date_input("Seleccionar fecha:", value=date.today())
        
        conn = sqlite3.connect(DB_PATH)
        try:
            ventas_fecha_df = pd.read_sql_query(
                "SELECT * FROM ventas WHERE DATE(fecha) = ? ORDER BY fecha DESC", 
                conn, 
                params=[fecha_export.strftime('%Y-%m-%d')]
            )
            
            if not ventas_fecha_df.empty:
                csv_fecha = ventas_fecha_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    f"📥 Descargar Ventas del {fecha_export.strftime('%d/%m/%Y')} (CSV)", 
                    data=csv_fecha, 
                    file_name=f"ventas_{fecha_export.strftime('%Y%m%d')}.csv", 
                    mime='text/csv'
                )
            else:
                st.info(f"No hay ventas para el {fecha_export.strftime('%d/%m/%Y')}")
        except Exception as e:
            st.error(f"Error al exportar por fecha: {str(e)}")
        finally:
            conn.close()
    
    # Exportar por rango de fechas
    st.divider()
    st.subheader("📅 Exportar por Rango de Fechas")
    
    col_rango1, col_rango2, col_rango3 = st.columns(3)
    
    with col_rango1:
        fecha_desde_export = st.date_input(
            "Desde:", 
            value=date.today().replace(day=1),
            key="export_desde"
        )
    
    with col_rango2:
        fecha_hasta_export = st.date_input(
            "Hasta:", 
            value=date.today(),
            key="export_hasta"
        )
    
    with col_rango3:
        if st.button("📊 Generar Reporte de Rango"):
            conn = sqlite3.connect(DB_PATH)
            try:
                ventas_rango_df = pd.read_sql_query(
                    "SELECT * FROM ventas WHERE DATE(fecha) BETWEEN ? AND ? ORDER BY fecha DESC", 
                    conn, 
                    params=[fecha_desde_export.strftime('%Y-%m-%d'), fecha_hasta_export.strftime('%Y-%m-%d')]
                )
                
                if not ventas_rango_df.empty:
                    csv_rango = ventas_rango_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        f"📥 Descargar Rango {fecha_desde_export.strftime('%d/%m/%Y')} - {fecha_hasta_export.strftime('%d/%m/%Y')}", 
                        data=csv_rango, 
                        file_name=f"ventas_rango_{fecha_desde_export.strftime('%Y%m%d')}_{fecha_hasta_export.strftime('%Y%m%d')}.csv", 
                        mime='text/csv'
                    )
                else:
                    st.info("No hay ventas en el rango seleccionado")
            except Exception as e:
                st.error(f"Error al generar reporte de rango: {str(e)}")
            finally:
                conn.close()
    
    # Estadísticas adicionales
    st.divider()
    st.subheader("📈 Estadísticas Rápidas")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        # Total de ventas registradas (contar tickets únicos por fecha)
        result_total = conn.execute("SELECT COUNT(DISTINCT fecha) FROM ventas").fetchone()
        total_ventas_registradas = result_total[0] if result_total else 0
        
        # Ventas del día actual (tickets únicos)
        result_hoy = conn.execute(
            f"SELECT COUNT(DISTINCT fecha) FROM ventas WHERE DATE(fecha) = '{date.today().strftime('%Y-%m-%d')}'"
        ).fetchone()
        ventas_hoy = result_hoy[0] if result_hoy else 0
        
        # Total facturado
        result_facturado = conn.execute("SELECT SUM(total) FROM ventas").fetchone()
        total_facturado = result_facturado[0] if result_facturado and result_facturado[0] else 0
        
        # Producto más vendido
        result_top_producto = conn.execute("""
            SELECT nombre, SUM(cantidad) as total_cantidad 
            FROM ventas 
            GROUP BY nombre 
            ORDER BY total_cantidad DESC 
            LIMIT 1
        """).fetchone()
        
        # Mostrar métricas
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("🛒 Total Ventas", total_ventas_registradas)
        
        with col_stat2:
            st.metric("📅 Ventas Hoy", ventas_hoy)
        
        with col_stat3:
            st.metric("💰 Total Facturado", f"${total_facturado:.2f}")
        
        with col_stat4:
            if result_top_producto:
                producto_nombre = result_top_producto[0]
                if len(producto_nombre) > 15:
                    producto_display = producto_nombre[:15] + "..."
                else:
                    producto_display = producto_nombre
                st.metric("🏆 Top Producto", producto_display)
            else:
                st.metric("🏆 Top Producto", "N/A")
    
    except Exception as e:
        st.error(f"Error al generar estadísticas: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()