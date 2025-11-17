import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time

conn = sqlite3.connect("pos_cremeria.db", check_same_thread=False)
cursor = conn.cursor()

# CSS personalizado para mejorar la apariencia
def aplicar_estilos_custom():
    st.markdown("""
    <style>
    /* Estilos generales */
    .main {
        padding-top: 1.5rem;
    }
    
    /* Título principal más compacto */
    .titulo-principal {
        font-size: 2.8rem !important;
        font-weight: bold !important;
        text-align: center !important;
        color: #2E8B57 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 1.5rem !important;
        padding: 1.2rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        border: 3px solid #2E8B57;
    }
    
    /* Métricas más grandes */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white !important;
        text-align: center;
        box-shadow: 0 6px 24px rgba(0,0,0,0.1);
        margin: 0.4rem 0;
    }
    
    .metric-value {
        font-size: 2.2rem !important;
        font-weight: bold !important;
        color: #FFD700 !important;
    }
    
    .metric-label {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: white !important;
    }
    
    /* Botones más grandes y atractivos para touch */
    .stButton > button {
        font-size: 1.2rem !important;
        font-weight: bold !important;
        padding: 1rem 2rem !important;
        min-height: 55px !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 3px 12px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    }
    
    /* Botón primario */
    .stButton > button[data-baseweb="button"][kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-size: 1.2rem !important;
    }
    
    /* Botón secundario */
    .stButton > button[data-baseweb="button"][kind="secondary"] {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%) !important;
        color: #333 !important;
    }
    
    /* Números de input más grandes para touch */
    .stNumberInput > div > div > input {
        font-size: 1.4rem !important;
        font-weight: bold !important;
        text-align: center !important;
        color: #2E8B57 !important;
        min-height: 55px !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #2E8B57 !important;
        box-shadow: 0 0 0 3px rgba(46,139,87,0.2) !important;
    }
    
    /* Selectbox más grande */
    .stSelectbox > div > div > div {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    
    /* Text input más grande para touch */
    .stTextInput > div > div > input {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        min-height: 55px !important;
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.2) !important;
    }
    
    /* Time input y Date input también más grandes */
    .stTimeInput > div > div > input,
    .stDateInput > div > div > input {
        font-size: 1.2rem !important;
        font-weight: bold !important;
        padding: 1rem !important;
        min-height: 55px !important;
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Alertas más prominentes */
    .alert-critica {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%) !important;
        color: white !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        text-align: center !important;
        animation: pulse 2s infinite !important;
        box-shadow: 0 6px 24px rgba(255,65,108,0.3) !important;
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.01); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Carrito de compras - color cambiado a verde */
    .carrito-item {
        background: linear-gradient(135deg, #a8d5ba 0%, #90c695 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.4rem 0;
        color: #1e3a28;
        font-size: 1.1rem;
        font-weight: 600;
        border: 1px solid #7eb693;
    }
    
    /* Totales destacados más compactos */
    .total-destacado {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        color: white;
        font-size: 1.8rem;
        font-weight: bold;
        box-shadow: 0 8px 32px rgba(79,172,254,0.3);
        margin: 0.8rem 0;
    }
    
    /* Dataframes más elegantes */
    .stDataFrame {
        font-size: 1rem !important;
    }
    
    /* Expandir más atractivo y compacto */
    .streamlit-expanderHeader {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important;
        border-radius: 8px !important;
        padding: 0.8rem !important;
    }
    
    /* Success messages más compactos */
    .stSuccess {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        padding: 0.8rem !important;
    }
    
    /* Error messages más compactos */
    .stError {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        padding: 0.8rem !important;
    }
    
    /* Info messages más compactos */
    .stInfo {
        font-size: 1rem !important;
        font-weight: 600 !important;
        padding: 0.8rem !important;
    }
    
    /* Warning messages más compactos */
    .stWarning {
        font-size: 1rem !important;
        font-weight: 600 !important;
        padding: 0.8rem !important;
    }
    
    /* Checkboxes más grandes para tablets y touch */
    .stCheckbox {
        margin: 0.8rem 0 !important;
    }
    
    .stCheckbox > label {
        font-size: 1.3rem !important;
        font-weight: bold !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        min-height: 60px !important;
        display: flex !important;
        align-items: center !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border-radius: 12px !important;
        border: 2px solid #dee2e6 !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stCheckbox > label:hover {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%) !important;
        border-color: #2196f3 !important;
        box-shadow: 0 4px 16px rgba(33,150,243,0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    .stCheckbox > label[data-checked="true"] {
        background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%) !important;
        color: white !important;
        border-color: #2e7d32 !important;
        box-shadow: 0 4px 16px rgba(76,175,80,0.3) !important;
    }
    
    .stCheckbox input[type="checkbox"] {
        width: 25px !important;
        height: 25px !important;
        margin-right: 15px !important;
        cursor: pointer !important;
        transform: scale(1.5) !important;
    }
    
    /* Radio buttons también más grandes para touch */
    .stRadio {
        margin: 0.8rem 0 !important;
    }
    
    .stRadio > label {
        font-size: 1.2rem !important;
        font-weight: bold !important;
        padding: 0.8rem !important;
        margin: 0.3rem 0 !important;
        min-height: 50px !important;
        display: flex !important;
        align-items: center !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
    }
    
    .stRadio > label:hover {
        background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 30%) !important;
        border-color: #ff9800 !important;
        box-shadow: 0 3px 12px rgba(255,152,0,0.2) !important;
    }
    
    .stRadio input[type="radio"] {
        width: 22px !important;
        height: 22px !important;
        margin-right: 12px !important;
        cursor: pointer !important;
        transform: scale(1.4) !important;
    }
    
    /* Mejorar área táctil de selectbox */
    .stSelectbox > div > div {
        min-height: 55px !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
    }
    
    .stSelectbox > div > div > div {
        padding: 1rem !important;
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Mejoras específicas para tablets y touch */
    @media (max-width: 1024px) {
        .main {
            padding: 0.5rem !important;
        }
        
        .stButton > button {
            min-height: 65px !important;
            font-size: 1.3rem !important;
            padding: 1.2rem 2.5rem !important;
        }
        
        .stCheckbox > label {
            min-height: 70px !important;
            padding: 1.2rem !important;
            font-size: 1.4rem !important;
        }
        
        .stRadio > label {
            min-height: 60px !important;
            padding: 1rem !important;
            font-size: 1.3rem !important;
        }
        
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input {
            min-height: 65px !important;
            font-size: 1.5rem !important;
            padding: 1.2rem !important;
        }
    }
    
    /* Espaciado adicional para elementos interactivos */
    .stCheckbox, .stRadio {
        margin: 1rem 0 !important;
    }
    
    /* Mejorar el contraste para pantallas touch */
    .stCheckbox > label[data-checked="true"],
    .stRadio > label[data-checked="true"] {
        background: linear-gradient(135deg, #28a745 0%, #155724 100%) !important;
        color: white !important;
        border-color: #155724 !important;
        font-weight: 900 !important;
        box-shadow: 0 6px 20px rgba(40,167,69,0.4) !important;
    }
    
    /* Hacer que los expandibles sean más fáciles de tocar */
    .streamlit-expanderHeader {
        min-height: 60px !important;
        padding: 1.2rem !important;
        font-size: 1.3rem !important;
    }
    
    html {
        scroll-behavior: smooth;
    }
    
    /* Marcar claramente el área del carrito y finalizar venta */
    #carrito-section {
        scroll-margin-top: 20px;
    }
    
    #finalizar-venta-section {
        scroll-margin-top: 20px;
    }
    
    /* Destacar el botón de finalizar cuando se hace scroll automático */
    .highlight-finalizar {
        animation: highlight-pulse 3s ease-in-out;
        box-shadow: 0 0 25px rgba(102, 126, 234, 0.8) !important;
        border: 2px solid #667eea !important;
    }
    
    @keyframes highlight-pulse {
        0%, 100% { 
            box-shadow: 0 0 25px rgba(102, 126, 234, 0.8);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 35px rgba(102, 126, 234, 1);
            transform: scale(1.02);
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Función para formatear moneda
def formatear_moneda(valor):
    """Formatear números como moneda con 2 decimales"""
    try:
        return f"${float(valor):,.2f}"
    except:
        return "$0.00"

# Función para mostrar métricas mejoradas
def mostrar_metrica_mejorada(titulo, valor, icono="💰", es_moneda=True):
    """Mostrar métrica con estilo mejorado"""
    if es_moneda:
        valor_formateado = formatear_moneda(valor)
    else:
        valor_formateado = f"{valor:,}"
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">{icono} {titulo}</div>
        <div class="metric-value">{valor_formateado}</div>
    </div>
    """, unsafe_allow_html=True)

# Crear tabla de ventas actualizada
cursor.execute('''
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    codigo TEXT,
    nombre TEXT,
    cantidad INTEGER,
    precio_unitario REAL,
    total REAL,
    tipo_cliente TEXT,
    tipos_pago TEXT,
    monto_efectivo REAL DEFAULT 0,
    monto_tarjeta REAL DEFAULT 0,
    monto_transferencia REAL DEFAULT 0,
    monto_credito REAL DEFAULT 0,
    fecha_vencimiento_credito TEXT,
    hora_vencimiento_credito TEXT DEFAULT '15:00',
    cliente_credito TEXT,
    pagado INTEGER DEFAULT 1,
    alerta_mostrada INTEGER DEFAULT 0,
    peso_vendido REAL DEFAULT 0,
    tipo_venta TEXT DEFAULT 'unidad'
)
''')

# Agregar nuevas columnas si no existen
cursor.execute("PRAGMA table_info(ventas)")
columns = [column[1] for column in cursor.fetchall()]

# Migrar columnas existentes y agregar nuevas
if 'tipos_pago' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN tipos_pago TEXT DEFAULT 'Efectivo'")
if 'monto_efectivo' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN monto_efectivo REAL DEFAULT 0")
if 'monto_tarjeta' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN monto_tarjeta REAL DEFAULT 0")
if 'monto_transferencia' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN monto_transferencia REAL DEFAULT 0")
if 'monto_credito' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN monto_credito REAL DEFAULT 0")
if 'fecha_vencimiento_credito' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN fecha_vencimiento_credito TEXT")
if 'hora_vencimiento_credito' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN hora_vencimiento_credito TEXT DEFAULT '15:00'")
if 'cliente_credito' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN cliente_credito TEXT")
if 'pagado' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN pagado INTEGER DEFAULT 1")
if 'alerta_mostrada' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN alerta_mostrada INTEGER DEFAULT 0")
if 'peso_vendido' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN peso_vendido REAL DEFAULT 0")
if 'tipo_venta' not in columns:
    cursor.execute("ALTER TABLE ventas ADD COLUMN tipo_venta TEXT DEFAULT 'unidad'")

# Crear tabla de alertas de crédito actualizada
cursor.execute('''
CREATE TABLE IF NOT EXISTS creditos_pendientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    monto REAL NOT NULL,
    fecha_venta TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    hora_vencimiento TEXT DEFAULT '15:00',
    venta_id INTEGER,
    pagado INTEGER DEFAULT 0,
    alerta_mostrada INTEGER DEFAULT 0,
    FOREIGN KEY (venta_id) REFERENCES ventas (id)
)
''')

# Agregar columna hora_vencimiento y alerta_mostrada si no existe
cursor.execute("PRAGMA table_info(creditos_pendientes)")
credito_columns = [column[1] for column in cursor.fetchall()]
if 'hora_vencimiento' not in credito_columns:
    cursor.execute("ALTER TABLE creditos_pendientes ADD COLUMN hora_vencimiento TEXT DEFAULT '15:00'")
if 'alerta_mostrada' not in credito_columns:
    cursor.execute("ALTER TABLE creditos_pendientes ADD COLUMN alerta_mostrada INTEGER DEFAULT 0")

conn.commit()

def parsear_codigo_bascula(codigo_completo):
    """
    Parsear tickets con múltiples productos.
    Formato: 13 dígitos por producto (8 código + 4 valor + 1 control)
    Retorna: [(codigo, valor), ...]
    """
    if not codigo_completo or len(codigo_completo) < 13:
        return []
    if len(codigo_completo) % 13 != 0:
        return []
    
    productos = []
    num_productos = len(codigo_completo) // 13
    
    for i in range(num_productos):
        inicio = i * 13
        codigo_prod = codigo_completo[inicio:inicio+8]
        valor_str = codigo_completo[inicio+8:inicio+12]
        try:
            valor = int(valor_str)
            productos.append((codigo_prod, valor))
        except ValueError:
            continue
    
    return productos

def obtener_producto_por_codigo(codigo):
    """Obtener información completa del producto por código"""
    cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
    return cursor.fetchone()

def obtener_precio_por_tipo(producto, tipo_cliente):
    """Obtiene el precio según el tipo de cliente para productos por unidad"""
    if tipo_cliente == "Normal":
        return float(producto[3]) if producto[3] else 0.0
    elif tipo_cliente == "Mayoreo Tipo 1":
        return float(producto[4]) if producto[4] else 0.0
    elif tipo_cliente == "Mayoreo Tipo 2":
        return float(producto[5]) if producto[5] else 0.0
    elif tipo_cliente == "Mayoreo Tipo 3":
        return float(producto[6]) if producto[6] else 0.0
    else:
        return float(producto[3]) if producto[3] else 0.0

def obtener_precio_granel_por_tipo(producto, tipo_cliente):
    """Obtiene el precio por Kg según el tipo de cliente para productos a granel"""
    cursor.execute("PRAGMA table_info(productos)")
    columnas = [col[1] for col in cursor.fetchall()]
    
    producto_dict = {}
    for i, valor in enumerate(producto):
        if i < len(columnas):
            producto_dict[columnas[i]] = valor
    
    precio_base_kg = float(producto_dict.get('precio_por_kg', 0.0)) if producto_dict.get('precio_por_kg') else 0.0
    
    if tipo_cliente == "Normal":
        return precio_base_kg
    elif tipo_cliente == "Mayoreo Tipo 1":
        return precio_base_kg * 0.95
    elif tipo_cliente == "Mayoreo Tipo 2":
        return precio_base_kg * 0.90
    elif tipo_cliente == "Mayoreo Tipo 3":
        return precio_base_kg * 0.85
    else:
        return precio_base_kg

def obtener_informacion_producto(producto):
    """Obtener información del producto usando mapeo por nombres de columnas"""
    cursor.execute("PRAGMA table_info(productos)")
    columnas = [col[1] for col in cursor.fetchall()]
    
    producto_dict = {}
    for i, valor in enumerate(producto):
        if i < len(columnas):
            producto_dict[columnas[i]] = valor
    
    return {
        'codigo': producto_dict.get('codigo', ''),
        'nombre': producto_dict.get('nombre', ''),
        'tipo_venta': producto_dict.get('tipo_venta', 'unidad'),
        'stock': int(producto_dict.get('stock', 0)) if producto_dict.get('stock') else 0,
        'stock_kg': float(producto_dict.get('stock_kg', 0.0)) if producto_dict.get('stock_kg') else 0.0,
        'peso_unitario': float(producto_dict.get('peso_unitario', 0.0)) if producto_dict.get('peso_unitario') else 0.0,
        'precio_por_kg': float(producto_dict.get('precio_por_kg', 0.0)) if producto_dict.get('precio_por_kg') else 0.0,
        'precio_normal': float(producto_dict.get('precio_normal', 0.0)) if producto_dict.get('precio_normal') else 0.0
    }

def agregar_credito(cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, venta_id):
    """Agregar un crédito pendiente con hora específica"""
    cursor.execute('''
        INSERT INTO creditos_pendientes (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, venta_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cliente, monto, fecha_venta, fecha_vencimiento, hora_vencimiento, venta_id))
    conn.commit()

def obtener_creditos_vencidos_con_hora():
    """Obtener créditos que vencen hoy considerando la hora"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
        FROM creditos_pendientes 
        WHERE ((fecha_vencimiento < ? OR (fecha_vencimiento = ? AND hora_vencimiento <= ?)) 
               AND pagado = 0)
        ORDER BY fecha_vencimiento, hora_vencimiento
    ''', (fecha_hoy, fecha_hoy, hora_actual))
    return cursor.fetchall()

def obtener_alertas_pendientes():
    """Obtener créditos que necesitan alerta pero no se ha mostrado"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id
        FROM creditos_pendientes 
        WHERE ((fecha_vencimiento < ? OR (fecha_vencimiento = ? AND hora_vencimiento <= ?)) 
               AND pagado = 0 AND alerta_mostrada = 0)
        ORDER BY fecha_vencimiento, hora_vencimiento
    ''', (fecha_hoy, fecha_hoy, hora_actual))
    return cursor.fetchall()

def marcar_alerta_mostrada(credito_id):
    """Marcar que la alerta ya fue mostrada"""
    cursor.execute("UPDATE creditos_pendientes SET alerta_mostrada = 1 WHERE id = ?", (credito_id,))
    conn.commit()

def marcar_credito_pagado(credito_id):
    """Marcar un crédito como pagado"""
    cursor.execute("UPDATE creditos_pendientes SET pagado = 1 WHERE id = ?", (credito_id,))
    conn.commit()

def mostrar_popup_alertas_mejorado():
    """Mostrar popup con alertas críticas y diseño mejorado"""
    alertas = obtener_alertas_pendientes()
    
    if alertas:
        st.markdown("""
        <div class="alert-critica">
            🐄🚨 ¡ALERTA DE CRÉDITOS VENCIDOS! 🚨🐄
        </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas:
            cliente, monto, fecha_venc, hora_venc, credito_id = alerta
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.error(f"💰 **{cliente}** debe {formatear_moneda(monto)} desde {fecha_venc} a las {hora_venc}")
            with col2:
                if st.button("✅ PAGADO", key=f"pagar_popup_{credito_id}", type="primary"):
                    marcar_credito_pagado(credito_id)
                    st.success(f"✅ Crédito de {cliente} marcado como pagado")
                    st.rerun()
            with col3:
                if st.button("⏰ MÁS TARDE", key=f"recordar_{credito_id}"):
                    marcar_alerta_mostrada(credito_id)
                    st.info("Se volverá a alertar mañana a las 3 PM")
                    st.rerun()

def mostrar():
    # Aplicar estilos personalizados
    aplicar_estilos_custom()
    
    # Título principal con vaca - más compacto
    st.markdown("""
    <div class="titulo-principal">
        🐄 CREMERÍA CAMACHO'S 🐄
    </div>
    """, unsafe_allow_html=True)
    
    # Sistema de alertas mejorado
    mostrar_popup_alertas_mejorado()
    
    # Verificar si es hora de mostrar recordatorios (3 PM)
    hora_actual = datetime.now().strftime("%H:%M")
    if hora_actual >= "15:00" and hora_actual <= "15:30":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); padding: 1.2rem; border-radius: 12px; text-align: center; font-size: 1.1rem; font-weight: bold; color: #2d3436; margin: 0.8rem 0;">
            🕒 HORA DE RECORDATORIOS (3:00 PM) - Revisa los créditos pendientes abajo
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Mensaje informativo del flujo
    st.markdown("""
    <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 1rem; border-radius: 12px; text-align: center; color: #2d3436; font-size: 1rem; font-weight: bold; margin: 0.8rem 0;">
        📝 <strong>FLUJO DE VENTA:</strong> 1️⃣ Agrega productos → 2️⃣ Selecciona tipo de cliente y pago → 3️⃣ Finaliza la venta
    </div>
    """, unsafe_allow_html=True)
    
    # Sección de productos - título más compacto
    st.markdown("""
    <div style="background: linear-gradient(135deg, #83b300 0%, #00a085 100%); padding: .5rem; border-radius: 16px; margin: 0.8rem 0;">
        <h2 style="color: white; text-align: center; margin-bottom: 0.8rem; font-size: 1.6rem;">📦 PASO 1: AGREGAR PRODUCTOS</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col_codigo, col_cantidad = st.columns([2, 1])
    
    with col_codigo:
        st.markdown("#### 🔍 Código de Barras")
        codigo = st.text_input(
            "Código de Barras",
            placeholder="Escanea o ingresa el código de barras del producto",
            label_visibility="collapsed",
            key="codigo_input"
        )
    
    # DETECCIÓN DE TICKETS
    es_ticket = False
    if codigo and len(codigo) >= 13 and len(codigo) % 13 == 0:
        es_ticket = True
        productos_ticket = parsear_codigo_bascula(codigo)
        
        if productos_ticket:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); padding: 1.5rem; border-radius: 15px; margin: 1rem 0; color: white; text-align: center;">
                <div style="font-size: 1.6rem; font-weight: bold;">🎫 TICKET DETECTADO</div>
                <div style="font-size: 1.2rem; margin-top: 0.5rem;">📦 {len(productos_ticket)} producto(s)</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✅ PROCESAR TICKET", type="primary", width='stretch'):
                agregados = 0
                no_encontrados = []

                # Debug: mostrar lista de productos parseados
                st.info(f"DEBUG: productos_ticket = {productos_ticket}")

                for codigo_prod, valor in productos_ticket:
                    prod = obtener_producto_por_codigo(codigo_prod)
                    if prod:
                        info = obtener_informacion_producto(prod)

                        # Debug: mostrar valores crudos y cálculos alternativos
                        cant_100 = valor // 100
                        cant_1000 = valor // 1000
                        st.info(f"DEBUG parse: codigo={codigo_prod} valor_raw={valor} -> //100={cant_100}, //1000={cant_1000}, tipo_db={info['tipo_venta']}")

                        if info['tipo_venta'] == 'granel':
                            peso_kg = valor / 1000.0
                            precio_kg = obtener_precio_granel_por_tipo(prod, "Normal")
                            total = precio_kg * peso_kg
                            if info['stock_kg'] >= peso_kg:
                                st.session_state.carrito.append({
                                    'codigo': info['codigo'],
                                    'nombre': f"{info['nombre']} ({peso_kg:.3f} Kg)",
                                    'cantidad': 1,
                                    'peso': peso_kg,
                                    'precio_unitario': precio_kg,
                                    'total': total,
                                    'tipo_venta': 'granel'
                                })
                                agregados += 1
                        else:
                            # Heurística: calcular cantidad por //100 por defecto,
                            # pero si ese resultado es muy grande y //1000 tiene sentido, usarlo.
                            cant = cant_100
                            # Si cant parece excesivo (>10) y cant_1000 es razonable, preferir cant_1000
                            if cant > 10 and cant_1000 > 0 and cant_1000 <= info.get('stock', cant_1000):
                                st.info(f"DEBUG ajuste cantidad: usando //1000 en vez de //100 para {codigo_prod} -> {cant_1000}")
                                cant = cant_1000
                            if cant == 0:
                                cant = 1

                            precio = obtener_precio_por_tipo(prod, "Normal")
                            total = precio * cant
                            if info['stock'] >= cant:
                                st.session_state.carrito.append({
                                    'codigo': info['codigo'],
                                    'nombre': info['nombre'],
                                    'cantidad': cant,
                                    'peso': 0,
                                    'precio_unitario': precio,
                                    'total': total,
                                    'tipo_venta': 'unidad'
                                })
                                agregados += 1
                    else:
                        no_encontrados.append(codigo_prod)

                if agregados > 0:
                    st.success(f"✅ {agregados} productos agregados")
                    st.rerun()
                if no_encontrados:
                    st.warning(f"⚠️ No encontrados: {', '.join(no_encontrados)}")
    
    # Verificar si el producto existe y obtener información
    producto_info = None
    info_producto = None
    if codigo and not es_ticket:
        producto_info = obtener_producto_por_codigo(codigo)
        if producto_info:
            info_producto = obtener_informacion_producto(producto_info)
    
    # Mostrar información del producto encontrado
    if info_producto:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 1.5rem; border-radius: 15px; margin: 1rem 0; color: white; text-align: center;">
            <div style="font-size: 1.4rem; font-weight: bold; margin-bottom: 0.5rem;">
                📦 PRODUCTO ENCONTRADO
            </div>
            <div style="font-size: 1.8rem; font-weight: bold; color: #fdcb6e;">
                {info_producto['nombre']}
            </div>
            <div style="font-size: 1.1rem; margin-top: 0.5rem;">
                🏷️ Código: {info_producto['codigo']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif codigo and len(codigo) > 3 and not es_ticket:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%); padding: 1.5rem; border-radius: 15px; margin: 1rem 0; color: white; text-align: center;">
            <div style="font-size: 1.4rem; font-weight: bold; margin-bottom: 0.5rem;">
                ❌ PRODUCTO NO ENCONTRADO
            </div>
            <div style="font-size: 1.1rem;">
                🔍 Código buscado: {codigo}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_cantidad:
        if info_producto:
            if info_producto['tipo_venta'] == 'granel':
                st.markdown("#### ⚖️ Peso (Kg)")
                peso = st.number_input(
                    "Peso en Kilogramos",
                    min_value=0.050, 
                    value=0.500, 
                    step=0.050, 
                    format="%.3f",
                    label_visibility="collapsed"
                )
                cantidad = 1
                # Información del producto a granel
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; color: white; text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: bold;">⚖️ PRODUCTO A GRANEL</div>
                </div>
                """, unsafe_allow_html=True)
                
                col_info_granel = st.columns(2)
                with col_info_granel[0]:
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 0.8rem; border-radius: 8px; text-align: center; color: #1565c0; font-weight: bold;">
                        📊 STOCK<br><span style="font-size: 1.3rem;">{info_producto['stock_kg']:.3f} Kg</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_info_granel[1]:
                    st.markdown(f"""
                    <div style="background: #e8f5e8; padding: 0.8rem; border-radius: 8px; text-align: center; color: #2e7d32; font-weight: bold;">
                        💰 PRECIO<br><span style="font-size: 1.3rem;">{formatear_moneda(info_producto['precio_por_kg'])}/Kg</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("#### 📊 Cantidad")
                cantidad = st.number_input(
                    "Cantidad de productos",
                    min_value=1, 
                    value=1, 
                    step=1,
                    label_visibility="collapsed"
                )
                peso = 0
                # Información del producto por unidad
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; color: white; text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: bold;">🏷️ PRODUCTO POR UNIDAD</div>
                </div>
                """, unsafe_allow_html=True)
                
                col_info_unidad = st.columns(2)
                with col_info_unidad[0]:
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 0.8rem; border-radius: 8px; text-align: center; color: #1565c0; font-weight: bold;">
                        📊 STOCK<br><span style="font-size: 1.3rem;">{info_producto['stock']} unidades</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_info_unidad[1]:
                    st.markdown(f"""
                    <div style="background: #e8f5e8; padding: 0.8rem; border-radius: 8px; text-align: center; color: #2e7d32; font-weight: bold;">
                        💰 PRECIO<br><span style="font-size: 1.3rem;">{formatear_moneda(info_producto['precio_normal'])}/unidad</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("#### 📊 Cantidad")
            cantidad = st.number_input(
                "Cantidad de productos",
                min_value=1, 
                value=1, 
                step=1,
                label_visibility="collapsed"
            )
            peso = 0
            # No mostrar nada aquí ya que el mensaje se muestra arriba

    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    # Variables por defecto para el flujo inicial (antes de seleccionar cliente)
    cliente_tipo_inicial = "Normal"  # Por defecto para mostrar precios iniciales

    # Botón para agregar al carrito mejorado
    col_btn_agregar = st.columns([2, 1, 2])
    with col_btn_agregar[1]:
        if st.button("🛒 AGREGAR AL CARRITO", type="primary"):
            if info_producto:
                if info_producto['tipo_venta'] == 'granel':
                    if info_producto['stock_kg'] >= peso:
                        precio_kg = obtener_precio_granel_por_tipo(producto_info, cliente_tipo_inicial)
                        total = precio_kg * peso
                        
                        precio_original = info_producto['precio_por_kg']
                        descuento_info = ""
                        if cliente_tipo_inicial != "Normal" and precio_kg < precio_original:
                            descuento_pct = ((precio_original - precio_kg) / precio_original * 100)
                            descuento_info = f" (Desc. {descuento_pct:.0f}%)"
                        
                        st.session_state.carrito.append({
                            'codigo': info_producto['codigo'],
                            'nombre': f"{info_producto['nombre']} ({peso:.3f} Kg){descuento_info}",
                            'cantidad': cantidad,
                            'peso': peso,
                            'precio_unitario': precio_kg,
                            'total': total,
                            'tipo_venta': 'granel'
                        })
                        
                        # Mensaje de éxito mejorado
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: .5rem; border-radius: 15px; text-align: center; color: white; font-size: 1.2rem; font-weight: bold; margin: 1rem 0;">
                            ✅ {info_producto['nombre']} AGREGADO<br>
                            ⚖️ {peso:.3f} Kg × {formatear_moneda(precio_kg)}/Kg = {formatear_moneda(total)}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Marcar que se debe hacer scroll
                        st.session_state.scroll_to_finalizar = True
                        
                        # Hacer rerun para que se muestre el carrito y luego scroll
                        st.rerun()
                        
                    else:
                        st.error(f"❌ **Stock insuficiente**. Disponible: **{info_producto['stock_kg']:.3f} Kg**")
                else:
                    if info_producto['stock'] >= cantidad:
                        precio = obtener_precio_por_tipo(producto_info, cliente_tipo_inicial)
                        total = precio * cantidad
                        
                        precio_original = info_producto['precio_normal']
                        descuento_info = ""
                        if cliente_tipo_inicial != "Normal" and precio < precio_original:
                            descuento_pct = ((precio_original - precio) / precio_original * 100)
                            descuento_info = f" (Desc. {descuento_pct:.0f}%)"
                        
                        st.session_state.carrito.append({
                            'codigo': info_producto['codigo'],
                            'nombre': f"{info_producto['nombre']}{descuento_info}",
                            'cantidad': cantidad,
                            'peso': 0,
                            'precio_unitario': precio,
                            'total': total,
                            'tipo_venta': 'unidad'
                        })
                        
                        # Mensaje de éxito mejorado
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: .5rem; border-radius: 15px; text-align: center; color: white; font-size: 1.2rem; font-weight: bold; margin: 1rem 0;">
                            ✅ {info_producto['nombre']} AGREGADO<br>
                            🏷️ {cantidad} × {formatear_moneda(precio)} = {formatear_moneda(total)}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Marcar que se debe hacer scroll
                        st.session_state.scroll_to_finalizar = True
                        
                        # Hacer rerun para que se muestre el carrito y luego scroll
                        st.rerun()
                        
                    else:
                        st.error(f"❌ **Stock insuficiente**. Disponible: **{info_producto['stock']} unidades**")
            else:
                st.warning("⚠️ **Producto no encontrado**")

    # Mostrar carrito - título más compacto y color cambiado
    if st.session_state.carrito:
        st.markdown("---")
        st.markdown("""        
        <div style="background: linear-gradient(135deg, #a8d5ba 0%, #90c695 100%); padding: 1.5rem; border-radius: 16px; margin: 0.8rem 0; border: 2px solid #7eb693;">
            <h2 style="color: #1e3a28; text-align: center; margin-bottom: 0.8rem; font-size: 1.6rem;">🛒 CARRITO DE COMPRAS</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Encabezados del carrito con mejor diseño
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; color: white; font-weight: bold; font-size: 1.1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 3; text-align: left;">
                    📦 NOMBRE DEL PRODUCTO
                </div>
                <div style="flex: 1.5; text-align: center;">
                    📊 CANTIDAD/PESO
                </div>
                <div style="flex: 1.5; text-align: center;">
                    💲 PRECIO UNITARIO
                </div>
                <div style="flex: 1.5; text-align: center;">
                    💰 TOTAL
                </div>
                <div style="flex: 0.5; text-align: center;">
                    ⚙️
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar items del carrito con diseño mejorado y organizado
        for i, item in enumerate(st.session_state.carrito):
            # Determinar el tipo de medida y formato
            if item['tipo_venta'] == 'granel':
                icono_producto = "⚖️"
                cantidad_formato = f"{item['peso']:.3f} Kg"
                precio_unitario_label = f"{formatear_moneda(item['precio_unitario'])}/Kg"
            else:
                icono_producto = "🏷️"
                cantidad_formato = f"{item['cantidad']} unidades"
                precio_unitario_label = f"{formatear_moneda(item['precio_unitario'])}/unidad"
            
            st.markdown(f"""
            <div class="carrito-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 3; text-align: left;">
                        {icono_producto} <strong>{item['nombre']}</strong><br>
                        <small style="color: #2d5a3d; font-size: 0.9rem;">Código: {item['codigo']}</small>
                    </div>
                    <div style="flex: 1.5; text-align: center; font-size: 1.1rem; font-weight: bold;">
                        {cantidad_formato}
                    </div>
                    <div style="flex: 1.5; text-align: center; font-size: 1.1rem; font-weight: bold;">
                        {precio_unitario_label}
                    </div>
                    <div style="flex: 1.5; text-align: center; font-size: 1.3rem; font-weight: bold; color: #1e3a28;">
                        {formatear_moneda(item['total'])}
                    </div>
                    <div style="flex: 0.5; text-align: center;">
                        <!-- Espacio para botones -->
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botones para eliminar y editar con mejor diseño
            col_acciones = st.columns([1, 5, 1, 1])
            with col_acciones[0]:
                if st.button("🗑️", key=f"eliminar_{i}", help="Eliminar este producto", type="secondary"):
                    st.session_state.carrito.pop(i)
                    st.success("✅ Producto eliminado del carrito")
                    st.rerun()
            
            with col_acciones[2]:
                if st.button("✏️", key=f"editar_{i}", help="Editar cantidad/peso", type="secondary"):
                    st.session_state[f'editando_{i}'] = True
                    st.rerun()
            
            # Sistema de edición mejorado
            if st.session_state.get(f'editando_{i}', False):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #d63031;">
                    <h4 style="color: white; margin-bottom: 1rem;">✏️ Editando: {item['nombre']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col_edit1, col_edit2, col_edit3, col_edit4 = st.columns([2, 1, 1, 1])
                
                with col_edit1:
                    st.info(f"**Producto:** {item['nombre']}")
                    st.info(f"**Código:** {item['codigo']}")
                
                with col_edit2:
                    if item['tipo_venta'] == 'granel':
                        nuevo_peso = st.number_input(
                            "**Nuevo peso (Kg):**", 
                            min_value=0.050, 
                            value=float(item['peso']), 
                            step=0.050, 
                            format="%.3f",
                            key=f"edit_peso_{i}"
                        )
                    else:
                        nueva_cantidad = st.number_input(
                            "**Nueva cantidad:**", 
                            min_value=1, 
                            value=int(item['cantidad']), 
                            step=1,
                            key=f"edit_cantidad_{i}"
                        )
                
                with col_edit3:
                    st.markdown("**Precio unitario:**")
                    if item['tipo_venta'] == 'granel':
                        st.info(f"{formatear_moneda(item['precio_unitario'])}/Kg")
                        nuevo_total = item['precio_unitario'] * nuevo_peso
                        st.success(f"**Nuevo total:** {formatear_moneda(nuevo_total)}")
                    else:
                        st.info(f"{formatear_moneda(item['precio_unitario'])}/unidad")
                        nuevo_total = item['precio_unitario'] * nueva_cantidad
                        st.success(f"**Nuevo total:** {formatear_moneda(nuevo_total)}")
                
                with col_edit4:
                    col_btn_edit = st.columns(2)
                    with col_btn_edit[0]:
                        if st.button("✅ Guardar", key=f"guardar_{i}", type="primary"):
                            if item['tipo_venta'] == 'granel':
                                st.session_state.carrito[i]['peso'] = nuevo_peso
                                st.session_state.carrito[i]['total'] = item['precio_unitario'] * nuevo_peso
                            else:
                                st.session_state.carrito[i]['cantidad'] = nueva_cantidad
                                st.session_state.carrito[i]['total'] = item['precio_unitario'] * nueva_cantidad
                            
                            del st.session_state[f'editando_{i}']
                            st.success("✅ Producto actualizado")
                            st.rerun()
                    
                    with col_btn_edit[1]:
                        if st.button("❌ Cancelar", key=f"cancelar_{i}", type="secondary"):
                            del st.session_state[f'editando_{i}']
                            st.rerun()
                
                st.markdown("---")
        
        # Resumen del carrito con mejor diseño
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); padding: 1rem; border-radius: 10px; margin: 1rem 0; color: white;">
            <h3 style="text-align: center; margin-bottom: 1rem; color: #ddd;">📊 RESUMEN DEL CARRITO</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Calcular total
        total_general = sum(item['total'] for item in st.session_state.carrito)
        
        # Mostrar total destacado
        st.markdown(f"""
        <div class="total-destacado">
            💰 TOTAL GENERAL: {formatear_moneda(total_general)}
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas del carrito mejoradas con más detalle
        col_metricas = st.columns(4)
        
        with col_metricas[0]:
            productos_unidad = len([item for item in st.session_state.carrito if item['tipo_venta'] == 'unidad'])
            total_unidades = sum([item['cantidad'] for item in st.session_state.carrito if item['tipo_venta'] == 'unidad'])
            mostrar_metrica_mejorada(f"Por Unidad\n{total_unidades} items", productos_unidad, "🏷️", False)
        
        with col_metricas[1]:
            productos_granel = len([item for item in st.session_state.carrito if item['tipo_venta'] == 'granel'])
            peso_total = sum([item['peso'] for item in st.session_state.carrito if item['tipo_venta'] == 'granel'])
            mostrar_metrica_mejorada(f"A Granel\n{peso_total:.3f} Kg", productos_granel, "⚖️", False)
        
        with col_metricas[2]:
            total_productos = len(st.session_state.carrito)
            mostrar_metrica_mejorada("Total Productos", total_productos, "📦", False)
        
        with col_metricas[3]:
            mostrar_metrica_mejorada("TOTAL A PAGAR", total_general, "💰", True)
        
        # Configuración de venta - DESPUÉS de agregar productos
        st.markdown("---")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2eb8b8 0%, #0984e3 100%); padding: 1.5rem; border-radius: 16px; margin: 0.8rem 0;">
            <h2 style="color: white; text-align: center; margin-bottom: 0.8rem; font-size: 1.6rem;">💰 PASO 2: CONFIGURAR VENTA</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Tipo de Cliente")
            cliente_tipo = st.selectbox(
                "Tipo de Cliente",
                [
                    "Normal", 
                    "Mayoreo Tipo 1", 
                    "Mayoreo Tipo 2", 
                    "Mayoreo Tipo 3"
                ],
                label_visibility="collapsed",
                key="cliente_tipo_final"
            )
        
        with col2:
            st.markdown("#### 💳 Tipos de Pago")
            
            modo_pago = st.radio(
                "Modo de pago:",
                ["💵 Pago único", "💰 Pago mixto"],
                index=0,
                horizontal=True,
                key="modo_pago_final"
            )
            
            if modo_pago == "� Pago mixto":
                st.markdown("**Selecciona múltiples tipos de pago:**")
                col_pago1, col_pago2 = st.columns(2)
                
                with col_pago1:
                    pago_efectivo = st.checkbox("💵 Efectivo", value=True, key="efectivo_final")
                    pago_tarjeta = st.checkbox("💳 Tarjeta", key="tarjeta_final")
                
                with col_pago2:
                    pago_transferencia = st.checkbox("📱 Transferencia", key="transferencia_final")
                    pago_credito = st.checkbox("📋 Crédito", key="credito_final")
                
            else:
                # Configurar pagos únicos basados en la selección
                pago_efectivo = modo_pago == "💵 Efectivo"
                pago_tarjeta = modo_pago == "💳 Tarjeta"
                pago_transferencia = modo_pago == "📱 Transferencia"
                pago_credito = modo_pago == "📋 Crédito"
        
        # Botón para recalcular precios si se cambia el tipo de cliente
        if cliente_tipo != "Normal":
            col_recalc1, col_recalc2, col_recalc3 = st.columns([1, 2, 1])
            with col_recalc2:
                if st.button(f"🔄 RECALCULAR PRECIOS PARA {cliente_tipo.upper()}", type="secondary", key="recalcular_precios"):
                    # Recalcular precios de todos los productos en el carrito
                    for i, item in enumerate(st.session_state.carrito):
                        # Obtener información del producto original
                        producto_original = obtener_producto_por_codigo(item['codigo'])
                        if producto_original:
                            if item['tipo_venta'] == 'granel':
                                nuevo_precio_kg = obtener_precio_granel_por_tipo(producto_original, cliente_tipo)
                                peso = item['peso']
                                nuevo_total = nuevo_precio_kg * peso
                                
                                # Actualizar precio y total
                                st.session_state.carrito[i]['precio_unitario'] = nuevo_precio_kg
                                st.session_state.carrito[i]['total'] = nuevo_total
                                
                                # Actualizar nombre con descuento
                                info_prod = obtener_informacion_producto(producto_original)
                                precio_original = info_prod['precio_por_kg']
                                descuento_info = ""
                                if nuevo_precio_kg < precio_original:
                                    descuento_pct = ((precio_original - nuevo_precio_kg) / precio_original * 100)
                                    descuento_info = f" (Desc. {descuento_pct:.0f}%)"
                                
                                # Limpiar nombre anterior y agregar nuevo descuento
                                nombre_base = info_prod['nombre']
                                st.session_state.carrito[i]['nombre'] = f"{nombre_base} ({peso:.3f} Kg){descuento_info}"
                            else:
                                nuevo_precio = obtener_precio_por_tipo(producto_original, cliente_tipo)
                                cantidad = item['cantidad']
                                nuevo_total = nuevo_precio * cantidad
                                
                                # Actualizar precio y total
                                st.session_state.carrito[i]['precio_unitario'] = nuevo_precio
                                st.session_state.carrito[i]['total'] = nuevo_total
                                
                                # Actualizar nombre con descuento
                                info_prod = obtener_informacion_producto(producto_original)
                                precio_original = info_prod['precio_normal']
                                descuento_info = ""
                                if nuevo_precio < precio_original:
                                    descuento_pct = ((precio_original - nuevo_precio) / precio_original * 100)
                                    descuento_info = f" (Desc. {descuento_pct:.0f}%)"
                                
                                # Limpiar nombre anterior y agregar nuevo descuento
                                nombre_base = info_prod['nombre']
                                st.session_state.carrito[i]['nombre'] = f"{nombre_base}{descuento_info}"
                    
                    st.success(f"✅ Precios recalculados para cliente {cliente_tipo}")
                    st.rerun()

        # Variables para almacenar información de pago
        monto_efectivo = 0
        monto_tarjeta = 0
        monto_transferencia = 0
        monto_credito = 0
        cliente_credito = None
        fecha_vencimiento_credito = None
        hora_vencimiento_credito = "15:00"

        # Información de descuentos con mejor formato - DESPUÉS de seleccionar cliente
        if cliente_tipo != "Normal":
            descuentos_aplicados = [item for item in st.session_state.carrito if 'Desc.' in item['nombre']]
            if descuentos_aplicados:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); padding: 1.5rem; border-radius: 15px; text-align: center; color: white; font-size: 1.2rem; font-weight: bold; margin: 1rem 0;">
                    🎉 CLIENTE {cliente_tipo.upper()} - ¡DESCUENTOS APLICADOS! 🎉<br>
                    <small style="font-size: 1rem;">Se aplicaron descuentos especiales en {len(descuentos_aplicados)} productos</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Configuración de pagos con diseño mejorado
        tipos_pago_seleccionados = []
        if pago_efectivo:
            tipos_pago_seleccionados.append("Efectivo")
        if pago_tarjeta:
            tipos_pago_seleccionados.append("Tarjeta")
        if pago_transferencia:
            tipos_pago_seleccionados.append("Transferencia")
        if pago_credito:
            tipos_pago_seleccionados.append("Crédito")
        
        if tipos_pago_seleccionados:
            st.markdown("---")
            st.markdown("""
            <div style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); padding: .5rem; border-radius: 16px; margin: 0.8rem 0;">
                <h2 style="color: white; text-align: center; margin-bottom: 0.8rem; font-size: 1.6rem;">💳 DISTRIBUCIÓN DE PAGOS</h2>
            </div>
            """, unsafe_allow_html=True)
            
            if len(tipos_pago_seleccionados) == 1:
                tipo_unico = tipos_pago_seleccionados[0]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #00cec9 0%, #55a3ff 100%); padding: 1.5rem; border-radius: 15px; text-align: center; color: white; font-size: 1.3rem; font-weight: bold; margin: 0.8rem 0;">
                    💰 Todo el monto ({formatear_moneda(total_general)}) será pagado con: <strong>{tipo_unico}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                if tipo_unico == "Efectivo":
                    monto_efectivo = total_general
                elif tipo_unico == "Tarjeta":
                    monto_tarjeta = total_general
                elif tipo_unico == "Transferencia":
                    monto_transferencia = total_general
                elif tipo_unico == "Crédito":
                    monto_credito = total_general
            
            else:
                st.markdown("#### Distribuye el monto total entre los tipos de pago seleccionados:")
                
                col_montos = st.columns(len(tipos_pago_seleccionados))
                
                for i, tipo in enumerate(tipos_pago_seleccionados):
                    with col_montos[i]:
                        if tipo == "Efectivo":
                            monto_efectivo = st.number_input(
                                f"Monto Efectivo",
                                min_value=0.0, 
                                max_value=float(total_general), 
                                step=0.01, 
                                key="efectivo", 
                                format="%.2f",
                                label_visibility="collapsed"
                            )
                            st.markdown("💵 **Efectivo**")
                        elif tipo == "Tarjeta":
                            monto_tarjeta = st.number_input(
                                f"Monto Tarjeta",
                                min_value=0.0, 
                                max_value=float(total_general), 
                                step=0.01, 
                                key="tarjeta", 
                                format="%.2f",
                                label_visibility="collapsed"
                            )
                            st.markdown("💳 **Tarjeta**")
                        elif tipo == "Transferencia":
                            monto_transferencia = st.number_input(
                                f"Monto Transferencia",
                                min_value=0.0, 
                                max_value=float(total_general), 
                                step=0.01, 
                                key="transferencia", 
                                format="%.2f",
                                label_visibility="collapsed"
                            )
                            st.markdown("📱 **Transferencia**")
                        elif tipo == "Crédito":
                            monto_credito = st.number_input(
                                f"Monto Crédito",
                                min_value=0.0, 
                                max_value=float(total_general), 
                                step=0.01, 
                                key="credito", 
                                format="%.2f",
                                label_visibility="collapsed"
                            )
                            st.markdown("📋 **Crédito**")
                
                # Validación de suma de pagos
                suma_pagos = monto_efectivo + monto_tarjeta + monto_transferencia + monto_credito
                diferencia = abs(suma_pagos - total_general)
                
                if diferencia > 0.01:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%); padding: 1rem; border-radius: 10px; text-align: center; color: white; font-size: 1.1rem; font-weight: bold;">
                        ❌ La suma de pagos ({formatear_moneda(suma_pagos)}) no coincide con el total ({formatear_moneda(total_general)})<br>
                        Diferencia: {formatear_moneda(diferencia)}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 1rem; border-radius: 10px; text-align: center; color: white; font-size: 1.1rem; font-weight: bold;">
                        ✅ Suma de pagos correcta: {formatear_moneda(suma_pagos)}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Campos adicionales para crédito - título más compacto
            if pago_credito and monto_credito > 0:
                st.markdown("---")
                st.markdown("""
                <div style="background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%); padding: 1.5rem; border-radius: 16px; margin: 0.8rem 0;">
                    <h3 style="color: white; text-align: center; margin-bottom: 0.8rem; font-size: 1.4rem;">📋 INFORMACIÓN DE CRÉDITO</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col_cred1, col_cred2 = st.columns(2)
                
                with col_cred1:
                    cliente_credito = st.text_input(
                        "Nombre del cliente para crédito",
                        placeholder="Nombre completo del cliente",
                        label_visibility="collapsed"
                    )
                    st.markdown("👤 **Nombre del cliente**")
                
                with col_cred2:
                    fecha_vencimiento_credito = st.date_input(
                        "Fecha de vencimiento del crédito",
                        value=datetime.now().date() + timedelta(days=1),
                        min_value=datetime.now().date()
                    )
                    
                    hora_vencimiento_credito = st.time_input(
                        "Hora de vencimiento",
                        value=datetime.strptime("15:00", "%H:%M").time()
                    )

        # Botones de acción principal SIN título "Finalizar Compra"
        st.markdown("---")
        
        # Agregar ancla específica para el scroll automático
        st.markdown('<div id="finalizar-venta-section"></div>', unsafe_allow_html=True)
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("🗑️ LIMPIAR CARRITO", type="secondary"):
                st.session_state.carrito = []
                keys_to_remove = [key for key in st.session_state.keys() if key.startswith('editando_')]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.success("🗑️ **Carrito limpiado**")
                st.rerun()
        
        with col_btn2:
            # Validaciones
            puede_finalizar = True
            mensaje_error = ""
            
            if not st.session_state.carrito:
                puede_finalizar = False
                mensaje_error = "El carrito está vacío"
            elif not tipos_pago_seleccionados:
                puede_finalizar = False
                mensaje_error = "Selecciona al menos un tipo de pago"
            elif len(tipos_pago_seleccionados) > 1:
                # Validación de suma de pagos
                suma_pagos = monto_efectivo + monto_tarjeta + monto_transferencia + monto_credito
                diferencia = abs(suma_pagos - total_general)
                
                if diferencia > 0.01:
                    puede_finalizar = False
                    mensaje_error = "La suma de pagos no coincide con el total"
            elif pago_credito and monto_credito > 0 and not cliente_credito:
                puede_finalizar = False
                mensaje_error = "Ingresa el nombre del cliente para crédito"
            
            if not puede_finalizar:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%); padding: 0.8rem; border-radius: 8px; text-align: center; color: white; font-size: 1rem; font-weight: bold;">
                    ❌ {mensaje_error}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Botón con ID específico y clase para targeting
                st.markdown('<div id="finalizar-venta-button" class="finalizar-button">', unsafe_allow_html=True)
                
                if st.button("💰 **FINALIZAR VENTA**", type="primary", key="finalizar_venta_btn"):
                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tipos_pago_str = ", ".join(tipos_pago_seleccionados)
                    
                    # Auto-configurar fecha y hora de vencimiento para crédito
                    if monto_credito > 0:
                        if fecha_vencimiento_credito is None:
                            fecha_vencimiento_credito = (datetime.now() + timedelta(days=1)).date()
                        if hora_vencimiento_credito is None:
                            hora_vencimiento_credito = datetime.strptime("15:00", "%H:%M").time()
                    
                    # Procesar venta
                    try:
                        venta_id = None
                        productos_vendidos = []
                        
                        for item in st.session_state.carrito:
                            pagado = 1
                            if monto_credito == total_general:
                                pagado = 0
                        
                            peso_vendido = item.get('peso', 0)
                            tipo_venta = item.get('tipo_venta', 'unidad')
                            
                            # Preparar fechas y horas de crédito de forma segura
                            fecha_credito_str = ""
                            hora_credito_str = "15:00"
                            
                            if fecha_vencimiento_credito:
                                if isinstance(fecha_vencimiento_credito, str):
                                    fecha_credito_str = fecha_vencimiento_credito
                                else:
                                    fecha_credito_str = fecha_vencimiento_credito.strftime("%Y-%m-%d")
                            
                            if hora_vencimiento_credito:
                                if isinstance(hora_vencimiento_credito, str):
                                    hora_credito_str = hora_vencimiento_credito
                                else:
                                    hora_credito_str = hora_vencimiento_credito.strftime("%H:%M")
                        
                            cursor.execute('''
                                INSERT INTO ventas (fecha, codigo, nombre, cantidad, precio_unitario, total, tipo_cliente, tipos_pago, 
                                                  monto_efectivo, monto_tarjeta, monto_transferencia, monto_credito,
                                                  fecha_vencimiento_credito, hora_vencimiento_credito, cliente_credito, pagado,
                                                  peso_vendido, tipo_venta)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (fecha, item['codigo'], item['nombre'], item['cantidad'], item['precio_unitario'], item['total'], 
                                  cliente_tipo, tipos_pago_str, monto_efectivo, monto_tarjeta, monto_transferencia, monto_credito,
                                  fecha_credito_str, hora_credito_str, 
                                  cliente_credito or "", pagado, peso_vendido, tipo_venta))
                        
                            if venta_id is None:
                                venta_id = cursor.lastrowid
                        
                            # Actualizar stock
                            if tipo_venta == 'granel':
                                cursor.execute("UPDATE productos SET stock_kg = stock_kg - ?, stock = stock - ? WHERE codigo = ?", 
                                             (peso_vendido, item['cantidad'], item['codigo']))
                            else:
                                cursor.execute("UPDATE productos SET stock = stock - ? WHERE codigo = ?", 
                                             (item['cantidad'], item['codigo']))
                        
                            productos_vendidos.append(item)
                        
                        # Si hay crédito, agregarlo a la tabla (DENTRO del try)
                        if monto_credito > 0 and cliente_credito:
                            # Preparar fechas para agregar crédito de forma segura
                            fecha_credito_para_tabla = fecha_credito_str if fecha_credito_str else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                            hora_credito_para_tabla = hora_credito_str if hora_credito_str else "15:00"
                            
                            agregar_credito(cliente_credito, monto_credito, fecha, 
                                          fecha_credito_para_tabla, 
                                          hora_credito_para_tabla, venta_id)
                    
                        conn.commit()
                        
                        # Mensaje de éxito mejorado
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 3rem; border-radius: 25px; text-align: center; color: white; font-size: 2rem; font-weight: bold; margin: 2rem 0; box-shadow: 0 15px 50px rgba(0,184,148,0.4);">
                            🎉 ¡VENTA REGISTRADA EXITOSAMENTE! 🎉<br>
                            <div style="font-size: 1.5rem; margin-top: 1rem;">
                                💰 Total: {formatear_moneda(total_general)}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.balloons()
                        
                        # Limpiar carrito
                        st.session_state.carrito = []
                        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('editando_')]
                        for key in keys_to_remove:
                            del st.session_state[key]
                            
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #e17055 0%, #d63031 100%); padding: 1.5rem; border-radius: 15px; text-align: center; color: white; font-size: 1.2rem; font-weight: bold;">
                            ❌ Error al procesar la venta: {str(e)}
                        </div>
                        """, unsafe_allow_html=True)
                        conn.rollback()
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        with col_btn3:
            with st.expander("📊 **VISTA PREVIA DE LA VENTA**", expanded=False):
                if st.session_state.carrito:
                    st.markdown(f"**Tipo de cliente:** {cliente_tipo}")
                    if tipos_pago_seleccionados:
                        st.markdown(f"**Tipos de pago:** {', '.join(tipos_pago_seleccionados)}")
                    
                    st.markdown(f"**Productos en carrito:** {len(st.session_state.carrito)}")
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); padding: 1.2rem; border-radius: 12px; text-align: center; color: white; font-size: 1.3rem; font-weight: bold; margin: 0.8rem 0;">
                        💰 TOTAL A COBRAR: {formatear_moneda(total_general)}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("El carrito está vacío")

    # Sección de créditos pendientes con diseño mejorado
    st.markdown("---")
    with st.expander("📋 **VER TODOS LOS CRÉDITOS PENDIENTES**"):
        # Obtener créditos detallados para gestión
        cursor.execute('''
            SELECT id, cliente, monto, fecha_vencimiento, hora_vencimiento, fecha_venta
            FROM creditos_pendientes 
            WHERE pagado = 0 
            ORDER BY fecha_vencimiento, hora_vencimiento
        ''')
        creditos_detallados = cursor.fetchall()
        
        if creditos_detallados:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%); padding: 1rem; border-radius: 12px; text-align: center; color: white; font-size: 1.3rem; font-weight: bold; margin: 1rem 0;">
                📋 GESTIÓN DE CRÉDITOS PENDIENTES
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar cada crédito individualmente con botones de acción
            for credito in creditos_detallados:
                credito_id, cliente, monto, fecha_venc, hora_venc, fecha_venta = credito
                
                # Determinar si está vencido
                ahora = datetime.now()
                fecha_vencimiento_dt = datetime.strptime(f"{fecha_venc} {hora_venc}", "%Y-%m-%d %H:%M")
                esta_vencido = ahora > fecha_vencimiento_dt
                
                # Color según estado
                color_fondo = "#ff7675" if esta_vencido else "#74b9ff"
                texto_estado = "🚨 VENCIDO" if esta_vencido else "⏰ PENDIENTE"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color_fondo} 0%, #ddd 30%); padding: 1.2rem; border-radius: 12px; margin: 0.8rem 0; border-left: 5px solid {'#d63031' if esta_vencido else '#0984e3'};">
                    <div style="color: white; font-weight: bold; font-size: 1.1rem;">
                        👤 <strong>{cliente}</strong> | 💰 {formatear_moneda(monto)} | 📅 {fecha_venc} a las {hora_venc}
                    </div>
                    <div style="color: #2d3436; font-size: 0.9rem; margin-top: 0.5rem;">
                        Venta realizada: {fecha_venta} | Estado: {texto_estado}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Botones de acción para cada crédito
                col_accion1, col_accion2, col_accion3 = st.columns([2, 1, 1])
                
                with col_accion1:
                    st.markdown(f"**Acciones para {cliente}:**")
                
                with col_accion2:
                    if st.button(f"✅ MARCAR PAGADO", key=f"pagar_credito_{credito_id}", type="primary"):
                        marcar_credito_pagado(credito_id)
                        st.success(f"✅ Crédito de {cliente} marcado como pagado!")
                        st.rerun()
                
                with col_accion3:
                    if st.button(f"📞 RECORDAR DESPUÉS", key=f"recordar_credito_{credito_id}", type="secondary"):
                        marcar_alerta_mostrada(credito_id)
                        st.info(f"⏰ Se recordará el crédito de {cliente} más tarde")
                        st.rerun()
                
                st.markdown("---")
            
            # Resumen total
            cursor.execute('''
                SELECT cliente, SUM(monto) as total_deuda, COUNT(*) as num_creditos
                FROM creditos_pendientes 
                WHERE pagado = 0 
                GROUP BY cliente
                ORDER BY total_deuda DESC
            ''')
            resumen_por_cliente = cursor.fetchall()
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); padding: 1rem; border-radius: 12px; text-align: center; color: white; font-size: 1.2rem; font-weight: bold; margin: 1rem 0;">
                📊 RESUMEN POR CLIENTE
            </div>
            """, unsafe_allow_html=True)
            
            if resumen_por_cliente:
                df_resumen = pd.DataFrame(resumen_por_cliente, columns=['Cliente', 'Deuda Total', 'Núm. Créditos'])
                
                # Formatear deuda como moneda
                df_resumen['Deuda Total'] = df_resumen['Deuda Total'].apply(formatear_moneda)
                
                st.dataframe(
                    df_resumen,
                    hide_index=True,
                    width='stretch'
                )
                
                # Calcular totales
                total_general_creditos = sum([credito[1] for credito in resumen_por_cliente])
                total_creditos_count = len(creditos_detallados)
                
                col_total1, col_total2 = st.columns(2)
                with col_total1:
                    mostrar_metrica_mejorada("Total Monto Créditos", total_general_creditos, "💰", True)
                with col_total2:
                    mostrar_metrica_mejorada("Total Créditos Pendientes", total_creditos_count, "�", False)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 1.5rem; border-radius: 15px; text-align: center; color: white; font-size: 1.2rem; font-weight: bold;">
                ✅ No hay créditos pendientes
            </div>
            """, unsafe_allow_html=True)

    # Sección de búsqueda rápida con diseño mejorado
    st.markdown("---")
    with st.expander("🔍 **BÚSQUEDA RÁPIDA DE PRODUCTOS**"):
        busqueda = st.text_input(
            "Buscar producto por nombre o código",
            placeholder="Escribe para buscar...",
            key="busqueda_productos",
            label_visibility="collapsed"
        )
        
        if busqueda and len(busqueda) > 2:
            cursor.execute('''
                SELECT codigo, nombre, tipo_venta, precio_normal, precio_por_kg, stock, stock_kg
                FROM productos 
                WHERE LOWER(codigo) LIKE LOWER(?) OR LOWER(nombre) LIKE LOWER(?)
                ORDER BY 
                    CASE 
                        WHEN LOWER(nombre) = LOWER(?) THEN 1
                        WHEN LOWER(nombre) LIKE LOWER(?) THEN 2
                        WHEN LOWER(codigo) = LOWER(?) THEN 3
                        ELSE 4
                    END, nombre
                LIMIT 10
            ''', (f"%{busqueda}%", f"%{busqueda}%", busqueda, f"{busqueda}%", busqueda))
            
            resultados = cursor.fetchall()
            
            if resultados:
                st.markdown("### **Resultados encontrados:**")
                for producto in resultados:
                    codigo, nombre, tipo_venta, precio_normal, precio_por_kg, stock, stock_kg = producto
                    
                    col_prod1, col_prod2, col_prod3 = st.columns([2, 1, 1])
                    
                    with col_prod1:
                        icono = "⚖️" if tipo_venta == 'granel' else "🏷️"
                        st.markdown(f"{icono} **{codigo}** - {nombre}")
                    
                    with col_prod2:
                        if tipo_venta == 'granel':
                            st.markdown(f"**{formatear_moneda(precio_por_kg)}/Kg** | **{stock_kg:.2f} Kg**")
                        else:
                            st.markdown(f"**{formatear_moneda(precio_normal)}/und** | **{stock} uds**")
                    
                    with col_prod3:
                        if st.button("➕ **AGREGAR**", key=f"busq_{codigo}", type="primary"):
                            st.session_state.codigo_busqueda = codigo
                            st.info(f"**Código {codigo} seleccionado**. Agrega cantidad/peso arriba.")
            else:
                st.info("**No se encontraron productos con esa búsqueda**")

    # JavaScript mejorado que se ejecuta después del render
    if st.session_state.get('scroll_to_finalizar', False):
        # Limpiar la bandera
        st.session_state.scroll_to_finalizar = False
        
        st.markdown("""
        <script>
        // Función más robusta para scroll automático
        function scrollToFinalizarVenta() {
            console.log('Iniciando scroll automático...');
            
            // Buscar elementos en orden de prioridad
            const targets = [
                document.getElementById('finalizar-venta-button'),
                document.getElementById('finalizar-venta-section'),
                document.getElementById('carrito-section'),
                document.querySelector('.finalizar-button'),
                document.querySelector('[data-testid="stButton"] button[kind="primary"]')
            ];
            
            let targetElement = null;
            for (let target of targets) {
                if (target) {
                    targetElement = target;
                    console.log('Elemento encontrado:', target);
                    break;
                }
            }
            
            if (targetElement) {
                // Agregar highlighting
                const button = targetElement.querySelector('button') || targetElement;
                if (button) {
                    button.classList.add('highlight-finalizar');
                    setTimeout(() => {
                        button.classList.remove('highlight-finalizar');
                    }, 3000);
                }
                
                // Scroll suave
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
                
                console.log('Scroll ejecutado exitosamente');
            } else {
                // Fallback: scroll hacia el final de la página
                console.log('Usando fallback scroll');
                const scrollTarget = Math.max(0, document.body.scrollHeight - window.innerHeight - 200);
                window.scrollTo({
                    top: scrollTarget,
                    behavior: 'smooth'
                });
            }
        }
        
        // Ejecutar el scroll con múltiples intentos
        let attempts = 0;
        const maxAttempts = 10;
        
        function tryScroll() {
            attempts++;
            console.log('Intento de scroll:', attempts);
            
            if (document.getElementById('finalizar-venta-section') || attempts >= maxAttempts) {
                scrollToFinalizarVenta();
            } else {
                setTimeout(tryScroll, 200);
            }
        }
        
        // Iniciar después de que se renderice la página
        setTimeout(tryScroll, 300);
        
        </script>
        """, unsafe_allow_html=True)

# Agregar funciones auxiliares faltantes
def mostrar_mensaje_exito(mensaje_principal, mensaje_detalle):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); padding: 1.2rem; border-radius: 12px; text-align: center; color: #155724; font-size: 1.1rem; font-weight: 600; margin: 0.8rem 0; border: 2px solid #28a745;">
        ✅ {mensaje_principal}<br>
        {mensaje_detalle}
    </div>
    """, unsafe_allow_html=True)

def mostrar_mensaje_error(mensaje):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f8d7da 0%, #f1b0b7 100%); padding: 1.2rem; border-radius: 12px; text-align: center; color: #721c24; font-size: 1.1rem; font-weight: 600; margin: 0.8rem 0; border: 2px solid #dc3545;">
        ❌ {mensaje}
    </div>
    """, unsafe_allow_html=True)

def mostrar_mensaje_info(mensaje):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #cce7ff 0%, #b3d9ff 100%); padding: 1.2rem; border-radius: 12px; text-align: center; color: #004085; font-size: 1.1rem; font-weight: 600; margin: 0.8rem 0; border: 2px solid #007bff;">
        💡 {mensaje}
    </div>
    """, unsafe_allow_html=True)