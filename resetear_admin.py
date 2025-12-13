#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import hashlib
import sys

print("=" * 70)
print("RESETEAR CREDENCIALES DE ADMIN")
print("=" * 70)

try:
    # Conectar a la BD
    conn = sqlite3.connect("pos_cremeria.db")
    cursor = conn.cursor()
    
    # El salt por defecto en config.py
    SALT = "default-salt"
    
    def hash_password(password):
        return hashlib.sha256((password + SALT).encode()).hexdigest()
    
    # Nueva contraseña
    nueva_contraseña = "Creme$123"
    password_hash = hash_password(nueva_contraseña)
    
    print(f"\n[INFO] Usuario: admin")
    print(f"[INFO] Contraseña: {nueva_contraseña}")
    print(f"[INFO] Salt: {SALT}")
    print(f"[INFO] Hash: {password_hash[:30]}...")
    
    # Actualizar o insertar
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
    existe = cursor.fetchone()
    
    if existe:
        print("\n[UPDATE] Actualizando usuario existente...")
        cursor.execute("UPDATE usuarios SET password = ? WHERE usuario = ?", 
                     (password_hash, "admin"))
    else:
        print("\n[INSERT] Creando nuevo usuario...")
        cursor.execute("INSERT INTO usuarios (usuario, password, activo) VALUES (?, ?, ?)", 
                     ("admin", password_hash, 1))
    
    conn.commit()
    
    print("[OK] Credenciales actualizadas exitosamente")
    
    # Verificar
    cursor.execute("SELECT usuario, activo FROM usuarios WHERE usuario = ?", ("admin",))
    usuario, activo = cursor.fetchone()
    estado = "Activo" if activo else "Inactivo"
    print(f"\n[VERIFY] Usuario: {usuario} ({estado})")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("AHORA PUEDES INGRESAR CON:")
    print(f"Usuario: admin")
    print(f"Contrasena: Creme$123")
    print("=" * 70)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    sys.exit(1)

print("\n[OK] Completado\n")
