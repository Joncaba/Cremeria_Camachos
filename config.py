"""
Módulo de configuración para manejar secretos y variables de entorno
"""
import streamlit as st
import os

def get_db_path():
    """Obtener la ruta de la base de datos desde secrets o usar default"""
    try:
        # Intentar obtener desde secrets.toml
        return st.secrets["database"]["path"]
    except (KeyError, FileNotFoundError):
        # Fallback a valor por defecto
        return os.getenv("DB_PATH", "pos_cremeria.db")

def get_encryption_key():
    """Obtener clave de encriptación"""
    try:
        return st.secrets["security"]["encryption_key"]
    except (KeyError, FileNotFoundError):
        return os.getenv("ENCRYPTION_KEY", "default-key-change-me")

def get_password_salt():
    """Obtener salt para passwords"""
    try:
        return st.secrets["security"]["password_salt"]
    except (KeyError, FileNotFoundError):
        return os.getenv("PASSWORD_SALT", "default-salt")

def get_session_timeout():
    """Obtener timeout de sesión en segundos"""
    try:
        return st.secrets["app"]["session_timeout"]
    except (KeyError, FileNotFoundError):
        return int(os.getenv("SESSION_TIMEOUT", "3600"))

def get_max_login_attempts():
    """Obtener número máximo de intentos de login"""
    try:
        return st.secrets["app"]["max_login_attempts"]
    except (KeyError, FileNotFoundError):
        return int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))

def get_admin_credentials():
    """Obtener credenciales de administrador por defecto (solo para inicialización)"""
    try:
        return {
            "username": st.secrets["admin"]["default_username"],
            "password": st.secrets["admin"]["default_password"]
        }
    except (KeyError, FileNotFoundError):
        return {
            "username": os.getenv("ADMIN_USERNAME", "admin"),
            "password": os.getenv("ADMIN_PASSWORD", "admin123")
        }

# Verificar si estamos en modo desarrollo o producción
def is_production():
    """Verificar si la app está en producción"""
    return os.getenv("STREAMLIT_ENV", "development") == "production"

def check_secrets_available():
    """Verificar si los secretos están configurados correctamente"""
    try:
        st.secrets["database"]["path"]
        return True
    except (KeyError, FileNotFoundError):
        return False
