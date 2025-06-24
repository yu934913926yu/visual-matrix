#!/usr/bin/env python
from app import create_app
from models import db, SystemConfig, StyleTemplates, RechargePackages, MembershipTiers, APIChannel, APIModel
from datetime import datetime

def init_database():
    """初始化数据库和基础数据"""
    app = create_app('development')
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成")
        
        # 初始化系统配置
        init_system_config()
        
        # 初始化风格模板
        init_style_templates()
        
        # 初始化充值包
        init_recharge_packages()
        
        # 初始化会员等级
        init_membership_tiers()
        
        # 初始化API通道
        init_api_channels()
        
        print("数据库初始化完成！")

def init_system_config():
    """初始化系统配置"""
    configs = [
        ('new_user_bonus_points', '50', '新用户注册赠送积分'),
        ('base_generation_cost', '10', '单张图片生成基础积分成本'),
        ('cny_to_points_rate', '30', '1元人民币对应积分数'),
        ('analyze_cost', '1', '图片分析消耗积分'),
        ('max_upload_size', '10485760', '最大上传文件大小(字节)'),
        ('supported_formats', 'jpg,jpeg,png,gif,webp', '支持的图片格式'),
        ('max_generation_quantity', '4', '单次最大生成数量'),
        ('webhook_secret', 'your-webhook-secret', '支付回调密钥')
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
    print("系统配置初始化完成")

def init_style_templates():
    """初始化风格模板"""
    templates = [
        {
            'name': '模特佩戴展示',
            'description': '专业模特佩戴商品的高端展示',
            'thumbnail_url': '/static/styles/model_display.jpg',
            'prompt_instruction': '请设计一个专业的模特展示场景，模特应该优雅地佩戴或使用商品，背景简洁高端，光线柔和自然，突出商品的质感和品质。场景应该具有时尚感和专业性。',
            'sort_order': 1
        },
        {
            'name': '自然场景融合',
            'description': '将商品与自然元素完美结合',
            'thumbnail_url': '/static/styles/natural_scene.jpg',
            'prompt_instruction': '创建一个自然和谐的场景，将商品巧妙地融入自然环境中，如森林、海滩、花园等。光线应该是自然的阳光，营造清新、健康、环保的感觉。',
            'sort_order': 2
        },
        {
            'name': '简约商务风格',
            'description': '现代简约的商务专业展示',
            'thumbnail_url': '/static/styles/business_style.jpg',
            'prompt_instruction': '设计一个现代简约的商务场景，背景应该是干净的办公环境或几何图形，用专业的打光突出商品，整体风格简洁、现代、专业。',
            'sort_order': 3
        },
        {
            'name': '奢华典雅风格',
            'description': '高端奢华的精美展示',
            'thumbnail_url': '/static/styles/luxury_style.jpg',
            'prompt_instruction': '创造一个奢华典雅的场景，使用高端材质如大理石、丝绸、金属等作为背景元素，打光应该营造出精致、昂贵、典雅的氛围。',
            'sort_order': 4
        },
        {
            'name': '生活场景应用',
            'description': '真实生活场景中的商品应用',
            'thumbnail_url': '/static/styles/lifestyle_scene.jpg',
            'prompt_instruction': '展示商品在真实生活场景中的使用情况，如家庭、办公室、户外活动等，让消费者能够想象自己使用该商品的场景。',
            'sort_order': 5
        },
        {
            'name': '艺术创意风格',
            'description': '富有创意的艺术化展示',
            'thumbnail_url': '/static/styles/artistic_style.jpg',
            'prompt_instruction': '运用艺术化的手法展示商品，可以包含抽象元素、创意构图、特殊光影效果等，让商品展示更具视觉冲击力和艺术感。',
            'sort_order': 6
        }
    ]
    
    for template_data in templates:
        existing = StyleTemplates.query.filter_by(name=template_data['name']).first()
        if not existing:
            template = StyleTemplates(**template_data)
            db.session.add(template)
    
    db.session.commit()
    print("风格模板初始化完成")

def init_recharge_packages():
    """初始化充值包"""
    packages = [
        {
            'name': '体验包',
            'cny_price': 10.0,
            'points_awarded': 300,
            'description': '新手体验，超值优惠',
            'sort_order': 1
        },
        {
            'name': '标准包',
            'cny_price': 30.0,
            'points_awarded': 1000,
            'description': '最受欢迎，性价比之选',
            'sort_order': 2
        },
        {
            'name': '专业包',
            'cny_price': 68.0,
            'points_awarded': 2500,
            'description': '专业用户推荐，超值赠送',
            'sort_order': 3
        },
        {
            'name': '旗舰包',
            'cny_price': 128.0,
            'points_awarded': 5000,
            'description': '企业级用量，尊享特权',
            'sort_order': 4
        }
    ]
    
    for package_data in packages:
        existing = RechargePackages.query.filter_by(name=package_data['name']).first()
        if not existing:
            package = RechargePackages(**package_data)
            db.session.add(package)
    
    db.session.commit()
    print("充值包初始化完成")

def init_membership_tiers():
    """初始化会员等级"""
    tiers = [
        {
            'name': 'VIP会员',
            'price_monthly': 29.0,
            'price_annually': 299.0,
            'points_grant': 500,
            'generation_discount_percent': 60  # 6折
        },
        {
            'name': 'SVIP会员',
            'price_monthly': 59.0,
            'price_annually': 599.0,
            'points_grant': 1200,
            'generation_discount_percent': 50  # 5折
        }
    ]
    
    for tier_data in tiers:
        existing = MembershipTiers.query.filter_by(name=tier_data['name']).first()
        if not existing:
            tier = MembershipTiers(**tier_data)
            db.session.add(tier)
    
    db.session.commit()
    print("会员等级初始化完成")

def init_api_channels():
    """初始化API通道（示例配置）"""
    channels = [
        {
            'name': 'OpenAI官方',
            'base_url': 'https://api.openai.com',
            'api_key': 'your-openai-api-key',  # 需要替换为实际的API密钥
            'is_active': False,  # 默认不激活，需要手动配置
            'models': [
                {'model_name': 'gpt-4-vision-preview', 'priority': 1},
                {'model_name': 'dall-e-3', 'priority': 2}
            ]
        },
        {
            'name': 'Google Gemini',
            'base_url': 'https://generativelanguage.googleapis.com',
            'api_key': 'your-gemini-api-key',  # 需要替换为实际的API密钥
            'is_active': False,
            'models': [
                {'model_name': 'gemini-pro-vision', 'priority': 1}
            ]
        }
    ]
    
    for channel_data in channels:
        existing = APIChannel.query.filter_by(name=channel_data['name']).first()
        if not existing:
            models = channel_data.pop('models')
            channel = APIChannel(**channel_data)
            db.session.add(channel)
            db.session.flush()  # 获取channel.id
            
            for model_data in models:
                model = APIModel(
                    channel_id=channel.id,
                    **model_data
                )
                db.session.add(model)
    
    db.session.commit()
    print("API通道初始化完成")

if __name__ == '__main__':
    init_database()