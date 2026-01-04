# -*- coding: utf-8 -*-
"""
自定义异常体系
提供细粒度的错误处理，替代通用 Exception
"""

from typing import Optional, Any


class SerialDataCompareError(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


# ============ 协议相关异常 ============

class ProtocolError(SerialDataCompareError):
    """协议相关错误基类"""
    pass


class ProtocolLoadError(ProtocolError):
    """协议加载错误"""
    
    def __init__(self, file_path: str, reason: str):
        super().__init__(
            f"无法加载协议文件: {reason}",
            {"file_path": file_path}
        )
        self.file_path = file_path
        self.reason = reason


class ProtocolValidationError(ProtocolError):
    """协议验证错误"""
    
    def __init__(self, field_path: str, message: str, value: Any = None):
        super().__init__(
            f"协议配置错误: {message}",
            {"field_path": field_path, "value": value}
        )
        self.field_path = field_path
        self.value = value


class ProtocolConversionError(ProtocolError):
    """协议格式转换错误"""
    
    def __init__(self, source_format: str, reason: str):
        super().__init__(
            f"协议格式转换失败: {reason}",
            {"source_format": source_format}
        )
        self.source_format = source_format


# ============ 解析相关异常 ============

class ParseError(SerialDataCompareError):
    """解析相关错误基类"""
    pass


class FrameNotFoundError(ParseError):
    """未找到有效帧"""
    
    def __init__(self, reason: str = "数据中未找到有效帧"):
        super().__init__(reason)


class FrameParseError(ParseError):
    """帧解析错误"""
    
    def __init__(self, frame_index: int, position: int, reason: str):
        super().__init__(
            f"帧 #{frame_index} 解析失败: {reason}",
            {"frame_index": frame_index, "position": position}
        )
        self.frame_index = frame_index
        self.position = position
        self.reason = reason


class FieldParseError(ParseError):
    """字段解析错误"""
    
    def __init__(self, field_name: str, position: int, reason: str, 
                 expected_bytes: int = 0, actual_bytes: int = 0):
        super().__init__(
            f"字段 '{field_name}' 解析失败: {reason}",
            {
                "field_name": field_name,
                "position": position,
                "expected_bytes": expected_bytes,
                "actual_bytes": actual_bytes
            }
        )
        self.field_name = field_name
        self.position = position
        self.expected_bytes = expected_bytes
        self.actual_bytes = actual_bytes


class DataTruncatedError(ParseError):
    """数据截断错误"""
    
    def __init__(self, expected: int, actual: int, context: str = ""):
        super().__init__(
            f"数据不完整: 期望 {expected} 字节，实际 {actual} 字节",
            {"expected": expected, "actual": actual, "context": context}
        )
        self.expected = expected
        self.actual = actual


# ============ 校验相关异常 ============

class ChecksumError(SerialDataCompareError):
    """校验相关错误基类"""
    pass


class ChecksumMismatchError(ChecksumError):
    """校验值不匹配"""
    
    def __init__(self, expected: int, actual: int, 
                 checksum_type: str = "", frame_index: int = 0):
        super().__init__(
            f"校验失败: 期望 0x{expected:02X}，实际 0x{actual:02X}",
            {
                "expected": f"0x{expected:02X}",
                "actual": f"0x{actual:02X}",
                "checksum_type": checksum_type,
                "frame_index": frame_index
            }
        )
        self.expected = expected
        self.actual = actual
        self.checksum_type = checksum_type
        self.frame_index = frame_index


class ChecksumConfigError(ChecksumError):
    """校验配置错误"""
    
    def __init__(self, config_field: str, message: str, value: Any = None):
        super().__init__(
            f"校验配置错误 [{config_field}]: {message}",
            {"config_field": config_field, "value": value}
        )
        self.config_field = config_field
        self.value = value


class ChecksumRangeError(ChecksumError):
    """校验范围错误"""
    
    def __init__(self, start: int, end: int, frame_length: int, 
                 checksum_position: int):
        super().__init__(
            f"校验范围无效: [{start}:{end}] 在帧长度 {frame_length} 中",
            {
                "start": start,
                "end": end,
                "frame_length": frame_length,
                "checksum_position": checksum_position
            }
        )
        self.start = start
        self.end = end
        self.frame_length = frame_length
        self.checksum_position = checksum_position


# ============ 配置相关异常 ============

class ConfigError(SerialDataCompareError):
    """配置相关错误基类"""
    pass


class ConfigLoadError(ConfigError):
    """配置加载错误"""
    
    def __init__(self, config_name: str, file_path: str, reason: str):
        super().__init__(
            f"加载配置 '{config_name}' 失败: {reason}",
            {"config_name": config_name, "file_path": file_path}
        )
        self.config_name = config_name
        self.file_path = file_path


class ConfigSaveError(ConfigError):
    """配置保存错误"""
    
    def __init__(self, config_name: str, file_path: str, reason: str):
        super().__init__(
            f"保存配置 '{config_name}' 失败: {reason}",
            {"config_name": config_name, "file_path": file_path}
        )
        self.config_name = config_name
        self.file_path = file_path


# ============ 数据相关异常 ============

class DataError(SerialDataCompareError):
    """数据相关错误基类"""
    pass


class InvalidHexDataError(DataError):
    """无效的十六进制数据"""
    
    def __init__(self, data: str, position: int = 0, char: str = ""):
        super().__init__(
            f"无效的十六进制数据",
            {"position": position, "invalid_char": char}
        )
        self.data = data
        self.position = position
        self.invalid_char = char


class DataLengthError(DataError):
    """数据长度错误"""
    
    def __init__(self, expected: int, actual: int, context: str = ""):
        super().__init__(
            f"数据长度不匹配: 期望 {expected}，实际 {actual}",
            {"expected": expected, "actual": actual, "context": context}
        )
        self.expected = expected
        self.actual = actual


# ============ 工具函数 ============

def format_exception_chain(exc: Exception) -> str:
    """格式化异常链为可读字符串"""
    lines = []
    current = exc
    while current:
        if isinstance(current, SerialDataCompareError):
            lines.append(f"• {current}")
        else:
            lines.append(f"• {type(current).__name__}: {current}")
        current = current.__cause__
    return "\n".join(lines)


def wrap_exception(exc: Exception, context: str) -> SerialDataCompareError:
    """将普通异常包装为自定义异常"""
    wrapped = SerialDataCompareError(f"{context}: {exc}")
    wrapped.__cause__ = exc
    return wrapped
