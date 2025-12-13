#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import hashlib
import sys

# Conectar a la BD
conn = sqlite3.connect("pos_cremeria.db")
cursor = conn.cursor()

# Función para hash de contraseña (igual a auth_manager.py)
def hash_password(password):
    salt = "cremeria_salt_2024"  # Mismo salt que en config
    return hashlib.sha256((password + salt).encode()).hexdigest()

try:
    # Verificar si la tabla usuarios existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
    tabla_existe = cursor.fetchone()
    
    if not tabla_existe:
        print("[ERROR] La tabla 'usuarios' NO existe")
        
        # Crear la tabla
        cursor.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                activo INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        print("[OK] Tabla 'usuarios' creada")
    
    # Mostrar todos los usuarios
    cursor.execute("SELECT usuario, password, activo FROM usuarios")
    usuarios = cursor.fetchall()
    
    if usuarios:
        print(f"[OK] Usuarios registrados: {len(usuarios)}")
        for user in usuarios:
            usuario, password, activo = user
            estado = "Activo" if activo else "Inactivo"
            print(f"  - {usuario}: {estado}")
    else:
        print("[INFO] No hay usuarios registrados")
    
    # Verificar si admin existe
    print("\n[CHECK] Buscando usuario 'admin'...")
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
    admin_user = cursor.fetchone()
    
    if admin_user:
        print("[OK] Usuario 'admin' existe")
        
        # Verificar si la contraseña es correcta
        password_esperado = hash_password("Creme$123")
        if admin_user[1] == password_esperado:
            print("[OK] La contraseña es CORRECTA")
        else:
            print("[ERROR] La contraseña NO coincide")
            print(f"[INFO] Actualizando contraseña...")
            cursor.execute("UPDATE usuarios SET password = ? WHERE usuario = ?", 
                         (password_esperado, "admin"))
            conn.commit()
            print("[OK] Contraseña actualizada")
    else:
        print("[ERROR] Usuario 'admin' NO existe")
        
        # Crear el usuario admin
        password_hash = hash_password("Creme$123")
        try:
            cursor.execute("INSERT INTO usuarios (usuario, password, activo) VALUES (?, ?, ?)", 
                         ("admin", password_hash, 1))
            conn.commit()
            print("[OK] Usuario 'admin' creado exitosamente")
        except Exception as e:
            print(f"[ERROR] Error al crear usuario: {e}")

except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
finally:
    conn.close()
    print("\n[OK] Verificacion completada")
