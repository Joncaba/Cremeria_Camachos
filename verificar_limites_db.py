"""
Script para verificar límites y estado de la base de datos SQLite
"""
import sqlite3
import os

def get_db_path():
    """Obtener ruta de la base de datos"""
    # Primero intentar leer desde secrets.toml
    secrets_path = os.path.join('.streamlit', 'secrets.toml')
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'path' in line and '=' in line:
                        return line.split('=')[1].strip().strip('"')
        except:
            pass
    return "pos_cremeria.db"

def bytes_to_mb(bytes_val):
    """Convertir bytes a megabytes"""
    return round(bytes_val / (1024 * 1024), 2)

def verificar_limites_sqlite():
    """Verificar límites y estado de SQLite"""
    
    db_path = get_db_path()
    
    print("=" * 60)
    print("📊 VERIFICACIÓN DE LÍMITES Y ESTADO DE BASE DE DATOS SQLite")
    print("=" * 60)
    
    # Verificar si existe el archivo
    if not os.path.exists(db_path):
        print(f"\n⚠️  Base de datos no encontrada: {db_path}")
        print("La base de datos se creará cuando ejecutes la aplicación.")
        return
    
    # Tamaño del archivo
    file_size = os.path.getsize(db_path)
    print(f"\n📁 Archivo de Base de Datos:")
    print(f"   Ruta: {db_path}")
    print(f"   Tamaño: {bytes_to_mb(file_size)} MB ({file_size:,} bytes)")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Límites de SQLite (valores por defecto)
        print(f"\n🔢 LÍMITES DE SQLite (valores típicos):")
        print(f"   Tamaño máximo de base de datos: 281 TB (281,474,976,710,656 bytes)")
        print(f"   Tamaño máximo de una tabla: 281 TB")
        print(f"   Máximo de columnas por tabla: 2,000")
        print(f"   Máximo de filas por tabla: 2^64 (18,446,744,073,709,551,616)")
        print(f"   Tamaño máximo de una fila: 1 GB")
        print(f"   Tamaño máximo de un string/BLOB: 1 GB")
        print(f"   Máximo de tablas en una base de datos: 2,147,483,646")
        print(f"   Longitud máxima de nombre SQL: 1000 bytes")
        
        # Límites configurables (PRAGMA)
        print(f"\n⚙️  LÍMITES CONFIGURABLES ACTUALES:")
        
        cursor.execute("PRAGMA max_page_count")
        max_pages = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        max_db_size = max_pages * page_size
        
        print(f"   Tamaño máximo configurado: {bytes_to_mb(max_db_size)} MB")
        print(f"   Tamaño de página: {page_size} bytes")
        print(f"   Número máximo de páginas: {max_pages:,}")
        
        cursor.execute("PRAGMA cache_size")
        cache_size = cursor.fetchone()[0]
        print(f"   Tamaño de caché: {cache_size} páginas")
        
        # Información de las tablas
        print(f"\n📋 TABLAS EN LA BASE DE DATOS:")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tablas = cursor.fetchall()
        print(f"   Total de tablas: {len(tablas)}")
        
        # Estadísticas por tabla
        print(f"\n📊 ESTADÍSTICAS POR TABLA:")
        print(f"   {'Tabla':<30} {'Filas':<15} {'Columnas':<10}")
        print(f"   {'-'*30} {'-'*15} {'-'*10}")
        
        for (tabla,) in tablas:
            if tabla.startswith('sqlite_'):
                continue
                
            # Contar filas
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            num_filas = cursor.fetchone()[0]
            
            # Contar columnas
            cursor.execute(f"PRAGMA table_info({tabla})")
            num_columnas = len(cursor.fetchall())
            
            print(f"   {tabla:<30} {num_filas:<15,} {num_columnas:<10}")
        
        # Índices
        print(f"\n🔍 ÍNDICES:")
        cursor.execute("""
            SELECT name, tbl_name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name
        """)
        indices = cursor.fetchall()
        print(f"   Total de índices: {len(indices)}")
        for nombre, tabla in indices:
            print(f"   - {nombre} (en tabla: {tabla})")
        
        # Integridad de la base de datos
        print(f"\n✅ VERIFICACIÓN DE INTEGRIDAD:")
        cursor.execute("PRAGMA integrity_check")
        resultado = cursor.fetchone()[0]
        if resultado == "ok":
            print(f"   Estado: ✅ Base de datos OK")
        else:
            print(f"   Estado: ⚠️ {resultado}")
        
        # Espacio libre
        cursor.execute("PRAGMA freelist_count")
        free_pages = cursor.fetchone()[0]
        free_space = free_pages * page_size
        print(f"\n💾 ESPACIO:")
        print(f"   Páginas libres: {free_pages:,}")
        print(f"   Espacio libre: {bytes_to_mb(free_space)} MB")
        print(f"   Espacio usado: {bytes_to_mb(file_size - free_space)} MB")
        print(f"   Utilización: {((file_size - free_space) / file_size * 100):.1f}%")
        
        # Límite práctico basado en tamaño actual
        porcentaje_usado = (file_size / max_db_size) * 100
        print(f"\n📈 CAPACIDAD:")
        print(f"   Uso actual: {porcentaje_usado:.4f}% del límite configurado")
        espacio_disponible = max_db_size - file_size
        print(f"   Espacio disponible: {bytes_to_mb(espacio_disponible)} MB")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if file_size > 1024 * 1024 * 100:  # > 100 MB
            print(f"   ⚠️  Base de datos grande. Considera:")
            print(f"      - Archivar datos antiguos")
            print(f"      - Implementar paginación en consultas")
            print(f"      - Hacer backups regulares")
        elif free_space > file_size * 0.3:  # > 30% de espacio libre
            print(f"   💡 Mucho espacio fragmentado. Ejecuta:")
            print(f"      VACUUM para optimizar")
        else:
            print(f"   ✅ Base de datos en buen estado")
        
        if len(indices) < len(tablas):
            print(f"   💡 Considera agregar índices para mejorar rendimiento")
        
        # Modo journal
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        print(f"\n📝 CONFIGURACIÓN ADICIONAL:")
        print(f"   Modo de journal: {journal_mode}")
        
        cursor.execute("PRAGMA synchronous")
        synchronous = cursor.fetchone()[0]
        print(f"   Nivel de sincronización: {synchronous}")
        
        print(f"\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error al verificar base de datos: {e}")
    finally:
        conn.close()

def optimizar_base_datos():
    """Optimizar la base de datos (VACUUM)"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    print("\n🔧 Optimizando base de datos...")
    print("   (Esto puede tomar unos momentos)")
    
    conn = sqlite3.connect(db_path)
    try:
        # Backup antes de optimizar
        backup_path = db_path.replace('.db', '_before_vacuum.db')
        print(f"   Creando backup: {backup_path}")
        
        import shutil
        shutil.copy2(db_path, backup_path)
        
        # Ejecutar VACUUM
        conn.execute("VACUUM")
        print("   ✅ Optimización completada")
        
        # Mostrar diferencia de tamaño
        old_size = os.path.getsize(backup_path)
        new_size = os.path.getsize(db_path)
        saved = old_size - new_size
        
        print(f"   Tamaño anterior: {bytes_to_mb(old_size)} MB")
        print(f"   Tamaño nuevo: {bytes_to_mb(new_size)} MB")
        print(f"   Espacio recuperado: {bytes_to_mb(saved)} MB")
        
    except Exception as e:
        print(f"   ❌ Error durante optimización: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    verificar_limites_sqlite()
    
    # Preguntar si desea optimizar
    if len(sys.argv) > 1 and sys.argv[1] == "--optimize":
        respuesta = input("\n¿Deseas optimizar la base de datos? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            optimizar_base_datos()
