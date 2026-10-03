# Script de compilacion para el informe academico (main.tex)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[1/3] pdflatex (primera pasada)..." -ForegroundColor Cyan
& pdflatex -synctex=1 -interaction=nonstopmode main.tex | Out-Null

Write-Host "[2/3] Procesando bibliografia con biber..." -ForegroundColor Yellow
& biber --quiet main

Write-Host "[3/3] pdflatex (pasada final de enlaces y referencias)..." -ForegroundColor Green
& pdflatex -synctex=1 -interaction=nonstopmode main.tex | Out-Null

if (Test-Path "main.pdf") {
    $pdf = Get-Item "main.pdf"
    $sizeMB = [math]::Round($pdf.Length / 1MB, 2)
    Write-Host "[OK] Informe compilado exitosamente: main.pdf ($sizeMB MB)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] No se pudo generar main.pdf. Revise main.log." -ForegroundColor Red
}
