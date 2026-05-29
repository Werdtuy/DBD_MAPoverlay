@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_NAME=DBDCompanionOverlay"
set "ROOT=%~dp0"
set "PYTHON="

if exist "%ROOT%.venv\Scripts\python.exe" (
    set "PYTHON=%ROOT%.venv\Scripts\python.exe"
) else (
    py --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON=py"
    ) else (
        python --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON=python"
        )
    )
)

if "%PYTHON%"=="" (
    echo Python was not found. Install Python 3.11+ or create a .venv first.
    goto fail
)

echo Using Python: %PYTHON%
%PYTHON% "%ROOT%scripts\build.py" %*
if errorlevel 1 goto fail

echo.
pause
exit /b 0

:fail
echo.
echo Build failed.
echo.
pause
exit /b 1
