from flask import Blueprint, request, jsonify, current_app
from models import db, AITask, GeneratedResult, StyleTemplates, SystemConfig
from werkzeug.utils import secure_filename
import os
import uuid

api_bp = Blueprint('api', __name__)

@api_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """图片分析接口"""
    try:
        # 获取上传的文件和参数
        if 'image' not in request.files:
            return jsonify({'error': '未上传图片'}), 400
        
        file = request.files['image']
        user_prompt = request.form.get('user_prompt', '')
        style_id = request.form.get('style_id')
        
        # 验证用户token (这里简化处理)
        user_id = 1  # 实际应用中需要从token解析
        
        # 保存上传的图片
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # 创建AI任务
        task = AITask(
            user_id=user_id,
            status='analyzing',
            original_image_path=file_path
        )
        db.session.add(task)
        db.session.commit()
        
        # 这里应该调用Celery任务进行异步分析
        # analyze_task.delay(task.id, file_path, user_prompt, style_id)
        
        return jsonify({
            'message': '分析任务已提交',
            'task_id': task.id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-final-image', methods=['POST'])
def generate_final_image():
    """最终图片生成接口"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        final_prompt = data.get('final_prompt')
        quantity = data.get('quantity', 1)
        
        # 验证任务存在
        task = AITask.query.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        # 计算消耗积分
        base_cost = int(SystemConfig.query.filter_by(config_key='base_generation_cost').first().config_value)
        total_cost = base_cost * quantity
        
        # 检查用户积分是否足够
        if task.user.points < total_cost:
            return jsonify({'error': '积分不足'}), 400
        
        # 扣除积分
        task.user.points -= total_cost
        task.total_cost_points = total_cost
        task.quantity_requested = quantity
        task.final_prompt = final_prompt
        task.status = 'generating'
        
        db.session.commit()
        
        # 调用Celery任务进行图片生成
        # generate_task.delay(task_id)
        
        return jsonify({
            'message': '生成任务已提交',
            'task_id': task_id,
            'cost': total_cost
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/style-templates', methods=['GET'])
def get_style_templates():
    """获取风格模板列表"""
    templates = StyleTemplates.query.filter_by(is_active=True).order_by(StyleTemplates.sort_order).all()
    
    return jsonify({
        'templates': [{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'thumbnail_url': t.thumbnail_url
        } for t in templates]
    })

@api_bp.route('/task-status/<int:task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    task = AITask.query.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    result = {
        'id': task.id,
        'status': task.status,
        'created_at': task.created_at.isoformat(),
        'quantity_requested': task.quantity_requested,
        'quantity_succeeded': task.quantity_succeeded
    }
    
    if task.status == 'completed':
        results = GeneratedResult.query.filter_by(task_id=task_id).all()
        result['generated_images'] = [{
            'id': r.id,
            'image_url': r.image_url,
            'finalized_image_url': r.finalized_image_url
        } for r in results]
    
    return jsonify(result)