# Desktop- und Startmenü-Verknüpfung für Rezept-Stempel (ohne Terminal).
# Aufruf:  .\packaging\windows\install-shortcut.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Exe = Join-Path $Root "dist\Rezept-Stempel.exe"
$Pyw = Join-Path $Root "Rezept-Stempel.pyw"

$GuiExe = Join-Path $Root ".venv\Scripts\rezept-stempel-gui.exe"
$Pythonw = Join-Path $Root ".venv\Scripts\pythonw.exe"

$Target = $null
$Args = $null
$WorkDir = "$Root"

if (Test-Path $Exe) {
    $Target = $Exe
    $WorkDir = Split-Path $Exe
} elseif (Test-Path $GuiExe) {
    $Target = $GuiExe
} else {
    if (-not (Test-Path $Pythonw)) {
        $cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
        if ($cmd) { $Pythonw = $cmd.Source }
    }
    if (-not (Test-Path $Pythonw)) {
        throw "Weder dist\Rezept-Stempel.exe noch pythonw.exe gefunden. Zuerst build.ps1 oder: pip install -e `".[desktop]`"."
    }
    $Target = $Pythonw
    $Args = "`"$Pyw`""
}

function New-RezeptShortcut([string]$LinkPath) {
    $Wsh = New-Object -ComObject WScript.Shell
    $Shortcut = $Wsh.CreateShortcut($LinkPath)
    $Shortcut.TargetPath = $Target
    if ($Args) { $Shortcut.Arguments = $Args }
    $Shortcut.WorkingDirectory = $WorkDir
    $Shortcut.WindowStyle = 1
    $Shortcut.Description = "Rezept-PDFs stempeln (Menge und Datum)"
    $Shortcut.Save()
    Write-Host "Verknuepfung: $LinkPath"
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
New-Item -ItemType Directory -Force -Path $StartMenu | Out-Null
New-RezeptShortcut (Join-Path $Desktop "Rezept-Stempel.lnk")
New-RezeptShortcut (Join-Path $StartMenu "Rezept-Stempel.lnk")
