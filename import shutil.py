import shutil
import os
from datetime import datetime

def exportar_proyecto():
    """Crear paquete completo del proyecto para exportar"""
    
    # Nombre del paquete
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_paquete = f"pos_cremeria_completo_{fecha}"
    
    # Crear directorio temporal
    os.makedirs(nombre_paquete, exist_ok=True)
    
    # Archivos a incluir
    archivos_incluir = [
        "main.py",
        "productos.py", 
        "inventario.py",
        "ventas.py",
        "finanzas.py",
        "turnos.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md"
    ]
    
    # Copiar archivos
    for archivo in archivos_incluir:
        if os.path.exists(archivo):
            shutil.copy2(archivo, nombre_paquete)
            print(f"✅ Copiado: {archivo}")
        else:
            print(f"⚠️ No encontrado: {archivo}")
    
    # Crear README de instalación
    readme_instalacion = f"""# 🐄 Sistema POS Cremería - Instalación

## 📋 Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación Rápida

### 1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación:

```bash
streamlit run main.py
```

### 3. Abrir en navegador:
La aplicación se abrirá automáticamente en: http://localhost:8501

## 🐳 Instalación con Docker (Alternativa)

```bash
# Construir imagen
docker build -t pos-cremeria .

# Ejecutar contenedor
docker run -p 8501:8501 pos-cremeria
```

## 📁 Estructura del Proyecto

- `main.py` - Archivo principal
- `productos.py` - Gestión de productos
- `ventas.py` - Punto de venta
- `inventario.py` - Control de inventario
- `finanzas.py` - Reportes financieros
- `turnos.py` - Sistema de turnos

## 🔧 Resolución de Problemas

Si tienes errores al ejecutar:

1. Verifica que Python esté instalado: `python --version`
2. Actualiza pip: `pip install --upgrade pip`
3. Instala dependencias una por una si hay conflictos

## 📞 Soporte
Sistema desarrollado para Cremería Camacho's
Fecha de exportación: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""
    
    # Escribir README de instalación
    with open(f"{nombre_paquete}/INSTALACION.md", "w", encoding="utf-8") as f:
        f.write(readme_instalacion)
    
    # Crear archivo requirements.txt completo si no existe
    requirements_completo = """streamlit==1.28.0
pandas==2.0.3
plotly==5.15.0
sqlite3
openpyxl==3.1.2
datetime
time
io
"""
    
    with open(f"{nombre_paquete}/requirements.txt", "w") as f:
        f.write(requirements_completo)
    
    # Crear archivo de configuración inicial
    config_inicial = f"""# Configuración inicial del sistema POS
# Generado automáticamente el {datetime.now().strftime("%d/%m/%Y")}

NOMBRE_EMPRESA = "Cremería Camacho's"
MONEDA = "MXN"
ZONA_HORARIA = "America/Mexico_City"

# Base de datos
DB_NAME = "pos_cremeria.db"

# Configuración de alertas
HORA_RECORDATORIOS = "15:00"  # 3 PM
DIAS_CREDITO_DEFAULT = 1

# Configuración de stock
STOCK_MINIMO_DEFAULT = 10
MARGEN_CRITICO_STOCK = 0.5  # 50% del stock mínimo
"""
    
    with open(f"{nombre_paquete}/config.py", "w", encoding="utf-8") as f:
        f.write(config_inicial)
    
    # Crear script de instalación automática
    script_instalacion = """@echo off
echo ========================================
echo   Sistema POS Cremeria - Instalacion
echo ========================================
echo.

echo Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo Descarga Python desde: https://python.org
    pause
    exit /b 1
)

echo.
echo Instalando dependencias...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Instalacion completada exitosamente!
echo ========================================
echo.
echo Para ejecutar el sistema:
echo   streamlit run main.py
echo.
pause
"""
    
    with open(f"{nombre_paquete}/instalar.bat", "w") as f:
        f.write(script_instalacion)
    
    # Crear script de ejecución
    script_ejecucion = """@echo off
echo Iniciando Sistema POS Cremeria...
streamlit run main.py
pause
"""
    
    with open(f"{nombre_paquete}/ejecutar.bat", "w") as f:
        f.write(script_ejecucion)
    
    # Comprimir todo en ZIP
    shutil.make_archive(nombre_paquete, 'zip', nombre_paquete)
    
    # Limpiar directorio temporal
    shutil.rmtree(nombre_paquete)
    
    print(f"✅ Proyecto exportado exitosamente: {nombre_paquete}.zip")
    print(f"📁 Tamaño del archivo: {os.path.getsize(f'{nombre_paquete}.zip') / 1024:.1f} KB")
    
    return f"{nombre_paquete}.zip"

if __name__ == "__main__":
    archivo_exportado = exportar_proyecto()
    print(f"\n🎉 ¡Exportación completada!")
    print(f"📦 Archivo: {archivo_exportado}")
    print(f"📋 Instrucciones:")
    print(f"   1. Copia el archivo {archivo_exportado} a la otra computadora")
    print(f"   2. Extrae el archivo ZIP")
    print(f"   3. Ejecuta 'instalar.bat' (Windows) o instala dependencias manualmente")
    print(f"   4. Ejecuta 'ejecutar.bat' o 'streamlit run main.py'")