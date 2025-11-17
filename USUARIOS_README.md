# 🔐 Módulo de Gestión de Usuarios

## 📋 Descripción
Sistema completo de gestión de usuarios con autenticación, control de acceso basado en roles y administración centralizada.

## 🚀 Características Principales

### 🔑 Autenticación
- ✅ Sistema de login seguro con contraseñas encriptadas (SHA-256)
- ✅ Validación de credenciales en base de datos
- ✅ Control de sesiones con Streamlit
- ✅ Registro de último acceso

### 👥 Gestión de Usuarios
- ✅ Crear nuevos usuarios
- ✅ Modificar contraseñas
- ✅ Activar/Desactivar usuarios
- ✅ Eliminar usuarios (excepto admin principal)
- ✅ Filtros avanzados por estado y rol

### 🔐 Roles de Usuario

#### Administrador (admin)
- Acceso completo a todas las funciones
- Gestión de usuarios
- Control total del sistema

#### Usuario Normal (usuario)
- Acceso a punto de venta
- Gestión de productos
- Inventario
- Pedidos
- Sin acceso a gestión de usuarios

## 📊 Base de Datos

### Tabla: `usuarios_admin`
```sql
CREATE TABLE usuarios_admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT DEFAULT 'usuario',
    activo INTEGER DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP,
    creado_por TEXT DEFAULT 'Sistema'
)
```

## 🔧 Credenciales por Defecto

**Usuario Administrador:**
- Usuario: `admin`
- Contraseña: `admin123`

⚠️ **IMPORTANTE:** Cambiar la contraseña después del primer inicio de sesión por seguridad.

## 📖 Uso

### Inicio de Sesión
1. Abrir la aplicación
2. Ingresar usuario y contraseña
3. Click en "Ingresar"

### Crear Usuario
1. Ir a "Gestión de Usuarios" (solo admin)
2. Pestaña "Crear Usuario"
3. Completar formulario:
   - Nombre de usuario (sin espacios)
   - Nombre completo
   - Contraseña (mínimo 6 caracteres)
   - Seleccionar rol
4. Click en "Crear Usuario"

### Cambiar Contraseña
1. Ir a "Gestión de Usuarios"
2. Pestaña "Gestionar Usuarios"
3. Seleccionar usuario
4. Pestaña "Cambiar Contraseña"
5. Ingresar nueva contraseña
6. Confirmar

### Activar/Desactivar Usuario
1. Seleccionar usuario en "Gestionar Usuarios"
2. Pestaña "Cambiar Estado"
3. Click en "Activar" o "Desactivar"

### Eliminar Usuario
1. Seleccionar usuario (no puede ser 'admin')
2. Pestaña "Eliminar Usuario"
3. Escribir nombre de usuario para confirmar
4. Click en "Eliminar Usuario"

## 🛡️ Seguridad

### Encriptación
- Todas las contraseñas se almacenan con hash SHA-256
- No se almacenan contraseñas en texto plano

### Validaciones
- Contraseñas mínimo 6 caracteres
- Usuarios únicos (no duplicados)
- Usuarios activos para login
- Protección del usuario admin principal

### Control de Acceso
- Verificación de rol antes de mostrar funciones
- Solo administradores pueden gestionar usuarios
- Session state para mantener autenticación

## 📊 Funciones del Módulo

### `usuarios.py`

#### Funciones Principales:
- `hash_password(password)` - Encriptar contraseña
- `crear_tabla_usuarios()` - Crear tabla en BD
- `verificar_es_admin(usuario)` - Verificar rol admin
- `obtener_todos_usuarios()` - Listar usuarios
- `crear_usuario()` - Crear nuevo usuario
- `actualizar_password()` - Cambiar contraseña
- `cambiar_estado_usuario()` - Activar/desactivar
- `eliminar_usuario()` - Eliminar usuario
- `actualizar_ultimo_acceso()` - Registrar acceso

#### Funciones de Interfaz:
- `mostrar()` - Pantalla principal
- `mostrar_lista_usuarios()` - Tabla de usuarios
- `mostrar_crear_usuario()` - Formulario crear
- `mostrar_gestionar_usuarios()` - Panel de gestión

## 🔄 Flujo de Trabajo

```
Login → Verificación → Session State → Menú Principal
                                           ↓
                        ┌──────────────────┼──────────────────┐
                        ↓                  ↓                  ↓
                   Usuarios          Otros Módulos      Cerrar Sesión
                   (Solo Admin)      (Todos los roles)      ↓
                        ↓                                 Logout
                   Gestión                                  ↓
                        ↓                                 Login
              ┌─────────┼─────────┐
              ↓         ↓         ↓
            Crear   Gestionar   Ver Lista
```

## 📈 Mejoras Futuras

- [ ] Recuperación de contraseña
- [ ] Autenticación de dos factores
- [ ] Historial de accesos por usuario
- [ ] Permisos granulares por módulo
- [ ] Expiración de contraseñas
- [ ] Política de contraseñas complejas
- [ ] Límite de intentos de login
- [ ] Registro de auditoría de acciones

## 🐛 Solución de Problemas

### No puedo iniciar sesión
- Verificar usuario y contraseña
- Verificar que el usuario esté activo
- Usar credenciales por defecto (admin/admin123)

### No veo el módulo de usuarios
- Verificar que sea usuario administrador
- El módulo solo es visible para rol "admin"

### Error al crear usuario
- Verificar que el nombre de usuario sea único
- Verificar que la contraseña tenga mínimo 6 caracteres
- No usar espacios en el nombre de usuario

## 📝 Notas

- El usuario `admin` no puede ser eliminado
- Los usuarios inactivos no pueden iniciar sesión
- Todas las operaciones de BD usan try-finally para evitar fugas
- Los cambios se reflejan inmediatamente después de guardar
