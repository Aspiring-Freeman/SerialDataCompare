# This Python file uses the following encoding: utf-8
"""
日志界面 - Fluent Design
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PySide6.QtCore import Qt
from datetime import datetime

from qfluentwidgets import (
    ScrollArea, CardWidget, PushButton, TextEdit, ComboBox,
    TitleLabel, FluentIcon as FIF, InfoBar, InfoBarPosition
)

from utils.theme_helper import ThemeHelper as TH


class LogInterface(QWidget):
    """日志界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log_interface")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 创建UI
        self.create_log_card()
        
        # 添加弹性空间
        main_layout.addStretch()
    
    def create_log_card(self):
        """创建日志卡片"""
        self.log_card = CardWidget(self)
        card_layout = QVBoxLayout(self.log_card)
        card_layout.setSpacing(15)
        
        # 标题和控制
        title_layout = QHBoxLayout()
        title = TitleLabel("系统日志")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 级别过滤
        self.level_combo = ComboBox()
        self.level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        title_layout.addWidget(self.level_combo)
        
        # 清空按钮
        clear_btn = PushButton(FIF.DELETE, "清空")
        clear_btn.clicked.connect(self.clear_logs)
        title_layout.addWidget(clear_btn)
        
        # 导出按钮
        export_btn = PushButton(FIF.SAVE, "导出")
        export_btn.clicked.connect(self.export_logs)
        title_layout.addWidget(export_btn)
        
        card_layout.addLayout(title_layout)
        
        # 日志文本
        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(600)
        # 限制最大行数，防止长时间运行后内存膨胀和界面卡顿
        self.log_text.document().setMaximumBlockCount(2000)
        card_layout.addWidget(self.log_text)
        
        self.layout().addWidget(self.log_card)
    
    def add_log(self, level: str, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据级别设置颜色
        color_map = TH.log_color_map()
        color = color_map.get(level, TH.info_log_color())
        
        log_html = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span><br>'
        self.log_text.append(log_html)
    
    def filter_logs(self):
        """过滤日志"""
        # TODO: 实现日志过滤
        pass
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.clear()
        InfoBar.success(
            title="成功",
            content="日志已清空",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def export_logs(self):
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                
                InfoBar.success(
                    title="成功",
                    content=f"日志已导出到 {file_path}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"导出失败: {str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
