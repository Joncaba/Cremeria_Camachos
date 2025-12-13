"""
Adaptador de base de datos - Wrapper unificado para SQLite y Supabase
Permite migración gradual sin romper la funcionalidad existente
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Detectar qué base de datos usar
USE_SUPABASE = os.getenv('USE_SUPABASE', 'false').lower() == 'true'

if USE_SUPABASE:
    try:
        from supabase_client import get_db as get_supabase_db
        # Usando Supabase como base de datos
    except ImportError:
        # Supabase no disponible, usando SQLite
        USE_SUPABASE = False

if not USE_SUPABASE:
    import sqlite3
    DB_PATH = "pos_cremeria.db"
    # Usando SQLite local


class DatabaseAdapter:
    """Adaptador universal para SQLite y Supabase"""
    
    def __init__(self):
        self.use_supabase = USE_SUPABASE
        if self.use_supabase:
            self.db = get_supabase_db()
        else:
            self.conn = None
    
    def _get_sqlite_conn(self):
        """Obtener conexión SQLite (reutilizable)"""
        if not self.conn:
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    # ==================== PRODUCTOS ====================
    
    def obtener_productos(self) -> List[Dict]:
        """Obtener todos los productos"""
        if self.use_supabase:
            return self.db.obtener_productos()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos")
            return [dict(row) for row in cursor.fetchall()]
    
    def obtener_producto(self, codigo: str) -> Optional[Dict]:
        """Obtener un producto por código"""
        if self.use_supabase:
            return self.db.obtener_producto_por_codigo(codigo)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def insertar_producto(self, producto: Dict) -> bool:
        """Insertar un nuevo producto"""
        if self.use_supabase:
            try:
                self.db.insertar_producto(producto)
                return True
            except:
                return False
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO productos (codigo, nombre, precio_normal, precio_mayoreo_1, 
                                          stock, precio_compra, precio_mayoreo_2, precio_mayoreo_3,
                                          stock_minimo, tipo_venta, precio_por_kg, peso_unitario,
                                          stock_kg, stock_minimo_kg, categoria, stock_maximo, stock_maximo_kg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    producto.get('codigo'), producto.get('nombre'), producto.get('precio_normal'),
                    producto.get('precio_mayoreo_1'), producto.get('stock', 0), 
                    producto.get('precio_compra', 0), producto.get('precio_mayoreo_2', 0),
                    producto.get('precio_mayoreo_3', 0), producto.get('stock_minimo', 10),
                    producto.get('tipo_venta', 'unidad'), producto.get('precio_por_kg', 0),
                    producto.get('peso_unitario', 0), producto.get('stock_kg', 0),
                    producto.get('stock_minimo_kg', 0), producto.get('categoria', 'cremeria'),
                    producto.get('stock_maximo', 0), producto.get('stock_maximo_kg', 0)
                ))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
    
    def actualizar_producto(self, codigo: str, datos: Dict) -> bool:
        """Actualizar un producto existente"""
        if self.use_supabase:
            try:
                self.db.actualizar_producto(codigo, datos)
                return True
            except:
                return False
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                # Construir SET dinámicamente
                sets = ", ".join([f"{k} = ?" for k in datos.keys()])
                valores = list(datos.values()) + [codigo]
                cursor.execute(f"UPDATE productos SET {sets} WHERE codigo = ?", valores)
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
    
    def eliminar_producto(self, codigo: str) -> bool:
        """Eliminar un producto"""
        if self.use_supabase:
            return self.db.eliminar_producto(codigo)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM productos WHERE codigo = ?", (codigo,))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
    
    def actualizar_stock(self, codigo: str, nuevo_stock: float, nuevo_stock_kg: float = None) -> bool:
        """Actualizar stock de un producto"""
        datos = {'stock': nuevo_stock}
        if nuevo_stock_kg is not None:
            datos['stock_kg'] = nuevo_stock_kg
        return self.actualizar_producto(codigo, datos)
    
    # ==================== VENTAS ====================
    
    def insertar_venta(self, venta: Dict) -> bool:
        """Registrar una nueva venta"""
        if self.use_supabase:
            try:
                self.db.insertar_venta(venta)
                return True
            except:
                return False
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO ventas (fecha, codigo, nombre, cantidad, precio_unitario, total,
                                       tipo_cliente, tipo_pago, tipos_pago, monto_efectivo,
                                       monto_tarjeta, monto_transferencia, peso_vendido, tipo_venta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    venta.get('fecha'), venta.get('codigo'), venta.get('nombre'),
                    venta.get('cantidad'), venta.get('precio_unitario'), venta.get('total'),
                    venta.get('tipo_cliente'), venta.get('tipo_pago'), venta.get('tipos_pago'),
                    venta.get('monto_efectivo', 0), venta.get('monto_tarjeta', 0),
                    venta.get('monto_transferencia', 0), venta.get('peso_vendido', 0),
                    venta.get('tipo_venta', 'unidad')
                ))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al insertar venta: {e}")
                conn.rollback()
                return False
    
    def obtener_ventas(self, limite: int = 100, fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict]:
        """Obtener ventas con filtros opcionales"""
        if self.use_supabase:
            return self.db.obtener_ventas(limite, fecha_inicio, fecha_fin)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            query = "SELECT * FROM ventas WHERE 1=1"
            params = []
            
            if fecha_inicio:
                query += " AND fecha >= ?"
                params.append(fecha_inicio)
            if fecha_fin:
                query += " AND fecha <= ?"
                params.append(fecha_fin)
            
            query += " ORDER BY fecha DESC, id DESC LIMIT ?"
            params.append(limite)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def obtener_total_ventas(self, fecha_inicio: str = None, fecha_fin: str = None) -> float:
        """Obtener total de ventas en un período"""
        if self.use_supabase:
            return self.db.obtener_total_ventas(fecha_inicio, fecha_fin)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            query = "SELECT SUM(total) as total FROM ventas WHERE 1=1"
            params = []
            
            if fecha_inicio:
                query += " AND fecha >= ?"
                params.append(fecha_inicio)
            if fecha_fin:
                query += " AND fecha <= ?"
                params.append(fecha_fin)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['total'] if result and result['total'] else 0.0
    
    # ==================== USUARIOS ====================
    
    def obtener_usuarios(self) -> List[Dict]:
        """Obtener todos los usuarios"""
        if self.use_supabase:
            return self.db.obtener_usuarios()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios_admin")
            return [dict(row) for row in cursor.fetchall()]
    
    def obtener_usuario(self, usuario: str) -> Optional[Dict]:
        """Obtener un usuario por nombre"""
        if self.use_supabase:
            return self.db.obtener_usuario(usuario)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT id, usuario, password, activo, rol FROM usuarios WHERE usuario = ?", (usuario,))
            row = cursor.fetchone()
            if row:
                # Convertir sqlite3.Row a diccionario
                return {
                    'id': row[0],
                    'usuario': row[1],
                    'password': row[2],
                    'activo': row[3],
                    'rol': row[4]
                }
            return None
    
    def insertar_usuario(self, usuario: Dict) -> bool:
        """Crear un nuevo usuario"""
        if self.use_supabase:
            try:
                self.db.insertar_usuario(usuario)
                return True
            except:
                return False
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO usuarios_admin (usuario, password, nombre_completo, rol, activo, creado_por)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    usuario.get('usuario'), usuario.get('password'), usuario.get('nombre_completo'),
                    usuario.get('rol', 'usuario'), usuario.get('activo', 1), usuario.get('creado_por', 'Sistema')
                ))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
    
    # ==================== TURNOS ====================
    
    def obtener_turnos(self) -> List[Dict]:
        """Obtener todos los turnos"""
        if self.use_supabase:
            return self.db.obtener_turnos()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM turnos ORDER BY turno")
            return [dict(row) for row in cursor.fetchall()]
    
    def insertar_turno(self, turno: Dict) -> bool:
        """Registrar un nuevo turno"""
        if self.use_supabase:
            try:
                self.db.insertar_turno(turno)
                return True
            except:
                return False
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO turnos (empleado, turno, timestamp)
                    VALUES (?, ?, ?)
                """, (turno.get('empleado'), turno.get('turno'), turno.get('timestamp')))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
    
    # ==================== FINANZAS ====================
    
    def obtener_egresos(self, fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict]:
        """Obtener egresos adicionales"""
        if self.use_supabase:
            return self.db.obtener_egresos(fecha_inicio, fecha_fin)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            query = "SELECT * FROM egresos_adicionales WHERE 1=1"
            params = []
            
            if fecha_inicio:
                query += " AND fecha >= ?"
                params.append(fecha_inicio)
            if fecha_fin:
                query += " AND fecha <= ?"
                params.append(fecha_fin)
            
            query += " ORDER BY fecha DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def insertar_egreso(self, egreso: Dict) -> bool:
        """Registrar un nuevo egreso"""
        if self.use_supabase:
            try:
                self.db.insertar_egreso(egreso)
                return True
            except:
                return False
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO egresos_adicionales (fecha, tipo, descripcion, monto, observaciones, usuario)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    egreso.get('fecha'), egreso.get('tipo'), egreso.get('descripcion'),
                    egreso.get('monto'), egreso.get('observaciones', ''), egreso.get('usuario', 'Sistema')
                ))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
    
    def obtener_ingresos_pasivos(self, fecha_inicio: str = None, fecha_fin: str = None) -> List[Dict]:
        """Obtener ingresos pasivos"""
        if self.use_supabase:
            return self.db.obtener_ingresos_pasivos(fecha_inicio, fecha_fin)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            query = "SELECT * FROM ingresos_pasivos WHERE 1=1"
            params = []
            
            if fecha_inicio:
                query += " AND fecha >= ?"
                params.append(fecha_inicio)
            if fecha_fin:
                query += " AND fecha <= ?"
                params.append(fecha_fin)
            
            query += " ORDER BY fecha DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def insertar_ingreso_pasivo(self, ingreso: Dict) -> bool:
        """Registrar un nuevo ingreso pasivo"""
        if self.use_supabase:
            try:
                self.db.insertar_ingreso_pasivo(ingreso)
                return True
            except:
                return False
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO ingresos_pasivos (fecha, descripcion, monto, observaciones, usuario)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    ingreso.get('fecha'), ingreso.get('descripcion'), ingreso.get('monto'),
                    ingreso.get('observaciones', ''), ingreso.get('usuario', 'Sistema')
                ))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False


# Instancia global
_adapter = None

def get_db_adapter() -> DatabaseAdapter:
    """Obtener instancia única del adaptador"""
    global _adapter
    if _adapter is None:
        _adapter = DatabaseAdapter()
    return _adapter
