"""
颜色配置管理
支持配置验证、迁移和类型安全
"""
import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PySide6.QtGui import QColor

from utils import atomic_write_json

logger = logging.getLogger(__name__)


@dataclass
class ColorValidationError:
    """颜色验证错误"""
    field: str
    value: str
    message: str


class ColorConfigValidator:
    """颜色配置验证器"""
    
    # 有效的十六进制颜色模式
    HEX_COLOR_PATTERN = re.compile(r'^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$')
    
    # 已知的颜色名称
    NAMED_COLORS = {
        'red', 'green', 'blue', 'white', 'black', 'yellow', 'cyan', 'magenta',
        'gray', 'grey', 'orange', 'pink', 'purple', 'brown', 'navy', 'teal',
        'olive', 'maroon', 'silver', 'lime', 'aqua', 'fuchsia'
    }
    
    @classmethod
    def is_valid_color(cls, color_str: str) -> bool:
        """检查是否为有效的颜色字符串"""
        if not color_str:
            return False
        
        # 十六进制格式
        if cls.HEX_COLOR_PATTERN.match(color_str):
            return True
        
        # 命名颜色
        if color_str.lower() in cls.NAMED_COLORS:
            return True
        
        # 使用 QColor 验证
        qcolor = QColor(color_str)
        return qcolor.isValid()
    
    @classmethod
    def normalize_color(cls, color_str: str) -> str:
        """标准化颜色字符串为 #RRGGBB 格式"""
        if not color_str:
            return '#FFFFFF'
        
        # 已经是标准格式
        if cls.HEX_COLOR_PATTERN.match(color_str):
            # 扩展 #RGB 到 #RRGGBB
            if len(color_str) == 4:
                r, g, b = color_str[1], color_str[2], color_str[3]
                return f'#{r}{r}{g}{g}{b}{b}'.upper()
            return color_str.upper()
        
        # 使用 QColor 转换
        qcolor = QColor(color_str)
        if qcolor.isValid():
            return qcolor.name().upper()
        
        return '#FFFFFF'
    
    @classmethod
    def validate_config(cls, config: Dict[str, str]) -> Tuple[bool, List[ColorValidationError]]:
        """
        验证整个配置
        
        Args:
            config: 颜色配置字典
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        for field_type, color_str in config.items():
            if not isinstance(color_str, str):
                errors.append(ColorValidationError(
                    field=field_type,
                    value=str(color_str),
                    message=f"颜色值必须是字符串，实际类型为 {type(color_str).__name__}"
                ))
                continue
            
            if not cls.is_valid_color(color_str):
                errors.append(ColorValidationError(
                    field=field_type,
                    value=color_str,
                    message=f"无效的颜色格式: {color_str}"
                ))
        
        return len(errors) == 0, errors


class ColorConfig:
    """颜色配置类 - 增强版"""
    
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
    
    # 配置版本（用于迁移）
    CONFIG_VERSION = 2
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化"""
        self.config_dir = config_dir or (Path.home() / '.serialdatacompare')
        self.config_file = self.config_dir / 'color_config.json'
        self._validator = ColorConfigValidator()
        self._load_errors: List[ColorValidationError] = []
        self.colors = self._load_colors_safe()
    
    @property
    def has_load_errors(self) -> bool:
        """加载时是否有错误"""
        return len(self._load_errors) > 0
    
    @property
    def load_errors(self) -> List[ColorValidationError]:
        """获取加载错误"""
        return self._load_errors.copy()
    
    def _load_colors_safe(self) -> Dict[str, str]:
        """安全加载颜色配置（带验证和迁移）"""
        self._load_errors = []
        
        if not self.config_file.exists():
            logger.info("颜色配置文件不存在，使用默认配置")
            return self.DEFAULT_COLORS.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"颜色配置文件 JSON 格式错误: {e}")
            self._load_errors.append(ColorValidationError(
                field="_file",
                value=str(self.config_file),
                message=f"JSON 格式错误: {e}"
            ))
            return self.DEFAULT_COLORS.copy()
        except Exception as e:
            logger.error(f"读取颜色配置文件失败: {e}")
            return self.DEFAULT_COLORS.copy()
        
        # 检查是否需要迁移
        config_version = data.get('_version', 1) if isinstance(data, dict) else 1
        
        # 提取颜色配置
        if isinstance(data, dict):
            # 新格式：可能包含元数据
            colors = data.get('colors', data)
            # 移除元数据键
            colors = {k: v for k, v in colors.items() if not k.startswith('_')}
        else:
            colors = {}
        
        # 验证配置
        is_valid, errors = self._validator.validate_config(colors)
        
        if not is_valid:
            self._load_errors.extend(errors)
            logger.warning(f"颜色配置验证发现 {len(errors)} 个问题")
            
            # 修复无效的颜色
            for error in errors:
                if error.field in colors:
                    colors[error.field] = self.DEFAULT_COLORS.get(
                        error.field, '#FFFFFF'
                    )
        
        # 合并默认值（确保所有类型都有颜色）
        result = self.DEFAULT_COLORS.copy()
        for field_type, color_str in colors.items():
            result[field_type] = self._validator.normalize_color(color_str)
        
        # 迁移旧配置
        if config_version < self.CONFIG_VERSION:
            self._migrate_config(result, config_version)
        
        return result
    
    def _migrate_config(self, colors: Dict[str, str], from_version: int):
        """迁移旧版本配置"""
        logger.info(f"迁移颜色配置 v{from_version} -> v{self.CONFIG_VERSION}")
        
        # v1 -> v2: 添加新的字段类型颜色
        if from_version < 2:
            # 添加 v2 新增的类型
            new_types = {
                'bcd': '#FFDAB9',      # 桃色
                'timestamp': '#B0E0E6', # 粉蓝色
                'array': '#DEB887',     # 原木色
            }
            for field_type, color in new_types.items():
                if field_type not in colors:
                    colors[field_type] = color
        
        # 保存迁移后的配置
        self.colors = colors
        self.save_colors()
    
    def load_colors(self) -> Dict[str, str]:
        """加载颜色配置（兼容旧接口）"""
        return self._load_colors_safe()
    
    def save_colors(self) -> bool:
        """
        保存颜色配置 - 使用原子写入确保数据安全
        
        Returns:
            是否成功
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加元数据
        data = {
            '_version': self.CONFIG_VERSION,
            'colors': self.colors
        }
        
        if atomic_write_json(str(self.config_file), data):
            logger.info("颜色配置保存成功")
            return True
        else:
            logger.error("保存颜色配置失败")
            return False
    
    def get_color(self, field_type: str) -> str:
        """获取字段类型对应的颜色"""
        return self.colors.get(field_type, '#FFFFFF')
    
    def set_color(self, field_type: str, color: str) -> bool:
        """
        设置字段类型的颜色
        
        Args:
            field_type: 字段类型
            color: 颜色字符串
            
        Returns:
            是否成功
        """
        if not self._validator.is_valid_color(color):
            logger.warning(f"无效的颜色值: {color}")
            return False
        
        normalized = self._validator.normalize_color(color)
        self.colors[field_type] = normalized
        return self.save_colors()
    
    def set_colors_batch(self, colors: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        批量设置颜色
        
        Args:
            colors: 颜色字典
            
        Returns:
            (是否完全成功, 失败的字段列表)
        """
        failed = []
        
        for field_type, color in colors.items():
            if not self._validator.is_valid_color(color):
                failed.append(field_type)
            else:
                self.colors[field_type] = self._validator.normalize_color(color)
        
        self.save_colors()
        return len(failed) == 0, failed
    
    def reset_colors(self):
        """重置为默认颜色"""
        self.colors = self.DEFAULT_COLORS.copy()
        self._load_errors = []
        self.save_colors()
    
    def reset_color(self, field_type: str) -> bool:
        """重置单个字段类型的颜色"""
        if field_type in self.DEFAULT_COLORS:
            self.colors[field_type] = self.DEFAULT_COLORS[field_type]
            return self.save_colors()
        return False
    
    def get_qcolor(self, field_type: str) -> QColor:
        """获取QColor对象"""
        color_str = self.get_color(field_type)
        return QColor(color_str)
    
    def get_all_field_types(self) -> List[str]:
        """获取所有已配置的字段类型"""
        return list(self.colors.keys())
    
    def export_config(self, file_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            data = {
                '_version': self.CONFIG_VERSION,
                '_exported_from': 'SerialDataCompare',
                'colors': self.colors
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"颜色配置导出成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"导出颜色配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        从文件导入配置
        
        Args:
            file_path: 源文件路径
            
        Returns:
            (是否成功, 警告列表)
        """
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"导入颜色配置失败: {e}")
            return False, [f"读取文件失败: {e}"]
        
        # 提取颜色配置
        if isinstance(data, dict):
            colors = data.get('colors', data)
            colors = {k: v for k, v in colors.items() if not k.startswith('_')}
        else:
            return False, ["无效的配置格式"]
        
        # 验证并导入
        is_valid, errors = self._validator.validate_config(colors)
        
        if errors:
            for error in errors:
                warnings.append(f"{error.field}: {error.message}")
        
        # 应用有效的颜色
        for field_type, color_str in colors.items():
            if self._validator.is_valid_color(color_str):
                self.colors[field_type] = self._validator.normalize_color(color_str)
        
        self.save_colors()
        logger.info(f"颜色配置导入完成，{len(warnings)} 个警告")
        
        return True, warnings

