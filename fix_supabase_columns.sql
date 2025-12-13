-- ========================================
-- CORRECCION DE ESTRUCTURA SUPABASE
-- Ejecutar en SQL Editor de Supabase
-- ========================================

-- PROBLEMA 1: Columna 'numero_producto' falta en tabla productos
ALTER TABLE public.productos 
ADD COLUMN IF NOT EXISTS numero_producto BIGINT;

-- PROBLEMA 2: Columna 'tipo_pago' falta en tabla ventas
ALTER TABLE public.ventas 
ADD COLUMN IF NOT EXISTS tipo_pago TEXT;

-- PROBLEMA 3: Columna 'fecha_venta' falta en tabla creditos_pendientes
ALTER TABLE public.creditos_pendientes 
ADD COLUMN IF NOT EXISTS fecha_venta TIMESTAMP WITH TIME ZONE;

-- PROBLEMA 4: Deshabilitar RLS en tablas con errores
ALTER TABLE public.productos DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.ventas DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.devoluciones DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.turnos DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.creditos_pendientes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.pedidos_items DISABLE ROW LEVEL SECURITY;

-- ========================================
-- VERIFICACION
-- ========================================

-- Verificar columnas de productos
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'productos' AND table_schema = 'public'
ORDER BY column_name;

-- Verificar columnas de ventas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ventas' AND table_schema = 'public'
ORDER BY column_name;

-- Verificar RLS deshabilitado
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('productos', 'ventas', 'usuarios', 'devoluciones', 'turnos', 'creditos_pendientes', 'pedidos_items')
ORDER BY tablename;
