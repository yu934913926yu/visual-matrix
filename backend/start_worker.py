#!/usr/bin/env python
import os
import sys
from celery_app import celery

if __name__ == '__main__':
    # 设置环境变量
    os.environ.setdefault('FLASK_ENV', 'development')
    
    # 启动Celery worker
    celery.start(argv=[
        'celery',
        'worker',
        '--app=celery_app.celery',
        '--loglevel=info',
        '--queues=analysis,generation,health',
        '--concurrency=4'
    ])