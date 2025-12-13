-- ================================================================================
-- SQL PARA CREAR TABLAS FALTANTES EN SUPABASE
-- Ejecutar en: Supabase SQL Editor
-- Fecha: 2025-12-12
-- Problema: sync_producto_to_supabase y sync_usuario_to_supabase existen pero
--           las tablas destino NO están en Supabase, causando pérdida de datos
-- ================================================================================

-- ========================================
-- A) TABLA PRODUCTOS
-- ========================================
-- Esta tabla es CRÍTICA - tiene sync implementado pero no existe en Supabase

DROP TABLE IF EXISTS productos CASCADE;

CREATE TABLE productos (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio_compra NUMERIC(10,2) NOT NULL DEFAULT 0,
    precio_normal NUMERIC(10,2) NOT NULL,
    precio_mayoreo_1 NUMERIC(10,2) NOT NULL,
    precio_mayoreo_2 NUMERIC(10,2) NOT NULL DEFAULT 0,
    precio_mayoreo_3 NUMERIC(10,2) NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    tipo_venta TEXT DEFAULT 'unidad',
    precio_por_kg NUMERIC(10,2) DEFAULT 0,
    peso_unitario NUMERIC(10,3) DEFAULT 0,
    stock_kg NUMERIC(10,3) DEFAULT 0,
    stock_minimo INTEGER DEFAULT 10,
    stock_minimo_kg NUMERIC(10,3) DEFAULT 0,
    stock_maximo INTEGER DEFAULT 30,
    stock_maximo_kg NUMERIC(10,3) DEFAULT 0,
    categoria TEXT DEFAULT 'cremeria',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT chk_tipo_venta CHECK (tipo_venta IN ('unidad', 'granel', 'ambos'))
);

-- Índices para productos
CREATE INDEX idx_productos_nombre ON productos(nombre);
CREATE INDEX idx_productos_categoria ON productos(categoria);
CREATE INDEX idx_productos_tipo_venta ON productos(tipo_venta);
CREATE INDEX idx_productos_stock_bajo ON productos(stock) WHERE stock <= stock_minimo;
CREATE INDEX idx_productos_stock_kg_bajo ON productos(stock_kg) WHERE stock_kg <= stock_minimo_kg;

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_productos_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER t_upd_productos
    BEFORE UPDATE ON productos
    FOR EACH ROW
    EXECUTE FUNCTION update_productos_timestamp();

-- RLS para productos
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "productos_select_all" ON productos;
CREATE POLICY "productos_select_all"
ON productos FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "productos_ins_auth" ON productos;
CREATE POLICY "productos_ins_auth"
ON productos FOR INSERT
TO authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "productos_upd_auth" ON productos;
CREATE POLICY "productos_upd_auth"
ON productos FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "productos_del_auth" ON productos;
CREATE POLICY "productos_del_auth"
ON productos FOR DELETE
TO authenticated
USING (true);

-- Función RPC para upsert de productos
CREATE OR REPLACE FUNCTION upsert_producto(_row JSONB)
RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    _codigo TEXT;
BEGIN
    _codigo := (_row->>'codigo')::TEXT;
    
    INSERT INTO productos (
        codigo, nombre, precio_compra, precio_normal, 
        precio_mayoreo_1, precio_mayoreo_2, precio_mayoreo_3,
        stock, tipo_venta, precio_por_kg, peso_unitario, stock_kg,
        stock_minimo, stock_minimo_kg, stock_maximo, stock_maximo_kg,
        categoria, created_at
    )
    VALUES (
        _codigo,
        (_row->>'nombre')::TEXT,
        COALESCE((_row->>'precio_compra')::NUMERIC, 0),
        (_row->>'precio_normal')::NUMERIC,
        (_row->>'precio_mayoreo_1')::NUMERIC,
        COALESCE((_row->>'precio_mayoreo_2')::NUMERIC, 0),
        COALESCE((_row->>'precio_mayoreo_3')::NUMERIC, 0),
        COALESCE((_row->>'stock')::INTEGER, 0),
        COALESCE((_row->>'tipo_venta')::TEXT, 'unidad'),
        COALESCE((_row->>'precio_por_kg')::NUMERIC, 0),
        COALESCE((_row->>'peso_unitario')::NUMERIC, 0),
        COALESCE((_row->>'stock_kg')::NUMERIC, 0),
        COALESCE((_row->>'stock_minimo')::INTEGER, 10),
        COALESCE((_row->>'stock_minimo_kg')::NUMERIC, 0),
        COALESCE((_row->>'stock_maximo')::INTEGER, 30),
        COALESCE((_row->>'stock_maximo_kg')::NUMERIC, 0),
        COALESCE((_row->>'categoria')::TEXT, 'cremeria'),
        COALESCE((_row->>'created_at')::TIMESTAMPTZ, NOW())
    )
    ON CONFLICT (codigo) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        precio_compra = EXCLUDED.precio_compra,
        precio_normal = EXCLUDED.precio_normal,
        precio_mayoreo_1 = EXCLUDED.precio_mayoreo_1,
        precio_mayoreo_2 = EXCLUDED.precio_mayoreo_2,
        precio_mayoreo_3 = EXCLUDED.precio_mayoreo_3,
        stock = EXCLUDED.stock,
        tipo_venta = EXCLUDED.tipo_venta,
        precio_por_kg = EXCLUDED.precio_por_kg,
        peso_unitario = EXCLUDED.peso_unitario,
        stock_kg = EXCLUDED.stock_kg,
        stock_minimo = EXCLUDED.stock_minimo,
        stock_minimo_kg = EXCLUDED.stock_minimo_kg,
        stock_maximo = EXCLUDED.stock_maximo,
        stock_maximo_kg = EXCLUDED.stock_maximo_kg,
        categoria = EXCLUDED.categoria,
        updated_at = NOW();
    
    RETURN 0; -- Productos usa codigo (TEXT) como PK, no retorna id numérico
END;
$$;

-- ========================================
-- B) TABLA USUARIOS_ADMIN
-- ========================================
-- Esta tabla es CRÍTICA - tiene sync implementado pero no existe en Supabase

DROP TABLE IF EXISTS usuarios_admin CASCADE;

CREATE TABLE usuarios_admin (
    id BIGSERIAL PRIMARY KEY,
    usuario TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT DEFAULT 'usuario',
    activo INTEGER DEFAULT 1,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    ultimo_acceso TIMESTAMPTZ,
    creado_por TEXT DEFAULT 'Sistema',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT chk_rol CHECK (rol IN ('admin', 'usuario', 'cajero', 'gerente')),
    CONSTRAINT chk_activo CHECK (activo IN (0, 1))
);

-- Índices para usuarios_admin
CREATE INDEX idx_usuarios_admin_usuario ON usuarios_admin(usuario);
CREATE INDEX idx_usuarios_admin_rol ON usuarios_admin(rol);
CREATE INDEX idx_usuarios_admin_activo ON usuarios_admin(activo);

-- Trigger para updated_at
CREATE TRIGGER t_upd_usuarios_admin
    BEFORE UPDATE ON usuarios_admin
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- RLS para usuarios_admin
ALTER TABLE usuarios_admin ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "usuarios_admin_select_all" ON usuarios_admin;
CREATE POLICY "usuarios_admin_select_all"
ON usuarios_admin FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "usuarios_admin_ins_auth" ON usuarios_admin;
CREATE POLICY "usuarios_admin_ins_auth"
ON usuarios_admin FOR INSERT
TO authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "usuarios_admin_upd_auth" ON usuarios_admin;
CREATE POLICY "usuarios_admin_upd_auth"
ON usuarios_admin FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "usuarios_admin_del_auth" ON usuarios_admin;
CREATE POLICY "usuarios_admin_del_auth"
ON usuarios_admin FOR DELETE
TO authenticated
USING (true);

-- Función RPC para upsert de usuarios_admin
CREATE OR REPLACE FUNCTION upsert_usuario_admin(_row JSONB)
RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    _id BIGINT;
BEGIN
    _id := COALESCE((_row->>'id')::BIGINT, 0);
    
    INSERT INTO usuarios_admin (
        id, usuario, password, nombre_completo, rol, activo,
        fecha_creacion, ultimo_acceso, creado_por
    )
    VALUES (
        CASE WHEN _id > 0 THEN _id ELSE DEFAULT END,
        (_row->>'usuario')::TEXT,
        (_row->>'password')::TEXT,
        (_row->>'nombre_completo')::TEXT,
        COALESCE((_row->>'rol')::TEXT, 'usuario'),
        COALESCE((_row->>'activo')::INTEGER, 1),
        COALESCE((_row->>'fecha_creacion')::TIMESTAMPTZ, NOW()),
        (_row->>'ultimo_acceso')::TIMESTAMPTZ,
        COALESCE((_row->>'creado_por')::TEXT, 'Sistema')
    )
    ON CONFLICT (id) DO UPDATE SET
        usuario = EXCLUDED.usuario,
        password = EXCLUDED.password,
        nombre_completo = EXCLUDED.nombre_completo,
        rol = EXCLUDED.rol,
        activo = EXCLUDED.activo,
        ultimo_acceso = EXCLUDED.ultimo_acceso,
        creado_por = EXCLUDED.creado_por,
        updated_at = NOW()
    RETURNING id INTO _id;
    
    RETURN _id;
END;
$$;

-- ========================================
-- C) TABLA TURNOS
-- ========================================
-- Tabla para control de turnos de atención al cliente
-- Actualmente NO tiene sync implementado pero es importante para operaciones

DROP TABLE IF EXISTS turnos CASCADE;

CREATE TABLE turnos (
    id BIGSERIAL PRIMARY KEY,
    empleado TEXT NOT NULL,
    turno INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para turnos
CREATE INDEX idx_turnos_empleado ON turnos(empleado);
CREATE INDEX idx_turnos_turno ON turnos(turno);
CREATE INDEX idx_turnos_timestamp ON turnos(timestamp DESC);

-- Trigger para updated_at
CREATE TRIGGER t_upd_turnos
    BEFORE UPDATE ON turnos
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- RLS para turnos
ALTER TABLE turnos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "turnos_select_all" ON turnos;
CREATE POLICY "turnos_select_all"
ON turnos FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "turnos_ins_auth" ON turnos;
CREATE POLICY "turnos_ins_auth"
ON turnos FOR INSERT
TO authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "turnos_upd_auth" ON turnos;
CREATE POLICY "turnos_upd_auth"
ON turnos FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- Función RPC para upsert de turnos
CREATE OR REPLACE FUNCTION upsert_turno(_row JSONB)
RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    _id BIGINT;
BEGIN
    _id := COALESCE((_row->>'id')::BIGINT, 0);
    
    INSERT INTO turnos (
        id, empleado, turno, timestamp
    )
    VALUES (
        CASE WHEN _id > 0 THEN _id ELSE DEFAULT END,
        (_row->>'empleado')::TEXT,
        (_row->>'turno')::INTEGER,
        (_row->>'timestamp')::TIMESTAMPTZ
    )
    ON CONFLICT (id) DO UPDATE SET
        empleado = EXCLUDED.empleado,
        turno = EXCLUDED.turno,
        timestamp = EXCLUDED.timestamp,
        updated_at = NOW()
    RETURNING id INTO _id;
    
    RETURN _id;
END;
$$;

-- ========================================
-- D) TABLA PEDIDOS_ITEMS (Individual Sync)
-- ========================================
-- Actualmente pedidos_items existe pero solo se sincroniza cuando se sincroniza
-- el pedido completo. Esta función RPC permite sincronización individual.

-- La tabla ya existe, solo agregamos la función RPC
CREATE OR REPLACE FUNCTION upsert_pedido_item(_row JSONB)
RETURNS BIGINT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    _id BIGINT;
BEGIN
    _id := COALESCE((_row->>'id')::BIGINT, 0);
    
    INSERT INTO pedidos_items (
        id, pedido_id, codigo_producto, nombre_producto,
        cantidad_solicitada, cantidad_recibida, precio_unitario,
        subtotal, proveedor, estado_item
    )
    VALUES (
        CASE WHEN _id > 0 THEN _id ELSE DEFAULT END,
        (_row->>'pedido_id')::BIGINT,
        (_row->>'codigo_producto')::TEXT,
        (_row->>'nombre_producto')::TEXT,
        (_row->>'cantidad_solicitada')::NUMERIC,
        COALESCE((_row->>'cantidad_recibida')::NUMERIC, 0),
        (_row->>'precio_unitario')::NUMERIC,
        (_row->>'subtotal')::NUMERIC,
        COALESCE((_row->>'proveedor')::TEXT, ''),
        COALESCE((_row->>'estado_item')::TEXT, 'PENDIENTE')
    )
    ON CONFLICT (id) DO UPDATE SET
        pedido_id = EXCLUDED.pedido_id,
        codigo_producto = EXCLUDED.codigo_producto,
        nombre_producto = EXCLUDED.nombre_producto,
        cantidad_solicitada = EXCLUDED.cantidad_solicitada,
        cantidad_recibida = EXCLUDED.cantidad_recibida,
        precio_unitario = EXCLUDED.precio_unitario,
        subtotal = EXCLUDED.subtotal,
        proveedor = EXCLUDED.proveedor,
        estado_item = EXCLUDED.estado_item
    RETURNING id INTO _id;
    
    RETURN _id;
END;
$$;

-- ========================================
-- E) COMENTARIOS Y DOCUMENTACIÓN
-- ========================================

COMMENT ON TABLE productos IS 'Catálogo de productos con soporte para venta por unidad y granel';
COMMENT ON TABLE usuarios_admin IS 'Usuarios administradores del sistema POS';
COMMENT ON TABLE turnos IS 'Sistema de turnos para atención al cliente';

COMMENT ON COLUMN productos.tipo_venta IS 'unidad, granel o ambos - determina cómo se vende el producto';
COMMENT ON COLUMN productos.peso_unitario IS 'Peso aproximado de una unidad en kg (para productos que se venden por ambos)';
COMMENT ON COLUMN productos.stock_kg IS 'Stock disponible en kilogramos (para productos a granel)';
COMMENT ON COLUMN usuarios_admin.activo IS '1 = activo, 0 = desactivado';
COMMENT ON COLUMN usuarios_admin.rol IS 'admin, usuario, cajero, gerente';

-- ================================================================================
-- RESUMEN DE EJECUCIÓN:
-- ================================================================================
-- Este script crea:
-- ✅ Tabla productos + índices + trigger + RLS + función upsert_producto
-- ✅ Tabla usuarios_admin + índices + trigger + RLS + función upsert_usuario_admin  
-- ✅ Tabla turnos + índices + trigger + RLS + función upsert_turno
-- ✅ Función upsert_pedido_item para sincronización individual de items
--
-- IMPORTANTE: Después de ejecutar este script:
-- 1. Ejecutar sincronización masiva de productos desde la app
-- 2. Ejecutar sincronización masiva de usuarios_admin desde la app
-- 3. (Opcional) Implementar sync para turnos en el código
-- 4. (Opcional) Implementar sync individual para pedidos_items
-- ================================================================================
