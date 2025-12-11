"""
======================================================================================
MÓDULO DE GESTIÓN DE PEDIDOS Y REABASTECIMIENTO
======================================================================================

FLUJO DE TRABAJO AUTOMATIZADO:

1. 📝 CREAR PEDIDO (Estado: PENDIENTE)
   - Se seleccionan productos con stock bajo
   - Se calcula automáticamente la cantidad para completar al stock máximo
   - Se genera el pedido con estado PENDIENTE

2. 📦 MARCAR COMO RECIBIDO (Estado: RECIBIDO)
   - Al presionar "Marcar como RECIBIDO" se ejecutan AUTOMÁTICAMENTE:
     ✓ Actualización del stock de todos los productos
     ✓ Generación de la orden de compra
     ✓ Cambio de estado del pedido a RECIBIDO
   - Esta acción NO ES REVERSIBLE

3. 💰 REGISTRAR PAGO (Estado: COMPLETADO)
   - En el módulo de Finanzas, al marcar la orden de compra como "Pagada"
   - Se ejecutan AUTOMÁTICAMENTE:
     ✓ Registro del egreso en finanzas
     ✓ Cambio de estado del pedido a COMPLETADO
     ✓ Actualización del estado de la orden de compra

ESTADOS DEL PEDIDO:
- 🟡 PENDIENTE: Pedido creado, esperando mercancía
- 🟢 RECIBIDO: Mercancía recibida, stock actualizado, orden generada
- ✅ COMPLETADO: Orden de compra pagada, proceso finalizado

======================================================================================
"""

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
from auth_manager import verificar_sesion_admin, cerrar_sesion_admin, obtener_tiempo_restante, mostrar_formulario_login

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

# Las funciones de autenticación ahora se importan desde auth_manager.py

# === GESTIÓN DE PEDIDOS Y CHECKLIST ===

def crear_tabla_pedidos():
    """Crear tabla de pedidos/checklist si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de pedidos (cabecera)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_pedido TEXT NOT NULL,
            fecha_entrega_esperada TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            total_productos INTEGER DEFAULT 0,
            total_costo REAL DEFAULT 0,
            notas TEXT DEFAULT '',
            creado_por TEXT NOT NULL,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            orden_compra_id INTEGER
        )
    ''')
    
    # Crear tabla de items de pedido (detalle)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            codigo_producto TEXT NOT NULL,
            nombre_producto TEXT NOT NULL,
            cantidad_solicitada REAL NOT NULL,
            cantidad_recibida REAL DEFAULT 0,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            proveedor TEXT DEFAULT '',
            estado_item TEXT DEFAULT 'PENDIENTE',
            FOREIGN KEY(pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
            FOREIGN KEY(codigo_producto) REFERENCES productos(codigo)
        )
    ''')
    
    # Crear tabla de órdenes de compra
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordenes_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_orden REAL NOT NULL,
            estado TEXT DEFAULT 'PENDIENTE',
            fecha_pago TEXT,
            notas TEXT,
            creado_por TEXT DEFAULT 'admin',
            FOREIGN KEY(pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE
        )
    ''')
    
    # Agregar columna pedido_id si no existe (migración)
    try:
        cursor.execute("SELECT pedido_id FROM ordenes_compra LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE ordenes_compra ADD COLUMN pedido_id INTEGER")
        conn.commit()
    
    conn.commit()
    conn.close()

def generar_orden_compra_desde_pedido(pedido_id):
    """Generar orden de compra para un pedido específico con estado RECIBIDO"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar que el pedido existe y está RECIBIDO
        cursor.execute("SELECT * FROM pedidos WHERE id = ? AND estado = 'RECIBIDO'", (pedido_id,))
        pedido = cursor.fetchone()
        
        if not pedido:
            return None, "El pedido no existe o no está en estado RECIBIDO"
        
        # Verificar que no tenga ya una orden de compra
        if pedido[8]:  # orden_compra_id
            return None, "Este pedido ya tiene una orden de compra generada"
        
        total_orden = pedido[5]  # total_costo
        
        # Crear la orden de compra
        cursor.execute("""
            INSERT INTO ordenes_compra (pedido_id, total_orden, estado, creado_por)
            VALUES (?, ?, 'PENDIENTE', 'admin')
        """, (pedido_id, total_orden))
        
        orden_id = cursor.lastrowid
        
        # Actualizar el pedido con el ID de la orden de compra
        cursor.execute("""
            UPDATE pedidos 
            SET orden_compra_id = ?
            WHERE id = ?
        """, (orden_id, pedido_id))
        
        conn.commit()
        
        # Sincronizar con Supabase
        if sync.is_online():
            # Sincronizar la orden de compra
            conn_temp = sqlite3.connect(DB_PATH)
            conn_temp.row_factory = sqlite3.Row
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT * FROM ordenes_compra WHERE id = ?", (orden_id,))
            orden = cursor_temp.fetchone()
            conn_temp.close()
            
            if orden:
                sync.sync_orden_compra_to_supabase(dict(orden))
        
        return orden_id, f"Orden de compra #{orden_id} creada exitosamente. Total: ${total_orden:.2f}"
        
    except Exception as e:
        conn.rollback()
        return None, f"Error al generar orden de compra: {str(e)}"
    finally:
        conn.close()

def obtener_productos_bajo_stock():
    """Obtener productos con stock bajo que necesitan reabastecimiento"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = None  # Forzar reconexión limpia
    
    query = """
    SELECT codigo, nombre, stock, stock_minimo, stock_kg, stock_minimo_kg, 
           stock_maximo, stock_maximo_kg, tipo_venta,
           precio_compra, precio_normal, precio_por_kg, categoria,
           CASE 
               WHEN tipo_venta = 'granel' THEN 
                   CASE WHEN stock_maximo_kg > 0 THEN CAST((stock_kg * 100.0 / stock_maximo_kg) AS INTEGER) ELSE 100 END
               ELSE 
                   CASE WHEN stock_maximo > 0 THEN CAST((stock * 100.0 / stock_maximo) AS INTEGER) ELSE 100 END
           END as porcentaje_stock,
           CASE 
               WHEN tipo_venta = 'granel' THEN 
                   CASE 
                       WHEN stock_maximo_kg > 0 THEN ROUND(MAX(stock_maximo_kg - stock_kg, 1.0), 2)
                       ELSE ROUND(MAX(stock_minimo_kg * 3.0, 5.0), 2)
                   END
               ELSE 
                   CASE 
                       WHEN stock_maximo > 0 THEN MAX(stock_maximo - stock, 1)
                       ELSE MAX(stock_minimo * 3, 10)
                   END
           END as cantidad_necesaria,
           CASE 
               WHEN tipo_venta = 'granel' THEN 
                   ROUND(CASE WHEN stock_maximo_kg > 0 THEN MAX(stock_maximo_kg - stock_kg, 1.0) ELSE MAX(stock_minimo_kg * 3.0, 5.0) END, 2)
               ELSE 
                   CASE WHEN stock_maximo > 0 THEN MAX(stock_maximo - stock, 1) ELSE MAX(stock_minimo * 3, 10) END
           END as cantidad_hasta_maximo
    FROM productos 
    WHERE (
        (tipo_venta = 'unidad' AND stock <= stock_minimo AND stock_minimo > 0) OR
        (tipo_venta = 'granel' AND stock_kg <= stock_minimo_kg AND stock_minimo_kg > 0)
    )
    ORDER BY categoria, porcentaje_stock ASC
    """
    
    try:
        productos_bajo_stock = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error al obtener productos bajo stock: {e}")
        productos_bajo_stock = pd.DataFrame()
    finally:
        conn.close()
    
    return productos_bajo_stock

def crear_pedido_con_productos(productos_lista, fecha_entrega_esperada="", notas="", creado_por="admin"):
    """Crear un pedido con múltiples productos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        fecha_pedido = datetime.now().strftime("%Y-%m-%d")
        total_productos = len(productos_lista)
        total_costo = sum(p['cantidad'] * p['precio'] for p in productos_lista)
        
        # Crear el pedido (cabecera)
        cursor.execute('''
            INSERT INTO pedidos 
            (fecha_pedido, fecha_entrega_esperada, estado, total_productos, total_costo, notas, creado_por)
            VALUES (?, ?, 'PENDIENTE', ?, ?, ?, ?)
        ''', (fecha_pedido, fecha_entrega_esperada, total_productos, total_costo, notas, creado_por))
        
        pedido_id = cursor.lastrowid
        
        # Insertar los items del pedido
        for producto in productos_lista:
            subtotal = producto['cantidad'] * producto['precio']
            cursor.execute('''
                INSERT INTO pedidos_items
                (pedido_id, codigo_producto, nombre_producto, cantidad_solicitada, precio_unitario, subtotal, proveedor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (pedido_id, producto['codigo'], producto['nombre'], producto['cantidad'], 
                  producto['precio'], subtotal, producto['proveedor']))
        
        conn.commit()
        
        # Sincronizar con Supabase
        if sync.is_online():
            conn_temp = sqlite3.connect(DB_PATH)
            conn_temp.row_factory = sqlite3.Row
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
            pedido = cursor_temp.fetchone()
            conn_temp.close()
            
            if pedido:
                sync.sync_pedido_to_supabase(dict(pedido))
        
        return pedido_id, True
        
    except Exception as e:
        conn.rollback()
        return None, False
    finally:
        conn.close()

def agregar_producto_a_pedido(codigo_producto, nombre_producto, cantidad_solicitada, precio_unitario, proveedor="", fecha_entrega_esperada="", notas="", creado_por="admin"):
    """DEPRECADO: Usar crear_pedido_con_productos en su lugar"""
    # Mantener por compatibilidad, pero crear un pedido con un solo producto
    productos_lista = [{
        'codigo': codigo_producto,
        'nombre': nombre_producto,
        'cantidad': cantidad_solicitada,
        'precio': precio_unitario,
        'proveedor': proveedor
    }]
    
    pedido_id, exito = crear_pedido_con_productos(productos_lista, fecha_entrega_esperada, notas, creado_por)
    return exito

def obtener_pedidos_activos():
    """Obtener todos los pedidos activos"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT id, fecha_pedido, fecha_entrega_esperada, estado, 
           total_productos, total_costo, notas, creado_por, orden_compra_id
    FROM pedidos 
    ORDER BY 
        CASE 
            WHEN estado = 'COMPLETADO' THEN 1 
            ELSE 0 
        END,
        fecha_pedido DESC
    """
    
    pedidos = pd.read_sql_query(query, conn)
    conn.close()
    return pedidos

def obtener_items_pedido(pedido_id):
    """Obtener los items/productos de un pedido específico"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT id, codigo_producto, nombre_producto, cantidad_solicitada, cantidad_recibida,
           precio_unitario, subtotal, proveedor, estado_item
    FROM pedidos_items 
    WHERE pedido_id = ?
    ORDER BY nombre_producto
    """
    
    items = pd.read_sql_query(query, conn, params=(pedido_id,))
    conn.close()
    return items

def marcar_pedido_como_recibido(pedido_id):
    """Marcar pedido como RECIBIDO: genera orden de compra y actualiza stock automáticamente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar que el pedido existe y está PENDIENTE
        cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
        pedido = cursor.fetchone()
        
        if not pedido:
            return False, "El pedido no existe"
        
        if pedido[3] != 'PENDIENTE':  # estado
            return False, f"El pedido ya está en estado {pedido[3]}"
        
        # 1. Actualizar estado a RECIBIDO
        cursor.execute("UPDATE pedidos SET estado = 'RECIBIDO' WHERE id = ?", (pedido_id,))
        
        # 2. Actualizar stock de productos usando cantidad_recibida (no cantidad_solicitada)
        cursor.execute("""
            SELECT pi.codigo_producto, pi.cantidad_recibida, p.tipo_venta
            FROM pedidos_items pi
            JOIN productos p ON pi.codigo_producto = p.codigo
            WHERE pi.pedido_id = ? AND pi.cantidad_recibida > 0
        """, (pedido_id,))
        
        items = cursor.fetchall()
        productos_actualizados = []
        
        for codigo_producto, cantidad_recibida, tipo_venta in items:
            if tipo_venta == 'granel':
                cursor.execute("""
                    UPDATE productos 
                    SET stock_kg = stock_kg + ?
                    WHERE codigo = ?
                """, (cantidad_recibida, codigo_producto))
            else:
                cursor.execute("""
                    UPDATE productos 
                    SET stock = stock + ?
                    WHERE codigo = ?
                """, (int(cantidad_recibida), codigo_producto))
            
            # Marcar item como RECIBIDO
            cursor.execute("""
                UPDATE pedidos_items 
                SET estado_item = 'RECIBIDO'
                WHERE pedido_id = ? AND codigo_producto = ?
            """, (pedido_id, codigo_producto))
            
            productos_actualizados.append(codigo_producto)
        
        # 3. Generar orden de compra con el total RECALCULADO (ya debe estar actualizado en la tabla pedidos)
        # Obtener el total_costo más reciente del pedido (que ya incluye cambios de cantidad_recibida)
        cursor.execute("""
            SELECT total_costo FROM pedidos WHERE id = ?
        """, (pedido_id,))
        
        total_orden = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO ordenes_compra (pedido_id, total_orden, estado, creado_por)
            VALUES (?, ?, 'PENDIENTE', 'admin')
        """, (pedido_id, total_orden))
        
        orden_id = cursor.lastrowid
        
        # 4. Vincular orden de compra al pedido
        cursor.execute("""
            UPDATE pedidos 
            SET orden_compra_id = ?
            WHERE id = ?
        """, (orden_id, pedido_id))
        
        conn.commit()
        
        # 5. Sincronizar con Supabase
        if sync.is_online():
            # Sincronizar productos actualizados
            for codigo in productos_actualizados:
                cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
                producto = cursor.fetchone()
                if producto:
                    producto_dict = {
                        'codigo': producto[0], 'nombre': producto[1], 'precio_compra': producto[2],
                        'precio_normal': producto[3], 'precio_mayoreo_1': producto[4],
                        'precio_mayoreo_2': producto[5], 'precio_mayoreo_3': producto[6],
                        'stock': producto[7], 'tipo_venta': producto[8], 'precio_por_kg': producto[9],
                        'peso_unitario': producto[10], 'stock_kg': producto[11],
                        'stock_minimo': producto[12], 'stock_minimo_kg': producto[13],
                        'stock_maximo': producto[14], 'stock_maximo_kg': producto[15],
                        'categoria': producto[16]
                    }
                    sync.sync_producto_to_supabase(producto_dict)
            
            # Sincronizar pedido
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
            pedido_actualizado = cursor.fetchone()
            if pedido_actualizado:
                sync.sync_pedido_to_supabase(dict(pedido_actualizado))
            
            # Sincronizar orden de compra
            cursor.execute("SELECT * FROM ordenes_compra WHERE id = ?", (orden_id,))
            orden = cursor.fetchone()
            if orden:
                sync.sync_orden_compra_to_supabase(dict(orden))
        
        return True, f"✅ Pedido marcado como RECIBIDO con {len(productos_actualizados)} productos\n💰 Cantidad recibida: {len(productos_actualizados)} productos\n📦 Orden de compra #{orden_id} generada por ${total_orden:.2f}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al marcar pedido como recibido: {str(e)}"
    finally:
        conn.close()

def marcar_pedido_como_completado(pedido_id):
    """Marcar pedido como COMPLETADO (se llama cuando se paga la orden de compra)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE pedidos SET estado = 'COMPLETADO' WHERE id = ?", (pedido_id,))
        conn.commit()
        
        # Sincronizar con Supabase
        if sync.is_online():
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
            pedido = cursor.fetchone()
            if pedido:
                sync.sync_pedido_to_supabase(dict(pedido))
        
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()

def actualizar_estado_pedido(pedido_id, estado=None, notas=None):
    """Actualizar el estado general de un pedido (DEPRECADO - usar marcar_pedido_como_recibido)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if estado is not None:
        updates.append("estado = ?")
        values.append(estado)
    
    if notas is not None:
        updates.append("notas = ?")
        values.append(notas)
    
    if updates:
        values.append(pedido_id)
        query = f"UPDATE pedidos SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    
    # Sincronizar con Supabase
    if sync.is_online():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
        pedido = cursor.fetchone()
        conn.close()
        
        if pedido:
            sync.sync_pedido_to_supabase(dict(pedido))
    
    return True

def actualizar_item_pedido(item_id, cantidad_recibida=None, estado_item=None):
    """Actualizar un item específico del pedido y recalcular el subtotal"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener el item actual para saber el precio unitario
        cursor.execute("""
            SELECT id, pedido_id, precio_unitario
            FROM pedidos_items
            WHERE id = ?
        """, (item_id,))
        
        item = cursor.fetchone()
        if not item:
            return False
        
        pedido_id = item[1]
        precio_unitario = item[2]
        
        updates = []
        values = []
        
        # Si se actualiza la cantidad recibida, recalcular el subtotal
        if cantidad_recibida is not None:
            updates.append("cantidad_recibida = ?")
            values.append(cantidad_recibida)
            
            # Recalcular subtotal = cantidad_recibida * precio_unitario
            nuevo_subtotal = cantidad_recibida * precio_unitario
            updates.append("subtotal = ?")
            values.append(nuevo_subtotal)
        
        if estado_item is not None:
            updates.append("estado_item = ?")
            values.append(estado_item)
        
        if updates:
            values.append(item_id)
            query = f"UPDATE pedidos_items SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            
            # Recalcular el total del pedido (suma de todos los subtotales)
            cursor.execute("""
                SELECT SUM(subtotal) FROM pedidos_items WHERE pedido_id = ?
            """, (pedido_id,))
            
            total_costo = cursor.fetchone()[0] or 0
            
            # Contar items que tienen cantidad_recibida > 0
            cursor.execute("""
                SELECT COUNT(*) FROM pedidos_items WHERE pedido_id = ? AND cantidad_recibida > 0
            """, (pedido_id,))
            
            total_productos = cursor.fetchone()[0]
            
            # Actualizar el total del pedido
            cursor.execute("""
                UPDATE pedidos 
                SET total_costo = ?, total_productos = ?
                WHERE id = ?
            """, (total_costo, total_productos, pedido_id))
            
            conn.commit()
        
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar item del pedido: {e}")
        return False
    finally:
        conn.close()

def eliminar_pedido(pedido_id):
    """Eliminar un pedido del sistema (incluyendo sus items por CASCADE)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
    conn.commit()
    conn.close()
    
    # Sincronizar con Supabase (eliminar también allá)
    if sync.is_online():
        try:
            sync.supabase_db.client.table('pedidos').delete().eq('id', pedido_id).execute()
        except Exception as e:
            print(f"Error al eliminar pedido de Supabase: {e}")
    
    return True

def actualizar_stock_desde_pedido(pedido_id):
    """Actualizar el stock de todos los productos de un pedido cuando se completa"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obtener todos los items del pedido con su cantidad recibida
    cursor.execute("""
        SELECT pi.codigo_producto, pi.cantidad_recibida, p.tipo_venta
        FROM pedidos_items pi
        JOIN productos p ON pi.codigo_producto = p.codigo
        WHERE pi.pedido_id = ? AND pi.cantidad_recibida > 0
    """, (pedido_id,))
    
    items = cursor.fetchall()
    productos_actualizados = []
    
    for codigo_producto, cantidad_recibida, tipo_venta in items:
        if tipo_venta == 'granel':
            cursor.execute("""
                UPDATE productos 
                SET stock_kg = stock_kg + ?
                WHERE codigo = ?
            """, (cantidad_recibida, codigo_producto))
        else:
            cursor.execute("""
                UPDATE productos 
                SET stock = stock + ?
                WHERE codigo = ?
            """, (int(cantidad_recibida), codigo_producto))
        
        productos_actualizados.append(codigo_producto)
    
    conn.commit()
    
    # Sincronizar a Supabase automáticamente
    if sync.is_online():
        try:
            for codigo in productos_actualizados:
                cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
                producto = cursor.fetchone()
                if producto:
                    producto_dict = {
                        'codigo': producto[0], 'nombre': producto[1], 'precio_compra': producto[2],
                        'precio_normal': producto[3], 'precio_mayoreo_1': producto[4],
                        'precio_mayoreo_2': producto[5], 'precio_mayoreo_3': producto[6],
                        'stock': producto[7], 'tipo_venta': producto[8], 'precio_por_kg': producto[9],
                        'peso_unitario': producto[10], 'stock_kg': producto[11],
                        'stock_minimo': producto[12], 'stock_minimo_kg': producto[13],
                        'stock_maximo': producto[14], 'stock_maximo_kg': producto[15],
                        'categoria': producto[16]
                    }
                    sync.sync_producto_to_supabase(producto_dict)
        except Exception as sync_error:
            print(f"Error en sincronización automática: {sync_error}")
    
    conn.close()
    return True

def mostrar():
    st.title("🛒 Gestión de Pedidos y Reabastecimiento")
    
    # ⚠️ IMPORTANTE: NO sincronizar productos desde Supabase para evitar sobrescribir ventas
    # La sincronización de productos se hace automáticamente HACIA Supabase cuando hay cambios
    # Solo sincronizar pedidos y órdenes de compra (que no afectan el stock)
    if sync.is_online():
        with st.spinner('🔄 Sincronizando pedidos y órdenes...'):
            resultado_pedidos = sync.sync_pedidos_from_supabase()
            resultado_ordenes = sync.sync_ordenes_compra_from_supabase()
            
            mensajes = []
            if resultado_pedidos.get('success', 0) > 0:
                mensajes.append(f"{resultado_pedidos['success']} pedidos")
            if resultado_ordenes.get('success', 0) > 0:
                mensajes.append(f"{resultado_ordenes['success']} órdenes")
            
            if mensajes:
                st.toast(f"✅ Sincronizados: {', '.join(mensajes)}")
    
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
    
    # === INFORMACIÓN DEL FLUJO DE TRABAJO ===
    with st.expander("ℹ️ ¿Cómo funciona el flujo de pedidos?", expanded=False):
        st.markdown("""
        ### 📋 Flujo Automatizado de Pedidos
        
        Este módulo gestiona todo el proceso de reabastecimiento de manera automática:
        
        #### 1️⃣ Crear Pedido (🟡 PENDIENTE)
        - Selecciona productos con stock bajo
        - Las cantidades se calculan automáticamente para completar al stock máximo
        - Ej: Si tienes 5 kg de Panela y máximo es 20 kg → se sugiere pedir 15 kg
        
        #### 2️⃣ Marcar como Recibido (🟢 RECIBIDO)
        Cuando presiones **"Marcar como RECIBIDO"**, el sistema automáticamente:
        - ✅ Actualiza el stock de todos los productos
        - ✅ Genera la orden de compra
        - ✅ Cambia el estado a RECIBIDO
        - ⚠️ **Esta acción NO ES REVERSIBLE**
        
        #### 3️⃣ Registrar Pago (✅ COMPLETADO)
        En el módulo de **Finanzas**, al marcar la orden como "Pagada":
        - ✅ Se registra el egreso automáticamente
        - ✅ El pedido se marca como COMPLETADO
        - ✅ El proceso finaliza
        
        ---
        
        **💡 Ventajas del nuevo sistema:**
        - 🚀 Todo es automático, menos errores
        - 📊 Stock siempre actualizado
        - 💰 Control financiero integrado
        - 🔄 Sincronización automática con Supabase
        """)
    
    # === CONTROL DE ACCESO ===
    es_admin = verificar_sesion_admin()
    
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        if es_admin:
            # Obtener tiempo restante usando función centralizada
            horas_restantes, minutos_restantes = obtener_tiempo_restante()
            st.success(f"✅ **Modo Administrador** - Usuario: {st.session_state.get('usuario_admin', 'admin')} | Sesión: {horas_restantes}h {minutos_restantes}m restantes")
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
        mostrar_formulario_login("PEDIDOS")
        st.markdown("---")
        
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
        col_titulo, col_refresh = st.columns([4, 1])
        with col_titulo:
            st.subheader("🚨 Productos que Necesitan Reabastecimiento")
            st.caption(f"🕐 Última actualización: {datetime.now().strftime('%H:%M:%S')}")
        with col_refresh:
            if st.button("🔄 Actualizar", key="refresh_bajo_stock", use_container_width=True):
                # Limpiar caché antes de actualizar
                if 'productos_bajo_stock_cache' in st.session_state:
                    del st.session_state.productos_bajo_stock_cache
                st.rerun()
        
        # Obtener productos con stock bajo (siempre fresh, sin caché)
        productos_bajo_stock = obtener_productos_bajo_stock()
        
        if not productos_bajo_stock.empty:
            st.warning(f"⚠️ **{len(productos_bajo_stock)} productos** necesitan reabastecimiento urgente")
            
            # Nota informativa sobre el criterio de alerta
            st.info("""
            🚨 **Criterio de Alerta:** Se muestran productos cuando **Stock Actual ≤ Stock Mínimo**  
            📊 **Cantidad Sugerida:** Stock Máximo - Stock Actual (para completar capacidad máxima)  
            💡 **Ejemplo:** Si tienes 5 kg y el máximo es 20 kg → Se sugiere pedir **15 kg**  
            ✏️ Puedes modificar las cantidades manualmente según tus necesidades
            """)
            
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
                                🛒 **Cantidad sugerida para completar stock máximo: {producto['cantidad_necesaria']:.1f} {unidad}**  
                                💰 Precio: ${producto['precio_compra']:.2f} | 💵 Total: ${producto['cantidad_necesaria'] * producto['precio_compra']:.2f}
                                """)
                            
                            with col_cantidad:
                                if seleccionado:
                                    cantidad_pedido = st.number_input(
                                        "🛒 Cantidad a pedir:",
                                        min_value=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                        value=float(producto['cantidad_necesaria']),  # Valor por defecto: completar al máximo
                                        step=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                        key=f"cantidad_{producto['codigo']}_{categoria}",
                                        format="%.1f" if producto['tipo_venta'] == 'granel' else "%.0f",
                                        help="Cantidad sugerida para alcanzar el stock máximo (capacidad completa)"
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
                        🛒 **Cantidad sugerida para completar stock máximo: {producto['cantidad_necesaria']:.1f} {unidad}**  
                        💰 Precio: ${producto['precio_compra']:.2f} | 💵 Total: ${producto['cantidad_necesaria'] * producto['precio_compra']:.2f}
                        """)
                    
                    with col_cantidad:
                        if seleccionado:
                            cantidad_pedido = st.number_input(
                                "🛒 Cantidad a pedir:",
                                min_value=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                value=float(producto['cantidad_necesaria']),
                                step=0.1 if producto['tipo_venta'] == 'granel' else 1.0,
                                key=f"cantidad_{producto['codigo']}",
                                format="%.1f" if producto['tipo_venta'] == 'granel' else "%.0f",
                                help="Cantidad sugerida para alcanzar el stock máximo (capacidad completa)"
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
                
                if st.button("✅ Crear Pedido de Reabastecimiento", type="primary", use_container_width=True):
                    try:
                        # Crear UN solo pedido con todos los productos
                        pedido_id, exito = crear_pedido_con_productos(
                            productos_lista=productos_seleccionados,
                            fecha_entrega_esperada=fecha_entrega.strftime("%Y-%m-%d"),
                            notas=notas_generales,
                            creado_por=st.session_state.get('usuario_admin', 'admin')
                        )
                        
                        if exito:
                            st.success(f"✅ Pedido #{pedido_id} creado exitosamente con {len(productos_seleccionados)} productos")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Error al crear el pedido")
                        
                    except Exception as e:
                        st.error(f"❌ Error al crear el pedido: {str(e)}")
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
                    ["Todos", "PENDIENTE", "RECIBIDO", "COMPLETADO"],
                    key="filtro_estado_pedidos"
                )
            
            with col_filtro2:
                mostrar_completados = st.checkbox("Mostrar pedidos completados", value=False)
            
            # Aplicar filtros
            df_filtrado = pedidos_df.copy()
            
            if filtro_estado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
            
            if not mostrar_completados:
                df_filtrado = df_filtrado[df_filtrado['estado'] != 'COMPLETADO']
            
            st.info(f"📊 Mostrando {len(df_filtrado)} de {len(pedidos_df)} pedidos")
            
            # Mostrar cada pedido con sus items
            for idx, pedido in df_filtrado.iterrows():
                # Estado visual del pedido
                estado_color = {
                    'PENDIENTE': '🟡',
                    'RECIBIDO': '🟢',
                    'COMPLETADO': '✅'
                }.get(pedido['estado'], '⚪')
                
                # Crear expander para cada pedido
                with st.expander(f"{estado_color} Pedido #{pedido['id']} - {pedido['total_productos']} productos - ${pedido['total_costo']:.2f}", expanded=(pedido['estado'] in ['PENDIENTE', 'EN_TRANSITO'])):
                    col_ped_info, col_ped_acciones = st.columns([2, 1])
                    
                    with col_ped_info:
                        st.markdown(f"""
                        **📋 Información del Pedido:**
                        - 📅 Fecha pedido: {pedido['fecha_pedido']}
                        - 🚚 Entrega esperada: {pedido['fecha_entrega_esperada'] or 'No especificada'}
                        - 📝 Estado: **{pedido['estado']}**
                        - 💰 Total: ${pedido['total_costo']:.2f}
                        - 📦 Productos: {pedido['total_productos']}
                        """)
                        
                        if pedido['notas']:
                            st.info(f"📝 **Notas:** {pedido['notas']}")
                        
                        # Obtener y mostrar items del pedido
                        items_df = obtener_items_pedido(pedido['id'])
                        
                        if not items_df.empty:
                            st.write("**Productos en este pedido:**")
                            
                            for item_idx, item in items_df.iterrows():
                                col_item_info, col_item_cantidad, col_item_subtotal = st.columns([2.5, 1.2, 1.3])
                                
                                with col_item_info:
                                    estado_item = "✅" if item['estado_item'] == 'RECIBIDO' else "⏳"
                                    st.write(f"{estado_item} **{item['nombre_producto']}** ({item['codigo_producto']})")
                                    st.write(f"   • Solicitado: {item['cantidad_solicitada']:.1f} | Precio: ${item['precio_unitario']:.2f}")
                                    if item['proveedor']:
                                        st.write(f"   • Proveedor: {item['proveedor']}")
                                
                                with col_item_cantidad:
                                    if es_admin and pedido['estado'] != 'COMPLETADO':
                                        nueva_cant_item = st.number_input(
                                            "Recibido:",
                                            min_value=0.0,
                                            value=float(item['cantidad_recibida']),
                                            step=1.0,
                                            key=f"item_{item['id']}_cantidad",
                                            label_visibility="collapsed"
                                        )
                                        
                                        # Calcular el nuevo subtotal en tiempo real
                                        nuevo_subtotal = nueva_cant_item * item['precio_unitario']
                                        
                                        # Mostrar si hay cambios
                                        if nueva_cant_item != item['cantidad_recibida']:
                                            st.warning(f"⚠️ Cambio detectado", icon="⚠️")
                                            if st.button("💾 Guardar", key=f"save_item_{item['id']}", use_container_width=True):
                                                actualizar_item_pedido(item['id'], cantidad_recibida=nueva_cant_item,
                                                                      estado_item='RECIBIDO' if nueva_cant_item > 0 else 'PENDIENTE')
                                                st.success("✅ Guardado", icon="✅")
                                                time.sleep(0.5)
                                                st.rerun()
                                    else:
                                        st.write(f"Recibido: {item['cantidad_recibida']:.1f}")
                                
                                with col_item_subtotal:
                                    if es_admin and pedido['estado'] != 'COMPLETADO':
                                        # Calcular el subtotal dinámicamente
                                        nueva_cant_item = st.session_state.get(f"item_{item['id']}_cantidad", item['cantidad_recibida'])
                                        nuevo_subtotal = nueva_cant_item * item['precio_unitario']
                                        
                                        # Mostrar el subtotal con cambio de color si es diferente
                                        if nuevo_subtotal != item['subtotal']:
                                            st.markdown(f"<div style='background-color: #fff3cd; padding: 8px; border-radius: 4px; text-align: center;'><b style='color: #856404;'>${nuevo_subtotal:.2f}</b><br><small style='color: #999;'>Nuevo: ${nuevo_subtotal:.2f}</small></div>", unsafe_allow_html=True)
                                        else:
                                            st.write(f"Subtotal: ${item['subtotal']:.2f}")
                                    else:
                                        st.write(f"Subtotal: ${item['subtotal']:.2f}")
                                
                                st.divider()
                    
                    with col_ped_acciones:
                        st.write("**Acciones:**")
                        
                        if es_admin:
                            # Mostrar estado actual con badge
                            estado_badge = {
                                'PENDIENTE': '🟡 PENDIENTE',
                                'RECIBIDO': '🟢 RECIBIDO',
                                'COMPLETADO': '✅ COMPLETADO'
                            }.get(pedido['estado'], pedido['estado'])
                            
                            st.info(f"**Estado actual:** {estado_badge}")
                            
                            # Botón para marcar como RECIBIDO (solo si está PENDIENTE)
                            if pedido['estado'] == 'PENDIENTE':
                                st.markdown("""<div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0;'>
                                <b>📦 IMPORTANTE - Antes de marcar como RECIBIDO:</b><br>
                                1️⃣ Revisa las cantidades solicitadas en cada producto<br>
                                2️⃣ Edita el campo "Recibido" con la cantidad real que recibiste<br>
                                3️⃣ Guarda los cambios presionando el botón 💾<br>
                                4️⃣ Una vez confirmadas todas las cantidades, presiona "Marcar como RECIBIDO"<br>
                                ✓ Se actualizará el stock con las cantidades que ingresaste<br>
                                ✓ Se generará la orden de compra<br>
                                ⚠️ No se podrá revertir este cambio
                                </div>""", unsafe_allow_html=True)
                                
                                if st.button("📦 Marcar como RECIBIDO", key=f"marcar_recibido_{pedido['id']}", type="primary", use_container_width=True):
                                    exito, mensaje = marcar_pedido_como_recibido(pedido['id'])
                                    
                                    if exito:
                                        st.success(mensaje)
                                        st.balloons()
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(mensaje)
                                        time.sleep(2)
                            
                            # Mostrar info de orden de compra si está RECIBIDO
                            elif pedido['estado'] == 'RECIBIDO':
                                if pedido.get('orden_compra_id'):
                                    st.success(f"✅ Orden de compra #{pedido['orden_compra_id']} generada")
                                    st.info("💳 Registra el pago en el módulo de Finanzas para marcar como COMPLETADO")
                                else:
                                    st.warning("⚠️ No se encontró orden de compra vinculada")
                            
                            # Si está COMPLETADO, solo mostrar info
                            elif pedido['estado'] == 'COMPLETADO':
                                st.success("✅ Pedido completado")
                                if pedido.get('orden_compra_id'):
                                    st.caption(f"Orden de compra #{pedido['orden_compra_id']} pagada")
                            
                            # Botón para eliminar
                            st.divider()
                            if st.button("🗑️ Eliminar Pedido", key=f"del_{pedido['id']}", type="secondary", use_container_width=True):
                                st.session_state[f'confirm_del_{pedido["id"]}'] = True
                            
                            if st.session_state.get(f'confirm_del_{pedido["id"]}', False):
                                if st.button("⚠️ CONFIRMAR ELIMINACIÓN", key=f"confirm_del_btn_{pedido['id']}", type="secondary", use_container_width=True):
                                    eliminar_pedido(pedido['id'])
                                    st.success("✅ Pedido eliminado")
                                    del st.session_state[f'confirm_del_{pedido["id"]}']
                                    time.sleep(1)
                                    st.rerun()
                        
                        elif not es_admin:
                            st.info("🔒 Modo solo lectura")
                        else:
                            st.success("✅ Completado")
                            if pedido.get('orden_compra_id'):
                                st.info(f"Orden: #{pedido['orden_compra_id']}")
        
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
            pedidos_pendientes = len(pedidos_df[pedidos_df['estado'] != 'COMPLETADO']) if not pedidos_df.empty else 0
            st.metric("⏳ Pedidos Pendientes", pedidos_pendientes)
        
        with col_met3:
            productos_criticos = len(productos_bajo_stock)
            st.metric("🚨 Productos Críticos", productos_criticos)
        
        with col_met4:
            if not pedidos_df.empty:
                inversion_total = pedidos_df[pedidos_df['estado'] != 'COMPLETADO']['total_costo'].sum()
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