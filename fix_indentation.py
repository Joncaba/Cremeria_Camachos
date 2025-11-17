#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para corregir la indentación en ventas.py"""

def fix_indentation():
    with open('ventas.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Líneas que necesitan cambiar de 12 espacios a 8 espacios (líneas 1476-1530 aprox)
    # Pero primero verificar el rango exacto
    modified = False
    new_lines = []
    
    for i, line in enumerate(lines, 1):
        # Si la línea tiene exactamente 12 espacios al inicio y está entre las líneas 1476-1530
        if 1476 <= i <= 1530:
            if line.startswith('            ') and not line.startswith('                '):
                # Tiene 12 espacios, reducir a 8
                new_line = line[4:]  # Quitar 4 espacios
                new_lines.append(new_line)
                modified = True
                print(f"Línea {i}: Reducida de 12 a 8 espacios")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    if modified:
        with open('ventas.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("\n✓ Archivo modificado exitosamente")
    else:
        print("No se encontraron líneas para modificar")

if __name__ == '__main__':
    fix_indentation()
