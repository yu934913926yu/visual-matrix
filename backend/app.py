from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, User, AITask, GeneratedResult, SystemConfig
from config import config
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    CORS(app)
    
    # 数据库迁移
    migrate = Migrate(app, db)
    
    # 创建上传目录
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # 注册蓝图
    from routes.auth import auth_bp
    from routes.api import api_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 基础路由
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Visual Matrix API v8.0',
            'status': 'running'
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        db.create_all()
        # 初始化系统配置
        init_system_config()
    app.run(debug=True, host='0.0.0.0', port=5000)

def init_system_config():
    """初始化系统配置"""
    configs = [
        ('new_user_bonus_points', '50', '新用户注册赠送积分'),
        ('base_generation_cost', '10', '单张图片生成基础积分成本'),
        ('cny_to_points_rate', '30', '1元人民币对应积分数'),
        ('analyze_cost', '1', '图片分析消耗积分')
    ]
    
    for key, value, desc in configs:
        existing = SystemConfig.query.filter_by(config_key=key).first()
        if not existing:
            config_item = SystemConfig(
                config_key=key,
                config_value=value,
                description=desc
            )
            db.session.add(config_item)
    
    db.session.commit()