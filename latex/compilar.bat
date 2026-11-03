@echo off
setlocal
pushd "%~dp0" || exit /b 1
echo Compilando main.tex...
pdflatex -halt-on-error -file-line-error -interaction=nonstopmode main.tex
if errorlevel 1 goto fallo
biber --quiet main
if errorlevel 1 goto fallo
pdflatex -halt-on-error -file-line-error -interaction=nonstopmode main.tex
if errorlevel 1 goto fallo
pdflatex -halt-on-error -file-line-error -interaction=nonstopmode main.tex
if errorlevel 1 goto fallo
if not exist main.pdf goto fallo
echo Informe generado: latex/main.pdf
popd
exit /b 0
:fallo
echo Error de compilacion. Revise latex/main.log y latex/main.blg.
popd
exit /b 1
