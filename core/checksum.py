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
                      checksum_config) -> tuple[bool, int, int]:
        """
        验证数据帧的校验码（简化版）
        
        Args:
            frame_data: 完整的帧数据（包括帧头、数据、校验码、帧尾）
            checksum_config: ChecksumConfig对象
            
        Returns:
            (是否通过, 期望校验值, 实际校验值)
        """
        checksum_type = checksum_config.checksum_type
        
        if checksum_type == ChecksumType.NONE:
            return True, 0, 0
        
        if len(frame_data) < checksum_config.checksum_length + 2:
            return False, 0, 0
        
        try:
            # 优先使用新的简化配置
            if checksum_config.checksum_position is not None:
                # 直接使用绝对位置提取校验码
                checksum_start = checksum_config.checksum_position
                checksum_end = checksum_start + checksum_config.checksum_length
                
                if checksum_end > len(frame_data):
                    return False, 0, 0
                
                actual_checksum_bytes = frame_data[checksum_start:checksum_end]
            else:
                # 使用旧版相对位置（兼容模式）
                checksum_start = len(frame_data) - 1 - checksum_config.checksum_length
                actual_checksum_bytes = frame_data[checksum_start:checksum_start + checksum_config.checksum_length]
            
            # 转换校验码为整数
            if checksum_config.checksum_length == 1:
                actual_checksum = actual_checksum_bytes[0]
            elif checksum_config.checksum_length == 2:
                actual_checksum = struct.unpack('<H', actual_checksum_bytes)[0]
            elif checksum_config.checksum_length == 4:
                actual_checksum = struct.unpack('<I', actual_checksum_bytes)[0]
            else:
                actual_checksum = int.from_bytes(actual_checksum_bytes, byteorder='little')
            
            # 确定校验计算范围（优先使用新配置）
            if checksum_config.checksum_start is not None and checksum_config.checksum_end is not None:
                # 使用绝对位置范围
                data_start = checksum_config.checksum_start
                data_end = checksum_config.checksum_end
            elif checksum_config.checksum_start is not None:
                # 只指定了起始位置，到校验码前
                data_start = checksum_config.checksum_start
                data_end = checksum_config.checksum_position if checksum_config.checksum_position else checksum_start
            elif checksum_config.checksum_end is not None:
                # 只指定了结束位置，从帧头开始
                data_start = 0
                data_end = checksum_config.checksum_end
            else:
                # 使用旧版offset配置（兼容模式）
                if checksum_config.start_offset == -1:
                    data_start = 0
                else:
                    data_start = 1 + checksum_config.start_offset
                
                if checksum_config.end_offset == 0:
                    data_end = checksum_start
                elif checksum_config.end_offset == -1:
                    data_end = len(frame_data) - 1
                elif checksum_config.end_offset < 0:
                    data_end = len(frame_data) + checksum_config.end_offset + 1
                else:
                    if checksum_config.end_offset < 100:
                        data_end = data_start + checksum_config.end_offset
                    else:
                        data_end = checksum_config.end_offset
            
            # 提取要校验的数据
            data_to_check = frame_data[data_start:data_end]
            
            # 计算期望的校验值
            expected_checksum = ChecksumCalculator.calculate(data_to_check, checksum_type)
            
            # 根据校验类型截取相应位数
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
            import traceback
            traceback.print_exc()
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
