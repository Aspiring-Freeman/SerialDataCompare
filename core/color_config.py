"""
颜色配置管理
"""
import json
import os
from pathlib import Path
from typing import Dict
from PySide6.QtGui import QColor


class ColorConfig:
    """颜色配置类"""
    
    # 默认颜色配置
    DEFAULT_COLORS = {
        'uint8': '#90EE90',     # 浅绿色
        'uint16': '#87CEEB',    # 天蓝色
        'uint32': '#DDA0DD',    # 梅红色
        'int8': '#98FB98',      # 淡绿色
        'int16': '#ADD8E6',     # 淡蓝色
        'int32': '#D8BFD8',     # 蓟色
        'float': '#FFB6C1',     # 浅粉色
        'double': '#FFA07A',    # 浅鲑鱼色
        'bytes': '#F0E68C',     # 卡其色
        'string': '#E0E0E0',    # 浅灰色
    }
    
    def __init__(self):
        """初始化"""
        self.config_dir = Path.home() / '.serialdatacompare'
        self.config_file = self.config_dir / 'color_config.json'
        self.colors = self.load_colors()
    
    def load_colors(self) -> Dict[str, str]:
        """加载颜色配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载颜色配置失败: {e}")
        
        return self.DEFAULT_COLORS.copy()
    
    def save_colors(self):
        """保存颜色配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.colors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存颜色配置失败: {e}")
    
    def get_color(self, field_type: str) -> str:
        """获取字段类型对应的颜色"""
        return self.colors.get(field_type, '#FFFFFF')
    
    def set_color(self, field_type: str, color: str):
        """设置字段类型的颜色"""
        self.colors[field_type] = color
        self.save_colors()
    
    def reset_colors(self):
        """重置为默认颜色"""
        self.colors = self.DEFAULT_COLORS.copy()
        self.save_colors()
    
    def get_qcolor(self, field_type: str) -> QColor:
        """获取QColor对象"""
        color_str = self.get_color(field_type)
        return QColor(color_str)
