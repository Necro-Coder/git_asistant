#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Assistant - Punto de entrada global con detección automática de Python
"""
import sys
import subprocess
import shutil
from pathlib import Path

# Ruta al script principal
SCRIPT_PATH = Path("D:/proyectos/git_asistant/git_asistant.py")

def find_python_command():
    """Encuentra el comando de Python disponible en el sistema."""
    python_commands = ["py", "python", "python3"]
    
    for cmd in python_commands:
        if shutil.which(cmd):
            print(f"[DEBUG] Usando comando Python: {cmd}", file=sys.stderr)
            return cmd
    
    return None

def main():
    """Ejecuta el script principal con todos los argumentos pasados."""
    if not SCRIPT_PATH.exists():
        print(f"Error: No se encontró el script en {SCRIPT_PATH}", file=sys.stderr)
        sys.exit(1)
    
    # Encontrar comando Python disponible
    python_cmd = find_python_command()
    if not python_cmd:
        print("Error: No se encontró Python instalado.", file=sys.stderr)
        print("Instala Python desde: https://www.python.org/downloads/", file=sys.stderr)
        print("Asegúrate de marcar 'Add Python to PATH' durante la instalación.", file=sys.stderr)
        print(f"Comandos probados: py, python, python3", file=sys.stderr)
        sys.exit(1)
    
    # Ejecutar el script principal con los mismos argumentos
    try:
        result = subprocess.run([python_cmd, str(SCRIPT_PATH)] + sys.argv[1:])
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error ejecutando el script: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()