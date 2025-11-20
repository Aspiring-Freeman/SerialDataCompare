#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试协议格式转换功能
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.protocol_converter import ProtocolConverter
from core.protocol_manager import ProtocolManager


def test_standard_format():
    """测试标准格式加载"""
    print("=" * 60)
    print("测试1: 标准格式")
    print("=" * 60)
    
    file_path = "protocol_example.json"
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    protocol = ProtocolManager.load_protocol(file_path)
    if protocol:
        print(f"✅ 成功加载标准格式协议")
        print(f"   协议名称: {protocol.protocol_name}")
        print(f"   版本: {protocol.version}")
        print(f"   字段数量: {len(protocol.fields)}")
        print(f"   校验类型: {protocol.checksum_config.checksum_type.value}")
        return True
    else:
        print("❌ 加载失败")
        return False


def test_extended_format():
    """测试扩展格式加载"""
    print("\n" + "=" * 60)
    print("测试2: 扩展格式")
    print("=" * 60)
    
    file_path = "protocol_extended_example.json"
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    protocol = ProtocolManager.load_protocol(file_path)
    if protocol:
        print(f"✅ 成功加载扩展格式协议（自动转换）")
        print(f"   协议名称: {protocol.protocol_name}")
        print(f"   版本: {protocol.version}")
        print(f"   字段数量: {len(protocol.fields)}")
        print(f"   校验类型: {protocol.checksum_config.checksum_type.value}")
        print("\n   字段详情:")
        for i, field in enumerate(protocol.fields):
            print(f"   [{i}] {field.name}: {field.byte_count}字节, 类型={field.field_type.value}")
        return True
    else:
        print("❌ 加载失败")
        return False


def test_format_detection():
    """测试格式检测"""
    print("\n" + "=" * 60)
    print("测试3: 格式检测")
    print("=" * 60)
    
    test_cases = [
        ("protocol_example.json", "standard"),
        ("protocol_extended_example.json", "extended")
    ]
    
    all_passed = True
    for file_path, expected_format in test_cases:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        detected_format = ProtocolConverter.detect_format(data)
        if detected_format == expected_format:
            print(f"✅ {file_path}: {detected_format} (正确)")
        else:
            print(f"❌ {file_path}: 检测为 {detected_format}, 期望 {expected_format}")
            all_passed = False
    
    return all_passed


def test_field_type_conversion():
    """测试字段类型转换"""
    print("\n" + "=" * 60)
    print("测试4: 字段类型转换")
    print("=" * 60)
    
    test_cases = [
        ("fixed", "bytes"),
        ("variable", "bytes"),
        ("command", "uint8"),
        ("array", "bytes"),
        ("uint8", "uint8"),
        ("uint16", "uint16"),
    ]
    
    all_passed = True
    for input_type, expected_output in test_cases:
        result = ProtocolConverter.convert_field_type(input_type)
        if result.value == expected_output:
            print(f"✅ {input_type} → {result.value}")
        else:
            print(f"❌ {input_type} → {result.value} (期望: {expected_output})")
            all_passed = False
    
    return all_passed


def main():
    """运行所有测试"""
    print("\n🧪 开始测试协议格式转换功能\n")
    
    results = []
    results.append(("标准格式加载", test_standard_format()))
    results.append(("扩展格式加载", test_extended_format()))
    results.append(("格式检测", test_format_detection()))
    results.append(("字段类型转换", test_field_type_conversion()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查")
        return 1


if __name__ == '__main__':
    sys.exit(main())
