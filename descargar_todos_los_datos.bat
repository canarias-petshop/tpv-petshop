@echo off
cd /d "D:\clon vs mode\tpv-petshop"
echo ===================================================
echo   DESCARGANDO COPIA DE SEGURIDAD DE DATOS (NUBE)
echo ===================================================
echo.
python backup_total_automatico.py
pause