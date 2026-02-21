# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import csv
import os
import re
import shutil
import tempfile
import json
import logging
from typing import List, Any, Callable, Optional
from models import ParseResult, DataFrame

logger = logging.getLogger(__name__)


def atomic_write_json(file_path: str, data: Any, indent: int = 2) -> bool:
    """
    原子写入 JSON 文件（带备份）
    
    使用临时文件 + 重命名模式确保写入安全：
    1. 如果原文件存在，先创建 .bak 备份
    2. 写入临时文件
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
        
        # 如果原文件存在，先创建备份
        bak_path = file_path + '.bak'
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, bak_path)
            except Exception as e:
                logger.warning(f"创建备份文件失败: {e}")
        
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
        logger.error(f"原子写入失败: {e}")
        return False


def safe_load_json(file_path: str, default: Any = None) -> Any:
    """
    安全加载 JSON 文件，损坏时自动从备份恢复
    
    加载顺序：
    1. 尝试加载主文件
    2. 主文件损坏则尝试从 .bak 恢复
    3. 都失败则返回默认值
    
    Args:
        file_path: JSON 文件路径
        default: 加载失败时的默认值
        
    Returns:
        加载的数据或默认值
    """
    # 尝试加载主文件
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"JSON 文件损坏: {file_path} - {e}")
    
    # 尝试从备份恢复
    bak_path = file_path + '.bak'
    if os.path.exists(bak_path):
        try:
            with open(bak_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 恢复成功，用备份覆盖损坏文件
            try:
                shutil.copy2(bak_path, file_path)
                logger.info(f"已从备份恢复: {file_path}")
            except Exception:
                pass
            return data
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"备份文件也已损坏: {bak_path} - {e}")
    
    return default


def strip_json_comments(text: str) -> str:
    """
    移除 JSON 文本中的单行注释（// ...）和尾逗号
    
    用户编写的协议 JSON 文件可能包含注释或尾逗号，标准 json 模块
    无法解析这些内容。本函数预处理后返回合法 JSON 字符串。
    
    处理规则：
    - 移除 // 开头的单行注释（考虑字符串内不移除）
    - 移除对象/数组末尾的尾逗号（如 {"a":1,}）
    
    Args:
        text: 可能包含注释和尾逗号的 JSON 文本
        
    Returns:
        清理后可被 json.loads 解析的字符串
    """
    # 移除单行注释（不在双引号字符串内的 // 注释）
    # 简单策略：逐行处理，仅移除不在引号内的 // 及其后内容
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        in_string = False
        escape_next = False
        result_chars = []
        i = 0
        while i < len(line):
            ch = line[i]
            if escape_next:
                result_chars.append(ch)
                escape_next = False
                i += 1
                continue
            if ch == '\\' and in_string:
                result_chars.append(ch)
                escape_next = True
                i += 1
                continue
            if ch == '"':
                in_string = not in_string
                result_chars.append(ch)
                i += 1
                continue
            if not in_string and ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
                # 找到行注释，截断本行
                break
            result_chars.append(ch)
            i += 1
        cleaned_lines.append(''.join(result_chars))
    
    cleaned = '\n'.join(cleaned_lines)
    
    # 移除尾逗号：在 } 或 ] 前面的逗号
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
    
    return cleaned


def load_json_with_comments(file_path: str, default: Any = None) -> Any:
    """
    加载可能包含 // 注释和尾逗号的 JSON 文件
    
    Args:
        file_path: JSON 文件路径
        default: 加载失败时的默认值
        
    Returns:
        解析后的数据或默认值
    """
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        cleaned = strip_json_comments(text)
        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"加载 JSON（含注释） 失败: {file_path} - {e}")
        return default


def safe_move_file(src: str, dst: str) -> bool:
    """
    安全移动文件（先复制再删除源文件，避免跨文件系统问题）
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        
    Returns:
        是否成功
    """
    try:
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)
        
        shutil.copy2(src, dst)
        # 验证复制成功
        if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src):
            os.remove(src)
            return True
        else:
            logger.error(f"文件移动验证失败: {src} -> {dst}")
            if os.path.exists(dst):
                os.remove(dst)
            return False
    except Exception as e:
        logger.error(f"文件移动失败: {src} -> {dst}: {e}")
        return False


def safe_move_directory(src: str, dst: str) -> bool:
    """
    安全移动目录（先复制再删除源目录）
    
    Args:
        src: 源目录路径
        dst: 目标目录路径
        
    Returns:
        是否成功
    """
    try:
        if os.path.exists(dst):
            logger.error(f"目标目录已存在: {dst}")
            return False
        
        shutil.copytree(src, dst)
        # 验证拷贝成功（至少检查目录存在）
        if os.path.isdir(dst):
            shutil.rmtree(src)
            return True
        else:
            logger.error(f"目录移动验证失败: {src} -> {dst}")
            return False
    except Exception as e:
        logger.error(f"目录移动失败: {src} -> {dst}: {e}")
        return False


def preprocess_hex_input(raw_input: str) -> str:
    """
    智能预处理十六进制输入数据
    
    处理实际串口日志格式：
    1. 移除行首时间戳（如 [10:23:45.123] 或 2024-01-01 10:00:00）
    2. 移除行首方向标记（如 TX:, RX:, Send:, Recv:, >>> 等）
    3. 移除注释（// 或 # 开头的部分）
    4. 合并多行为单行
    5. 移除多余空格
    
    Args:
        raw_input: 原始输入文本
        
    Returns:
        清洗后的纯十六进制字符串
    """
    lines = raw_input.strip().splitlines()
    hex_parts = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 移除行尾注释
        line = re.sub(r'//.*$', '', line)
        line = re.sub(r'#.*$', '', line)
        
        # 移除行首时间戳 [HH:MM:SS.mmm] 或 YYYY-MM-DD HH:MM:SS 等
        line = re.sub(r'^\[?\d{1,4}[-/:]\d{2}[-/:]\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?\]?\s*', '', line)
        line = re.sub(r'^\[?\d{2}:\d{2}:\d{2}(?:\.\d+)?\]?\s*', '', line)
        
        # 移除方向标记
        line = re.sub(r'^(?:TX|RX|Send|Recv|>>>|<<<|->|<-)\s*:?\s*', '', line, flags=re.IGNORECASE)
        
        # 只保留合法的十六进制字符和空格
        cleaned = re.sub(r'[^0-9a-fA-F\s]', ' ', line)
        cleaned = cleaned.strip()
        
        if cleaned:
            hex_parts.append(cleaned)
    
    # 合并为单行并规范化空格
    result = ' '.join(hex_parts)
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result


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
