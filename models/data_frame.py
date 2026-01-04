# -*- coding: utf-8 -*-
"""
数据模型模块 - 数据帧定义
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DataFrame:
    """数据帧"""
    frame_number: int  # 帧序号（从1开始）
    start_position: int  # 在原始数据中的起始位置（第一个字节的索引）
    end_position: int  # 在原始数据中的结束位置（最后一个字节的索引，包含）
    raw_data: bytes  # 原始字节数据
    
    # 解析后的字段数据
    fields: Dict[str, Any] = field(default_factory=dict)
    # 字段类型映射（字段名 -> 类型字符串）
    field_types: Dict[str, str] = field(default_factory=dict)
    
    # ============ 新增：字段字节位置映射 ============
    # {字段名: (帧内起始字节, 帧内结束字节)}
    field_byte_positions: Dict[str, tuple] = field(default_factory=dict)
    
    # ============ 新增：字段缩放值映射 ============
    # {字段名: 缩放后的格式化字符串，如 "25.5°C"}
    field_scaled_values: Dict[str, str] = field(default_factory=dict)
    
    # 校验信息
    checksum_valid: bool = True
    expected_checksum: Optional[int] = None
    actual_checksum: Optional[int] = None
    
    # 错误信息
    has_error: bool = False
    error_message: str = ""
    
    def add_field(self, field_name: str, value: Any, field_type: str = "", scaled_value: str = None):
        """
        添加解析后的字段
        
        Args:
            field_name: 字段名称
            value: 字段原始值
            field_type: 字段类型
            scaled_value: 缩放后的格式化值（可选，如 "25.5°C"）
        """
        self.fields[field_name] = value
        if field_type:
            self.field_types[field_name] = field_type
        if scaled_value is not None:
            self.field_scaled_values[field_name] = scaled_value
    
    def get_field_scaled_value(self, field_name: str) -> Optional[str]:
        """获取字段的缩放后值"""
        return self.field_scaled_values.get(field_name)
    
    def get_field(self, field_name: str) -> Optional[Any]:
        """获取字段值"""
        return self.fields.get(field_name)
    
    def get_field_byte_position(self, field_name: str) -> Optional[tuple]:
        """
        获取字段在帧内的字节位置
        
        Returns:
            (start, end) 元组，或 None 如果字段不存在
        """
        return self.field_byte_positions.get(field_name)
    
    def get_field_bytes(self, field_name: str) -> Optional[bytes]:
        """
        获取字段对应的原始字节
        
        Returns:
            字段对应的字节数据，或 None 如果字段不存在
        """
        pos = self.get_field_byte_position(field_name)
        if pos and len(pos) == 2:
            start, end = pos
            return self.raw_data[start:end]
        return None
    
    def set_checksum_result(self, valid: bool, expected: int, actual: int):
        """设置校验结果"""
        self.checksum_valid = valid
        self.expected_checksum = expected
        self.actual_checksum = actual
        if not valid:
            self.has_error = True
            # 根据值大小自动选择格式化宽度
            width = max(2, (max(expected, actual).bit_length() + 3) // 4)
            self.error_message = f"校验失败：期望{expected:0{width}X}，实际{actual:0{width}X}"
    
    def set_error(self, message: str):
        """设置错误"""
        self.has_error = True
        self.error_message = message
    
    def get_raw_data_hex(self) -> str:
        """获取原始数据的十六进制字符串"""
        return ' '.join(f'{b:02X}' for b in self.raw_data)
    
    def get_field_summary(self) -> str:
        """获取字段摘要"""
        if not self.fields:
            return "未解析"
        
        summary_parts = []
        for name, value in self.fields.items():
            if isinstance(value, bytes):
                value_str = ' '.join(f'{b:02X}' for b in value)
            else:
                value_str = str(value)
            summary_parts.append(f"{name}={value_str}")
        
        return ', '.join(summary_parts)
    
    def get_detailed_info(self) -> str:
        """获取详细信息（用于显示在详情区）"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"  数据帧 #{self.frame_number}")
        lines.append("=" * 80)
        lines.append(f"  位置范围: {self.start_position} - {self.end_position} ({len(self.raw_data)} 字节)")
        lines.append("")
        lines.append(f"  原始数据:")
        lines.append(f"  {self.get_raw_data_hex()}")
        lines.append("")
        
        if self.fields:
            lines.append("-" * 80)
            lines.append("  字段解析")
            lines.append("-" * 80)
            for name, value in self.fields.items():
                # 检查是否有缩放后的值
                scaled = self.field_scaled_values.get(name)
                
                if isinstance(value, bytes):
                    value_str = ' '.join(f'{b:02X}' for b in value)
                    # 尝试解码为ASCII字符串
                    try:
                        ascii_str = value.decode('ascii', errors='ignore')
                        if ascii_str and ascii_str.isprintable():
                            lines.append(f"  {name:<30s}: {value_str:<40s} [{ascii_str}]")
                        else:
                            lines.append(f"  {name:<30s}: {value_str}")
                    except:
                        lines.append(f"  {name:<30s}: {value_str}")
                elif isinstance(value, int):
                    if scaled:
                        # 显示原始值和缩放后的值
                        lines.append(f"  {name:<30s}: {value:<10d} (0x{value:X}) → {scaled}")
                    else:
                        lines.append(f"  {name:<30s}: {value:<10d} (0x{value:X})")
                elif isinstance(value, float):
                    if scaled:
                        lines.append(f"  {name:<30s}: {value:.4f} → {scaled}")
                    else:
                        lines.append(f"  {name:<30s}: {value:.4f}")
                else:
                    if scaled:
                        lines.append(f"  {name:<30s}: {value} → {scaled}")
                    else:
                        lines.append(f"  {name:<30s}: {value}")
            lines.append("")
        
        lines.append("-" * 80)
        lines.append("  校验信息")
        lines.append("-" * 80)
        if self.expected_checksum is not None and self.actual_checksum is not None:
            lines.append(f"  计算校验码: 0x{self.expected_checksum:02X}")
            lines.append(f"  帧内校验码: 0x{self.actual_checksum:02X}")
            if self.checksum_valid:
                lines.append(f"  校验状态: ✓ 通过")
            else:
                lines.append(f"  校验状态: ✗ 失败")
                lines.append(f"  >>> 警告: 数据可能损坏或协议配置错误！")
        else:
            lines.append("  (无校验配置)")
        
        if self.has_error:
            lines.append("")
            lines.append("-" * 80)
            lines.append("  错误信息")
            lines.append("-" * 80)
            lines.append(f"  ⚠ {self.error_message}")
        
        lines.append("=" * 80)
        return '\n'.join(lines)
    
    def get_detailed_info_html(self, color_config=None) -> str:
        """获取带颜色的HTML格式详细信息"""
        html_parts = []
        html_parts.append("<html><head><style>")
        html_parts.append("body { font-family: 'Courier New', monospace; font-size: 10pt; }")
        html_parts.append(".header { font-weight: bold; background-color: #e0e0e0; padding: 5px; }")
        html_parts.append(".section { margin-top: 10px; }")
        html_parts.append(".field { margin: 2px 0; }")
        html_parts.append(".field-name { display: inline-block; width: 250px; }")
        html_parts.append(".field-value { display: inline; }")
        html_parts.append(".error { color: red; font-weight: bold; }")
        html_parts.append(".success { color: green; font-weight: bold; }")
        html_parts.append("</style></head><body>")
        
        html_parts.append(f"<div class='header'>数据帧 #{self.frame_number}</div>")
        html_parts.append(f"<div class='section'>位置范围: {self.start_position} - {self.end_position} ({len(self.raw_data)} 字节)</div>")
        html_parts.append(f"<div class='section'>原始数据:<br/>{self.get_raw_data_hex()}</div>")
        
        if self.fields:
            html_parts.append("<div class='section'><b>字段解析:</b></div>")
            for name, value in self.fields.items():
                field_type = self.field_types.get(name, "")
                bg_color = ""
                if color_config and field_type:
                    bg_color = f" style='background-color: {color_config.get_color(field_type)};'"
                
                if isinstance(value, bytes):
                    value_str = ' '.join(f'{b:02X}' for b in value)
                    # 尝试解码为ASCII
                    try:
                        ascii_str = value.decode('ascii', errors='ignore')
                        if ascii_str and ascii_str.isprintable():
                            html_parts.append(f"<div class='field'><span class='field-name'{bg_color}>{name}:</span> <span class='field-value'>{value_str} [{ascii_str}]</span></div>")
                        else:
                            html_parts.append(f"<div class='field'><span class='field-name'{bg_color}>{name}:</span> <span class='field-value'>{value_str}</span></div>")
                    except:
                        html_parts.append(f"<div class='field'><span class='field-name'{bg_color}>{name}:</span> <span class='field-value'>{value_str}</span></div>")
                elif isinstance(value, int):
                    html_parts.append(f"<div class='field'><span class='field-name'{bg_color}>{name}:</span> <span class='field-value'>{value} (0x{value:X})</span></div>")
                elif isinstance(value, float):
                    html_parts.append(f"<div class='field'><span class='field-name'{bg_color}>{name}:</span> <span class='field-value'>{value:.4f}</span></div>")
                else:
                    html_parts.append(f"<div class='field'><span class='field-name'{bg_color}>{name}:</span> <span class='field-value'>{value}</span></div>")
        
        html_parts.append("<div class='section'><b>校验信息:</b></div>")
        if self.expected_checksum is not None and self.actual_checksum is not None:
            html_parts.append(f"<div>计算校验码: 0x{self.expected_checksum:02X}</div>")
            html_parts.append(f"<div>帧内校验码: 0x{self.actual_checksum:02X}</div>")
            if self.checksum_valid:
                html_parts.append("<div class='success'>校验状态: ✓ 通过</div>")
            else:
                html_parts.append("<div class='error'>校验状态: ✗ 失败</div>")
                html_parts.append("<div class='error'>⚠ 警告: 数据可能损坏或协议配置错误！</div>")
        else:
            html_parts.append("<div>(无校验配置)</div>")
        
        if self.has_error:
            html_parts.append(f"<div class='section'><b>错误信息:</b></div>")
            html_parts.append(f"<div class='error'>⚠ {self.error_message}</div>")
        
        html_parts.append("</body></html>")
        return ''.join(html_parts)


@dataclass
class ParseResult:
    """解析结果"""
    frames: list[DataFrame] = field(default_factory=list)
    total_bytes: int = 0
    input_data: str = ""  # 输入的原始数据（用于历史记录）
    
    def add_frame(self, frame: DataFrame):
        """添加数据帧"""
        self.frames.append(frame)
    
    def get_total_frames(self) -> int:
        """获取总帧数"""
        return len(self.frames)
    
    def get_valid_frames(self) -> int:
        """获取有效帧数"""
        return sum(1 for frame in self.frames if not frame.has_error)
    
    def get_error_frames(self) -> int:
        """获取错误帧数"""
        return sum(1 for frame in self.frames if frame.has_error)
    
    def get_frame(self, index: int) -> Optional[DataFrame]:
        """获取指定索引的帧"""
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None
    
    def get_summary(self) -> str:
        """获取统计摘要"""
        return (f"总帧数: {self.get_total_frames()}, "
                f"有效帧: {self.get_valid_frames()}, "
                f"错误帧: {self.get_error_frames()}")
