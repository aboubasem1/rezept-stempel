# Baut Rezept-Stempel.exe (ohne Konsole) und legt Verknüpfungen an.
# In PowerShell, im Ordner tools\rezept-stempel:
#   .\packaging\windows\build.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[desktop]"
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean ".\packaging\windows\Rezept-Stempel.spec"

$Exe = Join-Path $Root "dist\Rezept-Stempel.exe"
if (-not (Test-Path $Exe)) {
    throw "Build fehlgeschlagen: $Exe nicht gefunden."
}
Write-Host "EXE: $Exe"
& (Join-Path $PSScriptRoot "install-shortcut.ps1")
Write-Host "Fertig. Doppelklick auf die Desktop-Verknuepfung 'Rezept-Stempel'."
