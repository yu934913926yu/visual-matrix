# Gunicorn配置文件
import multiprocessing

# 绑定地址和端口
bind = "0.0.0.0:5000"

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作进程类型
worker_class = "eventlet"

# 工作进程连接数
worker_connections = 1000

# 最大请求数
max_requests = 1000

# 请求超时时间
timeout = 30

# 保活时间
keepalive = 2

# 日志配置
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# 进程管理
preload_app = True
daemon = False

# 其他配置
user = None
group = None
tmp_upload_dir = None