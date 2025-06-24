from flask import Blueprint, request, jsonify, current_app
from models import (db, User, AITask, GeneratedResult, Order, SystemConfig, 
                   StyleTemplates, RechargePackages, MembershipTiers, 
                   APIChannel, APIModel)
from utils.auth import admin_required
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

# ============ 仪表盘统计 ============
@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats(current_user):
    """获取管理后台仪表盘统计数据"""
    try:
        # 基础统计
        total_users = User.query.count()
        total_tasks = AITask.query.count()
        total_orders = Order.query.count()
        
        # 今日统计
        today = datetime.now().date()
        today_users = User.query.filter(func.date(User.created_at) == today).count()
        today_tasks = AITask.query.filter(func.date(AITask.created_at) == today).count()
        today_revenue = db.session.query(func.sum(Order.amount)).filter(
            func.date(Order.created_at) == today,
            Order.status == 'paid'
        ).scalar() or 0
        
        # 近7天统计
        week_ago = datetime.now() - timedelta(days=7)
        week_tasks = AITask.query.filter(AITask.created_at >= week_ago).count()
        week_revenue = db.session.query(func.sum(Order.amount)).filter(
            Order.created_at >= week_ago,
            Order.status == 'paid'
        ).scalar() or 0
        
        # 任务状态统计
        task_stats = db.session.query(
            AITask.status,
            func.count(AITask.id)
        ).group_by(AITask.status).all()
        
        # API健康状态
        healthy_channels = APIChannel.query.filter_by(is_healthy=True, is_active=True).count()
        total_channels = APIChannel.query.filter_by(is_active=True).count()
        
        return jsonify({
            'basic_stats': {
                'total_users': total_users,
                'total_tasks': total_tasks,
                'total_orders': total_orders,
                'total_revenue': week_revenue
            },
            'today_stats': {
                'new_users': today_users,
                'new_tasks': today_tasks,
                'revenue': today_revenue
            },
            'week_stats': {
                'tasks': week_tasks,
                'revenue': week_revenue
            },
            'task_stats': {status: count for status, count in task_stats},
            'api_health': {
                'healthy_channels': healthy_channels,
                'total_channels': total_channels,
                'health_rate': (healthy_channels / total_channels * 100) if total_channels > 0 else 0
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({'error': '获取统计数据失败'}), 500

# ============ 用户管理 ============
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """获取用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(User.username.contains(search))
        
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = []
        for user in pagination.items:
            users.append({
                'id': user.id,
                'username': user.username,
                'points': user.points,
                'role': user.role,
                'membership_tier_id': user.membership_tier_id,
                'membership_expires_at': user.membership_expires_at.isoformat() if user.membership_expires_at else None,
                'created_at': user.created_at.isoformat(),
                'task_count': len(user.ai_tasks),
                'order_count': len(user.orders)
            })
        
        return jsonify({
            'users': users,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({'error': '获取用户列表失败'}), 500

@admin_bp.route('/users/<int:user_id>/points', methods=['POST'])
@admin_required
def adjust_user_points(current_user, user_id):
    """调整用户积分"""
    try:
        data = request.get_json()
        adjustment = data.get('adjustment', 0)  # 正数为增加，负数为扣除
        reason = data.get('reason', '管理员调整')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        old_points = user.points
        user.points = max(0, user.points + adjustment)  # 确保积分不为负
        
        db.session.commit()
        
        logger.info(f"管理员 {current_user.username} 调整用户 {user.username} 积分: {old_points} -> {user.points} (原因: {reason})")
        
        return jsonify({
            'message': '积分调整成功',
            'old_points': old_points,
            'new_points': user.points,
            'adjustment': adjustment
        })
        
    except Exception as e:
        logger.error(f"调整用户积分失败: {str(e)}")
        return jsonify({'error': '调整积分失败'}), 500

@admin_bp.route('/users/<int:user_id>/membership', methods=['POST'])
@admin_required
def set_user_membership(current_user, user_id):
    """设置用户会员"""
    try:
        data = request.get_json()
        tier_id = data.get('tier_id')
        expires_at = data.get('expires_at')  # ISO格式时间字符串
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if tier_id:
            tier = MembershipTiers.query.get(tier_id)
            if not tier:
                return jsonify({'error': '会员等级不存在'}), 404
            user.membership_tier_id = tier_id
        else:
            user.membership_tier_id = None
        
        if expires_at:
            user.membership_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        else:
            user.membership_expires_at = None
        
        db.session.commit()
        
        logger.info(f"管理员 {current_user.username} 设置用户 {user.username} 会员状态")
        
        return jsonify({'message': '会员状态设置成功'})
        
    except Exception as e:
        logger.error(f"设置用户会员失败: {str(e)}")
        return jsonify({'error': '设置会员状态失败'}), 500

# ============ 系统配置管理 ============
@admin_bp.route('/system-config', methods=['GET'])
@admin_required
def get_system_config(current_user):
    """获取系统配置"""
    try:
        configs = SystemConfig.query.all()
        config_dict = {}
        
        for config in configs:
            config_dict[config.config_key] = {
                'value': config.config_value,
                'description': config.description,
                'updated_at': config.updated_at.isoformat()
            }
        
        return jsonify({'configs': config_dict})
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        return jsonify({'error': '获取系统配置失败'}), 500

@admin_bp.route('/system-config', methods=['POST'])
@admin_required
def update_system_config(current_user):
    """更新系统配置"""
    try:
        data = request.get_json()
        updates = data.get('configs', {})
        
        for key, value in updates.items():
            config = SystemConfig.query.filter_by(config_key=key).first()
            if config:
                config.config_value = str(value)
                config.updated_at = datetime.utcnow()
            else:
                new_config = SystemConfig(
                    config_key=key,
                    config_value=str(value),
                    description=f'由管理员 {current_user.username} 创建'
                )
                db.session.add(new_config)
        
        db.session.commit()
        
        logger.info(f"管理员 {current_user.username} 更新了系统配置: {list(updates.keys())}")
        
        return jsonify({'message': '系统配置更新成功'})
        
    except Exception as e:
        logger.error(f"更新系统配置失败: {str(e)}")
        return jsonify({'error': '更新系统配置失败'}), 500

# ============ 风格模板管理 ============
@admin_bp.route('/style-templates', methods=['GET'])
@admin_required
def get_style_templates_admin(current_user):
    """获取风格模板列表（管理员）"""
    try:
        templates = StyleTemplates.query.order_by(StyleTemplates.sort_order).all()
        
        return jsonify({
            'templates': [{
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'thumbnail_url': t.thumbnail_url,
                'prompt_instruction': t.prompt_instruction,
                'is_active': t.is_active,
                'sort_order': t.sort_order,
                'created_at': t.created_at.isoformat()
            } for t in templates]
        })
        
    except Exception as e:
        logger.error(f"获取风格模板失败: {str(e)}")
        return jsonify({'error': '获取风格模板失败'}), 500

@admin_bp.route('/style-templates', methods=['POST'])
@admin_required
def create_style_template(current_user):
    """创建风格模板"""
    try:
        data = request.get_json()
        
        template = StyleTemplates(
            name=data.get('name'),
            description=data.get('description'),
            thumbnail_url=data.get('thumbnail_url'),
            prompt_instruction=data.get('prompt_instruction'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(template)
        db.session.commit()
        
        logger.info(f"管理员 {current_user.username} 创建风格模板: {template.name}")
        
        return jsonify({
            'message': '风格模板创建成功',
            'template_id': template.id
        })
        
    except Exception as e:
        logger.error(f"创建风格模板失败: {str(e)}")
        return jsonify({'error': '创建风格模板失败'}), 500

@admin_bp.route('/style-templates/<int:template_id>', methods=['PUT'])
@admin_required
def update_style_template(current_user, template_id):
    """更新风格模板"""
    try:
        template = StyleTemplates.query.get(template_id)
        if not template:
            return jsonify({'error': '风格模板不存在'}), 404
        
        data = request.get_json()
        
        template.name = data.get('name', template.name)
        template.description = data.get('description', template.description)
        template.thumbnail_url = data.get('thumbnail_url', template.thumbnail_url)
        template.prompt_instruction = data.get('prompt_instruction', template.prompt_instruction)
        template.is_active = data.get('is_active', template.is_active)
        template.sort_order = data.get('sort_order', template.sort_order)
        
        db.session.commit()
        
        logger.info(f"管理员 {current_user.username} 更新风格模板: {template.name}")
        
        return jsonify({'message': '风格模板更新成功'})
        
    except Exception as e:
        logger.error(f"更新风格模板失败: {str(e)}")
        return jsonify({'error': '更新风格模板失败'}), 500

# ============ 充值包管理 ============
@admin_bp.route('/recharge-packages', methods=['GET'])
@admin_required
def get_recharge_packages_admin(current_user):
    """获取充值包列表（管理员）"""
    try:
        packages = RechargePackages.query.order_by(RechargePackages.sort_order).all()
        
        return jsonify({
            'packages': [{
                'id': p.id,
                'name': p.name,
                'cny_price': p.cny_price,
                'points_awarded': p.points_awarded,
                'description': p.description,
                'is_active': p.is_active,
                'sort_order': p.sort_order,
                'created_at': p.created_at.isoformat()
            } for p in packages]
        })
        
    except Exception as e:
        logger.error(f"获取充值包失败: {str(e)}")
        return jsonify({'error': '获取充值包失败'}), 500

@admin_bp.route('/recharge-packages', methods=['POST'])
@admin_required
def create_recharge_package(current_user):
    """创建充值包"""
    try:
        data = request.get_json()
        
        package = RechargePackages(
            name=data.get('name'),
            cny_price=data.get('cny_price'),
            points_awarded=data.get('points_awarded'),
            description=data.get('description'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(package)
        db.session.commit()
        
        logger.info(f"管理员 {current_user.username} 创建充值包: {package.name}")
        
        return jsonify({
            'message': '充值包创建成功',
            'package_id': package.id
        })
        
    except Exception as e:
        logger.error(f"创建充值包失败: {str(e)}")
        return jsonify({'error': '创建充值包失败'}), 500

# ============ API通道管理 ============
@admin_bp.route('/api-channels', methods=['GET'])
@admin_required
def get_api_channels(current_user):
    """获取API通道列表"""
    try:
        channels = APIChannel.query.all()
        
        channel_list = []
        for channel in channels:
            channel_data = {
                'id': channel.id,
                'name': channel.name,
                'base_url': channel.base_url,
                'is_active': channel.is_active,
                'is_healthy': channel.is_healthy,
                'last_checked_at': channel.last_checked_at.isoformat() if channel.last_checked_at else None,
                'latency_ms': channel.latency_ms,
                'created_at': channel.created_at.isoformat(),
                'models': []
            }
            
            for model in channel.api_models:
                channel_data['models'].append({
                    'id': model.id,
                    'model_name': model.model_name,
                    'priority': model.priority,
                    'is_active': model.is_active,
                    'is_available': model.is_available
                })
            
            channel_list.append(channel_data)
        
        return jsonify({'channels': channel_list})
        
    except Exception as e:
        logger.error(f"获取API通道失败: {str(e)}")
        return jsonify({'error': '获取API通道失败'}), 500

@admin_bp.route('/api-channels', methods=['POST'])
@admin_required
def create_api_channel(current_user):
    """创建API通道"""
    try:
        data = request.get_json()
        
        channel = APIChannel(
            name=data.get('name'),
            base_url=data.get('base_url'),
            api_key=data.get('api_key'),  # 实际应用中需要加密
            is_active=data.get('is_active', True),
            is_healthy=True
        )
        
        db.session.add(channel)
        db.session.commit()
        
        logger.info(f"管理员 {current_user.username} 创建API通道: {channel.name}")
        
        return jsonify({
            'message': 'API通道创建成功',
            'channel_id': channel.id
        })
        
    except Exception as e:
        logger.error(f"创建API通道失败: {str(e)}")
        return jsonify({'error': '创建API通道失败'}), 500

@admin_bp.route('/api-channels/<int:channel_id>/test', methods=['POST'])
@admin_required
def test_api_channel(current_user, channel_id):
    """测试API通道"""
    try:
        channel = APIChannel.query.get(channel_id)
        if not channel:
            return jsonify({'error': 'API通道不存在'}), 404
        
        # 这里可以实现实际的API测试逻辑
        # 例如发送一个测试请求到该通道
        
        import time
        import random
        
        # 模拟测试
        start_time = time.time()
        # 这里应该有实际的API调用
        time.sleep(random.uniform(0.1, 1.0))  # 模拟网络延迟
        end_time = time.time()
        
        latency = int((end_time - start_time) * 1000)
        is_healthy = latency < 5000  # 5秒以内认为健康
        
        # 更新通道状态
        channel.is_healthy = is_healthy
        channel.latency_ms = latency
        channel.last_checked_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'channel_id': channel_id,
            'is_healthy': is_healthy,
            'latency_ms': latency,
            'message': '测试完成'
        })
        
    except Exception as e:
        logger.error(f"测试API通道失败: {str(e)}")
        return jsonify({'error': '测试API通道失败'}), 500

# ============ 任务管理 ============
@admin_bp.route('/tasks', methods=['GET'])
@admin_required
def get_tasks_admin(current_user):
    """获取任务列表（管理员）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        user_id = request.args.get('user_id', type=int)
        
        query = AITask.query
        
        if status:
            query = query.filter(AITask.status == status)
        if user_id:
            query = query.filter(AITask.user_id == user_id)
        
        pagination = query.order_by(desc(AITask.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        tasks = []
        for task in pagination.items:
            tasks.append({
                'id': task.id,
                'user_id': task.user_id,
                'username': task.user.username,
                'status': task.status,
                'quantity_requested': task.quantity_requested,
                'quantity_succeeded': task.quantity_succeeded,
                'total_cost_points': task.total_cost_points,
                'created_at': task.created_at.isoformat(),
                'error_log': task.error_log,
                'generated_count': len(task.generated_results)
            })
        
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

@admin_bp.route('/tasks/<int:task_id>/retry', methods=['POST'])
@admin_required
def retry_task(current_user, task_id):
    """重试失败的任务"""
    try:
        task = AITask.query.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        if task.status not in ['failed']:
            return jsonify({'error': '只能重试失败的任务'}), 400
        
        # 重置任务状态
        task.status = 'pending'
        task.error_log = None
        db.session.commit()
        
        # 重新提交任务到队列
        if task.gemini_prompt:
            # 如果已经有分析结果，直接生成
            from tasks.ai_tasks import generate_task
            generate_task.delay(task_id)
        else:
            # 重新分析
            from tasks.ai_tasks import analyze_task
            analyze_task.delay(task_id, task.original_image_path)
        
        logger.info(f"管理员 {current_user.username} 重试任务 {task_id}")
        
        return jsonify({'message': '任务重试已提交'})
        
    except Exception as e:
        logger.error(f"重试任务失败: {str(e)}")
        return jsonify({'error': '重试任务失败'}), 500