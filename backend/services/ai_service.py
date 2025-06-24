import requests
import json
import time
import logging
from models import APIChannel, APIModel, db
from typing import Optional, List
import base64

logger = logging.getLogger(__name__)

class AIService:
    """AI服务调度器，负责智能选择可用的API通道"""
    
    def __init__(self):
        self.timeout = 30
        self.max_retries = 3
    
    def get_healthy_channels(self, model_type='analysis') -> List[dict]:
        """获取健康的API通道"""
        channels = db.session.query(APIChannel, APIModel).join(
            APIModel, APIChannel.id == APIModel.channel_id
        ).filter(
            APIChannel.is_active == True,
            APIChannel.is_healthy == True,
            APIModel.is_active == True,
            APIModel.is_available == True
        ).order_by(APIModel.priority.asc()).all()
        
        return [
            {
                'channel': channel,
                'model': model,
                'priority': model.priority
            }
            for channel, model in channels
        ]
    
    def analyze_image(self, image_path: str, prompt: str) -> Optional[str]:
        """
        图片分析 - 调用Gemini等视觉模型
        """
        healthy_channels = self.get_healthy_channels('analysis')
        
        if not healthy_channels:
            raise Exception("没有可用的AI分析通道")
        
        for channel_info in healthy_channels:
            try:
                channel = channel_info['channel']
                model = channel_info['model']
                
                logger.info(f"尝试使用通道 {channel.name} 的模型 {model.model_name}")
                
                if 'gemini' in model.model_name.lower():
                    result = self._call_gemini_vision(channel, model, image_path, prompt)
                elif 'gpt' in model.model_name.lower():
                    result = self._call_openai_vision(channel, model, image_path, prompt)
                else:
                    continue
                
                if result:
                    logger.info(f"分析成功，使用了 {channel.name}/{model.model_name}")
                    return result
                    
            except Exception as e:
                logger.warning(f"通道 {channel.name} 调用失败: {str(e)}")
                # 标记通道为不健康
                self._mark_channel_unhealthy(channel.id)
                continue
        
        raise Exception("所有AI分析通道都不可用")
    
    def generate_image(self, prompt: str) -> Optional[str]:
        """
        图片生成 - 调用DALL-E、Midjourney等生成模型
        """
        healthy_channels = self.get_healthy_channels('generation')
        
        if not healthy_channels:
            raise Exception("没有可用的AI生成通道")
        
        for channel_info in healthy_channels:
            try:
                channel = channel_info['channel']
                model = channel_info['model']
                
                logger.info(f"尝试使用通道 {channel.name} 的模型 {model.model_name}")
                
                if 'dall-e' in model.model_name.lower():
                    result = self._call_dalle(channel, model, prompt)
                elif 'midjourney' in model.model_name.lower():
                    result = self._call_midjourney(channel, model, prompt)
                elif 'stable-diffusion' in model.model_name.lower():
                    result = self._call_stable_diffusion(channel, model, prompt)
                else:
                    continue
                
                if result:
                    logger.info(f"生成成功，使用了 {channel.name}/{model.model_name}")
                    return result
                    
            except Exception as e:
                logger.warning(f"通道 {channel.name} 调用失败: {str(e)}")
                self._mark_channel_unhealthy(channel.id)
                continue
        
        raise Exception("所有AI生成通道都不可用")
    
    def _call_gemini_vision(self, channel: APIChannel, model: APIModel, image_path: str, prompt: str) -> str:
        """调用Gemini Vision API"""
        try:
            # 读取并编码图片
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            url = f"{channel.base_url}/v1/models/{model.model_name}:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': channel.api_key
            }
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            
            raise Exception("Gemini返回格式异常")
            
        except Exception as e:
            logger.error(f"Gemini调用失败: {str(e)}")
            raise e
    
    def _call_openai_vision(self, channel: APIChannel, model: APIModel, image_path: str, prompt: str) -> str:
        """调用OpenAI Vision API"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            url = f"{channel.base_url}/v1/chat/completions"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {channel.api_key}'
            }
            
            payload = {
                "model": model.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"OpenAI Vision调用失败: {str(e)}")
            raise e
    
    def _call_dalle(self, channel: APIChannel, model: APIModel, prompt: str) -> str:
        """调用DALL-E API"""
        try:
            url = f"{channel.base_url}/v1/images/generations"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {channel.api_key}'
            }
            
            payload = {
                "model": model.model_name,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard",
                "response_format": "url"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result['data'][0]['url']
            
        except Exception as e:
            logger.error(f"DALL-E调用失败: {str(e)}")
            raise e
    
    def _call_stable_diffusion(self, channel: APIChannel, model: APIModel, prompt: str) -> str:
        """调用Stable Diffusion API"""
        try:
            url = f"{channel.base_url}/v1/generation/text-to-image"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {channel.api_key}'
            }
            
            payload = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            # 这里需要根据实际API响应格式调整
            return result['artifacts'][0]['base64']  # 或者是URL
            
        except Exception as e:
            logger.error(f"Stable Diffusion调用失败: {str(e)}")
            raise e
    
    def _call_midjourney(self, channel: APIChannel, model: APIModel, prompt: str) -> str:
        """调用Midjourney API（第三方代理）"""
        try:
            url = f"{channel.base_url}/submit/imagine"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {channel.api_key}'
            }
            
            payload = {
                "prompt": prompt,
                "base64Array": []
            }
            
            # 提交任务
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            task_result = response.json()
            task_id = task_result.get('result')
            
            if not task_id:
                raise Exception("Midjourney任务提交失败")
            
            # 轮询结果
            for _ in range(60):  # 最多等待5分钟
                time.sleep(5)
                
                fetch_url = f"{channel.base_url}/task/{task_id}/fetch"
                fetch_response = requests.get(fetch_url, headers=headers, timeout=self.timeout)
                fetch_response.raise_for_status()
                
                fetch_result = fetch_response.json()
                status = fetch_result.get('status')
                
                if status == 'SUCCESS':
                    return fetch_result.get('imageUrl')
                elif status == 'FAILURE':
                    raise Exception("Midjourney生成失败")
            
            raise Exception("Midjourney生成超时")
            
        except Exception as e:
            logger.error(f"Midjourney调用失败: {str(e)}")
            raise e
    
    def _mark_channel_unhealthy(self, channel_id: int):
        """标记通道为不健康"""
        try:
            channel = APIChannel.query.get(channel_id)
            if channel:
                channel.is_healthy = False
                db.session.commit()
        except Exception as e:
            logger.error(f"标记通道不健康失败: {str(e)}")