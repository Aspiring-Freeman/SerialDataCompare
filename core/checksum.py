# -*- coding: utf-8 -*-
"""
校验算法模块
支持多种校验算法，包括：
- 累加和校验 (Sum)
- 异或校验 (XOR)
- CRC-8 系列
- CRC-16 系列 (包括 MODBUS, CCITT, XMODEM, USB 等)
- CRC-32 系列
- LRC (纵向冗余校验)
- BCC (块校验码)
- Fletcher 校验
- Adler 校验
"""

import struct
from typing import Optional, Tuple, Dict, Any
from models.protocol import ChecksumType


class CRCTables:
    """CRC 查找表 - 预计算以提高性能"""
    
    # CRC-8 表
    CRC8_TABLE = None
    CRC8_ITU_TABLE = None
    CRC8_ROHC_TABLE = None
    CRC8_MAXIM_TABLE = None
    
    # CRC-16 表
    CRC16_MODBUS_TABLE = None
    CRC16_CCITT_TABLE = None
    CRC16_CCITT_FALSE_TABLE = None
    CRC16_XMODEM_TABLE = None
    CRC16_X25_TABLE = None
    CRC16_DNP_TABLE = None
    CRC16_USB_TABLE = None
    CRC16_MAXIM_TABLE = None
    
    # CRC-32 表
    CRC32_TABLE = None
    
    @classmethod
    def _generate_crc8_table(cls, poly: int) -> list:
        """生成 CRC-8 查找表"""
        table = []
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ poly) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
            table.append(crc)
        return table
    
    @classmethod
    def _generate_crc8_table_reflected(cls, poly: int) -> list:
        """生成反射 CRC-8 查找表"""
        table = []
        poly_ref = cls._reflect8(poly)
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 0x01:
                    crc = ((crc >> 1) ^ poly_ref) & 0xFF
                else:
                    crc = (crc >> 1) & 0xFF
            table.append(crc)
        return table
    
    @classmethod
    def _generate_crc16_table(cls, poly: int) -> list:
        """生成 CRC-16 查找表"""
        table = []
        for i in range(256):
            crc = i << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ poly) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
            table.append(crc)
        return table
    
    @classmethod
    def _generate_crc16_table_reflected(cls, poly: int) -> list:
        """生成反射 CRC-16 查找表"""
        table = []
        poly_ref = cls._reflect16(poly)
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 0x0001:
                    crc = ((crc >> 1) ^ poly_ref) & 0xFFFF
                else:
                    crc = (crc >> 1) & 0xFFFF
            table.append(crc)
        return table
    
    @classmethod
    def _generate_crc32_table(cls, poly: int = 0xEDB88320) -> list:
        """生成 CRC-32 查找表（反射多项式）"""
        table = []
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 0x00000001:
                    crc = ((crc >> 1) ^ poly) & 0xFFFFFFFF
                else:
                    crc = (crc >> 1) & 0xFFFFFFFF
            table.append(crc)
        return table
    
    @staticmethod
    def _reflect8(value: int) -> int:
        """反射8位值"""
        result = 0
        for i in range(8):
            if value & (1 << i):
                result |= (1 << (7 - i))
        return result
    
    @staticmethod
    def _reflect16(value: int) -> int:
        """反射16位值"""
        result = 0
        for i in range(16):
            if value & (1 << i):
                result |= (1 << (15 - i))
        return result
    
    @classmethod
    def init_tables(cls):
        """初始化所有 CRC 表"""
        if cls.CRC8_TABLE is None:
            cls.CRC8_TABLE = cls._generate_crc8_table(0x07)
        if cls.CRC8_ITU_TABLE is None:
            cls.CRC8_ITU_TABLE = cls._generate_crc8_table(0x07)
        if cls.CRC8_ROHC_TABLE is None:
            cls.CRC8_ROHC_TABLE = cls._generate_crc8_table_reflected(0x07)
        if cls.CRC8_MAXIM_TABLE is None:
            cls.CRC8_MAXIM_TABLE = cls._generate_crc8_table_reflected(0x31)
        if cls.CRC16_MODBUS_TABLE is None:
            cls.CRC16_MODBUS_TABLE = cls._generate_crc16_table_reflected(0x8005)
        if cls.CRC16_CCITT_TABLE is None:
            cls.CRC16_CCITT_TABLE = cls._generate_crc16_table_reflected(0x1021)
        if cls.CRC16_CCITT_FALSE_TABLE is None:
            cls.CRC16_CCITT_FALSE_TABLE = cls._generate_crc16_table(0x1021)
        if cls.CRC16_XMODEM_TABLE is None:
            cls.CRC16_XMODEM_TABLE = cls._generate_crc16_table(0x1021)
        if cls.CRC16_X25_TABLE is None:
            cls.CRC16_X25_TABLE = cls._generate_crc16_table_reflected(0x1021)
        if cls.CRC16_DNP_TABLE is None:
            cls.CRC16_DNP_TABLE = cls._generate_crc16_table_reflected(0x3D65)
        if cls.CRC16_USB_TABLE is None:
            cls.CRC16_USB_TABLE = cls._generate_crc16_table_reflected(0x8005)
        if cls.CRC16_MAXIM_TABLE is None:
            cls.CRC16_MAXIM_TABLE = cls._generate_crc16_table_reflected(0x8005)
        if cls.CRC32_TABLE is None:
            cls.CRC32_TABLE = cls._generate_crc32_table()


# 初始化 CRC 表
CRCTables.init_tables()


class ChecksumCalculator:
    """校验计算器 - 支持多种校验算法"""
    
    @classmethod
    def calculate(cls, data: bytes, checksum_type: ChecksumType) -> int:
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
        
        calculator = cls._get_calculator(checksum_type)
        if calculator:
            return calculator(data)
        else:
            raise ValueError(f"不支持的校验类型: {checksum_type}")
    
    @classmethod
    def _get_calculator(cls, checksum_type: ChecksumType):
        """获取校验计算函数"""
        calculators = {
            # 累加和校验
            ChecksumType.SUM: cls._calculate_sum,
            ChecksumType.SUM16: cls._calculate_sum16,
            
            # 异或校验
            ChecksumType.XOR: cls._calculate_xor,
            ChecksumType.XOR16: cls._calculate_xor16,
            
            # CRC-8 系列
            ChecksumType.CRC8: cls._calculate_crc8,
            ChecksumType.CRC8_ITU: cls._calculate_crc8_itu,
            ChecksumType.CRC8_ROHC: cls._calculate_crc8_rohc,
            ChecksumType.CRC8_MAXIM: cls._calculate_crc8_maxim,
            
            # CRC-16 系列
            ChecksumType.CRC16: cls._calculate_crc16_modbus,  # 默认 MODBUS
            ChecksumType.CRC16_IBM: cls._calculate_crc16_ibm,
            ChecksumType.CRC16_MODBUS: cls._calculate_crc16_modbus,
            ChecksumType.CRC16_CCITT: cls._calculate_crc16_ccitt,
            ChecksumType.CRC16_CCITT_FALSE: cls._calculate_crc16_ccitt_false,
            ChecksumType.CRC16_XMODEM: cls._calculate_crc16_xmodem,
            ChecksumType.CRC16_X25: cls._calculate_crc16_x25,
            ChecksumType.CRC16_DNP: cls._calculate_crc16_dnp,
            ChecksumType.CRC16_USB: cls._calculate_crc16_usb,
            ChecksumType.CRC16_MAXIM: cls._calculate_crc16_maxim,
            
            # CRC-32 系列
            ChecksumType.CRC32: cls._calculate_crc32,
            ChecksumType.CRC32_MPEG2: cls._calculate_crc32_mpeg2,
            ChecksumType.CRC32_POSIX: cls._calculate_crc32_posix,
            
            # LRC
            ChecksumType.LRC: cls._calculate_lrc,
            
            # BCC
            ChecksumType.BCC: cls._calculate_bcc,
            
            # Fletcher
            ChecksumType.FLETCHER16: cls._calculate_fletcher16,
            ChecksumType.FLETCHER32: cls._calculate_fletcher32,
            
            # Adler
            ChecksumType.ADLER32: cls._calculate_adler32,
            
            # 自定义 CRC（需要通过 calculate_custom_crc 调用）
            ChecksumType.CRC_CUSTOM: None,
        }
        return calculators.get(checksum_type)
    
    @classmethod
    def calculate_custom_crc(cls, data: bytes, params) -> int:
        """
        使用自定义参数计算 CRC
        
        Args:
            data: 要校验的数据
            params: CRCParameters 对象，包含 poly, init, ref_in, ref_out, xor_out, width
            
        Returns:
            CRC 校验值
        """
        poly = params.poly
        init = params.init
        ref_in = params.ref_in
        ref_out = params.ref_out
        xor_out = params.xor_out
        width = params.width
        
        # 计算掩码
        if width == 8:
            mask = 0xFF
        elif width == 16:
            mask = 0xFFFF
        elif width == 32:
            mask = 0xFFFFFFFF
        else:
            mask = (1 << width) - 1
        
        crc = init & mask
        
        for byte in data:
            if ref_in:
                # 反转输入字节
                byte = cls._reflect_byte(byte)
            
            if width == 8:
                crc ^= byte
                for _ in range(8):
                    if crc & 0x80:
                        crc = ((crc << 1) ^ poly) & mask
                    else:
                        crc = (crc << 1) & mask
            elif width == 16:
                crc ^= (byte << 8)
                for _ in range(8):
                    if crc & 0x8000:
                        crc = ((crc << 1) ^ poly) & mask
                    else:
                        crc = (crc << 1) & mask
            elif width == 32:
                crc ^= (byte << 24)
                for _ in range(8):
                    if crc & 0x80000000:
                        crc = ((crc << 1) ^ poly) & mask
                    else:
                        crc = (crc << 1) & mask
        
        if ref_out:
            crc = cls._reflect_bits(crc, width)
        
        return (crc ^ xor_out) & mask
    
    @staticmethod
    def _reflect_byte(byte: int) -> int:
        """反转字节位序"""
        result = 0
        for i in range(8):
            if byte & (1 << i):
                result |= (1 << (7 - i))
        return result
    
    @staticmethod
    def _reflect_bits(value: int, width: int) -> int:
        """反转指定宽度的位序"""
        result = 0
        for i in range(width):
            if value & (1 << i):
                result |= (1 << (width - 1 - i))
        return result
    
    @classmethod
    def get_checksum_length(cls, checksum_type: ChecksumType, crc_params=None) -> int:
        """获取校验码的字节长度"""
        # 自定义 CRC 需要根据参数确定长度
        if checksum_type == ChecksumType.CRC_CUSTOM and crc_params:
            return (crc_params.width + 7) // 8
        
        length_map = {
            ChecksumType.NONE: 0,
            ChecksumType.SUM: 1,
            ChecksumType.SUM16: 2,
            ChecksumType.XOR: 1,
            ChecksumType.XOR16: 2,
            ChecksumType.CRC8: 1,
            ChecksumType.CRC8_ITU: 1,
            ChecksumType.CRC8_ROHC: 1,
            ChecksumType.CRC8_MAXIM: 1,
            ChecksumType.CRC16: 2,
            ChecksumType.CRC16_IBM: 2,
            ChecksumType.CRC16_MODBUS: 2,
            ChecksumType.CRC16_CCITT: 2,
            ChecksumType.CRC16_CCITT_FALSE: 2,
            ChecksumType.CRC16_XMODEM: 2,
            ChecksumType.CRC16_X25: 2,
            ChecksumType.CRC16_DNP: 2,
            ChecksumType.CRC16_USB: 2,
            ChecksumType.CRC16_MAXIM: 2,
            ChecksumType.CRC32: 4,
            ChecksumType.CRC32_MPEG2: 4,
            ChecksumType.CRC32_POSIX: 4,
            ChecksumType.LRC: 1,
            ChecksumType.BCC: 1,
            ChecksumType.FLETCHER16: 2,
            ChecksumType.FLETCHER32: 4,
            ChecksumType.ADLER32: 4,
            ChecksumType.CRC_CUSTOM: 2,  # 默认2字节
        }
        return length_map.get(checksum_type, 1)
    
    # ==================== 累加和校验 ====================
    
    @staticmethod
    def _calculate_sum(data: bytes) -> int:
        """累加和校验 - 所有字节累加，取低8位"""
        return sum(data) & 0xFF
    
    @staticmethod
    def _calculate_sum16(data: bytes) -> int:
        """累加和校验16位 - 所有字节累加，取低16位"""
        return sum(data) & 0xFFFF
    
    # ==================== 异或校验 ====================
    
    @staticmethod
    def _calculate_xor(data: bytes) -> int:
        """异或校验 - 所有字节异或"""
        result = 0
        for byte in data:
            result ^= byte
        return result
    
    @staticmethod
    def _calculate_xor16(data: bytes) -> int:
        """异或校验16位 - 按16位字异或"""
        result = 0
        # 如果数据长度为奇数，补0
        padded_data = data + (b'\x00' if len(data) % 2 else b'')
        for i in range(0, len(padded_data), 2):
            word = (padded_data[i] << 8) | padded_data[i + 1]
            result ^= word
        return result & 0xFFFF
    
    # ==================== CRC-8 系列 ====================
    
    @staticmethod
    def _calculate_crc8(data: bytes) -> int:
        """
        CRC-8 标准
        多项式: 0x07, 初值: 0x00, 结果异或: 0x00
        """
        crc = 0x00
        for byte in data:
            crc = CRCTables.CRC8_TABLE[(crc ^ byte) & 0xFF]
        return crc
    
    @staticmethod
    def _calculate_crc8_itu(data: bytes) -> int:
        """
        CRC-8/ITU
        多项式: 0x07, 初值: 0x00, 结果异或: 0x55
        """
        crc = 0x00
        for byte in data:
            crc = CRCTables.CRC8_ITU_TABLE[(crc ^ byte) & 0xFF]
        return crc ^ 0x55
    
    @staticmethod
    def _calculate_crc8_rohc(data: bytes) -> int:
        """
        CRC-8/ROHC
        多项式: 0x07, 初值: 0xFF, 反射输入输出
        """
        crc = 0xFF
        for byte in data:
            crc = CRCTables.CRC8_ROHC_TABLE[(crc ^ byte) & 0xFF]
        return crc
    
    @staticmethod
    def _calculate_crc8_maxim(data: bytes) -> int:
        """
        CRC-8/MAXIM (Dallas/Maxim)
        多项式: 0x31, 初值: 0x00, 反射输入输出
        用于 1-Wire 总线
        """
        crc = 0x00
        for byte in data:
            crc = CRCTables.CRC8_MAXIM_TABLE[(crc ^ byte) & 0xFF]
        return crc
    
    # ==================== CRC-16 系列 ====================
    
    @staticmethod
    def _calculate_crc16_modbus(data: bytes) -> int:
        """
        CRC-16/MODBUS
        多项式: 0x8005, 初值: 0xFFFF, 反射输入输出
        最常用的工业协议校验
        """
        crc = 0xFFFF
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC16_MODBUS_TABLE[(crc ^ byte) & 0xFF]
        return crc
    
    @staticmethod
    def _calculate_crc16_ibm(data: bytes) -> int:
        """
        CRC-16/IBM (CRC-16/ARC)
        多项式: 0x8005, 初值: 0x0000, 反射输入输出
        """
        crc = 0x0000
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC16_MODBUS_TABLE[(crc ^ byte) & 0xFF]
        return crc
    
    @staticmethod
    def _calculate_crc16_ccitt(data: bytes) -> int:
        """
        CRC-16/CCITT (Kermit)
        多项式: 0x1021, 初值: 0x0000, 反射输入输出
        """
        crc = 0x0000
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC16_CCITT_TABLE[(crc ^ byte) & 0xFF]
        return crc
    
    @staticmethod
    def _calculate_crc16_ccitt_false(data: bytes) -> int:
        """
        CRC-16/CCITT-FALSE
        多项式: 0x1021, 初值: 0xFFFF, 不反射
        """
        crc = 0xFFFF
        for byte in data:
            crc = ((crc << 8) ^ CRCTables.CRC16_CCITT_FALSE_TABLE[(crc >> 8) ^ byte]) & 0xFFFF
        return crc
    
    @staticmethod
    def _calculate_crc16_xmodem(data: bytes) -> int:
        """
        CRC-16/XMODEM
        多项式: 0x1021, 初值: 0x0000, 不反射
        用于 XMODEM 协议
        """
        crc = 0x0000
        for byte in data:
            crc = ((crc << 8) ^ CRCTables.CRC16_XMODEM_TABLE[(crc >> 8) ^ byte]) & 0xFFFF
        return crc
    
    @staticmethod
    def _calculate_crc16_x25(data: bytes) -> int:
        """
        CRC-16/X25
        多项式: 0x1021, 初值: 0xFFFF, 反射输入输出, 结果异或: 0xFFFF
        用于 X.25, HDLC, PPP 等协议
        """
        crc = 0xFFFF
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC16_X25_TABLE[(crc ^ byte) & 0xFF]
        return crc ^ 0xFFFF
    
    @staticmethod
    def _calculate_crc16_dnp(data: bytes) -> int:
        """
        CRC-16/DNP
        多项式: 0x3D65, 初值: 0x0000, 反射输入输出, 结果异或: 0xFFFF
        用于 DNP3 协议
        """
        crc = 0x0000
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC16_DNP_TABLE[(crc ^ byte) & 0xFF]
        return crc ^ 0xFFFF
    
    @staticmethod
    def _calculate_crc16_usb(data: bytes) -> int:
        """
        CRC-16/USB
        多项式: 0x8005, 初值: 0xFFFF, 反射输入输出, 结果异或: 0xFFFF
        用于 USB 协议
        """
        crc = 0xFFFF
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC16_USB_TABLE[(crc ^ byte) & 0xFF]
        return crc ^ 0xFFFF
    
    @staticmethod
    def _calculate_crc16_maxim(data: bytes) -> int:
        """
        CRC-16/MAXIM
        多项式: 0x8005, 初值: 0x0000, 反射输入输出, 结果异或: 0xFFFF
        """
        crc = 0x0000
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC16_MAXIM_TABLE[(crc ^ byte) & 0xFF]
        return crc ^ 0xFFFF
    
    # ==================== CRC-32 系列 ====================
    
    @staticmethod
    def _calculate_crc32(data: bytes) -> int:
        """
        CRC-32 标准 (ISO 3309, HDLC, ANSI X3.66, ITU-T V.42)
        多项式: 0x04C11DB7, 初值: 0xFFFFFFFF, 反射输入输出, 结果异或: 0xFFFFFFFF
        用于 ZIP, RAR, PNG, GZIP 等
        """
        crc = 0xFFFFFFFF
        for byte in data:
            crc = (crc >> 8) ^ CRCTables.CRC32_TABLE[(crc ^ byte) & 0xFF]
        return crc ^ 0xFFFFFFFF
    
    @staticmethod
    def _calculate_crc32_mpeg2(data: bytes) -> int:
        """
        CRC-32/MPEG-2
        多项式: 0x04C11DB7, 初值: 0xFFFFFFFF, 不反射, 结果异或: 0x00000000
        """
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte << 24
            for _ in range(8):
                if crc & 0x80000000:
                    crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
                else:
                    crc = (crc << 1) & 0xFFFFFFFF
        return crc
    
    @staticmethod
    def _calculate_crc32_posix(data: bytes) -> int:
        """
        CRC-32/POSIX (cksum)
        多项式: 0x04C11DB7, 初值: 0x00000000, 不反射, 结果异或: 0xFFFFFFFF
        """
        crc = 0x00000000
        for byte in data:
            crc ^= byte << 24
            for _ in range(8):
                if crc & 0x80000000:
                    crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
                else:
                    crc = (crc << 1) & 0xFFFFFFFF
        return crc ^ 0xFFFFFFFF
    
    # ==================== LRC/BCC ====================
    
    @staticmethod
    def _calculate_lrc(data: bytes) -> int:
        """
        LRC (Longitudinal Redundancy Check) - 纵向冗余校验
        所有字节累加取补码（二进制补码）
        常用于 ASCII 模式的 Modbus
        """
        lrc = sum(data) & 0xFF
        return ((~lrc) + 1) & 0xFF
    
    @staticmethod
    def _calculate_bcc(data: bytes) -> int:
        """
        BCC (Block Check Character) - 块校验码
        实际上就是异或校验，与 XOR 相同
        """
        result = 0
        for byte in data:
            result ^= byte
        return result
    
    # ==================== Fletcher 校验 ====================
    
    @staticmethod
    def _calculate_fletcher16(data: bytes) -> int:
        """
        Fletcher-16 校验
        比累加和更强，比 CRC 更快
        """
        sum1 = 0
        sum2 = 0
        for byte in data:
            sum1 = (sum1 + byte) % 255
            sum2 = (sum2 + sum1) % 255
        return (sum2 << 8) | sum1
    
    @staticmethod
    def _calculate_fletcher32(data: bytes) -> int:
        """
        Fletcher-32 校验
        按16位字计算
        """
        sum1 = 0
        sum2 = 0
        # 如果长度为奇数，补0
        padded_data = data + (b'\x00' if len(data) % 2 else b'')
        for i in range(0, len(padded_data), 2):
            word = padded_data[i] | (padded_data[i + 1] << 8)
            sum1 = (sum1 + word) % 0xFFFF
            sum2 = (sum2 + sum1) % 0xFFFF
        return (sum2 << 16) | sum1
    
    # ==================== Adler 校验 ====================
    
    @staticmethod
    def _calculate_adler32(data: bytes) -> int:
        """
        Adler-32 校验
        类似 Fletcher-32，但使用素数 65521 作为模数
        用于 zlib
        """
        MOD_ADLER = 65521
        a = 1
        b = 0
        for byte in data:
            a = (a + byte) % MOD_ADLER
            b = (b + a) % MOD_ADLER
        return (b << 16) | a


class ChecksumValidator:
    """校验验证器"""
    
    @staticmethod
    def validate_frame(frame_data: bytes, 
                      checksum_config) -> Tuple[bool, int, int]:
        """
        验证数据帧的校验码
        
        Args:
            frame_data: 完整的帧数据（包括帧头、数据、校验码、帧尾）
            checksum_config: ChecksumConfig对象
            
        Returns:
            (是否通过, 计算校验值, 帧内校验值)
        """
        checksum_type = checksum_config.checksum_type
        
        if checksum_type == ChecksumType.NONE:
            return True, 0, 0
        
        # 获取校验码长度
        expected_length = ChecksumCalculator.get_checksum_length(checksum_type)
        if checksum_config.checksum_length > 0:
            checksum_length = checksum_config.checksum_length
        else:
            checksum_length = expected_length
        
        if len(frame_data) < checksum_length + 2:
            return False, 0, 0
        
        try:
            # 确定校验码位置
            if checksum_config.checksum_position is not None:
                checksum_start = checksum_config.checksum_position
                checksum_end = checksum_start + checksum_length
                
                if checksum_end > len(frame_data):
                    return False, 0, 0
                
                actual_checksum_bytes = frame_data[checksum_start:checksum_end]
            else:
                checksum_start = len(frame_data) - 1 - checksum_length
                actual_checksum_bytes = frame_data[checksum_start:checksum_start + checksum_length]
            
            # 转换校验码为整数（根据配置的字节序）
            from models.protocol import Endianness
            is_big_endian = (checksum_config.checksum_endianness == Endianness.BIG)
            
            if checksum_length == 1:
                actual_checksum = actual_checksum_bytes[0]
            elif checksum_length == 2:
                fmt = '>H' if is_big_endian else '<H'
                actual_checksum = struct.unpack(fmt, actual_checksum_bytes)[0]
            elif checksum_length == 4:
                fmt = '>I' if is_big_endian else '<I'
                actual_checksum = struct.unpack(fmt, actual_checksum_bytes)[0]
            else:
                byteorder = 'big' if is_big_endian else 'little'
                actual_checksum = int.from_bytes(actual_checksum_bytes, byteorder=byteorder)
            
            # 确定校验计算范围
            if checksum_config.checksum_start is not None and checksum_config.checksum_end is not None:
                data_start = checksum_config.checksum_start
                data_end = checksum_config.checksum_end
            elif checksum_config.checksum_start is not None:
                data_start = checksum_config.checksum_start
                data_end = checksum_config.checksum_position if checksum_config.checksum_position else checksum_start
            elif checksum_config.checksum_end is not None:
                data_start = 0
                data_end = checksum_config.checksum_end
            else:
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
            
            # 计算校验值
            calculated_checksum = ChecksumCalculator.calculate(data_to_check, checksum_type)
            
            # 根据校验类型截取相应位数
            checksum_bits = checksum_length * 8
            mask = (1 << checksum_bits) - 1
            calculated_checksum &= mask
            
            # 比较
            is_valid = (calculated_checksum == actual_checksum)
            
            return is_valid, calculated_checksum, actual_checksum
            
        except Exception as e:
            print(f"校验验证出错: {e}")
            import traceback
            traceback.print_exc()
            return False, 0, 0
    
    @staticmethod
    def get_checksum_info(frame_data: bytes,
                         checksum_length: int = 1) -> Dict[str, Any]:
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
    from models.protocol import ChecksumConfig, ChecksumPosition
    
    ct = ChecksumType(checksum_type)
    config = ChecksumConfig(
        checksum_type=ct,
        position=ChecksumPosition.BEFORE_TAIL,
        checksum_length=checksum_length,
        start_offset=start_offset,
        end_offset=end_offset
    )
    is_valid, _, _ = ChecksumValidator.validate_frame(frame_data, config)
    return is_valid


def get_all_checksum_types() -> list:
    """获取所有支持的校验类型列表"""
    return [
        ("无校验", ChecksumType.NONE),
        # 累加和
        ("累加和", ChecksumType.SUM),
        ("累加和16位", ChecksumType.SUM16),
        # 异或
        ("异或校验", ChecksumType.XOR),
        ("异或校验16位", ChecksumType.XOR16),
        # CRC-8
        ("CRC-8", ChecksumType.CRC8),
        ("CRC-8/ITU", ChecksumType.CRC8_ITU),
        ("CRC-8/ROHC", ChecksumType.CRC8_ROHC),
        ("CRC-8/MAXIM", ChecksumType.CRC8_MAXIM),
        # CRC-16
        ("CRC-16/MODBUS", ChecksumType.CRC16_MODBUS),
        ("CRC-16/IBM", ChecksumType.CRC16_IBM),
        ("CRC-16/CCITT", ChecksumType.CRC16_CCITT),
        ("CRC-16/CCITT-FALSE", ChecksumType.CRC16_CCITT_FALSE),
        ("CRC-16/XMODEM", ChecksumType.CRC16_XMODEM),
        ("CRC-16/X25", ChecksumType.CRC16_X25),
        ("CRC-16/DNP", ChecksumType.CRC16_DNP),
        ("CRC-16/USB", ChecksumType.CRC16_USB),
        ("CRC-16/MAXIM", ChecksumType.CRC16_MAXIM),
        # CRC-32
        ("CRC-32", ChecksumType.CRC32),
        ("CRC-32/MPEG-2", ChecksumType.CRC32_MPEG2),
        ("CRC-32/POSIX", ChecksumType.CRC32_POSIX),
        # 其他
        ("LRC", ChecksumType.LRC),
        ("BCC", ChecksumType.BCC),
        ("Fletcher-16", ChecksumType.FLETCHER16),
        ("Fletcher-32", ChecksumType.FLETCHER32),
        ("Adler-32", ChecksumType.ADLER32),
    ]


def get_checksum_type_names() -> list:
    """获取所有校验类型的名称列表（用于UI显示）"""
    return [name for name, _ in get_all_checksum_types()]
