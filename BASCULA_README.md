# Decodificación de Códigos de Báscula

## Problema Solucionado

El sistema de ventas ahora puede decodificar correctamente los códigos de 13 dígitos que genera tu báscula.

### Formato de Código de Báscula

```
2080332010005
│││││││││││││
└────┬────┘└┬┘└─┬─┘
     │      │   └─────── Control/Descarte (4 dígitos)
     │      └──────────── Cantidad (2 dígitos)
     └────────────────── Código de Producto (7 dígitos)
```

**Ejemplo:**
- Código: `2080332010005`
- Producto: `2080332` → MANTEQUILLA EUGENIA 1KG
- Cantidad: `01` → 1 unidad
- Control: `0005` → (descarte)

## Cómo Funciona

### 1. **Tabla de Mapeo** (`bascula_mapeo`)

Se creó una tabla auxiliar en la BD que mapea códigos de báscula (7 dígitos) a códigos de productos:

```
codigo_bascula  │ producto_codigo     │ nombre
─────────────────┼────────────────────┼─────────────────────────
2000072         │ 72                 │ JOCOQUE
2000140         │ 20001400           │ Huevo Blanco
2080332         │ 7501111021029      │ MANTEQUILLA EUGENIA 1KG
```

### 2. **Función de Búsqueda** (`obtener_producto_por_codigo()`)

La función en `ventas.py` ahora:

1. **Extrae el código de 7 dígitos** del código completo de 13
2. **Busca en la tabla `bascula_mapeo`** primero
3. **Busca por código exacto** si no hay mapeo
4. **Busca por LIKE** como fallback

### 3. **Estrategias de Búsqueda** (en orden)

```
ESTRATEGIA 0: Código de báscula (13 dígitos)
   └─ Extrae primeros 7 dígitos
   └─ Busca en bascula_mapeo
   └─ Busca exacta por código
   └─ Busca LIKE

ESTRATEGIA 1: Búsqueda exacta por código
ESTRATEGIA 2: Búsqueda por número_producto (PLU)
ESTRATEGIA 3: Códigos de 9 dígitos + mapeo
ESTRATEGIA 4: Barcodes largos (últimos 6 dígitos)
```

## Mapeos Actuales

| Código Báscula | Código Producto | Nombre |
|---|---|---|
| `2000072` | `72` | JOCOQUE |
| `2000140` | `20001400` | Huevo Blanco |
| `2080332` | `7501111021029` | MANTEQUILLA EUGENIA 1KG |

## Agregar Nuevos Productos

Cuando agregues un nuevo producto a tu sistema de báscula, necesitas crear el mapeo:

### Opción 1: Script Interactivo

```powershell
python agregar_mapeo.py buscar MANTEQUILLA
```

Esto mostrará todos los productos con "MANTEQUILLA" en el nombre:

```
Codigo               PLU        Nombre
20001720                        Mantequilla Eugenia 90 gr
34                   34         MANTEQUILLA CAMACHOS 1KG
76                   76         MANTEQUILLA EUGENIA GRANEL
172                  172        MANTEQUILLA EUGENIA 90GR
...
```

Luego creas el mapeo:

```powershell
python agregar_mapeo.py mapear 2080332 7501111021029 "MANTEQUILLA EUGENIA 1KG"
```

### Opción 2: Directamente en Python

```python
import sqlite3

conn = sqlite3.connect('pos_cremeria.db')
cursor = conn.cursor()

# Insertar mapeo
cursor.execute("""
    INSERT INTO bascula_mapeo (codigo_bascula, producto_codigo, nombre)
    VALUES (?, ?, ?)
""", ('2080332', '7501111021029', 'MANTEQUILLA EUGENIA 1KG'))

conn.commit()
conn.close()
```

## Pruebas

Para verificar que todo funciona, ejecuta:

```powershell
python test_ticket_decodificacion.py
```

Salida esperada:

```
======================================================================
PRUEBA DE DECODIFICACION DE TICKETS DE BASCULA
======================================================================

Código: 2080332010005
  - Código báscula: 2080332
  - Cantidad: 01 (1 unidades)
  - Control: 0005
  - Encontrado: MANTEQUILLA EUGENIA 1KG
  - Status: OK

Código: 2000072010000
  - Código báscula: 2000072
  - Cantidad: 01 (1 unidades)
  - Control: 0000
  - Encontrado: JOCOQUE
  - Status: OK

Código: 2000140010000
  - Código báscula: 2000140
  - Cantidad: 01 (1 unidades)
  - Control: 0000
  - Encontrado: Huevo Blanco
  - Status: OK

======================================================================
RESULTADO: TODAS LAS PRUEBAS PASADAS
======================================================================
```

## Archivos Modificados

### 1. `ventas.py`
- Función `obtener_producto_por_codigo()` actualizada
- Agrega soporte para códigos de 13 dígitos
- Consulta tabla `bascula_mapeo`

### 2. Base de Datos (`pos_cremeria.db`)
- Tabla `bascula_mapeo` creada
- 3 mapeos iniciales agregados

### 3. Nuevos Scripts
- `agregar_mapeo.py` - Utilidad para agregar mapeos
- `test_ticket_decodificacion.py` - Pruebas de decodificación

## Formato SQL para Consultas Manuales

### Ver mapeos existentes
```sql
SELECT codigo_bascula, producto_codigo, nombre 
FROM bascula_mapeo 
ORDER BY codigo_bascula;
```

### Agregar nuevo mapeo
```sql
INSERT INTO bascula_mapeo (codigo_bascula, producto_codigo, nombre)
VALUES ('2000000', '99', 'NUEVO PRODUCTO');
```

### Eliminar mapeo
```sql
DELETE FROM bascula_mapeo WHERE codigo_bascula = '2000000';
```

### Actualizar mapeo
```sql
UPDATE bascula_mapeo 
SET producto_codigo = '100'
WHERE codigo_bascula = '2000000';
```

## Próximos Pasos

1. **Prueba en PRODUCCIÓN**: Escanea un ticket completo en ventas.py
2. **Agrega más mapeos**: Conforme uses más productos
3. **Verifica resultados**: Asegúrate que se agregan al carrito correctamente

## Soporte

Si un producto no se encuentra:
1. Ejecuta: `python agregar_mapeo.py buscar NOMBRE_PRODUCTO`
2. Identifica el código correcto
3. Crea el mapeo: `python agregar_mapeo.py mapear COD_BAS COD_PROD NOMBRE`
