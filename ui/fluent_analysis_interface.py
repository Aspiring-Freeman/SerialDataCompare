# This Python file uses the following encoding: utf-8
"""
数据分析界面 - Fluent Design
使用 QAbstractTableModel + QTableView 实现虚拟滚动，提升大数据量性能
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt

from qfluentwidgets import (
    ScrollArea, CardWidget, PushButton, TextEdit, TableView,
    TitleLabel, BodyLabel, FluentIcon as FIF, InfoBar, InfoBarPosition
)

from models import ParseResult
from models.frame_table_model import FrameTableModel
from ui.history_dialog import HistoryDialog
from utils.theme_helper import ThemeHelper as TH


class AnalysisInterface(QWidget):
    """数据分析界面"""
    
    analysis_started = Signal(str)
    frame_selected = Signal(int)
    
    def __init__(self, analysis_history=None, parent=None):
        super().__init__(parent)
        self.setObjectName("analysis_interface")
        self.analysis_history = analysis_history
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 创建滚动区域
        from qfluentwidgets import ScrollArea
        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        
        # 滚动区域内容
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建UI
        self.create_input_card()
        self.create_result_card()
        
        # 设置滚动区域（enableTransparentBackground 须在 setWidget 之后调用）
        scroll.setWidget(self.scroll_widget)
        scroll.enableTransparentBackground()
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
        
        self._hint_title = BodyLabel("📋 输入说明:")
        TH.apply_title_accent(self._hint_title)
        hint_layout.addWidget(self._hint_title)
        
        hint1 = BodyLabel("• 支持空格分隔的16进制格式")
        hint2 = BodyLabel("• 例: AA BB CC DD")
        hint3 = BodyLabel("• 或: AABBCCDD")
        hint4 = BodyLabel("• 自动识别帧头帧尾")
        hint5 = BodyLabel("• 支持多帧数据批量分析")
        
        self._hint_items = [hint1, hint2, hint3, hint4, hint5]
        for hint in self._hint_items:
            TH.apply_hint(hint)
            hint_layout.addWidget(hint)
        
        hint_layout.addStretch()
        input_layout.addLayout(hint_layout, 2)
        
        card_layout.addLayout(input_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.analyze_btn = PushButton(FIF.SEARCH, "开始分析")
        self.analyze_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.analyze_btn)
        
        clear_btn = PushButton(FIF.DELETE, "清空")
        clear_btn.clicked.connect(self.input_text.clear)
        button_layout.addWidget(clear_btn)
        
        # 分析历史
        history_btn = PushButton(FIF.HISTORY, "分析历史")
        history_btn.clicked.connect(self.show_analysis_history)
        button_layout.addWidget(history_btn)
        
        button_layout.addStretch()
        
        # 添加提示文本
        self._tip_label = BodyLabel("ℹ️ 提示：点击“开始分析”按钮进行数据解析，非实时分析")
        TH.apply_muted(self._tip_label, italic=True)
        button_layout.addWidget(self._tip_label)
        
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
        self._result_hint = BodyLabel("💡 点击表格行可查看详细信息")
        TH.apply_hint(self._result_hint)
        title_layout.addWidget(self._result_hint)
        
        title_layout.addStretch()
        
        # 导出按钮
        export_txt_btn = PushButton(FIF.DOCUMENT, "导出TXT")
        export_txt_btn.clicked.connect(self.export_txt)
        title_layout.addWidget(export_txt_btn)
        
        export_csv_btn = PushButton(FIF.DOCUMENT, "导出CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        title_layout.addWidget(export_csv_btn)
        
        card_layout.addLayout(title_layout)
        
        # 创建帧数据模型
        self.frame_model = FrameTableModel(self)
        
        # 结果表格 - 使用 qfluentwidgets TableView + FrameTableModel
        self.result_table = TableView()
        self.result_table.setModel(self.frame_model)
        self.result_table.setMinimumHeight(400)
        
        # 设置表格样式
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_table.setShowGrid(True)
        self.result_table.setSortingEnabled(False)  # 暂时禁用排序
        
        # 设置水平表头
        header = self.result_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignCenter)
        
        # 设置列宽
        column_widths = self.frame_model.get_column_widths()
        for i, width in enumerate(column_widths):
            self.result_table.setColumnWidth(i, width)
        
        # 隐藏垂直表头（行号由模型提供）
        self.result_table.verticalHeader().setVisible(False)
        
        # 连接选择信号
        self.result_table.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )
        
        card_layout.addWidget(self.result_table)
        
        # 底部说明栏
        bottom_hint_layout = QHBoxLayout()
        bottom_hint_layout.setSpacing(20)
        
        hint_icon1 = BodyLabel("📊")
        self._hint_text1 = BodyLabel("帧序号: 数据帧的顺序编号")
        TH.apply_hint(self._hint_text1, pixel_size=12)
        bottom_hint_layout.addWidget(hint_icon1)
        bottom_hint_layout.addWidget(self._hint_text1)
        
        hint_icon2 = BodyLabel("📍")
        self._hint_text2 = BodyLabel("位置: 数据帧在原始数据中的字节位置")
        TH.apply_hint(self._hint_text2, pixel_size=12)
        bottom_hint_layout.addWidget(hint_icon2)
        bottom_hint_layout.addWidget(self._hint_text2)
        
        hint_icon3 = BodyLabel("🔍")
        self._hint_text3 = BodyLabel("双击行可查看更多详情")
        TH.apply_hint(self._hint_text3, pixel_size=12)
        bottom_hint_layout.addWidget(hint_icon3)
        bottom_hint_layout.addWidget(self._hint_text3)
        
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
    
    def set_analyzing(self, is_analyzing: bool):
        """设置分析状态，用于线程安全控制
        
        Args:
            is_analyzing: True 表示正在分析，禁用按钮; False 表示分析完成，启用按钮
        """
        self.analyze_btn.setEnabled(not is_analyzing)
        if is_analyzing:
            self.analyze_btn.setText("分析中...")
        else:
            self.analyze_btn.setText("开始分析")
    
    def show_result(self, result: ParseResult):
        """显示分析结果"""
        # 使用模型设置数据，支持虚拟滚动
        self.frame_model.set_frames(result.frames)
        
        InfoBar.success(
            title="成功",
            content=f"分析完成，找到 {len(result.frames)} 个数据帧",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def clear_results(self):
        """清空分析结果"""
        self.frame_model.clear()
    
    def on_selection_changed(self, selected, deselected):
        """表格选择变化"""
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            self.frame_model.set_highlight_row(row)
            self.frame_selected.emit(row)
    
    def get_frame(self, row: int):
        """获取指定行的帧数据"""
        return self.frame_model.get_frame(row)
    
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
    
    def show_analysis_history(self):
        """显示分析历史记录"""
        if not self.analysis_history:
            InfoBar.warning(
                title="未初始化",
                content="分析历史功能未初始化",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        # 创建并显示历史对话框
        dialog = HistoryDialog(self.analysis_history, self)
        dialog.exec()

    def _refresh_styles(self):
        """主题切换后刷新所有样式
        
        注: FluentLabelBase 通过 setTextColor 设置的颜色会自动跟随主题，
        此方法仅作为安全回退，确保主题切换后一致性。
        """
        TH.apply_title_accent(self._hint_title)
        for h in self._hint_items:
            TH.apply_hint(h)
        TH.apply_muted(self._tip_label, italic=True)
        TH.apply_hint(self._result_hint)
        TH.apply_hint(self._hint_text1, pixel_size=12)
        TH.apply_hint(self._hint_text2, pixel_size=12)
        TH.apply_hint(self._hint_text3, pixel_size=12)
