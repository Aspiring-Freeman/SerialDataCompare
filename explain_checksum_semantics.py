#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验范围语义说明和转换工具

旧版配置 vs 简化配置的语义差异
"""

def explain_offset_semantics():
    """解释偏移量语义"""
    print("="*70)
    print("校验范围配置语义对比")
    print("="*70)
    print()
    
    print("【旧版配置】start_offset 的含义：")
    print("  - 含义：从**帧头后**偏移多少字节开始")
    print("  - start_offset=0  → 从位置1开始（帧头后第0个字节）")
    print("  - start_offset=1  → 从位置2开始（帧头后第1个字节）")
    print("  - start_offset=-1 → 从位置0开始（特殊值，表示包含帧头）")
    print()
    
    print("【简化配置】checksum_start 的含义：")
    print("  - 含义：**绝对位置索引**（从0开始）")
    print("  - checksum_start=0 → 从位置0开始（帧头位置）")
    print("  - checksum_start=1 → 从位置1开始（帧头后第一字节）")
    print("  - checksum_start=2 → 从位置2开始（帧头后第二字节）")
    print()
    
    print("="*70)
    print("转换规则")
    print("="*70)
    print()
    print("旧版 → 简化配置：")
    print("  start_offset=-1  → checksum_start=0  (包含帧头)")
    print("  start_offset=0   → checksum_start=1  (不包含帧头)")
    print("  start_offset=N   → checksum_start=N+1")
    print()
    print("  end_offset=-1    → checksum_end=帧长度-1  (到帧尾前)")
    print("  end_offset=0     → checksum_end=校验码位置")
    print()
    
    print("="*70)
    print("示例对比（106字节帧，校验码在104）")
    print("="*70)
    print()
    
    examples = [
        {
            "desc": "从帧头开始，到校验码前",
            "old": {"start_offset": -1, "end_offset": 0},
            "new": {"checksum_start": 0, "checksum_end": 104},
            "range": "[0:104]"
        },
        {
            "desc": "从帧头后开始，到帧尾前",
            "old": {"start_offset": 0, "end_offset": -1},
            "new": {"checksum_start": 1, "checksum_end": 105},
            "range": "[1:105]"
        },
        {
            "desc": "从帧头后开始，到校验码前",
            "old": {"start_offset": 0, "end_offset": 0},
            "new": {"checksum_start": 1, "checksum_end": 104},
            "range": "[1:104]"
        },
    ]
    
    for i, ex in enumerate(examples, 1):
        print(f"示例{i}: {ex['desc']}")
        print(f"  旧版配置: start_offset={ex['old']['start_offset']:3d}, end_offset={ex['old']['end_offset']:3d}")
        print(f"  简化配置: checksum_start={ex['new']['checksum_start']:3d}, checksum_end={ex['new']['checksum_end']:3d}")
        print(f"  实际范围: frame_data{ex['range']}")
        print()

def convert_old_to_new(start_offset: int, end_offset: int, 
                       frame_length: int, checksum_position: int) -> dict:
    """
    将旧版配置转换为简化配置
    
    Args:
        start_offset: 旧版起始偏移
        end_offset: 旧版结束偏移
        frame_length: 帧长度
        checksum_position: 校验码位置
    
    Returns:
        简化配置字典 {checksum_start, checksum_end}
    """
    # 计算起始位置
    if start_offset == -1:
        checksum_start = 0
    else:
        checksum_start = 1 + start_offset
    
    # 计算结束位置
    if end_offset == 0:
        checksum_end = checksum_position
    elif end_offset == -1:
        checksum_end = frame_length - 1
    elif end_offset < 0:
        checksum_end = frame_length + end_offset + 1
    else:
        checksum_end = checksum_start + end_offset
    
    return {
        "checksum_start": checksum_start,
        "checksum_end": checksum_end
    }

if __name__ == "__main__":
    explain_offset_semantics()
    
    print("="*70)
    print("转换工具示例")
    print("="*70)
    print()
    
    # 测试转换
    test_cases = [
        {"start": -1, "end": 0, "desc": "包含帧头，到校验码前"},
        {"start": 0, "end": -1, "desc": "不含帧头，到帧尾前"},
        {"start": 0, "end": 0, "desc": "不含帧头，到校验码前"},
    ]
    
    frame_length = 106
    checksum_position = 104
    
    for tc in test_cases:
        result = convert_old_to_new(tc["start"], tc["end"], frame_length, checksum_position)
        print(f"{tc['desc']}:")
        print(f"  输入: start_offset={tc['start']:3d}, end_offset={tc['end']:3d}")
        print(f"  输出: checksum_start={result['checksum_start']:3d}, checksum_end={result['checksum_end']:3d}")
        range_str = f"[{result['checksum_start']}:{result['checksum_end']}]"
        print(f"  范围: frame_data{range_str} = {result['checksum_end'] - result['checksum_start']} 字节")
        print()
