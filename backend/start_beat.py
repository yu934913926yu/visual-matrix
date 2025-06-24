#!/usr/bin/env python
import os
from celery_app import celery

if __name__ == '__main__':
    # 设置环境变量
    os.environ.setdefault('FLASK_ENV', 'development')
    
    # 启动Celery beat (定时任务调度器)
    celery.start(argv=[
        'celery',
        'beat',
        '--app=celery_app.celery',
        '--loglevel=info'
    ])