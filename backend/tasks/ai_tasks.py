from celery_app import celery
from models import db, AITask, GeneratedResult, StyleTemplates, APIChannel, APIModel
from services.ai_service import AIService
from services.websocket_service import WebSocketService
import traceback
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def analyze_task(self, task_id, image_path, user_prompt=None, style_id=None):
    """
    图片分析任务
    """
    task = None
    try:
        # 获取任务
        task = AITask.query.get(task_id)
        if not task:
            raise Exception(f"任务 {task_id} 不存在")
        
        # 更新任务状态
        task.status = 'analyzing'
        db.session.commit()
        
        # 构建分析提示词
        prompt = "请作为一名顶级的商业广告导演，仔细分析这张商品图片，并为其设计一个富有创意的商业场景。"
        
        # 如果用户提供了自定义需求
        if user_prompt:
            prompt += f"\n用户需求：{user_prompt}"
        
        # 如果选择了风格模板
        if style_id:
            style_template = StyleTemplates.query.get(style_id)
            if style_template:
                prompt += f"\n风格要求：{style_template.prompt_instruction}"
        
        prompt += "\n请生成一个详细的、适合AI图像生成的提示词，要求包含场景描述、光线设置、构图建议等。"
        
        # 调用AI服务进行分析
        ai_service = AIService()
        analysis_result = ai_service.analyze_image(image_path, prompt)
        
        if not analysis_result:
            raise Exception("AI分析返回空结果")
        
        # 更新任务结果
        task.gemini_prompt = analysis_result
        task.status = 'analyzed'
        db.session.commit()
        
        # 通过WebSocket推送结果
        WebSocketService.emit_to_user(
            task.user_id,
            'analysis_complete',
            {
                'task_id': task_id,
                'prompt': analysis_result,
                'status': 'analyzed'
            }
        )
        
        logger.info(f"分析任务 {task_id} 完成")
        return analysis_result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"分析任务 {task_id} 失败: {error_msg}")
        logger.error(traceback.format_exc())
        
        if task:
            task.status = 'failed'
            task.error_log = error_msg
            db.session.commit()
            
            # 推送错误信息
            WebSocketService.emit_to_user(
                task.user_id,
                'analysis_failed',
                {
                    'task_id': task_id,
                    'error': error_msg
                }
            )
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=e)
        
        raise e

@celery.task(bind=True, max_retries=3)
def generate_task(self, task_id):
    """
    图片生成任务
    """
    task = None
    try:
        # 获取任务
        task = AITask.query.get(task_id)
        if not task:
            raise Exception(f"任务 {task_id} 不存在")
        
        # 更新任务状态
        task.status = 'generating'
        db.session.commit()
        
        # 通知用户开始生成
        WebSocketService.emit_to_user(
            task.user_id,
            'generation_started',
            {
                'task_id': task_id,
                'quantity': task.quantity_requested
            }
        )
        
        ai_service = AIService()
        generated_count = 0
        
        # 批量生成图片
        for i in range(task.quantity_requested):
            try:
                image_url = ai_service.generate_image(task.final_prompt)
                
                if image_url:
                    # 保存生成结果
                    result = GeneratedResult(
                        task_id=task_id,
                        image_url=image_url
                    )
                    db.session.add(result)
                    generated_count += 1
                    
                    # 实时推送进度
                    WebSocketService.emit_to_user(
                        task.user_id,
                        'generation_progress',
                        {
                            'task_id': task_id,
                            'completed': generated_count,
                            'total': task.quantity_requested,
                            'image_url': image_url
                        }
                    )
                
            except Exception as img_error:
                logger.error(f"生成第 {i+1} 张图片失败: {str(img_error)}")
                continue
        
        # 更新任务状态
        task.quantity_succeeded = generated_count
        if generated_count > 0:
            task.status = 'completed'
        else:
            task.status = 'failed'
            task.error_log = "所有图片生成都失败了"
        
        db.session.commit()
        
        # 推送最终结果
        if task.status == 'completed':
            results = GeneratedResult.query.filter_by(task_id=task_id).all()
            WebSocketService.emit_to_user(
                task.user_id,
                'generation_complete',
                {
                    'task_id': task_id,
                    'images': [{'id': r.id, 'url': r.image_url} for r in results]
                }
            )
        else:
            WebSocketService.emit_to_user(
                task.user_id,
                'generation_failed',
                {
                    'task_id': task_id,
                    'error': task.error_log
                }
            )
        
        logger.info(f"生成任务 {task_id} 完成，成功生成 {generated_count} 张图片")
        return generated_count
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"生成任务 {task_id} 失败: {error_msg}")
        logger.error(traceback.format_exc())
        
        if task:
            task.status = 'failed'
            task.error_log = error_msg
            db.session.commit()
            
            WebSocketService.emit_to_user(
                task.user_id,
                'generation_failed',
                {
                    'task_id': task_id,
                    'error': error_msg
                }
            )
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=120, exc=e)
        
        raise e