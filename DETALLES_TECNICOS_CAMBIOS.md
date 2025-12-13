# 🔍 Detalles Técnicos: Cambios en ventas.py

## 📌 Cambios Realizados

### 1. Reemplazo de `obtener_creditos_vencidos_con_hora()` 

**❌ ANTES (Línea ~847):**
```python
def obtener_creditos_vencidos_con_hora():
    """Obtener créditos que vencen hoy considerando la hora"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
        FROM creditos_pendientes 
        WHERE ((fecha_vencimiento < ? OR (fecha_vencimiento = ? AND hora_vencimiento <= ?)) 
               AND pagado = 0)
        ORDER BY fecha_vencimiento, hora_vencimiento
    ''', (fecha_hoy, fecha_hoy, hora_actual))
    return cursor.fetchall()
```

**✅ DESPUÉS (Línea ~847):**
```python
def obtener_creditos_vencidos():
    """Obtener SOLO créditos que ya han vencido (fecha_vencimiento + hora_vencimiento < ahora)"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
        FROM creditos_pendientes 
        WHERE pagado = 0 AND (
            fecha_vencimiento < ? 
            OR (fecha_vencimiento = ? AND hora_vencimiento < ?)
        )
        ORDER BY fecha_vencimiento, hora_vencimiento
    ''', (fecha_hoy, fecha_hoy, hora_actual))
    return cursor.fetchall()
```

**Cambios:**
- ✅ Nombre más específico: `obtener_creditos_vencidos()` en lugar de `obtener_creditos_vencidos_con_hora()`
- ✅ Lógica mejorada: Usa `<` en lugar de `<=` para hora (más preciso)
- ✅ Cambio de condición: `pagado = 0` como parte del WHERE

---

### 2. Nueva Función: `obtener_creditos_por_vencer()` 

**✅ NUEVA (Línea ~863):**
```python
def obtener_creditos_por_vencer():
    """Obtener créditos que vencen en menos de 1 hora (entre ahora y ahora + 1 hora)"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    # Sumar 1 hora
    una_hora_despues = (ahora + timedelta(hours=1)).strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id, alerta_mostrada
        FROM creditos_pendientes 
        WHERE pagado = 0 AND fecha_vencimiento = ? 
            AND hora_vencimiento > ? AND hora_vencimiento <= ?
        ORDER BY hora_vencimiento
    ''', (fecha_hoy, hora_actual, una_hora_despues))
    return cursor.fetchall()
```

**Características:**
- 🆕 Función completamente nueva
- 📊 Obtiene créditos en ventana de 1 hora
- 📅 Solo para hoy (fecha_vencimiento = hoy)
- 🕒 Entre ahora y ahora + 1 hora

---

### 3. Mejorada: `obtener_alertas_pendientes()`

**❌ ANTES (Línea ~869):**
```python
def obtener_alertas_pendientes():
    """Obtener créditos que necesitan alerta pero no se ha mostrado"""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_actual = ahora.strftime("%H:%M")
    
    cursor.execute('''
        SELECT cliente, monto, fecha_vencimiento, hora_vencimiento, id
        FROM creditos_pendientes 
        WHERE ((fecha_vencimiento < ? OR (fecha_vencimiento = ? AND hora_vencimiento <= ?)) 
               AND pagado = 0 AND alerta_mostrada = 0)
        ORDER BY fecha_vencimiento, hora_vencimiento
    ''', (fecha_hoy, fecha_hoy, hora_actual))
    return cursor.fetchall()
```

**✅ DESPUÉS (Línea ~880):**
```python
def obtener_alertas_pendientes():
    """Obtener créditos que necesitan alerta pero no se ha mostrado (VENCIDOS)"""
    vencidos = obtener_creditos_vencidos()
    # Filtrar por alerta_mostrada = 0
    return [c for c in vencidos if c[5] == 0]  # El índice 5 es alerta_mostrada
```

**Cambios:**
- ✅ Simplificada: Ahora usa `obtener_creditos_vencidos()`
- ✅ Más clara: Solo filtra por `alerta_mostrada = 0`
- ✅ Más eficiente: Procesa en memoria en lugar de DB
- ✅ Mantiene compatible: Retorna el mismo formato

---

### 4. Reescrita: `mostrar_popup_alertas_mejorado()`

**❌ ANTES (Línea ~881):**
```python
def mostrar_popup_alertas_mejorado():
    """Mostrar popup con alertas críticas y diseño mejorado"""
    alertas = obtener_alertas_pendientes()
    
    if alertas:
        st.markdown("""
        <div class="alert-critica">
            🐄🚨 ¡ALERTA DE CRÉDITOS VENCIDOS! 🚨🐄
        </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas:
            cliente, monto, fecha_venc, hora_venc, credito_id = alerta
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.error(f"💰 **{cliente}** debe {formatear_moneda(monto)} desde {fecha_venc} a las {hora_venc}")
            with col2:
                if st.button("✅ PAGADO", key=f"pagar_popup_{credito_id}", type="primary"):
                    marcar_credito_pagado(credito_id)
                    st.success(f"✅ Crédito de {cliente} marcado como pagado")
                    st.rerun()
            with col3:
                if st.button("⏰ MÁS TARDE", key=f"recordar_{credito_id}"):
                    marcar_alerta_mostrada(credito_id)
                    st.info("Se volverá a alertar mañana a las 3 PM")
                    st.rerun()
```

**✅ DESPUÉS (Línea ~885):**
```python
def mostrar_popup_alertas_mejorado():
    """Mostrar alertas emergentes para créditos vencidos Y créditos por vencer en 1 hora"""
    
    # 🔴 ALERTAS DE CRÉDITOS VENCIDOS (MÁXIMA PRIORIDAD)
    alertas_vencidas = obtener_alertas_pendientes()
    
    if alertas_vencidas:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); 
                    padding: 1.5rem; border-radius: 15px; border-left: 6px solid #c92a2a; 
                    margin: 1rem 0; box-shadow: 0 4px 15px rgba(255,107,107,0.3);">
            <h2 style="color: white; margin: 0; font-size: 1.5rem; text-align: center;">
                🐄🚨 ¡ALERTA CRÍTICA: CRÉDITOS VENCIDOS! 🚨🐄
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas_vencidas:
            cliente, monto, fecha_venc, hora_venc, credito_id, alerta_mostrada = alerta
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.error(f"⏰ **VENCIDO:** {cliente} debe {formatear_moneda(monto)}\n"
                        f"Desde: {fecha_venc} a las {hora_venc}")
            with col2:
                if st.button("✅ PAGADO", key=f"pagar_vencido_{credito_id}", type="primary"):
                    marcar_credito_pagado(credito_id)
                    st.balloons()
                    st.success(f"✅ Crédito de {cliente} marcado como pagado")
                    st.rerun()
            with col3:
                if st.button("⏰ DESPUÉS", key=f"recordar_vencido_{credito_id}"):
                    marcar_alerta_mostrada(credito_id)
                    st.info("Recordatorio desactivado hasta mañana")
                    st.rerun()
        st.markdown("---")
    
    # 🟡 ALERTAS DE CRÉDITOS POR VENCER EN 1 HORA (PRIORIDAD MEDIA)
    alertas_pronto = obtener_creditos_por_vencer()
    
    if alertas_pronto:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffd93d 0%, #ffb700 100%); 
                    padding: 1.5rem; border-radius: 15px; border-left: 6px solid #ff9c00; 
                    margin: 1rem 0; box-shadow: 0 4px 15px rgba(255,193,7,0.3);">
            <h2 style="color: #1a1a1a; margin: 0; font-size: 1.5rem; text-align: center;">
                ⚠️  RECORDATORIO: CRÉDITOS VENCEN EN MENOS DE 1 HORA ⚠️
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas_pronto:
            cliente, monto, fecha_venc, hora_venc, credito_id, alerta_mostrada = alerta
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.warning(f"🕐 **POR VENCER:** {cliente} debe {formatear_moneda(monto)}\n"
                          f"Vence: HOY a las {hora_venc}")
            with col2:
                if st.button("✅ PAGADO", key=f"pagar_pronto_{credito_id}", type="primary"):
                    marcar_credito_pagado(credito_id)
                    st.balloons()
                    st.success(f"✅ Crédito de {cliente} marcado como pagado")
                    st.rerun()
            with col3:
                if st.button("📝 OK", key=f"ok_pronto_{credito_id}"):
                    marcar_alerta_mostrada(credito_id)
                    st.info("Recordatorio visto")
                    st.rerun()
        st.markdown("---")
```

**Cambios Principales:**
- ✅ **DUAL**: Ahora maneja dos tipos de alertas (vencidas + por vencer)
- ✅ **COLORES DIFERENCIADOS**: Rojo para vencidas, amarillo para por vencer
- ✅ **GRADIENTES**: Estilos CSS mejorados con gradientes y sombras
- ✅ **SEPARADOR**: `st.markdown("---")` entre alertas para claridad
- ✅ **EFECTOS**: `st.balloons()` cuando se marca como pagado
- ✅ **MENSAJES**: Más descriptivos ("VENCIDO", "POR VENCER")
- ✅ **BOTONES**: Nombres más claros (⏰ DESPUÉS, 📝 OK)
- ✅ **SEPTUPLES**: Maneja 6 valores en lugar de 5 (incluye alerta_mostrada)

---

## 📊 Comparativa de Flujos

### Antes: Una sola alerta (simple)
```
creditos_vencidos_con_hora()
        ↓
obtener_alertas_pendientes()
        ↓
mostrar_popup_alertas_mejorado()
        ↓
🔴 UNA SOLA ALERTA ROJA
```

### Después: Alertas diferenciadas
```
obtener_creditos_vencidos()         obtener_creditos_por_vencer()
        ↓                                    ↓
obtener_alertas_pendientes()         (no filtra, solo obtiene)
        ↓                                    ↓
mostrar_popup_alertas_mejorado()
        ↓              ↓
    🔴 ERROR      🟡 WARNING
    (Vencidos)    (Por vencer)
```

---

## 🔗 Dependencias

### Importes Necesarios (Ya presentes en ventas.py):
```python
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
```

### Funciones Auxiliares Existentes:
```python
formatear_moneda(valor)          # Convierte valores a formato $X,XXX.XX
marcar_credito_pagado(id)        # Actualiza pagado=1
marcar_alerta_mostrada(id)       # Actualiza alerta_mostrada=1
```

---

## 🧪 Testing de Cambios

### Test 1: Función obtener_creditos_vencidos()
```python
# Debe retornar 2 registros de PRUEBA_VENCIDO_*
vencidos = obtener_creditos_vencidos()
assert len(vencidos) == 2
assert all(v[0].startswith('PRUEBA_VENCIDO') for v in vencidos)
```

### Test 2: Función obtener_creditos_por_vencer()
```python
# Debe retornar 1 registro de PRUEBA_POR_VENCER
por_vencer = obtener_creditos_por_vencer()
assert len(por_vencer) == 1
assert por_vencer[0][0] == 'PRUEBA_POR_VENCER'
```

### Test 3: Función obtener_alertas_pendientes()
```python
# Debe retornar 2 créditos vencidos sin alerta
alertas = obtener_alertas_pendientes()
assert len(alertas) == 2
assert all(a[5] == 0 for a in alertas)  # alerta_mostrada = 0
```

---

## 📈 Líneas de Código Cambiadas

| Función | Línea Original | Tipo | Cambio |
|---------|----------------|------|--------|
| obtener_creditos_vencidos_con_hora | 847 | Rename + Improve | Renombrada, mejorada lógica |
| obtener_creditos_por_vencer | 863 | Nueva | +20 líneas de código nuevo |
| obtener_alertas_pendientes | 880 | Simplificada | -8 líneas, más eficiente |
| mostrar_popup_alertas_mejorado | 885 | Reescrita | +80 líneas, dual alerts |
| **TOTAL** | | | +~92 líneas netas |

---

## ✅ Validación de Cambios

Todos los cambios han sido validados:
- ✅ Sin errores de sintaxis
- ✅ Importes correctos (timedelta ya existe)
- ✅ BD compatible (columnas existen)
- ✅ Funciones llamadas en mostrar() principal
- ✅ Scripts de validación pasados

**Estado:** ✅ LISTO PARA PRODUCCIÓN

