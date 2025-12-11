# 🔄 Sincronización Órdenes de Compra y Pedidos - Supabase

## ✅ Actualización Implementada

Se ha actualizado el sistema para sincronizar automáticamente con Supabase en tiempo real las nuevas tablas de **Órdenes de Compra** y **Pedidos de Reabastecimiento**.

### Módulos Actualizados:

1. **sync_manager.py** - Nuevas funciones:
   - `sync_orden_compra_to_supabase()` - Sincronizar una orden de compra
   - `sync_all_ordenes_compra_to_supabase()` - Sincronizar todas las órdenes
   - `sync_ordenes_compra_from_supabase()` - Cargar órdenes desde Supabase
   - `sync_pedido_to_supabase()` - Sincronizar un pedido
   - `sync_all_pedidos_to_supabase()` - Sincronizar todos los pedidos
   - `sync_pedidos_from_supabase()` - Cargar pedidos desde Supabase

2. **pedidos.py** - Sincronización automática:
   - Al inicio del módulo: Carga productos, pedidos y órdenes desde Supabase
   - Al crear pedido: Sincroniza inmediatamente
   - Al actualizar estado: Sincroniza cambios
   - Al eliminar pedido: Elimina también en Supabase
   - Al generar orden de compra: Sincroniza orden y pedidos actualizados

3. **finanzas.py** - Sincronización automática:
   - Al inicio del módulo: Carga órdenes de compra desde Supabase
   - Al marcar como pagada: Sincroniza orden actualizada
   - Al guardar notas: Sincroniza cambios

## 📋 Instrucciones de Configuración en Supabase

### Paso 1: Crear las Tablas

1. Abre tu proyecto en Supabase: https://nmeupnpdjctwbojmjrow.supabase.co
2. Ve a **SQL Editor**
3. Copia y pega el contenido del archivo `supabase_tables.sql`
4. Ejecuta el script presionando **RUN**

### Paso 2: Verificar las Tablas

Ve a **Table Editor** y verifica que se crearon:
- `ordenes_compra`
- `pedidos_reabastecimiento`

### Paso 3: Verificar Políticas RLS

En **Authentication > Policies** verifica que existen las políticas:
- "Permitir todas las operaciones en ordenes_compra"
- "Permitir todas las operaciones en pedidos_reabastecimiento"

## 🔄 Funcionamiento de la Sincronización

### Sincronización Automática:

**Al abrir el módulo de Pedidos:**
- ✅ Carga productos actualizados desde Supabase
- ✅ Carga pedidos actualizados desde Supabase
- ✅ Carga órdenes de compra desde Supabase
- 📢 Muestra notificación: "✅ Sincronizados: X productos, Y pedidos, Z órdenes"

**Al crear/modificar un pedido:**
- ✅ Guarda en SQLite local
- ✅ Sincroniza inmediatamente con Supabase
- ✅ Continúa funcionando si no hay internet

**Al generar orden de compra:**
- ✅ Guarda orden en SQLite local
- ✅ Actualiza pedidos con ID de orden
- ✅ Sincroniza orden con Supabase
- ✅ Sincroniza todos los pedidos actualizados

**Al marcar orden como pagada (finanzas):**
- ✅ Actualiza estado en SQLite local
- ✅ Registra en egresos
- ✅ Sincroniza orden con Supabase
- 📢 Muestra: "☁️ Orden sincronizada con Supabase"

**Al guardar notas en orden:**
- ✅ Guarda en SQLite local
- ✅ Sincroniza con Supabase
- 📢 Muestra: "☁️ Notas sincronizadas con Supabase"

### Modo Offline:

Si no hay conexión a internet:
- ✅ El sistema sigue funcionando normalmente en SQLite local
- ⚠️ No se sincroniza con Supabase
- 🔄 Al recuperar conexión, la próxima vez que abras el módulo se sincronizará automáticamente

## 🎯 Ventajas de la Sincronización

1. **Respaldo en la Nube**: Todos los datos están respaldados en Supabase
2. **Acceso Remoto**: Puedes acceder desde cualquier dispositivo
3. **Sincronización Automática**: No necesitas hacer nada manualmente
4. **Trabajo Offline**: Sigue funcionando sin internet
5. **Recuperación de Datos**: Si se borra la base de datos local, se puede recuperar desde Supabase
6. **Tiempo Real**: Los cambios se sincronizan inmediatamente

## 📊 Estructura de las Tablas

### ordenes_compra
```sql
id BIGSERIAL PRIMARY KEY              -- ID único autoincremental
fecha_creacion TIMESTAMP              -- Fecha de creación (automática)
total_orden DECIMAL(10,2)             -- Monto total de la orden
estado TEXT                           -- PENDIENTE o PAGADA
fecha_pago TIMESTAMP                  -- Fecha de pago (null si pendiente)
notas TEXT                            -- Notas adicionales
creado_por TEXT                       -- Usuario (default: 'admin')
```

### pedidos_reabastecimiento
```sql
id BIGSERIAL PRIMARY KEY              -- ID único autoincremental
codigo_producto TEXT                  -- Código del producto
nombre_producto TEXT                  -- Nombre del producto
stock_actual DECIMAL(10,2)            -- Stock al momento del pedido
stock_minimo DECIMAL(10,2)            -- Stock mínimo configurado
cantidad_sugerida DECIMAL(10,2)       -- Cantidad sugerida
cantidad_ordenada DECIMAL(10,2)       -- Cantidad ordenada
cantidad_recibida DECIMAL(10,2)       -- Cantidad recibida
precio_unitario DECIMAL(10,2)         -- Precio por unidad
costo_total DECIMAL(10,2)             -- Costo total
proveedor TEXT                        -- Nombre del proveedor
fecha_pedido TIMESTAMP                -- Fecha del pedido
fecha_recepcion TIMESTAMP             -- Fecha de recepción
estado TEXT                           -- PENDIENTE, RECIBIDO, CANCELADO
observaciones TEXT                    -- Observaciones adicionales
orden_compra_id BIGINT                -- FK a ordenes_compra
```

## 🔍 Verificación

Para verificar que la sincronización funciona:

1. **Crear un pedido:**
   - Ve al módulo Pedidos
   - Crea un pedido nuevo
   - Verifica en Supabase Table Editor → `pedidos_reabastecimiento`

2. **Generar orden de compra:**
   - Marca algunos pedidos como RECIBIDO
   - Genera una orden de compra
   - Verifica en Supabase Table Editor → `ordenes_compra`
   - Verifica que los pedidos tienen `orden_compra_id` asignado

3. **Marcar como pagada:**
   - Ve al módulo Finanzas → Egresos → Órdenes de Compra
   - Marca una orden como pagada
   - Verifica que el estado cambió a PAGADA en Supabase
   - Verifica que se registró en egresos

## 🆘 Solución de Problemas

### Si no se sincroniza:

1. **Verifica conexión a internet:**
   - El sistema muestra mensajes cuando está offline
   - Verifica que puedes acceder a https://nmeupnpdjctwbojmjrow.supabase.co

2. **Verifica que las tablas existen:**
   - Entra a Supabase → Table Editor
   - Busca `ordenes_compra` y `pedidos_reabastecimiento`
   - Si no existen, ejecuta `supabase_tables.sql`

3. **Verifica las políticas RLS:**
   - Ve a Authentication → Policies
   - Verifica que las políticas permiten todas las operaciones
   - Si no existen, ejecuta nuevamente el script SQL

4. **Revisa los logs:**
   - Abre la consola donde se ejecuta Streamlit
   - Busca mensajes de error relacionados con Supabase
   - Los errores empiezan con "Error al sincronizar..."

### Errores comunes:

**"Sin conexión a internet"**
- El sistema funciona normalmente offline
- Los datos se sincronizarán cuando se recupere la conexión

**"Supabase no retornó datos"**
- Verifica que las tablas existen
- Verifica las políticas RLS
- Revisa la consola de Supabase para errores

**"Error al sincronizar..."**
- Verifica que los campos coinciden entre SQLite y Supabase
- Verifica que no hay restricciones de llaves foráneas rotas

## ✨ Estado Actual

✅ **Productos**: Sincronización bidireccional completa
✅ **Pedidos**: Sincronización automática en tiempo real
✅ **Órdenes de Compra**: Sincronización automática en tiempo real
✅ **Inventario**: Sincronización al guardar cambios
✅ **Modo Offline**: Funcionando correctamente
✅ **Manejo de Errores**: Robusto con mensajes claros

## 📝 Notas Técnicas

- La sincronización usa `upsert` con `on_conflict` para evitar duplicados
- Los IDs se mantienen consistentes entre SQLite y Supabase
- Las fechas se guardan en formato ISO 8601
- Los decimales se manejan con precisión de 2 decimales
- Las eliminaciones en SQLite también se eliminan en Supabase
- La sincronización no bloquea la UI
