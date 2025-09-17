# Git Assistant PowerShell Script
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ScriptPath = "D:\proyectos\git_asistant\git_asistant.py"

# Función para verificar si un comando existe
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Verificar que el script existe
if (-not (Test-Path $ScriptPath)) {
    Write-Error "No se encontró el script en: $ScriptPath"
    exit 1
}

# Intentar diferentes comandos de Python en orden de preferencia
$PythonCommands = @("py", "python", "python3")
$PythonCmd = $null

foreach ($cmd in $PythonCommands) {
    if (Test-Command $cmd) {
        $PythonCmd = $cmd
        Write-Verbose "Usando comando Python: $cmd"
        break
    }
}

if ($null -eq $PythonCmd) {
    Write-Error @"
Error: No se encontró Python instalado.
Instala Python desde: https://www.python.org/downloads/
Asegúrate de marcar 'Add Python to PATH' durante la instalación.

Comandos probados: $($PythonCommands -join ', ')
"@
    exit 1
}

# Ejecutar el script
try {
    & $PythonCmd $ScriptPath @Arguments
} catch {
    Write-Error "Error ejecutando el script: $_"
    exit 1
}