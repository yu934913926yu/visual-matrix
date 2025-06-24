# 多阶段构建
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Python后端镜像
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    redis-server \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制后端代码
COPY backend/ ./backend/

# 安装Python依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制前端构建文件
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 复制配置文件
COPY backend/supervisord.conf /etc/supervisor/conf.d/
COPY deploy/nginx.conf /etc/nginx/sites-available/default

# 创建必要目录
RUN mkdir -p /app/backend/logs \
    /app/backend/uploads \
    /app/backend/processed \
    /var/log/supervisor

# 暴露端口
EXPOSE 80 5000

# 启动脚本
COPY deploy/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]