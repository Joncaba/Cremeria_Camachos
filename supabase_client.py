"""
Cliente de Supabase para la aplicación de Punto de Venta
Reemplaza las conexiones SQLite con Supabase (PostgreSQL)
"""
import streamlit as st
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import os

def get_supabase_client() -> Client:
    """
    Obtener cliente de Supabase configurado
    
    Returns:
        Client: Cliente de Supabase autenticado
    """
    try:
        # Intentar obtener desde secrets.toml
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except (KeyError, FileNotFoundError):
        # Fallback a variables de entorno
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(
                "Credenciales de Supabase no encontradas. "
                "Configura secrets.toml o variables de entorno."
            )
    
    return create_client(url, key)

class SupabaseDB:
    """Clase para manejar operaciones de base de datos con Supabase"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    # ==================== PRODUCTOS ====================
    
    def obtener_productos(self) -> List[Dict]:
        """Obtener todos los productos"""
        response = self.client.table('productos').select('*').execute()
        return response.data
    
    def obtener_producto_por_codigo(self, codigo: str) -> Optional[Dict]:
        """Obtener un producto por código"""
        response = self.client.table('productos')\
            .select('*')\
            .eq('codigo', codigo)\
            .execute()
        return response.data[0] if response.data else None
    
    def insertar_producto(self, producto: Dict) -> Dict:
        """Insertar un nuevo producto"""
        response = self.client.table('productos').insert(producto).execute()
        return response.data[0]
    
    def actualizar_producto(self, codigo: str, datos: Dict) -> Dict:
        """Actualizar un producto existente"""
        response = self.client.table('productos')\
            .update(datos)\
            .eq('codigo', codigo)\
            .execute()
        return response.data[0] if response.data else None
    
    def eliminar_producto(self, codigo: str) -> bool:
        """Eliminar un producto"""
        response = self.client.table('productos')\
            .delete()\
            .eq('codigo', codigo)\
            .execute()
        return len(response.data) > 0
    
    def actualizar_stock(self, codigo: str, nuevo_stock: float, 
                        nuevo_stock_kg: float = None) -> Dict:
        """Actualizar stock de un producto"""
        datos = {'stock': nuevo_stock}
        if nuevo_stock_kg is not None:
            datos['stock_kg'] = nuevo_stock_kg
        return self.actualizar_producto(codigo, datos)
    
    # ==================== VENTAS ====================
    
    def insertar_venta(self, venta: Dict) -> Dict:
        """Registrar una nueva venta"""
        response = self.client.table('ventas').insert(venta).execute()
        return response.data[0]
    
    def obtener_ventas(self, limite: int = 100, 
                       fecha_inicio: str = None,
                       fecha_fin: str = None) -> List[Dict]:
        """Obtener ventas con filtros opcionales"""
        query = self.client.table('ventas').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        
        response = query.order('fecha', desc=True)\
            .order('id', desc=True)\
            .limit(limite)\
            .execute()
        return response.data
    
    def obtener_venta_por_id(self, venta_id: int) -> Optional[Dict]:
        """Obtener una venta por ID"""
        response = self.client.table('ventas')\
            .select('*')\
            .eq('id', venta_id)\
            .execute()
        return response.data[0] if response.data else None
    
    def obtener_total_ventas(self, fecha_inicio: str = None,
                            fecha_fin: str = None) -> float:
        """Obtener total de ventas en un período"""
        query = self.client.table('ventas').select('total')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        
        response = query.execute()
        return sum(v['total'] for v in response.data if v['total'])
    
    # ==================== USUARIOS ====================
    
    def obtener_usuarios(self) -> List[Dict]:
        """Obtener todos los usuarios"""
        response = self.client.table('usuarios_admin').select('*').execute()
        return response.data
    
    def obtener_usuario(self, usuario: str) -> Optional[Dict]:
        """Obtener un usuario por nombre de usuario"""
        response = self.client.table('usuarios_admin')\
            .select('*')\
            .eq('usuario', usuario)\
            .execute()
        return response.data[0] if response.data else None
    
    def insertar_usuario(self, usuario: Dict) -> Dict:
        """Crear un nuevo usuario"""
        response = self.client.table('usuarios_admin').insert(usuario).execute()
        return response.data[0]
    
    def actualizar_usuario(self, usuario: str, datos: Dict) -> Dict:
        """Actualizar un usuario"""
        response = self.client.table('usuarios_admin')\
            .update(datos)\
            .eq('usuario', usuario)\
            .execute()
        return response.data[0] if response.data else None
    
    def actualizar_ultimo_acceso(self, usuario: str, timestamp: str) -> Dict:
        """Actualizar último acceso de un usuario"""
        return self.actualizar_usuario(usuario, {'ultimo_acceso': timestamp})
    
    # ==================== TURNOS ====================
    
    def obtener_turnos(self) -> List[Dict]:
        """Obtener todos los turnos"""
        response = self.client.table('turnos')\
            .select('*')\
            .order('turno')\
            .execute()
        return response.data
    
    def insertar_turno(self, turno: Dict) -> Dict:
        """Registrar un nuevo turno"""
        response = self.client.table('turnos').insert(turno).execute()
        return response.data[0]
    
    # ==================== CRÉDITOS ====================
    
    def obtener_creditos_pendientes(self) -> List[Dict]:
        """Obtener créditos pendientes"""
        response = self.client.table('creditos_pendientes')\
            .select('*')\
            .eq('pagado', 0)\
            .execute()
        return response.data
    
    def insertar_credito(self, credito: Dict) -> Dict:
        """Registrar un nuevo crédito"""
        response = self.client.table('creditos_pendientes')\
            .insert(credito)\
            .execute()
        return response.data[0]
    
    def marcar_credito_pagado(self, credito_id: int) -> Dict:
        """Marcar un crédito como pagado"""
        response = self.client.table('creditos_pendientes')\
            .update({'pagado': 1})\
            .eq('id', credito_id)\
            .execute()
        return response.data[0] if response.data else None
    
    # ==================== EGRESOS ====================
    
    def obtener_egresos(self, fecha_inicio: str = None,
                       fecha_fin: str = None) -> List[Dict]:
        """Obtener egresos adicionales"""
        query = self.client.table('egresos_adicionales').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        
        response = query.order('fecha', desc=True).execute()
        return response.data
    
    def insertar_egreso(self, egreso: Dict) -> Dict:
        """Registrar un nuevo egreso"""
        response = self.client.table('egresos_adicionales')\
            .insert(egreso)\
            .execute()
        return response.data[0]
    
    # ==================== INGRESOS PASIVOS ====================
    
    def obtener_ingresos_pasivos(self, fecha_inicio: str = None,
                                 fecha_fin: str = None) -> List[Dict]:
        """Obtener ingresos pasivos"""
        query = self.client.table('ingresos_pasivos').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        
        response = query.order('fecha', desc=True).execute()
        return response.data
    
    def insertar_ingreso_pasivo(self, ingreso: Dict) -> Dict:
        """Registrar un nuevo ingreso pasivo"""
        response = self.client.table('ingresos_pasivos')\
            .insert(ingreso)\
            .execute()
        return response.data[0]
    
    # ==================== PEDIDOS ====================
    
    def obtener_pedidos(self, estado: str = None) -> List[Dict]:
        """Obtener pedidos de reabastecimiento"""
        query = self.client.table('pedidos_reabastecimiento').select('*')
        
        if estado:
            query = query.eq('estado', estado)
        
        response = query.order('fecha_pedido', desc=True).execute()
        return response.data
    
    def insertar_pedido(self, pedido: Dict) -> Dict:
        """Crear un nuevo pedido"""
        response = self.client.table('pedidos_reabastecimiento')\
            .insert(pedido)\
            .execute()
        return response.data[0]
    
    def actualizar_pedido(self, pedido_id: int, datos: Dict) -> Dict:
        """Actualizar un pedido existente"""
        response = self.client.table('pedidos_reabastecimiento')\
            .update(datos)\
            .eq('id', pedido_id)\
            .execute()
        return response.data[0] if response.data else None

# Instancia global (singleton)
_db_instance = None

def get_db() -> SupabaseDB:
    """Obtener instancia única de SupabaseDB"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance
