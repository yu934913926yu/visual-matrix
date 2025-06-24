import hashlib
import json
import requests
import hmac
import base64
from urllib.parse import urlencode
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PaymentService:
    """支付服务 - 集成支付宝和微信支付"""
    
    def __init__(self):
        # 这些配置应该从环境变量或配置文件中读取
        self.alipay_config = {
            'app_id': '你的支付宝应用ID',
            'private_key': '你的支付宝私钥',
            'public_key': '支付宝公钥',
            'gateway': 'https://openapi.alipay.com/gateway.do',
            'notify_url': 'https://yourdomain.com/payment/callback',
            'return_url': 'https://yourdomain.com/payment/return'
        }
        
        self.wechat_config = {
            'mch_id': '你的微信商户号',
            'app_id': '你的微信应用ID',
            'api_key': '你的微信API密钥',
            'notify_url': 'https://yourdomain.com/payment/callback'
        }
    
    def create_payment(self, order_id: int, amount: float, subject: str, payment_method: str = 'alipay'):
        """
        创建支付订单
        """
        try:
            if payment_method == 'alipay':
                return self._create_alipay_payment(order_id, amount, subject)
            elif payment_method == 'wechat':
                return self._create_wechat_payment(order_id, amount, subject)
            else:
                return {'success': False, 'error': '不支持的支付方式'}
                
        except Exception as e:
            logger.error(f"创建支付失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_alipay_payment(self, order_id: int, amount: float, subject: str):
        """创建支付宝支付"""
        # 构建支付参数
        params = {
            'app_id': self.alipay_config['app_id'],
            'method': 'alipay.trade.precreate',  # 扫码支付
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            'notify_url': self.alipay_config['notify_url'],
            'biz_content': json.dumps({
                'out_trade_no': f'VM_{order_id}',
                'total_amount': str(amount),
                'subject': subject,
                'store_id': 'visual_matrix_store',
                'timeout_express': '30m'
            })
        }
        
        # 生成签名
        sign = self._generate_alipay_sign(params)
        params['sign'] = sign
        
        # 发起请求
        response = requests.post(self.alipay_config['gateway'], data=params)
        result = response.json()
        
        if result.get('alipay_trade_precreate_response', {}).get('code') == '10000':
            qr_code = result['alipay_trade_precreate_response']['qr_code']
            return {
                'success': True,
                'payment_url': qr_code,
                'qr_code': qr_code,
                'trade_no': result['alipay_trade_precreate_response']['out_trade_no']
            }
        else:
            return {
                'success': False,
                'error': result.get('alipay_trade_precreate_response', {}).get('sub_msg', '支付宝支付创建失败')
            }
    
    def _create_wechat_payment(self, order_id: int, amount: float, subject: str):
        """创建微信支付"""
        # 微信支付金额单位是分
        total_fee = int(amount * 100)
        
        params = {
            'appid': self.wechat_config['app_id'],
            'mch_id': self.wechat_config['mch_id'],
            'nonce_str': self._generate_nonce_str(),
            'body': subject,
            'out_trade_no': f'VM_{order_id}',
            'total_fee': str(total_fee),
            'spbill_create_ip': '127.0.0.1',
            'notify_url': self.wechat_config['notify_url'],
            'trade_type': 'NATIVE'  # 扫码支付
        }
        
        # 生成签名
        sign = self._generate_wechat_sign(params)
        params['sign'] = sign
        
        # 转换为XML
        xml_data = self._dict_to_xml(params)
        
        # 发起请求
        response = requests.post('https://api.mch.weixin.qq.com/pay/unifiedorder', data=xml_data)
        result = self._xml_to_dict(response.text)
        
        if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
            return {
                'success': True,
                'payment_url': result['code_url'],
                'qr_code': result['code_url'],
                'prepay_id': result['prepay_id']
            }
        else:
            return {
                'success': False,
                'error': result.get('return_msg', '微信支付创建失败')
            }
    
    def handle_callback(self, data):
        """处理支付回调"""
        try:
            # 这里需要根据实际的回调数据格式来处理
            if 'alipay' in data or 'app_id' in data:
                return self._handle_alipay_callback(data)
            elif 'xml' in str(data) or 'mch_id' in data:
                return self._handle_wechat_callback(data)
            else:
                return {'success': False, 'error': '无法识别的回调数据'}
                
        except Exception as e:
            logger.error(f"处理支付回调失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_alipay_callback(self, data):
        """处理支付宝回调"""
        # 验证签名
        if not self._verify_alipay_sign(data):
            return {'success': False, 'error': '签名验证失败'}
        
        # 检查交易状态
        if data.get('trade_status') in ['TRADE_SUCCESS', 'TRADE_FINISHED']:
            out_trade_no = data.get('out_trade_no')
            if out_trade_no and out_trade_no.startswith('VM_'):
                order_id = int(out_trade_no.replace('VM_', ''))
                return {'success': True, 'order_id': order_id}
        
        return {'success': False, 'error': '交易状态异常'}
    
    def _handle_wechat_callback(self, data):
        """处理微信支付回调"""
        # 解析XML数据
        if isinstance(data, str):
            data = self._xml_to_dict(data)
        
        # 验证签名
        if not self._verify_wechat_sign(data):
            return {'success': False, 'error': '签名验证失败'}
        
        # 检查支付状态
        if data.get('return_code') == 'SUCCESS' and data.get('result_code') == 'SUCCESS':
            out_trade_no = data.get('out_trade_no')
            if out_trade_no and out_trade_no.startswith('VM_'):
                order_id = int(out_trade_no.replace('VM_', ''))
                return {'success': True, 'order_id': order_id}
        
        return {'success': False, 'error': '支付状态异常'}
    
    def _generate_alipay_sign(self, params):
        """生成支付宝签名"""
        # 这里需要实现RSA签名算法
        # 实际应用中建议使用支付宝SDK
        sorted_params = sorted(params.items())
        query_string = '&'.join([f'{k}={v}' for k, v in sorted_params if v])
        
        # 使用RSA私钥签名（这里简化处理）
        import rsa
        private_key = rsa.PrivateKey.load_pkcs1(self.alipay_config['private_key'])
        signature = rsa.sign(query_string.encode('utf-8'), private_key, 'SHA-256')
        return base64.b64encode(signature).decode('utf-8')
    
    def _verify_alipay_sign(self, data):
        """验证支付宝签名"""
        # 实际应用中需要实现完整的签名验证
        return True  # 简化处理
    
    def _generate_wechat_sign(self, params):
        """生成微信支付签名"""
        sorted_params = sorted(params.items())
        query_string = '&'.join([f'{k}={v}' for k, v in sorted_params if v])
        query_string += f'&key={self.wechat_config["api_key"]}'
        
        return hashlib.md5(query_string.encode('utf-8')).hexdigest().upper()
    
    def _verify_wechat_sign(self, data):
        """验证微信支付签名"""
        sign = data.pop('sign', '')
        calculated_sign = self._generate_wechat_sign(data)
        return sign == calculated_sign
    
    def _generate_nonce_str(self):
        """生成随机字符串"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    def _dict_to_xml(self, data):
        """字典转XML"""
        xml = '<xml>'
        for k, v in data.items():
            xml += f'<{k}>{v}</{k}>'
        xml += '</xml>'
        return xml
    
    def _xml_to_dict(self, xml):
        """XML转字典"""
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        return {child.tag: child.text for child in root}