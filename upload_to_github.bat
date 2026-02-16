@echo off
chcp 65001 >nul
echo ============================================
echo   🐙 上传到 GitHub
echo ============================================
echo.

cd /d "%~dp0"

REM 检查git
where git >nul 2>&1
if errorlevel 1 (
    echo ❌ Git未找到，请先安装Git
    pause
    exit /b 1
)

REM 初始化仓库
echo 🔧 初始化Git仓库...
git init
git branch -M main

REM 添加文件
echo 📤 添加文件...
git add image_downloader_gui.py image_downloader.py push_to_github.py

REM 提交
echo 📝 提交...
git commit -m "初始提交：添加网页图片下载器"

REM 设置远程仓库
echo 🔗 设置远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/chjantonychen/image-downloader.git

REM 推送
echo 🚀 推送到GitHub...
git push -u origin main

echo.
echo ============================================
echo ✅ 上传完成！
echo 📝 请在GitHub输入用户名和密码
echo 💡 密码请使用Personal Access Token
echo ============================================
pause
