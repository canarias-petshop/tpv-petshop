@echo off
cd /d "D:\clon vs mode\tpv-petshop"
echo =========================================
echo INICIANDO COPIA DE SEGURIDAD ANIMALARIUM
echo =========================================

echo.
echo [1/2] Iniciando Copia de Base de Datos (Nube)...
.venv\Scripts\python.exe backup_total_automatico.py

echo.
echo [2/2] Iniciando Copia del Codigo Fuente e Imagenes...
.venv\Scripts\python.exe backup_codigo.py

echo.
echo =========================================
echo COPIA DE SEGURIDAD COMPLETADA CON EXITO
echo =========================================
