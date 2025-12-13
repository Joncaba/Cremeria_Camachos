# Resumen de Cambios: Estructura Código + Número de Producto

## 🎯 Problema Resuelto

Tu sistema ahora maneja correctamente múltiples formatos de entrada de códigos:

✅ **Código simple**: `172` → Busca por código o número_producto
✅ **Barcode completo**: `7501111021029` → Busca exacta
✅ **Ticket de báscula (13 dígitos)**: `7501111021029` → Extrae primeros 9 (`750111102`) y busca con LIKE
✅ **Código de báscula (9 dígitos)**: `750111102` → Busca LIKE y extrae PLU

## 📋 Cambios Realizados

### 1. Actualizado `ventas.py` - Función `obtener_producto_por_codigo()`

**Nueva estrategia de búsqueda (en orden):**

1. **Búsqueda exacta**: `WHERE codigo = ?`
2. **Búsqueda por PLU**: `WHERE numero_producto = ?` (si es número)
3. **Extracción de báscula**: Extrae últimos 5-7 dígitos, busca por `numero_producto`
4. **Búsqueda LIKE para báscula**: `WHERE codigo LIKE '750111102%'` ← **NUEVA**
5. **Búsqueda parcial**: `WHERE codigo LIKE '%{últimos_6}'`

**Beneficio**: Cuando la báscula envía solo los primeros 9 dígitos de un barcode completo registrado en BD, ahora lo encuentra automáticamente.

### 2. Actualizado `inventario.py`

**Columnas agregadas:**
- Ahora muestra `numero_producto` (PLU) en la tabla de productos
- Etiqueta: `🔢 PLU` para fácil identificación

**Ubicaciones:**
- Tabla de alertas de stock bajo
- Tabla principal de editor de inventario
- Fácil identificación visual de números PLU

### 3. Script de Diagnóstico Creado

**Archivo**: `diagnosticar_busqueda.py`

**Uso:**
```bash
python diagnosticar_busqueda.py 172
python diagnosticar_busqueda.py 7501111021029
python diagnosticar_busqueda.py 2080332010005
```

**Beneficio**: Verifica si un código será encontrado ANTES de escanear en el POS

### 4. Documentación Actualizada

**Archivos:**
- `GUIA_CODIGO_NUMERO_PRODUCTO.md` - Guía completa
- Este archivo - Resumen ejecutivo

## ✅ Flujo Ahora Funciona

### Caso 1: MANTEQUILLA EUGENIA 90GR (Código simple)
```
BD:
  codigo: 172
  numero_producto: 172
  
Escaneado: 172 → ENCONTRADO ✓
```

### Caso 2: MANTEQUILLA EUGENIA 1KG (Barcode completo)
```
BD:
  codigo: 7501111021029
  numero_producto: 7501111021029

Escaneado completo: 7501111021029 → ENCONTRADO ✓
Ticket báscula: 7501111021029 → Extrae 750111102 → ENCONTRADO ✓ (búsqueda LIKE)
```

### Caso 3: Cualquier producto con PLU simple
```
BD:
  codigo: 200006500 (barcode)
  numero_producto: 123

Escaneado: 123 → ENCONTRADO ✓ (búsqueda por numero_producto)
```

## 🔍 Cómo Verificar Tu Sistema

### Test 1: Verifica que productos existan
```bash
# En la terminal
sqlite3 pos_cremeria.db "SELECT codigo, numero_producto, nombre FROM productos LIMIT 5;"
```

### Test 2: Diagnostica un código específico
```bash
# Reemplaza 172 con tu código
python diagnosticar_busqueda.py 172
```

### Test 3: Prueba en POS (ventas.py)
1. Abre el POS (ventas.py)
2. Escanea un código que exista
3. Debería encontrar el producto

### Test 4: Prueba con tickets de báscula
1. Escanea un ticket completo de 13 dígitos
2. El sistema extrae los primeros 9 dígitos
3. Busca en BD con LIKE
4. Debería encontrar el producto

## 🛠️ Configuración Recomendada

### Mejor Estructura Para Productos

#### Opción A: Con Barcode (RECOMENDADA)
```
codigo: 7501111021029    ← Barcode completo (desde báscula o proveedor)
numero_producto: 80332   ← PLU simple (para búsquedas rápidas)
nombre: MANTEQUILLA EUGENIA 1KG
```

**Ventajas:**
- Búsqueda exacta rápida
- Ticket de báscula funciona automáticamente
- PLU simple para referencias manuales

**Para asignar:**
```bash
python agregar_codigo_barras.py 80332 7501111021029
```

#### Opción B: Con Código iTegra
```
codigo: 172              ← Código PLU simple
numero_producto: 172     ← Mismo número
nombre: MANTEQUILLA EUGENIA 90GR
```

**Ventajas:**
- Búsqueda rápida
- No hay ambigüedad
- Fácil de recordar

## 📱 Flujo de POS Actualizado

```
Usuario escanea código
        ↓
parsear_codigo_bascula() - Detecta si es ticket (13 dígitos) y extrae primeros 9
        ↓
obtener_producto_por_codigo() - Busca con 5 estrategias
        ↓
        ├─ Búsqueda exacta
        ├─ Búsqueda por PLU
        ├─ Extracción de PLU
        ├─ LIKE para báscula ← NUEVA ESTRATEGIA
        └─ Búsqueda parcial
        ↓
ENCONTRADO → Muestra producto en POS ✓
NO ENCONTRADO → Muestra alerta de producto no encontrado
```

## ⚠️ Problemas Comunes y Soluciones

### "Producto no encontrado" al escanear

1. **Verifica que existe:**
   ```bash
   python diagnosticar_busqueda.py <tu_codigo>
   ```

2. **Si sale ERROR:**
   - El producto no está en BD
   - Importa con: `python sincronizar_plu_a_productos.py`
   - O agrega manualmente en inventario

3. **Si sale ENCONTRADO pero no en POS:**
   - Reinicia el POS (ctrl+c y vuelve a abrir)
   - Verifica en inventario que el stock > 0

### "Múltiples productos encontrados"

- Tus códigos son demasiado similares
- Usa códigos más específicos (9+ dígitos)
- Revisa BD: `SELECT * FROM productos WHERE codigo LIKE '%XXX'`

### Barcode no funciona en báscula

- Verifica que el barcode esté registrado en BD
- Usa diagnóstico: `python diagnosticar_busqueda.py <barcode>`
- Si no funciona, agrégalo: `python agregar_codigo_barras.py <plu> <barcode>`

## 📊 Estructura BD Final

### Tabla `productos`

| Campo | Tipo | Ejemplo | Propósito |
|-------|------|---------|-----------|
| codigo | TEXT | `7501111021029` | Identificador (barcode, PLU o código bascula) |
| numero_producto | INTEGER | `80332` | PLU del catálogo (inmutable) |
| nombre | TEXT | `MANTEQUILLA EUGENIA 1KG` | Descripción |
| precio_normal | REAL | `45.50` | Precio de venta |
| stock | INTEGER | `25` | Cantidad |

### Tabla `codigos_barras` (Auxiliar)

Mapeo histórico de cambios de código:

| campo | codigo_anterior | plu | nombre | precio |
|-------|-----------------|-----|--------|--------|
| 1 | 172 | 172 | MANTEQUILLA EUGENIA 90GR | 32.00 |

## ✨ Beneficios del Nueva Estructura

1. ✅ **Compatible con báscula**: Automáticamente extrae y busca
2. ✅ **Búsqueda flexible**: 5 estrategias diferentes
3. ✅ **Sin ambigüedad**: `codigo` vs `numero_producto` claros
4. ✅ **Visible en inventario**: Ves el PLU de cada producto
5. ✅ **Diagnóstico fácil**: Usa `diagnosticar_busqueda.py`
6. ✅ **Historial**: Tabla `codigos_barras` rastrea cambios

## 🚀 Próximos Pasos Recomendados

### Inmediatos
1. ✅ Reinicia el POS para cargar cambios
2. ✅ Prueba con `diagnosticar_busqueda.py <tu_codigo>`
3. ✅ Escanea en POS para verificar

### Corto Plazo
1. Revisa BD para productos sin `numero_producto`
2. Completa campos faltantes
3. Crea mapeo de códigos de báscula si es necesario

### Documentación
1. Muestra esta guía al staff
2. Explica que ahora funciona con báscula
3. Instala diagnóstico en máquinas para troubleshooting

## 📞 Soporte

**Para diagnosticar cualquier código:**
```bash
python diagnosticar_busqueda.py <codigo>
```

**Para ver estructura BD:**
```bash
# Windows PowerShell
sqlite3 pos_cremeria.db "SELECT codigo, numero_producto, nombre FROM productos LIMIT 10;"
```

**Para probar en POS:**
- Abre inventario y verifica que veas número_producto (columna PLU)
- Escanea un código que exista
- Debería agregarse al carrito
