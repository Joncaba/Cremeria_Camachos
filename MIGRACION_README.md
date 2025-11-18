"""
📝 GUÍA DE MIGRACIÓN A SUPABASE
================================

Tu aplicación ahora puede funcionar con SQLite O Supabase!

## ✅ Lo que ya tienes configurado:

1. ✅ Supabase configurado en `.streamlit/secrets.toml`
2. ✅ Cliente de Supabase (`supabase_client.py`)
3. ✅ Adaptador universal (`db_adapter.py`)
4. ✅ Datos migrados a Supabase

## 🔄 Cómo funciona la migración:

El archivo `db_adapter.py` actúa como un "traductor" entre SQLite y Supabase.
Tus módulos pueden usar el mismo código y funcionará con ambas bases de datos!

## 🚀 Para usar SUPABASE (recomendado):

Por defecto, la aplicación usa Supabase automáticamente.

Si quieres forzar el uso de Supabase:
```python
# En cualquier archivo .py
import os
os.environ['USE_SUPABASE'] = 'true'
```

## 📁 Para usar SQLITE (local):

Si quieres volver a SQLite temporalmente:
```python
import os
os.environ['USE_SUPABASE'] = 'false'
```

## 📋 Archivos actualizados:

Los siguientes módulos YA están listos para usar Supabase:
- ✅ `streamlit_app.py` - App principal
- ✅ `main.py` - App principal alternativa  
- ⏳ `productos.py` - Gestión de productos (por actualizar)
- ⏳ `ventas.py` - Sistema de ventas (por actualizar)
- ⏳ `inventario.py` - Control de inventario (por actualizar)
- ⏳ `finanzas.py` - Reportes financieros (por actualizar)
- ⏳ `turnos.py` - Gestión de turnos (por actualizar)
- ⏳ `pedidos.py` - Reabastecimiento (por actualizar)
- ⏳ `usuarios.py` - Usuarios admin (por actualizar)

## 🔧 Cómo actualizar un módulo:

### Antes (SQLite):
```python
import sqlite3

conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM productos")
productos = cursor.fetchall()
```

### Después (Supabase compatible):
```python
from db_adapter import get_db_adapter

db = get_db_adapter()
productos = db.obtener_productos()
```

## 📊 Ventajas de usar Supabase:

✅ **Acceso desde cualquier lugar** - No necesitas archivo .db
✅ **Backups automáticos** - Supabase guarda copias
✅ **Mejor rendimiento** - PostgreSQL es más rápido
✅ **Escalable** - Soporta más usuarios simultáneos
✅ **Despliegue fácil** - Funciona en Streamlit Cloud
✅ **Sincronización** - Múltiples dispositivos en tiempo real

## ⚡ Migración progresiva:

No necesitas migrar todo de una vez! El adaptador permite que:
- SQLite siga funcionando en desarrollo
- Supabase funcione en producción
- Puedas probar ambos sin romper nada

## 🧪 Probar la conexión:

```bash
python test_supabase.py
```

Deberías ver:
```
✅ 12 productos encontrados
✅ 2 usuarios encontrados
✅ 14 ventas obtenidas
✅ Total de ventas: $3,079.78
```

## 📝 Siguiente paso:

Ejecuta tu aplicación normalmente:
```bash
streamlit run streamlit_app.py
```

La app detectará automáticamente Supabase y lo usará!

## 🆘 Solución de problemas:

### "No se pueden leer los datos"
1. Verifica `python test_supabase.py` funcione
2. Confirma que RLS está desactivado en Supabase
3. Revisa que secrets.toml tenga las credenciales correctas

### "Quiero volver a SQLite"
```python
# En tu código antes de importar módulos:
import os
os.environ['USE_SUPABASE'] = 'false'
```

### "Error al insertar datos"
- Supabase usa tipos más estrictos (DECIMAL vs REAL)
- Los decimales deben ser números, no strings
- Las fechas deben estar en formato ISO: 'YYYY-MM-DD HH:MM:SS'

## 📚 Recursos:

- [Documentación Supabase](https://supabase.com/docs)
- [Python Client](https://supabase.com/docs/reference/python/introduction)
- Archivo: `MIGRACION_SUPABASE.md` - Guía completa
- Archivo: `supabase_client.py` - API de Supabase
- Archivo: `db_adapter.py` - Adaptador universal

## ✨ Estado actual:

🟢 **LISTO PARA USAR SUPABASE**

Tu app está configurada y puede funcionar con ambas bases de datos.
Supabase se usa por defecto. SQLite está disponible como respaldo.

---
Última actualización: 2025-11-17
