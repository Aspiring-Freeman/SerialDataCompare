#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试保存和加载简化配置"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.protocol import ProtocolConfig, ChecksumConfig, ChecksumType, ChecksumPosition, FieldDefinition, FieldType
from core.protocol_manager import ProtocolManager

def test_save_load_simplified_config():
    """测试保存和加载简化配置"""
    print("=== 测试保存和加载简化配置 ===\n")
    
    # 创建一个使用简化配置的协议
    checksum_config = ChecksumConfig(
        checksum_type=ChecksumType.SUM,
        position=ChecksumPosition.BEFORE_TAIL,
        start_offset=0,
        end_offset=-1,
        checksum_length=1,
        # 简化配置字段
        checksum_position=104,
        checksum_start=0,
        checksum_end=104
    )
    
    protocol = ProtocolConfig(
        protocol_name="测试水表协议",
        version="1.0",
        description="测试简化配置保存和加载",
        frame_header="68",
        frame_tail="16",
        frame_length=106,  # 固定帧长度
        checksum_config=checksum_config,
        fields=[
            FieldDefinition(
                name="设备地址",
                byte_count=1,
                field_type=FieldType.UINT8,
                description="设备地址",
                order=0
            )
        ]
    )
    
    print("1. 原始协议配置:")
    print(f"   - protocol_name: {protocol.protocol_name}")
    print(f"   - frame_length: {protocol.frame_length}")
    print(f"   - checksum_position: {protocol.checksum_config.checksum_position}")
    print(f"   - checksum_start: {protocol.checksum_config.checksum_start}")
    print(f"   - checksum_end: {protocol.checksum_config.checksum_end}")
    
    # 保存到文件
    test_file = project_root / "test_watermeter.json"
    print(f"\n2. 保存到文件: {test_file}")
    
    success = ProtocolManager.save_protocol(protocol, str(test_file))
    if success:
        print("   ✓ 保存成功")
    else:
        print("   ✗ 保存失败")
        return False
    
    # 读取 JSON 内容查看
    print("\n3. 检查保存的 JSON 内容:")
    with open(test_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    
    print(f"   - frame_length 存在: {'frame_length' in saved_data}")
    if 'frame_length' in saved_data:
        print(f"     值: {saved_data['frame_length']}")
    
    print(f"   - checksum_config.checksum_position 存在: {'checksum_position' in saved_data.get('checksum_config', {})}")
    if 'checksum_position' in saved_data.get('checksum_config', {}):
        print(f"     值: {saved_data['checksum_config']['checksum_position']}")
    
    print(f"   - checksum_config.checksum_start 存在: {'checksum_start' in saved_data.get('checksum_config', {})}")
    if 'checksum_start' in saved_data.get('checksum_config', {}):
        print(f"     值: {saved_data['checksum_config']['checksum_start']}")
    
    print(f"   - checksum_config.checksum_end 存在: {'checksum_end' in saved_data.get('checksum_config', {})}")
    if 'checksum_end' in saved_data.get('checksum_config', {}):
        print(f"     值: {saved_data['checksum_config']['checksum_end']}")
    
    # 加载回来
    print("\n4. 从文件加载:")
    loaded_protocol = ProtocolManager.load_protocol(str(test_file))
    
    if loaded_protocol:
        print("   ✓ 加载成功")
        print(f"\n5. 加载后的协议配置:")
        print(f"   - protocol_name: {loaded_protocol.protocol_name}")
        print(f"   - frame_length: {loaded_protocol.frame_length}")
        print(f"   - checksum_position: {loaded_protocol.checksum_config.checksum_position}")
        print(f"   - checksum_start: {loaded_protocol.checksum_config.checksum_start}")
        print(f"   - checksum_end: {loaded_protocol.checksum_config.checksum_end}")
        
        # 验证
        print("\n6. 验证结果:")
        checks = [
            ("frame_length", protocol.frame_length, loaded_protocol.frame_length),
            ("checksum_position", protocol.checksum_config.checksum_position, 
             loaded_protocol.checksum_config.checksum_position),
            ("checksum_start", protocol.checksum_config.checksum_start, 
             loaded_protocol.checksum_config.checksum_start),
            ("checksum_end", protocol.checksum_config.checksum_end, 
             loaded_protocol.checksum_config.checksum_end),
        ]
        
        all_passed = True
        for field_name, original, loaded in checks:
            match = original == loaded
            status = "✓" if match else "✗"
            print(f"   {status} {field_name}: {original} == {loaded} ? {match}")
            if not match:
                all_passed = False
        
        print("\n" + "="*60)
        if all_passed:
            print("✅ 所有测试通过！简化配置已正确保存和加载。")
        else:
            print("❌ 测试失败！部分字段未正确保存或加载。")
        print("="*60)
        
        return all_passed
    else:
        print("   ✗ 加载失败")
        return False

if __name__ == "__main__":
    success = test_save_load_simplified_config()
    sys.exit(0 if success else 1)
