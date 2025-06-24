from flask import Blueprint, request, jsonify, current_app
from models import db, AITask, GeneratedResult, StyleTemplates, SystemConfig, User, ProjectFolder
from werkzeug.utils import secure_filename
from utils.auth import token_required
from tasks.ai_tasks import analyze_task, generate_task
import os
import uuid
import logging

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

@api_bp.route('/analyze-image', methods=['POST'])
@token_required
def analyze_image(current_user):
    """图片分析接口"""
    try:
        # 检查用户积分
        analyze_cost = int(SystemConfig.query.filter_by(config_key='analyze_cost').first().config_value)
        if current_user.points < analyze_cost:
            return jsonify({'error': '积分不足，请先充值'}), 400
        
        # 获取上传的文件和参数
        if 'image' not in request.files:
            return jsonify({'error': '未上传图片'}), 400
        
        file = request.files['image']
        user_prompt = request.form.get('user_prompt', '')
        style_id = request.form.get('style_id', type=int)
        
        # 验证文件
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 保存上传的图片
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # 扣除分析积分
        current_user.points -= analyze_cost
        
        # 创建AI任务
        task = AITask(
            user_id=current_user.id,
            status='pending',
            original_image_path=file_path
        )
        db.session.add(task)
        db.session.commit()
        
        # 提交异步分析任务
        analyze_task.delay(task.id, file_path, user_prompt, style_id)
        
        return jsonify({
            'message': '分析任务已提交',
            'task_id': task.id,
            'cost': analyze_cost
        })
    
    except Exception as e:
        logger.error(f"图片分析失败: {str(e)}")
        return jsonify({'error': '图片分析失败'}), 500

@api_bp.route('/generate-final-image', methods=['POST'])
@token_required
def generate_final_image(current_user):
    """最终图片生成接口"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        final_prompt = data.get('final_prompt')
        quantity = data.get('quantity', 1)
        
        # 验证任务存在且属于当前用户
        task = AITask.query.filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        if task.status != 'analyzed':
            return jsonify({'error': '任务状态异常'}), 400
        
        # 计算消耗积分（考虑会员折扣）
        base_cost = int(SystemConfig.query.filter_by(config_key='base_generation_cost').first().config_value)
        
        # 计算会员折扣
        discount = 1.0
        if current_user.membership_tier_id and current_user.membership_expires_at:
            from datetime import datetime
            if current_user.membership_expires_at > datetime.utcnow():
                discount = current_user.membership_tier.generation_discount_percent / 100.0
        
        total_cost = int(base_cost * quantity * discount)
        
        # 检查用户积分是否足够
        if current_user.points < total_cost:
            return jsonify({'error': '积分不足，请先充值'}), 400
        
        # 扣除积分
        current_user.points -= total_cost
        task.total_cost_points = total_cost
        task.quantity_requested = quantity
        task.final_prompt = final_prompt
        task.status = 'generating'
        
        db.session.commit()
        
        # 提交异步生成任务
        generate_task.delay(task_id)
        
        return jsonify({
            'message': '生成任务已提交',
            'task_id': task_id,
            'cost': total_cost,
            'discount_applied': discount < 1.0
        })
    
    except Exception as e:
        logger.error(f"图片生成失败: {str(e)}")
        return jsonify({'error': '图片生成失败'}), 500

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
@token_required
def get_task_status(current_user, task_id):
    """获取任务状态"""
    task = AITask.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    result = {
        'id': task.id,
        'status': task.status,
        'created_at': task.created_at.isoformat(),
        'quantity_requested': task.quantity_requested,
        'quantity_succeeded': task.quantity_succeeded,
        'total_cost_points': task.total_cost_points,
        'gemini_prompt': task.gemini_prompt,
        'final_prompt': task.final_prompt,
        'error_log': task.error_log
    }
    
    if task.status in ['completed', 'generating']:
        results = GeneratedResult.query.filter_by(task_id=task_id).all()
        result['generated_images'] = [{
            'id': r.id,
            'image_url': r.image_url,
            'finalized_image_url': r.finalized_image_url,
            'created_at': r.created_at.isoformat()
        } for r in results]
    
    return jsonify(result)

@api_bp.route('/image/finalize', methods=['POST'])
@token_required
def finalize_image(current_user):
    """完成图片编辑并生成最终版本"""
    try:
        data = request.get_json()
        result_id = data.get('result_id')
        editor_data = data.get('editor_data')  # Fabric.js画布数据
        
        # 验证生成结果存在且属于当前用户
        result = GeneratedResult.query.join(AITask).filter(
            GeneratedResult.id == result_id,
            AITask.user_id == current_user.id
        ).first()
        
        if not result:
            return jsonify({'error': '图片不存在'}), 404
        
        # 使用图片处理服务生成最终图片
        from services.image_service import ImageService
        image_service = ImageService()
        
        finalized_url = image_service.apply_editor_data(
            result.image_url,
            editor_data
        )
        
        # 保存编辑数据和最终图片URL
        result.editor_data_json = json.dumps(editor_data)
        result.finalized_image_url = finalized_url
        
        db.session.commit()
        
        return jsonify({
            'message': '图片编辑完成',
            'finalized_image_url': finalized_url
        })
    
    except Exception as e:
        logger.error(f"完成图片编辑失败: {str(e)}")
        return jsonify({'error': '图片编辑失败'}), 500

@api_bp.route('/projects', methods=['GET'])
@token_required
def get_user_projects(current_user):
    """获取用户的项目文件夹"""
    folders = ProjectFolder.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'folders': [{
            'id': f.id,
            'name': f.name,
            'created_at': f.created_at.isoformat(),
            'task_count': len(f.ai_tasks)
        } for f in folders]
    })

@api_bp.route('/projects', methods=['POST'])
@token_required
def create_project(current_user):
    """创建项目文件夹"""
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'error': '文件夹名称不能为空'}), 400
        
        folder = ProjectFolder(
            user_id=current_user.id,
            name=name
        )
        
        db.session.add(folder)
        db.session.commit()
        
        return jsonify({
            'message': '文件夹创建成功',
            'folder_id': folder.id
        })
    
    except Exception as e:
        logger.error(f"创建文件夹失败: {str(e)}")
        return jsonify({'error': '创建文件夹失败'}), 500

@api_bp.route('/tasks/<int:task_id>/move-to-project', methods=['POST'])
@token_required
def move_task_to_project(current_user, task_id):
    """将任务移动到项目文件夹"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        
        task = AITask.query.filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        if project_id:
            folder = ProjectFolder.query.filter_by(id=project_id, user_id=current_user.id).first()
            if not folder:
                return jsonify({'error': '文件夹不存在'}), 404
        
        task.project_id = project_id
        db.session.commit()
        
        return jsonify({'message': '任务移动成功'})
    
    except Exception as e:
        logger.error(f"移动任务失败: {str(e)}")
        return jsonify({'error': '移动任务失败'}), 500

def allowed_file(filename):
    """检查文件格式是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/my-tasks', methods=['GET'])
@token_required
def get_my_tasks(current_user):
    """获取当前用户的任务列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        project_id = request.args.get('project_id', type=int)
        
        query = AITask.query.filter_by(user_id=current_user.id)
        
        if status:
            query = query.filter(AITask.status == status)
        if project_id:
            query = query.filter(AITask.project_id == project_id)
        
        pagination = query.order_by(AITask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        tasks = []
        for task in pagination.items:
            task_data = {
                'id': task.id,
                'status': task.status,
                'quantity_requested': task.quantity_requested,
                'quantity_succeeded': task.quantity_succeeded,
                'total_cost_points': task.total_cost_points,
                'created_at': task.created_at.isoformat(),
                'project_id': task.project_id,
                'project_name': task.project_folder.name if task.project_folder else None,
                'generated_images': []
            }
            
            for result in task.generated_results:
                task_data['generated_images'].append({
                    'id': result.id,
                    'image_url': result.image_url,
                    'finalized_image_url': result.finalized_image_url,
                    'created_at': result.created_at.isoformat()
                })
            
            tasks.append(task_data)
        
        return jsonify({
            'tasks': tasks,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total
            }
        })
    
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({'error': '获取任务列表失败'}), 500

@api_bp.route('/user/points-history', methods=['GET'])
@token_required
def get_points_history(current_user):
    """获取用户积分历史"""
    try:
        # 从订单记录中获取充值历史
        orders = Order.query.filter_by(
            user_id=current_user.id,
            status='paid',
            product_type='points'
        ).order_by(Order.created_at.desc()).all()
        
        # 从任务记录中获取消费历史
        tasks = AITask.query.filter_by(user_id=current_user.id).filter(
            AITask.total_cost_points > 0
        ).order_by(AITask.created_at.desc()).all()
        
        history = []
        
        # 添加充值记录
        for order in orders:
            history.append({
                'type': 'recharge',
                'points': order.points_gained,
                'amount': order.amount,
                'created_at': order.created_at.isoformat(),
                'description': f'充值 - {order.amount}元'
            })
        
        # 添加消费记录
        for task in tasks:
            history.append({
                'type': 'consume',
                'points': -task.total_cost_points,
                'task_id': task.id,
                'created_at': task.created_at.isoformat(),
                'description': f'图片生成 - {task.quantity_requested}张'
            })
        
        # 按时间排序
        history.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'current_points': current_user.points,
            'history': history[:50]  # 只返回最近50条记录
        })
    
    except Exception as e:
        logger.error(f"获取积分历史失败: {str(e)}")
        return jsonify({'error': '获取积分历史失败'}), 500