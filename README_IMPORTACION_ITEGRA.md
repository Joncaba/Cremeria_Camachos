# Importación de Catálogo iTegra a Inventario

## 📋 Resumen

Este sistema te permite importar tu catálogo completo de PLUs desde archivos iTegra a tu sistema de punto de venta, manteniendo la estructura de tu base de datos intacta.

## 🗂️ Estructura de Tablas

### Tabla `productos` (Principal - Actualizada)
- Código: `codigo` (número del PLU o código de barras real)
- Número Producto: `numero_producto` (PLU del producto iTegra)
- Nombre, precios, stock, etc.

### Tabla `plu_catalogo` (Auxiliar)
- PLU número
- Nombre
- Precio base

### Tabla `codigos_barras` (Auxiliar)
- Código de barras escaneables
- PLU vinculado
- Nombre y precio

## 🚀 Uso

### 1. Importar Catálogo iTegra

```powershell
python -X utf8 importar_itegra_plu.py "ruta\al\archivo.iTegra"
```

**Resultado:**
- ✅ Importa todos los PLUs con nombres y precios
- ✅ Detecta códigos de barras si existen en el archivo
- ✅ Crea catálogo en tablas auxiliares

**Ejemplo:**
```powershell
python -X utf8 importar_itegra_plu.py "c:\Users\jo_na\Documents\2025_12_11.iTegra"
# Salida: Importación completada: codigos 0 nuevos, 0 actualizados | PLUs 543 nuevos, 10 actualizados
```

### 2. Sincronizar a Inventario Visible

```powershell
python -X utf8 sincronizar_plu_a_productos.py
```

**Resultado:**
- ✅ Agrega productos nuevos a tu inventario con código numérico (ej: `1`, `2`, `3`...)
- ✅ Crea columna `numero_producto` con el PLU del producto
- ✅ **NO modifica** productos existentes
- ✅ Los productos aparecen inmediatamente en `inventario.py`

**Ejemplo:**
```powershell
python -X utf8 sincronizar_plu_a_productos.py
# Salida: 
# Agregando columna numero_producto...
# Productos insertados: 543
```

### 3. Agregar Códigos de Barras Manualmente (Opcional)

Cuando tengas un código de barras real para un producto:

```powershell
python agregar_codigo_barras.py 1 7501234567890
```

**Parámetros:**
- Primer argumento: **Número del producto** (PLU, ej: `1`, `2`, `3`)
- Segundo argumento: **Código de barras** a vincular

**Resultado:**
- ✅ Reemplaza el código numérico con el código de barras real `7501234567890`
- ✅ El producto ahora es escaneable en ventas
- ✅ Mantiene el `numero_producto` para referencia

**Ejemplo:**
```powershell
python agregar_codigo_barras.py 1 7501234567890
# Salida:
# ✅ Código de barras '7501234567890' vinculado a producto 'JAM COR PIERNA'
#    Número producto: 1 | Código anterior: 1 → Nuevo código: 7501234567890
```

## 📊 Formato iTegra Soportado

```
"PLUs"<id>|seccion|?|NOMBRE||PLU|tipo|?|PRECIO|...
           [0]     [1]  [2] [3]  [4][5] [6] [7] [8]
```

- **[3]**: Nombre del producto
- **[4]**: Código de barras (opcional, puede estar vacío)
- **[5]**: Número PLU
- **[8]**: Precio de venta

## 🔄 Flujo de Trabajo Recomendado

1. **Importación Inicial:**
   ```powershell
   python -X utf8 importar_itegra_plu.py "archivo.iTegra"
   python -X utf8 sincronizar_plu_a_productos.py
   ```

2. **Ver en Inventario:**
   - Abre tu aplicación Streamlit
   - Ve a módulo "Inventario"
   - Verás todos los productos con código numérico (1, 2, 3...)
   - La columna `numero_producto` muestra el PLU

3. **Agregar Códigos de Barras Gradualmente:**
   - Cuando escanees un producto en la báscula o lector
   - Ejecuta: `python agregar_codigo_barras.py <numero_plu> <codigo_escaneado>`
   - Ejemplo: `python agregar_codigo_barras.py 1 7501234567890`
   - El producto queda listo para ventas con escaneo

4. **Reimportar Actualizaciones:**
   - Si cambias precios en iTegra
   - Vuelve a ejecutar paso 1
   - Los productos existentes se actualizan, los nuevos se agregan

## ✅ Ventajas

- ✅ **No invasivo**: Tu base de datos actual no se modifica
- ✅ **Reversible**: Puedes eliminar productos importados si es necesario
- ✅ **Incremental**: Agrega códigos de barras conforme los obtengas
- ✅ **Compatible**: Funciona con tu sistema actual de ventas e inventario
- ✅ **Flexible**: Soporta productos con y sin códigos de barras

## 🔧 Mantenimiento

### Limpiar Importación (Si necesitas empezar de nuevo)

```powershell
# Opción 1: Usar script de limpieza
python limpiar_plu_antiguos.py

# Opción 2: SQL manual
# Conectar a pos_cremeria.db y ejecutar:
# DELETE FROM productos WHERE numero_producto IS NOT NULL AND numero_producto > 0;
# DELETE FROM plu_catalogo;
# DELETE FROM codigos_barras;
```

### Ver Estadísticas

```sql
-- Total de PLUs importados:
SELECT COUNT(*) FROM plu_catalogo;

-- Total de códigos de barras vinculados:
SELECT COUNT(*) FROM codigos_barras;

-- Productos en inventario:
SELECT COUNT(*) FROM productos;

-- Productos con solo número (sin código de barras):
SELECT COUNT(*) FROM productos WHERE numero_producto IS NOT NULL AND LENGTH(codigo) < 5;
```

## 📝 Notas Importantes

1. **Códigos numéricos**: Los productos sin código de barras usan su número PLU como código (1, 2, 3...)
2. **Número de producto**: Campo `numero_producto` almacena el PLU original del iTegra
3. **Precios**: El precio importado va a `precio_normal` (precio de venta)
4. **Stock**: Los productos nuevos inician con stock 0
5. **Tipo de venta**: Por defecto es "unidad" (ajusta manualmente si es granel)
6. **Stock máximo**: Por defecto es 30 unidades (ajusta según necesites)

## 🎯 Próximos Pasos

1. ✅ Importar catálogo completo
2. ✅ Verificar productos en inventario
3. 🔄 Ajustar precios de compra manualmente en inventario
4. 🔄 Configurar stock mínimo/máximo por producto
5. 🔄 Agregar códigos de barras conforme los obtengas
6. 🔄 Configurar productos a granel si los hay

---

**Creado:** Diciembre 2025  
**Versión:** 1.0
