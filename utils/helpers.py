# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import csv
from typing import List
from models import ParseResult, DataFrame


def export_to_txt(result: ParseResult, file_path: str) -> bool:
    """
    导出解析结果到文本文件
    
    Args:
        result: 解析结果
        file_path: 文件路径
        
    Returns:
        是否成功
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("串口数据分析结果\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"统计信息:\n")
            f.write(f"  总帧数: {result.get_total_frames()}\n")
            f.write(f"  有效帧: {result.get_valid_frames()}\n")
            f.write(f"  错误帧: {result.get_error_frames()}\n")
            f.write(f"  总字节数: {result.total_bytes}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("帧详细信息\n")
            f.write("=" * 80 + "\n\n")
            
            for frame in result.frames:
                f.write(frame.get_detailed_info())
                f.write("\n" + "-" * 80 + "\n\n")
        
        return True
    except Exception as e:
        print(f"导出TXT失败: {e}")
        return False


def export_to_csv(result: ParseResult, file_path: str) -> bool:
    """
    导出解析结果到CSV文件
    
    Args:
        result: 解析结果
        file_path: 文件路径
        
    Returns:
        是否成功
    """
    try:
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '帧序号', '起始位置', '结束位置', '原始数据',
                '解析结果', '校验状态', '错误信息'
            ])
            
            # 写入数据
            for frame in result.frames:
                checksum_status = ''
                if frame.expected_checksum is not None:
                    checksum_status = '✓ 通过' if frame.checksum_valid else '✗ 失败'
                else:
                    checksum_status = '无校验'
                
                writer.writerow([
                    frame.frame_number,
                    frame.start_position,
                    frame.end_position,
                    frame.get_raw_data_hex(),
                    frame.get_field_summary(),
                    checksum_status,
                    frame.error_message if frame.has_error else ''
                ])
        
        return True
    except Exception as e:
        print(f"导出CSV失败: {e}")
        return False


def format_hex(data: bytes, separator: str = ' ', bytes_per_line: int = 16) -> str:
    """
    格式化字节数据为十六进制字符串
    
    Args:
        data: 字节数据
        separator: 字节间分隔符
        bytes_per_line: 每行显示的字节数（0表示不换行）
        
    Returns:
        格式化的十六进制字符串
    """
    hex_str = separator.join(f'{b:02X}' for b in data)
    
    if bytes_per_line > 0:
        # 分行
        hex_parts = hex_str.split(separator)
        lines = []
        for i in range(0, len(hex_parts), bytes_per_line):
            line = separator.join(hex_parts[i:i+bytes_per_line])
            lines.append(line)
        return '\n'.join(lines)
    
    return hex_str


def bytes_to_int(data: bytes, signed: bool = False, byteorder: str = 'little') -> int:
    """
    字节转整数
    
    Args:
        data: 字节数据
        signed: 是否有符号
        byteorder: 字节序 ('little' 或 'big')
        
    Returns:
        整数值
    """
    return int.from_bytes(data, byteorder=byteorder, signed=signed)


def int_to_bytes(value: int, length: int, signed: bool = False, byteorder: str = 'little') -> bytes:
    """
    整数转字节
    
    Args:
        value: 整数值
        length: 字节长度
        signed: 是否有符号
        byteorder: 字节序 ('little' 或 'big')
        
    Returns:
        字节数据
    """
    return value.to_bytes(length, byteorder=byteorder, signed=signed)
