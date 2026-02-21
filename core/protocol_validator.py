# -*- coding: utf-8 -*-
"""
协议JSON格式验证模块
使用JSON Schema验证协议配置文件的正确性
"""

import json
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

# JSON Schema 定义协议格式
PROTOCOL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SerialDataCompare Protocol Schema",
    "description": "串口数据比较工具协议配置格式",
    "type": "object",
    "required": ["protocol_name", "frame_header", "frame_tail", "fields"],
    "properties": {
        "protocol_name": {
            "type": "string",
            "description": "协议名称",
            "minLength": 1,
            "maxLength": 100
        },
        "version": {
            "type": "string",
            "description": "协议版本",
            "pattern": "^[0-9]+\\.[0-9]+(\\.[0-9]+)?$",
            "default": "1.0"
        },
        "schema_version": {
            "type": "string",
            "description": "Schema版本，用于兼容性检查",
            "default": "1.0"
        },
        "description": {
            "type": "string",
            "description": "协议描述"
        },
        "frame_header": {
            "type": "string",
            "description": "帧头（十六进制字符串）",
            "pattern": "^[0-9A-Fa-f]+$"
        },
        "frame_tail": {
            "type": "string",
            "description": "帧尾（十六进制字符串）",
            "pattern": "^[0-9A-Fa-f]+$"
        },
        "frame_length": {
            "type": "integer",
            "description": "固定帧长度（字节）",
            "minimum": 1
        },
        "length_field_name": {
            "type": "string",
            "description": "长度字段名称"
        },
        "checksum_config": {
            "type": "object",
            "description": "校验配置",
            "properties": {
                "checksum_type": {
                    "type": "string",
                    "description": "校验类型"
                },
                "position": {
                    "type": "string",
                    "enum": ["帧尾前", "帧尾后", "自定义位置"]
                },
                "checksum_position": {
                    "type": "integer",
                    "description": "校验码位置"
                },
                "checksum_length": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                    "default": 1
                },
                "checksum_start": {
                    "type": "integer",
                    "description": "校验计算起始位置"
                },
                "checksum_end": {
                    "type": "integer",
                    "description": "校验计算结束位置"
                },
                "checksum_endianness": {
                    "type": "string",
                    "enum": ["big", "little"],
                    "default": "little"
                },
                "crc_params": {
                    "type": "object",
                    "description": "自定义CRC参数",
                    "properties": {
                        "poly": {"type": "integer"},
                        "init": {"type": "integer"},
                        "ref_in": {"type": "boolean"},
                        "ref_out": {"type": "boolean"},
                        "xor_out": {"type": "integer"},
                        "width": {"type": "integer", "enum": [8, 16, 32]}
                    }
                }
            }
        },
        "fields": {
            "type": "array",
            "description": "字段定义列表",
            "items": {
                "$ref": "#/definitions/field"
            }
        }
    },
    "definitions": {
        "field": {
            "type": "object",
            "required": ["name", "byte_count", "field_type"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "字段名称",
                    "minLength": 1,
                    "maxLength": 50
                },
                "byte_count": {
                    "type": "integer",
                    "description": "字节数（0表示变长）",
                    "minimum": 0
                },
                "field_type": {
                    "type": "string",
                    "description": "字段类型",
                    "enum": [
                        "uint8", "uint16", "uint32",
                        "int8", "int16", "int32",
                        "float", "double",
                        "bytes", "string",
                        "bcd", "bcd_rev", "bcd_datetime"
                    ]
                },
                "description": {
                    "type": "string",
                    "description": "字段描述"
                },
                "order": {
                    "type": "integer",
                    "description": "字段顺序"
                },
                "length_field": {
                    "type": "string",
                    "description": "长度字段名（变长字段）"
                },
                "endianness": {
                    "type": "string",
                    "enum": ["big", "little"],
                    "default": "big"
                },
                "locked": {
                    "type": "boolean",
                    "default": False
                },
                "length_offset": {
                    "type": "integer",
                    "description": "长度偏移",
                    "default": 0
                },
                "length_formula": {
                    "type": "string",
                    "description": "长度计算公式"
                },
                # 缩放配置
                "multiplier": {
                    "type": "number",
                    "description": "缩放倍率",
                    "default": 1.0
                },
                "value_offset": {
                    "type": "number",
                    "description": "值偏移",
                    "default": 0.0
                },
                "unit": {
                    "type": "string",
                    "description": "单位（如°C, V, A）"
                },
                "decimal_places": {
                    "type": "integer",
                    "description": "小数位数",
                    "minimum": -1,
                    "default": -1
                },
                # 位域配置
                "bit_fields": {
                    "type": "array",
                    "description": "位域定义",
                    "items": {
                        "$ref": "#/definitions/bit_field"
                    }
                },
                # 条件配置
                "condition": {
                    "$ref": "#/definitions/condition"
                },
                # 计算表达式
                "calculation": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                        "output_format": {"type": "string"}
                    }
                }
            }
        },
        "bit_field": {
            "type": "object",
            "required": ["name", "start_bit", "bit_count"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "位域名称"
                },
                "start_bit": {
                    "type": "integer",
                    "description": "起始位（从LSB开始）",
                    "minimum": 0,
                    "maximum": 31
                },
                "bit_count": {
                    "type": "integer",
                    "description": "位数",
                    "minimum": 1,
                    "maximum": 32
                },
                "description": {
                    "type": "string"
                },
                "display_format": {
                    "type": "string",
                    "enum": ["hex", "binary", "decimal", ""]
                },
                "value_map": {
                    "type": "object",
                    "description": "值映射表"
                }
            }
        },
        "condition": {
            "type": "object",
            "required": ["field_name", "operator", "value"],
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "依赖的字段名"
                },
                "operator": {
                    "type": "string",
                    "description": "操作符",
                    "enum": ["==", "!=", ">", "<", ">=", "<=", "in", "not_in", "&", "!&"]
                },
                "value": {
                    "description": "比较值"
                }
            }
        }
    }
}


class ValidationSeverity(Enum):
    """验证问题严重级别"""
    ERROR = "error"         # 致命错误，无法加载
    WARNING = "warning"     # 警告，可以加载但可能有问题
    INFO = "info"           # 信息提示，建议优化


@dataclass
class ValidationError:
    """验证错误信息"""
    path: str           # 错误位置路径，如 "fields[0].name"
    message: str        # 错误消息
    value: Any = None   # 问题值
    severity: ValidationSeverity = ValidationSeverity.ERROR  # 严重级别


class ProtocolValidator:
    """协议配置验证器"""
    
    # 当前支持的Schema版本
    CURRENT_SCHEMA_VERSION = "1.0"
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        验证协议配置数据
        
        Args:
            data: 协议配置字典
            
        Returns:
            (is_valid, errors) 元组
        """
        errors = []
        
        # 1. 检查必需字段
        required_fields = ["protocol_name", "frame_header", "frame_tail", "fields"]
        for field in required_fields:
            if field not in data:
                errors.append(ValidationError(
                    path=field,
                    message=f"缺少必需字段: {field}"
                ))
        
        if errors:
            return False, errors
        
        # 2. 验证协议名称
        if not isinstance(data["protocol_name"], str) or not data["protocol_name"].strip():
            errors.append(ValidationError(
                path="protocol_name",
                message="协议名称不能为空",
                value=data.get("protocol_name")
            ))
        
        # 3. 验证帧头帧尾（十六进制格式）
        for field_name in ["frame_header", "frame_tail"]:
            value = data.get(field_name, "")
            if not cls._is_valid_hex_string(value):
                errors.append(ValidationError(
                    path=field_name,
                    message=f"{field_name} 必须是有效的十六进制字符串",
                    value=value
                ))
        
        # 4. 验证字段列表
        fields = data.get("fields", [])
        if not isinstance(fields, list):
            errors.append(ValidationError(
                path="fields",
                message="fields 必须是数组",
                value=type(fields).__name__
            ))
        else:
            # 验证每个字段
            field_names = set()
            for i, field in enumerate(fields):
                field_errors = cls._validate_field(field, i, field_names)
                errors.extend(field_errors)
                if "name" in field:
                    field_names.add(field["name"])
        
        # 5. 验证校验配置
        if "checksum_config" in data:
            checksum_errors = cls._validate_checksum_config(data["checksum_config"])
            errors.extend(checksum_errors)
        
        # 6. 验证frame_length
        if "frame_length" in data:
            if not isinstance(data["frame_length"], int) or data["frame_length"] < 1:
                errors.append(ValidationError(
                    path="frame_length",
                    message="frame_length 必须是正整数",
                    value=data.get("frame_length")
                ))
        
        # 7. 版本兼容性检查
        schema_version = data.get("schema_version", "1.0")
        if not cls._is_compatible_version(schema_version):
            errors.append(ValidationError(
                path="schema_version",
                message=f"Schema版本 {schema_version} 可能不兼容当前版本 {cls.CURRENT_SCHEMA_VERSION}",
                value=schema_version,
                severity=ValidationSeverity.WARNING
            ))
        
        # 8. 检查是否缺少可选但推荐的字段
        if "description" not in data:
            errors.append(ValidationError(
                path="description",
                message="建议添加协议描述信息",
                severity=ValidationSeverity.INFO
            ))
        if "version" not in data:
            errors.append(ValidationError(
                path="version",
                message="建议添加协议版本号",
                severity=ValidationSeverity.INFO
            ))
        
        # 判断是否有效：只看 ERROR 级别
        has_errors = any(e.severity == ValidationSeverity.ERROR for e in errors)
        return not has_errors, errors
    
    @classmethod
    def _validate_field(cls, field: Dict[str, Any], index: int, existing_names: set) -> List[ValidationError]:
        """验证单个字段定义"""
        errors = []
        path_prefix = f"fields[{index}]"
        
        # 必需字段
        if "name" not in field:
            errors.append(ValidationError(
                path=f"{path_prefix}.name",
                message="字段缺少 name 属性"
            ))
        elif not isinstance(field["name"], str) or not field["name"].strip():
            errors.append(ValidationError(
                path=f"{path_prefix}.name",
                message="字段名称不能为空",
                value=field.get("name")
            ))
        elif field["name"] in existing_names:
            errors.append(ValidationError(
                path=f"{path_prefix}.name",
                message=f"字段名称重复: {field['name']}",
                value=field["name"]
            ))
        
        if "byte_count" not in field:
            errors.append(ValidationError(
                path=f"{path_prefix}.byte_count",
                message="字段缺少 byte_count 属性"
            ))
        elif not isinstance(field["byte_count"], int) or field["byte_count"] < 0:
            errors.append(ValidationError(
                path=f"{path_prefix}.byte_count",
                message="byte_count 必须是非负整数",
                value=field.get("byte_count")
            ))
        
        if "field_type" not in field:
            errors.append(ValidationError(
                path=f"{path_prefix}.field_type",
                message="字段缺少 field_type 属性"
            ))
        else:
            valid_types = [
                "uint8", "uint16", "uint32", "int8", "int16", "int32",
                "float", "double", "bytes", "string", "bcd", "bcd_rev", "bcd_datetime"
            ]
            if field["field_type"] not in valid_types:
                errors.append(ValidationError(
                    path=f"{path_prefix}.field_type",
                    message=f"无效的字段类型: {field['field_type']}，有效类型: {', '.join(valid_types)}",
                    value=field["field_type"]
                ))
        
        # 验证字节序
        if "endianness" in field:
            if field["endianness"] not in ["big", "little"]:
                errors.append(ValidationError(
                    path=f"{path_prefix}.endianness",
                    message="endianness 必须是 'big' 或 'little'",
                    value=field["endianness"]
                ))
        
        # 验证缩放参数
        if "multiplier" in field:
            if not isinstance(field["multiplier"], (int, float)):
                errors.append(ValidationError(
                    path=f"{path_prefix}.multiplier",
                    message="multiplier 必须是数字",
                    value=field["multiplier"]
                ))
        
        if "value_offset" in field:
            if not isinstance(field["value_offset"], (int, float)):
                errors.append(ValidationError(
                    path=f"{path_prefix}.value_offset",
                    message="value_offset 必须是数字",
                    value=field["value_offset"]
                ))
        
        if "decimal_places" in field:
            if not isinstance(field["decimal_places"], int) or field["decimal_places"] < -1:
                errors.append(ValidationError(
                    path=f"{path_prefix}.decimal_places",
                    message="decimal_places 必须是 >= -1 的整数",
                    value=field["decimal_places"]
                ))
        
        # 验证位域
        if "bit_fields" in field:
            bf_errors = cls._validate_bit_fields(field["bit_fields"], path_prefix)
            errors.extend(bf_errors)
        
        # 验证条件
        if "condition" in field:
            cond_errors = cls._validate_condition(field["condition"], path_prefix)
            errors.extend(cond_errors)
        
        return errors
    
    @classmethod
    def _validate_bit_fields(cls, bit_fields: List, path_prefix: str) -> List[ValidationError]:
        """验证位域定义列表"""
        errors = []
        
        if not isinstance(bit_fields, list):
            errors.append(ValidationError(
                path=f"{path_prefix}.bit_fields",
                message="bit_fields 必须是数组"
            ))
            return errors
        
        for i, bf in enumerate(bit_fields):
            bf_path = f"{path_prefix}.bit_fields[{i}]"
            
            if "name" not in bf:
                errors.append(ValidationError(
                    path=f"{bf_path}.name",
                    message="位域缺少 name 属性"
                ))
            
            if "start_bit" not in bf:
                errors.append(ValidationError(
                    path=f"{bf_path}.start_bit",
                    message="位域缺少 start_bit 属性"
                ))
            elif not isinstance(bf["start_bit"], int) or bf["start_bit"] < 0:
                errors.append(ValidationError(
                    path=f"{bf_path}.start_bit",
                    message="start_bit 必须是非负整数",
                    value=bf["start_bit"]
                ))
            
            if "bit_count" not in bf:
                errors.append(ValidationError(
                    path=f"{bf_path}.bit_count",
                    message="位域缺少 bit_count 属性"
                ))
            elif not isinstance(bf["bit_count"], int) or bf["bit_count"] < 1:
                errors.append(ValidationError(
                    path=f"{bf_path}.bit_count",
                    message="bit_count 必须是正整数",
                    value=bf["bit_count"]
                ))
        
        return errors
    
    @classmethod
    def _validate_condition(cls, condition: Dict, path_prefix: str) -> List[ValidationError]:
        """验证条件定义"""
        errors = []
        cond_path = f"{path_prefix}.condition"
        
        if not isinstance(condition, dict):
            errors.append(ValidationError(
                path=cond_path,
                message="condition 必须是对象"
            ))
            return errors
        
        if "field_name" not in condition:
            errors.append(ValidationError(
                path=f"{cond_path}.field_name",
                message="条件缺少 field_name 属性"
            ))
        
        if "operator" not in condition:
            errors.append(ValidationError(
                path=f"{cond_path}.operator",
                message="条件缺少 operator 属性"
            ))
        else:
            valid_operators = ["==", "!=", ">", "<", ">=", "<=", "in", "not_in", "&", "!&"]
            if condition["operator"] not in valid_operators:
                errors.append(ValidationError(
                    path=f"{cond_path}.operator",
                    message=f"无效的操作符: {condition['operator']}",
                    value=condition["operator"]
                ))
        
        if "value" not in condition:
            errors.append(ValidationError(
                path=f"{cond_path}.value",
                message="条件缺少 value 属性"
            ))
        
        return errors
    
    @classmethod
    def _validate_checksum_config(cls, config: Dict) -> List[ValidationError]:
        """验证校验配置"""
        errors = []
        
        if not isinstance(config, dict):
            errors.append(ValidationError(
                path="checksum_config",
                message="checksum_config 必须是对象"
            ))
            return errors
        
        # 验证校验长度
        if "checksum_length" in config:
            length = config["checksum_length"]
            if not isinstance(length, int) or length < 1 or length > 4:
                errors.append(ValidationError(
                    path="checksum_config.checksum_length",
                    message="checksum_length 必须是 1-4 之间的整数",
                    value=length
                ))
        
        # 验证字节序
        if "checksum_endianness" in config:
            if config["checksum_endianness"] not in ["big", "little"]:
                errors.append(ValidationError(
                    path="checksum_config.checksum_endianness",
                    message="checksum_endianness 必须是 'big' 或 'little'",
                    value=config["checksum_endianness"]
                ))
        
        # 验证CRC参数
        if "crc_params" in config:
            crc = config["crc_params"]
            if isinstance(crc, dict):
                if "width" in crc and crc["width"] not in [8, 16, 32]:
                    errors.append(ValidationError(
                        path="checksum_config.crc_params.width",
                        message="CRC width 必须是 8, 16 或 32",
                        value=crc["width"]
                    ))
        
        return errors
    
    @staticmethod
    def _is_valid_hex_string(value: str) -> bool:
        """检查是否为有效的十六进制字符串"""
        if not isinstance(value, str) or not value:
            return False
        try:
            int(value, 16)
            return len(value) % 2 == 0 or len(value) == 1
        except ValueError:
            return False
    
    @staticmethod
    def _is_compatible_version(version: str) -> bool:
        """检查版本兼容性"""
        try:
            major, minor = version.split(".")[:2]
            current_major, current_minor = ProtocolValidator.CURRENT_SCHEMA_VERSION.split(".")[:2]
            # 主版本号必须相同
            return major == current_major
        except (ValueError, AttributeError):
            return True  # 版本格式不正确时不阻止加载
    
    @classmethod
    def format_errors(cls, errors: List[ValidationError]) -> str:
        """格式化错误信息为可读字符串"""
        if not errors:
            return "验证通过"
        
        lines = [f"发现 {len(errors)} 个问题："]
        for i, err in enumerate(errors, 1):
            if err.value is not None:
                lines.append(f"  {i}. [{err.path}] {err.message} (值: {err.value})")
            else:
                lines.append(f"  {i}. [{err.path}] {err.message}")
        
        return "\n".join(lines)
    
    @classmethod
    def validate_file(cls, file_path: str) -> Tuple[bool, str]:
        """
        验证协议文件
        
        Args:
            file_path: 协议文件路径
            
        Returns:
            (is_valid, message) 元组
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误: {str(e)}"
        except FileNotFoundError:
            return False, f"文件不存在: {file_path}"
        except Exception as e:
            return False, f"读取文件失败: {str(e)}"
        
        is_valid, errors = cls.validate(data)
        return is_valid, cls.format_errors(errors)
