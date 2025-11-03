# -*- coding: utf-8 -*-
"""
校验算法模块
支持多种校验算法，可自定义校验范围
"""

import struct
from typing import Optional
from models.protocol import ChecksumType


class ChecksumCalculator:
    """校验计算器基类"""
    
    @staticmethod
    def calculate(data: bytes, checksum_type: ChecksumType) -> int:
        """
        计算校验值
        
        Args:
            data: 要校验的数据（不包括校验码本身）
            checksum_type: 校验类型
            
        Returns:
            校验值
        """
        if checksum_type == ChecksumType.NONE:
            return 0
        elif checksum_type == ChecksumType.SUM:
            return ChecksumCalculator._calculate_sum(data)
        elif checksum_type == ChecksumType.XOR:
            return ChecksumCalculator._calculate_xor(data)
        elif checksum_type == ChecksumType.CRC16:
            return ChecksumCalculator._calculate_crc16(data)
        elif checksum_type == ChecksumType.CRC32:
            return ChecksumCalculator._calculate_crc32(data)
        else:
            raise ValueError(f"不支持的校验类型: {checksum_type}")
    
    @staticmethod
    def _calculate_sum(data: bytes) -> int:
        """
        累加和校验
        所有字节累加，取低8位
        """
        return sum(data) & 0xFF
    
    @staticmethod
    def _calculate_xor(data: bytes) -> int:
        """
        异或校验
        所有字节异或
        """
        result = 0
        for byte in data:
            result ^= byte
        return result
    
    @staticmethod
    def _calculate_crc16(data: bytes, poly: int = 0xA001) -> int:
        """
        CRC16校验 (Modbus)
        
        Args:
            data: 要校验的数据
            poly: 多项式，默认0xA001（Modbus）
            
        Returns:
            CRC16值（16位）
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
        return crc & 0xFFFF
    
    @staticmethod
    def _calculate_crc32(data: bytes) -> int:
        """
        CRC32校验
        
        Returns:
            CRC32值（32位）
        """
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x00000001:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF


class ChecksumValidator:
    """校验验证器"""
    
    @staticmethod
    def validate_frame(frame_data: bytes, 
                      checksum_type: ChecksumType,
                      start_offset: int = 0,
                      end_offset: int = -1,
                      checksum_length: int = 1) -> tuple[bool, int, int]:
        """
        验证数据帧的校验码
        
        Args:
            frame_data: 完整的帧数据（包括帧头、数据、校验码、帧尾）
            checksum_type: 校验类型
            start_offset: 校验起始偏移（从帧头后开始计数，0表示紧跟帧头）
            end_offset: 校验结束偏移（-1表示到校验码前，-2表示到帧尾前等）
            checksum_length: 校验码字节数
            
        Returns:
            (是否通过, 期望校验值, 实际校验值)
        """
        if checksum_type == ChecksumType.NONE:
            return True, 0, 0
        
        if len(frame_data) < checksum_length + 2:  # 至少要有帧头+校验码+帧尾
            return False, 0, 0
        
        try:
            # 提取校验码
            # 假设校验码在帧尾前（最常见的情况）
            checksum_start = len(frame_data) - 1 - checksum_length  # 帧尾前
            actual_checksum_bytes = frame_data[checksum_start:checksum_start + checksum_length]
            
            # 根据校验码长度转换为整数
            if checksum_length == 1:
                actual_checksum = actual_checksum_bytes[0]
            elif checksum_length == 2:
                actual_checksum = struct.unpack('<H', actual_checksum_bytes)[0]  # 小端序
            elif checksum_length == 4:
                actual_checksum = struct.unpack('<I', actual_checksum_bytes)[0]  # 小端序
            else:
                # 多字节情况，转为整数
                actual_checksum = int.from_bytes(actual_checksum_bytes, byteorder='little')
            
            # 确定要校验的数据范围
            # start_offset: -1表示包含帧头(索引0)，0表示帧头后第一个字节(索引1)，1表示跳过一个字节(索引2)
            # end_offset: -1表示到帧尾前(校验码后)，-2表示到校验码前，正数表示具体索引
            
            if start_offset == -1:
                # 包含帧头
                data_start = 0
            else:
                # 从帧头后开始，跳过start_offset个字节
                data_start = 1 + start_offset
            
            if end_offset == -1:
                # 到帧尾前（即校验码后）
                data_end = len(frame_data) - 1
            elif end_offset == -2:
                # 到校验码前
                data_end = checksum_start
            elif end_offset < 0:
                # 其他负数：从尾部开始计数
                data_end = len(frame_data) + end_offset
            else:
                # 正数：直接使用索引
                data_end = end_offset
            
            # 提取要校验的数据
            data_to_check = frame_data[data_start:data_end]
            
            # 计算期望的校验值
            expected_checksum = ChecksumCalculator.calculate(data_to_check, checksum_type)
            
            # 对于CRC16和CRC32，需要根据校验码长度截取
            if checksum_type == ChecksumType.CRC16:
                expected_checksum &= 0xFFFF
            elif checksum_type == ChecksumType.CRC32:
                expected_checksum &= 0xFFFFFFFF
            else:
                expected_checksum &= 0xFF
            
            # 比较
            is_valid = (expected_checksum == actual_checksum)
            
            return is_valid, expected_checksum, actual_checksum
            
        except Exception as e:
            print(f"校验验证出错: {e}")
            return False, 0, 0
    
    @staticmethod
    def get_checksum_info(frame_data: bytes,
                         checksum_length: int = 1) -> dict:
        """
        获取校验码信息（用于调试）
        
        Returns:
            包含校验码位置和值的字典
        """
        if len(frame_data) < checksum_length + 2:
            return {}
        
        checksum_start = len(frame_data) - 1 - checksum_length
        checksum_bytes = frame_data[checksum_start:checksum_start + checksum_length]
        
        return {
            'position': checksum_start,
            'bytes': checksum_bytes,
            'hex': ' '.join(f'{b:02X}' for b in checksum_bytes)
        }


# 便捷函数
def calculate_checksum(data: bytes, checksum_type: str) -> int:
    """
    计算校验值的便捷函数
    
    Args:
        data: 要校验的数据
        checksum_type: 校验类型字符串
        
    Returns:
        校验值
    """
    ct = ChecksumType(checksum_type)
    return ChecksumCalculator.calculate(data, ct)


def validate_checksum(frame_data: bytes,
                     checksum_type: str,
                     start_offset: int = 0,
                     end_offset: int = -1,
                     checksum_length: int = 1) -> bool:
    """
    验证校验码的便捷函数
    
    Returns:
        是否通过校验
    """
    ct = ChecksumType(checksum_type)
    is_valid, _, _ = ChecksumValidator.validate_frame(
        frame_data, ct, start_offset, end_offset, checksum_length
    )
    return is_valid
