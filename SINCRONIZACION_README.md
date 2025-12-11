# 🔄 Sistema de Sincronización SQLite ↔️ Supabase

## 📋 Descripción

Tu aplicación ahora funciona con un **sistema híbrido** que te permite:

- ✅ **Trabajar offline** con SQLite local
- ✅ **Sincronización automática** a Supabase cuando hay internet
- ✅ **Sincronización manual** bidireccional (local → nube y nube → local)
- ✅ **Detección automática** de conexión a internet

## 🎯 Casos de Uso

### 1. Trabajo Normal (Con Internet)
Cuando guardes o edites un producto:
1. Se guarda primero en SQLite local
2. **Automáticamente** se sincroniza a Supabase
3. Mensaje: "✅ Producto sincronizado a Supabase exitosamente"

### 2. Trabajo Offline (Sin Internet)
Cuando NO haya internet:
1. Los productos se guardan solo en SQLite local
2. Mensaje: "📴 Sin conexión - Producto guardado solo localmente"
3. Cuando vuelva el internet, puedes sincronizar manualmente

### 3. Actualizar Precios desde Supabase
Si cambias precios en el dashboard de Supabase:
1. Ve a **Gestión de Productos**
2. Abre el panel **"🔄 Sincronización SQLite ↔️ Supabase"**
3. Click en **"⬇️ Sincronizar Todo Supabase → Local"**
4. Los precios se actualizan en tu base de datos local

### 4. Sincronización Manual Completa
Si trabajaste offline y quieres subir todo:
1. Conecta a internet
2. Abre el panel de sincronización
3. Click en **"⬆️ Sincronizar Todo Local → Supabase"**
4. Todos los cambios se suben a la nube

## 🔧 Funcionamiento Técnico

### Detección de Conexión
El sistema verifica automáticamente:
1. Conexión a internet (usando Google DNS 8.8.8.8)
2. Disponibilidad de Supabase
3. Respuesta del servidor

### Sincronización Automática
Después de cada operación de guardado:
```python
# El sistema automáticamente ejecuta:
1. Guardar en SQLite (siempre)
2. Si hay internet → Sincronizar a Supabase
3. Mostrar estado de sincronización
```

### Sincronización Manual
Disponible en el panel de sincronización:
- **Local → Supabase**: Sube todos los productos locales a la nube
- **Supabase → Local**: Descarga todos los productos de la nube

## 📊 Indicadores de Estado

### En Gestión de Productos
Verás indicadores de conexión:

**Con Internet:**
```
✅ Conectado a Supabase - Sincronización automática activa
```

**Sin Internet:**
```
📴 Sin conexión a Supabase - Trabajando en modo offline (SQLite local)
```

### Después de Guardar un Producto

**Con sincronización exitosa:**
```
✅ Producto guardado en SQLite
🌐 Sincronizando a Supabase...
✅ Producto sincronizado a Supabase exitosamente
```

**Sin conexión:**
```
✅ Producto guardado en SQLite
📴 Sin conexión - Producto guardado solo localmente
```

## 🚀 Ventajas del Sistema Híbrido

### 1. **Disponibilidad Total**
- Funciona 100% offline con SQLite
- Funciona 100% online con Supabase
- No se pierde ningún dato

### 2. **Flexibilidad**
- Cambias precios en Supabase → Sincronizas a local
- Trabajas offline → Sincronizas cuando vuelva internet
- Control total sobre cuándo y qué sincronizar

### 3. **Seguridad**
- Datos siempre guardados localmente
- Respaldo automático en la nube
- Dos copias de toda la información

### 4. **Rendimiento**
- Operaciones rápidas en SQLite local
- No depende de la velocidad de internet
- Sincronización en segundo plano

## ⚠️ Consideraciones Importantes

### 1. Conflictos de Datos
Si modificas el mismo producto en ambos lados:
- **Última sincronización gana**: El dato más reciente sobrescribe al anterior
- Recomendación: Usa una sola fuente de verdad (preferiblemente local)

### 2. Flujo Recomendado

**Para uso normal:**
1. Trabaja normalmente en la aplicación
2. El sistema sincroniza automáticamente
3. No necesitas hacer nada manual

**Para cambios en Supabase:**
1. Haces cambios en el dashboard de Supabase
2. Abres la app
3. Click en "⬇️ Sincronizar Todo Supabase → Local"
4. Listo

**Para recuperación después de offline:**
1. Vuelve la conexión a internet
2. Click en "⬆️ Sincronizar Todo Local → Supabase"
3. Todos los cambios offline se suben

### 3. Base de Datos Principal
- **SQLite es la base primaria**: Todas las operaciones se hacen primero aquí
- **Supabase es el respaldo en la nube**: Se sincroniza después
- Esto garantiza que nunca pierdas datos por falta de internet

## 🔍 Verificación de Sincronización

Para verificar que todo está sincronizado:

1. Abre **Gestión de Productos**
2. Expande el panel **"🔄 Sincronización SQLite ↔️ Supabase"**
3. Click en **"🔄 Verificar Conexión"**
4. El sistema te dirá si está conectado

## 📝 Archivos Relacionados

- `sync_manager.py`: Gestor de sincronización
- `productos.py`: Módulo actualizado con sincronización automática
- `supabase_client.py`: Cliente de Supabase
- `pos_cremeria.db`: Base de datos SQLite local

## 🆘 Solución de Problemas

### "❌ Sin conexión"
**Causa**: No hay internet o Supabase no responde  
**Solución**: 
- Verifica tu conexión a internet
- El sistema funciona normalmente en modo offline
- Sincroniza manualmente cuando vuelva la conexión

### "⚠️ No se pudo sincronizar a Supabase"
**Causa**: Error temporal de Supabase  
**Solución**:
- Los datos están guardados en SQLite
- Intenta sincronizar manualmente más tarde
- Usa el botón "⬆️ Sincronizar Todo"

### "Precios no actualizados después de sincronizar"
**Causa**: Caché del navegador  
**Solución**:
- Click en "🔄 Refrescar Lista" en la lista de productos
- O presiona F5 en el navegador

## ✨ Características Futuras

Posibles mejoras:
- [ ] Log de sincronizaciones realizadas
- [ ] Indicador de productos pendientes de sincronizar
- [ ] Sincronización por lotes programada
- [ ] Resolución de conflictos inteligente

---

**Última actualización:** 2025-11-17  
**Versión:** 1.0
