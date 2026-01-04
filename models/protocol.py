# -*- coding: utf-8 -*-
"""
数据模型模块 - 协议配置和字段定义
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ChecksumType(Enum):
    """校验类型枚举 - 支持多种校验算法"""
    NONE = "无校验"
    
    # 累加和校验
    SUM = "累加和"
    SUM16 = "累加和16位"
    
    # 异或校验
    XOR = "异或校验"
    XOR16 = "异或校验16位"
    
    # CRC-8 系列
    CRC8 = "CRC-8"
    CRC8_ITU = "CRC-8/ITU"
    CRC8_ROHC = "CRC-8/ROHC"
    CRC8_MAXIM = "CRC-8/MAXIM"
    
    # CRC-16 系列
    CRC16_IBM = "CRC-16/IBM"
    CRC16_MODBUS = "CRC-16/MODBUS"
    CRC16_CCITT = "CRC-16/CCITT"
    CRC16_CCITT_FALSE = "CRC-16/CCITT-FALSE"
    CRC16_XMODEM = "CRC-16/XMODEM"
    CRC16_X25 = "CRC-16/X25"
    CRC16_DNP = "CRC-16/DNP"
    CRC16_USB = "CRC-16/USB"
    CRC16_MAXIM = "CRC-16/MAXIM"
    CRC16 = "CRC16"  # 兼容旧版，等同于 MODBUS
    
    # CRC-32 系列
    CRC32 = "CRC-32"
    CRC32_MPEG2 = "CRC-32/MPEG-2"
    CRC32_POSIX = "CRC-32/POSIX"
    
    # LRC (纵向冗余校验)
    LRC = "LRC"
    
    # BCC (块校验码)
    BCC = "BCC"
    
    # Fletcher 校验
    FLETCHER16 = "Fletcher-16"
    FLETCHER32 = "Fletcher-32"
    
    # Adler 校验
    ADLER32 = "Adler-32"
    
    # ============ 新增：自定义CRC ============
    CRC_CUSTOM = "自定义CRC"  # 使用 CRCParameters 配置


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
    
    # ============ 新增：BCD码类型 ============
    BCD = "bcd"              # 标准BCD码（每字节表示00-99）
    BCD_REVERSED = "bcd_rev" # 逆序BCD码（字节顺序反转）
    BCD_DATETIME = "bcd_datetime"  # BCD日期时间（YYMMDDhhmmss）


class Endianness(Enum):
    """字节序枚举"""
    BIG = "big"      # 大端（网络字节序）
    LITTLE = "little"  # 小端（x86字节序）


def format_field_value(value: Any, field_type: Optional['FieldType'] = None) -> str:
    """
    格式化字段值以供显示，将bytes对象转换为可读的十六进制字符串
    
    Args:
        value: 字段值（可能是bytes、int、float、str等）
        field_type: 字段类型（可选）
        
    Returns:
        格式化后的字符串
    """
    if isinstance(value, bytes):
        # 将bytes转换为大写十六进制字符串，用空格分隔
        return ' '.join(f'{b:02X}' for b in value)
    elif field_type == FieldType.BYTES if field_type else False:
        # 如果指定了BYTES类型但值不是bytes，尝试转换
        if isinstance(value, (list, tuple)):
            return ' '.join(f'{b:02X}' for b in value)
        elif isinstance(value, int):
            # 整数显示为十六进制
            return f'{value:02X}'
    return str(value)


@dataclass
class CRCParameters:
    """CRC算法参数化配置 - 支持自定义CRC变体"""
    poly: int = 0x8005        # 多项式
    init: int = 0xFFFF        # 初始值
    ref_in: bool = True       # 输入反转
    ref_out: bool = True      # 输出反转
    xor_out: int = 0x0000     # 结果异或值
    width: int = 16           # CRC位宽（8/16/32）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'poly': self.poly,
            'init': self.init,
            'ref_in': self.ref_in,
            'ref_out': self.ref_out,
            'xor_out': self.xor_out,
            'width': self.width
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CRCParameters':
        return cls(
            poly=data.get('poly', 0x8005),
            init=data.get('init', 0xFFFF),
            ref_in=data.get('ref_in', True),
            ref_out=data.get('ref_out', True),
            xor_out=data.get('xor_out', 0x0000),
            width=data.get('width', 16)
        )
    
    @classmethod
    def modbus(cls) -> 'CRCParameters':
        """MODBUS CRC16"""
        return cls(poly=0x8005, init=0xFFFF, ref_in=True, ref_out=True, xor_out=0x0000, width=16)
    
    @classmethod
    def ccitt(cls) -> 'CRCParameters':
        """CRC16-CCITT"""
        return cls(poly=0x1021, init=0xFFFF, ref_in=False, ref_out=False, xor_out=0x0000, width=16)
    
    @classmethod
    def xmodem(cls) -> 'CRCParameters':
        """CRC16-XMODEM"""
        return cls(poly=0x1021, init=0x0000, ref_in=False, ref_out=False, xor_out=0x0000, width=16)
    
    @classmethod
    def crc32(cls) -> 'CRCParameters':
        """标准CRC32"""
        return cls(poly=0x04C11DB7, init=0xFFFFFFFF, ref_in=True, ref_out=True, xor_out=0xFFFFFFFF, width=32)


@dataclass
class ChecksumConfig:
    """校验配置（简化版）"""
    checksum_type: ChecksumType = ChecksumType.NONE
    position: ChecksumPosition = ChecksumPosition.BEFORE_TAIL
    
    # 简化配置：直接指定绝对位置
    checksum_position: Optional[int] = None  # 校验码在整帧中的位置（从0开始的索引）
    checksum_length: int = 1  # 校验码字节数
    checksum_start: Optional[int] = None  # 校验计算起始位置（从0开始），None表示从帧头开始
    checksum_end: Optional[int] = None    # 校验计算结束位置（不包含），None表示到校验码前
    
    # 校验码字节序（大端/小端）
    # 小端：低字节在前（如 MODBUS CRC16 结果 0x1234 存储为 34 12）
    # 大端：高字节在前（如 XMODEM CRC16 结果 0x1234 存储为 12 34）
    checksum_endianness: Endianness = Endianness.LITTLE  # 默认小端（MODBUS等常用协议）
    
    # ============ 新增：自定义CRC参数 ============
    # 当 checksum_type 为 CRC_CUSTOM 时使用
    crc_params: Optional[CRCParameters] = None
    
    # 旧版兼容字段（如果新字段为None则使用这些）
    start_offset: int = 0  # 从帧头后第几个字节开始（0表示紧跟帧头）
    end_offset: int = -1   # 到帧尾前第几个字节结束（-1表示到校验码前）
    
    def __post_init__(self):
        """数据验证"""
        if self.checksum_length < 1:
            self.checksum_length = 1


@dataclass
class BitFieldDefinition:
    """位域定义 - 用于在一个字节或多个字节中提取特定的位"""
    name: str                   # 位域名称
    start_bit: int              # 起始位（0-based，从LSB开始）
    bit_count: int              # 位数
    description: str = ""       # 描述
    display_format: str = ""    # 显示格式（如 "hex", "binary", "decimal"）
    value_map: Optional[Dict[int, str]] = None  # 值映射表（可选）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'name': self.name,
            'start_bit': self.start_bit,
            'bit_count': self.bit_count,
            'description': self.description,
            'display_format': self.display_format
        }
        if self.value_map:
            result['value_map'] = self.value_map
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BitFieldDefinition':
        """从字典创建"""
        return cls(
            name=data['name'],
            start_bit=data.get('start_bit', 0),
            bit_count=data.get('bit_count', 1),
            description=data.get('description', ''),
            display_format=data.get('display_format', ''),
            value_map=data.get('value_map')
        )
    
    def extract_value(self, byte_value: int) -> int:
        """从字节值中提取位域值"""
        mask = (1 << self.bit_count) - 1
        return (byte_value >> self.start_bit) & mask
    
    def format_value(self, value: int) -> str:
        """格式化位域值"""
        # 如果有值映射，优先使用映射
        if self.value_map and value in self.value_map:
            return self.value_map[value]
        
        # 根据显示格式返回
        if self.display_format == 'hex':
            return f'0x{value:X}'
        elif self.display_format == 'binary':
            return f'{value:0{self.bit_count}b}b'
        else:
            return str(value)


@dataclass
class FieldCondition:
    """字段条件 - 定义字段是否存在或如何解析的条件"""
    field_name: str             # 依赖的字段名
    operator: str               # 操作符: ==, !=, >, <, >=, <=, in, not_in
    value: Any                  # 比较值
    
    def evaluate(self, parsed_fields: Dict[str, Any]) -> bool:
        """评估条件是否满足"""
        if self.field_name not in parsed_fields:
            return False
        
        field_value = parsed_fields[self.field_name]
        
        if self.operator == '==':
            return field_value == self.value
        elif self.operator == '!=':
            return field_value != self.value
        elif self.operator == '>':
            return field_value > self.value
        elif self.operator == '<':
            return field_value < self.value
        elif self.operator == '>=':
            return field_value >= self.value
        elif self.operator == '<=':
            return field_value <= self.value
        elif self.operator == 'in':
            return field_value in self.value
        elif self.operator == 'not_in':
            return field_value not in self.value
        elif self.operator == '&':  # 按位与
            return (field_value & self.value) != 0
        elif self.operator == '!&':  # 按位与等于0
            return (field_value & self.value) == 0
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field_name': self.field_name,
            'operator': self.operator,
            'value': self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldCondition':
        return cls(
            field_name=data['field_name'],
            operator=data.get('operator', '=='),
            value=data['value']
        )


@dataclass
class CalculationExpression:
    """计算表达式 - 用于对字段值进行转换计算"""
    expression: str             # 表达式字符串，如 "x * 0.1", "x / 100", "(x - 32) * 5 / 9"
    output_format: str = ""     # 输出格式，如 "{:.2f}°C"
    
    def evaluate(self, value: Any) -> Any:
        """
        计算表达式
        在表达式中，x 代表原始字段值
        支持基本数学运算和一些常用函数
        """
        try:
            # 安全的表达式求值
            import math
            # 定义安全的命名空间
            safe_namespace = {
                'x': value,
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'int': int,
                'float': float,
                'pow': pow,
                'sqrt': math.sqrt,
                'log': math.log,
                'log10': math.log10,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
            }
            result = eval(self.expression, {"__builtins__": {}}, safe_namespace)
            return result
        except Exception:
            return value
    
    def format_result(self, value: Any) -> str:
        """格式化计算结果"""
        try:
            computed = self.evaluate(value)
            if self.output_format:
                return self.output_format.format(computed)
            return str(computed)
        except Exception:
            return str(value)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expression': self.expression,
            'output_format': self.output_format
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationExpression':
        return cls(
            expression=data.get('expression', 'x'),
            output_format=data.get('output_format', '')
        )


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
    # 字节序（仅对多字节类型有效）
    endianness: Endianness = Endianness.BIG
    # 锁定状态（锁定后不允许编辑）
    locked: bool = False
    
    # ============ 新增：长度偏置支持 ============
    # 实际长度 = 长度字段值 + length_offset
    # 例如：DLT645协议中，长度字段值不包含帧头帧尾，需要 offset
    length_offset: int = 0
    # 长度计算公式（高级用法，优先于 length_offset）
    # 例如："x + 2" 或 "x - 5"，其中 x 为长度字段值
    length_formula: Optional[str] = None
    
    # ============ 新增：位域支持 ============
    # 位域定义列表（用于在字段内提取多个位域）
    bit_fields: Optional[List[BitFieldDefinition]] = None
    
    # ============ 新增：条件字段支持 ============
    # 字段存在条件（满足条件时该字段才存在）
    condition: Optional[FieldCondition] = None
    
    # ============ 新增：计算表达式支持 ============
    # 计算表达式（用于对字段值进行转换）
    calculation: Optional[CalculationExpression] = None
    
    # ============ 新增：数值缩放支持（工业表计协议常用）============
    # 缩放公式: display_value = raw_value * multiplier + value_offset
    # 例如：温度传感器 raw=250, multiplier=0.1, value_offset=-40 => 显示 -15°C
    multiplier: float = 1.0           # 倍率，默认1（不缩放）
    value_offset: float = 0.0         # 值偏移，默认0（不偏移）
    unit: str = ""                    # 单位，如 "°C", "V", "A", "kWh"
    decimal_places: int = -1          # 小数位数，-1表示自动
    
    def calculate_actual_length(self, length_value: int) -> int:
        """
        计算实际长度
        
        Args:
            length_value: 长度字段的原始值
            
        Returns:
            计算后的实际长度
        """
        if self.length_formula:
            try:
                # 使用公式计算
                result = eval(self.length_formula, {"__builtins__": {}}, {'x': length_value})
                return int(result)
            except Exception:
                pass
        # 使用简单偏置
        return length_value + self.length_offset
    
    def is_multi_byte_type(self) -> bool:
        """判断是否为多字节类型"""
        # 对于数值类型，直接返回True
        if self.field_type in [
            FieldType.UINT16, FieldType.UINT32,
            FieldType.INT16, FieldType.INT32,
            FieldType.FLOAT, FieldType.DOUBLE
        ]:
            return True
        # 对于 BYTES 和 STRING，检查长度是否大于1
        if self.field_type in [FieldType.BYTES, FieldType.STRING]:
            return self.byte_count > 1
        return False
    
    def has_bit_fields(self) -> bool:
        """判断是否有位域定义"""
        return self.bit_fields is not None and len(self.bit_fields) > 0
    
    def is_conditional(self) -> bool:
        """判断是否是条件字段"""
        return self.condition is not None
    
    def has_calculation(self) -> bool:
        """判断是否有计算表达式"""
        return self.calculation is not None
    
    def has_scaling(self) -> bool:
        """判断是否需要缩放转换"""
        return self.multiplier != 1.0 or self.value_offset != 0.0
    
    def apply_scaling(self, value: Any) -> Any:
        """
        应用缩放转换
        公式: display_value = raw_value * multiplier + value_offset
        
        Args:
            value: 原始值（可以是int/float/str）
            
        Returns:
            缩放后的值
        """
        if not self.has_scaling():
            return value
        
        try:
            # 尝试转换为数值
            if isinstance(value, (int, float)):
                num_value = float(value)
            elif isinstance(value, str):
                # BCD等字符串类型也尝试转换
                num_value = float(value)
            else:
                return value
            
            # 应用缩放公式
            result = num_value * self.multiplier + self.value_offset
            return result
        except (ValueError, TypeError):
            return value
    
    def format_scaled_value(self, value: Any) -> str:
        """
        格式化缩放后的值（带单位）
        
        Args:
            value: 原始值
            
        Returns:
            格式化的字符串，如 "25.5°C"
        """
        scaled = self.apply_scaling(value)
        
        if isinstance(scaled, float):
            if self.decimal_places >= 0:
                # 使用指定的小数位数
                formatted = f"{scaled:.{self.decimal_places}f}"
            else:
                # 自动格式化，移除末尾的0
                formatted = f"{scaled:.6f}".rstrip('0').rstrip('.')
        else:
            formatted = str(scaled)
        
        # 添加单位
        if self.unit:
            formatted = f"{formatted}{self.unit}"
        
        return formatted

    def check_condition(self, parsed_fields: Dict[str, Any]) -> bool:
        """检查条件是否满足（无条件时返回True）"""
        if self.condition is None:
            return True
        return self.condition.evaluate(parsed_fields)
    
    def apply_calculation(self, value: Any) -> Any:
        """应用计算表达式"""
        if self.calculation is None:
            return value
        return self.calculation.evaluate(value)
    
    def format_calculated_value(self, value: Any) -> str:
        """格式化计算后的值"""
        if self.calculation is None:
            return str(value)
        return self.calculation.format_result(value)
    
    def extract_bit_fields(self, byte_value: int) -> Dict[str, Any]:
        """提取所有位域值"""
        result = {}
        if self.bit_fields:
            for bf in self.bit_fields:
                result[bf.name] = {
                    'value': bf.extract_value(byte_value),
                    'formatted': bf.format_value(bf.extract_value(byte_value)),
                    'description': bf.description
                }
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'name': self.name,
            'byte_count': self.byte_count,
            'field_type': self.field_type.value,
            'description': self.description,
            'order': self.order,
            'length_field': self.length_field,
            'locked': self.locked,
            'length_offset': self.length_offset
        }
        # 保存长度公式
        if self.length_formula:
            result['length_formula'] = self.length_formula
            
        # 只有多字节类型才保存字节序
        if self.is_multi_byte_type():
            result['endianness'] = self.endianness.value
        
        # 保存位域定义
        if self.bit_fields:
            result['bit_fields'] = [bf.to_dict() for bf in self.bit_fields]
        
        # 保存条件
        if self.condition:
            result['condition'] = self.condition.to_dict()
        
        # 保存计算表达式
        if self.calculation:
            result['calculation'] = self.calculation.to_dict()
        
        # 保存缩放配置（仅在非默认值时保存）
        if self.has_scaling():
            result['multiplier'] = self.multiplier
            result['value_offset'] = self.value_offset
        if self.unit:
            result['unit'] = self.unit
        if self.decimal_places >= 0:
            result['decimal_places'] = self.decimal_places
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldDefinition':
        """从字典创建"""
        field_type = FieldType(data.get('field_type', 'bytes'))
        # 解析字节序，默认为大端
        endianness = Endianness.BIG
        if 'endianness' in data:
            endianness = Endianness(data['endianness'])
        
        # 解析位域定义
        bit_fields = None
        if 'bit_fields' in data and data['bit_fields']:
            bit_fields = [BitFieldDefinition.from_dict(bf) for bf in data['bit_fields']]
        
        # 解析条件
        condition = None
        if 'condition' in data and data['condition']:
            condition = FieldCondition.from_dict(data['condition'])
        
        # 解析计算表达式
        calculation = None
        if 'calculation' in data and data['calculation']:
            calculation = CalculationExpression.from_dict(data['calculation'])
        
        return cls(
            name=data['name'],
            byte_count=data['byte_count'],
            field_type=field_type,
            description=data.get('description', ''),
            order=data.get('order', 0),
            length_field=data.get('length_field'),
            endianness=endianness,
            locked=data.get('locked', False),
            length_offset=data.get('length_offset', 0),
            length_formula=data.get('length_formula'),
            bit_fields=bit_fields,
            condition=condition,
            calculation=calculation,
            # 缩放配置
            multiplier=data.get('multiplier', 1.0),
            value_offset=data.get('value_offset', 0.0),
            unit=data.get('unit', ''),
            decimal_places=data.get('decimal_places', -1)
        )


@dataclass
class ProtocolConfig:
    """协议配置"""
    protocol_name: str = "默认协议"
    version: str = "1.0"
    description: str = ""
    file_path: Optional[str] = None  # 协议文件路径（用于历史记录）
    
    # 帧标识
    frame_header: str = "68"  # 十六进制字符串
    frame_tail: str = "16"    # 十六进制字符串
    
    # 帧长度配置（可选）
    frame_length: Optional[int] = None  # 固定帧长度（字节数），包括帧头帧尾。如果指定，将优先使用此长度而非查找帧尾
    length_field_name: Optional[str] = None  # 长度字段名称（如"整包长度"），用于从数据中读取帧长度
    
    # 校验配置
    checksum_config: ChecksumConfig = field(default_factory=ChecksumConfig)
    
    # 字段定义列表
    fields: List[FieldDefinition] = field(default_factory=list)
    
    # UI锁定状态
    basic_info_locked: bool = False  # 基本信息锁定状态
    checksum_locked: bool = False    # 校验配置锁定状态
    
    def __post_init__(self):
        """数据验证"""
        # 确保帧头帧尾有默认值
        if not self.frame_header:
            self.frame_header = "68"
        if not self.frame_tail:
            self.frame_tail = "16"
        
        # 确保帧头帧尾是有效的十六进制
        try:
            int(self.frame_header, 16)
            int(self.frame_tail, 16)
        except (ValueError, TypeError):
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
        result = {
            'protocol_name': self.protocol_name,
            'version': self.version,
            'description': self.description,
            'frame_header': self.frame_header,
            'frame_tail': self.frame_tail,
        }
        
        # 添加可选的帧配置字段
        if self.frame_length is not None:
            result['frame_length'] = self.frame_length
        if self.length_field_name is not None:
            result['length_field_name'] = self.length_field_name
        
        # 构建校验配置
        checksum_config = {
            'checksum_type': self.checksum_config.checksum_type.value,
            'position': self.checksum_config.position.value,
            'start_offset': self.checksum_config.start_offset,
            'end_offset': self.checksum_config.end_offset,
            'checksum_length': self.checksum_config.checksum_length
        }
        
        # 添加简化配置字段（如果存在）
        if self.checksum_config.checksum_position is not None:
            checksum_config['checksum_position'] = self.checksum_config.checksum_position
        if self.checksum_config.checksum_start is not None:
            checksum_config['checksum_start'] = self.checksum_config.checksum_start
        if self.checksum_config.checksum_end is not None:
            checksum_config['checksum_end'] = self.checksum_config.checksum_end
        # 添加校验码字节序
        checksum_config['checksum_endianness'] = self.checksum_config.checksum_endianness.value
        
        result['checksum_config'] = checksum_config
        result['fields'] = [f.to_dict() for f in self.fields]
        
        # 保存UI锁定状态
        result['basic_info_locked'] = self.basic_info_locked
        result['checksum_locked'] = self.checksum_locked
        
        return result
    
    @staticmethod
    def _convert_checksum_type(checksum_type_str: str) -> ChecksumType:
        """转换校验类型字符串为枚举（支持多种格式）"""
        # 转换为大写进行匹配
        type_upper = checksum_type_str.upper()
        
        # 映射表（只包含实际存在的枚举值）
        type_mapping = {
            'SUM': ChecksumType.SUM,
            '累加和': ChecksumType.SUM,
            'XOR': ChecksumType.XOR,
            '异或': ChecksumType.XOR,
            '异或校验': ChecksumType.XOR,
            'CRC16': ChecksumType.CRC16,
            'CRC32': ChecksumType.CRC32,
            'NONE': ChecksumType.NONE,
            '无校验': ChecksumType.NONE,
            '无': ChecksumType.NONE
        }
        
        # 查找匹配
        for key, value in type_mapping.items():
            if type_upper == key.upper() or checksum_type_str == key:
                return value
        
        # 如果都不匹配，尝试直接创建枚举
        try:
            return ChecksumType(checksum_type_str)
        except ValueError:
            # 默认返回无校验
            return ChecksumType.NONE
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolConfig':
        """从字典创建（用于JSON加载）"""
        checksum_data = data.get('checksum_config', {})
        
        # 转换校验类型（支持多种格式）
        checksum_type_str = checksum_data.get('checksum_type', '无校验')
        checksum_type = cls._convert_checksum_type(checksum_type_str)
        
        checksum_config = ChecksumConfig(
            checksum_type=checksum_type,
            position=ChecksumPosition(checksum_data.get('position', '帧尾前')),
            checksum_position=checksum_data.get('checksum_position'),  # 新字段：校验码绝对位置
            checksum_length=checksum_data.get('checksum_length', 1),
            checksum_start=checksum_data.get('checksum_start'),  # 新字段：校验计算起始位置
            checksum_end=checksum_data.get('checksum_end'),      # 新字段：校验计算结束位置
            checksum_endianness=Endianness(checksum_data.get('checksum_endianness', 'little')),  # 校验码字节序
            start_offset=checksum_data.get('start_offset', 0),   # 旧版兼容
            end_offset=checksum_data.get('end_offset', -1)       # 旧版兼容
        )
        
        fields = [FieldDefinition.from_dict(f) for f in data.get('fields', [])]
        
        return cls(
            protocol_name=data.get('protocol_name', '默认协议'),
            version=data.get('version', '1.0'),
            description=data.get('description', ''),
            frame_header=data['frame_header'],
            frame_tail=data['frame_tail'],
            frame_length=data.get('frame_length'),  # 可选的固定帧长度
            length_field_name=data.get('length_field_name'),  # 可选的长度字段名称
            checksum_config=checksum_config,
            fields=fields,
            basic_info_locked=data.get('basic_info_locked', False),
            checksum_locked=data.get('checksum_locked', False)
        )
