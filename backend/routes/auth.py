from flask import Blueprint, request, jsonify, redirect, current_app
from models import db, User, SystemConfig
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import requests
import json
import logging
from utils.auth import token_required
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # 检查用户是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': '用户名已存在'}), 400
    
    # 获取新用户赠送积分配置
    bonus_config = SystemConfig.query.filter_by(config_key='new_user_bonus_points').first()
    bonus_points = int(bonus_config.config_value) if bonus_config else 50
    
    # 创建新用户
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        points=bonus_points
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '注册成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'points': user.points
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 生成JWT token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, 'your-secret-key', algorithm='HS256')
    
    return jsonify({
        'message': '登录成功',
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'points': user.points,
            'role': user.role,
            'membership_tier_id': user.membership_tier_id,
            'membership_expires_at': user.membership_expires_at.isoformat() if user.membership_expires_at else None
        }
    })

@auth_bp.route('/wechat/login', methods=['GET'])
def wechat_login():
    """微信登录 - 生成微信授权URL"""
    # 生成state参数用于防止CSRF攻击
    import uuid
    state = str(uuid.uuid4())
    
    # 可以将state存储在session或redis中
    # session['wx_state'] = state
    
    # 构建微信授权URL
    auth_url = f"https://open.weixin.qq.com/connect/oauth2/authorize"
    params = {
        'appid': current_app.config.get('WECHAT_APP_ID'),
        'redirect_uri': current_app.config.get('WECHAT_REDIRECT_URI'),
        'response_type': 'code',
        'scope': 'snsapi_userinfo',
        'state': state
    }
    
    full_url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}#wechat_redirect"
    
    return jsonify({
        'wechat_auth_url': full_url,
        'state': state
    })

@auth_bp.route('/wechat/callback', methods=['GET'])
def wechat_callback():
    """微信OAuth回调处理"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return jsonify({'error': '微信授权失败'}), 400
    
    try:
        # 1. 使用code换取access_token
        token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
        token_params = {
            'appid': current_app.config.get('WECHAT_APP_ID'),
            'secret': current_app.config.get('WECHAT_APP_SECRET'),
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.get(token_url, params=token_params)
        token_data = token_response.json()
        
        if 'errcode' in token_data:
            logger.error(f"微信获取access_token失败: {token_data}")
            return jsonify({'error': '获取微信授权失败'}), 400
        
        access_token = token_data['access_token']
        openid = token_data['openid']
        unionid = token_data.get('unionid')
        
        # 2. 获取用户信息
        userinfo_url = 'https://api.weixin.qq.com/sns/userinfo'
        userinfo_params = {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN'
        }
        
        userinfo_response = requests.get(userinfo_url, params=userinfo_params)
        userinfo_data = userinfo_response.json()
        
        if 'errcode' in userinfo_data:
            logger.error(f"获取微信用户信息失败: {userinfo_data}")
            return jsonify({'error': '获取用户信息失败'}), 400
        
        # 3. 创建或更新用户
        user = User.query.filter_by(wx_openid=openid).first()
        
        if not user:
            # 新用户
            bonus_config = SystemConfig.query.filter_by(config_key='new_user_bonus_points').first()
            bonus_points = int(bonus_config.config_value) if bonus_config else 50
            
            user = User(
                username=f"wx_{userinfo_data['nickname']}_{openid[-6:]}",  # 生成唯一用户名
                wx_openid=openid,
                wx_unionid=unionid,
                points=bonus_points
            )
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"新微信用户注册: {user.username}")
        else:
            # 更新用户信息
            if unionid and not user.wx_unionid:
                user.wx_unionid = unionid
                db.session.commit()
        
        # 4. 生成JWT token
        secret_key = current_app.config.get('JWT_SECRET_KEY', current_app.config['SECRET_KEY'])
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', datetime.timedelta(days=7))
        }, secret_key, algorithm='HS256')
        
        # 5. 重定向到前端，带上token
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/login-success?token={token}")
        
    except Exception as e:
        logger.error(f"微信登录处理失败: {str(e)}")
        return jsonify({'error': '微信登录失败'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取用户信息"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'points': current_user.points,
            'role': current_user.role,
            'membership_tier_id': current_user.membership_tier_id,
            'membership_expires_at': current_user.membership_expires_at.isoformat() if current_user.membership_expires_at else None,
            'membership_tier': {
                'name': current_user.membership_tier.name,
                'discount': current_user.membership_tier.generation_discount_percent
            } if current_user.membership_tier else None
        }
    })

@auth_bp.route('/update-profile', methods=['POST'])
@token_required
def update_profile(current_user):
    """更新用户资料"""
    data = request.get_json()
    
    # 只允许更新特定字段
    if 'username' in data:
        # 检查新用户名是否已存在
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != current_user.id:
            return jsonify({'error': '用户名已存在'}), 400
        current_user.username = data['username']
    
    db.session.commit()
    
    return jsonify({
        'message': '资料更新成功',
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'points': current_user.points
        }
    })