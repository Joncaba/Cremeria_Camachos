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

# Instancia global del gestor de sincronización
_sync_manager = None

def get_sync_manager() -> SyncManager:
    """Obtener instancia del gestor de sincronización"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager
