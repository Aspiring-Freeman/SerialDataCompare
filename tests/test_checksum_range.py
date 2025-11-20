#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试校验范围计算"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.protocol import ChecksumConfig, ChecksumType

def test_checksum_range():
    """测试校验范围计算"""
    
    # 模拟一个 106 字节的帧
    frame_data = bytes(range(106))  # 0x00 到 0x69
    
    # 配置 1: 简化配置
    config1 = ChecksumConfig(
        checksum_type=ChecksumType.SUM,
        checksum_length=1,
        checksum_position=104,
        checksum_start=0,
        checksum_end=104
    )
    
    print("=== 测试简化配置 ===")
    print(f"checksum_position: {config1.checksum_position}")
    print(f"checksum_start: {config1.checksum_start}")
    print(f"checksum_end: {config1.checksum_end}")
    print()
    
    # 模拟校验逻辑
    if config1.checksum_start is not None and config1.checksum_end is not None:
        data_start = config1.checksum_start
        data_end = config1.checksum_end
        print(f"✓ 使用绝对位置范围")
        print(f"  数据起始: {data_start}")
        print(f"  数据结束: {data_end}")
        print(f"  校验范围: frame_data[{data_start}:{data_end}]")
        print(f"  范围长度: {data_end - data_start} 字节")
        
        data_to_check = frame_data[data_start:data_end]
        print(f"  实际数据: {' '.join(f'{b:02X}' for b in data_to_check[:10])}... (前10字节)")
        
        checksum_value = sum(data_to_check) & 0xFF
        print(f"  计算校验: 0x{checksum_value:02X}")
        
        checksum_pos = config1.checksum_position
        print(f"\n  校验码位置: {checksum_pos}")
        print(f"  校验码值: 0x{frame_data[checksum_pos]:02X}")
    
    print("\n" + "="*60 + "\n")
    
    # 配置 2: 旧版配置
    config2 = ChecksumConfig(
        checksum_type=ChecksumType.SUM,
        checksum_length=1,
        position="帧尾前",
        start_offset=0,
        end_offset=-1
    )
    
    print("=== 测试旧版配置 ===")
    print(f"position: {config2.position}")
    print(f"start_offset: {config2.start_offset}")
    print(f"end_offset: {config2.end_offset}")
    print()
    
    # 模拟旧版逻辑
    checksum_start = len(frame_data) - 1 - config2.checksum_length
    print(f"校验码起始位置: {checksum_start}")
    
    if config2.start_offset == -1:
        data_start = 0
    else:
        data_start = 1 + config2.start_offset
    
    if config2.end_offset == 0:
        data_end = checksum_start
    elif config2.end_offset == -1:
        data_end = len(frame_data) - 1
    elif config2.end_offset < 0:
        data_end = len(frame_data) + config2.end_offset + 1
    else:
        if config2.end_offset < 100:
            data_end = data_start + config2.end_offset
        else:
            data_end = config2.end_offset
    
    print(f"✓ 使用旧版offset配置")
    print(f"  数据起始: {data_start}")
    print(f"  数据结束: {data_end}")
    print(f"  校验范围: frame_data[{data_start}:{data_end}]")
    print(f"  范围长度: {data_end - data_start} 字节")
    
    data_to_check = frame_data[data_start:data_end]
    print(f"  实际数据: {' '.join(f'{b:02X}' for b in data_to_check[:10])}... (前10字节)")
    
    checksum_value = sum(data_to_check) & 0xFF
    print(f"  计算校验: 0x{checksum_value:02X}")
    
    print("\n" + "="*60 + "\n")
    
    # 对比
    print("=== 对比结果 ===")
    config1_range = f"[{config1.checksum_start}:{config1.checksum_end}]"
    
    # 旧版计算
    checksum_start_old = len(frame_data) - 1 - config2.checksum_length
    if config2.start_offset == -1:
        data_start_old = 0
    else:
        data_start_old = 1 + config2.start_offset
    if config2.end_offset == -1:
        data_end_old = len(frame_data) - 1
    else:
        data_end_old = checksum_start_old
    
    config2_range = f"[{data_start_old}:{data_end_old}]"
    
    print(f"简化配置范围: {config1_range} = {config1.checksum_end - config1.checksum_start} 字节")
    print(f"旧版配置范围: {config2_range} = {data_end_old - data_start_old} 字节")
    
    if config1_range == config2_range:
        print("✓ 两种配置范围一致")
    else:
        print("✗ 两种配置范围不一致！")

if __name__ == "__main__":
    test_checksum_range()
