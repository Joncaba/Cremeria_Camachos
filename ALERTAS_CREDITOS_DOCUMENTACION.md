# 🐄 Sistema de Alertas Emergentes de Créditos - Documentación

## Descripción General

Se ha implementado un **sistema completo de alertas emergentes** para créditos pendientes en el módulo **Punto de Venta**. El sistema muestra:

1. **🔴 Alertas Críticas**: Créditos que **YA HAN VENCIDO**
2. **🟡 Recordatorios**: Créditos que vencen **EN MENOS DE 1 HORA**

---

## Características del Sistema

### ✅ Alertas Vencidas (🔴 ERROR - MÁXIMA PRIORIDAD)

Se muestran cuando:
- El crédito no ha sido pagado (`pagado = 0`)
- La fecha de vencimiento + hora de vencimiento **es menor a la hora actual**
- La alerta **aún no ha sido vista** (`alerta_mostrada = 0`)

**Ejemplo:**
```
Hoy: 2025-12-12 10:03
Crédito vence: 2025-12-11 15:00  ← YA PASÓ
→ Mostrar alerta 🔴 ERROR
```

**Acciones disponibles:**
- ✅ **PAGADO**: Marca el crédito como pagado (`pagado = 1`)
- ⏰ **DESPUÉS**: Marca la alerta como vista (`alerta_mostrada = 1`) - se mostrará nuevamente mañana

### ⚠️ Alertas por Vencer (🟡 WARNING - PRIORIDAD MEDIA)

Se muestran cuando:
- El crédito no ha sido pagado (`pagado = 0`)
- Vence **hoy**
- El tiempo de vencimiento está entre **ahora y ahora + 1 hora**

**Ejemplo:**
```
Hoy: 2025-12-12 10:03
Crédito vence: 2025-12-12 10:33  ← EN 30 MINUTOS
→ Mostrar alerta 🟡 WARNING
```

**Acciones disponibles:**
- ✅ **PAGADO**: Marca el crédito como pagado (`pagado = 1`)
- 📝 **OK**: Marca la alerta como vista (`alerta_mostrada = 1`)

---

## Flujo de Funcionamiento

```
┌─────────────────────────────────────────────────────────┐
│ Usuario abre "Punto de Venta"                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │ mostrar_popup_alertas   │
        │ _mejorado()             │
        └────────┬────────────────┘
                 │
    ┌────────────┴────────────────┐
    │                             │
    ▼                             ▼
┌─────────────────────┐   ┌──────────────────────┐
│ Obtener créditos    │   │ Obtener créditos     │
│ VENCIDOS            │   │ POR VENCER           │
│                     │   │                      │
│ obtener_alertas_    │   │ obtener_creditos_    │
│ pendientes()        │   │ por_vencer()         │
└────────┬────────────┘   └──────┬───────────────┘
         │                       │
    ┌────┴─────────────────────┬─┘
    │                          │
    ▼                          ▼
┌──────────────────────┐  ┌──────────────────────┐
│ MOSTRAR ALERTAS      │  │ MOSTRAR RECORDATORIOS│
│ 🔴 ROJAS - ERROR     │  │ 🟡 AMARILLAS - WARN  │
│                      │  │                      │
│ Con botones:         │  │ Con botones:         │
│ ✅ PAGADO            │  │ ✅ PAGADO            │
│ ⏰ DESPUÉS           │  │ 📝 OK                │
└────────┬─────────────┘  └──────┬───────────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │ Al hacer    │
              │ clic en     │
              │ botones:    │
              │             │
              │ ✅ Actualizar│
              │    estado   │
              │ 🔄 Rerun    │
              │    página   │
              └─────────────┘
```

---

## Funciones Implementadas

### 1. `obtener_creditos_vencidos()`
```python
def obtener_creditos_vencidos():
    """Obtener SOLO créditos que ya han vencido"""
    # Retorna: [(cliente, monto, fecha_venc, hora_venc, id, alerta_mostrada), ...]
```

**Lógica:**
- Busca créditos con `pagado = 0`
- Filtra por: `fecha_vencimiento < hoy` O `(fecha_vencimiento = hoy AND hora < ahora)`
- Ordena por fecha y hora

---

### 2. `obtener_creditos_por_vencer()`
```python
def obtener_creditos_por_vencer():
    """Obtener créditos que vencen en menos de 1 hora"""
    # Retorna: [(cliente, monto, fecha_venc, hora_venc, id, alerta_mostrada), ...]
```

**Lógica:**
- Busca créditos con `pagado = 0`
- Filtra por: `fecha_vencimiento = hoy` Y `ahora < hora_vencimiento <= ahora + 1 hora`
- Ordena por hora de vencimiento

---

### 3. `obtener_alertas_pendientes()`
```python
def obtener_alertas_pendientes():
    """Obtener créditos vencidos CON ALERTA PENDIENTE"""
    # Retorna: solo créditos vencidos donde alerta_mostrada = 0
```

**Lógica:**
- Llama a `obtener_creditos_vencidos()`
- Filtra por `alerta_mostrada = 0`

---

### 4. `marcar_alerta_mostrada(credito_id)`
```python
def marcar_alerta_mostrada(credito_id):
    """Marcar que la alerta ya fue vista"""
    # UPDATE creditos_pendientes SET alerta_mostrada = 1 WHERE id = ?
```

---

### 5. `marcar_credito_pagado(credito_id)`
```python
def marcar_credito_pagado(credito_id):
    """Marcar un crédito como pagado"""
    # UPDATE creditos_pendientes SET pagado = 1 WHERE id = ?
```

---

### 6. `mostrar_popup_alertas_mejorado()`
```python
def mostrar_popup_alertas_mejorado():
    """Mostrar alertas emergentes para créditos vencidos Y por vencer"""
    # Mostrar 🔴 ERROR para vencidos
    # Mostrar 🟡 WARNING para por vencer
    # Incluir botones de acción
```

---

## Estructura de la Tabla `creditos_pendientes`

```sql
CREATE TABLE creditos_pendientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    monto REAL NOT NULL,
    fecha_venta TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,        -- Fecha del vencimiento (YYYY-MM-DD)
    hora_vencimiento TEXT DEFAULT '15:00',  -- Hora del vencimiento (HH:MM)
    venta_id INTEGER,
    pagado INTEGER DEFAULT 0,               -- 0 = Pendiente, 1 = Pagado
    alerta_mostrada INTEGER DEFAULT 0,      -- 0 = No visto, 1 = Alerta mostrada
    FOREIGN KEY (venta_id) REFERENCES ventas (id)
)
```

---

## Ejemplo de Uso

### Escenario 1: Crédito Vencido Hace 1 Día

```
BD:
- cliente: "Juan Pérez"
- monto: $500.00
- fecha_vencimiento: "2025-12-11"
- hora_vencimiento: "15:00"
- pagado: 0
- alerta_mostrada: 0

Hora actual: 2025-12-12 10:03

Resultado:
✅ obtener_creditos_vencidos() retorna este registro
✅ obtener_alertas_pendientes() filtra por alerta_mostrada=0 → lo retorna
✅ mostrar_popup_alertas_mejorado() muestra:
   🔴 ¡ALERTA CRÍTICA!
   ⏰ VENCIDO: Juan Pérez debe $500.00
   Desde: 2025-12-11 a las 15:00
   [✅ PAGADO] [⏰ DESPUÉS]
```

### Escenario 2: Crédito Vence en 30 Minutos

```
BD:
- cliente: "María López"
- monto: $1,200.00
- fecha_vencimiento: "2025-12-12"
- hora_vencimiento: "10:33"
- pagado: 0
- alerta_mostrada: 0

Hora actual: 2025-12-12 10:03

Resultado:
✅ obtener_creditos_por_vencer() retorna este registro
✅ mostrar_popup_alertas_mejorado() muestra:
   🟡 ⚠️  RECORDATORIO: CRÉDITOS VENCEN EN MENOS DE 1 HORA
   🕐 POR VENCER: María López debe $1,200.00
   Vence: HOY a las 10:33
   [✅ PAGADO] [📝 OK]
```

### Escenario 3: Usuario Hace Clic en ✅ PAGADO

```
1. Usuario hace clic en "✅ PAGADO"
2. Se ejecuta: marcar_credito_pagado(credito_id)
3. UPDATE creditos_pendientes SET pagado = 1 WHERE id = ?
4. st.balloons() - efecto visual
5. st.success() - mensaje de confirmación
6. st.rerun() - recargar página
7. El crédito YA NO aparece en alertas (pagado=1)
```

### Escenario 4: Usuario Hace Clic en ⏰ DESPUÉS

```
1. Usuario hace clic en "⏰ DESPUÉS"
2. Se ejecuta: marcar_alerta_mostrada(credito_id)
3. UPDATE creditos_pendientes SET alerta_mostrada = 1 WHERE id = ?
4. El crédito SIGUE PENDIENTE pero NO vuelve a alertar hoy
5. Mañana a las 15:00 si aún no está pagado, volverá a alertar
```

---

## Testing

Se han creado dos scripts para validar la funcionalidad:

### `test_alertas_creditos.py`
Inserta 6 créditos de prueba con diferentes estados:
1. ✅ Vencido hace 1 día
2. ✅ Vencido hoy hace 1 hora
3. ⚠️ Por vencer en 30 minutos
4. Crédito normal (no alerta)
5. Crédito futuro (no alerta)
6. Crédito pagado (no alerta)

**Uso:**
```bash
python test_alertas_creditos.py
```

### `verificar_alertas.py`
Valida que las funciones de alertas trabajen correctamente:
- Verifica `obtener_creditos_vencidos()`
- Verifica `obtener_creditos_por_vencer()`
- Verifica `obtener_alertas_pendientes()`
- Muestra estadísticas del sistema

**Uso:**
```bash
python verificar_alertas.py
```

---

## Verificación en Punto de Venta

1. Ejecutar la aplicación:
   ```bash
   streamlit run main.py
   ```

2. Iniciar sesión con admin:
   ```
   Usuario: admin
   Contraseña: Creme$123
   ```

3. Hacer clic en "Punto de Venta"

4. **Deberías ver:**
   - 🔴 Alerta roja (ERROR) para créditos vencidos
   - 🟡 Alerta amarilla (WARNING) para créditos por vencer en < 1 hora
   - Botones de acción para cada alerta

---

## Cambios en el Código

### Archivo: `ventas.py`

**Nuevas funciones:**
- `obtener_creditos_vencidos()` - Línea ~847
- `obtener_creditos_por_vencer()` - Nueva
- `obtener_alertas_pendientes()` (MEJORADA) - Mantiene alerta_mostrada
- `mostrar_popup_alertas_mejorado()` (REESCRITA) - Maneja ambos tipos de alertas

**Cambios en estructura:**
- La tabla `creditos_pendientes` ya tenía `hora_vencimiento` y `alerta_mostrada`
- Se utilizan para implementar alertas más precisas

---

## Próximas Mejoras Posibles

1. **Alertas por email/SMS** - Notificar a clientes de créditos vencidos
2. **Historial de alertas** - Guardar cuándo se mostró cada alerta
3. **Alertas personalizables** - Permitir configurar hora de alerta (no solo 1 hora antes)
4. **Recordatorios automáticos** - Mostrar nuevamente si usuario sale de Punto de Venta
5. **Deuda por cliente** - Vista de deuda total por cliente
6. **Pagos parciales** - Permitir pagar solo parte del crédito

---

## Contacto y Soporte

Para reportar problemas o sugerir mejoras, contacta al equipo de desarrollo.

**Última actualización:** 2025-12-12
