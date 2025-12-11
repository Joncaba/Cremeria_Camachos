# 🚀 Guía de Migración a Supabase

## 📋 Cambios Realizados: SQLite → PostgreSQL

### Conversiones Principales:

1. **AUTOINCREMENT → SERIAL**
   - SQLite: `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - PostgreSQL: `id SERIAL PRIMARY KEY`

2. **REAL → DECIMAL**
   - SQLite: `precio REAL`
   - PostgreSQL: `precio DECIMAL(10,2)` (mejor precisión para dinero)

3. **Timestamps**
   - Mantenido: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

4. **Foreign Keys**
   - Agregado: `ON DELETE SET NULL` y `ON DELETE CASCADE`

5. **Secuencias**
   - Agregado: `SELECT setval()` para mantener IDs existentes

## 🔧 Pasos para Importar en Supabase

### Opción 1: Desde el Dashboard de Supabase (Recomendado)

1. **Accede a tu proyecto en Supabase**
   - Ve a [app.supabase.com](https://app.supabase.com)
   - Selecciona tu proyecto o crea uno nuevo

2. **Abre el SQL Editor**
   - En el menú lateral: `SQL Editor`
   - Click en `+ New Query`

3. **Copia y pega el contenido**
   - Abre: `pos_cremeria_supabase.sql`
   - Copia TODO el contenido
   - Pégalo en el editor SQL

4. **Ejecuta el script**
   - Click en `Run` o presiona `Ctrl+Enter`
   - Espera a que termine (puede tardar unos segundos)

5. **Verifica las tablas**
   - Ve a `Table Editor` en el menú lateral
   - Deberías ver las 8 tablas creadas

### Opción 2: Usando psql (Línea de comandos)

```bash
# Obtén tu connection string de Supabase:
# Settings → Database → Connection string (usar "Connection pooling" en producción)

psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres" -f pos_cremeria_supabase.sql
```

### Opción 3: Por partes (Si hay errores)

Si el script completo falla, ejecuta en este orden:

1. **Primero: Crear tablas**
   ```sql
   -- Solo las secciones DROP TABLE y CREATE TABLE
   ```

2. **Segundo: Insertar datos**
   ```sql
   -- Solo las secciones INSERT INTO
   ```

3. **Tercero: Crear índices**
   ```sql
   -- Solo las secciones CREATE INDEX
   ```

4. **Cuarto: Configurar RLS**
   ```sql
   -- Solo las secciones ALTER TABLE y CREATE POLICY
   ```

## 🔐 Configuración de Seguridad (RLS)

El script incluye Row Level Security (RLS) básico. Las políticas actuales permiten:
- ✅ Todos los usuarios autenticados pueden hacer todo
- ❌ Usuarios no autenticados: sin acceso

### Personalizar políticas según tu app:

```sql
-- Ejemplo: Solo admin puede modificar usuarios
DROP POLICY IF EXISTS "Permitir todo a usuarios autenticados" ON usuarios_admin;

CREATE POLICY "Solo admin puede modificar usuarios" 
ON usuarios_admin 
FOR ALL 
USING (
  auth.jwt() ->> 'user_metadata' ->> 'rol' = 'admin'
);

-- Ejemplo: Todos pueden ver productos, solo admin puede modificar
CREATE POLICY "Todos pueden ver productos" 
ON productos 
FOR SELECT 
USING (true);

CREATE POLICY "Solo admin puede modificar productos" 
ON productos 
FOR ALL 
USING (
  auth.jwt() ->> 'user_metadata' ->> 'rol' = 'admin'
);
```

## 📊 Verificación Post-Importación

Ejecuta estas queries para verificar:

```sql
-- Contar registros en cada tabla
SELECT 'productos' as tabla, COUNT(*) as registros FROM productos
UNION ALL
SELECT 'ventas', COUNT(*) FROM ventas
UNION ALL
SELECT 'usuarios_admin', COUNT(*) FROM usuarios_admin
UNION ALL
SELECT 'egresos_adicionales', COUNT(*) FROM egresos_adicionales
UNION ALL
SELECT 'ingresos_pasivos', COUNT(*) FROM ingresos_pasivos
UNION ALL
SELECT 'turnos', COUNT(*) FROM turnos
UNION ALL
SELECT 'creditos_pendientes', COUNT(*) FROM creditos_pendientes
UNION ALL
SELECT 'pedidos_reabastecimiento', COUNT(*) FROM pedidos_reabastecimiento;

-- Verificar secuencias
SELECT 
  schemaname, 
  sequencename, 
  last_value 
FROM pg_sequences 
WHERE schemaname = 'public';

-- Verificar foreign keys
SELECT
  tc.table_name, 
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## 🔄 Conectar tu App Streamlit a Supabase

### 1. Instalar dependencias:

```bash
pip install supabase-py python-dotenv
```

### 2. Agregar a requirements.txt:

```txt
supabase-py>=2.0.0
python-dotenv>=1.0.0
```

### 3. Configurar secrets.toml:

```toml
[supabase]
url = "https://[YOUR-PROJECT-REF].supabase.co"
key = "tu-anon-key-aqui"
service_role_key = "tu-service-role-key-aqui"  # Solo para operaciones admin
```

### 4. Crear módulo de conexión (supabase_client.py):

```python
import streamlit as st
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Obtener cliente de Supabase"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)
```

### 5. Ejemplo de uso:

```python
from supabase_client import get_supabase_client

# Obtener productos
supabase = get_supabase_client()
response = supabase.table('productos').select('*').execute()
productos = response.data

# Insertar venta
nueva_venta = {
    'fecha': '2025-11-16',
    'total': 150.50,
    'tipo_cliente': 'Normal'
}
supabase.table('ventas').insert(nueva_venta).execute()

# Actualizar producto
supabase.table('productos')\
    .update({'stock': 10})\
    .eq('codigo', '11111')\
    .execute()
```

## 📝 Diferencias a tener en cuenta

| SQLite | PostgreSQL/Supabase | Acción Necesaria |
|--------|---------------------|------------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` | ✅ Ya convertido |
| `REAL` | `DECIMAL(10,2)` | ✅ Ya convertido |
| Texto insensible a mayúsculas | Texto sensible | Usar `ILIKE` en vez de `LIKE` |
| Sin autenticación | RLS habilitado | Configurar políticas |
| Archivo local | Base de datos en la nube | Actualizar connection string |

## 🎯 Resultados Esperados

Después de la importación deberías tener:

- ✅ 8 tablas creadas
- ✅ 12 productos
- ✅ 2 usuarios
- ✅ 14 ventas
- ✅ 3 egresos
- ✅ 1 ingreso pasivo
- ✅ 6 turnos
- ✅ 0 créditos pendientes
- ✅ 0 pedidos
- ✅ 8 índices para rendimiento
- ✅ RLS habilitado en todas las tablas

## 🆘 Solución de Problemas

### Error: "relation already exists"
```sql
-- Ejecuta primero:
DROP TABLE IF EXISTS [nombre_tabla] CASCADE;
```

### Error: "permission denied"
- Verifica que estás usando el usuario correcto
- En Supabase Dashboard, ve a Settings → Database → Connection pooling

### Error en secuencias
```sql
-- Reiniciar secuencias manualmente:
SELECT setval('ventas_id_seq', (SELECT MAX(id) FROM ventas));
```

### Las políticas RLS bloquean todo
```sql
-- Temporalmente desabilitar RLS (solo para testing):
ALTER TABLE productos DISABLE ROW LEVEL SECURITY;
```

## 📚 Recursos Adicionales

- [Documentación Supabase](https://supabase.com/docs)
- [PostgreSQL vs SQLite](https://supabase.com/docs/guides/database/tables)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Python Client](https://supabase.com/docs/reference/python/introduction)

## ✅ Checklist Final

- [ ] Script ejecutado sin errores
- [ ] Todas las tablas creadas
- [ ] Datos importados correctamente
- [ ] Índices creados
- [ ] RLS configurado
- [ ] Connection string guardado en secrets.toml
- [ ] Librería supabase-py instalada
- [ ] Primera conexión exitosa desde Python
- [ ] Políticas RLS ajustadas a tus necesidades
- [ ] Backup del archivo pos_cremeria.db original guardado
