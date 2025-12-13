# VALIDACIÓN DE TABLAS DE FINANZAS EN SUPABASE

## ✅ RESUMEN DE AUDITORÍA

### Tablas del Módulo de Finanzas en SQLite Local:

1. **egresos_adicionales** (6 registros)
   - Columnas: id, fecha, tipo, descripcion, monto, observaciones, usuario, fuente
   - Uso: Egresos manuales (luz, agua, servicios, etc.)
   
2. **ingresos_pasivos** (1 registro)
   - Columnas: id, fecha, descripcion, monto, observaciones, usuario, fuente
   - Uso: Ingresos adicionales (renta, dividendos, etc.)
   
3. **caja_chica_movimientos** (0 registros)
   - Columnas: id, fecha, tipo, monto, descripcion, usuario, referencia_tipo, referencia_id
   - Uso: Movimientos de caja chica (ingresos/egresos/ajustes)
   
4. **ordenes_compra** (3 registros)
   - Columnas: id, fecha_creacion, total_orden, estado, fecha_pago, notas, creado_por, pedido_id
   - Uso: Órdenes de compra de pedidos

---

## 🔄 SINCRONIZACIÓN YA IMPLEMENTADA

Todas las funciones de sincronización YA EXISTEN en `sync_manager.py`:

### Funciones de Sincronización Local → Supabase:
- ✅ `sync_egreso_to_supabase()` - Línea 581
- ✅ `sync_ingreso_to_supabase()` - Línea 678
- ✅ `sync_caja_chica_movimiento_to_supabase()` - Línea 1002
- ✅ `sync_orden_compra_to_supabase()` - Línea 270

### Funciones de Sincronización Supabase → Local:
- ✅ `sync_egresos_from_supabase()` - Línea 629
- ✅ `sync_ingresos_from_supabase()` - Línea 726
- ✅ `sync_ordenes_compra_from_supabase()` - Línea 315
- ❓ `sync_caja_chica_from_supabase()` - NO ENCONTRADA (puede agregarse si es necesario)

---

## 📋 PASOS PARA COMPLETAR LA CONFIGURACIÓN

### 1. Crear Tablas en Supabase
Ejecuta el archivo: `supabase_finanzas_tablas.sql`

**Dónde ejecutarlo:**
- Ve a Supabase Dashboard
- Abre SQL Editor
- Copia y pega todo el contenido del archivo
- Haz clic en "Run"

**Qué incluye el script:**
- ✅ Creación de 4 tablas con estructura completa
- ✅ Índices para optimizar consultas
- ✅ Triggers para `updated_at` automático
- ✅ Políticas RLS (Row Level Security)
- ✅ Funciones RPC para upsert (inserción o actualización)

### 2. Verificar que las Tablas se Crearon

Ejecuta esta consulta en Supabase SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'egresos_adicionales', 
    'ingresos_pasivos', 
    'caja_chica_movimientos', 
    'ordenes_compra'
);
```

Deberías ver las 4 tablas listadas.

### 3. Verificar Funciones RPC

Ejecuta esta consulta:

```sql
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name IN (
    'upsert_egreso_adicional',
    'upsert_ingreso_pasivo',
    'upsert_caja_chica_movimiento',
    'upsert_orden_compra'
);
```

Deberías ver las 4 funciones RPC.

### 4. Sincronizar Datos Existentes

Una vez creadas las tablas en Supabase, sincroniza los datos existentes:

**Opción A: Usar la interfaz de Streamlit**
- Ve al módulo de Finanzas
- Busca el botón "⬆️ Sincronizar Todo" (si existe)

**Opción B: Ejecutar sincronización manual**

```python
# En Python console o crear script temporal:
from sync_manager import get_sync_manager
import sqlite3

sync = get_sync_manager()
conn = sqlite3.connect('pos_cremeria.db')
cur = conn.cursor()

# Sincronizar egresos
cur.execute("SELECT * FROM egresos_adicionales")
egresos = cur.fetchall()
for egreso in egresos:
    egreso_dict = {
        'id': egreso[0],
        'fecha': egreso[1],
        'tipo': egreso[2],
        'descripcion': egreso[3],
        'monto': egreso[4],
        'observaciones': egreso[5],
        'usuario': egreso[6],
        'fuente': egreso[7]
    }
    sync.sync_egreso_to_supabase(egreso_dict)

# Repetir para ingresos_pasivos, caja_chica_movimientos, ordenes_compra
conn.close()
```

---

## ⚠️ NOTAS IMPORTANTES

### Columnas Agregadas Recientemente:
- **egresos_adicionales.fuente** - Agregada hoy (Caja Chica/Banco)
- **ingresos_pasivos.fuente** - Agregada hoy (Caja Chica/Banco)

### Sincronización Automática:
El código ya llama automáticamente a las funciones de sincronización en:
- `finanzas.py` - Después de registrar egresos/ingresos
- `sync_manager.py` - Funciones de upsert ya implementadas

### RLS Policies:
Las políticas permiten:
- ✅ Lectura pública (SELECT)
- ✅ Inserción/Actualización solo autenticados

---

## ✅ CHECKLIST FINAL

- [ ] Ejecutar `supabase_finanzas_tablas.sql` en Supabase
- [ ] Verificar que las 4 tablas se crearon
- [ ] Verificar que las 4 funciones RPC existen
- [ ] Sincronizar datos existentes (6 egresos, 1 ingreso, 3 órdenes)
- [ ] Probar registro de nuevo egreso y verificar en Supabase
- [ ] Probar registro de nuevo ingreso y verificar en Supabase

---

## 🔍 COMANDO RÁPIDO DE VALIDACIÓN

Para verificar que todo está correcto, ejecuta en Python:

```python
from sync_manager import get_sync_manager

sync = get_sync_manager()
if sync.is_online():
    print("✅ Conexión a Supabase OK")
    
    # Verificar que las funciones RPC existen probando una sincronización
    test_egreso = {
        'id': 9999,
        'fecha': '2025-12-12 00:00:00',
        'tipo': 'Test',
        'descripcion': 'Test de validación',
        'monto': 1.0,
        'observaciones': 'Test',
        'usuario': 'Test',
        'fuente': 'Banco'
    }
    
    success, msg = sync.sync_egreso_to_supabase(test_egreso)
    if success:
        print("✅ Sincronización de egresos funcionando")
    else:
        print(f"❌ Error: {msg}")
else:
    print("❌ Sin conexión a Supabase")
```

---

Generado el: 2025-12-12
Módulo: Finanzas (finanzas.py)
