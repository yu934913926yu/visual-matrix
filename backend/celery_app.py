from celery import Celery
from config import Config
import os

def make_celery(app=None):
    celery = Celery(
        'visual_matrix',
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=['tasks.ai_tasks', 'tasks.health_check']
    )
    
    if app:
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# 创建Celery实例
celery = make_celery()

# Celery配置
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_routes={
        'tasks.ai_tasks.analyze_task': {'queue': 'analysis'},
        'tasks.ai_tasks.generate_task': {'queue': 'generation'},
        'tasks.health_check.check_api_health': {'queue': 'health'}
    },
    beat_schedule={
        'check-api-health': {
            'task': 'tasks.health_check.check_api_health',
            'schedule': 300.0,  # 每5分钟检查一次
        },
    }
)