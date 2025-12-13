# Guía: Estructura de Código y Número de Producto

## 🎯 Objetivo

Tu sistema de POS ahora maneja múltiples formatos de entrada:
- **Código de barras:** barcode completo (13 dígitos)
- **Tickets de báscula:** códigos de 9 dígitos + peso (13 dígitos total)
- **Código numérico:** números simples (1-543)
- **Número de producto (PLU):** identificador único del producto en el catálogo

## 📊 Estructura de Datos

### En la Base de Datos (tabla `productos`)

| Campo | Tipo | Ejemplo | Propósito |
|-------|------|---------|-----------|
| `codigo` | TEXT | `7501111021029` o `172` o `208033201` | Identificador principal (barcode, PLU o código de báscula) |
| `numero_producto` | INTEGER | `80332` o `172` | PLU del catálogo iTegra (inmutable) |
| `nombre` | TEXT | `MANTEQUILLA EUGENIA 1KG` | Nombre del producto |
| `precio_normal` | REAL | `45.50` | Precio unitario |
| `stock` | INTEGER | `25` | Cantidad en unidades (para productos por unidad) |

### Ejemplos Reales

#### Producto 1: MANTEQUILLA EUGENIA 1KG (Con barcode de báscula)
```
codigo: 7501111021029
numero_producto: 80332
nombre: MANTEQUILLA EUGENIA 1KG
```

Cuando escaneas en la báscula → ticket `2080332010005`:
- Código extraído: `208033201`
- El sistema busca este código en BD
- Si no encuentra, busca últimos 5 dígitos: `33201` → PLU `33201`
- Si sigue sin encontrar, busca últimos 6 dígitos: `8033201` → PLU `8033201`

#### Producto 2: MANTEQUILLA EUGENIA 90GR (Importado de catálogo iTegra)
```
codigo: 172
numero_producto: 172
nombre: MANTEQUILLA EUGENIA 90GR
```

Cuando escaneas: `172`
- Búsqueda exacta por código → ENCONTRADO

## 🔍 Estrategia de Búsqueda en ventas.py

La función `obtener_producto_por_codigo()` usa estas estrategias en orden:

### Estrategia 1: Búsqueda Exacta
```sql
SELECT * FROM productos WHERE codigo = '7501111021029'
```
- Si el usuario escanea un barcode completo
- Si el usuario ingresa un código conocido

### Estrategia 2: Búsqueda por PLU
```sql
SELECT * FROM productos WHERE numero_producto = 172
```
- Si el usuario escanea un número simple
- Convierte texto a número automáticamente

### Estrategia 3: Extracción de Ticket de Báscula
```
Entrada: 2080332010005 (13 dígitos)
├─ Código de báscula: 208033201 (primeros 9)
├─ Peso: 001 decagramos = 10 gramos
├─ Checksum: 5
└─ Búsqueda: últimos 5-7 dígitos → PLU
```

### Estrategia 3B: Búsqueda LIKE para Báscula
```sql
SELECT * FROM productos WHERE codigo LIKE '750111102%'
```
- Si el código tiene 9 dígitos (código de báscula)
- Busca productos cuyo código **comience con esos dígitos**
- **CRÍTICO**: Maneja el caso donde tu barcode completo (7501111021029) se registró en BD
- Cuando la báscula escanea solo los primeros 9 dígitos (750111102), encuentra el producto

### Estrategia 4: Búsqueda Parcial
- Si el código es un barcode largo
- Busca productos cuyo código **termine igual**
- Útil para códigos truncados

## 📱 Flujo de POS

### Escenario 1: Usuario escanea barcode simple
```
Escanea: 172
↓
obtener_producto_por_codigo('172')
├─ Búsqueda exacta: codigo='172' ✓ ENCONTRADO
└─ Devuelve: MANTEQUILLA EUGENIA 90GR
```

### Escenario 2: Usuario escanea barcode completo
```
Escanea: 7501111021029
↓
obtener_producto_por_codigo('7501111021029')
├─ Búsqueda exacta: codigo='7501111021029' ✓ ENCONTRADO
└─ Devuelve: MANTEQUILLA EUGENIA 1KG
```

### Escenario 3: Báscula genera ticket de 13 dígitos
```
Escanea: 2080332010005 O 7501111021029
↓
parsear_codigo_bascula() extrae primeros 9 dígitos
↓
obtener_producto_por_codigo('208033201') O ('750111102')
├─ Búsqueda exacta: ✗ NO encontrado
├─ Búsqueda por PLU: ✗ NO encontrado
├─ Extracción de últimos 5-7: PLU extraído ✗ NO encontrado
├─ Búsqueda LIKE: codigo LIKE '750111102%' ✓ ENCONTRADO
└─ Devuelve: MANTEQUILLA EUGENIA 1KG (si está registrado con codigo=7501111021029)
```

**IMPORTANTE**: Si tu barcode completo está en la BD (7501111021029), la búsqueda LIKE lo encontrará automáticamente cuando la báscula envíe solo los primeros 9 dígitos (750111102).

## ⚙️ Cómo Configurar Correctamente

### Caso A: Productos Importados de iTegra (Mantequilla Eugenia GRANEL)
```
Situación actual:
  codigo: 172
  numero_producto: 172
  nombre: MANTEQUILLA EUGENIA GRANEL
  
Búsqueda funciona: Sí ✓
```

### Caso B: Productos con Barcode Completo
```
Ideal:
  codigo: 7501111021029 (barcode completo)
  numero_producto: 80332 (PLU del catálogo)
  nombre: MANTEQUILLA EUGENIA 1KG
  
Búsqueda:
  - Escanea barcode → codigo exacto ✓
  - Escanea PLU (80332) → numero_producto ✓
```

### Caso C: Productos con Código de Báscula
```
Necesario:
  codigo: 208033201 (código de báscula) O
  numero_producto: 33201 o 8033201 (PLU extraído)
  nombre: PRODUCTO
  
O crear entrada de mapeo en tabla auxiliar:
  CREATE TABLE bascula_mapeo (
    codigo_bascula TEXT PRIMARY KEY,
    producto_id INTEGER,
    FOREIGN KEY (producto_id) REFERENCES productos(rowid)
  )
```

## 🛠️ Cómo Agregar Código de Barras

Para asignar un barcode a un producto existente:

```bash
python agregar_codigo_barras.py 172 7501111021029
```

Esto actualiza:
- `productos.codigo = '7501111021029'` (de 172 a barcode completo)
- `productos.numero_producto = 172` (se mantiene igual)
- Inserta en `codigos_barras`: (código_anterior, PLU, nombre, precio)

## 📋 Tabla de Referencia Rápida

| Escanea | Tipo | Campo Búsqueda | Lógica |
|---------|------|---|---|
| `172` | Código simple | codigo | Búsqueda exacta |
| `7501111021029` | Barcode | codigo | Búsqueda exacta |
| `2080332010005` | Ticket báscula | numero_producto | Extracción y búsqueda |
| Desconocido | Unknown | numero_producto | Fallback a búsqueda parcial |

## 🐛 Diagnosticar Problemas

### "Producto no encontrado" al escanear ticket

1. Verifica que el producto esté en BD:
   ```python
   SELECT * FROM productos WHERE codigo LIKE '208033201%' 
   OR numero_producto = 33201
   ```

2. Si no existe, agrégalo con `sincronizar_plu_a_productos.py`

3. Si existe pero sigue sin encontrar:
   - Verifica el formato del ticket (debe ser 13 dígitos)
   - Revisa los dígitos extraídos manualmente

### "Múltiples productos encontrados"

- Tu código es demasiado genérico (p. ej., últimos 3 dígitos)
- Usa códigos más específicos de 9+ dígitos

## ✅ Checklist de Configuración

- [ ] Todos los productos importados tienen `numero_producto` populado
- [ ] Barcode asignados tienen `codigo` = barcode completo, `numero_producto` = PLU original
- [ ] Productos viejos sin `numero_producto` fueron eliminados
- [ ] Tabla `codigos_barras` tiene registro de mapeos
- [ ] Probaste escanear barcode en POS
- [ ] Probaste escanear ticket de báscula en POS
- [ ] Probaste ingresar código manual en POS

## 📞 Soporte

Si un tipo de código no se encuentra:
1. Copia el código exacto escaneado
2. Busca en BD: `SELECT * FROM productos WHERE codigo LIKE '%{ultimos_6_digitos}%'`
3. Valida que existe y actualiza la estrategia si es necesario
