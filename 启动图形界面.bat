@echo off
chcp 65001 >nul
cd /d "%~dp0"

where pythonw >nul 2>&1
if %errorlevel%==0 (
  start "" pythonw "%~dp0enhance_gui.py"
  exit /b 0
)

where python >nul 2>&1
if %errorlevel%==0 (
  start "" python "%~dp0enhance_gui.py"
  exit /b 0
)

echo 未找到 Python，请先安装 Python 3 并勾选 Add Python to PATH。
pause
