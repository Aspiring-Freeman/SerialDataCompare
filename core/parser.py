# -*- coding: utf-8 -*-
"""
数据解析模块
负责解析十六进制数据、识别帧、解析字段
"""

import re
import struct
from typing import List, Optional
from models import (
    ProtocolConfig, DataFrame, ParseResult,
    FieldType, ChecksumType
)
from core.checksum import ChecksumValidator


class DataParser:
    """数据解析器"""
    
    def __init__(self, protocol: ProtocolConfig):
        """
        初始化解析器
        
        Args:
            protocol: 协议配置
        """
        self.protocol = protocol
    
    @staticmethod
    def parse_hex_string(hex_string: str) -> bytes:
        """
        解析十六进制字符串为字节数据
        
        Args:
            hex_string: 十六进制字符串，可以包含空格、逗号、换行等分隔符
            
        Returns:
            字节数据
            
        Raises:
            ValueError: 如果输入不是有效的十六进制
        """
        # 移除所有空白字符和分隔符
        cleaned = re.sub(r'[\s,;:\-]+', '', hex_string.upper())
        
        # 验证是否为有效的十六进制
        if not re.match(r'^[0-9A-F]*$', cleaned):
            raise ValueError("输入包含无效的十六进制字符")
        
        # 确保长度为偶数
        if len(cleaned) % 2 != 0:
            raise ValueError("十六进制字符串长度必须为偶数")
        
        # 转换为字节
        return bytes.fromhex(cleaned)
    
    def find_frames(self, data: bytes) -> List[tuple[int, int]]:
        """
        在数据中查找所有帧的位置（增强版，支持多种分帧策略）
        
        分帧策略优先级：
        1. 如果配置了 frame_length，使用固定长度分帧
        2. 如果配置了 length_field_name，读取长度字段值进行分帧
        3. 否则使用传统的帧头+帧尾查找方式
        
        Args:
            data: 原始字节数据
            
        Returns:
            帧位置列表 [(start, end), ...]
        """
        frames = []
        header = self.protocol.get_header_bytes()
        tail = self.protocol.get_tail_bytes()
        header_len = len(header)
        tail_len = len(tail)
        
        pos = 0
        while pos < len(data):
            # 查找帧头
            header_pos = data.find(header, pos)
            if header_pos == -1:
                break
            
            frame_end = None
            
            # 策略1: 使用固定帧长度
            if self.protocol.frame_length is not None:
                frame_end = header_pos + self.protocol.frame_length
                if frame_end > len(data):
                    # 数据不足，帧不完整
                    break
                    
            # 策略2: 从数据中读取长度字段
            elif self.protocol.length_field_name is not None:
                try:
                    # 查找长度字段定义
                    length_field = None
                    length_offset = header_len  # 从帧头后开始计算偏移
                    
                    for field_def in self.protocol.fields:
                        if field_def.name == self.protocol.length_field_name:
                            length_field = field_def
                            break
                        length_offset += field_def.byte_count
                    
                    if length_field:
                        # 读取长度字段的值
                        field_start = header_pos + length_offset
                        field_end = field_start + length_field.byte_count
                        
                        if field_end <= len(data):
                            length_data = data[field_start:field_end]
                            # 根据字段类型解析长度值
                            if length_field.field_type == FieldType.UINT8:
                                frame_length = length_data[0] if len(length_data) >= 1 else 0
                            elif length_field.field_type == FieldType.UINT16:
                                frame_length = struct.unpack('<H', length_data[:2])[0] if len(length_data) >= 2 else 0
                            else:
                                frame_length = int.from_bytes(length_data, byteorder='little')
                            
                            if frame_length > 0:
                                frame_end = header_pos + frame_length
                                if frame_end > len(data):
                                    # 数据不足
                                    break
                except Exception:
                    # 长度字段解析失败，回退到帧尾查找
                    pass
            
            # 策略3: 传统的帧尾查找（如果前两种策略都未成功）
            if frame_end is None:
                search_start = header_pos + header_len
                tail_pos = data.find(tail, search_start)
                
                if tail_pos == -1:
                    # 没有找到帧尾，可能是不完整的帧
                    break
                
                frame_end = tail_pos + tail_len
            
            # 验证帧的完整性（如果有帧尾，检查帧尾是否正确）
            if frame_end > header_pos:
                # 检查帧尾位置是否有正确的帧尾标识
                expected_tail_pos = frame_end - tail_len
                if expected_tail_pos >= 0 and expected_tail_pos + tail_len <= len(data):
                    actual_tail = data[expected_tail_pos:expected_tail_pos + tail_len]
                    if actual_tail == tail:
                        # 帧尾正确，记录这一帧
                        frames.append((header_pos, frame_end))
                        pos = frame_end
                    else:
                        # 帧尾不匹配，可能是数据中的伪帧头，继续查找
                        pos = header_pos + 1
                else:
                    frames.append((header_pos, frame_end))
                    pos = frame_end
            else:
                # 异常情况，跳过这个帧头
                pos = header_pos + 1
        
        return frames
    
    def parse_field(self, data: bytes, field_def, parsed_fields: dict) -> any:
        """
        解析单个字段
        
        Args:
            data: 字段的字节数据
            field_def: 字段定义
            parsed_fields: 已解析的字段（用于处理变长字段）
            
        Returns:
            解析后的值
        """
        field_type = field_def.field_type
        
        try:
            if field_type == FieldType.UINT8:
                return data[0] if len(data) >= 1 else 0
            
            elif field_type == FieldType.UINT16:
                if len(data) >= 2:
                    return struct.unpack('<H', data[:2])[0]  # 小端序
                return 0
            
            elif field_type == FieldType.UINT32:
                if len(data) >= 4:
                    return struct.unpack('<I', data[:4])[0]
                return 0
            
            elif field_type == FieldType.INT8:
                if len(data) >= 1:
                    return struct.unpack('b', data[:1])[0]
                return 0
            
            elif field_type == FieldType.INT16:
                if len(data) >= 2:
                    return struct.unpack('<h', data[:2])[0]
                return 0
            
            elif field_type == FieldType.INT32:
                if len(data) >= 4:
                    return struct.unpack('<i', data[:4])[0]
                return 0
            
            elif field_type == FieldType.FLOAT:
                if len(data) >= 4:
                    return struct.unpack('<f', data[:4])[0]
                return 0.0
            
            elif field_type == FieldType.DOUBLE:
                if len(data) >= 8:
                    return struct.unpack('<d', data[:8])[0]
                return 0.0
            
            elif field_type == FieldType.BYTES:
                return data
            
            elif field_type == FieldType.STRING:
                try:
                    return data.decode('utf-8').rstrip('\x00')
                except:
                    return data.decode('latin-1').rstrip('\x00')
            
            else:
                return data
                
        except Exception as e:
            print(f"解析字段 {field_def.name} 时出错: {e}")
            return data
    
    def parse_frame_fields(self, frame_data: bytes) -> dict:
        """
        解析帧中的所有字段
        
        Args:
            frame_data: 完整的帧数据（包括帧头和帧尾）
            
        Returns:
            字段字典 {字段名: 值}
        """
        fields = {}
        
        # 跳过帧头
        header_len = len(self.protocol.get_header_bytes())
        tail_len = len(self.protocol.get_tail_bytes())
        checksum_len = self.protocol.checksum_config.checksum_length
        
        # 数据部分（帧头后，到校验码或帧尾前）
        if self.protocol.checksum_config.checksum_type != ChecksumType.NONE:
            # 有校验码，数据在帧头后到校验码前
            data_end = len(frame_data) - tail_len - checksum_len
        else:
            # 无校验码，数据在帧头后到帧尾前
            data_end = len(frame_data) - tail_len
        
        data_part = frame_data[header_len:data_end]
        
        # 解析每个字段
        offset = 0
        for field_def in self.protocol.fields:
            if offset >= len(data_part):
                break
            
            # 确定字段长度
            if field_def.byte_count == 0:
                # 变长字段，从长度字段获取
                if field_def.length_field and field_def.length_field in fields:
                    field_len = fields[field_def.length_field]
                else:
                    # 取剩余所有数据
                    field_len = len(data_part) - offset
            else:
                field_len = field_def.byte_count
            
            # 提取字段数据
            field_data = data_part[offset:offset + field_len]
            
            # 解析字段
            field_value = self.parse_field(field_data, field_def, fields)
            fields[field_def.name] = field_value
            
            offset += field_len
        
        return fields
    
    def parse_single_frame(self, frame_data: bytes, 
                          frame_number: int,
                          start_position: int) -> DataFrame:
        """
        解析单个数据帧
        
        Args:
            frame_data: 帧数据
            frame_number: 帧序号
            start_position: 在原始数据中的起始位置
            
        Returns:
            解析后的数据帧对象
        """
        frame = DataFrame(
            frame_number=frame_number,
            start_position=start_position,
            end_position=start_position + len(frame_data),
            raw_data=frame_data
        )
        
        try:
            # 解析字段
            fields = self.parse_frame_fields(frame_data)
            for name, value in fields.items():
                # 找到对应的字段定义，获取类型
                field_type = ""
                for field_def in self.protocol.fields:
                    if field_def.name == name:
                        field_type = field_def.field_type.value
                        break
                frame.add_field(name, value, field_type)
            
            # 校验
            if self.protocol.checksum_config.checksum_type != ChecksumType.NONE:
                is_valid, expected, actual = ChecksumValidator.validate_frame(
                    frame_data,
                    self.protocol.checksum_config
                )
                frame.set_checksum_result(is_valid, expected, actual)
        
        except Exception as e:
            frame.set_error(f"解析错误: {str(e)}")
        
        return frame
    
    def parse(self, hex_string: str) -> ParseResult:
        """
        解析十六进制字符串
        
        Args:
            hex_string: 输入的十六进制字符串
            
        Returns:
            解析结果
        """
        result = ParseResult()
        
        try:
            # 转换为字节数据
            data = self.parse_hex_string(hex_string)
            result.total_bytes = len(data)
            
            # 查找所有帧
            frame_positions = self.find_frames(data)
            
            # 解析每一帧
            for i, (start, end) in enumerate(frame_positions, 1):
                frame_data = data[start:end]
                frame = self.parse_single_frame(frame_data, i, start)
                result.add_frame(frame)
        
        except ValueError as e:
            # 数据格式错误
            error_frame = DataFrame(
                frame_number=0,
                start_position=0,
                end_position=0,
                raw_data=b''
            )
            error_frame.set_error(f"数据格式错误: {str(e)}")
            result.add_frame(error_frame)
        
        except Exception as e:
            # 其他错误
            error_frame = DataFrame(
                frame_number=0,
                start_position=0,
                end_position=0,
                raw_data=b''
            )
            error_frame.set_error(f"解析失败: {str(e)}")
            result.add_frame(error_frame)
        
        return result
