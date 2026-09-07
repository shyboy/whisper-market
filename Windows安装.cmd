@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo 没有找到 Python。请在 Codex 中打开本文件夹并阅读安装说明.md。
) else (
  python "%~dp0install.py"
)
pause
