"""
Gestor de Sincronización entre SQLite Local y Supabase
Permite trabajo offline con sincronización automática cuando hay internet
"""
import sqlite3
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import socket

try:
    from supabase_client import get_db as get_supabase_db
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

class SyncManager:
    def __init__(self, sqlite_path="pos_cremeria.db"):
        self.sqlite_path = sqlite_path
        self.supabase_db = None
        
        # Intentar conectar con Supabase
        if SUPABASE_AVAILABLE:
            try:
                self.supabase_db = get_supabase_db()
            except Exception as e:
                print(f"No se pudo conectar a Supabase: {e}")
    
    def check_internet_connection(self) -> bool:
        """Verificar si hay conexión a internet"""
        try:
            # Intentar conectar a Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def is_online(self) -> bool:
        """Verificar si hay conexión a Supabase"""
        if not SUPABASE_AVAILABLE or not self.supabase_db:
            return False
        
        if not self.check_internet_connection():
            return False
        
        # Verificar que Supabase responde
        try:
            self.supabase_db.client.table('productos').select('codigo').limit(1).execute()
            return True
        except Exception:
            return False
    
    def sync_producto_to_supabase(self, producto_data: Dict) -> tuple[bool, str]:
        """Sincronizar un producto de SQLite a Supabase
        
        Returns:
            tuple[bool, str]: (éxito, mensaje_error)
        """
        if not self.is_online():
            return False, "Sin conexión a internet"
        
        try:
            # Asegurar que el campo 'codigo' sea la clave primaria para el upsert
            if 'codigo' not in producto_data:
                return False, "Falta el campo 'codigo' en los datos del producto"
            
            # Insertar o actualizar en Supabase
            result = self.supabase_db.client.table('productos').upsert(producto_data, on_conflict='codigo').execute()
            
            if result.data:
                return True, ""
            else:
                return False, "Supabase no retornó datos"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error al sincronizar producto a Supabase: {error_msg}")
            return False, error_msg
    
    def sync_all_productos_to_supabase(self) -> Dict[str, int]:
        """Sincronizar todos los productos de SQLite a Supabase"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión a internet'}
        
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        conn.close()
        
        success = 0
        failed = 0
        
        for producto in productos:
            producto_dict = dict(producto)
            if self.sync_producto_to_supabase(producto_dict):
                success += 1
            else:
                failed += 1
        
        return {'success': success, 'failed': failed}
    
    def sync_producto_from_supabase(self, codigo: str) -> bool:
        """Sincronizar un producto de Supabase a SQLite"""
        if not self.is_online():
            return False
        
        try:
            # Obtener producto de Supabase
            result = self.supabase_db.client.table('productos').select('*').eq('codigo', codigo).execute()
            
            if not result.data:
                return False
            
            producto = result.data[0]
            
            # Actualizar en SQLite
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO productos 
                (codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3, 
                 stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, 
                 stock_maximo, stock_maximo_kg, categoria) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                producto['codigo'], producto['nombre'], producto['precio_compra'], 
                producto['precio_normal'], producto['precio_mayoreo_1'], producto['precio_mayoreo_2'], 
                producto['precio_mayoreo_3'], producto['stock'], producto['tipo_venta'], 
                producto.get('precio_por_kg', 0), producto.get('peso_unitario', 0), 
                producto.get('stock_kg', 0), producto.get('stock_minimo', 10), 
                producto.get('stock_minimo_kg', 0), producto.get('stock_maximo', 0),
                producto.get('stock_maximo_kg', 0), producto.get('categoria', 'cremeria')
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error al sincronizar producto desde Supabase: {e}")
            return False
    
    def sync_all_productos_from_supabase(self) -> Dict[str, int]:
        """Sincronizar todos los productos de Supabase a SQLite"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión a internet'}
        
        try:
            # Obtener todos los productos de Supabase
            result = self.supabase_db.client.table('productos').select('*').execute()
            productos = result.data
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            success = 0
            failed = 0
            
            for producto in productos:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO productos 
                        (codigo, nombre, precio_compra, precio_normal, precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3, 
                         stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg, stock_minimo, stock_minimo_kg, 
                         stock_maximo, stock_maximo_kg, categoria) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        producto['codigo'], producto['nombre'], producto['precio_compra'], 
                        producto['precio_normal'], producto['precio_mayoreo_1'], producto['precio_mayoreo_2'], 
                        producto['precio_mayoreo_3'], producto['stock'], producto['tipo_venta'], 
                        producto.get('precio_por_kg', 0), producto.get('peso_unitario', 0), 
                        producto.get('stock_kg', 0), producto.get('stock_minimo', 10), 
                        producto.get('stock_minimo_kg', 0), producto.get('stock_maximo', 0),
                        producto.get('stock_maximo_kg', 0), producto.get('categoria', 'cremeria')
                    ))
                    success += 1
                except Exception as e:
                    print(f"Error al sincronizar producto {producto['codigo']}: {e}")
                    failed += 1
            
            conn.commit()
            conn.close()
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar productos desde Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    def compare_producto(self, codigo: str) -> Optional[Dict]:
        """Comparar un producto entre SQLite y Supabase"""
        if not self.is_online():
            return None
        
        try:
            # Obtener de SQLite
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
            sqlite_producto = cursor.fetchone()
            conn.close()
            
            # Obtener de Supabase
            result = self.supabase_db.client.table('productos').select('*').eq('codigo', codigo).execute()
            supabase_producto = result.data[0] if result.data else None
            
            if not sqlite_producto and not supabase_producto:
                return None
            
            return {
                'codigo': codigo,
                'exists_sqlite': sqlite_producto is not None,
                'exists_supabase': supabase_producto is not None,
                'sqlite_data': dict(sqlite_producto) if sqlite_producto else None,
                'supabase_data': supabase_producto,
                'different': self._are_different(sqlite_producto, supabase_producto) if sqlite_producto and supabase_producto else True
            }
            
        except Exception as e:
            print(f"Error al comparar producto: {e}")
            return None
    
    def _are_different(self, sqlite_row, supabase_dict) -> bool:
        """Comparar si hay diferencias en campos importantes"""
        if not sqlite_row or not supabase_dict:
            return True
        
        sqlite_dict = dict(sqlite_row)
        
        # Campos a comparar
        campos = ['precio_compra', 'precio_normal', 'precio_mayoreo_1', 'precio_mayoreo_2', 
                  'precio_mayoreo_3', 'stock', 'precio_por_kg', 'stock_kg']
        
        for campo in campos:
            sqlite_val = sqlite_dict.get(campo, 0)
            supabase_val = supabase_dict.get(campo, 0)
            
            # Convertir a float para comparación
            if sqlite_val != supabase_val:
                return True
        
        return False
    
    def auto_sync_after_save(self, codigo: str) -> bool:
        """Sincronización automática después de guardar un producto"""
        if not self.is_online():
            return False
        
        # Obtener datos de SQLite
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
        producto = cursor.fetchone()
        conn.close()
        
        if producto:
            return self.sync_producto_to_supabase(dict(producto))
        
        return False
    
    # ===== SINCRONIZACIÓN ORDENES DE COMPRA =====
    
    def sync_orden_compra_to_supabase(self, orden_data: Dict) -> tuple[bool, str]:
        """Sincronizar una orden de compra a Supabase"""
        if not self.is_online():
            return False, "Sin conexión a internet"
        
        try:
            # Insertar o actualizar en Supabase
            result = self.supabase_db.client.table('ordenes_compra').upsert(orden_data, on_conflict='id').execute()
            
            if result.data:
                return True, ""
            else:
                return False, "Supabase no retornó datos"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error al sincronizar orden de compra a Supabase: {error_msg}")
            return False, error_msg
    
    def sync_all_ordenes_compra_to_supabase(self) -> Dict[str, int]:
        """Sincronizar todas las órdenes de compra a Supabase"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión a internet'}
        
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ordenes_compra")
        ordenes = cursor.fetchall()
        conn.close()
        
        success = 0
        failed = 0
        
        for orden in ordenes:
            orden_dict = dict(orden)
            exito, _ = self.sync_orden_compra_to_supabase(orden_dict)
            if exito:
                success += 1
            else:
                failed += 1
        
        return {'success': success, 'failed': failed}
    
    def sync_ordenes_compra_from_supabase(self) -> Dict[str, int]:
        """Sincronizar órdenes de compra desde Supabase a SQLite"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión a internet'}
        
        try:
            # Obtener datos de Supabase
            result = self.supabase_db.client.table('ordenes_compra').select('*').execute()
            ordenes_supabase = result.data if result.data else []
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            success = 0
            failed = 0
            
            for orden in ordenes_supabase:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO ordenes_compra 
                        (id, fecha_creacion, total_orden, estado, fecha_pago, notas, creado_por)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        orden['id'],
                        orden.get('fecha_creacion'),
                        orden.get('total_orden', 0),
                        orden.get('estado', 'PENDIENTE'),
                        orden.get('fecha_pago'),
                        orden.get('notas'),
                        orden.get('creado_por', 'admin')
                    ))
                    success += 1
                except Exception as e:
                    print(f"Error al sincronizar orden {orden['id']}: {e}")
                    failed += 1
            
            conn.commit()
            conn.close()
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar órdenes desde Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    # ===== SINCRONIZACIÓN PEDIDOS REABASTECIMIENTO =====
    
    def sync_pedido_to_supabase(self, pedido_data: Dict) -> tuple[bool, str]:
        """Sincronizar un pedido de reabastecimiento a Supabase"""
        if not self.is_online():
            return False, "Sin conexión a internet"
        
        try:
            # Insertar o actualizar en Supabase
            result = self.supabase_db.client.table('pedidos_reabastecimiento').upsert(pedido_data, on_conflict='id').execute()
            
            if result.data:
                return True, ""
            else:
                return False, "Supabase no retornó datos"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error al sincronizar pedido a Supabase: {error_msg}")
            return False, error_msg
    
    def sync_all_pedidos_to_supabase(self) -> Dict[str, int]:
        """Sincronizar todos los pedidos de reabastecimiento a Supabase"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión a internet'}
        
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pedidos_reabastecimiento")
        pedidos = cursor.fetchall()
        conn.close()
        
        success = 0
        failed = 0
        
        for pedido in pedidos:
            pedido_dict = dict(pedido)
            exito, _ = self.sync_pedido_to_supabase(pedido_dict)
            if exito:
                success += 1
            else:
                failed += 1
        
        return {'success': success, 'failed': failed}
    
    def sync_pedidos_from_supabase(self) -> Dict[str, int]:
        """Sincronizar pedidos de reabastecimiento desde Supabase a SQLite"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión a internet'}
        
        try:
            # Obtener datos de Supabase
            result = self.supabase_db.client.table('pedidos_reabastecimiento').select('*').execute()
            pedidos_supabase = result.data if result.data else []
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            success = 0
            failed = 0
            
            for pedido in pedidos_supabase:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO pedidos_reabastecimiento 
                        (id, codigo_producto, nombre_producto, stock_actual, stock_minimo, 
                         cantidad_sugerida, cantidad_ordenada, cantidad_recibida, 
                         precio_unitario, costo_total, proveedor, fecha_pedido, 
                         fecha_recepcion, estado, observaciones, orden_compra_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pedido['id'],
                        pedido.get('codigo_producto'),
                        pedido.get('nombre_producto'),
                        pedido.get('stock_actual', 0),
                        pedido.get('stock_minimo', 0),
                        pedido.get('cantidad_sugerida', 0),
                        pedido.get('cantidad_ordenada', 0),
                        pedido.get('cantidad_recibida', 0),
                        pedido.get('precio_unitario', 0),
                        pedido.get('costo_total', 0),
                        pedido.get('proveedor'),
                        pedido.get('fecha_pedido'),
                        pedido.get('fecha_recepcion'),
                        pedido.get('estado', 'PENDIENTE'),
                        pedido.get('observaciones'),
                        pedido.get('orden_compra_id')
                    ))
                    success += 1
                except Exception as e:
                    print(f"Error al sincronizar pedido {pedido['id']}: {e}")
                    failed += 1
            
            conn.commit()
            conn.close()
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar pedidos desde Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    # ===== SINCRONIZACIÓN VENTAS =====
    
    def sync_venta_to_supabase(self, venta_data: Dict) -> tuple[bool, str]:
        """Sincronizar una venta a Supabase"""
        if not self.is_online():
            return False, "Sin conexión a internet"
        
        try:
            # Insertar o actualizar en Supabase
            result = self.supabase_db.client.table('ventas').upsert(venta_data, on_conflict='id').execute()
            
            if result.data:
                return True, ""
            else:
                return False, "Supabase no retornó datos"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error al sincronizar venta a Supabase: {error_msg}")
            return False, error_msg
    
    def sync_all_ventas_to_supabase(self) -> Dict[str, int]:
        """Sincronizar todas las ventas de SQLite a Supabase"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ventas")
            ventas = cursor.fetchall()
            conn.close()
            
            success = 0
            failed = 0
            
            for venta in ventas:
                venta_dict = dict(venta)
                resultado, _ = self.sync_venta_to_supabase(venta_dict)
                if resultado:
                    success += 1
                else:
                    failed += 1
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar ventas a Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    def sync_ventas_from_supabase(self) -> Dict[str, int]:
        """Sincronizar ventas desde Supabase a SQLite"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            # Obtener todas las ventas de Supabase
            response = self.supabase_db.client.table('ventas').select('*').execute()
            ventas = response.data
            
            if not ventas:
                return {'success': 0, 'failed': 0, 'message': 'No hay ventas en Supabase'}
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            success = 0
            failed = 0
            
            for venta in ventas:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO ventas 
                        (id, fecha, codigo, nombre, cantidad, precio_unitario, total, tipo_cliente, tipos_pago,
                         monto_efectivo, monto_tarjeta, monto_transferencia, monto_credito,
                         fecha_vencimiento_credito, hora_vencimiento_credito, cliente_credito, pagado, 
                         alerta_mostrada, peso_vendido, tipo_venta)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        venta.get('id'),
                        venta.get('fecha'),
                        venta.get('codigo'),
                        venta.get('nombre'),
                        venta.get('cantidad'),
                        venta.get('precio_unitario'),
                        venta.get('total'),
                        venta.get('tipo_cliente'),
                        venta.get('tipos_pago'),
                        venta.get('monto_efectivo', 0),
                        venta.get('monto_tarjeta', 0),
                        venta.get('monto_transferencia', 0),
                        venta.get('monto_credito', 0),
                        venta.get('fecha_vencimiento_credito'),
                        venta.get('hora_vencimiento_credito', '15:00'),
                        venta.get('cliente_credito', ''),
                        venta.get('pagado', 1),
                        venta.get('alerta_mostrada', 0),
                        venta.get('peso_vendido', 0),
                        venta.get('tipo_venta', 'unidad')
                    ))
                    success += 1
                except Exception as e:
                    print(f"Error al insertar venta {venta.get('id')}: {e}")
                    failed += 1
            
            conn.commit()
            conn.close()
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar ventas desde Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    # ===== SINCRONIZACIÓN EGRESOS ADICIONALES =====
    
    def sync_egreso_to_supabase(self, egreso_data: Dict) -> tuple[bool, str]:
        """Sincronizar un egreso adicional a Supabase"""
        if not self.is_online():
            return False, "Sin conexión a internet"
        
        try:
            result = self.supabase_db.client.table('egresos_adicionales').upsert(egreso_data, on_conflict='id').execute()
            
            if result.data:
                return True, ""
            else:
                return False, "Supabase no retornó datos"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error al sincronizar egreso a Supabase: {error_msg}")
            return False, error_msg
    
    def sync_all_egresos_to_supabase(self) -> Dict[str, int]:
        """Sincronizar todos los egresos de SQLite a Supabase"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM egresos_adicionales")
            egresos = cursor.fetchall()
            conn.close()
            
            success = 0
            failed = 0
            
            for egreso in egresos:
                egreso_dict = dict(egreso)
                resultado, _ = self.sync_egreso_to_supabase(egreso_dict)
                if resultado:
                    success += 1
                else:
                    failed += 1
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar egresos a Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    def sync_egresos_from_supabase(self) -> Dict[str, int]:
        """Sincronizar egresos desde Supabase a SQLite"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            response = self.supabase_db.client.table('egresos_adicionales').select('*').execute()
            egresos = response.data
            
            if not egresos:
                return {'success': 0, 'failed': 0, 'message': 'No hay egresos en Supabase'}
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            success = 0
            failed = 0
            
            for egreso in egresos:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO egresos_adicionales 
                        (id, fecha, tipo, descripcion, monto, observaciones, usuario)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        egreso.get('id'),
                        egreso.get('fecha'),
                        egreso.get('tipo'),
                        egreso.get('descripcion'),
                        egreso.get('monto'),
                        egreso.get('observaciones'),
                        egreso.get('usuario', 'Sistema')
                    ))
                    success += 1
                except Exception as e:
                    print(f"Error al insertar egreso {egreso.get('id')}: {e}")
                    failed += 1
            
            conn.commit()
            conn.close()
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar egresos desde Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    # ===== SINCRONIZACIÓN INGRESOS PASIVOS =====
    
    def sync_ingreso_to_supabase(self, ingreso_data: Dict) -> tuple[bool, str]:
        """Sincronizar un ingreso pasivo a Supabase"""
        if not self.is_online():
            return False, "Sin conexión a internet"
        
        try:
            result = self.supabase_db.client.table('ingresos_pasivos').upsert(ingreso_data, on_conflict='id').execute()
            
            if result.data:
                return True, ""
            else:
                return False, "Supabase no retornó datos"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error al sincronizar ingreso a Supabase: {error_msg}")
            return False, error_msg
    
    def sync_all_ingresos_to_supabase(self) -> Dict[str, int]:
        """Sincronizar todos los ingresos de SQLite a Supabase"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ingresos_pasivos")
            ingresos = cursor.fetchall()
            conn.close()
            
            success = 0
            failed = 0
            
            for ingreso in ingresos:
                ingreso_dict = dict(ingreso)
                resultado, _ = self.sync_ingreso_to_supabase(ingreso_dict)
                if resultado:
                    success += 1
                else:
                    failed += 1
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar ingresos a Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    def sync_ingresos_from_supabase(self) -> Dict[str, int]:
        """Sincronizar ingresos desde Supabase a SQLite"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            response = self.supabase_db.client.table('ingresos_pasivos').select('*').execute()
            ingresos = response.data
            
            if not ingresos:
                return {'success': 0, 'failed': 0, 'message': 'No hay ingresos en Supabase'}
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            success = 0
            failed = 0
            
            for ingreso in ingresos:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO ingresos_pasivos 
                        (id, fecha, descripcion, monto, observaciones, usuario)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        ingreso.get('id'),
                        ingreso.get('fecha'),
                        ingreso.get('descripcion'),
                        ingreso.get('monto'),
                        ingreso.get('observaciones'),
                        ingreso.get('usuario', 'Sistema')
                    ))
                    success += 1
                except Exception as e:
                    print(f"Error al insertar ingreso {ingreso.get('id')}: {e}")
                    failed += 1
            
            conn.commit()
            conn.close()
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar ingresos desde Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    # ===== SINCRONIZACIÓN CRÉDITOS PENDIENTES =====
    
    def sync_credito_to_supabase(self, credito_data: Dict) -> tuple[bool, str]:
        """Sincronizar un crédito pendiente a Supabase"""
        if not self.is_online():
            return False, "Sin conexión a internet"
        
        try:
            result = self.supabase_db.client.table('creditos_pendientes').upsert(credito_data, on_conflict='id').execute()
            
            if result.data:
                return True, ""
            else:
                return False, "Supabase no retornó datos"
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error al sincronizar crédito a Supabase: {error_msg}")
            return False, error_msg
    
    def sync_all_creditos_to_supabase(self) -> Dict[str, int]:
        """Sincronizar todos los créditos de SQLite a Supabase"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM creditos_pendientes")
            creditos = cursor.fetchall()
            conn.close()
            
            success = 0
            failed = 0
            
            for credito in creditos:
                credito_dict = dict(credito)
                resultado, _ = self.sync_credito_to_supabase(credito_dict)
                if resultado:
                    success += 1
                else:
                    failed += 1
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar créditos a Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    def sync_creditos_from_supabase(self) -> Dict[str, int]:
        """Sincronizar créditos desde Supabase a SQLite"""
        if not self.is_online():
            return {'success': 0, 'failed': 0, 'error': 'Sin conexión'}
        
        try:
            response = self.supabase_db.client.table('creditos_pendientes').select('*').execute()
            creditos = response.data
            
            if not creditos:
                return {'success': 0, 'failed': 0, 'message': 'No hay créditos en Supabase'}
            
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            success = 0
            failed = 0
            
            for credito in creditos:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO creditos_pendientes 
                        (id, venta_id, cliente, monto, fecha_credito, fecha_vencimiento, hora_vencimiento, estado, alerta_mostrada)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        credito.get('id'),
                        credito.get('venta_id'),
                        credito.get('cliente'),
                        credito.get('monto'),
                        credito.get('fecha_credito'),
                        credito.get('fecha_vencimiento'),
                        credito.get('hora_vencimiento', '15:00'),
                        credito.get('estado', 'pendiente'),
                        credito.get('alerta_mostrada', 0)
                    ))
                    success += 1
                except Exception as e:
                    print(f"Error al insertar crédito {credito.get('id')}: {e}")
                    failed += 1
            
            conn.commit()
            conn.close()
            
            return {'success': success, 'failed': failed}
            
        except Exception as e:
            print(f"Error al sincronizar créditos desde Supabase: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}

# Instancia global del gestor de sincronización
_sync_manager = None

def get_sync_manager() -> SyncManager:
    """Obtener instancia del gestor de sincronización"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager
