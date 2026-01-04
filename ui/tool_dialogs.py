# -*- coding: utf-8 -*-
"""
小工具对话框
包含 HEX/ASCII 转换器和进制转换器
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QWidget,
    QLabel, QFrame, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from qfluentwidgets import (
    SubtitleLabel, BodyLabel, 
    TextEdit, PushButton, LineEdit, ComboBox,
    InfoBar, InfoBarPosition, FluentIcon as FIF,
    isDarkTheme
)


def get_dialog_stylesheet():
    """获取对话框样式表"""
    if isDarkTheme():
        return """
            QDialog {
                background-color: #202020;
                color: #ffffff;
            }
            QFrame {
                background-color: transparent;
            }
            QLabel {
                color: #ffffff;
            }
        """
    else:
        return """
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QFrame {
                background-color: transparent;
            }
            QLabel {
                color: #000000;
            }
        """

class HexAsciiConverterDialog(QDialog):
    """HEX/ASCII 转换器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('HEX ↔ ASCII 转换器')
        # 使用标准窗口标志，支持调整大小、移动和最大化
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(600, 500)
        self.setMinimumSize(400, 350)
        # 允许调整大小
        self.setSizeGripEnabled(True)
        # 应用主题样式
        self.setStyleSheet(get_dialog_stylesheet())
        
        # 主布局
        self.viewLayout = QVBoxLayout(self)
        self.viewLayout.setContentsMargins(20, 20, 20, 20)
        self.viewLayout.setSpacing(10)
        
        # 标题
        self.titleLabel = SubtitleLabel('HEX ↔ ASCII 转换器', self)
        self.viewLayout.addWidget(self.titleLabel)
        
        # 说明
        self.descLabel = BodyLabel('在上方输入 HEX 或 ASCII，点击按钮进行转换', self)
        self.descLabel.setTextColor("#888888", "#888888")
        self.viewLayout.addWidget(self.descLabel)
        
        # HEX 输入区域
        hexFrame = QFrame(self)
        hexLayout = QVBoxLayout(hexFrame)
        hexLayout.setContentsMargins(0, 10, 0, 0)
        
        hexLabel = BodyLabel('HEX (十六进制)', self)
        hexLabel.setFont(QFont("", 10, QFont.Bold))
        hexLayout.addWidget(hexLabel)
        
        self.hexEdit = TextEdit(self)
        self.hexEdit.setPlaceholderText('输入 HEX 数据，如: 48 65 6C 6C 6F 或 48656C6C6F')
        self.hexEdit.setMinimumHeight(100)
        hexLayout.addWidget(self.hexEdit)
        
        self.viewLayout.addWidget(hexFrame)
        
        # 转换按钮区域
        btnFrame = QFrame(self)
        btnLayout = QHBoxLayout(btnFrame)
        btnLayout.setContentsMargins(0, 5, 0, 5)
        
        self.hexToAsciiBtn = PushButton('HEX → ASCII ↓', self)
        self.hexToAsciiBtn.setIcon(FIF.DOWN)
        self.hexToAsciiBtn.clicked.connect(self.hex_to_ascii)
        btnLayout.addWidget(self.hexToAsciiBtn)
        
        self.asciiToHexBtn = PushButton('ASCII → HEX ↑', self)
        self.asciiToHexBtn.setIcon(FIF.UP)
        self.asciiToHexBtn.clicked.connect(self.ascii_to_hex)
        btnLayout.addWidget(self.asciiToHexBtn)
        
        self.clearBtn = PushButton('清空', self)
        self.clearBtn.setIcon(FIF.DELETE)
        self.clearBtn.clicked.connect(self.clear_all)
        btnLayout.addWidget(self.clearBtn)
        
        self.viewLayout.addWidget(btnFrame)
        
        # ASCII 输入区域
        asciiFrame = QFrame(self)
        asciiLayout = QVBoxLayout(asciiFrame)
        asciiLayout.setContentsMargins(0, 0, 0, 10)
        
        asciiLabel = BodyLabel('ASCII (文本)', self)
        asciiLabel.setFont(QFont("", 10, QFont.Bold))
        asciiLayout.addWidget(asciiLabel)
        
        self.asciiEdit = TextEdit(self)
        self.asciiEdit.setPlaceholderText('输入文本，如: Hello World')
        self.asciiEdit.setMinimumHeight(100)
        asciiLayout.addWidget(self.asciiEdit)
        
        self.viewLayout.addWidget(asciiFrame)
        
        # 关闭按钮
        btnCloseFrame = QFrame(self)
        btnCloseLayout = QHBoxLayout(btnCloseFrame)
        btnCloseLayout.setContentsMargins(0, 10, 0, 0)
        btnCloseLayout.addStretch()
        
        self.closeBtn = PushButton('关闭', self)
        self.closeBtn.clicked.connect(self.close)
        btnCloseLayout.addWidget(self.closeBtn)
        
        self.viewLayout.addWidget(btnCloseFrame)
    
    def hex_to_ascii(self):
        """将 HEX 转换为 ASCII"""
        hex_text = self.hexEdit.toPlainText().strip()
        if not hex_text:
            self.show_info('请输入 HEX 数据', 'warning')
            return
        
        try:
            # 移除空格和常见分隔符
            hex_clean = hex_text.replace(' ', '').replace('-', '').replace(':', '')
            hex_clean = hex_clean.replace('0x', '').replace('0X', '')
            
            # 验证长度
            if len(hex_clean) % 2 != 0:
                self.show_info('HEX 长度必须为偶数', 'error')
                return
            
            # 转换为字节
            bytes_data = bytes.fromhex(hex_clean)
            
            # 转换为可读的 ASCII 表示
            # 可打印字符直接显示，不可打印字符显示为 .
            result_chars = []
            for b in bytes_data:
                if 32 <= b <= 126:  # 可打印 ASCII 字符
                    result_chars.append(chr(b))
                else:
                    result_chars.append('.')  # 不可打印字符显示为点
            
            result = ''.join(result_chars)
            
            # 同时显示详细信息
            printable_count = sum(1 for b in bytes_data if 32 <= b <= 126)
            non_printable_count = len(bytes_data) - printable_count
            
            self.asciiEdit.setPlainText(result)
            
            if non_printable_count > 0:
                self.show_info(f'转换成功，共 {len(bytes_data)} 字节（{non_printable_count} 个不可打印字符用 . 表示）', 'success')
            else:
                self.show_info(f'转换成功，共 {len(bytes_data)} 字节', 'success')
            
        except ValueError as e:
            self.show_info(f'无效的 HEX 格式: {str(e)}', 'error')
    
    def ascii_to_hex(self):
        """将 ASCII 转换为 HEX"""
        ascii_text = self.asciiEdit.toPlainText()
        if not ascii_text:
            self.show_info('请输入文本', 'warning')
            return
        
        try:
            # 编码为字节
            bytes_data = ascii_text.encode('utf-8')
            
            # 转换为 HEX 字符串（带空格分隔）
            hex_result = ' '.join(f'{b:02X}' for b in bytes_data)
            
            self.hexEdit.setPlainText(hex_result)
            self.show_info(f'转换成功，共 {len(bytes_data)} 字节', 'success')
            
        except Exception as e:
            self.show_info(f'转换失败: {str(e)}', 'error')
    
    def clear_all(self):
        """清空所有内容"""
        self.hexEdit.clear()
        self.asciiEdit.clear()
    
    def show_info(self, message: str, info_type: str = 'info'):
        """显示信息提示"""
        if info_type == 'success':
            InfoBar.success(
                title='成功',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        elif info_type == 'warning':
            InfoBar.warning(
                title='提示',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        elif info_type == 'error':
            InfoBar.error(
                title='错误',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )


class BaseConverterDialog(QDialog):
    """进制转换器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('进制转换器')
        # 使用标准窗口标志，支持调整大小、移动和最大化
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(550, 450)
        self.setMinimumSize(400, 350)
        # 允许调整大小
        self.setSizeGripEnabled(True)
        # 应用主题样式
        self.setStyleSheet(get_dialog_stylesheet())
        
        # 主布局
        self.viewLayout = QVBoxLayout(self)
        self.viewLayout.setContentsMargins(20, 20, 20, 20)
        self.viewLayout.setSpacing(10)
        
        # 标题
        self.titleLabel = SubtitleLabel('进制转换器', self)
        self.viewLayout.addWidget(self.titleLabel)
        
        # 说明
        self.descLabel = BodyLabel('支持二进制、八进制、十进制、十六进制相互转换', self)
        self.descLabel.setTextColor("#888888", "#888888")
        self.viewLayout.addWidget(self.descLabel)
        
        # 输入区域
        inputFrame = QFrame(self)
        inputLayout = QHBoxLayout(inputFrame)
        inputLayout.setContentsMargins(0, 15, 0, 10)
        
        self.inputEdit = LineEdit(self)
        self.inputEdit.setPlaceholderText('输入要转换的数值')
        self.inputEdit.setClearButtonEnabled(True)
        self.inputEdit.textChanged.connect(self.on_input_changed)
        inputLayout.addWidget(self.inputEdit, 3)
        
        self.baseCombo = ComboBox(self)
        self.baseCombo.addItems(['二进制 (2)', '八进制 (8)', '十进制 (10)', '十六进制 (16)'])
        self.baseCombo.setCurrentIndex(2)  # 默认十进制
        self.baseCombo.currentIndexChanged.connect(self.on_input_changed)
        inputLayout.addWidget(self.baseCombo, 1)
        
        self.viewLayout.addWidget(inputFrame)
        
        # 转换按钮
        self.convertBtn = PushButton('转换', self)
        self.convertBtn.setIcon(FIF.SYNC)
        self.convertBtn.clicked.connect(self.convert)
        self.viewLayout.addWidget(self.convertBtn)
        
        # 结果区域
        resultFrame = QFrame(self)
        resultLayout = QGridLayout(resultFrame)
        resultLayout.setContentsMargins(0, 15, 0, 10)
        resultLayout.setSpacing(10)
        
        # 二进制结果
        binLabel = BodyLabel('二进制 (BIN):', self)
        binLabel.setFont(QFont("", 10, QFont.Bold))
        resultLayout.addWidget(binLabel, 0, 0)
        self.binEdit = LineEdit(self)
        self.binEdit.setReadOnly(True)
        resultLayout.addWidget(self.binEdit, 0, 1)
        
        # 八进制结果
        octLabel = BodyLabel('八进制 (OCT):', self)
        octLabel.setFont(QFont("", 10, QFont.Bold))
        resultLayout.addWidget(octLabel, 1, 0)
        self.octEdit = LineEdit(self)
        self.octEdit.setReadOnly(True)
        resultLayout.addWidget(self.octEdit, 1, 1)
        
        # 十进制结果
        decLabel = BodyLabel('十进制 (DEC):', self)
        decLabel.setFont(QFont("", 10, QFont.Bold))
        resultLayout.addWidget(decLabel, 2, 0)
        self.decEdit = LineEdit(self)
        self.decEdit.setReadOnly(True)
        resultLayout.addWidget(self.decEdit, 2, 1)
        
        # 十六进制结果
        hexLabel = BodyLabel('十六进制 (HEX):', self)
        hexLabel.setFont(QFont("", 10, QFont.Bold))
        resultLayout.addWidget(hexLabel, 3, 0)
        self.hexEdit = LineEdit(self)
        self.hexEdit.setReadOnly(True)
        resultLayout.addWidget(self.hexEdit, 3, 1)
        
        self.viewLayout.addWidget(resultFrame)
        
        # 关闭按钮
        btnCloseFrame = QFrame(self)
        btnCloseLayout = QHBoxLayout(btnCloseFrame)
        btnCloseLayout.setContentsMargins(0, 10, 0, 0)
        btnCloseLayout.addStretch()
        
        self.closeBtn = PushButton('关闭', self)
        self.closeBtn.clicked.connect(self.close)
        btnCloseLayout.addWidget(self.closeBtn)
        
        self.viewLayout.addWidget(btnCloseFrame)
    
    def get_base(self) -> int:
        """获取当前选择的进制"""
        index = self.baseCombo.currentIndex()
        bases = [2, 8, 10, 16]
        return bases[index]
    
    def on_input_changed(self):
        """输入改变时自动转换"""
        # 实时转换（可选）
        pass
    
    def convert(self):
        """执行转换"""
        input_text = self.inputEdit.text().strip()
        if not input_text:
            self.show_info('请输入数值', 'warning')
            return
        
        base = self.get_base()
        
        try:
            # 清理输入
            input_clean = input_text.replace(' ', '')
            if base == 16:
                input_clean = input_clean.replace('0x', '').replace('0X', '')
            elif base == 2:
                input_clean = input_clean.replace('0b', '').replace('0B', '')
            elif base == 8:
                input_clean = input_clean.replace('0o', '').replace('0O', '')
            
            # 转换为十进制整数
            value = int(input_clean, base)
            
            # 处理负数
            if value < 0:
                self.show_info('暂不支持负数转换', 'warning')
                return
            
            # 显示各进制结果
            self.binEdit.setText(bin(value)[2:])  # 去掉 '0b' 前缀
            self.octEdit.setText(oct(value)[2:])  # 去掉 '0o' 前缀
            self.decEdit.setText(str(value))
            self.hexEdit.setText(hex(value)[2:].upper())  # 去掉 '0x' 前缀并大写
            
            self.show_info('转换成功', 'success')
            
        except ValueError:
            base_names = {2: '二进制', 8: '八进制', 10: '十进制', 16: '十六进制'}
            self.show_info(f'无效的 {base_names[base]} 数值', 'error')
            self.clear_results()
    
    def clear_results(self):
        """清空结果"""
        self.binEdit.clear()
        self.octEdit.clear()
        self.decEdit.clear()
        self.hexEdit.clear()
    
    def show_info(self, message: str, info_type: str = 'info'):
        """显示信息提示"""
        if info_type == 'success':
            InfoBar.success(
                title='成功',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        elif info_type == 'warning':
            InfoBar.warning(
                title='提示',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        elif info_type == 'error':
            InfoBar.error(
                title='错误',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )


class ChecksumCalculatorDialog(QDialog):
    """校验码计算器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('校验码计算器')
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(700, 600)
        self.setMinimumSize(500, 450)
        self.setSizeGripEnabled(True)
        # 应用主题样式
        self.setStyleSheet(get_dialog_stylesheet())
        
        # 主布局
        self.viewLayout = QVBoxLayout(self)
        self.viewLayout.setContentsMargins(20, 20, 20, 20)
        self.viewLayout.setSpacing(10)
        
        # 标题
        self.titleLabel = SubtitleLabel('校验码计算器', self)
        self.viewLayout.addWidget(self.titleLabel)
        
        # 说明
        self.descLabel = BodyLabel('输入 HEX 数据，选择校验算法计算校验码', self)
        self.descLabel.setTextColor("#888888", "#888888")
        self.viewLayout.addWidget(self.descLabel)
        
        # 输入区域
        inputFrame = QFrame(self)
        inputLayout = QVBoxLayout(inputFrame)
        inputLayout.setContentsMargins(0, 10, 0, 0)
        
        inputLabel = BodyLabel('HEX 数据 (十六进制)', self)
        inputLabel.setFont(QFont("", 10, QFont.Bold))
        inputLayout.addWidget(inputLabel)
        
        self.inputEdit = TextEdit(self)
        self.inputEdit.setPlaceholderText('输入 HEX 数据，如: AA BB 01 02 03 04 或 AABB01020304')
        self.inputEdit.setMinimumHeight(100)
        inputLayout.addWidget(self.inputEdit)
        
        self.viewLayout.addWidget(inputFrame)
        
        # 校验类型选择
        typeFrame = QFrame(self)
        typeLayout = QHBoxLayout(typeFrame)
        typeLayout.setContentsMargins(0, 5, 0, 5)
        
        typeLabel = BodyLabel('校验类型:', self)
        typeLabel.setFont(QFont("", 10, QFont.Bold))
        typeLayout.addWidget(typeLabel)
        
        self.checksumTypeCombo = ComboBox(self)
        self.checksumTypeCombo.addItems([
            "累加和", "累加和16位", "累加和(取低字节)",
            "异或校验", "异或校验16位",
            "CRC-8", "CRC-8/ITU", "CRC-8/ROHC", "CRC-8/MAXIM",
            "CRC-16/MODBUS", "CRC-16/IBM", "CRC-16/CCITT", "CRC-16/CCITT-FALSE",
            "CRC-16/XMODEM", "CRC-16/X25", "CRC-16/DNP", "CRC-16/USB", "CRC-16/MAXIM",
            "CRC-32", "CRC-32/MPEG-2", "CRC-32/POSIX",
            "LRC", "BCC"
        ])
        self.checksumTypeCombo.setMinimumWidth(200)
        typeLayout.addWidget(self.checksumTypeCombo, 1)
        
        self.viewLayout.addWidget(typeFrame)
        
        # 计算按钮
        self.calcBtn = PushButton('计算校验码', self)
        self.calcBtn.setIcon(FIF.ACCEPT)
        self.calcBtn.clicked.connect(self.calculate)
        self.viewLayout.addWidget(self.calcBtn)
        
        # 结果区域
        resultFrame = QFrame(self)
        resultLayout = QVBoxLayout(resultFrame)
        resultLayout.setContentsMargins(0, 10, 0, 0)
        
        resultLabel = BodyLabel('计算结果', self)
        resultLabel.setFont(QFont("", 10, QFont.Bold))
        resultLayout.addWidget(resultLabel)
        
        self.resultEdit = TextEdit(self)
        self.resultEdit.setReadOnly(True)
        self.resultEdit.setMinimumHeight(150)
        resultLayout.addWidget(self.resultEdit)
        
        self.viewLayout.addWidget(resultFrame)
        
        # 底部弹性空间
        self.viewLayout.addStretch()
    
    def calculate(self):
        """计算校验码"""
        input_text = self.inputEdit.toPlainText().strip()
        if not input_text:
            self.show_info('请输入 HEX 数据', 'warning')
            return
        
        try:
            # 解析 HEX 数据
            hex_str = input_text.replace(' ', '').replace('\n', '').replace('\r', '')
            if len(hex_str) % 2 != 0:
                self.show_info('HEX 数据长度必须为偶数', 'error')
                return
            
            data = bytes.fromhex(hex_str)
            
            checksum_type = self.checksumTypeCombo.currentText()
            
            # 导入校验计算模块
            from core.checksum import ChecksumCalculator
            from models.protocol import ChecksumType
            
            # 类型映射
            type_map = {
                "累加和": ChecksumType.SUM,
                "累加和16位": ChecksumType.SUM16,
                "累加和(取低字节)": ChecksumType.SUM,
                "异或校验": ChecksumType.XOR,
                "异或校验16位": ChecksumType.XOR16,
                "CRC-8": ChecksumType.CRC8,
                "CRC-8/ITU": ChecksumType.CRC8_ITU,
                "CRC-8/ROHC": ChecksumType.CRC8_ROHC,
                "CRC-8/MAXIM": ChecksumType.CRC8_MAXIM,
                "CRC-16/MODBUS": ChecksumType.CRC16_MODBUS,
                "CRC-16/IBM": ChecksumType.CRC16_IBM,
                "CRC-16/CCITT": ChecksumType.CRC16_CCITT,
                "CRC-16/CCITT-FALSE": ChecksumType.CRC16_CCITT_FALSE,
                "CRC-16/XMODEM": ChecksumType.CRC16_XMODEM,
                "CRC-16/X25": ChecksumType.CRC16_X25,
                "CRC-16/DNP": ChecksumType.CRC16_DNP,
                "CRC-16/USB": ChecksumType.CRC16_USB,
                "CRC-16/MAXIM": ChecksumType.CRC16_MAXIM,
                "CRC-32": ChecksumType.CRC32,
                "CRC-32/MPEG-2": ChecksumType.CRC32_MPEG2,
                "CRC-32/POSIX": ChecksumType.CRC32_POSIX,
                "LRC": ChecksumType.LRC,
                "BCC": ChecksumType.BCC,
            }
            
            cs_type = type_map.get(checksum_type, ChecksumType.SUM)
            
            # 计算校验码
            result = ChecksumCalculator.calculate(data, cs_type)
            
            # 格式化结果
            result_lines = []
            result_lines.append(f"输入数据: {' '.join(f'{b:02X}' for b in data)}")
            result_lines.append(f"数据长度: {len(data)} 字节")
            result_lines.append(f"校验类型: {checksum_type}")
            result_lines.append("-" * 40)
            
            if isinstance(result, int):
                # 根据校验类型确定字节数
                if "16" in checksum_type or "MODBUS" in checksum_type or "CCITT" in checksum_type or "XMODEM" in checksum_type or "X25" in checksum_type or "DNP" in checksum_type or "USB" in checksum_type or "MAXIM" in checksum_type:
                    byte_count = 2
                elif "32" in checksum_type:
                    byte_count = 4
                else:
                    byte_count = 1
                
                result_lines.append(f"校验码 (十进制): {result}")
                result_lines.append(f"校验码 (十六进制): 0x{result:0{byte_count*2}X}")
                
                # 显示大端小端格式
                if byte_count == 2:
                    high_byte = (result >> 8) & 0xFF
                    low_byte = result & 0xFF
                    result_lines.append(f"校验码 (大端): {high_byte:02X} {low_byte:02X}")
                    result_lines.append(f"校验码 (小端): {low_byte:02X} {high_byte:02X}")
                elif byte_count == 4:
                    b0 = result & 0xFF
                    b1 = (result >> 8) & 0xFF
                    b2 = (result >> 16) & 0xFF
                    b3 = (result >> 24) & 0xFF
                    result_lines.append(f"校验码 (大端): {b3:02X} {b2:02X} {b1:02X} {b0:02X}")
                    result_lines.append(f"校验码 (小端): {b0:02X} {b1:02X} {b2:02X} {b3:02X}")
                
                # 累加和取低字节的特殊处理
                if checksum_type == "累加和(取低字节)":
                    low_byte = result & 0xFF
                    result_lines.append(f"低字节: 0x{low_byte:02X}")
            else:
                result_lines.append(f"校验码: {result}")
            
            self.resultEdit.setPlainText('\n'.join(result_lines))
            self.show_info('计算完成', 'success')
            
        except ValueError as e:
            self.show_info(f'HEX 格式错误: {str(e)}', 'error')
        except Exception as e:
            self.show_info(f'计算失败: {str(e)}', 'error')
            import traceback
            traceback.print_exc()
    
    def show_info(self, message: str, info_type: str = 'success'):
        """显示提示信息"""
        if info_type == 'success':
            InfoBar.success(
                title='成功',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self
            )
        elif info_type == 'warning':
            InfoBar.warning(
                title='提示',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        elif info_type == 'error':
            InfoBar.error(
                title='错误',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )