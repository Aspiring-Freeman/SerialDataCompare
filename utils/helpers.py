# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import csv
import os
import tempfile
import json
from typing import List, Any, Callable
from models import ParseResult, DataFrame


def atomic_write_json(file_path: str, data: Any, indent: int = 2) -> bool:
    """
    原子写入 JSON 文件
    
    使用临时文件 + 重命名模式确保写入安全：
    1. 先写入临时文件
    2. 确保临时文件写入成功
    3. 原子性地将临时文件重命名为目标文件
    
    这样即使程序崩溃或断电，也不会损坏原有文件。
    
    Args:
        file_path: 目标文件路径
        data: 要写入的数据
        indent: JSON 缩进
        
    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 创建临时文件（在同一目录以确保原子重命名）
        fd, temp_path = tempfile.mkstemp(
            suffix='.tmp',
            prefix='atomic_',
            dir=dir_path if dir_path else '.'
        )
        
        try:
            # 写入临时文件
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            
            # 原子性重命名（在同一文件系统上是原子操作）
            os.replace(temp_path, file_path)
            return True
            
        except Exception:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
            
    except Exception as e:
        print(f"原子写入失败: {e}")
        return False


def atomic_write_text(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    原子写入文本文件
    
    Args:
        file_path: 目标文件路径
        content: 要写入的文本内容
        encoding: 文件编码
        
    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 创建临时文件
        fd, temp_path = tempfile.mkstemp(
            suffix='.tmp',
            prefix='atomic_',
            dir=dir_path if dir_path else '.'
        )
        
        try:
            # 写入临时文件
            with os.fdopen(fd, 'w', encoding=encoding) as f:
                f.write(content)
            
            # 原子性重命名
            os.replace(temp_path, file_path)
            return True
            
        except Exception:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
            
    except Exception as e:
        print(f"原子写入失败: {e}")
        return False


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
