# -*- coding: utf-8 -*-
"""
Fluent UI 增强组件
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, BodyLabel, ToolTipFilter, ToolTipPosition
)


def set_fluent_tooltip(widget: QWidget, text: str,
                       position: ToolTipPosition = ToolTipPosition.TOP):
    """
    为控件设置 Fluent Design 风格的工具提示
    
    使用 qfluentwidgets 的 ToolTipFilter 替代原生 Qt tooltip，
    避免黑框等显示问题。
    
    Args:
        widget: 目标控件
        text: 提示文本
        position: 提示位置（TOP, BOTTOM, LEFT, RIGHT）
    """
    widget.setToolTip(text)
    widget.installEventFilter(ToolTipFilter(widget, showDelay=300, position=position))


class FluentDialogBase(MessageBoxBase):
    """
    Fluent Design 风格对话框基类
    
    继承自 qfluentwidgets.MessageBoxBase，统一对话框外观：
    - 自动设置标题和描述
    - 提供内容区域布局 (self.content_layout)
    - 支持自定义按钮文本
    
    用法:
        class MyDialog(FluentDialogBase):
            def __init__(self, parent=None):
                super().__init__("标题", "描述", parent)
                # 添加控件到 self.content_layout
                self.my_input = LineEdit()
                self.content_layout.addWidget(self.my_input)
    """
    
    def __init__(self, title: str, description: str = "",
                 parent=None, ok_text: str = "确定", cancel_text: str = "取消"):
        super().__init__(parent)
        
        # 标题
        self.title_label = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.title_label)
        
        # 描述
        if description:
            self.desc_label = BodyLabel(description, self)
            self.desc_label.setWordWrap(True)
            self.viewLayout.addWidget(self.desc_label)
        
        # 内容区域布局（子类在此添加控件）
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self.viewLayout.addLayout(self.content_layout)
        
        # 设置按钮文本
        self.yesButton.setText(ok_text)
        self.cancelButton.setText(cancel_text)
        
        # 设置最小宽度
        self.widget.setMinimumWidth(400)