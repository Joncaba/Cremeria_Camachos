# 🎉 Sistema de Alertas Emergentes - Guía Rápida

## ✨ ¿Qué se implementó?

Tu solicitud: **"creditos pendientes no se estan mostrando de manera emergente al inicio cuando ya han expirado la fecha de pago, necesito que se recuerden cuando hayan sido expirados y una hora antes de las 4pm"**

### ✅ Solución Implementada:

1. **🔴 Alertas Críticas** - Se muestran cuando un crédito YA HA VENCIDO
2. **🟡 Recordatorios** - Se muestran cuando un crédito vence EN MENOS DE 1 HORA
3. **Emergentes** - Se muestran automáticamente al abrir "Punto de Venta"

---

## 🚀 Cómo Probar

### Opción A: Prueba Rápida (Recomendado)

```bash
# 1. Validar que todo está OK
python validar_sistema_alertas.py

# 2. Ejecutar la app
streamlit run main.py

# 3. Iniciar sesión: admin / Creme$123
# 4. Ir a "Punto de Venta"
# 5. ¡Deberías ver las alertas automáticamente!
```

### Opción B: Prueba Completa

```bash
# 1. Insertar datos de prueba
python test_alertas_creditos.py

# 2. Verificar que funcionan
python verificar_alertas.py

# 3. Validar el sistema completo
python validar_sistema_alertas.py

# 4. Ejecutar la app
streamlit run main.py

# 5. Cuando termines, limpiar
python limpiar_prueba_alertas.py
```

---

## 📊 Qué Verás

### 🔴 Alerta de Crédito Vencido (ROJO)
```
┌─────────────────────────────────────────┐
│ 🐄🚨 ¡ALERTA CRÍTICA: CRÉDITOS VENCIDOS! │
├─────────────────────────────────────────┤
│ ⏰ VENCIDO: Cliente debe $1,000.00      │
│ Desde: 2025-12-11 a las 15:00           │
│ [✅ PAGADO] [⏰ DESPUÉS]                 │
└─────────────────────────────────────────┘
```

### 🟡 Alerta de Crédito por Vencer (AMARILLO)
```
┌─────────────────────────────────────────┐
│ ⚠️  RECORDATORIO: CRÉDITOS VENCEN EN     │
│     MENOS DE 1 HORA ⚠️                  │
├─────────────────────────────────────────┤
│ 🕐 POR VENCER: Cliente debe $500.00    │
│ Vence: HOY a las 16:45                  │
│ [✅ PAGADO] [📝 OK]                     │
└─────────────────────────────────────────┘
```

---

## 🎯 Cómo Funcionan los Botones

### ✅ PAGADO
- **Qué hace**: Marca el crédito como pagado
- **Resultado**: La alerta desaparece, el crédito sale del sistema
- **BD**: Actualiza `pagado = 1`

### ⏰ DESPUÉS (Créditos Vencidos)
- **Qué hace**: Desactiva la alerta por ahora
- **Resultado**: No vuelve a alertar hoy
- **BD**: Actualiza `alerta_mostrada = 1`
- **Nota**: Mañana a las 15:00 volverá a alertar si sigue sin pagarse

### 📝 OK (Créditos por Vencer)
- **Qué hace**: Marca que viste el recordatorio
- **Resultado**: La alerta desaparece
- **BD**: Actualiza `alerta_mostrada = 1`

---

## 📁 Archivos Creados/Modificados

### ✏️ Modificado
- **`ventas.py`** - Agregadas 6 funciones nuevas para alertas

### ✨ Creados
- **`test_alertas_creditos.py`** - Script para insertar datos de prueba
- **`verificar_alertas.py`** - Script para validar funcionamiento
- **`validar_sistema_alertas.py`** - Validación rápida completa
- **`limpiar_prueba_alertas.py`** - Limpia datos de prueba
- **`ALERTAS_CREDITOS_DOCUMENTACION.md`** - Documentación técnica completa
- **`CAMBIOS_ALERTAS_CREDITOS.md`** - Resumen de cambios

---

## 🔧 Funciones Nuevas en ventas.py

```python
# Obtiene créditos vencidos
obtener_creditos_vencidos()

# Obtiene créditos por vencer en < 1 hora
obtener_creditos_por_vencer()

# Obtiene créditos vencidos sin alerta mostrada
obtener_alertas_pendientes()

# Marca una alerta como mostrada
marcar_alerta_mostrada(credito_id)

# Marca un crédito como pagado
marcar_credito_pagado(credito_id)

# Muestra las alertas en la interfaz
mostrar_popup_alertas_mejorado()
```

---

## 💾 Base de Datos

La tabla `creditos_pendientes` usa estos campos:

- `id` - Identificador único
- `cliente` - Nombre del cliente
- `monto` - Cantidad pendiente
- `fecha_vencimiento` - Fecha del vencimiento (YYYY-MM-DD)
- `hora_vencimiento` - Hora del vencimiento (HH:MM) - Default: 15:00
- `pagado` - 0 = Pendiente, 1 = Pagado
- `alerta_mostrada` - 0 = Sin mostrar, 1 = Ya mostrada

---

## ❓ Preguntas Frecuentes

### P: ¿Por qué no veo alertas?
**R:** 
1. Valida con: `python validar_sistema_alertas.py`
2. Asegúrate de que hay créditos vencidos en la BD
3. Verifica que `pagado = 0` para esos créditos

### P: ¿Cómo agrego créditos reales?
**R:** Los créditos se crean automáticamente en Punto de Venta cuando seleccionas "Crédito" como forma de pago. Especifica la fecha y hora de vencimiento.

### P: ¿Qué pasa si cambio la hora del sistema?
**R:** Las alertas se recalculan automáticamente basándose en la hora actual del sistema.

### P: ¿Puedo cambiar la hora de vencimiento por defecto?
**R:** Sí, está en la línea de creación de tabla (Default: '15:00'). Modifica según necesites.

### P: ¿Las alertas se repiten?
**R:** No. Se muestran una sola vez por día usando `alerta_mostrada`. Puedes hacer clic en "⏰ DESPUÉS" para ocultar.

---

## 🆘 Soporte Rápido

Si algo no funciona:

```bash
# 1. Validar el sistema
python validar_sistema_alertas.py

# 2. Ver detalles de alertas
python verificar_alertas.py

# 3. Ver documentación completa
cat ALERTAS_CREDITOS_DOCUMENTACION.md
```

---

## 📝 Próximas Mejoras Posibles

- [ ] Alertas por email/SMS a clientes
- [ ] Historial de alertas mostradas
- [ ] Alertas personalizables por cliente
- [ ] Recordatorios automáticos cada hora
- [ ] Reportes de créditos vencidos
- [ ] Pagos parciales

---

**¿Preguntas?** Revisa `ALERTAS_CREDITOS_DOCUMENTACION.md` para detalles técnicos completos.

**Estado:** ✅ Listo para usar  
**Última actualización:** 2025-12-12
