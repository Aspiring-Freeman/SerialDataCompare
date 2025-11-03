# -*- coding: utf-8 -*-
"""
协议管理模块
负责协议配置的保存、加载和验证
"""

import json
import os
from typing import Optional
from models import ProtocolConfig
from core.protocol_converter import ProtocolConverter


class ProtocolManager:
    """协议管理器"""
    
    @staticmethod
    def save_protocol(protocol: ProtocolConfig, file_path: str) -> bool:
        """
        保存协议配置到文件
        
        Args:
            protocol: 协议配置对象
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            data = protocol.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存协议失败: {e}")
            return False
    
    @staticmethod
    def load_protocol(file_path: str) -> Optional[ProtocolConfig]:
        """
        从文件加载协议配置（自动检测并转换格式）
        
        Args:
            file_path: 文件路径
            
        Returns:
            协议配置对象，如果失败返回None
        """
        try:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 使用转换器自动检测并转换格式
            protocol = ProtocolConverter.validate_and_convert(data)
            return protocol
        except Exception as e:
            print(f"加载协议失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def validate_protocol(protocol: ProtocolConfig) -> tuple[bool, str]:
        """
        验证协议配置是否有效
        
        Args:
            protocol: 协议配置对象
            
        Returns:
            (是否有效, 错误消息)
        """
        try:
            # 检查帧头
            if not protocol.frame_header:
                return False, "帧头不能为空"
            
            try:
                int(protocol.frame_header, 16)
            except ValueError:
                return False, "帧头不是有效的十六进制"
            
            # 检查帧尾
            if not protocol.frame_tail:
                return False, "帧尾不能为空"
            
            try:
                int(protocol.frame_tail, 16)
            except ValueError:
                return False, "帧尾不是有效的十六进制"
            
            # 检查字段
            if not protocol.fields:
                return False, "至少需要定义一个字段"
            
            # 检查字段名称唯一性
            field_names = [f.name for f in protocol.fields]
            if len(field_names) != len(set(field_names)):
                return False, "字段名称必须唯一"
            
            # 检查变长字段的长度字段是否存在
            for field in protocol.fields:
                if field.byte_count == 0 and field.length_field:
                    if field.length_field not in field_names:
                        return False, f"字段 {field.name} 的长度字段 {field.length_field} 不存在"
            
            return True, ""
            
        except Exception as e:
            return False, f"验证出错: {str(e)}"
    
    @staticmethod
    def get_default_protocol() -> ProtocolConfig:
        """
        获取默认协议配置
        
        Returns:
            默认协议配置
        """
        from models import FieldDefinition, FieldType, ChecksumConfig, ChecksumType, ChecksumPosition
        
        protocol = ProtocolConfig(
            protocol_name="默认协议",
            version="1.0",
            description="这是一个默认的协议配置示例",
            frame_header="68",
            frame_tail="16"
        )
        
        # 设置校验
        protocol.checksum_config = ChecksumConfig(
            checksum_type=ChecksumType.SUM,
            position=ChecksumPosition.BEFORE_TAIL,
            start_offset=0,
            end_offset=-1,
            checksum_length=1
        )
        
        # 添加默认字段
        protocol.add_field(FieldDefinition(
            name="地址",
            byte_count=1,
            field_type=FieldType.UINT8,
            description="设备地址"
        ))
        
        protocol.add_field(FieldDefinition(
            name="命令",
            byte_count=1,
            field_type=FieldType.UINT8,
            description="命令码"
        ))
        
        protocol.add_field(FieldDefinition(
            name="长度",
            byte_count=1,
            field_type=FieldType.UINT8,
            description="数据长度"
        ))
        
        protocol.add_field(FieldDefinition(
            name="数据",
            byte_count=0,  # 变长
            field_type=FieldType.BYTES,
            description="数据内容",
            length_field="长度"
        ))
        
        return protocol
