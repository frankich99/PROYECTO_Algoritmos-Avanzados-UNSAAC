# Script de compilacion para el informe academico (main.tex)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[1/4] pdflatex (primera pasada)..." -ForegroundColor Cyan
& pdflatex -halt-on-error -file-line-error -interaction=nonstopmode main.tex | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pdflatex fallo; revise latex/main.log." }

Write-Host "[2/4] Procesando bibliografia con biber..." -ForegroundColor Yellow
& biber --quiet main
if ($LASTEXITCODE -ne 0) { throw "biber fallo; revise latex/main.blg." }

Write-Host "[3/4] pdflatex (referencias)..." -ForegroundColor Green
& pdflatex -halt-on-error -file-line-error -interaction=nonstopmode main.tex | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pdflatex fallo; revise latex/main.log." }

Write-Host "[4/4] pdflatex (enlaces y numeracion)..." -ForegroundColor Green
& pdflatex -halt-on-error -file-line-error -interaction=nonstopmode main.tex | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pdflatex fallo; revise latex/main.log." }

if (Test-Path "main.pdf") {
    $pdf = Get-Item "main.pdf"
    $sizeMB = [math]::Round($pdf.Length / 1MB, 2)
    Write-Host "[OK] Informe compilado exitosamente: main.pdf ($sizeMB MB)" -ForegroundColor Green
} else {
    throw "No se pudo generar main.pdf. Revise latex/main.log."
}
