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
        在数据中查找所有帧的位置（验证管线版）
        
        管线流程：
        1. 定位帧头（无帧头时从 pos=0 开始）
        2. 预测帧结束位置（固定长度 > 长度字段 > 帧尾搜索）
        3. 验证帧尾（如果配置了帧尾）
        4. 通过全部验证 → 接受；否则视为伪帧头，前移1字节
        
        无帧头且无帧尾时，将整段数据视为单帧。
        
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
        has_header = header_len > 0
        has_tail = tail_len > 0
        
        # ── 特殊情况：无帧头 ──
        if not has_header:
            return self._find_frames_no_header(data, tail, tail_len, has_tail)
        
        # ── 正常流程：有帧头 ──
        # 防御性上限：最大迭代次数 = 数据长度 + 1
        max_iterations = len(data) + 1
        iteration_count = 0
        
        pos = 0
        while pos < len(data):
            iteration_count += 1
            if iteration_count > max_iterations:
                import logging
                logging.getLogger(__name__).error(
                    f"find_frames 循环超过最大迭代次数 {max_iterations}，强制退出"
                )
                break
            
            # ── 阶段1: 定位帧头 ──
            header_pos = data.find(header, pos)
            if header_pos == -1:
                break
            
            # ── 阶段2: 预测帧结束位置（按优先级尝试多种策略）──
            frame_end = None
            
            # 策略A: 使用固定帧长度
            if self.protocol.frame_length is not None:
                candidate_end = header_pos + self.protocol.frame_length
                if candidate_end <= len(data):
                    frame_end = candidate_end
                else:
                    # 数据不足，帧不完整
                    break
            
            # 策略B: 从数据中读取长度字段
            if frame_end is None and self.protocol.length_field_name is not None:
                frame_end = self._read_length_field_end(data, header_pos, header_len)
                if frame_end is not None and frame_end > len(data):
                    # 数据不足
                    break
            
            # 策略C: 传统的帧尾搜索（仅当前两种策略都未成功时使用）
            if frame_end is None:
                if has_tail:
                    search_start = header_pos + header_len
                    tail_pos = data.find(tail, search_start)
                    if tail_pos == -1:
                        break  # 没有找到帧尾
                    frame_end = tail_pos + tail_len
                else:
                    # 有帧头但没有帧尾也没有长度信息，无法定帧
                    pos = header_pos + 1
                    continue
            
            # ── 阶段3: 验证帧尾 ──
            if frame_end is not None and frame_end > header_pos:
                tail_valid = True  # 默认通过（无帧尾时直接通过）
                
                if has_tail:
                    expected_tail_pos = frame_end - tail_len
                    if expected_tail_pos >= header_pos + header_len and expected_tail_pos + tail_len <= len(data):
                        actual_tail = data[expected_tail_pos:expected_tail_pos + tail_len]
                        tail_valid = (actual_tail == tail)
                    else:
                        tail_valid = False
                
                # ── 阶段4: 接受或拒绝 ──
                if tail_valid:
                    frames.append((header_pos, frame_end))
                    pos = max(frame_end, pos + 1)
                else:
                    # 帧尾不匹配 → 视为伪帧头，前移1字节继续
                    import logging
                    logging.getLogger(__name__).debug(
                        f"帧头@{header_pos} 帧尾验证失败（预期@{frame_end - tail_len}），跳过"
                    )
                    pos = header_pos + 1
            else:
                pos = header_pos + 1
        
        return frames
    
    def _find_frames_no_header(self, data: bytes, tail: bytes,
                                tail_len: int, has_tail: bool) -> List[tuple[int, int]]:
        """无帧头时的分帧逻辑
        
        策略优先级：
        1. 固定帧长度 → 按长度切割
        2. 帧尾搜索 → 按帧尾切割
        3. 都没有 → 整段数据作为单帧
        """
        frames = []
        
        # 策略1: 固定帧长度 → 按长度连续切割
        if self.protocol.frame_length is not None:
            fl = self.protocol.frame_length
            pos = 0
            while pos + fl <= len(data):
                frame_end = pos + fl
                # 如果有帧尾，验证一下
                if has_tail:
                    expected_tail_pos = frame_end - tail_len
                    if expected_tail_pos >= 0:
                        actual_tail = data[expected_tail_pos:frame_end]
                        if actual_tail != tail:
                            # 帧尾不匹配，跳过这段
                            pos += 1
                            continue
                frames.append((pos, frame_end))
                pos = frame_end
            return frames
        
        # 策略2: 按帧尾切割
        if has_tail:
            pos = 0
            while pos < len(data):
                tail_pos = data.find(tail, pos)
                if tail_pos == -1:
                    break
                frame_end = tail_pos + tail_len
                frames.append((pos, frame_end))
                pos = frame_end
            return frames
        
        # 策略3: 无帧头无帧尾无长度 → 整段数据作为单帧
        if len(data) > 0:
            frames.append((0, len(data)))
        return frames
    
    def _read_length_field_end(self, data: bytes, header_pos: int, header_len: int) -> Optional[int]:
        """从数据中读取长度字段并计算帧结束位置
        
        Returns:
            帧结束位置，解析失败返回 None
        """
        try:
            length_field = None
            length_offset = header_len  # 从帧头后开始计算偏移
            
            for field_def in self.protocol.fields:
                if field_def.name == self.protocol.length_field_name:
                    length_field = field_def
                    break
                length_offset += field_def.byte_count
            
            if not length_field:
                return None
            
            field_start = header_pos + length_offset
            field_end = field_start + length_field.byte_count
            
            if field_end > len(data):
                return None
            
            length_data = data[field_start:field_end]
            from models import Endianness
            endian_prefix = '>' if (hasattr(length_field, 'endianness') and 
                                    length_field.endianness == Endianness.BIG) else '<'
            
            if length_field.field_type == FieldType.UINT8:
                frame_length = length_data[0] if len(length_data) >= 1 else 0
            elif length_field.field_type == FieldType.UINT16:
                frame_length = struct.unpack(f'{endian_prefix}H', length_data[:2])[0] if len(length_data) >= 2 else 0
            elif length_field.field_type == FieldType.UINT32:
                frame_length = struct.unpack(f'{endian_prefix}I', length_data[:4])[0] if len(length_data) >= 4 else 0
            else:
                byteorder = 'big' if endian_prefix == '>' else 'little'
                frame_length = int.from_bytes(length_data, byteorder=byteorder)
            
            if frame_length > 0:
                return header_pos + frame_length
            return None
        except Exception:
            return None
    
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
        
        # 确定字节序前缀（默认大端）
        from models import Endianness
        if hasattr(field_def, 'endianness'):
            endian_prefix = '>' if field_def.endianness == Endianness.BIG else '<'
        else:
            # 如果没有endianness属性，默认使用大端
            endian_prefix = '>'
        
        try:
            if field_type == FieldType.UINT8:
                return data[0] if len(data) >= 1 else 0
            
            elif field_type == FieldType.UINT16:
                if len(data) >= 2:
                    return struct.unpack(f'{endian_prefix}H', data[:2])[0]
                return 0
            
            elif field_type == FieldType.UINT32:
                if len(data) >= 4:
                    return struct.unpack(f'{endian_prefix}I', data[:4])[0]
                return 0
            
            elif field_type == FieldType.INT8:
                if len(data) >= 1:
                    return struct.unpack('b', data[:1])[0]
                return 0
            
            elif field_type == FieldType.INT16:
                if len(data) >= 2:
                    return struct.unpack(f'{endian_prefix}h', data[:2])[0]
                return 0
            
            elif field_type == FieldType.INT32:
                if len(data) >= 4:
                    return struct.unpack(f'{endian_prefix}i', data[:4])[0]
                return 0
            
            elif field_type == FieldType.FLOAT:
                if len(data) >= 4:
                    return struct.unpack(f'{endian_prefix}f', data[:4])[0]
                return 0.0
            
            elif field_type == FieldType.DOUBLE:
                if len(data) >= 8:
                    return struct.unpack(f'{endian_prefix}d', data[:8])[0]
                return 0.0
            
            # ============ 新增：BCD码类型支持 ============
            elif field_type == FieldType.BCD:
                # 标准BCD码：每字节表示00-99
                return self._parse_bcd(data, reverse=False)
            
            elif field_type == FieldType.BCD_REVERSED:
                # 逆序BCD码：字节顺序反转（常见于DLT645）
                return self._parse_bcd(data, reverse=True)
            
            elif field_type == FieldType.BCD_DATETIME:
                # BCD日期时间格式：YYMMDDhhmmss
                return self._parse_bcd_datetime(data)
            
            elif field_type == FieldType.BYTES:
                # 原始字节类型：不做字节序处理，直接返回原始数据
                # 字节序仅对数值类型有意义，BYTES 类型应保持原始顺序
                return data
            
            elif field_type == FieldType.STRING:
                # 字符串类型也可能需要字节序处理（如UTF-16等）
                if len(data) > 1 and hasattr(field_def, 'endianness'):
                    from models import Endianness
                    if field_def.endianness == Endianness.LITTLE:
                        # 对于多字节字符编码，可能需要调整字节序
                        # 这里保持简单处理，主要用于原始字节串
                        pass
                try:
                    return data.decode('utf-8').rstrip('\x00')
                except:
                    return data.decode('latin-1').rstrip('\x00')
            
            else:
                return data
                
        except Exception as e:
            print(f"解析字段 {field_def.name} 时出错: {e}")
            return data
    
    def _parse_bcd(self, data: bytes, reverse: bool = False) -> str:
        """
        解析BCD码数据
        
        Args:
            data: BCD编码的字节数据
            reverse: 是否反转字节顺序（用于逆序BCD）
            
        Returns:
            解析后的字符串，如 "123456"
        """
        if reverse:
            data = bytes(reversed(data))
        
        result = []
        for byte in data:
            high = (byte >> 4) & 0x0F
            low = byte & 0x0F
            # 检查是否为有效BCD（0-9）
            if high <= 9:
                result.append(str(high))
            if low <= 9:
                result.append(str(low))
        
        return ''.join(result)
    
    def _parse_bcd_datetime(self, data: bytes) -> str:
        """
        解析BCD日期时间格式
        
        Args:
            data: BCD编码的日期时间数据（通常6字节：YYMMDDhhmmss）
            
        Returns:
            格式化的日期时间字符串，如 "20-12-25 14:30:00"
        """
        if len(data) < 6:
            return self._parse_bcd(data, reverse=False)
        
        # 逐字节解析
        parts = []
        for byte in data[:6]:
            high = (byte >> 4) & 0x0F
            low = byte & 0x0F
            parts.append(f"{high}{low}")
        
        # 格式化为 YY-MM-DD hh:mm:ss
        if len(parts) >= 6:
            return f"{parts[0]}-{parts[1]}-{parts[2]} {parts[3]}:{parts[4]}:{parts[5]}"
        return ''.join(parts)
    
    def parse_frame_fields(self, frame_data: bytes) -> dict:
        """
        解析帧中的所有字段
        
        增强功能：
        - 支持条件字段（根据其他字段值决定是否解析）
        - 支持计算表达式（对原始值进行转换）
        - 支持位域解析（提取位级数据）
        
        Args:
            frame_data: 完整的帧数据（包括帧头和帧尾）
            
        Returns:
            字段字典 {字段名: 值}
        """
        fields = {}
        field_byte_positions = {}  # 记录每个字段的字节位置 {字段名: (start, end)}
        
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
            
            # ============ 新增：检查条件字段 ============
            # 如果字段有条件，检查条件是否满足
            if field_def.is_conditional():
                if not field_def.check_condition(fields):
                    # 条件不满足，跳过此字段
                    continue
            
            # 确定字段长度
            if field_def.byte_count == 0:
                # 变长字段，从长度字段获取
                if field_def.length_field and field_def.length_field in fields:
                    raw_length = fields[field_def.length_field]
                    # 确保是整数类型
                    if not isinstance(raw_length, int):
                        try:
                            raw_length = int(raw_length)
                        except (ValueError, TypeError):
                            raw_length = len(data_part) - offset
                    
                    # ============ 新增：应用长度偏置/公式 ============
                    field_len = field_def.calculate_actual_length(raw_length)
                else:
                    # 取剩余所有数据
                    field_len = len(data_part) - offset
            else:
                field_len = field_def.byte_count
            
            # 确保长度有效
            field_len = max(0, min(field_len, len(data_part) - offset))
            
            # 提取字段数据
            field_data = data_part[offset:offset + field_len]
            
            # 记录字段位置
            field_start = header_len + offset
            field_end = field_start + field_len
            field_byte_positions[field_def.name] = (field_start, field_end)
            
            # 解析字段
            field_value = self.parse_field(field_data, field_def, fields)
            
            # ============ 新增：应用计算表达式 ============
            if field_def.has_calculation():
                # 保存原始值
                fields[f'{field_def.name}_raw'] = field_value
                # 应用计算
                field_value = field_def.apply_calculation(field_value)
            
            # ============ 新增：应用缩放转换 ============
            if field_def.has_scaling():
                # 保存原始值（如果没有被计算表达式保存）
                if f'{field_def.name}_raw' not in fields:
                    fields[f'{field_def.name}_raw'] = field_value
                # 保存缩放后的格式化值
                fields[f'{field_def.name}_scaled'] = field_def.format_scaled_value(field_value)
            
            fields[field_def.name] = field_value
            
            # ============ 新增：位域解析 ============
            if field_def.has_bit_fields():
                # 获取字段的整数值用于位域提取
                if isinstance(field_value, int):
                    bit_value = field_value
                elif isinstance(field_value, bytes):
                    bit_value = int.from_bytes(field_value, byteorder='big')
                else:
                    bit_value = 0
                
                # 提取所有位域
                bit_fields = field_def.extract_bit_fields(bit_value)
                for bf_name, bf_info in bit_fields.items():
                    # 将位域作为子字段添加
                    full_name = f'{field_def.name}.{bf_name}'
                    fields[full_name] = bf_info['formatted']
            
            offset += field_len
        
        # 保存字段位置信息（用于高亮显示）
        fields['_byte_positions'] = field_byte_positions
        
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
            end_position=start_position + len(frame_data) - 1,  # 结束位置是最后一个字节的索引
            raw_data=frame_data
        )
        
        try:
            # 解析字段
            fields = self.parse_frame_fields(frame_data)
            
            # 提取字节位置信息
            byte_positions = fields.pop('_byte_positions', {})
            frame.field_byte_positions = byte_positions
            
            for name, value in fields.items():
                # 跳过内部字段（以_开头的）
                if name.startswith('_'):
                    continue
                # 跳过 _raw 和 _scaled 后缀字段（这些是附加信息）
                if name.endswith('_raw') or name.endswith('_scaled'):
                    continue
                    
                # 找到对应的字段定义，获取类型和缩放信息
                field_type = ""
                scaled_value = None
                for field_def in self.protocol.fields:
                    if field_def.name == name:
                        field_type = field_def.field_type.value
                        # 获取缩放后的值
                        scaled_key = f'{name}_scaled'
                        if scaled_key in fields:
                            scaled_value = fields[scaled_key]
                        break
                    # 检查是否是位域字段
                    if name.startswith(f'{field_def.name}.'):
                        field_type = 'bitfield'
                        break
                frame.add_field(name, value, field_type, scaled_value=scaled_value)
            
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
        result.input_data = hex_string  # 保存输入数据用于历史记录
        
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
