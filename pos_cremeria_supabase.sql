-- PostgreSQL Database Dump para Supabase
-- Convertido desde SQLite: pos_cremeria.db
-- Date: 2025-11-16 23:29:35
-- Compatible con PostgreSQL/Supabase

-- Eliminar tablas si existen
DROP TABLE IF EXISTS creditos_pendientes CASCADE;
DROP TABLE IF EXISTS egresos_adicionales CASCADE;
DROP TABLE IF EXISTS ingresos_pasivos CASCADE;
DROP TABLE IF EXISTS pedidos_reabastecimiento CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS turnos CASCADE;
DROP TABLE IF EXISTS usuarios_admin CASCADE;
DROP TABLE IF EXISTS ventas CASCADE;

-- Tabla: productos
CREATE TABLE productos (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio_normal DECIMAL(10,2) NOT NULL,
    precio_mayoreo_1 DECIMAL(10,2) NOT NULL,
    stock INTEGER NOT NULL,
    precio_compra DECIMAL(10,2) DEFAULT 0,
    precio_mayoreo_2 DECIMAL(10,2) DEFAULT 0,
    precio_mayoreo_3 DECIMAL(10,2) DEFAULT 0,
    stock_minimo INTEGER DEFAULT 10,
    tipo_venta TEXT DEFAULT 'unidad',
    precio_por_kg DECIMAL(10,2) DEFAULT 0,
    peso_unitario DECIMAL(10,3) DEFAULT 0,
    stock_kg DECIMAL(10,3) DEFAULT 0,
    stock_minimo_kg DECIMAL(10,3) DEFAULT 0,
    categoria TEXT DEFAULT 'cremeria',
    stock_maximo INTEGER DEFAULT 0,
    stock_maximo_kg DECIMAL(10,3) DEFAULT 0
);

-- Tabla: usuarios_admin
CREATE TABLE usuarios_admin (
    id SERIAL PRIMARY KEY,
    usuario TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT DEFAULT 'usuario',
    activo INTEGER DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP,
    creado_por TEXT DEFAULT 'Sistema'
);

-- Tabla: ventas
CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP,
    codigo TEXT,
    nombre TEXT,
    cantidad INTEGER,
    precio_unitario DECIMAL(10,2),
    total DECIMAL(10,2),
    tipo_cliente TEXT,
    tipo_pago TEXT DEFAULT 'Efectivo',
    fecha_vencimiento_credito TEXT,
    cliente_credito TEXT,
    pagado INTEGER DEFAULT 1,
    tipos_pago TEXT DEFAULT 'Efectivo',
    monto_efectivo DECIMAL(10,2) DEFAULT 0,
    monto_tarjeta DECIMAL(10,2) DEFAULT 0,
    monto_transferencia DECIMAL(10,2) DEFAULT 0,
    monto_credito DECIMAL(10,2) DEFAULT 0,
    hora_vencimiento_credito TEXT DEFAULT '15:00',
    alerta_mostrada INTEGER DEFAULT 0,
    peso_vendido DECIMAL(10,3) DEFAULT 0,
    tipo_venta TEXT DEFAULT 'unidad'
);

-- Tabla: creditos_pendientes
CREATE TABLE creditos_pendientes (
    id SERIAL PRIMARY KEY,
    cliente TEXT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_venta TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    venta_id INTEGER,
    pagado INTEGER DEFAULT 0,
    hora_vencimiento TEXT DEFAULT '15:00',
    alerta_mostrada INTEGER DEFAULT 0,
    FOREIGN KEY (venta_id) REFERENCES ventas (id) ON DELETE SET NULL
);

-- Tabla: egresos_adicionales
CREATE TABLE egresos_adicionales (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    observaciones TEXT,
    usuario TEXT DEFAULT 'Sistema'
);

-- Tabla: ingresos_pasivos
CREATE TABLE ingresos_pasivos (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    observaciones TEXT,
    usuario TEXT DEFAULT 'Sistema'
);

-- Tabla: pedidos_reabastecimiento
CREATE TABLE pedidos_reabastecimiento (
    id SERIAL PRIMARY KEY,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    cantidad_solicitada DECIMAL(10,3) NOT NULL,
    cantidad_recibida DECIMAL(10,3) DEFAULT 0,
    precio_unitario DECIMAL(10,2) NOT NULL,
    costo_total DECIMAL(10,2) NOT NULL,
    proveedor TEXT DEFAULT '',
    fecha_pedido TEXT NOT NULL,
    fecha_entrega_esperada TEXT,
    fecha_entrega_real TEXT,
    estado TEXT DEFAULT 'PENDIENTE',
    completado INTEGER DEFAULT 0,
    notas TEXT DEFAULT '',
    creado_por TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(codigo_producto) REFERENCES productos(codigo) ON DELETE CASCADE
);

-- Tabla: turnos
CREATE TABLE turnos (
    id SERIAL PRIMARY KEY,
    empleado TEXT NOT NULL,
    turno INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

-- Insertar datos en productos
INSERT INTO productos VALUES
('11111','Yogurt Natural',28.0,27.0,20,22.0,26.0,25.0,10,'unidad',0.0,0.0,0.0,0.0,'cremeria',0,0.0),
('44444','Queso',150.0,142.5,7,100.0,135.0,127.5,2,'granel',150.0,3.0,21.0,0.0,'cremeria',0,0.0),
('66666','Salchicha de pavo',27.0,25.65,0,20.0,24.84,24.3,0,'granel',27.0,0.0,20.0,4.0,'cremeria',0,0.0),
('200006500','Queso Cotija',142.0,134.9,-3,130.0,130.64,127.8,0,'granel',142.0,0.0,8.635,2.0,'cremeria',0,0.0),
('33333','Piña',39.0,37.0,15,30.0,36.0,35.0,5,'unidad',0.0,0.0,0.0,0.0,'abarrotes',0,0.0),
('20803010','Yogurt Yoplay Durazno',49.0,0.0,17,39.0,0.0,0.0,5,'unidad',0.0,0.0,0.0,0.0,'cremeria',0,0.0),
('22222','Jalapeños 105g',36.0,35.0,15,30.0,34.0,33.0,5,'unidad',0.0,0.0,0.0,0.0,'abarrotes',0,0.0),
('200000300','Jamon Pierna Andalucia',125.0,118.75,-3,100.0,115.0,112.5,0,'granel',125.0,0.0,14.115,2.0,'cremeria',0,0.0),
('20001400','Huevo Blanco',42.0,39.9,-1,39.0,38.64,37.8,0,'granel',42.0,0.0,38.125,5.0,'cremeria',0,0.0),
('20004010','Galleta Campechana',63.0,59.0,18,58.0,57.0,56.0,5,'unidad',0.0,0.0,0.0,0.0,'abarrotes',0,0.0),
('20001050','Crema Robles',72.0,68.4,-1,60.0,66.24,64.8,0,'granel',72.0,0.0,18.895,4.0,'cremeria',0,0.0),
('200005200','Queso Panela',110.0,104.5,-2,90.0,101.2,99.0,0,'granel',110.0,0.0,0.0,2.0,'cremeria',0,0.0);

-- Insertar datos en usuarios_admin
INSERT INTO usuarios_admin (id, usuario, password, nombre_completo, rol, activo, fecha_creacion, ultimo_acceso, creado_por) VALUES
(1,'admin','240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9','Administrador Principal','admin',1,'2025-11-03 16:49:57','2025-11-16 00:28:58','Migración'),
(2,'creme','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','Cremeria Camachos','usuario',1,'2025-11-04 16:46:28','2025-11-04 16:46:41','admin');

-- Ajustar secuencia de usuarios_admin
SELECT setval('usuarios_admin_id_seq', (SELECT MAX(id) FROM usuarios_admin));

-- Insertar datos en ventas
INSERT INTO ventas (id, fecha, codigo, nombre, cantidad, precio_unitario, total, tipo_cliente, tipo_pago, fecha_vencimiento_credito, cliente_credito, pagado, tipos_pago, monto_efectivo, monto_tarjeta, monto_transferencia, monto_credito, hora_vencimiento_credito, alerta_mostrada, peso_vendido, tipo_venta) VALUES
(1,'2025-11-10 03:39:40','20001400','Huevo Blanco (1.875 Kg)',1,42.0,78.75,'Normal','Efectivo','','',1,'Efectivo',428.31,0.0,0.0,0.0,'15:00',0,1.875,'granel'),
(2,'2025-11-10 03:39:40','20004010','Galleta Campechana',2,63.0,126.0,'Normal','Efectivo','','',1,'Efectivo',428.31,0.0,0.0,0.0,'15:00',0,0.0,'unidad'),
(3,'2025-11-10 03:39:40','20001050','Crema Robles (3.105 Kg)',1,72.0,223.56,'Normal','Efectivo','','',1,'Efectivo',428.31,0.0,0.0,0.0,'15:00',0,3.105,'granel'),
(4,'2025-11-13 02:40:22','200006500','Queso Cotija (0.455 Kg)',1,142.0,64.61,'Normal','Efectivo','','',1,'Efectivo, Tarjeta',100.0,50.49,0.0,0.0,'15:00',0,0.455,'granel'),
(5,'2025-11-13 02:40:22','200000300','Jamon Pierna Andalucia (0.295 Kg)',1,125.0,36.875,'Normal','Efectivo','','',1,'Efectivo, Tarjeta',100.0,50.49,0.0,0.0,'15:00',0,0.295,'granel'),
(6,'2025-11-13 02:40:22','20803010','Yogurt Yoplay Durazno',1,49.0,49.0,'Normal','Efectivo','','',1,'Efectivo, Tarjeta',100.0,50.49,0.0,0.0,'15:00',0,0.0,'unidad'),
(7,'2025-11-13 02:44:00','200006500','Queso Cotija (0.455 Kg)',1,142.0,64.61,'Normal','Efectivo','','',1,'Efectivo',150.485,0.0,0.0,0.0,'15:00',0,0.455,'granel'),
(8,'2025-11-13 02:44:00','200000300','Jamon Pierna Andalucia (0.295 Kg)',1,125.0,36.875,'Normal','Efectivo','','',1,'Efectivo',150.485,0.0,0.0,0.0,'15:00',0,0.295,'granel'),
(9,'2025-11-13 02:44:00','20803010','Yogurt Yoplay Durazno',1,49.0,49.0,'Normal','Efectivo','','',1,'Efectivo',150.485,0.0,0.0,0.0,'15:00',0,0.0,'unidad'),
(10,'2025-11-13 02:54:44','200005200','Queso Panela (0.450 Kg)',1,110.0,2090.0,'Normal','Efectivo','','',1,'Efectivo',2090.0,0.0,0.0,0.0,'15:00',0,19.0,'granel'),
(11,'2025-11-13 02:58:32','200005200','Queso Panela (0.500 Kg)',1,110.0,110.0,'Normal','Efectivo','','',1,'Efectivo',110.0,0.0,0.0,0.0,'15:00',0,1.0,'granel'),
(12,'2025-11-16 00:30:04','200006500','Queso Cotija (0.455 Kg)',1,142.0,64.61,'Normal','Efectivo','','',1,'Efectivo',150.485,0.0,0.0,0.0,'15:00',0,0.455,'granel'),
(13,'2025-11-16 00:30:04','200000300','Jamon Pierna Andalucia (0.295 Kg)',1,125.0,36.875,'Normal','Efectivo','','',1,'Efectivo',150.485,0.0,0.0,0.0,'15:00',0,0.295,'granel'),
(14,'2025-11-16 00:30:04','20803010','Yogurt Yoplay Durazno',1,49.0,49.0,'Normal','Efectivo','','',1,'Efectivo',150.485,0.0,0.0,0.0,'15:00',0,0.0,'unidad');

-- Ajustar secuencia de ventas
SELECT setval('ventas_id_seq', (SELECT MAX(id) FROM ventas));

-- Insertar datos en egresos_adicionales
INSERT INTO egresos_adicionales (id, fecha, tipo, descripcion, monto, observaciones, usuario) VALUES
(1,'2025-10-30 00:00:00','Servicios','Pago de Contador',1500.0,'del mes de Octubre','Sistema'),
(2,'2025-10-30 00:00:00','Otros','Pedido para la casa ',300.0,'Pedido realizado a Paul ','Sistema'),
(3,'2025-11-13 00:00:00','Otros','Pedido a la casa ',100.0,'se lo pedi a kevin ','Sistema');

-- Ajustar secuencia de egresos_adicionales
SELECT setval('egresos_adicionales_id_seq', (SELECT MAX(id) FROM egresos_adicionales));

-- Insertar datos en ingresos_pasivos
INSERT INTO ingresos_pasivos (id, fecha, descripcion, monto, observaciones, usuario) VALUES
(1,'2025-10-30 00:00:00','Apartado del mes de octubre',3000.0,'','Sistema');

-- Ajustar secuencia de ingresos_pasivos
SELECT setval('ingresos_pasivos_id_seq', (SELECT MAX(id) FROM ingresos_pasivos));

-- Insertar datos en turnos
INSERT INTO turnos (id, empleado, turno, timestamp) VALUES
(1,'Carlos',1,'2025-10-27 20:15:14'),
(2,'Ana',2,'2025-10-27 23:12:06'),
(3,'Marta',3,'2025-10-27 23:12:16'),
(4,'Ana',4,'2025-10-27 23:12:25'),
(5,'Ana',5,'2025-10-30 18:22:20'),
(6,'Ana',6,'2025-11-13 03:16:57');

-- Ajustar secuencia de turnos
SELECT setval('turnos_id_seq', (SELECT MAX(id) FROM turnos));

-- Crear índices para mejorar rendimiento
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_ventas_codigo ON ventas(codigo);
CREATE INDEX idx_productos_categoria ON productos(categoria);
CREATE INDEX idx_productos_tipo_venta ON productos(tipo_venta);
CREATE INDEX idx_usuarios_usuario ON usuarios_admin(usuario);
CREATE INDEX idx_creditos_venta_id ON creditos_pendientes(venta_id);
CREATE INDEX idx_pedidos_codigo_producto ON pedidos_reabastecimiento(codigo_producto);

-- Comentarios en las tablas
COMMENT ON TABLE productos IS 'Catálogo de productos de la cremería';
COMMENT ON TABLE ventas IS 'Registro de todas las ventas realizadas';
COMMENT ON TABLE usuarios_admin IS 'Usuarios del sistema con sus roles';
COMMENT ON TABLE creditos_pendientes IS 'Control de créditos pendientes de pago';
COMMENT ON TABLE egresos_adicionales IS 'Registro de gastos y egresos';
COMMENT ON TABLE ingresos_pasivos IS 'Registro de ingresos adicionales';
COMMENT ON TABLE pedidos_reabastecimiento IS 'Gestión de pedidos a proveedores';
COMMENT ON TABLE turnos IS 'Control de turnos de empleados';

-- Habilitar Row Level Security (RLS) para seguridad en Supabase
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios_admin ENABLE ROW LEVEL SECURITY;
ALTER TABLE creditos_pendientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE egresos_adicionales ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingresos_pasivos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos_reabastecimiento ENABLE ROW LEVEL SECURITY;
ALTER TABLE turnos ENABLE ROW LEVEL SECURITY;

-- Políticas básicas de RLS (ajustar según necesidades)
-- Permitir todas las operaciones para usuarios autenticados
CREATE POLICY "Permitir todo a usuarios autenticados" ON productos FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Permitir todo a usuarios autenticados" ON ventas FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Permitir todo a usuarios autenticados" ON usuarios_admin FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Permitir todo a usuarios autenticados" ON creditos_pendientes FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Permitir todo a usuarios autenticados" ON egresos_adicionales FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Permitir todo a usuarios autenticados" ON ingresos_pasivos FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Permitir todo a usuarios autenticados" ON pedidos_reabastecimiento FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Permitir todo a usuarios autenticados" ON turnos FOR ALL USING (auth.role() = 'authenticated');

-- Fin del script
