-- ======================================================================================
-- SUPABASE SCHEMA FIXES FOR CONTINUOUS SYNC
-- ======================================================================================
-- Run this in Supabase SQL Editor to fix constraint and column mismatches

-- 1. FIX ventas: fecha field can be empty string
-- Make fecha nullable or add default
ALTER TABLE public.ventas 
  ALTER COLUMN fecha SET DEFAULT CURRENT_TIMESTAMP;

-- 2. FIX productos: precio_mayoreo_1 NOT NULL constraint
-- Make it nullable or add default
ALTER TABLE public.productos 
  ALTER COLUMN precio_mayoreo_1 DROP NOT NULL;

-- 3. FIX pedidos_items: Foreign key constraint on pedido_id
-- Ensure pedidos are synced BEFORE pedidos_items
-- If you need to relax temporarily:
-- ALTER TABLE public.pedidos_items DROP CONSTRAINT pedidos_items_pedido_id_fkey;
-- ALTER TABLE public.pedidos_items ADD CONSTRAINT pedidos_items_pedido_id_fkey 
--   FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;

-- 4. FIX usuarios: Table should be 'usuarios' not 'usuarios_admin'
-- Option A: Rename usuarios_admin to usuarios
-- ALTER TABLE public.usuarios_admin RENAME TO usuarios;

-- Option B: Create usuarios as a view/copy from usuarios_admin
-- CREATE TABLE IF NOT EXISTS public.usuarios (
--   usuario TEXT PRIMARY KEY,
--   password TEXT NOT NULL,
--   activo INTEGER DEFAULT 1,
--   rol TEXT DEFAULT 'vendedor',
--   nombre_completo TEXT
-- );

-- For now, update sync_all_continuous.py to use 'usuarios_admin' instead of 'usuarios'
-- OR rename the table if you want unified naming

-- 5. Verify RLS is enabled on all tables (optional safety measure)
-- ALTER TABLE public.ventas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.productos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.pedidos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.pedidos_items ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.ordenes_compra ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.usuarios_admin ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.devoluciones ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.caja_chica_movimientos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.ingresos_pasivos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.egresos_adicionales ENABLE ROW LEVEL SECURITY;

-- ======================================================================================
-- SUMMARY OF ISSUES
-- ======================================================================================
-- 1. ventas.fecha: empty string not allowed - make nullable or check SQLite for NULLs
-- 2. productos.precio_mayoreo_1: NOT NULL but sync sending NULLs - drop NOT NULL constraint
-- 3. pedidos_items → pedidos: FK violation - ensure pedidos sync first (done, but check order)
-- 4. usuarios: table name mismatch (usuarios_admin vs usuarios) - rename or update script
-- ======================================================================================
