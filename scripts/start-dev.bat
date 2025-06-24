@echo off
echo === 启动Visual Matrix开发环境 ===

REM 启动Redis (需要先安装Redis for Windows)
echo 请确保Redis已经在运行...

REM 启动后端
echo 启动后端Flask应用...
cd backend

if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt

REM 初始化数据库
python init_db.py

REM 启动Flask应用
start /b python app.py

REM 启动Celery Worker
start /b python start_worker.py

REM 启动Celery Beat
start /b python start_beat.py

cd ..\frontend

REM 检查node_modules
if not exist "node_modules" (
    echo 安装前端依赖...
    npm install
)

REM 启动前端开发服务器
echo 启动前端开发服务器...
start /b npm run dev

echo === 启动完成 ===
echo 前端地址: http://localhost:3000
echo 后端API: http://localhost:5000
echo.
echo 按任意键停止所有服务
pause

REM 停止所有相关进程
taskkill /f /im python.exe
taskkill /f /im node.exe