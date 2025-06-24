#!/bin/bash

# 启动Redis
redis-server --daemonize yes

# 等待Redis启动
sleep 2

# 初始化数据库
cd /app/backend
python init_db.py

# 启动Nginx
nginx

# 启动Supervisor管理的进程
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf