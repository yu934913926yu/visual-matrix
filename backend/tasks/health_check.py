from celery_app import celery
from models import db, APIChannel, APIModel
import requests
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery.task
def check_api_health():
    """
    定期检查所有API通道的健康状态
    """
    logger.info("开始API健康检查...")
    
    channels = APIChannel.query.filter_by(is_active=True).all()
    
    for channel in channels:
        try:
            check_single_channel(channel)
        except Exception as e:
            logger.error(f"检查通道 {channel.name} 健康状态失败: {str(e)}")
    
    logger.info("API健康检查完成")

def check_single_channel(channel):
    """检查单个通道的健康状态"""
    try:
        start_time = time.time()
        
        # 根据不同的API类型发送不同的健康检查请求
        if 'openai' in channel.base_url.lower() or 'dall-e' in channel.name.lower():
            health_check_openai(channel)
        elif 'google' in channel.base_url.lower() or 'gemini' in channel.name.lower():
            health_check_gemini(channel)
        else:
            # 通用健康检查 - 简单的HTTP请求
            response = requests.get(f"{channel.base_url}/health", timeout=10)
            response.raise_for_status()
        
        end_time = time.time()
        latency = int((end_time - start_time) * 1000)
        
        # 更新通道状态
        channel.is_healthy = True
        channel.latency_ms = latency
        channel.last_checked_at = datetime.utcnow()
        
        # 更新关联模型的可用性
        for model in channel.api_models:
            model.is_available = True
        
        logger.info(f"通道 {channel.name} 健康检查通过，延迟: {latency}ms")
        
    except Exception as e:
        # 标记为不健康
        channel.is_healthy = False
        channel.last_checked_at = datetime.utcnow()
        
        # 标记关联模型为不可用
        for model in channel.api_models:
            model.is_available = False
        
        logger.warning(f"通道 {channel.name} 健康检查失败: {str(e)}")
    
    finally:
        db.session.commit()

def health_check_openai(channel):
    """OpenAI API健康检查"""
    url = f"{channel.base_url}/v1/models"
    headers = {
        'Authorization': f'Bearer {channel.api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    # 检查返回的模型列表
    result = response.json()
    if 'data' not in result:
        raise Exception("API响应格式异常")

def health_check_gemini(channel):
    """Gemini API健康检查"""
    url = f"{channel.base_url}/v1/models"
    params = {'key': channel.api_key}
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    result = response.json()
    if 'models' not in result:
        raise Exception("API响应格式异常")

@celery.task
def update_model_availability():
    """
    更新模型可用性状态
    """
    logger.info("开始更新模型可用性...")
    
    channels = APIChannel.query.filter_by(is_active=True, is_healthy=True).all()
    
    for channel in channels:
        try:
            if 'openai' in channel.base_url.lower():
                update_openai_models(channel)
            elif 'google' in channel.base_url.lower():
                update_gemini_models(channel)
        except Exception as e:
            logger.error(f"更新通道 {channel.name} 模型可用性失败: {str(e)}")
    
    db.session.commit()
    logger.info("模型可用性更新完成")

def update_openai_models(channel):
    """更新OpenAI模型可用性"""
    url = f"{channel.base_url}/v1/models"
    headers = {
        'Authorization': f'Bearer {channel.api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    result = response.json()
    available_models = [model['id'] for model in result['data']]
    
    # 更新数据库中的模型状态
    for model in channel.api_models:
        model.is_available = model.model_name in available_models

def update_gemini_models(channel):
    """更新Gemini模型可用性"""
    url = f"{channel.base_url}/v1/models"
    params = {'key': channel.api_key}
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    result = response.json()
    available_models = [model['name'].split('/')[-1] for model in result['models']]
    
    # 更新数据库中的模型状态
    for model in channel.api_models:
        model.is_available = model.model_name in available_models