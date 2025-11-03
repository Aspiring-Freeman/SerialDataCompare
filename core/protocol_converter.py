# -*- coding: utf-8 -*-
"""
协议格式转换器
用于兼容不同格式的协议JSON文件
"""

from typing import Dict, Any, List
from models import ProtocolConfig, FieldDefinition, ChecksumConfig, ChecksumType, ChecksumPosition, FieldType


class ProtocolConverter:
    """协议格式转换器"""
    
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
    
    @staticmethod
    def convert_field_type(field_type_str: str) -> FieldType:
        """转换字段类型字符串"""
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
    
    @staticmethod
    def convert_from_extended(data: Dict[str, Any]) -> Dict[str, Any]:
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
                'checksum_type': ProtocolConverter.convert_checksum_type(
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
        for i, field_data in enumerate(data.get('fields', [])):
            # 跳过帧头、帧尾、校验码（这些已经在协议配置中）
            field_type = field_data.get('field_type', 'bytes')
            if field_type in ['fixed'] and field_data.get('name') in ['帧开始符', '固定帧尾', '帧头', '帧尾']:
                continue
            if field_type == 'checksum':
                continue
            
            # 转换字段
            byte_count = field_data.get('byte_count', 1)
            
            # 处理范围索引（如 "16-65"）
            index_str = str(field_data.get('index', i))
            if '-' in index_str:
                # 这是一个范围，使用指定的字节数
                pass
            
            converted_field = {
                'name': field_data.get('name', f'字段{i+1}'),
                'byte_count': byte_count,
                'field_type': ProtocolConverter.convert_field_type(field_type).value,
                'description': field_data.get('description', ''),
                'order': len(fields)
            }
            
            # 如果有 length_field，添加
            if 'length_field' in field_data:
                converted_field['length_field'] = field_data['length_field']
            
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
