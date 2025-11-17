import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

print("\n=== CORRIGIENDO PRECIOS DE PRODUCTOS A GRANEL ===\n")

# Actualizar todos los productos a granel para que precio_normal = precio_por_kg
cursor.execute("""
    UPDATE productos 
    SET precio_normal = precio_por_kg 
    WHERE tipo_venta = 'granel' AND precio_por_kg > 0
""")

affected = cursor.rowcount
conn.commit()

print(f"✅ Se actualizaron {affected} productos a granel")

# Verificar el producto específico
cursor.execute("SELECT codigo, nombre, tipo_venta, precio_normal, precio_por_kg FROM productos WHERE codigo='200000300'")
producto = cursor.fetchone()

if producto:
    print(f"\n📦 Producto verificado:")
    print(f"  Código: {producto[0]}")
    print(f"  Nombre: {producto[1]}")
    print(f"  Tipo: {producto[2]}")
    print(f"  Precio Normal: ${producto[3]:.2f}")
    print(f"  Precio por Kg: ${producto[4]:.2f}")
    
    if producto[3] == producto[4]:
        print(f"\n✅ ¡Precios sincronizados correctamente!")
    else:
        print(f"\n⚠️ Los precios aún no coinciden")

conn.close()
print("\n")
