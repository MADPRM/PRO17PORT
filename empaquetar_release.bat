@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===================================================
echo   PRO17PORT — Empaquetador de Release para Windows
echo ===================================================
echo.

set "DIST_DIR=%~dp0dist"
set "STAGE_DIR=%DIST_DIR%\PRO17PORT-Windows-x64"
set "ZIP_FILE=%DIST_DIR%\PRO17PORT-v1.0-Windows-x64.zip"

if not exist "out\PES2017.exe" (
    if exist "out\gpu\PES2017.exe" (
        copy /y "out\gpu\PES2017.exe" "out\PES2017.exe" >nul
    ) else (
        echo [ERROR] No se encontro out\PES2017.exe. Compila primero con build.sh o ninja.
        pause
        exit /b 1
    )
)

echo [1/4] Preparando carpeta de distribucion...
if exist "%STAGE_DIR%" rmdir /s /q "%STAGE_DIR%"
if exist "%ZIP_FILE%" del /f /q "%ZIP_FILE%"
mkdir "%STAGE_DIR%"
mkdir "%STAGE_DIR%\out"
mkdir "%STAGE_DIR%\scripts"

echo [2/4] Optimizando binario principal (reduccion de tamano)...
where llvm-strip >nul 2>nul
if %errorlevel% equ 0 (
    llvm-strip --strip-debug -o "%STAGE_DIR%\out\PES2017.exe" "out\PES2017.exe"
) else (
    copy /y "out\PES2017.exe" "%STAGE_DIR%\out\PES2017.exe" >nul
)

echo [3/4] Copiando librerias DLL de Windows y scripts de inicio...
copy /y "out\*.dll" "%STAGE_DIR%\out\" >nul
copy /y "PES2017_Launcher.exe" "%STAGE_DIR%\" >nul
copy /y "launcher_pes2017.py" "%STAGE_DIR%\" >nul
copy /y "jugar_pes2017.bat" "%STAGE_DIR%\" >nul
copy /y "pes2017.ini" "%STAGE_DIR%\" >nul
copy /y "README.md" "%STAGE_DIR%\" >nul
copy /y "scripts\*.py" "%STAGE_DIR%\scripts\" >nul

echo [4/4] Creando archivo comprimido ZIP para GitHub Releases...
if exist "D:\MSYS2\clang64\bin\python3.exe" (
    D:\MSYS2\clang64\bin\python3.exe -c "import zipfile, os; from pathlib import Path; src = Path(r'%STAGE_DIR%'); dst = Path(r'%ZIP_FILE%'); z = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED); [z.write(Path(r)/f, Path(r).relative_to(src)/f) for r, _, files in os.walk(src) for f in files]; z.close()"
) else (
    python -c "import zipfile, os; from pathlib import Path; src = Path(r'%STAGE_DIR%'); dst = Path(r'%ZIP_FILE%'); z = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED); [z.write(Path(r)/f, Path(r).relative_to(src)/f) for r, _, files in os.walk(src) for f in files]; z.close()" 2>nul
)
if not exist "%ZIP_FILE%" (
    powershell -NoProfile -Command "$ProgressPreference = 'SilentlyContinue'; Compress-Archive -Path '%STAGE_DIR%\*' -DestinationPath '%ZIP_FILE%' -Force"
)

echo.
echo ===================================================
echo   PAQUETE DE RELEASE GENERADO CON EXITO
echo   Ubicacion: %ZIP_FILE%
echo ===================================================
echo.
