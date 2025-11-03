# -*- coding: utf-8 -*-
"""
数据模型模块 - 协议配置和字段定义
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ChecksumType(Enum):
    """校验类型枚举"""
    NONE = "无校验"
    SUM = "累加和"
    XOR = "异或校验"
    CRC16 = "CRC16"
    CRC32 = "CRC32"


class ChecksumPosition(Enum):
    """校验码位置枚举"""
    BEFORE_TAIL = "帧尾前"
    AFTER_TAIL = "帧尾后"
    CUSTOM = "自定义位置"


class FieldType(Enum):
    """字段数据类型枚举"""
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    FLOAT = "float"
    DOUBLE = "double"
    BYTES = "bytes"
    STRING = "string"


@dataclass
class ChecksumConfig:
    """校验配置"""
    checksum_type: ChecksumType = ChecksumType.NONE
    position: ChecksumPosition = ChecksumPosition.BEFORE_TAIL
    # 自定义校验范围（如果position是CUSTOM）
    start_offset: int = 0  # 从帧头后第几个字节开始（0表示紧跟帧头）
    end_offset: int = -1   # 到帧尾前第几个字节结束（-1表示到校验码前）
    checksum_length: int = 1  # 校验码字节数
    
    def __post_init__(self):
        """数据验证"""
        if self.checksum_length < 1:
            self.checksum_length = 1


@dataclass
class FieldDefinition:
    """字段定义"""
    name: str
    byte_count: int  # 字节数，0表示变长
    field_type: FieldType
    description: str = ""
    order: int = 0
    # 如果是变长字段，指定长度字段的名称
    length_field: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'byte_count': self.byte_count,
            'field_type': self.field_type.value,
            'description': self.description,
            'order': self.order,
            'length_field': self.length_field
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldDefinition':
        """从字典创建"""
        field_type = FieldType(data.get('field_type', 'bytes'))
        return cls(
            name=data['name'],
            byte_count=data['byte_count'],
            field_type=field_type,
            description=data.get('description', ''),
            order=data.get('order', 0),
            length_field=data.get('length_field')
        )


@dataclass
class ProtocolConfig:
    """协议配置"""
    protocol_name: str = "默认协议"
    version: str = "1.0"
    description: str = ""
    
    # 帧标识
    frame_header: str = "68"  # 十六进制字符串
    frame_tail: str = "16"    # 十六进制字符串
    
    # 校验配置
    checksum_config: ChecksumConfig = field(default_factory=ChecksumConfig)
    
    # 字段定义列表
    fields: List[FieldDefinition] = field(default_factory=list)
    
    def __post_init__(self):
        """数据验证"""
        # 确保帧头帧尾是有效的十六进制
        try:
            int(self.frame_header, 16)
            int(self.frame_tail, 16)
        except ValueError:
            raise ValueError("帧头或帧尾不是有效的十六进制字符串")
    
    def add_field(self, field_def: FieldDefinition):
        """添加字段"""
        field_def.order = len(self.fields)
        self.fields.append(field_def)
    
    def remove_field(self, index: int):
        """删除字段"""
        if 0 <= index < len(self.fields):
            del self.fields[index]
            # 重新排序
            for i, field_def in enumerate(self.fields):
                field_def.order = i
    
    def move_field_up(self, index: int):
        """字段上移"""
        if 0 < index < len(self.fields):
            self.fields[index], self.fields[index - 1] = \
                self.fields[index - 1], self.fields[index]
            # 更新order
            self.fields[index].order = index
            self.fields[index - 1].order = index - 1
    
    def move_field_down(self, index: int):
        """字段下移"""
        if 0 <= index < len(self.fields) - 1:
            self.fields[index], self.fields[index + 1] = \
                self.fields[index + 1], self.fields[index]
            # 更新order
            self.fields[index].order = index
            self.fields[index + 1].order = index + 1
    
    def get_header_bytes(self) -> bytes:
        """获取帧头字节"""
        return bytes.fromhex(self.frame_header)
    
    def get_tail_bytes(self) -> bytes:
        """获取帧尾字节"""
        return bytes.fromhex(self.frame_tail)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON保存）"""
        return {
            'protocol_name': self.protocol_name,
            'version': self.version,
            'description': self.description,
            'frame_header': self.frame_header,
            'frame_tail': self.frame_tail,
            'checksum_config': {
                'checksum_type': self.checksum_config.checksum_type.value,
                'position': self.checksum_config.position.value,
                'start_offset': self.checksum_config.start_offset,
                'end_offset': self.checksum_config.end_offset,
                'checksum_length': self.checksum_config.checksum_length
            },
            'fields': [f.to_dict() for f in self.fields]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolConfig':
        """从字典创建（用于JSON加载）"""
        checksum_data = data.get('checksum_config', {})
        checksum_config = ChecksumConfig(
            checksum_type=ChecksumType(checksum_data.get('checksum_type', '无校验')),
            position=ChecksumPosition(checksum_data.get('position', '帧尾前')),
            start_offset=checksum_data.get('start_offset', 0),
            end_offset=checksum_data.get('end_offset', -1),
            checksum_length=checksum_data.get('checksum_length', 1)
        )
        
        fields = [FieldDefinition.from_dict(f) for f in data.get('fields', [])]
        
        return cls(
            protocol_name=data.get('protocol_name', '默认协议'),
            version=data.get('version', '1.0'),
            description=data.get('description', ''),
            frame_header=data['frame_header'],
            frame_tail=data['frame_tail'],
            checksum_config=checksum_config,
            fields=fields
        )
