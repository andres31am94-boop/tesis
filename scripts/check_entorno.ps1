# check_entorno.ps1
# Verifica el entorno de desarrollo de la tesis. SOLO LEE informacion: no instala ni modifica nada.
# Uso (desde la carpeta tesis):  powershell -ExecutionPolicy Bypass -File .\scripts\check_entorno.ps1
# Resultado: docs\entorno\reporte_entorno.txt

$ErrorActionPreference = "Continue"
$carpetaTesis = Split-Path -Parent $PSScriptRoot
$archivoSalida = Join-Path $carpetaTesis "docs\entorno\reporte_entorno.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $archivoSalida) | Out-Null

$reporte = New-Object System.Collections.Generic.List[string]
$reporte.Add("Reporte de entorno - " + (Get-Date -Format "yyyy-MM-dd HH:mm"))

function Seccion($titulo) {
    $reporte.Add("")
    $reporte.Add("=== $titulo ===")
}

function Probar($descripcion, [scriptblock]$comando) {
    try {
        $resultado = (& $comando 2>&1 | Out-String).Trim()
        if ($resultado -eq "") { $resultado = "(sin salida)" }
        $reporte.Add("[$descripcion]`n$resultado")
    } catch {
        $reporte.Add("[$descripcion]`nNO ENCONTRADO -> $($_.Exception.Message)")
    }
}

Seccion "Sistema operativo y hardware"
Probar "Sistema operativo" { (Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture | Format-List | Out-String) }
Probar "CPU" { (Get-CimInstance Win32_Processor).Name }
Probar "RAM total (GB)" { [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1) }
Probar "Espacio libre en C: (GB)" { [math]::Round((Get-PSDrive C).Free / 1GB, 1) }

Seccion "GPU"
Probar "Tarjetas de video" { Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion | Format-Table -AutoSize | Out-String }
Probar "nvidia-smi (solo GPU NVIDIA)" { nvidia-smi }

Seccion "Python"
Probar "python --version" { python --version }
Probar "Ubicaciones de python" { where.exe python }
Probar "Versiones instaladas (py launcher)" { py -0p }
Probar "pip" { python -m pip --version }

Seccion "SUMO"
Probar "Variable SUMO_HOME" { if ($env:SUMO_HOME) { $env:SUMO_HOME } else { "NO DEFINIDA" } }
Probar "Ubicacion de sumo" { where.exe sumo }
Probar "sumo --version" { sumo --version }

Seccion "Git"
Probar "git --version" { git --version }

Seccion "Librerias de Python"
$modulos = @("numpy", "pandas", "matplotlib", "scipy", "yaml", "cv2", "torch", "ultralytics", "serial", "traci", "sumolib")
foreach ($modulo in $modulos) {
    Probar "import $modulo" { python -c "import $modulo as m; print(getattr(m, '__version__', 'instalado (sin __version__)'))" }
}
Probar "PyTorch con CUDA" { python -c "import torch; print('torch', torch.__version__, '| CUDA disponible:', torch.cuda.is_available())" }

Seccion "ESP32 / Arduino"
Probar "Arduino IDE (instalacion por usuario)" { Test-Path "$env:LOCALAPPDATA\Programs\Arduino IDE\Arduino IDE.exe" }
Probar "Arduino IDE (Program Files)" { Test-Path "C:\Program Files\Arduino IDE\Arduino IDE.exe" }
Probar "arduino-cli" { arduino-cli version }
Probar "PlatformIO" { pio --version }

Seccion "Camara"
Probar "Camaras detectadas" { Get-PnpDevice -Class Camera, Image -ErrorAction SilentlyContinue | Select-Object Status, FriendlyName | Format-Table -AutoSize | Out-String }

$reporte | Out-File -FilePath $archivoSalida -Encoding utf8
$reporte | ForEach-Object { Write-Output $_ }
Write-Output ""
Write-Output "Reporte guardado en: $archivoSalida"
