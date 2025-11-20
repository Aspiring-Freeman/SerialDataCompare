#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断校验范围问题"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.protocol import ProtocolConfig
from core.checksum import ChecksumValidator

def diagnose_checksum_range():
    """诊断校验范围配置"""
    
    # 读取协议配置
    protocol_file = project_root / "test_watermeter.json"
    print(f"读取协议文件: {protocol_file}")
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        protocol_dict = json.load(f)
    
    protocol = ProtocolConfig.from_dict(protocol_dict)
    
    print("\n=== 协议配置信息 ===")
    print(f"协议名称: {protocol.protocol_name}")
    print(f"帧头: 0x{protocol.frame_header}")
    print(f"帧尾: 0x{protocol.frame_tail}")
    print(f"固定帧长度: {protocol.frame_length}")
    
    print("\n=== 校验配置 ===")
    config = protocol.checksum_config
    print(f"校验类型: {config.checksum_type}")
    print(f"校验长度: {config.checksum_length}")
    
    print("\n--- 简化配置（绝对位置）---")
    print(f"checksum_position: {config.checksum_position}")
    print(f"checksum_start: {config.checksum_start}")
    print(f"checksum_end: {config.checksum_end}")
    
    print("\n--- 旧版配置（相对偏移）---")
    print(f"position: {config.position}")
    print(f"start_offset: {config.start_offset}")
    print(f"end_offset: {config.end_offset}")
    
    # 测试数据（106字节）
    hex_str = "68 AD 6A 01 D3 0E 8E 0D 0A 00 00 00 00 00 00 00 10 0E 00 00 01 01 01 01 38 36 32 31 31 38 30 36 39 34 34 30 35 37 33 34 36 30 31 31 33 32 38 36 34 35 32 36 34 33 38 39 38 36 31 31 32 34 32 30 37 30 32 32 39 34 39 37 36 33 10 01 01 01 10 0E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 01 01 00 00 00 01 06 94 16"
    data = bytes([int(b, 16) for b in hex_str.split()])
    
    print(f"\n=== 测试数据 ===")
    print(f"数据长度: {len(data)} 字节")
    print(f"帧头: 0x{data[0]:02X}")
    print(f"帧尾: 0x{data[-1]:02X}")
    print(f"位置104的值: 0x{data[104]:02X}")
    print(f"位置105的值: 0x{data[105]:02X}")
    
    # 检查校验逻辑会使用哪个配置
    print("\n=== 校验计算逻辑判断 ===")
    use_simplified = (config.checksum_position is not None or 
                     config.checksum_start is not None or 
                     config.checksum_end is not None)
    print(f"是否使用简化配置: {use_simplified}")
    
    if use_simplified:
        print("\n--- 简化配置计算 ---")
        checksum_pos = config.checksum_position
        calc_start = config.checksum_start if config.checksum_start is not None else 0
        calc_end = config.checksum_end if config.checksum_end is not None else checksum_pos
        
        print(f"校验码位置: {checksum_pos}")
        print(f"计算范围: data[{calc_start}:{calc_end}]")
        print(f"范围说明: 从位置{calc_start}到位置{calc_end-1}（不包含{calc_end}）")
        
        # 实际计算
        checksum_bytes = data[checksum_pos:checksum_pos + config.checksum_length]
        actual_checksum = int.from_bytes(checksum_bytes, byteorder='big')
        
        calc_data = data[calc_start:calc_end]
        expected_checksum = sum(calc_data) & 0xFF
        
        print(f"\n实际校验码: 0x{actual_checksum:02X} (位置{checksum_pos})")
        print(f"计算校验码: 0x{expected_checksum:02X}")
        print(f"计算的字节数: {len(calc_data)}")
        print(f"校验{'✓ 通过' if actual_checksum == expected_checksum else '✗ 失败'}")
        
        # 显示计算的字节范围
        print(f"\n计算范围的实际字节:")
        print(f"  起始: data[{calc_start}] = 0x{data[calc_start]:02X}")
        print(f"  结束: data[{calc_end-1}] = 0x{data[calc_end-1]:02X}")
        
    else:
        print("\n--- 旧版配置计算 ---")
        # 旧版逻辑
        header_len = len(bytes.fromhex(protocol.frame_header))
        tail_len = len(bytes.fromhex(protocol.frame_tail))
        
        start_pos = header_len + config.start_offset
        if config.end_offset < 0:
            # 负偏移从后往前数
            end_pos = len(data) - tail_len - config.checksum_length + config.end_offset + 1
        else:
            end_pos = header_len + config.end_offset
        
        print(f"帧头长度: {header_len}")
        print(f"帧尾长度: {tail_len}")
        print(f"start_offset: {config.start_offset} → 起始位置: {start_pos}")
        print(f"end_offset: {config.end_offset} → 结束位置: {end_pos}")
        print(f"计算范围: data[{start_pos}:{end_pos}]")
    
    print("\n=== GUI 中显示的信息 ===")
    print("当您在 GUI 中看到校验范围时，显示的是:")
    print(f"  - 简化配置: 从 {config.checksum_start} 到 {config.checksum_end}")
    print(f"  - 旧版配置: start_offset={config.start_offset}, end_offset={config.end_offset}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    diagnose_checksum_range()
