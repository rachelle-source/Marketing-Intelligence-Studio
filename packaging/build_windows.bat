@echo off
REM Build the Windows .exe. Run this ON WINDOWS with Python 3.12+ installed
REM (get it from python.org — check "Add Python to PATH" during install).
REM
REM Usage: double-click this file, or run it from a Command Prompt:
REM     packaging\build_windows.bat

cd /d "%~dp0\.."

python -m venv .venv
call .venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller packaging\pyinstaller.spec --noconfirm --distpath dist --workpath build

echo.
echo Build complete:
echo   dist\Marketing Intelligence Studio\Marketing Intelligence Studio.exe
echo.
pause
