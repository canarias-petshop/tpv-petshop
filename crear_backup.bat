@echo off
echo ===================================================
echo   CREANDO BACKUP LOCAL: Animalarium ERP v3.0
echo ===================================================

set FECHA=%date:~6,4%%date:~3,2%%date:~0,2%
set NOMBRE_ZIP=Backup_Animalarium_v3.0_%FECHA%.zip

echo Comprimiendo proyecto (ignorando archivos innecesarios)...
powershell.exe -nologo -noprofile -command "Get-ChildItem -Exclude '.venv', '__pycache__', '.git', '*.zip', 'fichas_a_importar' | Compress-Archive -DestinationPath '%NOMBRE_ZIP%' -Force"

echo.
echo ✅ Backup %NOMBRE_ZIP% creado con exito en tu carpeta.
pause