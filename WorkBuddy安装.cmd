@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo 没有找到 Python。请先安装 Python 3.11 或以上，再运行本文件。
) else (
  python "%~dp0install-workbuddy.py"
)
pause
