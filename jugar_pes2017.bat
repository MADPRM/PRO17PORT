@echo off
setlocal
cd /d "%~dp0"
if exist "PES2017_Launcher.exe" (
    start "" "%~dp0PES2017_Launcher.exe"
) else if exist "launcher_pes2017.py" (
    start "" pythonw "%~dp0launcher_pes2017.py"
) else (
    echo [ERROR] No se encontro PES2017_Launcher.exe ni launcher_pes2017.py.
    pause
)
