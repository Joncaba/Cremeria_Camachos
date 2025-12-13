"""
Script para agregar códigos de barras a productos existentes.

Uso:
    python agregar_codigo_barras.py 123 7501234567890
    
Esto vinculará el código de barras 7501234567890 al producto con número 123.
El número es el PLU del producto (numero_producto).
"""
import sqlite3
import sys

DB_PATH = "pos_cremeria.db"

def agregar_codigo_barras(numero_producto, codigo_barras):
    """Vincular un código de barras a un producto existente por su número de producto (PLU)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # Verificar que el producto existe por numero_producto
        cur.execute("SELECT codigo, numero_producto, nombre, precio_normal FROM productos WHERE numero_producto = ?", (numero_producto,))
        producto = cur.fetchone()
        
        if not producto:
            print(f"❌ Error: Producto con número '{numero_producto}' no encontrado")
            return False
        
        codigo_actual, num_prod, nombre, precio = producto
        
        # Verificar si el código de barras ya está en uso
        cur.execute("SELECT codigo FROM productos WHERE codigo = ? AND numero_producto != ?", (codigo_barras, numero_producto))
        if cur.fetchone():
            print(f"⚠️  Código de barras '{codigo_barras}' ya está en uso por otro producto")
            return False
        
        # Actualizar código en codigos_barras si existe
        cur.execute("SELECT codigo FROM codigos_barras WHERE plu = ?", (numero_producto,))
        if cur.fetchone():
            cur.execute(
                "UPDATE codigos_barras SET codigo = ?, nombre = ?, precio = ? WHERE plu = ?",
                (codigo_barras, nombre, precio, numero_producto)
            )
        else:
            cur.execute(
                "INSERT INTO codigos_barras (codigo, plu, nombre, precio) VALUES (?, ?, ?, ?)",
                (codigo_barras, numero_producto, nombre, precio)
            )
        
        # Actualizar el código del producto en la tabla productos
        cur.execute("UPDATE productos SET codigo = ? WHERE numero_producto = ?", (codigo_barras, numero_producto))
        
        conn.commit()
        print(f"✅ Código de barras '{codigo_barras}' vinculado a producto '{nombre}'")
        print(f"   Número producto: {numero_producto} | Código anterior: {codigo_actual} → Nuevo código: {codigo_barras}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    
    try:
        numero_producto = int(sys.argv[1])
    except ValueError:
        print("❌ Error: El primer argumento debe ser un número (PLU del producto)")
        print(__doc__)
        sys.exit(1)
    
    codigo_barras = sys.argv[2]
    
    agregar_codigo_barras(numero_producto, codigo_barras)

if __name__ == "__main__":
    main()
