-- Desactivar RLS en todas las tablas para acceso sin autenticación
-- Ejecutar en SQL Editor de Supabase

ALTER TABLE productos DISABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios_admin DISABLE ROW LEVEL SECURITY;
ALTER TABLE ventas DISABLE ROW LEVEL SECURITY;
ALTER TABLE creditos_pendientes DISABLE ROW LEVEL SECURITY;
ALTER TABLE egresos_adicionales DISABLE ROW LEVEL SECURITY;
ALTER TABLE ingresos_pasivos DISABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos_reabastecimiento DISABLE ROW LEVEL SECURITY;
ALTER TABLE turnos DISABLE ROW LEVEL SECURITY;

-- Verificar que RLS está desactivado
SELECT 
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '✅ RLS desactivado en todas las tablas';
    RAISE NOTICE '⚠️  ADVERTENCIA: Las tablas ahora son accesibles sin autenticación';
    RAISE NOTICE '💡 Esto es OK para desarrollo, pero considera habilitar RLS en producción';
END $$;
