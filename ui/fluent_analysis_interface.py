# This Python file uses the following encoding: utf-8
"""
数据分析界面 - Fluent Design
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem
from PySide6.QtCore import Signal, Qt

from qfluentwidgets import (
    ScrollArea, CardWidget, PushButton, TextEdit, TableWidget,
    TitleLabel, BodyLabel, FluentIcon as FIF, InfoBar, InfoBarPosition
)

from models import ParseResult


class AnalysisInterface(QWidget):
    """数据分析界面"""
    
    analysis_started = Signal(str)
    frame_selected = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("analysis_interface")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 创建滚动区域
        from qfluentwidgets import ScrollArea
        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none}")
        
        # 滚动区域内容
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建UI
        self.create_input_card()
        self.create_result_card()
        
        # 设置滚动区域
        scroll.setWidget(self.scroll_widget)
        main_layout.addWidget(scroll)
        
        # 当前协议
        self.current_protocol = None
    
    def create_input_card(self):
        """创建输入卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = TitleLabel("数据输入")
        card_layout.addWidget(title)
        
        # 输入框布局(带说明)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(15)
        
        # 左侧输入区域
        input_left = QVBoxLayout()
        input_left.setSpacing(10)
        
        input_label = BodyLabel("Hex 数据:")
        input_label.setMinimumWidth(80)
        input_left.addWidget(input_label)
        
        self.input_text = TextEdit()
        self.input_text.setPlaceholderText("例如: AA BB 01 02 03 04 0D 0A")
        self.input_text.setMinimumHeight(150)
        input_left.addWidget(self.input_text)
        
        input_layout.addLayout(input_left, 3)
        
        # 右侧说明区域
        hint_layout = QVBoxLayout()
        hint_layout.setSpacing(8)
        hint_layout.setContentsMargins(10, 0, 0, 0)
        
        hint_title = BodyLabel("📋 输入说明:")
        hint_title.setStyleSheet("font-weight: bold; color: #0078D4;")
        hint_layout.addWidget(hint_title)
        
        hint1 = BodyLabel("• 支持空格分隔的16进制格式")
        hint2 = BodyLabel("• 例: AA BB CC DD")
        hint3 = BodyLabel("• 或: AABBCCDD")
        hint4 = BodyLabel("• 自动识别帧头帧尾")
        hint5 = BodyLabel("• 支持多帧数据批量分析")
        
        for hint in [hint1, hint2, hint3, hint4, hint5]:
            hint.setStyleSheet("color: #606060; font-size: 13px;")
            hint_layout.addWidget(hint)
        
        hint_layout.addStretch()
        input_layout.addLayout(hint_layout, 2)
        
        card_layout.addLayout(input_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        analyze_btn = PushButton(FIF.SEARCH, "开始分析")
        analyze_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(analyze_btn)
        
        clear_btn = PushButton(FIF.DELETE, "清空")
        clear_btn.clicked.connect(self.input_text.clear)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        card_layout.addLayout(button_layout)
        
        self.scroll_layout.addWidget(card)
    
    def create_result_card(self):
        """创建结果卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题和操作栏
        title_layout = QHBoxLayout()
        title = TitleLabel("分析结果")
        title_layout.addWidget(title)
        
        # 说明文字
        hint_label = BodyLabel("💡 点击表格行可查看详细信息")
        hint_label.setStyleSheet("color: #606060; font-size: 13px; margin-left: 20px;")
        title_layout.addWidget(hint_label)
        
        title_layout.addStretch()
        
        # 导出按钮
        export_txt_btn = PushButton(FIF.DOCUMENT, "导出TXT")
        export_txt_btn.clicked.connect(self.export_txt)
        title_layout.addWidget(export_txt_btn)
        
        export_csv_btn = PushButton(FIF.DOCUMENT, "导出CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        title_layout.addWidget(export_csv_btn)
        
        card_layout.addLayout(title_layout)
        
        # 结果表格
        self.result_table = TableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels([
            "帧序号", "起始位置", "结束位置", "原始数据", "解析结果"
        ])
        self.result_table.setMinimumHeight(400)
        
        # 设置列宽
        self.result_table.setColumnWidth(0, 80)
        self.result_table.setColumnWidth(1, 90)
        self.result_table.setColumnWidth(2, 90)
        self.result_table.setColumnWidth(3, 400)
        self.result_table.setColumnWidth(4, 300)
        
        # 连接选择信号
        self.result_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        card_layout.addWidget(self.result_table)
        
        # 底部说明栏
        bottom_hint_layout = QHBoxLayout()
        bottom_hint_layout.setSpacing(20)
        
        hint_icon1 = BodyLabel("📊")
        hint_text1 = BodyLabel("帧序号: 数据帧的顺序编号")
        hint_text1.setStyleSheet("color: #606060; font-size: 12px;")
        bottom_hint_layout.addWidget(hint_icon1)
        bottom_hint_layout.addWidget(hint_text1)
        
        hint_icon2 = BodyLabel("📍")
        hint_text2 = BodyLabel("位置: 数据帧在原始数据中的字节位置")
        hint_text2.setStyleSheet("color: #606060; font-size: 12px;")
        bottom_hint_layout.addWidget(hint_icon2)
        bottom_hint_layout.addWidget(hint_text2)
        
        hint_icon3 = BodyLabel("🔍")
        hint_text3 = BodyLabel("双击行可查看更多详情")
        hint_text3.setStyleSheet("color: #606060; font-size: 12px;")
        bottom_hint_layout.addWidget(hint_icon3)
        bottom_hint_layout.addWidget(hint_text3)
        
        bottom_hint_layout.addStretch()
        
        card_layout.addLayout(bottom_hint_layout)
        
        self.scroll_layout.addWidget(card)
    
    def set_protocol(self, protocol):
        """设置当前协议"""
        self.current_protocol = protocol
    
    def start_analysis(self):
        """开始分析"""
        hex_data = self.input_text.toPlainText().strip()
        
        if not hex_data:
            InfoBar.warning(
                title="警告",
                content="请输入数据",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        if not self.current_protocol:
            InfoBar.error(
                title="错误",
                content="请先配置协议",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        self.analysis_started.emit(hex_data)
    
    def show_result(self, result: ParseResult):
        """显示分析结果"""
        self.result_table.setRowCount(len(result.frames))
        
        for i, frame in enumerate(result.frames):
            # 帧序号
            self.result_table.setItem(i, 0, QTableWidgetItem(f"{i + 1}"))
            
            # 起始位置
            self.result_table.setItem(i, 1, QTableWidgetItem(f"{frame.start_position}"))
            
            # 结束位置
            self.result_table.setItem(i, 2, QTableWidgetItem(f"{frame.end_position}"))
            
            # 原始数据
            raw_hex = frame.raw_data.hex().upper() if isinstance(frame.raw_data, bytes) else str(frame.raw_data)
            self.result_table.setItem(i, 3, QTableWidgetItem(raw_hex))
            
            # 解析结果
            parsed = ", ".join([
                f"{k}: {v}" for k, v in frame.fields.items()
            ])
            self.result_table.setItem(i, 4, QTableWidgetItem(parsed))
        
        InfoBar.success(
            title="成功",
            content=f"分析完成，找到 {len(result.frames)} 个数据帧",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def on_selection_changed(self):
        """选择改变"""
        selected = self.result_table.currentRow()
        if selected >= 0:
            self.frame_selected.emit(selected)
    
    def export_txt(self):
        """导出TXT"""
        # TODO: 实现导出逻辑
        InfoBar.info(
            title="提示",
            content="导出功能开发中",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def export_csv(self):
        """导出CSV"""
        # TODO: 实现导出逻辑
        InfoBar.info(
            title="提示",
            content="导出功能开发中",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
