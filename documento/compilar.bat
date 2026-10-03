@echo off
echo ========================================================
echo Compilando informe LaTeX (main.tex)...
echo ========================================================
pdflatex -synctex=1 -interaction=nonstopmode main.tex
biber --quiet main
pdflatex -synctex=1 -interaction=nonstopmode main.tex
echo ========================================================
echo Compilacion finalizada. Verifique main.pdf.
echo ========================================================
pause
