-- Script SQL para crear las tablas necesarias en Supabase
-- Ejecutar este script en el SQL Editor de Supabase

-- IMPORTANTE: Eliminar tablas existentes para recrearlas con la estructura correcta
DROP TABLE IF EXISTS pedidos_items CASCADE;
DROP TABLE IF EXISTS ordenes_compra CASCADE;
DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS pedidos_reabastecimiento CASCADE;
DROP TABLE IF EXISTS ventas CASCADE;
DROP TABLE IF EXISTS creditos_pendientes CASCADE;
DROP TABLE IF EXISTS egresos_adicionales CASCADE;
DROP TABLE IF EXISTS ingresos_pasivos CASCADE;

-- ========================================
-- TABLA DE VENTAS
-- ========================================

CREATE TABLE ventas (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP NOT NULL,
    codigo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    tipo_cliente TEXT DEFAULT 'Público General',
    tipos_pago TEXT DEFAULT 'Efectivo',
    monto_efectivo DECIMAL(10,2) DEFAULT 0,
    monto_tarjeta DECIMAL(10,2) DEFAULT 0,
    monto_transferencia DECIMAL(10,2) DEFAULT 0,
    monto_credito DECIMAL(10,2) DEFAULT 0,
    fecha_vencimiento_credito DATE,
    hora_vencimiento_credito TEXT DEFAULT '15:00',
    cliente_credito TEXT DEFAULT '',
    pagado INTEGER DEFAULT 1,
    alerta_mostrada INTEGER DEFAULT 0,
    peso_vendido DECIMAL(10,3) DEFAULT 0,
    tipo_venta TEXT DEFAULT 'unidad'
);

-- Índices para ventas
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
CREATE INDEX IF NOT EXISTS idx_ventas_codigo ON ventas(codigo);
CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(tipo_cliente);
CREATE INDEX IF NOT EXISTS idx_ventas_credito ON ventas(cliente_credito) WHERE cliente_credito != '';
CREATE INDEX IF NOT EXISTS idx_ventas_pagado ON ventas(pagado);

-- ========================================
-- TABLA DE CRÉDITOS PENDIENTES
-- ========================================

CREATE TABLE creditos_pendientes (
    id BIGSERIAL PRIMARY KEY,
    venta_id INTEGER,
    cliente TEXT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_credito TIMESTAMP NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    hora_vencimiento TEXT DEFAULT '15:00',
    estado TEXT DEFAULT 'pendiente',
    alerta_mostrada INTEGER DEFAULT 0
);

-- Índices para créditos
CREATE INDEX IF NOT EXISTS idx_creditos_cliente ON creditos_pendientes(cliente);
CREATE INDEX IF NOT EXISTS idx_creditos_estado ON creditos_pendientes(estado);
CREATE INDEX IF NOT EXISTS idx_creditos_vencimiento ON creditos_pendientes(fecha_vencimiento);

-- ========================================
-- TABLA DE EGRESOS ADICIONALES
-- ========================================

CREATE TABLE egresos_adicionales (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    observaciones TEXT,
    usuario TEXT DEFAULT 'Sistema'
);

-- Índices para egresos
CREATE INDEX IF NOT EXISTS idx_egresos_fecha ON egresos_adicionales(fecha);
CREATE INDEX IF NOT EXISTS idx_egresos_tipo ON egresos_adicionales(tipo);

-- ========================================
-- TABLA DE INGRESOS PASIVOS
-- ========================================

CREATE TABLE ingresos_pasivos (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    observaciones TEXT,
    usuario TEXT DEFAULT 'Sistema'
);

-- Índices para ingresos
CREATE INDEX IF NOT EXISTS idx_ingresos_fecha ON ingresos_pasivos(fecha);

-- ========================================
-- TABLAS DE PEDIDOS Y ÓRDENES DE COMPRA
-- ========================================

-- Tabla de pedidos (cabecera) - CREAR PRIMERO
CREATE TABLE pedidos (
    id BIGSERIAL PRIMARY KEY,
    fecha_pedido TIMESTAMP NOT NULL,
    fecha_entrega_esperada TIMESTAMP,
    estado TEXT DEFAULT 'PENDIENTE',
    total_productos INTEGER DEFAULT 0,
    total_costo DECIMAL(10,2) DEFAULT 0,
    notas TEXT,
    creado_por TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    orden_compra_id BIGINT
);

-- Tabla de items/productos del pedido (detalle)
CREATE TABLE pedidos_items (
    id BIGSERIAL PRIMARY KEY,
    pedido_id BIGINT NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    cantidad_solicitada DECIMAL(10,2) NOT NULL,
    cantidad_recibida DECIMAL(10,2) DEFAULT 0,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    proveedor TEXT DEFAULT '',
    estado_item TEXT DEFAULT 'PENDIENTE'
);

-- Tabla de órdenes de compra
CREATE TABLE ordenes_compra (
    id BIGSERIAL PRIMARY KEY,
    pedido_id BIGINT NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_orden DECIMAL(10,2) NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE',
    fecha_pago TIMESTAMP,
    notas TEXT,
    creado_por TEXT DEFAULT 'admin'
);

-- Índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha_pedido);
CREATE INDEX IF NOT EXISTS idx_pedidos_items_pedido ON pedidos_items(pedido_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_items_codigo ON pedidos_items(codigo_producto);
CREATE INDEX IF NOT EXISTS idx_ordenes_pedido ON ordenes_compra(pedido_id);
CREATE INDEX IF NOT EXISTS idx_ordenes_estado ON ordenes_compra(estado);
CREATE INDEX IF NOT EXISTS idx_ordenes_fecha ON ordenes_compra(fecha_creacion);

-- ========================================
-- SEGURIDAD Y POLÍTICAS
-- ========================================

-- Habilitar Row Level Security (RLS)
ALTER TABLE ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE creditos_pendientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE egresos_adicionales ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingresos_pasivos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordenes_compra ENABLE ROW LEVEL SECURITY;

-- Políticas de acceso para ventas
DROP POLICY IF EXISTS "Permitir todas las operaciones en ventas" ON ventas;
CREATE POLICY "Permitir todas las operaciones en ventas"
ON ventas FOR ALL
USING (true)
WITH CHECK (true);

-- Políticas de acceso para créditos
DROP POLICY IF EXISTS "Permitir todas las operaciones en creditos_pendientes" ON creditos_pendientes;
CREATE POLICY "Permitir todas las operaciones en creditos_pendientes"
ON creditos_pendientes FOR ALL
USING (true)
WITH CHECK (true);

-- Políticas de acceso para egresos
DROP POLICY IF EXISTS "Permitir todas las operaciones en egresos_adicionales" ON egresos_adicionales;
CREATE POLICY "Permitir todas las operaciones en egresos_adicionales"
ON egresos_adicionales FOR ALL
USING (true)
WITH CHECK (true);

-- Políticas de acceso para ingresos
DROP POLICY IF EXISTS "Permitir todas las operaciones en ingresos_pasivos" ON ingresos_pasivos;
CREATE POLICY "Permitir todas las operaciones en ingresos_pasivos"
ON ingresos_pasivos FOR ALL
USING (true)
WITH CHECK (true);

-- Políticas de acceso para pedidos
DROP POLICY IF EXISTS "Permitir todas las operaciones en pedidos" ON pedidos;
CREATE POLICY "Permitir todas las operaciones en pedidos"
ON pedidos FOR ALL
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir todas las operaciones en pedidos_items" ON pedidos_items;
CREATE POLICY "Permitir todas las operaciones en pedidos_items"
ON pedidos_items FOR ALL
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir todas las operaciones en ordenes_compra" ON ordenes_compra;
CREATE POLICY "Permitir todas las operaciones en ordenes_compra"
ON ordenes_compra FOR ALL
USING (true)
WITH CHECK (true);

-- ========================================
-- DOCUMENTACIÓN
-- ========================================

COMMENT ON TABLE ventas IS 'Registro de todas las ventas realizadas en el punto de venta';
COMMENT ON TABLE creditos_pendientes IS 'Créditos pendientes de pago de clientes';
COMMENT ON TABLE egresos_adicionales IS 'Egresos adicionales del negocio (servicios, gastos operativos, etc.)';
COMMENT ON TABLE ingresos_pasivos IS 'Ingresos adicionales no relacionados con ventas directas';
COMMENT ON TABLE pedidos IS 'Pedidos de reabastecimiento (cabecera) - un pedido agrupa múltiples productos';
COMMENT ON TABLE pedidos_items IS 'Items/productos de cada pedido (detalle)';
COMMENT ON TABLE ordenes_compra IS 'Órdenes de compra generadas desde pedidos recibidos - una orden por pedido';
COMMENT ON COLUMN ventas.tipo_venta IS 'granel o unidad - determina si se vendió por peso o por unidades';
COMMENT ON COLUMN ventas.peso_vendido IS 'Peso en kg para productos a granel';
COMMENT ON COLUMN ventas.pagado IS '1 = pagado, 0 = pendiente de pago (crédito)';
COMMENT ON COLUMN pedidos.estado IS 'PENDIENTE, EN_TRANSITO, RECIBIDO, COMPLETADO';
COMMENT ON COLUMN pedidos.orden_compra_id IS 'FK a ordenes_compra - se asigna cuando se genera la orden';
COMMENT ON COLUMN pedidos_items.estado_item IS 'PENDIENTE o RECIBIDO - estado individual de cada producto';
COMMENT ON COLUMN ordenes_compra.estado IS 'PENDIENTE o PAGADA';
COMMENT ON COLUMN ordenes_compra.pedido_id IS 'FK al pedido del cual se generó esta orden';




