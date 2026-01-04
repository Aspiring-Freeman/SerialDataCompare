# -*- coding: utf-8 -*-
"""
协议格式转换器
用于兼容不同格式的协议JSON文件
支持语义类型保留和智能类型推断
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from models import ProtocolConfig, FieldDefinition, ChecksumConfig, ChecksumType, ChecksumPosition, FieldType


class SemanticType(Enum):
    """语义类型 - 用于保留字段的业务含义"""
    UNKNOWN = "unknown"
    HEADER = "header"          # 帧头
    TAIL = "tail"              # 帧尾
    ADDRESS = "address"        # 地址
    COMMAND = "command"        # 命令码
    LENGTH = "length"          # 长度字段
    DATA = "data"              # 数据字段
    CHECKSUM = "checksum"      # 校验码
    TIMESTAMP = "timestamp"    # 时间戳
    COUNTER = "counter"        # 计数器
    STATUS = "status"          # 状态字段
    VERSION = "version"        # 版本号
    RESERVED = "reserved"      # 保留字段
    ARRAY = "array"            # 数组数据


@dataclass
class TypeMapping:
    """类型映射结果"""
    field_type: FieldType
    semantic_type: SemanticType
    confidence: float  # 0.0-1.0 置信度
    source_hint: str   # 来源提示（用于调试）


class ProtocolConverter:
    """协议格式转换器"""
    
    # 语义类型关键词映射
    SEMANTIC_KEYWORDS = {
        SemanticType.HEADER: ['帧头', '帧开始', 'header', 'start', 'sof', '起始'],
        SemanticType.TAIL: ['帧尾', '帧结束', 'tail', 'end', 'eof', '结束符'],
        SemanticType.ADDRESS: ['地址', 'address', 'addr', 'id', '设备地址', '从站'],
        SemanticType.COMMAND: ['命令', 'command', 'cmd', 'function', '功能码', '操作码'],
        SemanticType.LENGTH: ['长度', 'length', 'len', 'size', '数据长度', '字节数'],
        SemanticType.DATA: ['数据', 'data', 'payload', '内容', '负载'],
        SemanticType.CHECKSUM: ['校验', 'checksum', 'crc', 'sum', 'check', 'fcs'],
        SemanticType.TIMESTAMP: ['时间', 'time', 'timestamp', 'date', '日期'],
        SemanticType.COUNTER: ['计数', 'counter', 'count', 'seq', '序号'],
        SemanticType.STATUS: ['状态', 'status', 'state', 'flag', '标志'],
        SemanticType.VERSION: ['版本', 'version', 'ver', '协议版本'],
        SemanticType.RESERVED: ['保留', 'reserved', 'rsvd', '预留'],
        SemanticType.ARRAY: ['数组', 'array', 'list', '列表', '集合'],
    }
    
    # 扩展格式类型到标准类型的映射
    EXTENDED_TYPE_MAP = {
        'fixed': (FieldType.BYTES, SemanticType.UNKNOWN, 0.5),
        'variable': (FieldType.BYTES, SemanticType.DATA, 0.6),
        'command': (FieldType.UINT8, SemanticType.COMMAND, 0.8),
        'checksum': (FieldType.UINT8, SemanticType.CHECKSUM, 0.9),
        'array': (FieldType.BYTES, SemanticType.ARRAY, 0.7),
        'length': (FieldType.UINT16, SemanticType.LENGTH, 0.9),
        'address': (FieldType.UINT8, SemanticType.ADDRESS, 0.9),
        'status': (FieldType.UINT8, SemanticType.STATUS, 0.8),
        'timestamp': (FieldType.UINT32, SemanticType.TIMESTAMP, 0.8),
        'counter': (FieldType.UINT16, SemanticType.COUNTER, 0.8),
        'data': (FieldType.BYTES, SemanticType.DATA, 0.8),
        'reserved': (FieldType.BYTES, SemanticType.RESERVED, 0.9),
    }
    
    @staticmethod
    def detect_format(data: Dict[str, Any]) -> str:
        """
        检测JSON格式类型
        
        Returns:
            'standard' - 标准格式（程序内部格式）
            'extended' - 扩展格式（包含index, value等字段）
            'unknown' - 无法识别
        """
        if 'fields' not in data:
            return 'unknown'
        
        fields = data['fields']
        if not fields:
            return 'unknown'
        
        first_field = fields[0]
        
        # 检查是否为扩展格式
        if 'index' in first_field or 'value' in first_field or 'format' in first_field:
            return 'extended'
        
        # 检查是否为标准格式
        if 'name' in first_field and 'byte_count' in first_field and 'field_type' in first_field:
            return 'standard'
        
        return 'unknown'
    
    @staticmethod
    def convert_checksum_type(checksum_str: str) -> ChecksumType:
        """转换校验类型字符串"""
        mapping = {
            '无校验': ChecksumType.NONE,
            '累加和': ChecksumType.SUM,
            'SUM': ChecksumType.SUM,
            '异或校验': ChecksumType.XOR,
            'XOR': ChecksumType.XOR,
            'CRC16': ChecksumType.CRC16,
            'CRC32': ChecksumType.CRC32,
        }
        return mapping.get(checksum_str, ChecksumType.NONE)
    
    @classmethod
    def infer_semantic_type(cls, field_name: str, field_type_str: str = "",
                            byte_count: int = 1) -> Tuple[SemanticType, float]:
        """
        从字段名和类型推断语义类型
        
        Args:
            field_name: 字段名
            field_type_str: 字段类型字符串
            byte_count: 字节数
            
        Returns:
            (语义类型, 置信度)
        """
        name_lower = field_name.lower()
        
        # 首先从名称关键词推断（优先级更高）
        best_match = (SemanticType.UNKNOWN, 0.0)
        for sem_type, keywords in cls.SEMANTIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_lower:
                    # 计算置信度（完全匹配更高）
                    if name_lower == keyword:
                        conf = 0.95
                    elif name_lower.startswith(keyword) or name_lower.endswith(keyword):
                        conf = 0.85
                    else:
                        conf = 0.7
                    
                    if conf > best_match[1]:
                        best_match = (sem_type, conf)
        
        # 如果从名称找到了语义类型，直接返回
        if best_match[1] > 0:
            return best_match
        
        # 否则检查扩展类型映射
        if field_type_str in cls.EXTENDED_TYPE_MAP:
            _, sem_type, conf = cls.EXTENDED_TYPE_MAP[field_type_str]
            return sem_type, conf
        
        return best_match
    
    @classmethod
    def convert_field_type_enhanced(cls, field_type_str: str, 
                                    field_name: str = "",
                                    byte_count: int = 1) -> TypeMapping:
        """
        增强的字段类型转换（保留语义信息）
        
        Args:
            field_type_str: 字段类型字符串
            field_name: 字段名（用于语义推断）
            byte_count: 字节数
            
        Returns:
            TypeMapping 对象
        """
        # 推断语义类型
        sem_type, sem_conf = cls.infer_semantic_type(field_name, field_type_str, byte_count)
        
        # 检查扩展格式映射
        if field_type_str in cls.EXTENDED_TYPE_MAP:
            field_type, _, type_conf = cls.EXTENDED_TYPE_MAP[field_type_str]
            return TypeMapping(
                field_type=field_type,
                semantic_type=sem_type,
                confidence=max(sem_conf, type_conf),
                source_hint=f"extended:{field_type_str}"
            )
        
        # 标准格式直接转换
        try:
            field_type = FieldType(field_type_str)
            return TypeMapping(
                field_type=field_type,
                semantic_type=sem_type,
                confidence=sem_conf,
                source_hint=f"standard:{field_type_str}"
            )
        except ValueError:
            pass
        
        # 根据字节数智能选择类型
        field_type = cls._infer_type_from_size(byte_count, sem_type)
        return TypeMapping(
            field_type=field_type,
            semantic_type=sem_type,
            confidence=max(0.4, sem_conf),
            source_hint=f"inferred:size={byte_count}"
        )
    
    @staticmethod
    def _infer_type_from_size(byte_count: int, sem_type: SemanticType) -> FieldType:
        """根据字节数和语义类型推断字段类型"""
        # 对于数组/数据类型，直接用 BYTES
        if sem_type in (SemanticType.DATA, SemanticType.ARRAY, SemanticType.RESERVED):
            return FieldType.BYTES
        
        # 根据字节数选择
        size_mapping = {
            1: FieldType.UINT8,
            2: FieldType.UINT16,
            4: FieldType.UINT32,
        }
        return size_mapping.get(byte_count, FieldType.BYTES)
    
    @staticmethod
    def convert_field_type(field_type_str: str) -> FieldType:
        """转换字段类型字符串（兼容旧接口）"""
        # 扩展格式映射
        extended_mapping = {
            'fixed': FieldType.BYTES,
            'variable': FieldType.BYTES,
            'command': FieldType.UINT8,
            'checksum': FieldType.UINT8,
            'array': FieldType.BYTES,
        }
        
        # 先检查是否是扩展格式
        if field_type_str in extended_mapping:
            return extended_mapping[field_type_str]
        
        # 标准格式
        try:
            return FieldType(field_type_str)
        except ValueError:
            return FieldType.BYTES
    
    @classmethod
    def convert_from_extended(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从扩展格式转换为标准格式
        
        扩展格式特点：
        - 有 index 字段
        - 有 value 字段（固定值）
        - 有 format 字段（HEX/ASCII）
        - field_type 使用 fixed/variable/command 等
        """
        standard_data = {
            'protocol_name': data.get('protocol_name', '未命名协议'),
            'version': data.get('version', '1.0'),
            'description': data.get('description', ''),
            'frame_header': data.get('frame_header', '68'),
            'frame_tail': data.get('frame_tail', '16'),
        }
        
        # 转换校验配置
        checksum_config = data.get('checksum_config', {})
        if isinstance(checksum_config, dict):
            standard_data['checksum_config'] = {
                'checksum_type': cls.convert_checksum_type(
                    checksum_config.get('checksum_type', '无校验')
                ).value,
                'position': ChecksumPosition.BEFORE_TAIL.value,
                'start_offset': checksum_config.get('start_offset', 0),
                'end_offset': checksum_config.get('end_offset', -1),
                'checksum_length': checksum_config.get('checksum_length', 1)
            }
        else:
            standard_data['checksum_config'] = {
                'checksum_type': ChecksumType.NONE.value,
                'position': ChecksumPosition.BEFORE_TAIL.value,
                'start_offset': 0,
                'end_offset': -1,
                'checksum_length': 1
            }
        
        # 转换字段
        fields = []
        conversion_notes = []  # 记录转换过程的注释
        
        for i, field_data in enumerate(data.get('fields', [])):
            # 跳过帧头、帧尾、校验码（这些已经在协议配置中）
            field_type = field_data.get('field_type', 'bytes')
            field_name = field_data.get('name', f'字段{i+1}')
            
            if field_type in ['fixed'] and field_name in ['帧开始符', '固定帧尾', '帧头', '帧尾']:
                conversion_notes.append(f"跳过帧头/帧尾字段: {field_name}")
                continue
            if field_type == 'checksum':
                conversion_notes.append(f"跳过校验码字段: {field_name}")
                continue
            
            # 获取字节数
            byte_count = field_data.get('byte_count', 1)
            
            # 处理范围索引（如 "16-65"）
            index_str = str(field_data.get('index', i))
            if '-' in index_str:
                # 这是一个范围，使用指定的字节数
                try:
                    parts = index_str.split('-')
                    start_idx = int(parts[0])
                    end_idx = int(parts[1])
                    inferred_count = end_idx - start_idx + 1
                    if byte_count == 1 and inferred_count > 1:
                        byte_count = inferred_count
                        conversion_notes.append(
                            f"字段 '{field_name}' 从索引范围推断字节数: {byte_count}"
                        )
                except (ValueError, IndexError):
                    pass
            
            # 使用增强的类型转换
            type_mapping = cls.convert_field_type_enhanced(
                field_type, field_name, byte_count
            )
            
            converted_field = {
                'name': field_name,
                'byte_count': byte_count,
                'field_type': type_mapping.field_type.value,
                'description': field_data.get('description', ''),
                'order': len(fields)
            }
            
            # 保留语义类型信息（如果有价值）
            if type_mapping.semantic_type != SemanticType.UNKNOWN:
                converted_field['_semantic_type'] = type_mapping.semantic_type.value
                converted_field['_conversion_confidence'] = type_mapping.confidence
            
            # 如果有 length_field，添加
            if 'length_field' in field_data:
                converted_field['length_field'] = field_data['length_field']
            
            # 保留缩放信息（如果有）
            if 'multiplier' in field_data:
                converted_field['multiplier'] = field_data['multiplier']
            if 'value_offset' in field_data:
                converted_field['value_offset'] = field_data['value_offset']
            if 'unit' in field_data:
                converted_field['unit'] = field_data['unit']
            if 'decimal_places' in field_data:
                converted_field['decimal_places'] = field_data['decimal_places']
            
            # 保留位域定义（如果有）
            if 'bitfields' in field_data:
                converted_field['bitfields'] = field_data['bitfields']
            
            fields.append(converted_field)
        
        standard_data['fields'] = fields
        
        return standard_data
    
    @staticmethod
    def convert_to_standard(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将任意格式转换为标准格式
        """
        format_type = ProtocolConverter.detect_format(data)
        
        if format_type == 'standard':
            return data
        elif format_type == 'extended':
            return ProtocolConverter.convert_from_extended(data)
        else:
            raise ValueError(f"无法识别的协议格式")
    
    @staticmethod
    def validate_and_convert(data: Dict[str, Any]) -> ProtocolConfig:
        """
        验证并转换为ProtocolConfig对象
        
        Args:
            data: JSON数据字典
            
        Returns:
            ProtocolConfig对象
            
        Raises:
            ValueError: 如果数据无效
        """
        # 检测并转换格式
        standard_data = ProtocolConverter.convert_to_standard(data)
        
        # 使用标准方法加载
        return ProtocolConfig.from_dict(standard_data)
    
    @staticmethod
    def get_format_examples() -> Dict[str, str]:
        """获取格式示例"""
        return {
            'standard': '''标准格式示例：
{
  "protocol_name": "示例协议",
  "version": "1.0",
  "description": "协议说明",
  "frame_header": "68",
  "frame_tail": "16",
  "checksum_config": {
    "checksum_type": "累加和",
    "position": "帧尾前",
    "start_offset": 0,
    "end_offset": -1,
    "checksum_length": 1
  },
  "fields": [
    {
      "name": "地址",
      "byte_count": 1,
      "field_type": "uint8",
      "description": "设备地址",
      "order": 0
    },
    {
      "name": "命令",
      "byte_count": 1,
      "field_type": "uint8",
      "description": "命令码",
      "order": 1
    }
  ]
}''',
            'extended': '''扩展格式示例（自动转换）：
{
  "protocol_name": "工业协议",
  "version": "1.0",
  "description": "工业设备通信协议",
  "frame_header": "68",
  "frame_tail": "16",
  "checksum_config": {
    "checksum_type": "累加和",
    "start_offset": 0,
    "end_offset": -1,
    "checksum_length": 1
  },
  "fields": [
    {
      "index": 0,
      "name": "设备地址",
      "byte_count": 1,
      "field_type": "fixed",
      "format": "HEX",
      "description": "设备地址"
    },
    {
      "index": 1,
      "name": "命令码",
      "byte_count": 1,
      "field_type": "command",
      "format": "HEX",
      "description": "命令类型"
    }
  ]
}'''
        }
