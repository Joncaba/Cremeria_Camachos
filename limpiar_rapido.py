#!/usr/bin/env python3
"""
Script rápido para limpiar base de datos - Sin confirmaciones interactivas
Para usar dentro del contenedor Docker
"""

import sqlite3
import shutil
from datetime import datetime

def limpiar_rapido():
    """Limpiar base de datos sin confirmaciones"""
    
    db_path = "pos_cremeria.db"
    
    try:
        # Backup automático
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_path, backup_name)
        print(f"Backup creado: {backup_name}")
        
        # Limpiar
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Eliminar datos
        cursor.execute("DELETE FROM creditos_pendientes")
        cursor.execute("DELETE FROM pedidos_reabastecimiento")
        cursor.execute("DELETE FROM ventas")
        cursor.execute("DELETE FROM productos")
        cursor.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        conn.close()
        
        print("✅ Base de datos limpia")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    limpiar_rapido()