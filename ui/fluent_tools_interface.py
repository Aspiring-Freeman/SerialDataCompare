# -*- coding: utf-8 -*-
"""
小工具界面 - 显示工具卡片，点击打开对应工具对话框
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

from qfluentwidgets import (
    ScrollArea, TitleLabel, BodyLabel, CardWidget,
    IconWidget, FluentIcon as FIF, isDarkTheme
)

from ui.tool_dialogs import HexAsciiConverterDialog, BaseConverterDialog, ChecksumCalculatorDialog, HexLogExtractorDialog


class ToolCard(CardWidget):
    """工具卡片组件"""
    
    toolClicked = Signal()  # 重命名避免与CardWidget的clicked冲突
    
    def __init__(self, icon, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 160)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._is_clicking = False  # 防止双重触发
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 图标
        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(40, 40)
        layout.addWidget(self.iconWidget, 0, Qt.AlignLeft)
        
        # 标题
        self.titleLabel = BodyLabel(title, self)
        self.titleLabel.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(self.titleLabel)
        
        # 描述
        self.descLabel = BodyLabel(description, self)
        self.descLabel.setWordWrap(True)
        self.descLabel.setTextColor("#666666", "#aaaaaa")
        layout.addWidget(self.descLabel)
        
        layout.addStretch()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放时触发点击"""
        if event.button() == Qt.LeftButton and not self._is_clicking:
            self._is_clicking = True
            self.toolClicked.emit()
            # 使用定时器重置状态，防止快速点击
            from PySide6.QtCore import QTimer
            QTimer.singleShot(300, lambda: setattr(self, '_is_clicking', False))
        super().mouseReleaseEvent(event)


class ToolsInterface(ScrollArea):
    """小工具界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toolsInterface")
        self.setWidgetResizable(True)
        
        # 主容器
        self.container = QWidget()
        self.setWidget(self.container)
        
        # 主布局
        self.mainLayout = QVBoxLayout(self.container)
        self.mainLayout.setContentsMargins(36, 20, 36, 20)
        self.mainLayout.setSpacing(20)
        
        # 初始化界面
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 标题
        titleLabel = TitleLabel('小工具', self)
        self.mainLayout.addWidget(titleLabel)
        
        # 描述
        descLabel = BodyLabel('实用的数据转换、计算和分析工具', self)
        descLabel.setTextColor("#666666", "#aaaaaa")
        self.mainLayout.addWidget(descLabel)
        
        # 分隔
        self.mainLayout.addSpacing(10)
        
        # 工具卡片区域
        cardsFrame = QFrame(self)
        cardsLayout = QHBoxLayout(cardsFrame)
        cardsLayout.setContentsMargins(0, 0, 0, 0)
        cardsLayout.setSpacing(20)
        cardsLayout.setAlignment(Qt.AlignLeft)
        
        # HEX/ASCII 转换器卡片
        self.hexAsciiCard = ToolCard(
            FIF.CODE,
            'HEX ↔ ASCII',
            '十六进制与 ASCII 文本互转',
            self
        )
        self.hexAsciiCard.toolClicked.connect(self.open_hex_ascii_converter)
        cardsLayout.addWidget(self.hexAsciiCard)
        
        # 进制转换器卡片
        self.baseCard = ToolCard(
            FIF.CALORIES,
            '进制转换',
            '二/八/十/十六进制互转',
            self
        )
        self.baseCard.toolClicked.connect(self.open_base_converter)
        cardsLayout.addWidget(self.baseCard)
        
        # 校验码计算器卡片
        self.checksumCard = ToolCard(
            FIF.CHECKBOX,
            '校验码计算',
            '计算各种校验码(CRC/SUM/XOR等)',
            self
        )
        self.checksumCard.toolClicked.connect(self.open_checksum_calculator)
        cardsLayout.addWidget(self.checksumCard)
        
        # HEX日志提取器卡片
        self.hexLogCard = ToolCard(
            FIF.SCROLL,
            'HEX日志提取',
            '从串口日志中提取HEX数据帧',
            self
        )
        self.hexLogCard.toolClicked.connect(self.open_hex_log_extractor)
        cardsLayout.addWidget(self.hexLogCard)
        
        # 预留更多工具位置
        cardsLayout.addStretch()
        
        self.mainLayout.addWidget(cardsFrame)
        
        # 底部弹性空间
        self.mainLayout.addStretch()
    
    def open_hex_ascii_converter(self):
        """打开 HEX/ASCII 转换器"""
        dialog = HexAsciiConverterDialog(self.window())
        dialog.show()
    
    def open_base_converter(self):
        """打开进制转换器"""
        dialog = BaseConverterDialog(self.window())
        dialog.show()
    
    def open_checksum_calculator(self):
        """打开校验码计算器"""
        dialog = ChecksumCalculatorDialog(self.window())
        dialog.show()
    
    def open_hex_log_extractor(self):
        """打开HEX日志提取器"""
        dialog = HexLogExtractorDialog(self.window())
        dialog.show()
