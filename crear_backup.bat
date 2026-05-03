@echo off
chcp 65001 >nul
echo ===================================================
echo    CREANDO COPIA DE SEGURIDAD (ANIMALARIUM TPV)
echo ===================================================
echo.

:: Obtener fecha y hora en formato limpio
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%b%%a)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set mytime=%mytime: =0%

:: Crear carpeta contenedora
set backup_folder=backups\codigo_backup_%mydate%_%mytime%
if not exist backups mkdir backups
mkdir "%backup_folder%"

:: Copiar los archivos Python y Markdown
copy *.py "%backup_folder%\" >nul
copy *.md "%backup_folder%\" >nul

echo [OK] Copia de seguridad completada con exito.
echo Los archivos se han guardado en: %backup_folder%
echo.
pause