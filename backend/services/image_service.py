from PIL import Image, ImageDraw, ImageFont
import requests
import io
import json
import os
import uuid
import logging
from typing import Dict, Any, Optional
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class ImageService:
    """图片处理服务 - 负责图片的后期处理和合成"""
    
    def __init__(self):
        self.upload_folder = 'uploads'
        self.processed_folder = 'processed'
        
        # 确保目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.processed_folder, exist_ok=True)
    
    def apply_editor_data(self, base_image_url: str, editor_data: Dict[str, Any]) -> str:
        """
        根据编辑器数据在基础图片上添加文字、LOGO等元素
        """
        try:
            # 下载基础图片
            base_image = self._download_image(base_image_url)
            
            # 解析编辑器数据并应用到图片上
            final_image = self._apply_fabric_data(base_image, editor_data)
            
            # 保存最终图片
            final_url = self._save_processed_image(final_image)
            
            return final_url
        
        except Exception as e:
            logger.error(f"应用编辑数据失败: {str(e)}")
            raise e
    
    def _download_image(self, image_url: str) -> Image.Image:
        """下载图片并转换为PIL Image对象"""
        try:
            if image_url.startswith('http'):
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                image_data = io.BytesIO(response.content)
            else:
                # 本地文件路径
                image_data = image_url
            
            image = Image.open(image_data)
            
            # 确保图片是RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
        
        except Exception as e:
            logger.error(f"下载图片失败: {str(e)}")
            raise e
    
    def _apply_fabric_data(self, base_image: Image.Image, editor_data: Dict[str, Any]) -> Image.Image:
        """
        根据Fabric.js编辑器数据在图片上添加元素
        """
        try:
            # 创建一个可编辑的图片副本
            result_image = base_image.copy()
            draw = ImageDraw.Draw(result_image)
            
            # 获取画布对象列表
            objects = editor_data.get('objects', [])
            
            for obj in objects:
                obj_type = obj.get('type', '')
                
                if obj_type == 'textbox' or obj_type == 'text':
                    self._add_text_to_image(draw, result_image, obj)
                elif obj_type == 'image':
                    self._add_image_to_image(result_image, obj)
                elif obj_type == 'rect':
                    self._add_rectangle_to_image(draw, obj)
                elif obj_type == 'circle':
                    self._add_circle_to_image(draw, obj)
            
            return result_image
        
        except Exception as e:
            logger.error(f"应用Fabric数据失败: {str(e)}")
            raise e
    
    def _add_text_to_image(self, draw: ImageDraw.Draw, image: Image.Image, text_obj: Dict[str, Any]):
        """在图片上添加文字"""
        try:
            text = text_obj.get('text', '')
            left = int(text_obj.get('left', 0))
            top = int(text_obj.get('top', 0))
            font_size = int(text_obj.get('fontSize', 20))
            fill_color = text_obj.get('fill', '#000000')
            font_family = text_obj.get('fontFamily', 'Arial')
            
            # 转换颜色格式
            if fill_color.startswith('#'):
                fill_color = tuple(int(fill_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 尝试加载字体
            try:
                # 在实际部署时，需要确保系统中有这些字体文件
                font_path = self._get_font_path(font_family)
                font = ImageFont.truetype(font_path, font_size)
            except:
                # 如果加载字体失败，使用默认字体
                font = ImageFont.load_default()
            
            # 处理多行文本
            lines = text.split('\n')
            y_offset = 0
            
            for line in lines:
                draw.text((left, top + y_offset), line, font=font, fill=fill_color)
                # 计算行高
                bbox = font.getbbox(line)
                line_height = bbox[3] - bbox[1]
                y_offset += line_height + 5  # 5像素行间距
        
        except Exception as e:
            logger.error(f"添加文字失败: {str(e)}")
    
    def _add_image_to_image(self, base_image: Image.Image, image_obj: Dict[str, Any]):
        """在基础图片上叠加另一张图片（如LOGO）"""
        try:
            image_url = image_obj.get('src', '')
            left = int(image_obj.get('left', 0))
            top = int(image_obj.get('top', 0))
            width = int(image_obj.get('width', 100))
            height = int(image_obj.get('height', 100))
            opacity = float(image_obj.get('opacity', 1.0))
            
            if not image_url:
                return
            
            # 下载并处理叠加图片
            overlay_image = self._download_image(image_url)
            
            # 调整大小
            overlay_image = overlay_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # 处理透明度
            if opacity < 1.0:
                # 创建带透明度的图片
                overlay_rgba = overlay_image.convert('RGBA')
                alpha = overlay_rgba.split()[-1]
                alpha = alpha.point(lambda p: int(p * opacity))
                overlay_rgba.putalpha(alpha)
                overlay_image = overlay_rgba
            
            # 粘贴到基础图片上
            if overlay_image.mode == 'RGBA':
                base_image.paste(overlay_image, (left, top), overlay_image)
            else:
                base_image.paste(overlay_image, (left, top))
        
        except Exception as e:
            logger.error(f"添加图片失败: {str(e)}")
    
    def _add_rectangle_to_image(self, draw: ImageDraw.Draw, rect_obj: Dict[str, Any]):
        """在图片上添加矩形"""
        try:
            left = int(rect_obj.get('left', 0))
            top = int(rect_obj.get('top', 0))
            width = int(rect_obj.get('width', 100))
            height = int(rect_obj.get('height', 100))
            fill_color = rect_obj.get('fill', '#000000')
            stroke_color = rect_obj.get('stroke', None)
            stroke_width = int(rect_obj.get('strokeWidth', 1))
            
            # 转换颜色
            if fill_color and fill_color.startswith('#'):
                fill_color = tuple(int(fill_color[i:i+2], 16) for i in (1, 3, 5))
            
            if stroke_color and stroke_color.startswith('#'):
                stroke_color = tuple(int(stroke_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 绘制矩形
            bbox = [left, top, left + width, top + height]
            draw.rectangle(bbox, fill=fill_color, outline=stroke_color, width=stroke_width)
        
        except Exception as e:
            logger.error(f"添加矩形失败: {str(e)}")
    
    def _add_circle_to_image(self, draw: ImageDraw.Draw, circle_obj: Dict[str, Any]):
        """在图片上添加圆形"""
        try:
            left = int(circle_obj.get('left', 0))
            top = int(circle_obj.get('top', 0))
            radius = int(circle_obj.get('radius', 50))
            fill_color = circle_obj.get('fill', '#000000')
            stroke_color = circle_obj.get('stroke', None)
            stroke_width = int(circle_obj.get('strokeWidth', 1))
            
            # 转换颜色
            if fill_color and fill_color.startswith('#'):
                fill_color = tuple(int(fill_color[i:i+2], 16) for i in (1, 3, 5))
            
            if stroke_color and stroke_color.startswith('#'):
                stroke_color = tuple(int(stroke_color[i:i+2], 16) for i in (1, 3, 5))
            
            # 绘制圆形
            bbox = [left - radius, top - radius, left + radius, top + radius]
            draw.ellipse(bbox, fill=fill_color, outline=stroke_color, width=stroke_width)
        
        except Exception as e:
            logger.error(f"添加圆形失败: {str(e)}")
    
    def _get_font_path(self, font_family: str) -> str:
        """获取字体文件路径"""
        # 字体映射表
        font_mapping = {
            'Arial': '/System/Library/Fonts/Arial.ttf',
            'Times New Roman': '/System/Library/Fonts/Times New Roman.ttf',
            'Helvetica': '/System/Library/Fonts/Helvetica.ttc',
            'SimHei': '/System/Library/Fonts/SimHei.ttf',  # 黑体
            'SimSun': '/System/Library/Fonts/SimSun.ttf',  # 宋体
        }
        
        # 在Windows系统上的字体路径
        if os.name == 'nt':
            font_mapping.update({
                'Arial': 'C:/Windows/Fonts/arial.ttf',
                'Times New Roman': 'C:/Windows/Fonts/times.ttf',
                'SimHei': 'C:/Windows/Fonts/simhei.ttf',
                'SimSun': 'C:/Windows/Fonts/simsun.ttc',
            })
        
        return font_mapping.get(font_family, font_mapping['Arial'])
    
    def _save_processed_image(self, image: Image.Image) -> str:
        """保存处理后的图片并返回URL"""
        try:
            # 生成唯一文件名
            filename = f"processed_{uuid.uuid4().hex}.jpg"
            file_path = os.path.join(self.processed_folder, filename)
            
            # 保存图片
            image.save(file_path, 'JPEG', quality=95)
            
            # 返回相对URL（实际部署时需要配置为完整URL）
            return f"/static/processed/{filename}"
        
        except Exception as e:
            logger.error(f"保存处理后图片失败: {str(e)}")
            raise e
    
    def create_thumbnail(self, image_url: str, size: tuple = (300, 300)) -> str:
        """创建图片缩略图"""
        try:
            image = self._download_image(image_url)
            
            # 创建缩略图
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 保存缩略图
            filename = f"thumb_{uuid.uuid4().hex}.jpg"
            file_path = os.path.join(self.processed_folder, filename)
            image.save(file_path, 'JPEG', quality=85)
            
            return f"/static/processed/{filename}"
        
        except Exception as e:
            logger.error(f"创建缩略图失败: {str(e)}")
            raise e
    
    def compress_image(self, image_url: str, quality: int = 80) -> str:
        """压缩图片"""
        try:
            image = self._download_image(image_url)
            
            # 压缩保存
            filename = f"compressed_{uuid.uuid4().hex}.jpg"
            file_path = os.path.join(self.processed_folder, filename)
            image.save(file_path, 'JPEG', quality=quality, optimize=True)
            
            return f"/static/processed/{filename}"
        
        except Exception as e:
            logger.error(f"压缩图片失败: {str(e)}")
            raise e