#!/usr/bin/env python3
"""
Script para limpiar la base de datos del sistema POS
Elimina todos los productos, ventas y datos financieros para hacer pruebas frescas
"""

import sqlite3
import os
from datetime import datetime

def limpiar_base_datos():
    """Eliminar todos los datos de productos, ventas y finanzas"""
    
    db_path = "pos_cremeria.db"
    
    # Verificar que la base de datos existe
    if not os.path.exists(db_path):
        print("❌ No se encontró la base de datos pos_cremeria.db")
        return False
    
    print("🗑️  LIMPIEZA DE BASE DE DATOS")
    print("=" * 50)
    
    # Hacer backup antes de limpiar
    backup_name = f"backup_pos_cremeria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        # Crear backup
        import shutil
        shutil.copy2(db_path, backup_name)
        print(f"✅ Backup creado: {backup_name}")
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Mostrar estado actual
        cursor.execute("SELECT COUNT(*) FROM productos")
        productos_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ventas")
        ventas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM creditos_pendientes")
        creditos_count = cursor.fetchone()[0]
        
        # Verificar si existe tabla de pedidos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pedidos_reabastecimiento'")
        pedidos_table_exists = cursor.fetchone() is not None
        
        pedidos_count = 0
        if pedidos_table_exists:
            cursor.execute("SELECT COUNT(*) FROM pedidos_reabastecimiento")
            pedidos_count = cursor.fetchone()[0]
        
        print(f"📊 Estado actual:")
        print(f"   • Productos: {productos_count}")
        print(f"   • Ventas: {ventas_count}")
        print(f"   • Créditos: {creditos_count}")
        print(f"   • Pedidos: {pedidos_count}")
        print()
        
        # Confirmar limpieza
        respuesta = input("¿Estás seguro de que quieres eliminar TODOS los datos? (escribe 'SI' para confirmar): ")
        
        if respuesta.upper() != 'SI':
            print("❌ Operación cancelada")
            conn.close()
            return False
        
        print("\n🗑️  Iniciando limpieza...")
        
        # Limpiar tablas en orden (respetando dependencias)
        
        # 1. Eliminar créditos pendientes
        cursor.execute("DELETE FROM creditos_pendientes")
        print("✅ Créditos eliminados")
        
        # 2. Eliminar pedidos si la tabla existe
        if pedidos_table_exists:
            cursor.execute("DELETE FROM pedidos_reabastecimiento")
            print("✅ Pedidos eliminados")
        
        # 3. Eliminar ventas
        cursor.execute("DELETE FROM ventas")
        print("✅ Ventas eliminadas")
        
        # 4. Eliminar productos
        cursor.execute("DELETE FROM productos")
        print("✅ Productos eliminados")
        
        # 5. Resetear contadores automáticos (si existen)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('productos', 'ventas', 'creditos_pendientes', 'pedidos_reabastecimiento')")
        print("✅ Contadores reseteados")
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar limpieza
        cursor.execute("SELECT COUNT(*) FROM productos")
        productos_final = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ventas")
        ventas_final = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM creditos_pendientes")
        creditos_final = cursor.fetchone()[0]
        
        pedidos_final = 0
        if pedidos_table_exists:
            cursor.execute("SELECT COUNT(*) FROM pedidos_reabastecimiento")
            pedidos_final = cursor.fetchone()[0]
        
        print(f"\n✅ LIMPIEZA COMPLETADA")
        print(f"📊 Estado final:")
        print(f"   • Productos: {productos_final}")
        print(f"   • Ventas: {ventas_final}")
        print(f"   • Créditos: {creditos_final}")
        print(f"   • Pedidos: {pedidos_final}")
        
        # Cerrar conexión
        conn.close()
        
        print(f"\n🎉 Base de datos limpia y lista para pruebas")
        print(f"💾 Backup guardado como: {backup_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        return False

def main():
    """Función principal"""
    print("🧹 HERRAMIENTA DE LIMPIEZA - SISTEMA POS CREMERÍA")
    print("=" * 60)
    print("⚠️  ADVERTENCIA: Esta operación eliminará TODOS los datos")
    print("📝 Se creará un backup automáticamente")
    print()
    
    resultado = limpiar_base_datos()
    
    if resultado:
        print("\n✅ Proceso completado exitosamente")
        print("🔄 Reinicia el contenedor Docker para aplicar los cambios")
    else:
        print("\n❌ El proceso no se completó correctamente")

if __name__ == "__main__":
    main()