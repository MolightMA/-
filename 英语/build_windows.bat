@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [打包] 调用 build_release.py（目录模式，首次较慢）...
python build_release.py
if errorlevel 1 (
  echo 打包失败。
  exit /b 1
)
echo.
echo 完成。请打开文件夹: dist\英语学习\
echo 双击运行: 英语学习.exe
echo 可将整个「英语学习」文件夹压缩发给别人使用。
pause
