from flask import Blueprint, request, jsonify, current_app
from models import db, User, Order, RechargePackages, MembershipTiers, SystemConfig
from services.payment_service import PaymentService
from utils.auth import token_required
import logging

logger = logging.getLogger(__name__)
payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/recharge-packages', methods=['GET'])
def get_recharge_packages():
    """获取充值套餐列表"""
    packages = RechargePackages.query.filter_by(is_active=True).order_by(RechargePackages.sort_order).all()
    
    return jsonify({
        'packages': [{
            'id': p.id,
            'name': p.name,
            'cny_price': p.cny_price,
            'points_awarded': p.points_awarded,
            'description': p.description,
            'bonus_points': p.points_awarded - int(p.cny_price * 30)  # 计算赠送积分
        } for p in packages]
    })

@payment_bp.route('/membership-tiers', methods=['GET'])
def get_membership_tiers():
    """获取会员等级列表"""
    tiers = MembershipTiers.query.all()
    
    return jsonify({
        'tiers': [{
            'id': t.id,
            'name': t.name,
            'price_monthly': t.price_monthly,
            'price_annually': t.price_annually,
            'points_grant': t.points_grant,
            'generation_discount_percent': t.generation_discount_percent,
            'annual_savings': t.price_monthly * 12 - t.price_annually
        } for t in tiers]
    })

@payment_bp.route('/create-order', methods=['POST'])
@token_required
def create_order(current_user):
    """创建订单"""
    try:
        data = request.get_json()
        product_type = data.get('product_type')  # 'points' 或 'membership'
        product_id = data.get('product_id')
        payment_method = data.get('payment_method', 'alipay')  # alipay/wechat
        billing_cycle = data.get('billing_cycle', 'monthly')  # monthly/annually (仅会员)
        
        if product_type not in ['points', 'membership']:
            return jsonify({'error': '无效的产品类型'}), 400
        
        # 计算订单金额和积分
        if product_type == 'points':
            package = RechargePackages.query.get(product_id)
            if not package or not package.is_active:
                return jsonify({'error': '充值套餐不存在'}), 404
            
            amount = package.cny_price
            points_gained = package.points_awarded
            
        elif product_type == 'membership':
            tier = MembershipTiers.query.get(product_id)
            if not tier:
                return jsonify({'error': '会员等级不存在'}), 404
            
            amount = tier.price_annually if billing_cycle == 'annually' else tier.price_monthly
            points_gained = tier.points_grant
        
        # 创建订单
        order = Order(
            user_id=current_user.id,
            amount=amount,
            status='pending',
            product_type=product_type,
            product_id=product_id,
            points_gained=points_gained
        )
        
        db.session.add(order)
        db.session.commit()
        
        # 调用支付服务创建支付链接
        payment_service = PaymentService()
        payment_result = payment_service.create_payment(
            order_id=order.id,
            amount=amount,
            subject=f"视觉矩阵-{package.name if product_type == 'points' else tier.name}",
            payment_method=payment_method
        )
        
        if payment_result['success']:
            return jsonify({
                'order_id': order.id,
                'payment_url': payment_result['payment_url'],
                'qr_code': payment_result.get('qr_code'),
                'amount': amount
            })
        else:
            order.status = 'failed'
            db.session.commit()
            return jsonify({'error': '创建支付失败'}), 500
            
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}")
        return jsonify({'error': '创建订单失败'}), 500

@payment_bp.route('/payment-callback', methods=['POST'])
def payment_callback():
    """支付回调处理"""
    try:
        # 这里需要根据具体的支付提供商来处理回调
        data = request.get_json() or request.form.to_dict()
        
        payment_service = PaymentService()
        callback_result = payment_service.handle_callback(data)
        
        if callback_result['success']:
            order_id = callback_result['order_id']
            order = Order.query.get(order_id)
            
            if order and order.status == 'pending':
                # 处理支付成功逻辑
                process_successful_payment(order)
                
                return jsonify({'success': True})
        
        return jsonify({'error': '回调处理失败'}), 400
        
    except Exception as e:
        logger.error(f"支付回调处理失败: {str(e)}")
        return jsonify({'error': '回调处理失败'}), 500

@payment_bp.route('/order-status/<int:order_id>', methods=['GET'])
@token_required
def get_order_status(current_user, order_id):
    """查询订单状态"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    
    return jsonify({
        'order_id': order.id,
        'status': order.status,
        'amount': order.amount,
        'product_type': order.product_type,
        'points_gained': order.points_gained,
        'created_at': order.created_at.isoformat()
    })

def process_successful_payment(order):
    """处理支付成功的订单"""
    try:
        order.status = 'paid'
        user = order.user
        
        if order.product_type == 'points':
            # 充值积分
            user.points += order.points_gained
            logger.info(f"用户 {user.id} 充值 {order.points_gained} 积分")
            
        elif order.product_type == 'membership':
            # 开通/续费会员
            tier = MembershipTiers.query.get(order.product_id)
            user.membership_tier_id = tier.id
            
            # 计算会员到期时间
            from datetime import datetime, timedelta
            if user.membership_expires_at and user.membership_expires_at > datetime.utcnow():
                # 续费
                base_date = user.membership_expires_at
            else:
                # 新开通
                base_date = datetime.utcnow()
            
            # 这里需要根据订单中的billing_cycle来确定延长时间
            extend_days = 365 if order.amount == tier.price_annually else 30
            user.membership_expires_at = base_date + timedelta(days=extend_days)
            
            # 赠送积分
            if tier.points_grant > 0:
                user.points += tier.points_grant
            
            logger.info(f"用户 {user.id} 开通会员 {tier.name}")
        
        db.session.commit()
        
        # 可以在这里发送通知给用户
        from services.websocket_service import WebSocketService
        WebSocketService.emit_to_user(
            user.id,
            'payment_success',
            {
                'order_id': order.id,
                'type': order.product_type,
                'points_gained': order.points_gained
            }
        )
        
    except Exception as e:
        logger.error(f"处理支付成功订单失败: {str(e)}")
        raise e