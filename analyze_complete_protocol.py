#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工业协议数据分析脚本
"""

import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.protocol import ProtocolConfig
from core.parser import DataParser

def main():
    # 完整的106字节数据帧
    data_hex = """
    68 AD 6A 00 C8 0E DE 0D 0B 00 00 00 00 00 00 00 10 0E 00 00 01 01 01 01 
    38 36 38 34 38 39 30 38 33 34 31 31 34 36 38 34 36 30 31 33 30 34 30 31 
    36 32 39 39 33 32 38 39 38 36 30 38 38 30 31 31 32 35 38 30 35 32 39 39 
    33 32 16 01 01 01 10 0E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
    01 01 01 00 00 00 01 00 E6 16
    """
    
    # 清理数据
    data_hex = data_hex.replace('\n', ' ').strip()
    data_bytes = bytes.fromhex(data_hex)
    
    print("=" * 80)
    print("工业通信器物协议完整数据分析")
    print("=" * 80)
    print(f"\n总字节数: {len(data_bytes)}")
    print(f"原始数据: {data_hex}")
    
    # 加载协议配置
    protocol_file = project_root / "protocol_industrial_fixed_v2.json"
    print(f"\n加载协议配置: {protocol_file}")
    
    try:
        with open(protocol_file, 'r', encoding='utf-8') as f:
            protocol_dict = json.load(f)
        
        protocol = ProtocolConfig.from_dict(protocol_dict)
        print(f"✓ 协议加载成功: {protocol.protocol_name} v{protocol.version}")
        
        # 创建解析器并解析
        parser = DataParser(protocol)
        
        # 将字节数据转换为十六进制字符串
        hex_str = ' '.join(f'{b:02X}' for b in data_bytes)
        result = parser.parse(hex_str)
        
        # 显示解析结果
        if result and result.frames:
            print(f"\n检测到 {len(result.frames)} 个数据帧")
            print(f"有效帧数: {result.get_valid_frames()}")
            print(f"错误帧数: {result.get_error_frames()}")
            
            for i, frame in enumerate(result.frames, 1):
                print(f"\n{'='*80}")
                print(f"数据帧 #{i}")
                print(f"位置范围: {frame.start_position} - {frame.end_position} ({len(frame.raw_data)} 字节)")
                print(f"\n原始数据:")
                
                # 格式化输出原始数据（每行16字节）
                frame_bytes = frame.raw_data
                for j in range(0, len(frame_bytes), 16):
                    hex_line = ' '.join(f'{b:02X}' for b in frame_bytes[j:j+16])
                    print(f"  {hex_line}")
                
                # 字段解析
                print(f"\n字段解析:")
                for field_name, value in frame.fields.items():
                    # 格式化显示
                    if isinstance(value, bytes):
                        value_str = ' '.join(f'{b:02X}' for b in value)
                        print(f"  {field_name}: {value_str}")
                    else:
                        print(f"  {field_name}: {value}")
                
                # 校验信息
                print(f"\n校验信息:")
                if frame.checksum_valid is not None:
                    status = "✓ 成功" if frame.checksum_valid else "✗ 失败"
                    print(f"  校验状态: {status}")
                    if frame.expected_checksum is not None:
                        print(f"  期望校验码: 0x{frame.expected_checksum:02X}")
                    if frame.actual_checksum is not None:
                        print(f"  实际校验码: 0x{frame.actual_checksum:02X}")
                    if frame.has_error:
                        print(f"  ⚠ {frame.error_message}")
                else:
                    print(f"  无校验")
        else:
            print(f"\n❌ 解析失败: 未找到数据帧")
    
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 80)
    return 0

if __name__ == '__main__':
    sys.exit(main())
