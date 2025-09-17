# Git Assistant 🚀

Un asistente de Git para consola desarrollado en Python que te permite gestionar múltiples proyectos de forma interactiva y eficiente.

**Autor:** Rubén Núñez Cotano

## 📋 Características

- **Gestión multiproyecto**: Maneja varios repositorios desde un archivo de configuración
- **Interfaz interactiva**: Navegación intuitiva con menús y selecciones
- **Operaciones Git completas**: Pull, Push, Commit, Branch management, Pull Requests
- **Explorador de archivos**: Navega y selecciona archivos específicos para commit
- **Manejo de ramas**: Crea, cambia y gestiona ramas fácilmente
- **Integración con GitHub CLI**: Crea Pull Requests directamente desde la consola
- **Gestión de dependencias automática**: Instala automáticamente las dependencias necesarias

## 🔧 Requisitos del Sistema

- **Python 3.7+**
- **Git** instalado y configurado
- **GitHub CLI (opcional)** para crear Pull Requests
- **Windows PowerShell** (recomendado)

## 📦 Instalación y Configuración

### Paso 1: Clonar el Repositorio

```powershell
git clone https://github.com/Necro-Coder/git_asistant.git
cd git_asistant
```

### Paso 2: Instalar Dependencias

El programa instalará automáticamente las dependencias cuando se ejecute por primera vez, pero también puedes instalarlas manualmente:

```powershell
pip install -r requirements.txt
```

**Dependencias incluidas:**
- `rich` - Interfaz de consola mejorada
- `InquirerPy` - Menús interactivos
- `pyyaml` - Soporte para archivos YAML
- `requests` - Peticiones HTTP

### Paso 3: Configurar Proyectos

Edita el archivo `proyectos.json` para incluir tus repositorios:

```json
[
    { "name": "Mi Proyecto 1", "path": "C:\\ruta\\a\\mi\\proyecto1" },
    { "name": "Mi Proyecto 2", "path": "C:\\ruta\\a\\mi\\proyecto2" },
    { "name": "Git-Assistant", "path": "D:\\proyectos\\git_asistant" }
]
```

También puedes usar formato YAML creando un archivo `proyectos.yaml`:

```yaml
- name: "Mi Proyecto 1"
  path: "C:\\ruta\\a\\mi\\proyecto1"
- name: "Mi Proyecto 2"
  path: "C:\\ruta\\a\\mi\\proyecto2"
```

## 🔐 Configuración de Git y GitHub

### Configuración Inicial de Git

Antes de usar el asistente, configura tu identidad en Git:

```powershell
# Configurar nombre de usuario y email
git config --global user.name "Tu Nombre"
git config --global user.email "tu.email@ejemplo.com"

# Configurar el gestor de credenciales (recomendado para Windows)
git config --global credential.helper manager
```

### Autenticación con GitHub

#### Opción 1: Token de Acceso Personal (Recomendado)

1. **Ve a GitHub** en tu navegador
2. **Navega a Settings** → Developer settings → Personal access tokens → Tokens (classic)
3. **Genera un nuevo token** con los permisos necesarios:
   - `repo` (acceso completo a repositorios)
   - `workflow` (si usas GitHub Actions)
   - `write:packages` (si publicas paquetes)
4. **Copia el token** generado
5. **En la primera operación Git**, cuando te pida credenciales:
   - Usuario: tu nombre de usuario de GitHub
   - Contraseña: pega el token (no tu contraseña real)

#### Opción 2: GitHub CLI (Recomendado para Pull Requests)

```powershell
# Instalar GitHub CLI
winget install GitHub.cli

# Autenticarse
gh auth login
```

Sigue las instrucciones en pantalla para autenticarte a través del navegador.

### Verificar Configuración

```powershell
# Verificar configuración de Git
git config --global --list

# Verificar autenticación con GitHub CLI
gh auth status

# Probar conexión con GitHub
git ls-remote https://github.com/tu-usuario/tu-repo.git
```

## 🚀 Uso del Programa

### Ejecutar el Asistente

```powershell
python git_asistant.py
```

### Flujo de Trabajo Típico

1. **Selecciona archivo de configuración** (por defecto `proyectos.json`)
2. **Elige los proyectos** que quieres gestionar
3. **Para cada proyecto:**
   - Verifica el estado del repositorio
   - Selecciona o crea una rama
   - Añade archivos si hay cambios
   - Realiza commit si es necesario
   - Ejecuta operaciones Git (pull, push, etc.)

### Operaciones Disponibles

- **Pull**: Actualiza desde el repositorio remoto
- **Fetch**: Descarga cambios sin fusionar
- **Status**: Muestra el estado del repositorio
- **Log**: Muestra el historial de commits
- **Push directo**: Sube cambios a origin HEAD
- **Push con upstream**: Establece la rama upstream
- **Pull Request**: Crea PR usando GitHub CLI
- **Gestión de ramas**: Cambia o crea nuevas ramas

## 🛠️ Funcionalidades Avanzadas

### Explorador de Archivos Interactivo

El programa incluye un explorador que te permite:
- Navegar por directorios
- Seleccionar archivos específicos para commit
- Ver archivos ya seleccionados
- Deshacer selecciones

### Gestión Automática de Dependencias

Si faltan dependencias, el programa:
1. Intenta instalarlas automáticamente
2. Si falla, reintenta con `--user`
3. Proporciona instrucciones claras en caso de error

### Manejo de Errores y Reversión

El programa incluye manejo de Ctrl+C que revierte automáticamente:
- Archivos añadidos al staging area
- Cambios de rama
- Operaciones incompletas

## 📝 Ejemplos de Uso

### Ejemplo 1: Actualizar Múltiples Proyectos

```powershell
python git_asistant.py
# Selecciona proyectos.json
# Marca los proyectos que quieres actualizar
# Para cada uno: Pull → Status → Push si es necesario
```

### Ejemplo 2: Crear Nueva Rama y Push

```powershell
python git_asistant.py
# Selecciona un proyecto
# Elige "Crear nueva rama"
# Añade archivos modificados
# Commit con mensaje descriptivo
# Push y establecer upstream
```

### Ejemplo 3: Crear Pull Request

```powershell
python git_asistant.py
# Selecciona proyecto
# Realiza cambios y commit
# Elige "Crear Pull Request"
# Completa título, descripción y rama base
```

## ⚠️ Solución de Problemas

### Error de Dependencias

```
[deps] ERROR: No se pudieron instalar las dependencias.
```

**Solución:**
```powershell
# Intenta instalación manual
pip install -r requirements.txt

# Si falla por permisos, usa --user
pip install --user -r requirements.txt

# O crea un entorno virtual
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Error de Autenticación Git

```
fatal: Authentication failed
```

**Solución:**
1. Verifica que tu token de acceso personal sea válido
2. Asegúrate de usar el token como contraseña, no tu contraseña de GitHub
3. Actualiza el gestor de credenciales:
   ```powershell
   git config --global credential.helper manager
   ```

### GitHub CLI No Encontrado

```
ERROR: GitHub CLI no está instalado
```

**Solución:**
```powershell
# Instalar GitHub CLI
winget install GitHub.cli

# O descargar desde: https://cli.github.com/
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaFuncionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/NuevaFuncionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisa la sección de **Solución de Problemas**
2. Abre un **Issue** en GitHub
3. Consulta la documentación de **Git** y **GitHub CLI**

---

**¡Que disfrutes gestionando tus repositorios! 🎉**
