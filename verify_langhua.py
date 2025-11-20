#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 Langhua 协议配置是否正确"""

import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.protocol import ProtocolConfig
from core.parser import DataParser

def main():
    # 加载 Langhua 协议配置
    protocol_file = project_root / "document/Protocol_json_format/Langhua/Langhua.json"
    print(f"加载协议文件: {protocol_file}")
    
    with open(protocol_file, 'r', encoding='utf-8') as f:
        protocol_dict = json.load(f)
    
    protocol = ProtocolConfig.from_dict(protocol_dict)
    print(f"\n协议名称: {protocol.protocol_name}")
    print(f"帧长度: {protocol.frame_length}")
    print(f"校验配置:")
    print(f"  - 校验类型: {protocol.checksum_config.checksum_type}")
    print(f"  - 校验位置: {protocol.checksum_config.checksum_position}")
    print(f"  - 校验起始: {protocol.checksum_config.checksum_start}")
    print(f"  - 校验结束: {protocol.checksum_config.checksum_end}")
    print(f"  - 校验长度: {protocol.checksum_config.checksum_length}")
    
    # 用户提供的失败帧数据
    hex_str = "68 AD 6A 01 D3 0E 8E 0D 0A 00 00 00 00 00 00 00 10 0E 00 00 01 01 01 01 38 36 32 31 31 38 30 36 39 34 34 30 35 37 33 34 36 30 31 31 33 32 38 36 34 35 32 36 34 33 38 39 38 36 31 31 32 34 32 30 37 30 32 32 39 34 39 37 36 33 10 01 01 01 10 0E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 01 01 00 00 00 01 06 94 16"
    data = bytes([int(b, 16) for b in hex_str.split()])
    
    print(f"\n数据长度: {len(data)} 字节")
    print(f"数据: {data.hex(' ').upper()}")
    
    # 创建解析器并解析
    parser = DataParser(protocol)
    parse_result = parser.parse(data)
    
    print(f"\n解析结果:")
    print(f"  - 成功: {parse_result.success}")
    print(f"  - 消息: {parse_result.message}")
    print(f"  - 解析帧数: {len(parse_result.frames)}")
    
    if parse_result.frames:
        frame = parse_result.frames[0]
        print(f"\n第一帧详情:")
        print(f"  - 起始位置: {frame.start_position}")
        print(f"  - 结束位置: {frame.end_position}")
        print(f"  - 帧长度: {len(frame.raw_data)} 字节")
        print(f"  - 校验状态: {frame.checksum_status}")
        
        if frame.checksum_info:
            print(f"\n校验信息:")
            print(f"  - 期望值: 0x{frame.checksum_info.get('expected', 'N/A'):02X}")
            print(f"  - 实际值: 0x{frame.checksum_info.get('actual', 'N/A'):02X}")
            print(f"  - 校验通过: {frame.checksum_info.get('valid', False)}")
        
        print(f"\n解析字段数: {len(frame.fields)}")
        # 显示前几个字段
        for i, (field_name, field_value) in enumerate(frame.fields.items()):
            if i < 10:  # 只显示前10个字段
                print(f"  - {field_name}: {field_value}")
            elif i == 10:
                print(f"  ... (共 {len(frame.fields)} 个字段)")
                break
    
    # 总结
    print("\n" + "="*60)
    if parse_result.success and parse_result.frames:
        frame = parse_result.frames[0]
        if frame.checksum_status == "valid":
            print("✓ 验证成功！协议配置正确，校验通过。")
        else:
            print("✗ 警告：帧解析成功但校验未通过。")
            if frame.checksum_info:
                print(f"  期望: 0x{frame.checksum_info.get('expected', 0):02X}, "
                      f"实际: 0x{frame.checksum_info.get('actual', 0):02X}")
    else:
        print("✗ 验证失败：无法正确解析帧。")
    print("="*60)

if __name__ == "__main__":
    main()
