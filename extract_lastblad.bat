@echo off
setlocal
cd /d "%~dp0"

echo Running The Last Blade extractor from:
echo %CD%
echo.

python "%~dp0extract_lastblad.py"

echo.
pause
