-- ========================================
-- FIX FINAL - Últimos 4 problemas
-- Ejecutar en SQL Editor de Supabase
-- ========================================

-- PROBLEMA 1: creditos_pendientes - falta columna 'pagado'
ALTER TABLE public.creditos_pendientes 
ADD COLUMN IF NOT EXISTS pagado BOOLEAN DEFAULT FALSE;

-- PROBLEMA 2: ventas - fechas vacías como cadenas ""
-- No se puede arreglar con SQL, se arreglará en el código de sincronización

-- PROBLEMA 3: usuarios - constraint duplicado
-- La tabla 'usuarios' tiene un constraint de usuario único
-- Necesitamos eliminar el constraint o cambiar la estrategia de upsert

-- Primero, verificar si hay constraint
-- SELECT constraint_name 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'usuarios' AND constraint_type = 'UNIQUE';

-- PROBLEMA 4: pedidos_items - foreign key
-- Este error es porque el pedido_id no existe en la tabla 'pedidos'
-- Necesitamos verificar que todos los pedidos estén sincronizados primero

-- ========================================
-- VERIFICACIONES
-- ========================================

-- Ver estructura de creditos_pendientes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'creditos_pendientes' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Ver constraints de usuarios
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints 
WHERE table_name = 'usuarios' AND table_schema = 'public';

-- Ver registros de pedidos en Supabase
SELECT id, fecha, total FROM public.pedidos ORDER BY id;
