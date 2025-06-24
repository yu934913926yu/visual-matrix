#!/bin/bash

echo "=== 启动Visual Matrix开发环境 ==="

# 检查Redis是否运行
if ! pgrep -x "redis-server" > /dev/null; then
    echo "启动Redis..."
    redis-server --daemonize yes
fi

# 启动后端
echo "启动后端Flask应用..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python -m venv venv
fi

source venv/bin/activate  # Linux/Mac
# 或者在Windows上使用: venv\Scripts\activate

pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动Flask应用
python app.py &
FLASK_PID=$!

# 启动Celery Worker
python start_worker.py &
WORKER_PID=$!

# 启动Celery Beat
python start_beat.py &
BEAT_PID=$!

cd ../frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端开发服务器
echo "启动前端开发服务器..."
npm run dev &
FRONTEND_PID=$!

echo "=== 启动完成 ==="
echo "前端地址: http://localhost:3000"
echo "后端API: http://localhost:5000"
echo ""
echo "按Ctrl+C停止所有服务"

# 等待用户中断
trap "echo '正在停止服务...'; kill $FLASK_PID $WORKER_PID $BEAT_PID $FRONTEND_PID; exit" INT

wait