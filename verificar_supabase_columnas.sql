-- =========================================
-- CONSULTA DE DIAGNÓSTICO PARA SUPABASE
-- =========================================
-- Ejecutar este script en Supabase SQL Editor para ver qué columnas ya existen

-- Ver todas las tablas de finanzas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('egresos_adicionales', 'ingresos_pasivos', 'caja_chica_movimientos', 'ordenes_compra');

-- Ver columnas de egresos_adicionales
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'egresos_adicionales'
ORDER BY ordinal_position;

-- Ver columnas de ingresos_pasivos
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'ingresos_pasivos'
ORDER BY ordinal_position;

-- Ver columnas de caja_chica_movimientos
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'caja_chica_movimientos'
ORDER BY ordinal_position;

-- Ver columnas de ordenes_compra
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'ordenes_compra'
ORDER BY ordinal_position;
