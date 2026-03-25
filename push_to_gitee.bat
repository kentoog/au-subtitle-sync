@echo off
echo ========================================
echo AU 字幕外挂同步程序 - 推送到 Gitee
echo ========================================
echo.

REM 检查是否已初始化 Git 仓库
if not exist ".git" (
    echo [1/5] 初始化 Git 仓库...
    git init
    if errorlevel 1 (
        echo 错误: Git 初始化失败
        pause
        exit /b 1
    )
)

echo [2/5] 添加文件到暂存区...
git add .
if errorlevel 1 (
    echo 错误: 添加文件失败
    pause
    exit /b 1
)

echo [3/5] 提交代码...
git commit -m "Initial commit: AU 字幕外挂同步程序"
if errorlevel 1 (
    echo 警告: 可能没有新的更改需要提交
)

echo.
echo ========================================
echo 请先在 Gitee 上创建仓库，然后执行以下命令：
echo.
echo git remote add origin https://gitee.com/你的用户名/au-subtitle-sync.git
echo git branch -M main
echo git push -u origin main
echo ========================================
echo.

set /p remote_url="请输入 Gitee 仓库地址 (留空跳过): "

if not "%remote_url%"=="" (
    echo [4/5] 添加远程仓库...
    git remote add origin %remote_url% 2>nul
    git remote set-url origin %remote_url%
    
    echo [5/5] 推送到 Gitee...
    git branch -M main
    git push -u origin main
    if errorlevel 1 (
        echo 错误: 推送失败，请检查仓库地址和权限
        pause
        exit /b 1
    )
    echo.
    echo 推送成功！
)

echo.
echo 完成！
pause
