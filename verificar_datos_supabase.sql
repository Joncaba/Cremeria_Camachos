-- Query simple para verificar datos en Supabase
-- Ejecuta esto en SQL Editor de Supabase

-- Ver cuántos registros hay en cada tabla (ignora RLS)
SELECT 
    'productos' as tabla, 
    COUNT(*) as registros 
FROM productos;

SELECT 
    'usuarios_admin' as tabla, 
    COUNT(*) as registros 
FROM usuarios_admin;

SELECT 
    'ventas' as tabla, 
    COUNT(*) as registros 
FROM ventas;

-- Ver primeros productos
SELECT * FROM productos LIMIT 5;

-- Ver usuarios
SELECT usuario, nombre_completo, rol FROM usuarios_admin;

-- Ver estado de RLS
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
