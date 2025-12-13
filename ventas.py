import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time

# Importar sistema de autenticación centralizado
from auth_manager import verificar_sesion_admin, cerrar_sesion_admin, obtener_tiempo_restante, mostrar_formulario_login

# Importar gestor de sincronización
try:
    from sync_manager import get_sync_manager
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False
    print("sync_manager no disponible")

conn = sqlite3.connect("pos_cremeria.db", check_same_thread=False)
cursor = conn.cursor()

# Helper para reiniciar la ejecución de Streamlit de forma compatible con varias versiones
def safe_rerun():
    """Intentar reiniciar la app de Streamlit.

    Primero intenta usar `st.experimental_rerun()` si está disponible.
    Si no, intenta levantar la excepción interna RerunException que Streamlit utiliza.
    Si todo falla, marca un flag en session_state para una re-ejecución de respaldo.
    """
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        # si experimental_rerun existe pero falla, seguimos a intentar la excepción interna
        pass

    # Intentar importar y lanzar la excepción interna usada por Streamlit
    candidates = [
        "streamlit.runtime.scriptrunner.script_runner",
        "streamlit.runtime.scriptrunner",
        "streamlit.scriptrunner",
    ]
    for mod in candidates:
        try:
            m = __import__(mod, fromlist=["RerunException"])
            RerunException = getattr(m, "RerunException", None)
            if RerunException:
                raise RerunException()
        except Exception:
            continue

    # Fallback: pedir una re-ejecución en el siguiente ciclo (no inmediato)
    try:
        st.session_state['_request_rerun_fallback'] = True
    except Exception:
        pass


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
            box-shadow: 0 0 40px rgba(102, 126, 234, 1);
            transform: scale(1.02);
        }
    }
    
    /* ESTILO ESPECIAL PARA CAMPO DE CÓDIGO - SIEMPRE RESALTADO */
    input[aria-label="Código de Barras"],
    input[placeholder*="Escanea"] {
        border: 3px solid #00b894 !important;
        box-shadow: 0 0 15px rgba(0, 184, 148, 0.5) !important;
        background: #f0fff4 !important;
        font-size: 1.3rem !important;
        font-weight: bold !important;
        animation: pulse-ready 2s infinite;
    }
    
    @keyframes pulse-ready {
        0%, 100% {
            box-shadow: 0 0 15px rgba(0, 184, 148, 0.5);
            border-color: #00b894;
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
    Parsear tickets con múltiples productos de báscula.
    
    Formato por producto: 13 dígitos
    - Primeros 7 dígitos: código del producto (PLU báscula)
    - Siguiente 1 dígito: cantidad entera (unidades)
    - Últimos 5 dígitos: peso en formato especial (decagramos × 10)
    
    Ejemplos:
    - 2080332010005 → código 2080332, cantidad 0, peso 10005 → 1.0005 kg (aprox 1 unidad)
    - 2000072002559 → código 2000072, cantidad 0, peso 02559 → 0.2559 kg = 255.9g
    - 2000140018758 → código 2000140, cantidad 0, peso 18758 → 1.8758 kg = 1875.8g
    
    El peso se convierte: dividir entre 10000 para obtener kilogramos
    Ejemplo: 02559 / 10000 = 0.2559 kg
    
    Retorna: [(codigo_7_digitos, peso_en_gramos), ...]
    """
    if not codigo_completo or len(codigo_completo) < 13:
        return []
    if len(codigo_completo) % 13 != 0:
        return []
    
    productos = []
    num_productos = len(codigo_completo) // 13
    
    for i in range(num_productos):
        inicio = i * 13
        segmento = codigo_completo[inicio:inicio+13]
        
        # Extraer las partes según el formato real
        codigo_prod = segmento[0:7]      # 7 dígitos: código de producto
        cantidad_dig = segmento[7:8]     # 1 dígito: cantidad entera (usualmente 0 para granel)
        peso_str = segmento[8:13]        # 5 dígitos: peso en formato especial
        
        # Debug: imprimir qué se está extrayendo
        print(f"Producto {i+1}: segmento='{segmento}' → codigo='{codigo_prod}', cant='{cantidad_dig}', peso_str='{peso_str}'")
        
        try:
            # Convertir peso: dividir entre 10000 y multiplicar por 1000 para obtener gramos
            # Ejemplo: 02559 → 2559/10000 = 0.2559 kg = 255.9 g
            peso_int = int(peso_str)
            peso_gramos = (peso_int / 10000) * 1000  # Convertir a gramos
            productos.append((codigo_prod, int(peso_gramos)))
        except ValueError:
            print(f"  ⚠️ Error al parsear peso: '{peso_str}'")
            continue
    
    return productos

def obtener_producto_por_codigo(codigo):
    """
    Obtener información completa del producto por código.
    Maneja múltiples formatos de búsqueda:
    
    Formato de báscula: 2080332010005
      - Primeros 7 dígitos: código del producto (2080332)
        * Si comienza con "20": extraer últimos 5-6 dígitos como PLU
        * Ejemplo: 2000072 → PLU 72, 2000140 → PLU 140, 2080332 → PLU 80332
      - Siguientes 2 dígitos: cantidad (01)
      - Últimos 4 dígitos: peso en gramos (0005)
    
    Estrategias de búsqueda:
    1. Búsqueda exacta por código
    2. Búsqueda por número_producto (PLU)
    3. Extracción de PLU desde código de báscula (7 dígitos)
    4. Búsqueda en mapeo de báscula (tabla auxiliar)
    5. Búsqueda parcial con LIKE
    6. Búsqueda flexible para barcodes truncados
    """
    if not codigo:
        return None
    
    codigo_str = str(codigo).strip()
    
    # ESTRATEGIA 0A: Si el código tiene 7 dígitos y comienza con "20" (código de báscula)
    # Primero buscar en tabla de mapeo, luego intentar extraer PLU
    if len(codigo_str) == 7 and codigo_str.startswith('20') and codigo_str.isdigit():
        # PRIMERO: Buscar en mapeo (tiene prioridad)
        cursor.execute("""
            SELECT p.* FROM productos p
            JOIN bascula_mapeo bm ON p.codigo = bm.producto_codigo
            WHERE bm.codigo_bascula = ?
        """, (codigo_str,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado
        
        # SEGUNDO: Extraer PLU de los últimos dígitos
        # Ejemplos:
        # 2000072 → probar 72, 0072, 00072
        # 2000140 → probar 140, 0140, 00140
        # 2080332 → probar 80332, 0332, 332
        
        for longitud in [5, 4, 3, 2]:
            plu_str = codigo_str[-longitud:].lstrip('0') or '0'
            try:
                plu = int(plu_str)
                cursor.execute("SELECT * FROM productos WHERE numero_producto = ?", (plu,))
                resultado = cursor.fetchone()
                if resultado:
                    return resultado
            except ValueError:
                continue
    
    # ESTRATEGIA 0B: Si el código tiene 13 dígitos (ticket completo)
    if len(codigo_str) == 13 and codigo_str.isdigit():
        codigo_bascula = codigo_str[:7]
        # Usar la estrategia de 7 dígitos recursivamente
        return obtener_producto_por_codigo(codigo_bascula)
    
    # ESTRATEGIA 1: Búsqueda exacta por código
    cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo_str,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado
    
    # ESTRATEGIA 2: Si es un número, buscar por numero_producto (PLU)
    try:
        codigo_int = int(codigo_str)
        cursor.execute("SELECT * FROM productos WHERE numero_producto = ?", (codigo_int,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado
    except ValueError:
        pass
    
    # ESTRATEGIA 3: Si el código tiene 9 dígitos (código de báscula 9 dígitos),
    # buscar en tabla de mapeo
    if len(codigo_str) == 9 and codigo_str.isdigit():
        cursor.execute("""
            SELECT p.* FROM productos p
            JOIN bascula_mapeo bm ON p.codigo = bm.producto_codigo
            WHERE bm.codigo_bascula = ?
        """, (codigo_str,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado
        
        # Si no existe mapeo, intentar extracción de PLU
        ultimos_5 = codigo_str[-5:]
        ultimos_6 = codigo_str[-6:]
        ultimos_7 = codigo_str[-7:]
        
        for intento in [ultimos_7, ultimos_6, ultimos_5]:
            try:
                plu = int(intento)
                cursor.execute("SELECT * FROM productos WHERE numero_producto = ?", (plu,))
                resultado = cursor.fetchone()
                if resultado:
                    return resultado
            except ValueError:
                pass
        
        # Búsqueda LIKE para códigos de báscula
        cursor.execute("SELECT * FROM productos WHERE codigo LIKE ?", (f"{codigo_str}%",))
        resultado = cursor.fetchone()
        if resultado:
            return resultado
    
    # ESTRATEGIA 4: Si el código es largo (barcode), buscar por últimos dígitos
    if len(codigo_str) > 6:
        ultimos_6 = codigo_str[-6:]
        cursor.execute("SELECT * FROM productos WHERE codigo LIKE ?", (f"%{ultimos_6}",))
        resultado = cursor.fetchone()
        if resultado:
            return resultado
    
    return None

def obtener_precio_por_tipo(producto, tipo_cliente):
    """Obtiene el precio según el tipo de cliente para productos por unidad"""
    # Normalizar usando nombres de columna (más robusto que índices)
    cursor.execute("PRAGMA table_info(productos)")
    columnas = [col[1] for col in cursor.fetchall()]

    producto_dict = {}
    for i, valor in enumerate(producto):
        if i < len(columnas):
            producto_dict[columnas[i]] = valor

    precio_base = float(producto_dict.get('precio_normal', 0.0)) if producto_dict.get('precio_normal') else 0.0

    # Buscar columnas explícitas de mayoreo si existen
    def buscar_columna(*candidatos):
        for c in candidatos:
            if c in producto_dict and producto_dict[c] not in (None, ''):
                try:
                    return float(producto_dict[c])
                except Exception:
                    pass
        return None

    if tipo_cliente == "Normal":
        return precio_base
    elif tipo_cliente == "Mayoreo Tipo 1":
        encontrado = buscar_columna('precio_mayoreo_1', 'precio_mayoreo1', 'precio_mayoreo_tipo1', 'precio_mayoreo')
        return encontrado if encontrado is not None else round(precio_base * 0.95, 2)
    elif tipo_cliente == "Mayoreo Tipo 2":
        encontrado = buscar_columna('precio_mayoreo_2', 'precio_mayoreo2')
        return encontrado if encontrado is not None else round(precio_base * 0.90, 2)
    elif tipo_cliente == "Mayoreo Tipo 3":
        encontrado = buscar_columna('precio_mayoreo_3', 'precio_mayoreo3')
        return encontrado if encontrado is not None else round(precio_base * 0.85, 2)
    else:
        return precio_base

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

def obtener_creditos_vencidos():
    """Obtener SOLO créditos que ya han vencido (fecha_vencimiento + hora_vencimiento < ahora)"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
        FROM creditos_pendientes 
        WHERE pagado = 0 AND (
            fecha_vencimiento < ? 
            OR (fecha_vencimiento = ? AND hora_vencimiento < ?)
        )
        ORDER BY fecha_vencimiento, hora_vencimiento
    ''', (fecha_hoy, fecha_hoy, hora_actual))
    return cursor.fetchall()

def obtener_creditos_por_vencer():
    """Obtener créditos que vencen en menos de 1 hora (entre ahora y ahora + 1 hora)"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    # Sumar 1 hora
    una_hora_despues = (ahora + timedelta(hours=1)).strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
        FROM creditos_pendientes 
        WHERE pagado = 0 AND fecha_vencimiento = ? 
            AND hora_vencimiento > ? AND hora_vencimiento <= ?
        ORDER BY hora_vencimiento
    ''', (fecha_hoy, hora_actual, una_hora_despues))
    return cursor.fetchall()

def obtener_alertas_pendientes():
    """Obtener créditos que necesitan alerta pero no se ha mostrado (VENCIDOS)"""
    vencidos = obtener_creditos_vencidos()
    # Filtrar por alerta_mostrada = 0
    return [c for c in vencidos if c[5] == 0]  # El índice 5 es alerta_mostrada

def marcar_alerta_mostrada(credito_id):
    """Marcar que la alerta ya fue mostrada"""
    cursor.execute("UPDATE creditos_pendientes SET alerta_mostrada = 1 WHERE id = ?", (credito_id,))
    conn.commit()

def marcar_credito_pagado(credito_id):
    """Marcar un crédito como pagado"""
    cursor.execute("UPDATE creditos_pendientes SET pagado = 1 WHERE id = ?", (credito_id,))
    conn.commit()

def mostrar_popup_alertas_mejorado():
    """Mostrar alertas emergentes para créditos vencidos Y créditos por vencer en 1 hora"""
    
    # 🔴 ALERTAS DE CRÉDITOS VENCIDOS (MÁXIMA PRIORIDAD)
    alertas_vencidas = obtener_alertas_pendientes()
    
    if alertas_vencidas:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); 
                    padding: 1.5rem; border-radius: 15px; border-left: 6px solid #c92a2a; 
                    margin: 1rem 0; box-shadow: 0 4px 15px rgba(255,107,107,0.3);">
            <h2 style="color: white; margin: 0; font-size: 1.5rem; text-align: center;">
                🐄🚨 ¡ALERTA CRÍTICA: CRÉDITOS VENCIDOS! 🚨🐄
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas_vencidas:
            cliente, monto, fecha_venc, hora_venc, credito_id, alerta_mostrada = alerta
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.error(f"⏰ **VENCIDO:** {cliente} debe {formatear_moneda(monto)}\n"
                        f"Desde: {fecha_venc} a las {hora_venc}")
            with col2:
                if st.button("✅ PAGADO", key=f"pagar_vencido_{credito_id}", type="primary"):
                    marcar_credito_pagado(credito_id)
                    st.balloons()
                    st.success(f"✅ Crédito de {cliente} marcado como pagado")
                    st.rerun()
            with col3:
                if st.button("⏰ DESPUÉS", key=f"recordar_vencido_{credito_id}"):
                    marcar_alerta_mostrada(credito_id)
                    st.info("Recordatorio desactivado hasta mañana")
                    st.rerun()
        st.markdown("---")
    
    # 🟡 ALERTAS DE CRÉDITOS POR VENCER EN 1 HORA (PRIORIDAD MEDIA)
    alertas_pronto = obtener_creditos_por_vencer()
    
    if alertas_pronto:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffd93d 0%, #ffb700 100%); 
                    padding: 1.5rem; border-radius: 15px; border-left: 6px solid #ff9c00; 
                    margin: 1rem 0; box-shadow: 0 4px 15px rgba(255,193,7,0.3);">
            <h2 style="color: #1a1a1a; margin: 0; font-size: 1.5rem; text-align: center;">
                ⚠️  RECORDATORIO: CRÉDITOS VENCEN EN MENOS DE 1 HORA ⚠️
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas_pronto:
            cliente, monto, fecha_venc, hora_venc, credito_id, alerta_mostrada = alerta
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.warning(f"🕐 **POR VENCER:** {cliente} debe {formatear_moneda(monto)}\n"
                          f"Vence: HOY a las {hora_venc}")
            with col2:
                if st.button("✅ PAGADO", key=f"pagar_pronto_{credito_id}", type="primary"):
                    marcar_credito_pagado(credito_id)
                    st.balloons()
                    st.success(f"✅ Crédito de {cliente} marcado como pagado")
                    st.rerun()
            with col3:
                if st.button("📝 OK", key=f"ok_pronto_{credito_id}"):
                    marcar_alerta_mostrada(credito_id)
                    st.info("Recordatorio visto")
                    st.rerun()
        st.markdown("---")

def mostrar():
    # Aplicar estilos personalizados
    aplicar_estilos_custom()
    
    # SCRIPT GLOBAL PARA MANTENER FOCUS EN CAMPO DE CÓDIGO
    components.html(
        """
        <script>
        (function() {
            let focusInterval;
            let clickHandlerAdded = false;
            
            function enfocarCampoCodigo() {
                const doc = window.parent.document;
                const input = doc.querySelector('input[aria-label="Código de Barras"]') || 
                             doc.querySelector('input[placeholder*="ESCANEA"]') ||
                             doc.querySelectorAll('input[type="text"]')[0];
                
                if (input && document.activeElement !== input) {
                    input.focus();
                    return true;
                }
                return false;
            }
            
            function agregarClickHandler() {
                if (clickHandlerAdded) return;
                
                const doc = window.parent.document;
                const paso1 = doc.getElementById('paso1-seccion');
                
                if (paso1) {
                    paso1.addEventListener('click', enfocarCampoCodigo);
                    doc.addEventListener('click', function(e) {
                        // No enfocar si se está interactuando con la sección de ventas de hoy
                        if (e.target.closest('[data-testid="stSelectbox"]')) return;
                        if (e.target.closest('button')) return;
                        
                        // Si el click no es en un input, select o button, enfocar el campo de código
                        if (!e.target.matches('input, select, button, textarea, a')) {
                            enfocarCampoCodigo();
                        }
                    });
                    clickHandlerAdded = true;
                }
            }
            
            // Intentar enfocar cada 100ms durante los primeros 3 segundos
            focusInterval = setInterval(() => {
                // No enfocar si hay un selectbox abierto o activo
                const doc = window.parent.document;
                const selectActivo = doc.querySelector('[data-testid="stSelectbox"] input:focus');
                if (!selectActivo && enfocarCampoCodigo()) {
                    agregarClickHandler();
                }
            }, 100);
            
            setTimeout(() => {
                clearInterval(focusInterval);
                agregarClickHandler();
                enfocarCampoCodigo();
            }, 3000);
            
            // También enfocar cuando la página se vuelve visible
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) {
                    setTimeout(enfocarCampoCodigo, 100);
                }
            });
        })();
        </script>
        """,
        height=0
    )
    
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
    
    # Mostrar mensaje de éxito si se finalizó una venta
    if st.session_state.get('mostrar_mensaje_exito', False):
        total_venta = st.session_state.get('total_venta', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 2rem; border-radius: 25px; text-align: center; color: white; font-size: 2rem; font-weight: bold; margin: 2rem 0; box-shadow: 0 15px 50px rgba(0,184,148,0.4); animation: slideIn 0.5s ease-out;">
            🎉 ¡VENTA REGISTRADA EXITOSAMENTE! 🎉<br>
            <div style="font-size: 1.5rem; margin-top: 1rem;">
                💰 Total: {formatear_moneda(total_venta)}
            </div>
        </div>
        <style>
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
        """, unsafe_allow_html=True)
        st.balloons()
        
        # Limpiar el flag después de mostrar
        st.session_state['mostrar_mensaje_exito'] = False
        if 'total_venta' in st.session_state:
            del st.session_state['total_venta']
    
    # Mostrar estado actual del carrito y botón para vaciarlo
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []
    
    num_items_carrito = len(st.session_state.carrito)
    
    col_titulo, col_boton = st.columns([3, 1])
    with col_titulo:
        st.markdown(f"""
        <div id="paso1-seccion" style="background: linear-gradient(135deg, #83b300 0%, #00a085 100%); padding: .5rem; border-radius: 16px; margin: 0.8rem 0;">
            <h2 style="color: white; text-align: center; margin-bottom: 0.8rem; font-size: 1.6rem;">
                📦 PASO 1: AGREGAR PRODUCTOS 
                <span style="background: rgba(255,255,255,0.3); padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 1.2rem;">
                    🛒 {num_items_carrito}
                </span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col_boton:
        if num_items_carrito > 0:
            if st.button("🗑️ Vaciar Carrito", use_container_width=True, type="secondary"):
                st.session_state.carrito = []
                st.session_state['ultimo_ticket_procesado'] = ''
                st.session_state['codigos_ya_agregados_ticket'] = set()
                st.rerun()
    
    col_codigo, col_cantidad = st.columns([2, 1])
    
    # Inicializar contador para forzar recreación del widget
    if 'codigo_widget_counter' not in st.session_state:
        st.session_state.codigo_widget_counter = 0
    
    with col_codigo:
        st.markdown("#### 🔍 Código de Barras")
        
        # Sistema de limpieza mejorado: usar un key dinámico para forzar recreación
        if st.session_state.get('limpiar_codigo', False):
            st.session_state.codigo_widget_counter += 1
            st.session_state['limpiar_codigo'] = False
        
        # Usar key dinámico que cambia cuando se limpia
        widget_key = f"codigo_input_{st.session_state.codigo_widget_counter}"
        
        # Indicador visual de que el campo está listo
        st.markdown("""
        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); 
                    padding: 0.3rem 1rem; 
                    border-radius: 8px; 
                    text-align: center; 
                    color: white; 
                    font-size: 0.9rem; 
                    font-weight: bold; 
                    margin-bottom: 0.5rem;
                    animation: blink 1.5s infinite;">
            ✨ LISTO PARA ESCANEAR ✨
        </div>
        <style>
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        codigo = st.text_input(
            "Código de Barras",
            value="",
            placeholder="👉 ESCANEA AQUÍ o ingresa código",
            label_visibility="collapsed",
            key=widget_key,
            help="Campo activo - Escanea directamente aquí"
        )
        
        # ACUMULADOR DE TICKETS: Si llega un código de 13 dígitos, acumular
        # ESTRATEGIA FINAL: Capturar múltiplos de 13 dígitos y procesar con timeout simple
        if codigo and codigo.isdigit() and len(codigo) >= 13 and len(codigo) % 13 == 0:
            import time
            tiempo_actual = time.time()
            
            num_productos = len(codigo) // 13
            print(f"\n🎫 TICKET RECIBIDO: {len(codigo)} dígitos, {num_productos} producto(s)")
            print(f"   Código: {codigo}")
            
            # Obtener estado del buffer
            buffer_ticket = st.session_state.get('buffer_ticket', '')
            ultimo_tiempo = st.session_state.get('buffer_ticket_tiempo', 0)
            intentos_espera = st.session_state.get('buffer_intentos_espera', 0)
            
            # Si este código es diferente o más largo que el buffer, actualizarlo
            if not buffer_ticket or codigo != buffer_ticket:
                if len(codigo) > len(buffer_ticket):
                    print(f"   ✅ Actualizando buffer (ticket más completo)")
                    st.session_state['buffer_ticket'] = codigo
                    st.session_state['buffer_ticket_tiempo'] = tiempo_actual
                    st.session_state['buffer_intentos_espera'] = 0
                    st.info(f"📊 {num_productos} producto(s) detectado(s) - Esperando más bloques...")
                    codigo = ""
                    time.sleep(0.5)
                    st.rerun()
                else:
                    print(f"   ℹ️ Buffer ya tiene ticket más completo, ignorando")
                    codigo = ""
            else:
                # El buffer no ha cambiado, incrementar contador de espera
                intentos_espera += 1
                st.session_state['buffer_intentos_espera'] = intentos_espera
                print(f"   ⏳ Buffer sin cambios, intento {intentos_espera}/4")
                
                # Después de 4 intentos sin cambios (4 × 0.5s = 2s), procesar
                if intentos_espera >= 4:
                    print(f"   ✅ PROCESANDO: {len(buffer_ticket)} dígitos, {len(buffer_ticket)//13} productos")
                    codigo = buffer_ticket
                    st.success(f"✅ Procesando {len(codigo)//13} producto(s)")
                    # Limpiar todo
                    st.session_state['buffer_ticket'] = ''
                    st.session_state['buffer_ticket_tiempo'] = 0
                    st.session_state['buffer_intentos_espera'] = 0
                else:
                    # Seguir esperando
                    st.info(f"📊 {num_productos} producto(s) - Verificando bloques adicionales ({intentos_espera}/4)...")
                    codigo = ""
                    time.sleep(0.5)
                    st.rerun()
                
        elif codigo:
            # No es un código válido de ticket
            st.session_state['buffer_ticket'] = ''
            st.session_state['buffer_ticket_tiempo'] = 0
            st.session_state['buffer_intentos_espera'] = 0
    
    # INYECTAR AUTOFOCUS Y DEBOUNCE PARA CAPTURAR ESCÁNER COMPLETO
    components.html(
        """
        <script>
        const interval = setInterval(() => {
            const parentDoc = window.parent.document;
            const input = parentDoc.querySelector('input[aria-label="Código de Barras"]') || 
                         parentDoc.querySelector('input[placeholder*="ESCANEA"]');
            
            if (input && !input.hasAttribute('data-scanner-ready')) {
                input.setAttribute('autofocus', 'autofocus');
                input.setAttribute('data-scanner-ready', 'true');
                input.focus();
                input.click();
                
                // Deshabilitar el auto-submit de Streamlit temporalmente
                // para que el escáner pueda enviar todos los dígitos
                let typingTimer;
                const doneTypingInterval = 200; // 200ms después de la última tecla
                
                input.addEventListener('input', function(e) {
                    clearTimeout(typingTimer);
                    typingTimer = setTimeout(() => {
                        // Después de 200ms sin input, enviar el formulario
                        const enterEvent = new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            bubbles: true
                        });
                        input.dispatchEvent(enterEvent);
                    }, doneTypingInterval);
                });
                
                clearInterval(interval);
            }
        }, 50);
        
        // Limpiar después de 3 segundos
        setTimeout(() => clearInterval(interval), 3000);
        </script>
        """,
        height=0
    )
    
    # DETECCIÓN DE TICKETS
    es_ticket = False
    productos_ticket = []
    
    if codigo and len(codigo) >= 13 and len(codigo) % 13 == 0:
        es_ticket = True
        productos_ticket = parsear_codigo_bascula(codigo)
        
        # Los escáneres modernos envían todos los datos de una vez
        # Procesar inmediatamente sin esperas
        
        if productos_ticket:
            num_productos = len(productos_ticket)
            emoji_cantidad = "📦" if num_productos <= 5 else "📦📦" if num_productos <= 10 else "📦📦📦"
            mensaje_cantidad = f"{num_productos} producto{'s' if num_productos != 1 else ''}"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); padding: 1.5rem; border-radius: 15px; margin: 1rem 0; color: white; text-align: center;">
                <div style="font-size: 1.6rem; font-weight: bold;">🎫 TICKET DETECTADO</div>
                <div style="font-size: 1.2rem; margin-top: 0.5rem;">{emoji_cantidad} {mensaje_cantidad}</div>
                <div style="font-size: 0.9rem; margin-top: 0.3rem; opacity: 0.9;">{len(codigo)} dígitos escaneados</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Procesar automáticamente solo UNA VEZ - VALIDACIÓN ESTRICTA
            ultimo = st.session_state.get('ultimo_ticket_procesado', '')
            print(f"DEBUG: Verificando ticket - ultimo={ultimo}, codigo={codigo}, son iguales={ultimo==codigo}")
            
            # IMPORTANTE: Validar si este ticket ya fue procesado O es sub-ticket de uno ya procesado
            # Caso 1: Ticket idéntico
            ticket_ya_procesado = (ultimo == codigo)
            
            # Caso 2: Ticket actual es parte de uno ya procesado (ticket parcial repetido)
            if not ticket_ya_procesado and ultimo and len(ultimo) > len(codigo):
                ticket_ya_procesado = ultimo.startswith(codigo)
                if ticket_ya_procesado:
                    print(f"⚠️ TICKET PARCIAL DETECTADO - Este ticket es parte de uno ya procesado")
            
            # Caso 3: Ticket actual CONTIENE uno ya procesado (ticket completo después de uno parcial)
            if not ticket_ya_procesado and ultimo and len(codigo) > len(ultimo):
                ticket_ya_procesado = codigo.startswith(ultimo)
                if ticket_ya_procesado:
                    print(f"⚠️ TICKET EXTENDIDO DETECTADO - Ya procesamos la versión parcial de este ticket")
            
            if ticket_ya_procesado:
                print(f"⚠️ TICKET YA PROCESADO - Saltando completamente")
                st.info("✅ Ticket ya procesado anteriormente")
                # Limpiar el campo y no hacer nada más
                st.session_state['limpiar_codigo'] = True
                codigo = ""  # Limpiar para evitar re-procesar
                # NO HACER st.rerun() aquí para evitar loops infinitos
            else:
                print(f"✨ ENTRANDO AL BLOQUE DE PROCESAMIENTO - Primera vez para este ticket")
                # Marcar como procesado INMEDIATAMENTE ANTES de hacer cualquier cosa
                st.session_state['ultimo_ticket_procesado'] = codigo
                
                # Asegurar que el carrito existe
                if 'carrito' not in st.session_state:
                    st.session_state.carrito = []

                # IMPORTANTE: Contar productos en carrito ANTES de procesar
                productos_antes = len(st.session_state.carrito)
                print(f"📊 CARRITO ANTES DE PROCESAR: {productos_antes} productos")
                
                # DEBUG: Mostrar QUÉ productos hay en el carrito
                if productos_antes > 0:
                    print(f"🔍 PRODUCTOS EN CARRITO ANTES DE PROCESAR:")
                    for i, item in enumerate(st.session_state.carrito, 1):
                        print(f"   {i}. {item.get('nombre', 'SIN NOMBRE')} - Código: {item.get('codigo', 'N/A')}")

                # Debug: guardar códigos parseados en session_state para verlos después
                st.session_state['debug_ticket'] = [(c, v) for c, v in productos_ticket]

                agregados = 0
                no_encontrados = []
                
                # Limpiar set de duplicados para este nuevo ticket
                st.session_state['codigos_ya_agregados_ticket'] = set()
                codigos_ya_agregados = st.session_state['codigos_ya_agregados_ticket']

                print(f"\n{'='*60}")
                print(f"INICIANDO PROCESAMIENTO DE {len(productos_ticket)} PRODUCTOS")
                print(f"{'='*60}")
                
                for idx, (codigo_prod, valor) in enumerate(productos_ticket, 1):
                    print(f"\n{'─'*60}")
                    print(f"PROCESANDO PRODUCTO {idx} DE {len(productos_ticket)}")
                    print(f"{'─'*60}")
                    # Intentar buscar con código de diferentes longitudes
                    prod = None
                    codigo_real_encontrado = None
                    
                    print(f"\n🔍 Buscando producto con código: {codigo_prod}, valor: {valor}")
                    
                    for longitud in [9, 8, 7, 6, 5]:
                        codigo_intento = codigo_prod[:longitud]
                        print(f"  Intentando con longitud {longitud}: {codigo_intento}")
                        prod = obtener_producto_por_codigo(codigo_intento)
                        if prod:
                            info = obtener_informacion_producto(prod)
                            codigo_real_encontrado = info['codigo']
                            print(f"  ✅ Encontrado: {info['nombre']} (tipo: {info['tipo_venta']}, stock_kg: {info['stock_kg']})")
                            break
                        else:
                            print(f"  ❌ No encontrado con longitud {longitud}")
                    
                    # Verificar si ya agregamos este producto (por código real)
                    if codigo_real_encontrado and codigo_real_encontrado in codigos_ya_agregados:
                        print(f"⚠️ DUPLICADO DETECTADO: {codigo_real_encontrado} - saltando...")
                        continue
                    
                    if prod:
                        # Marcar como agregado ANTES de procesarlo
                        codigos_ya_agregados.add(codigo_real_encontrado)
                        print(f"✓ Procesando: {info['nombre']} (tipo: {info['tipo_venta']})")

                        if info['tipo_venta'] in ['granel', 'kg']:
                            peso_kg = valor / 1000.0
                            print(f"  📦 Producto a granel: {peso_kg:.3f} kg")
                            precio_kg = obtener_precio_granel_por_tipo(prod, "Normal")
                            print(f"  💰 Precio por kg: ${precio_kg}")
                            total = precio_kg * peso_kg
                            print(f"  💵 Total: ${total:.2f}")
                            print(f"  📊 Stock disponible: {info['stock_kg']:.3f} kg")
                            if info['stock_kg'] >= peso_kg:
                                print(f"  ✅ HAY STOCK - Agregando al carrito")
                            else:
                                print(f"  ❌ SIN STOCK SUFICIENTE ({info['stock_kg']:.3f} < {peso_kg:.3f})")
                            if info['stock_kg'] >= peso_kg:
                                item = {
                                    'codigo': info['codigo'],
                                    'nombre': f"{info['nombre']} ({peso_kg:.3f} Kg)",
                                    'cantidad': 1,
                                    'peso': peso_kg,
                                    'precio_unitario': precio_kg,
                                    'total': total,
                                    'tipo_venta': info['tipo_venta']
                                }
                                st.session_state.carrito.append(item)
                                print(f"  🛒 AGREGADO AL CARRITO")
                                agregados += 1
                        else:
                            print(f"  📦 Producto por unidad")
                            # Calcular cantidad
                            cant = valor // 100
                            if valor % 1000 == 0 and (valor // 1000) > 0:
                                cant = valor // 1000
                            if cant == 0:
                                cant = 1

                            precio = obtener_precio_por_tipo(prod, "Normal")
                            total = precio * cant
                            if info['stock'] >= cant:
                                item = {
                                    'codigo': info['codigo'],
                                    'nombre': info['nombre'],
                                    'cantidad': cant,
                                    'peso': 0,
                                    'precio_unitario': precio,
                                    'total': total,
                                    'tipo_venta': 'unidad'
                                }
                                st.session_state.carrito.append(item)
                                print(f"  🛒 AGREGADO AL CARRITO")
                                agregados += 1
                    else:
                        print(f"  ❌ PRODUCTO NO ENCONTRADO: {codigo_prod}")
                        no_encontrados.append(codigo_prod)
                
                print(f"\n{'='*60}")
                print(f"FIN DEL LOOP - Procesados {len(productos_ticket)} productos")
                print(f"Agregados al carrito: {agregados}")
                print(f"No encontrados: {len(no_encontrados)}")
                
                # VERIFICAR: ¿Cuántos productos hay ahora en el carrito?
                productos_despues = len(st.session_state.carrito)
                print(f"📊 CARRITO DESPUÉS DE PROCESAR: {productos_despues} productos")
                print(f"📊 DIFERENCIA: {productos_despues - productos_antes} productos agregados")
                
                # DEBUG: Mostrar TODOS los productos finales
                print(f"🔍 PRODUCTOS FINALES EN CARRITO:")
                for i, item in enumerate(st.session_state.carrito, 1):
                    print(f"   {i}. {item.get('nombre', 'SIN NOMBRE')} - Código: {item.get('codigo', 'N/A')}")
                print(f"{'='*60}\n")

                # Mostrar resultados del procesamiento con más detalle
                if agregados > 0:
                    st.success(f"✅ {agregados} producto(s) agregado(s) → Total en carrito: {productos_despues} productos")
                if no_encontrados:
                    st.warning(f"⚠️ No encontrados: {', '.join(no_encontrados)}")
                
                # Limpiar el código de entrada completamente AL FINAL
                st.session_state['limpiar_codigo'] = True
                # Hacer rerun para limpiar el campo visualmente DESPUÉS de procesar todo
                st.rerun()
    
    # Verificar si el producto existe y obtener información (SOLO si NO es ticket)
    # Si es un ticket, NO mostrar ningún mensaje de producto individual
    producto_info = None
    info_producto = None
    
    if not es_ticket:
        if codigo:
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
        elif codigo and len(codigo) > 3:
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
    # Si no hay código ingresado, mostrar listado de ventas realizadas hoy
    elif not codigo:
        try:
            # Agrupar por venta (mismo timestamp 'fecha' para la misma venta) y obtener un número de venta mínimo
            cursor.execute(
                """
                SELECT
                    MIN(id) as venta_num,
                    datetime(fecha, 'localtime') as fecha_local,
                    SUM(total) as total_venta,
                    COUNT(*) as items
                FROM ventas
                WHERE date(fecha, 'localtime') = date('now', 'localtime')
                GROUP BY fecha_local
                ORDER BY fecha_local DESC
                """
            )
            ventas_hoy = cursor.fetchall()
        except Exception:
            ventas_hoy = []

        st.markdown("""
        <div style="background: linear-gradient(135deg, #0984e3 0%, #74b9ff 100%); padding: .6rem; border-radius: 12px; margin: 0.8rem 0; color: white;">
            <h3 style="margin:0;">🧾 Ventas de hoy</h3>
            <div style="font-size:0.9rem; opacity:0.9;">Listado de ventas con fecha, hora y monto</div>
        </div>
        """, unsafe_allow_html=True)

        if ventas_hoy:
            # Preparar DataFrame agrupado por venta: venta_num, fecha_local, total_venta
            df = pd.DataFrame(ventas_hoy, columns=["venta_num", "fecha_local", "total_venta", "items"]) 
            def split_fecha_hora(fecha_str):
                try:
                    if isinstance(fecha_str, str) and ' ' in fecha_str:
                        fecha_part, hora_part = fecha_str.split(' ', 1)
                        return fecha_part, hora_part
                    return fecha_str, ''
                except Exception:
                    return fecha_str, ''

            df[["Fecha", "Hora"]] = df["fecha_local"].apply(lambda f: pd.Series(split_fecha_hora(f)))
            df_display = df[["venta_num", "Fecha", "Hora", "total_venta"]].copy()
            df_display = df_display.rename(columns={"venta_num": "Venta", "total_venta": "Total"})
            # Marcar cada fila como 1 venta (según requerimiento)
            df_display["Ventas"] = 1
            # Reordenar columnas
            df_display = df_display[["Venta", "Fecha", "Hora", "Total", "Ventas"]]
            st.dataframe(df_display.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No se registraron ventas hoy.")
    
    with col_cantidad:
        if info_producto:
            if info_producto.get('tipo_venta') in ['granel', 'kg']:
                st.markdown("#### ⚖️ Peso (Kg)")
                peso = st.number_input(
                    "Peso en Kilogramos",
                    min_value=0.050,
                    value=0.500,
                    step=0.050,
                    format="%.3f",
                    label_visibility="collapsed",
                )
                cantidad = 1

                # Información del producto a granel
                st.markdown(
                    f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; color: white; text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: bold;">⚖️ PRODUCTO A GRANEL</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                col_info_granel = st.columns(2)
                with col_info_granel[0]:
                    st.markdown(
                        f"""
                    <div style="background: #e3f2fd; padding: 0.8rem; border-radius: 8px; text-align: center; color: #1565c0; font-weight: bold;">
                        📊 STOCK<br><span style="font-size: 1.3rem;">{info_producto['stock_kg']:.3f} Kg</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with col_info_granel[1]:
                    st.markdown(
                        f"""
                    <div style="background: #e8f5e8; padding: 0.8rem; border-radius: 8px; text-align: center; color: #2e7d32; font-weight: bold;">
                        💰 PRECIO<br><span style="font-size: 1.3rem;">{formatear_moneda(info_producto['precio_por_kg'])}/Kg</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("#### 📊 Cantidad")
                cantidad = st.number_input(
                    "Cantidad de productos",
                    min_value=1,
                    value=1,
                    step=1,
                    label_visibility="collapsed",
                )
                peso = 0

                # Información del producto por unidad
                st.markdown(
                    f"""
                <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; color: white; text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: bold;">🏷️ PRODUCTO POR UNIDAD</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                col_info_unidad = st.columns(2)
                with col_info_unidad[0]:
                    st.markdown(
                        f"""
                    <div style="background: #e3f2fd; padding: 0.8rem; border-radius: 8px; text-align: center; color: #1565c0; font-weight: bold;">
                        📊 STOCK<br><span style="font-size: 1.3rem;">{info_producto['stock']} unidades</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with col_info_unidad[1]:
                    st.markdown(
                        f"""
                    <div style="background: #e8f5e8; padding: 0.8rem; border-radius: 8px; text-align: center; color: #2e7d32; font-weight: bold;">
                        💰 PRECIO<br><span style="font-size: 1.3rem;">{formatear_moneda(info_producto['precio_normal'])}/unidad</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown("#### 📊 Cantidad")
            cantidad = st.number_input(
                "Cantidad de productos",
                min_value=1,
                value=1,
                step=1,
                label_visibility="collapsed",
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
                if info_producto['tipo_venta'] in ['granel', 'kg']:
                    if info_producto['stock_kg'] >= peso:
                        precio_kg = obtener_precio_granel_por_tipo(producto_info, cliente_tipo_inicial)
                        total = precio_kg * peso
                        
                        precio_original = info_producto['precio_por_kg']
                        descuento_info = ""
                        if cliente_tipo_inicial != "Normal" and precio_kg < precio_original:
                            descuento_pct = ((precio_original - precio_kg) / precio_original * 100)
                            descuento_info = f" (Desc. {descuento_pct:.0f}%)"
                        
                        item = {
                            'codigo': info_producto['codigo'],
                            'nombre': f"{info_producto['nombre']} ({peso:.3f} Kg){descuento_info}",
                            'cantidad': cantidad,
                            'peso': peso,
                            'precio_unitario': precio_kg,
                            'total': total,
                            'tipo_venta': 'granel'
                        }
                        st.info(f"DEBUG append(manual-granel): {item}")
                        st.session_state.carrito.append(item)
                        
                        # Limpiar campos de entrada
                        st.session_state['limpiar_codigo'] = True
                        
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
                        
                        item = {
                            'codigo': info_producto['codigo'],
                            'nombre': f"{info_producto['nombre']}{descuento_info}",
                            'cantidad': cantidad,
                            'peso': 0,
                            'precio_unitario': precio,
                            'total': total,
                            'tipo_venta': 'unidad'
                        }
                        st.info(f"DEBUG append(manual-unidad): {item}")
                        st.session_state.carrito.append(item)
                        
                        # Limpiar campos de entrada
                        st.session_state['limpiar_codigo'] = True
                        
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
        
        # Ocultar debug de ticket en producción
        # (Si se requiere, habilitar bajo un flag de desarrollo)
        
        st.markdown("""        
        <div style="background: linear-gradient(135deg, #a8d5ba 0%, #90c695 100%); padding: 0.6rem; border-radius: 12px; margin: 0.6rem 0; border: 1px solid #7eb693;">
            <h2 style="color: #1e3a28; text-align: center; margin: 0; font-size: 1.3rem;">🛒 CARRITO DE COMPRAS</h2>
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
            if item['tipo_venta'] in ['granel', 'kg']:
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
                # Solo permitir edición para productos por unidad (no granel)
                if item['tipo_venta'] not in ['granel', 'kg']:
                    if st.button("✏️", key=f"editar_{i}", help="Editar cantidad", type="secondary"):
                        st.session_state[f'editando_{i}'] = True
                        st.rerun()
            
            # Sistema de edición mejorado
            if st.session_state.get(f'editando_{i}', False):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #d63031;">
                    <h4 style="color: white; margin-bottom: 1rem;">✏️ Editando: {item['nombre']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Obtener stock actual del producto
                producto_actual = obtener_producto_por_codigo(item['codigo'])
                stock_disponible = 0
                stock_kg_disponible = 0.0
                tiene_stock_suficiente = True
                
                if producto_actual:
                    info_prod = obtener_informacion_producto(producto_actual)
                    stock_disponible = info_prod['stock']
                    stock_kg_disponible = info_prod['stock_kg']
                
                col_edit1, col_edit2, col_edit3, col_edit4 = st.columns([2, 1, 1, 1])
                
                with col_edit1:
                    st.info(f"**Producto:** {item['nombre']}")
                    st.info(f"**Código:** {item['codigo']}")
                    
                    # Mostrar stock disponible según tipo de venta (soporta 'granel' o 'kg')
                    if item['tipo_venta'] in ['granel', 'kg']:
                        if stock_kg_disponible > 0:
                            st.success(f"📦 **Stock disponible:** {stock_kg_disponible:.3f} Kg")
                        else:
                            st.error(f"⚠️ **Stock disponible:** {stock_kg_disponible:.3f} Kg")
                    else:
                        if stock_disponible > 0:
                            st.success(f"📦 **Stock disponible:** {stock_disponible} unidades")
                        else:
                            st.error(f"⚠️ **Stock disponible:** {stock_disponible} unidades")
                
                with col_edit2:
                    if item['tipo_venta'] in ['granel', 'kg']:
                        nuevo_peso = st.number_input(
                            "**Nuevo peso (Kg):**", 
                            min_value=0.050, 
                            value=float(item['peso']), 
                            step=0.050, 
                            format="%.3f",
                            key=f"edit_peso_{i}"
                        )
                        # Validar stock
                        if nuevo_peso > stock_kg_disponible:
                            tiene_stock_suficiente = False
                            st.error(f"⚠️ Excede stock: {stock_kg_disponible:.3f} Kg")
                    else:
                        nueva_cantidad = st.number_input(
                            "**Nueva cantidad:**", 
                            min_value=1, 
                            value=int(item['cantidad']), 
                            step=1,
                            key=f"edit_cantidad_{i}"
                        )
                        # Validar stock
                        if nueva_cantidad > stock_disponible:
                            tiene_stock_suficiente = False
                            st.error(f"⚠️ Excede stock: {stock_disponible} unid.")
                
                with col_edit3:
                    st.markdown("**Precio unitario:**")
                    if item['tipo_venta'] in ['granel', 'kg']:
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
                        # Deshabilitar botón si no hay stock suficiente
                        if st.button("✅ Guardar", key=f"guardar_{i}", type="primary", disabled=not tiene_stock_suficiente):
                            if item['tipo_venta'] in ['granel', 'kg']:
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
                
                # Mensaje adicional si no hay stock suficiente
                if not tiene_stock_suficiente:
                    st.warning("⚠️ **No puedes guardar:** La cantidad solicitada excede el stock disponible.")
                
                st.markdown("---")
        
        # Resumen del carrito con mejor diseño
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); padding: 0.6rem; border-radius: 10px; margin: 0.8rem 0; color: white;">
            <h3 style="text-align: center; margin: 0; color: #ddd; font-size: 1.1rem;">📊 RESUMEN DEL CARRITO</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Calcular total
        total_general = sum(item['total'] for item in st.session_state.carrito)
        
        # Mostrar total destacado
        st.markdown(f"""
        <div class="total-destacado" style="padding: 0.5rem; font-size: 1.1rem;">
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
            productos_granel = len([item for item in st.session_state.carrito if item['tipo_venta'] in ['granel', 'kg']])
            peso_total = sum([item['peso'] for item in st.session_state.carrito if item['tipo_venta'] in ['granel', 'kg']])
            mostrar_metrica_mejorada(f"A Granel\n{peso_total:.3f} Kg", productos_granel, "⚖️", False)
        
        with col_metricas[2]:
            total_productos = len(st.session_state.carrito)
            mostrar_metrica_mejorada("Total Productos", total_productos, "📦", False)
        
        with col_metricas[3]:
            mostrar_metrica_mejorada("TOTAL A PAGAR", total_general, "💰", True)
        
        # Configuración de venta - DESPUÉS de agregar productos (mejor disposición visual)
        st.markdown("---")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2eb8b8 0%, #0984e3 100%); padding: 1rem; border-radius: 12px; margin: 0.6rem 0;">
            <h2 style="color: white; text-align: center; margin: 0; font-size: 1.5rem;">💰 PASO 2: CONFIGURAR VENTA</h2>
        </div>
        """, unsafe_allow_html=True)

        # Mejor reparto: columna para tipo de cliente (más compacta) y columna para pagos (más ancha)
        col1, col2 = st.columns([1.2, 2.8])

        with col1:
            st.markdown("""
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="font-size:1.1rem;">👤</div>
                <div style="font-weight:700;">Tipo de Cliente</div>
            </div>  
            """, unsafe_allow_html=True)
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

            # caption eliminado por petición del usuario (limpieza visual)

        with col2:
            st.markdown("""
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="font-size:1.1rem;">💳</div>
                <div style="font-weight:700;">Tipos de Pago</div>
            </div>
            """, unsafe_allow_html=True)

            # Elegir modo de pago: Pago único (elige un tipo) o Pago mixto (varios tipos)
            modo_pago = st.radio(
                "Modo de pago:",
                ["Pago único", "Pago mixto"],
                index=0,
                horizontal=True,
                key="modo_pago_final"
            )

            if modo_pago == "Pago mixto":
                st.markdown("**Selecciona múltiples tipos de pago:**")
                col_pago1, col_pago2 = st.columns(2)

                with col_pago1:
                    pago_efectivo = st.checkbox("💵 Efectivo", value=True, key="efectivo_final")
                    pago_tarjeta = st.checkbox("💳 Tarjeta", key="tarjeta_final")

                with col_pago2:
                    pago_transferencia = st.checkbox("🏦 Transferencia", key="transferencia_final")
                    pago_credito = st.checkbox("🧾 Crédito", key="credito_final")

            else:
                # Pago único: usar radio buttons para selección exclusiva
                st.markdown("**Selecciona la forma de pago:**")
                
                # Inicializar el tipo de pago seleccionado si no existe
                if 'tipo_pago_unico_selected' not in st.session_state:
                    st.session_state.tipo_pago_unico_selected = 'Efectivo'
                
                # Radio buttons con opciones de pago
                pago_seleccionado = st.radio(
                    "Método de pago",
                    options=['Efectivo', 'Tarjeta', 'Transferencia', 'Crédito'],
                    index=['Efectivo', 'Tarjeta', 'Transferencia', 'Crédito'].index(st.session_state.tipo_pago_unico_selected),
                    format_func=lambda x: {'Efectivo': '💵 Efectivo', 'Tarjeta': '💳 Tarjeta', 'Transferencia': '🏦 Transferencia', 'Crédito': '🧾 Crédito'}[x],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="radio_pago_unico"
                )
                
                # Actualizar session state
                st.session_state.tipo_pago_unico_selected = pago_seleccionado
                
                # Convertir selección a variables booleanas para compatibilidad
                pago_efectivo = (pago_seleccionado == 'Efectivo')
                pago_tarjeta = (pago_seleccionado == 'Tarjeta')
                pago_transferencia = (pago_seleccionado == 'Transferencia')
                pago_credito = (pago_seleccionado == 'Crédito')

            # (removed helper emoji row as requested — the selectable checkboxes/buttons are above)
        
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
                        
                            # Actualizar stock según tipo de venta
                            if tipo_venta == 'granel':
                                # Para productos a granel, solo restar del stock_kg
                                cursor.execute("UPDATE productos SET stock_kg = stock_kg - ? WHERE codigo = ?", 
                                             (peso_vendido, item['codigo']))
                            else:
                                # Para productos por unidad, solo restar del stock
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
                        
                        # Sincronizar con Supabase automáticamente
                        if SYNC_AVAILABLE:
                            try:
                                sync_manager = get_sync_manager()
                                if sync_manager.is_online():
                                    # Sincronizar la venta recién registrada
                                    cursor.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,))
                                    venta_registrada = cursor.fetchone()
                                    if venta_registrada:
                                        venta_dict = {
                                            'id': venta_registrada[0],
                                            'fecha': venta_registrada[1],
                                            'codigo': venta_registrada[2],
                                            'nombre': venta_registrada[3],
                                            'cantidad': venta_registrada[4],
                                            'precio_unitario': venta_registrada[5],
                                            'total': venta_registrada[6],
                                            'tipo_cliente': venta_registrada[7],
                                            'tipos_pago': venta_registrada[8],
                                            'monto_efectivo': venta_registrada[9],
                                            'monto_tarjeta': venta_registrada[10],
                                            'monto_transferencia': venta_registrada[11],
                                            'monto_credito': venta_registrada[12],
                                            'fecha_vencimiento_credito': venta_registrada[13],
                                            'hora_vencimiento_credito': venta_registrada[14],
                                            'cliente_credito': venta_registrada[15],
                                            'pagado': venta_registrada[16],
                                            'alerta_mostrada': venta_registrada[17],
                                            'peso_vendido': venta_registrada[18],
                                            'tipo_venta': venta_registrada[19]
                                        }
                                        sync_manager.sync_venta_to_supabase(venta_dict)
                                    
                                    # Sincronizar el stock actualizado de cada producto vendido
                                    for item_vendido in productos_vendidos:
                                        cursor.execute("SELECT * FROM productos WHERE codigo = ?", (item_vendido['codigo'],))
                                        producto_actualizado = cursor.fetchone()
                                        if producto_actualizado:
                                            producto_dict = {
                                                'codigo': producto_actualizado[0],
                                                'nombre': producto_actualizado[1],
                                                'precio_compra': producto_actualizado[2],
                                                'precio_normal': producto_actualizado[3],
                                                'precio_mayoreo_1': producto_actualizado[4],
                                                'precio_mayoreo_2': producto_actualizado[5],
                                                'precio_mayoreo_3': producto_actualizado[6],
                                                'stock': producto_actualizado[7],
                                                'tipo_venta': producto_actualizado[8],
                                                'precio_por_kg': producto_actualizado[9],
                                                'peso_unitario': producto_actualizado[10],
                                                'stock_kg': producto_actualizado[11],
                                                'stock_minimo': producto_actualizado[12],
                                                'stock_minimo_kg': producto_actualizado[13],
                                                'stock_maximo': producto_actualizado[14],
                                                'stock_maximo_kg': producto_actualizado[15],
                                                'categoria': producto_actualizado[16]
                                            }
                                            sync_manager.sync_producto_to_supabase(producto_dict)
                            except Exception as sync_error:
                                print(f"Error en sincronización automática: {sync_error}")
                        
                        # Guardar mensaje de éxito para mostrar después del rerun
                        st.session_state['mostrar_mensaje_exito'] = True
                        st.session_state['total_venta'] = total_general
                        
                        # Limpiar carrito y campos de entrada
                        st.session_state.carrito = []
                        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('editando_')]
                        for key in keys_to_remove:
                            del st.session_state[key]
                        
                        # Resetear método de pago a Efectivo para la siguiente venta
                        st.session_state.tipo_pago_unico_selected = 'Efectivo'
                        
                        # Marcar que se debe limpiar el código para nueva venta
                        st.session_state['limpiar_codigo'] = True
                        st.session_state['venta_finalizada'] = True
                        
                        # Rerun inmediato para que el autofocus funcione correctamente
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
                    use_container_width=True
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

    # --- SECCIÓN: VENTAS DE HOY CON DETALLE COMPLETO ---
    st.markdown("---")
    st.subheader("📋 Ventas de Hoy - Detalle por Venta")
    st.write("💡 **Tip:** Los montos deben sumar exactamente el total de la venta para poder actualizar.")

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Obtener todas las ventas de hoy con información completa
        query_hoy = """
            SELECT 
                id, fecha, codigo, nombre, cantidad, precio_unitario, total,
                tipo_cliente, tipos_pago,
                monto_efectivo, monto_tarjeta, monto_transferencia, monto_credito,
                cliente_credito
            FROM ventas 
            WHERE DATE(fecha) = ?
            ORDER BY fecha DESC
        """
        
        ventas_hoy_df = pd.read_sql_query(query_hoy, conn, params=(fecha_hoy,))
        
        if ventas_hoy_df.empty:
            st.info("ℹ️ No hay ventas registradas hoy.")
        else:
            # Agrupar ventas por fecha (ticket)
            grouped = list(ventas_hoy_df.groupby('fecha', sort=False))
            
            for idx, (fecha_ticket, group) in enumerate(grouped):
                # Usar el menor id del grupo como identificador
                min_id = int(group['id'].min())
                
                # Resumen del ticket
                nombres = group['nombre'].tolist()
                if len(nombres) == 1:
                    display_name = nombres[0]
                else:
                    display_name = f"{nombres[0]} (+{len(nombres)-1} más)"
                
                total_ticket = float(group['total'].sum())
                tipos_pago = group.iloc[0].get('tipos_pago', 'N/A')
                
                # Keys para widgets
                ef_key = f"ef_hoy_{min_id}"
                tar_key = f"tar_hoy_{min_id}"
                trans_key = f"trans_hoy_{min_id}"
                cred_key = f"cred_hoy_{min_id}"
                
                pending_auto = f"pending_auto_hoy_{min_id}"
                pending_reset = f"pending_reset_hoy_{min_id}"
                pending_restore = f"pending_restore_hoy_{min_id}"
                
                # Aplicar acciones pendientes
                if pending_auto in st.session_state:
                    st.session_state[ef_key] = st.session_state.pop(pending_auto)
                
                if pending_reset in st.session_state:
                    vals = st.session_state.pop(pending_reset)
                    st.session_state[ef_key] = vals[0]
                    st.session_state[tar_key] = vals[1]
                    st.session_state[trans_key] = vals[2]
                    st.session_state[cred_key] = vals[3]
                
                if pending_restore in st.session_state:
                    st.session_state.pop(pending_restore)
                    st.session_state[ef_key] = round(float(group['monto_efectivo'].fillna(0).sum()), 2)
                    st.session_state[tar_key] = round(float(group['monto_tarjeta'].fillna(0).sum()), 2)
                    st.session_state[trans_key] = round(float(group['monto_transferencia'].fillna(0).sum()), 2)
                    st.session_state[cred_key] = round(float(group['monto_credito'].fillna(0).sum()), 2)
                
                # Clamp valores al total del ticket
                total_venta = round(total_ticket, 2)
                for k in (ef_key, tar_key, trans_key, cred_key):
                    if k in st.session_state:
                        try:
                            val = float(st.session_state.get(k, 0.0))
                        except Exception:
                            val = 0.0
                        if val > total_venta:
                            st.session_state[k] = total_venta
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
                        
                        # Mostrar distribución actual
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
                        st.write(f"**Total a distribuir: ${total_venta:.2f}**")
                        
                        # Inicializar valores
                        monto_efectivo_inicial = min(round(efectivo_sum, 2), total_venta)
                        monto_tarjeta_inicial = min(round(tarjeta_sum, 2), total_venta)
                        monto_transferencia_inicial = min(round(transferencia_sum, 2), total_venta)
                        monto_credito_inicial = min(round(credito_sum, 2), total_venta)
                        
                        suma_inicial = monto_efectivo_inicial + monto_tarjeta_inicial + monto_transferencia_inicial + monto_credito_inicial
                        if abs(suma_inicial - total_venta) > 0.01:
                            monto_efectivo_inicial = total_venta
                            monto_tarjeta_inicial = 0.0
                            monto_transferencia_inicial = 0.0
                            monto_credito_inicial = 0.0
                        
                        st.session_state.setdefault(ef_key, round(monto_efectivo_inicial, 2))
                        st.session_state.setdefault(tar_key, round(monto_tarjeta_inicial, 2))
                        st.session_state.setdefault(trans_key, round(monto_transferencia_inicial, 2))
                        st.session_state.setdefault(cred_key, round(monto_credito_inicial, 2))
                        
                        # Inputs para nuevos montos
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
                        
                        # Validar suma
                        suma_nueva = nuevo_efectivo + nuevo_tarjeta + nuevo_transferencia + nuevo_credito
                        diferencia = abs(suma_nueva - total_venta)
                        
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
                        
                        # Botones de auto-ajuste
                        if diferencia > 0.01:
                            col_auto1, col_auto2 = st.columns(2)
                            
                            with col_auto1:
                                if st.button(
                                    "🔧 Auto-ajustar al Efectivo", 
                                    key=f"auto_efectivo_hoy_{min_id}",
                                    help="Asignar toda la diferencia al efectivo"
                                ):
                                    diferencia_restante = total_venta - (nuevo_tarjeta + nuevo_transferencia + nuevo_credito)
                                    if diferencia_restante >= 0:
                                        st.session_state[pending_auto] = round(diferencia_restante, 2)
                                        st.info(f"💡 Ajustando efectivo a ${diferencia_restante:.2f}")
                                        st.rerun()
                            
                            with col_auto2:
                                if st.button(
                                    "🔄 Resetear a 100% Efectivo", 
                                    key=f"reset_efectivo_hoy_{min_id}",
                                    help="Poner todo el monto en efectivo"
                                ):
                                    st.session_state[pending_reset] = (round(total_venta, 2), 0.0, 0.0, 0.0)
                                    st.info("💡 Configurando 100% efectivo")
                                    st.rerun()
                        
                        # Botones principales
                        st.divider()
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            button_disabled = diferencia > 0.01
                            button_type = "primary" if not button_disabled else "secondary"
                            button_text = "💾 Actualizar" if not button_disabled else "❌ Corrige la suma"
                            
                            if st.button(
                                button_text,
                                key=f"update_hoy_{min_id}",
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
                                    
                                    st.success(f"✅ Venta #{min_id} actualizada correctamente")
                                    
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
                                    
                                    import time
                                    time.sleep(2)
                                    st.rerun()
                                
                                except Exception as e:
                                    st.error(f"❌ Error al actualizar: {str(e)}")
                                    conn.rollback()
                        
                        with col_btn2:
                            if st.button(
                                f"🔄 Restaurar Valores", 
                                key=f"reset_hoy_{min_id}",
                                help="Restaurar a los valores guardados en la base de datos"
                            ):
                                st.session_state[pending_restore] = True
                                st.info("🔄 Restaurando valores originales...")
                                import time
                                time.sleep(0.2)
                                st.rerun()
            
            # Tabla resumen de ventas de hoy con tipo de pago editable
            st.divider()
            st.subheader("📊 Resumen de Ventas de Hoy")
            
            # Mostrar tabla con selectbox editable para tipos_pago
            opciones_tipos_pago = ["Efectivo", "Tarjeta", "Transferencia", "Efectivo, Tarjeta", "Efectivo, Transferencia", "Tarjeta, Transferencia", "Crédito", "Sin especificar"]
            
            # Agrupar por fecha para mostrar una fila por ticket
            ventas_agrupadas = ventas_hoy_df.groupby('fecha').agg({
                'id': 'min',
                'codigo': lambda x: f"{list(x)[0]}" + (f" (+{len(x)-1})" if len(x) > 1 else ""),
                'nombre': lambda x: f"{list(x)[0]}" + (f" (+{len(x)-1} más)" if len(x) > 1 else ""),
                'cantidad': 'sum',
                'total': 'sum',
                'tipos_pago': 'first',
                'tipo_cliente': 'first'
            }).reset_index().sort_values('fecha', ascending=False)
            
            # Mostrar cada fila con selectbox editable
            for idx, row in ventas_agrupadas.iterrows():
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 0.8, 1.2, 1.5, 0.7, 0.9, 1.5, 1.0])
                
                with col1:
                    st.markdown(f'<div style="display:flex;align-items:center;height:35px;font-size:0.85rem;">🆔 {int(row["id"])}</div>', unsafe_allow_html=True)
                
                with col2:
                    hora_formato = pd.to_datetime(row['fecha']).strftime('%H:%M')
                    st.markdown(f'<div style="display:flex;align-items:center;height:35px;font-size:0.85rem;">🕐 {hora_formato}</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f'<div style="display:flex;align-items:center;height:35px;font-size:0.85rem;">📦 {row["codigo"]}</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f'<div style="display:flex;align-items:center;height:35px;font-size:0.85rem;">📋 {row["nombre"]}</div>', unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f'<div style="display:flex;align-items:center;height:35px;font-size:0.85rem;">📊 {row["cantidad"]}</div>', unsafe_allow_html=True)
                
                with col6:
                    st.markdown(f'<div style="display:flex;align-items:center;height:35px;font-size:0.85rem;">💰 ${row["total"]:.2f}</div>', unsafe_allow_html=True)
                
                with col7:
                    # Selectbox para tipos de pago (editable) - más compacto
                    tipo_pago_actual = row['tipos_pago'] if row['tipos_pago'] in opciones_tipos_pago else "Sin especificar"
                    
                    # CSS para hacer el selectbox más pequeño
                    st.markdown("""
                    <style>
                    div[data-testid="stSelectbox"] > div > div {
                        min-height: 35px !important;
                        height: 35px !important;
                    }
                    div[data-testid="stSelectbox"] > div > div > div {
                        padding: 0.3rem 0.5rem !important;
                        font-size: 0.85rem !important;
                        line-height: 1.2 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    nuevo_tipo_pago = st.selectbox(
                        "💳",
                        opciones_tipos_pago,
                        index=opciones_tipos_pago.index(tipo_pago_actual),
                        key=f"tipo_pago_tabla_{int(row['id'])}_{idx}",
                        label_visibility="collapsed"
                    )
                    
                    # Auto-guardar si cambió el tipo de pago
                    if nuevo_tipo_pago != tipo_pago_actual:
                        try:
                            # Obtener el total de la venta
                            total_venta = float(row['total'])
                            
                            # Resetear todos los montos
                            monto_efectivo = 0.0
                            monto_tarjeta = 0.0
                            monto_transferencia = 0.0
                            monto_credito = 0.0
                            
                            # Asignar el monto según el tipo de pago seleccionado
                            if nuevo_tipo_pago == "Efectivo":
                                monto_efectivo = total_venta
                            elif nuevo_tipo_pago == "Tarjeta":
                                monto_tarjeta = total_venta
                            elif nuevo_tipo_pago == "Transferencia":
                                monto_transferencia = total_venta
                            elif nuevo_tipo_pago == "Crédito":
                                monto_credito = total_venta
                            elif nuevo_tipo_pago == "Efectivo, Tarjeta":
                                # Dividir 50/50 entre efectivo y tarjeta
                                monto_efectivo = total_venta / 2
                                monto_tarjeta = total_venta / 2
                            elif nuevo_tipo_pago == "Efectivo, Transferencia":
                                # Dividir 50/50 entre efectivo y transferencia
                                monto_efectivo = total_venta / 2
                                monto_transferencia = total_venta / 2
                            elif nuevo_tipo_pago == "Tarjeta, Transferencia":
                                # Dividir 50/50 entre tarjeta y transferencia
                                monto_tarjeta = total_venta / 2
                                monto_transferencia = total_venta / 2
                            
                            # Actualizar la BD con tipos_pago Y los montos individuales
                            cursor.execute("""
                                UPDATE ventas 
                                SET tipos_pago = ?,
                                    monto_efectivo = ?,
                                    monto_tarjeta = ?,
                                    monto_transferencia = ?,
                                    monto_credito = ?
                                WHERE fecha = ?
                            """, (nuevo_tipo_pago, monto_efectivo, monto_tarjeta, 
                                  monto_transferencia, monto_credito, row['fecha']))
                            conn.commit()
                            st.success("✅", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                with col8:
                    st.markdown(f'<div style="display:flex;align-items:center;height:35px;font-size:0.85rem;">👤 {row["tipo_cliente"]}</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ Error al cargar ventas de hoy: {str(e)}")
    
    # Script para hacer focus automático en el campo de código después de finalizar venta
    if st.session_state.get('venta_finalizada', False):
        st.session_state['venta_finalizada'] = False
        
        st.markdown("""
        <script>
        // Función para hacer focus en el campo de código después de finalizar venta
        function focusCodigoAfterVenta() {
            console.log('Intentando hacer focus en campo de código después de venta...');
            
            // Buscar el input de código por diferentes métodos
            const searchMethods = [
                () => window.parent.document.querySelectorAll('input[aria-label="Código de Barras"]'),
                () => window.parent.document.querySelectorAll('input[placeholder*="Escanea o ingresa"]'),
                () => window.parent.document.querySelectorAll('input[type="text"]'),
                () => document.querySelectorAll('input[aria-label="Código de Barras"]'),
                () => document.querySelectorAll('input[placeholder*="Escanea o ingresa"]')
            ];
            
            let codigoInput = null;
            
            for (let method of searchMethods) {
                try {
                    const inputs = method();
                    if (inputs && inputs.length > 0) {
                        codigoInput = inputs[0];
                        console.log('Input encontrado usando método:', method);
                        break;
                    }
                } catch (e) {
                    console.log('Error en método de búsqueda:', e);
                }
            }
            
            if (codigoInput) {
                // Limpiar el campo
                codigoInput.value = '';
                
                // Hacer focus
                codigoInput.focus();
                codigoInput.select();
                
                // Scroll hacia arriba para que el campo esté visible
                codigoInput.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
                
                console.log('✅ Focus establecido en campo de código');
                return true;
            } else {
                console.log('❌ No se encontró el campo de código');
                return false;
            }
        }
        
        // Intentar hacer focus múltiples veces con delays crecientes
        setTimeout(() => focusCodigoAfterVenta(), 100);
        setTimeout(() => focusCodigoAfterVenta(), 300);
        setTimeout(() => focusCodigoAfterVenta(), 600);
        setTimeout(() => focusCodigoAfterVenta(), 1000);
        setTimeout(() => focusCodigoAfterVenta(), 1500);
        setTimeout(() => focusCodigoAfterVenta(), 2500);
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

# ======================== PUNTO DE ENTRADA PRINCIPAL ========================

# Solo verificar sesión si se ejecuta ventas.py directamente (no desde main.py)
if __name__ == "__main__":
    # Verificar sesión administrativa
    if not verificar_sesion_admin():
        # Mostrar formulario de login si no hay sesión válida
        mostrar_formulario_login("VENTAS")
    else:
        # Si hay sesión válida, mostrar la aplicación
        mostrar()
else:
    # Si se importa desde otro módulo (main.py), asumir sesión ya verificada
    # El módulo será llamado por main.py solo si la sesión es válida
    pass