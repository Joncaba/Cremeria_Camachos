# 🔐 Configuración de Secretos y Seguridad

## Configuración Local

### 1. Configurar secrets.toml

El archivo `.streamlit/secrets.toml` contiene información sensible y **NO debe subirse a Git**.

**Edita `.streamlit/secrets.toml`** y personaliza:

```toml
[database]
path = "pos_cremeria.db"

[security]
encryption_key = "TU-CLAVE-SUPER-SECRETA-AQUI"
password_salt = "TU-SALT-ALEATORIO-UNICO"

[admin]
default_username = "admin"
default_password = "CAMBIAR-INMEDIATAMENTE"

[app]
session_timeout = 3600
max_login_attempts = 3
```

### 2. Generar claves seguras

Puedes generar claves aleatorias seguras con Python:

```python
import secrets
import hashlib

# Generar encryption_key
print("encryption_key:", secrets.token_urlsafe(32))

# Generar password_salt
print("password_salt:", secrets.token_hex(16))
```

## Despliegue en Streamlit Cloud

### 1. Subir código a GitHub

```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/tu-repo.git
git push -u origin main
```

### 2. Configurar Secrets en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu repositorio
3. En la configuración de tu app, ve a **"Secrets"**
4. Copia el contenido de tu `.streamlit/secrets.toml` local
5. Pega y guarda

**Importante:** Los secretos en Streamlit Cloud están encriptados y seguros.

## Archivos Protegidos

Estos archivos **NO se suben a Git** (ya están en `.gitignore`):

- `.streamlit/secrets.toml` - Secretos y configuración sensible
- `*.db` - Archivos de base de datos
- `.env` - Variables de entorno alternativas

## Variables de Entorno (Alternativa)

Si prefieres usar variables de entorno en lugar de secrets.toml:

```bash
# Windows PowerShell
$env:DB_PATH = "pos_cremeria.db"
$env:ENCRYPTION_KEY = "tu-clave-aqui"
$env:PASSWORD_SALT = "tu-salt-aqui"
$env:STREAMLIT_ENV = "production"
```

## Seguridad Adicional

### Cambiar contraseñas por defecto

1. Inicia sesión con el usuario admin
2. Ve a **Gestión de Usuarios**
3. Cambia la contraseña inmediatamente

### Migración de datos existentes

Si ya tienes una base de datos con contraseñas hasheadas con el método anterior:

```python
# Ejecutar una sola vez para migrar
import sqlite3
import hashlib
from config import get_password_salt

def migrate_passwords():
    # Este script es para referencia - ajusta según necesites
    # Las contraseñas existentes necesitarán rehashing con el nuevo salt
    pass
```

## Verificar Configuración

Ejecuta para verificar que todo está configurado:

```python
import config

print("DB Path:", config.get_db_path())
print("Secrets disponibles:", config.check_secrets_available())
print("Modo producción:", config.is_production())
```

## Backup de Base de Datos

**Importante:** Haz backups regulares de tu base de datos:

```bash
# Backup manual
cp pos_cremeria.db pos_cremeria_backup_$(date +%Y%m%d).db
```

Para backups automáticos, considera usar servicios en la nube con encriptación.

## Troubleshooting

### Error: "Configuración de secretos no encontrada"

- Verifica que `.streamlit/secrets.toml` existe
- Verifica que el formato TOML es correcto
- En Streamlit Cloud, verifica que los secretos están configurados en la app

### Error de conexión a base de datos

- Verifica que la ruta en `secrets.toml` es correcta
- Asegúrate que el archivo de base de datos existe
- Verifica permisos de lectura/escritura

## Soporte

Para más información sobre secrets en Streamlit:
- [Documentación oficial](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
