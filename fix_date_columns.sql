-- ========================================
-- FIX DEFINITIVO - Columnas problemáticas
-- Ejecutar en SQL Editor de Supabase
-- ========================================

-- PROBLEMA 1: ventas - fecha_vencimiento_credito debe permitir NULL o ser TEXT
ALTER TABLE public.ventas 
ALTER COLUMN fecha_vencimiento_credito DROP NOT NULL;

-- Si la columna es DATE, cambiarla a TEXT para aceptar cadenas vacías
ALTER TABLE public.ventas 
ALTER COLUMN fecha_vencimiento_credito TYPE TEXT;

-- PROBLEMA 2: creditos_pendientes - fecha_credito no debe ser NOT NULL
ALTER TABLE public.creditos_pendientes 
ALTER COLUMN fecha_credito DROP NOT NULL;

-- Agregar columna pagado si no existe
ALTER TABLE public.creditos_pendientes 
ADD COLUMN IF NOT EXISTS pagado BOOLEAN DEFAULT FALSE;

-- ========================================
-- VERIFICACION
-- ========================================

-- Ver estructura de ventas
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'ventas' 
  AND table_schema = 'public'
  AND column_name IN ('fecha', 'fecha_vencimiento_credito')
ORDER BY ordinal_position;

-- Ver estructura de creditos_pendientes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'creditos_pendientes' 
  AND table_schema = 'public'
ORDER BY ordinal_position;
