@echo off
setlocal

REM Intentar con 'py' primero (Python Launcher para Windows)
where py >nul 2>&1
if %errorlevel% == 0 (
    py "%~dp0git_asistant.py" %*
    goto :end
)

REM Si 'py' no está disponible, intentar con 'python'
where python >nul 2>&1
if %errorlevel% == 0 (
    python "%~dp0git_asistant.py" %*
    goto :end
)

REM Si 'python' no está disponible, intentar con 'python3'
where python3 >nul 2>&1
if %errorlevel% == 0 (
    python3 "%~dp0git_asistant.py" %*
    goto :end
)

REM Si ninguno funciona, mostrar error
echo Error: No se encontro Python instalado.
echo Instala Python desde: https://www.python.org/downloads/
echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
exit /b 1

:end