from flask import Blueprint, request, jsonify
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('register', methods=['POST'])
def register()
    用户注册
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password
        return jsonify({'error' '用户名和密码不能为空'}), 400
    
    # 检查用户是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user
        return jsonify({'error' '用户名已存在'}), 400
    
    # 创建新用户
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        points=50  # 新用户赠送50积分
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message' '注册成功',
        'user' {
            'id' user.id,
            'username' user.username,
            'points' user.points
        }
    }), 201

@auth_bp.route('login', methods=['POST'])
def login()
    用户登录
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password
        return jsonify({'error' '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password)
        return jsonify({'error' '用户名或密码错误'}), 401
    
    # 生成JWT token
    token = jwt.encode({
        'user_id' user.id,
        'exp' datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, 'your-secret-key', algorithm='HS256')
    
    return jsonify({
        'message' '登录成功',
        'token' token,
        'user' {
            'id' user.id,
            'username' user.username,
            'points' user.points,
            'role' user.role
        }
    })

@auth_bp.route('profile', methods=['GET'])
def get_profile()
    获取用户信息
    # 这里需要添加JWT验证装饰器
    token = request.headers.get('Authorization')
    if not token
        return jsonify({'error' '未提供token'}), 401
    
    try
        # 移除 Bearer  前缀
        if token.startswith('Bearer ')
            token = token[7]
        
        payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        
        if not user
            return jsonify({'error' '用户不存在'}), 404
        
        return jsonify({
            'user' {
                'id' user.id,
                'username' user.username,
                'points' user.points,
                'role' user.role,
                'membership_tier_id' user.membership_tier_id,
                'membership_expires_at' user.membership_expires_at.isoformat() if user.membership_expires_at else None
            }
        })
    
    except jwt.ExpiredSignatureError
        return jsonify({'error' 'Token已过期'}), 401
    except jwt.InvalidTokenError
        return jsonify({'error' '无效的token'}), 401