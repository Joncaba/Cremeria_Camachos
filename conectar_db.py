"""
Script para conectarse e interactuar con la base de datos SQLite
Ejecuta: python conectar_db.py
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "pos_cremeria.db"

def conectar():
    """Establecer conexión a la base de datos"""
    if not os.path.exists(DB_PATH):
        print(f"⚠️  Base de datos no encontrada: {DB_PATH}")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
    return conn

def mostrar_menu():
    """Mostrar menú de opciones"""
    print("\n" + "="*60)
    print("🗄️  CONSOLA DE BASE DE DATOS - CREMERÍA")
    print("="*60)
    print("1. Ver todas las tablas")
    print("2. Ver productos")
    print("3. Ver ventas")
    print("4. Ver usuarios")
    print("5. Ver turnos")
    print("6. Ver estadísticas generales")
    print("7. Ejecutar consulta SQL personalizada")
    print("8. Ver estructura de una tabla")
    print("9. Exportar datos a CSV")
    print("0. Salir")
    print("="*60)

def ver_tablas(conn):
    """Mostrar todas las tablas"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, sql FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    
    print("\n📋 TABLAS EN LA BASE DE DATOS:")
    print("-" * 60)
    for row in cursor.fetchall():
        tabla = row[0]
        cursor.execute(f"SELECT COUNT(*) as total FROM {tabla}")
        count = cursor.fetchone()[0]
        print(f"  • {tabla:<30} ({count:,} registros)")

def ver_productos(conn):
    """Ver todos los productos"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, categoria, precio_venta, stock_actual, unidad_medida 
        FROM productos 
        ORDER BY categoria, nombre
    """)
    
    print("\n📦 PRODUCTOS:")
    print(f"{'ID':<5} {'Nombre':<25} {'Categoría':<15} {'Precio':<10} {'Stock':<10} {'Unidad':<10}")
    print("-" * 85)
    
    for row in cursor.fetchall():
        print(f"{row['id']:<5} {row['nombre']:<25} {row['categoria']:<15} "
              f"${row['precio_venta']:<9.2f} {row['stock_actual']:<10.2f} {row['unidad_medida']:<10}")

def ver_ventas(conn, limite=20):
    """Ver últimas ventas"""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT id, fecha, hora, total, metodo_pago, usuario 
        FROM ventas 
        ORDER BY fecha DESC, hora DESC
        LIMIT {limite}
    """)
    
    print(f"\n💰 ÚLTIMAS {limite} VENTAS:")
    print(f"{'ID':<5} {'Fecha':<12} {'Hora':<10} {'Total':<12} {'Método':<15} {'Usuario':<15}")
    print("-" * 75)
    
    for row in cursor.fetchall():
        print(f"{row['id']:<5} {row['fecha']:<12} {row['hora']:<10} "
              f"${row['total']:<11.2f} {row['metodo_pago']:<15} {row['usuario']:<15}")

def ver_usuarios(conn):
    """Ver usuarios del sistema"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT usuario, nombre_completo, rol, activo, ultimo_acceso 
        FROM usuarios_admin 
        ORDER BY usuario
    """)
    
    print("\n👥 USUARIOS:")
    print(f"{'Usuario':<15} {'Nombre':<25} {'Rol':<10} {'Estado':<10} {'Último Acceso':<20}")
    print("-" * 85)
    
    for row in cursor.fetchall():
        estado = "✅ Activo" if row['activo'] else "❌ Inactivo"
        ultimo = row['ultimo_acceso'] if row['ultimo_acceso'] else "Nunca"
        print(f"{row['usuario']:<15} {row['nombre_completo']:<25} {row['rol']:<10} "
              f"{estado:<10} {ultimo:<20}")

def ver_turnos(conn):
    """Ver turnos disponibles"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM turnos ORDER BY numero_turno")
    
    print("\n🎫 TURNOS:")
    print(f"{'Turno':<10} {'Estado':<15} {'Nombre':<25} {'Tipo':<15}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        print(f"{row['numero_turno']:<10} {row['estado']:<15} "
              f"{row['nombre_cliente'] or 'N/A':<25} {row['tipo_atencion']:<15}")

def ver_estadisticas(conn):
    """Ver estadísticas generales"""
    cursor = conn.cursor()
    
    print("\n📊 ESTADÍSTICAS GENERALES:")
    print("-" * 60)
    
    # Total de ventas
    cursor.execute("SELECT COUNT(*), SUM(total) FROM ventas")
    ventas_count, ventas_total = cursor.fetchone()
    print(f"  💰 Ventas totales: {ventas_count or 0:,} ventas")
    print(f"  💵 Ingresos totales: ${ventas_total or 0:,.2f}")
    
    # Productos
    cursor.execute("SELECT COUNT(*) FROM productos")
    productos_count = cursor.fetchone()[0]
    print(f"  📦 Productos registrados: {productos_count:,}")
    
    # Producto más vendido
    cursor.execute("""
        SELECT productos, SUM(cantidad) as total 
        FROM ventas 
        WHERE productos IS NOT NULL 
        GROUP BY productos 
        ORDER BY total DESC 
        LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"  🏆 Producto más vendido: {result[0]} ({result[1]:.0f} unidades)")
    
    # Venta promedio
    cursor.execute("SELECT AVG(total) FROM ventas WHERE total > 0")
    promedio = cursor.fetchone()[0]
    if promedio:
        print(f"  📈 Venta promedio: ${promedio:.2f}")
    
    # Ventas de hoy
    hoy = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*), SUM(total) FROM ventas WHERE fecha = ?", (hoy,))
    ventas_hoy, total_hoy = cursor.fetchone()
    print(f"  📅 Ventas de hoy: {ventas_hoy or 0} ventas - ${total_hoy or 0:.2f}")

def ejecutar_consulta(conn):
    """Ejecutar consulta SQL personalizada"""
    print("\n💻 CONSULTA SQL PERSONALIZADA")
    print("Ejemplos:")
    print("  SELECT * FROM productos WHERE categoria = 'Lácteos';")
    print("  SELECT fecha, SUM(total) FROM ventas GROUP BY fecha;")
    print("\nEscribe 'cancelar' para volver al menú")
    print("-" * 60)
    
    consulta = input("SQL> ").strip()
    
    if consulta.lower() == 'cancelar':
        return
    
    if not consulta:
        print("⚠️  Consulta vacía")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute(consulta)
        
        if consulta.upper().startswith('SELECT'):
            resultados = cursor.fetchall()
            
            if not resultados:
                print("✅ Consulta ejecutada. Sin resultados.")
                return
            
            # Mostrar resultados
            print(f"\n📊 Resultados ({len(resultados)} filas):")
            print("-" * 80)
            
            # Encabezados
            columnas = [desc[0] for desc in cursor.description]
            print(" | ".join(f"{col:<15}" for col in columnas))
            print("-" * 80)
            
            # Datos (limitar a 50 filas)
            for row in resultados[:50]:
                valores = [str(val) if val is not None else 'NULL' for val in row]
                print(" | ".join(f"{val:<15}" for val in valores))
            
            if len(resultados) > 50:
                print(f"\n... ({len(resultados) - 50} filas más no mostradas)")
        else:
            conn.commit()
            print(f"✅ Consulta ejecutada correctamente. Filas afectadas: {cursor.rowcount}")
            
    except sqlite3.Error as e:
        print(f"❌ Error SQL: {e}")

def ver_estructura_tabla(conn):
    """Ver estructura de una tabla"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tablas = [row[0] for row in cursor.fetchall()]
    
    print("\n📋 Tablas disponibles:")
    for i, tabla in enumerate(tablas, 1):
        print(f"  {i}. {tabla}")
    
    seleccion = input("\nNombre de la tabla: ").strip()
    
    if seleccion not in tablas:
        print(f"⚠️  Tabla '{seleccion}' no encontrada")
        return
    
    cursor.execute(f"PRAGMA table_info({seleccion})")
    columnas = cursor.fetchall()
    
    print(f"\n🔍 ESTRUCTURA DE '{seleccion}':")
    print(f"{'ID':<5} {'Columna':<25} {'Tipo':<15} {'Nulo':<8} {'Default':<15} {'PK':<5}")
    print("-" * 80)
    
    for col in columnas:
        cid, nombre, tipo, notnull, default, pk = col
        notnull_str = "NO" if notnull else "SI"
        default_str = str(default) if default else ""
        pk_str = "SI" if pk else ""
        print(f"{cid:<5} {nombre:<25} {tipo:<15} {notnull_str:<8} {default_str:<15} {pk_str:<5}")

def exportar_a_csv(conn):
    """Exportar tabla a CSV"""
    import csv
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tablas = [row[0] for row in cursor.fetchall()]
    
    print("\n📋 Tablas disponibles:")
    for i, tabla in enumerate(tablas, 1):
        print(f"  {i}. {tabla}")
    
    seleccion = input("\nNombre de la tabla a exportar: ").strip()
    
    if seleccion not in tablas:
        print(f"⚠️  Tabla '{seleccion}' no encontrada")
        return
    
    filename = f"{seleccion}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    cursor.execute(f"SELECT * FROM {seleccion}")
    datos = cursor.fetchall()
    columnas = [desc[0] for desc in cursor.description]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columnas)
        writer.writerows(datos)
    
    print(f"✅ Datos exportados a: {filename}")
    print(f"   {len(datos)} registros exportados")

def main():
    """Función principal"""
    conn = conectar()
    
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    print("✅ Conectado a:", DB_PATH)
    
    try:
        while True:
            mostrar_menu()
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "0":
                print("\n👋 Cerrando conexión...")
                break
            elif opcion == "1":
                ver_tablas(conn)
            elif opcion == "2":
                ver_productos(conn)
            elif opcion == "3":
                limite = input("¿Cuántas ventas mostrar? (default: 20): ").strip()
                limite = int(limite) if limite.isdigit() else 20
                ver_ventas(conn, limite)
            elif opcion == "4":
                ver_usuarios(conn)
            elif opcion == "5":
                ver_turnos(conn)
            elif opcion == "6":
                ver_estadisticas(conn)
            elif opcion == "7":
                ejecutar_consulta(conn)
            elif opcion == "8":
                ver_estructura_tabla(conn)
            elif opcion == "9":
                exportar_a_csv(conn)
            else:
                print("❌ Opción no válida")
            
            input("\nPresiona Enter para continuar...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
    finally:
        conn.close()
        print("✅ Conexión cerrada")

if __name__ == "__main__":
    main()
