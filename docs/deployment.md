# Visual Matrix 部署指南

## 目录
1. [环境准备](#环境准备)
2. [开发环境部署](#开发环境部署)
3. [生产环境部署](#生产环境部署)
4. [配置说明](#配置说明)
5. [常见问题](#常见问题)

## 环境准备

### 系统要求
- Python 3.10+
- Node.js 16+
- Redis 6.0+
- PostgreSQL 13+ (生产环境推荐)
- Nginx (生产环境)

### 依赖服务
1. **Redis** - 用于Celery任务队列和WebSocket
2. **数据库** - SQLite（开发）或 PostgreSQL（生产）
3. **AI服务** - 需要至少配置一个AI服务（OpenAI/Gemini）

## 开发环境部署

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/visual-matrix.git
cd visual-matrix
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp .env.example .env

# 编辑.env文件，填入必要的配置
# 最少需要配置：
# - SECRET_KEY
# - 至少一个AI服务的API密钥
```

### 3. 初始化数据库

```bash
# 在backend目录下
python init_db.py

# 创建管理员账号（可选）
python create_admin.py
```

### 4. 启动后端服务

需要同时启动以下服务：

```bash
# 终端1 - Flask应用
python app.py

# 终端2 - Celery Worker
python start_worker.py

# 终端3 - Celery Beat（定时任务）
python start_beat.py

# 终端4 - Redis（如果未安装为系统服务）
redis-server
```

### 5. 前端设置

```bash
cd ../frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 6. 访问应用
- 前端：http://localhost:3000
- 后端API：http://localhost:5000

## 生产环境部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install python3.10 python3-pip nodejs npm redis-server postgresql nginx supervisor -y
```

### 2. 创建专用用户

```bash
sudo useradd -m -s /bin/bash visualmatrix
sudo su - visualmatrix
```

### 3. 部署代码

```bash
# 克隆代码
git clone https://github.com/yourusername/visual-matrix.git
cd visual-matrix

# 设置生产环境变量
cd backend
cp .env.example .env
# 编辑.env，设置生产环境配置
```

### 4. PostgreSQL设置

```bash
# 创建数据库和用户
sudo -u postgres psql

CREATE DATABASE visual_matrix;
CREATE USER visualmatrix WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE visual_matrix TO visualmatrix;
\q
```

### 5. 后端部署

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 初始化数据库
python init_db.py

# 收集静态文件
mkdir -p static
cp -r uploads static/
cp -r processed static/
```

### 6. 前端构建

```bash
cd ../frontend
npm install
npm run build
```

### 7. Supervisor配置

创建文件 `/etc/supervisor/conf.d/visualmatrix.conf`:

```ini
[program:visualmatrix-gunicorn]
command=/home/visualmatrix/visual-matrix/backend/venv/bin/gunicorn -c gunicorn.conf.py app:app
directory=/home/visualmatrix/visual-matrix/backend
user=visualmatrix
autostart=true
autorestart=true
stderr_logfile=/var/log/visualmatrix/gunicorn.err.log
stdout_logfile=/var/log/visualmatrix/gunicorn.out.log

[program:visualmatrix-celery]
command=/home/visualmatrix/visual-matrix/backend/venv/bin/python start_worker.py
directory=/home/visualmatrix/visual-matrix/backend
user=visualmatrix
autostart=true
autorestart=true
stderr_logfile=/var/log/visualmatrix/celery.err.log
stdout_logfile=/var/log/visualmatrix/celery.out.log

[program:visualmatrix-beat]
command=/home/visualmatrix/visual-matrix/backend/venv/bin/python start_beat.py
directory=/home/visualmatrix/visual-matrix/backend
user=visualmatrix
autostart=true
autorestart=true
stderr_logfile=/var/log/visualmatrix/beat.err.log
stdout_logfile=/var/log/visualmatrix/beat.out.log
```

### 8. Nginx配置

创建文件 `/etc/nginx/sites-available/visualmatrix`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # 前端静态文件
    location / {
        root /home/visualmatrix/visual-matrix/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # API代理
    location ~ ^/(api|auth|payment|admin) {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 上传大小限制
        client_max_body_size 10M;
    }
    
    # WebSocket
    location /socket.io {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 静态文件
    location /static {
        alias /home/visualmatrix/visual-matrix/backend/static;
        expires 30d;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/visualmatrix /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL证书（推荐）

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com
```

### 10. 启动服务

```bash
# 创建日志目录
sudo mkdir -p /var/log/visualmatrix
sudo chown visualmatrix:visualmatrix /var/log/visualmatrix

# 启动Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

## 配置说明

### 必要配置

1. **SECRET_KEY** - Flask密钥，生产环境必须修改
2. **JWT_SECRET_KEY** - JWT加密密钥
3. **DATABASE_URL** - 数据库连接字符串
4. **AI服务密钥** - 至少配置一个：
   - OPENAI_API_KEY
   - GEMINI_API_KEY

### 可选配置

1. **微信登录**
   - WECHAT_APP_ID
   - WECHAT_APP_SECRET
   
2. **支付系统**
   - 支付宝相关配置
   - 微信支付相关配置

3. **邮件服务**
   - MAIL_SERVER
   - MAIL_USERNAME
   - MAIL_PASSWORD

### 性能优化

1. **Gunicorn配置** (`backend/gunicorn.conf.py`)
   - workers: CPU核心数 * 2 + 1
   - worker_class: eventlet（支持WebSocket）
   
2. **Redis配置**
   - 设置最大内存限制
   - 配置持久化策略
   
3. **数据库优化**
   - 创建适当的索引
   - 定期清理过期数据

## 常见问题

### Q1: WebSocket连接失败
**A**: 检查Nginx配置中的WebSocket代理设置，确保使用eventlet worker。

### Q2: 文件上传失败
**A**: 检查目录权限和Nginx的client_max_body_size设置。

### Q3: Celery任务不执行
**A**: 确保Redis正在运行，检查Celery Worker日志。

### Q4: 数据库迁移问题
**A**: 使用Flask-Migrate管理数据库版本：
```bash
flask db init
flask db migrate -m "描述"
flask db upgrade
```

### Q5: 内存占用过高
**A**: 
- 限制Gunicorn worker数量
- 配置Redis最大内存
- 使用Celery任务清理临时文件

## 监控和维护

### 日志位置
- Gunicorn: `/var/log/visualmatrix/gunicorn.*.log`
- Celery: `/var/log/visualmatrix/celery.*.log`
- Nginx: `/var/log/nginx/access.log` 和 `error.log`

### 备份策略
1. 数据库：每日备份
2. 上传文件：定期同步到对象存储
3. 配置文件：版本控制

### 监控建议
- 使用Prometheus + Grafana监控系统指标
- 配置Sentry进行错误追踪
- 设置告警规则（CPU、内存、磁盘）

## 安全建议

1. **定期更新依赖**
   ```bash
   pip list --outdated
   npm outdated
   ```

2. **限制API访问频率**
   - 使用Flask-Limiter
   - Nginx rate limiting

3. **数据加密**
   - 使用HTTPS
   - 加密敏感配置
   - 数据库连接使用SSL

4. **权限控制**
   - 最小权限原则
   - 定期审查用户权限
   - API密钥定期轮换