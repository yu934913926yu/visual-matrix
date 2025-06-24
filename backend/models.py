from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=True)
    points = db.Column(db.Integer, default=50)  # 新用户赠送50积分
    wx_openid = db.Column(db.String(100), unique=True, nullable=True)
    wx_unionid = db.Column(db.String(100), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')  # user/admin
    membership_tier_id = db.Column(db.Integer, db.ForeignKey('membership_tiers.id'), nullable=True)
    membership_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    ai_tasks = db.relationship('AITask', backref='user', lazy=True)
    project_folders = db.relationship('ProjectFolder', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class AITask(db.Model):
    __tablename__ = 'ai_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/analyzing/generating/completed/failed
    original_image_path = db.Column(db.String(200), nullable=False)
    gemini_prompt = db.Column(db.Text, nullable=True)
    final_prompt = db.Column(db.Text, nullable=True)
    error_log = db.Column(db.Text, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project_folders.id'), nullable=True)
    quantity_requested = db.Column(db.Integer, default=1)
    quantity_succeeded = db.Column(db.Integer, default=0)
    total_cost_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    generated_results = db.relationship('GeneratedResult', backref='task', lazy=True)

class GeneratedResult(db.Model):
    __tablename__ = 'generated_results'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('ai_tasks.id'), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    finalized_image_url = db.Column(db.String(200), nullable=True)
    editor_data_json = db.Column(db.Text, nullable=True)  # 存储编辑器数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectFolder(db.Model):
    __tablename__ = 'project_folders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    ai_tasks = db.relationship('AITask', backref='project_folder', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # 订单金额
    status = db.Column(db.String(20), default='pending')  # pending/paid/failed
    product_type = db.Column(db.String(20), nullable=False)  # points/membership
    product_id = db.Column(db.Integer, nullable=False)  # 关联到充值包或会员等级ID
    points_gained = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MembershipTiers(db.Model):
    __tablename__ = 'membership_tiers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 如：VIP、SVIP
    price_monthly = db.Column(db.Float, nullable=False)
    price_annually = db.Column(db.Float, nullable=False)
    points_grant = db.Column(db.Integer, default=0)  # 购买时赠送积分
    generation_discount_percent = db.Column(db.Integer, default=100)  # 折扣率，100=无折扣
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', backref='membership_tier', lazy=True)

class StyleTemplates(db.Model):
    __tablename__ = 'style_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.String(200), nullable=True)
    prompt_instruction = db.Column(db.Text, nullable=False)  # 核心提示词指令
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RechargePackages(db.Model):
    __tablename__ = 'recharge_packages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 如：30元特惠包
    cny_price = db.Column(db.Float, nullable=False)  # 人民币价格
    points_awarded = db.Column(db.Integer, nullable=False)  # 到账积分
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIChannel(db.Model):
    __tablename__ = 'api_channels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 如：OpenAI、Google
    base_url = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(200), nullable=False)  # 实际应用中需要加密
    is_active = db.Column(db.Boolean, default=True)
    is_healthy = db.Column(db.Boolean, default=True)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    latency_ms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    api_models = db.relationship('APIModel', backref='channel', lazy=True)

class APIModel(db.Model):
    __tablename__ = 'api_models'
    
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('api_channels.id'), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)  # 如：gpt-4, gemini-pro
    priority = db.Column(db.Integer, default=1)  # 优先级，数字越小优先级越高
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)