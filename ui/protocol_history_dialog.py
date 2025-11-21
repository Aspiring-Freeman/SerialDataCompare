"""
协议历史记录查看对话框
"""
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, BodyLabel, 
    ListWidget, PushButton, TextEdit,
    MessageBox
)
from core.protocol_history import ProtocolHistory
import os


class ProtocolHistoryDialog(MessageBoxBase):
    """协议历史记录对话框"""
    
    protocol_selected = Signal(str)  # 发送选中的协议文件路径
    
    def __init__(self, history_manager: ProtocolHistory, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.titleLabel = SubtitleLabel("协议历史记录", self)
        self.setup_ui()
        self.load_history()
        
        # 设置对话框大小
        self.widget.setMinimumWidth(700)
        self.widget.setMinimumHeight(500)
    
    def setup_ui(self):
        """设置UI"""
        # 协议列表标题
        list_label = BodyLabel("📜 最近使用的协议:")
        list_label.setStyleSheet("font-weight: bold;")
        self.viewLayout.addWidget(list_label)
        
        # 协议列表
        self.list_widget = ListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.list_widget.setMinimumHeight(200)
        self.viewLayout.addWidget(self.list_widget)
        
        # 详细信息标题
        detail_label = BodyLabel("📋 协议信息:")
        detail_label.setStyleSheet("font-weight: bold;")
        self.viewLayout.addWidget(detail_label)
        
        # 详细信息文本
        self.detail_text = TextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(100)
        self.viewLayout.addWidget(self.detail_text)
        
        # 添加按钮
        self.btn_load = PushButton("加载选中协议")
        self.btn_load.setEnabled(False)
        self.btn_load.clicked.connect(self.on_load_clicked)
        
        self.btn_clear = PushButton("清空历史")
        self.btn_clear.clicked.connect(self.on_clear_clicked)
        
        # 添加按钮到底部
        self.yesButton.setText("关闭")
        self.yesButton.clicked.connect(lambda: self.accept())
        
        self.buttonGroup.layout().addWidget(self.btn_load)
        self.buttonGroup.layout().addWidget(self.btn_clear)
    
    def load_history(self):
        """加载历史记录"""
        self.list_widget.clear()
        history = self.history_manager.get_history()
        
        for record in history:
            name = record.get('name', '')
            path = record.get('path', '')
            
            # 检查文件是否存在
            exists = os.path.exists(path)
            
            # 创建列表项
            item = QListWidgetItem()
            if exists:
                item.setText(f"✓ {name}")
            else:
                item.setText(f"❌ {name} (文件不存在)")
                item.setForeground(Qt.GlobalColor.gray)
            
            item.setData(Qt.ItemDataRole.UserRole, record)
            self.list_widget.addItem(item)
    
    def on_selection_changed(self):
        """选择改变"""
        items = self.list_widget.selectedItems()
        if not items:
            self.btn_load.setEnabled(False)
            self.detail_text.clear()
            return
        
        item = items[0]
        record = item.data(Qt.ItemDataRole.UserRole)
        
        # 显示详细信息
        name = record.get('name', '')
        path = record.get('path', '')
        exists = os.path.exists(path)
        
        details = []
        details.append(f"协议名称: {name}")
        details.append(f"文件路径: {path}")
        details.append(f"文件状态: {'✓ 存在' if exists else '❌ 不存在'}")
        
        if exists:
            # 获取文件大小和修改时间
            try:
                size = os.path.getsize(path)
                mtime = os.path.getmtime(path)
                from datetime import datetime
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                details.append(f"文件大小: {size} 字节")
                details.append(f"修改时间: {mtime_str}")
            except Exception as e:
                details.append(f"获取文件信息失败: {e}")
        
        self.detail_text.setText('\n'.join(details))
        self.btn_load.setEnabled(exists)
    
    def on_item_double_clicked(self, item):
        """双击项目"""
        record = item.data(Qt.ItemDataRole.UserRole)
        path = record.get('path', '')
        
        if os.path.exists(path):
            self.protocol_selected.emit(path)
            self.accept()
    
    def on_load_clicked(self):
        """加载按钮点击"""
        items = self.list_widget.selectedItems()
        if not items:
            return
        
        item = items[0]
        record = item.data(Qt.ItemDataRole.UserRole)
        path = record.get('path', '')
        
        if os.path.exists(path):
            self.protocol_selected.emit(path)
            self.accept()
    
    def on_clear_clicked(self):
        """清空历史"""
        w = MessageBox("确认", "确定要清空所有协议历史记录吗？", self.window())
        if w.exec():
            self.history_manager.clear_history()
            self.load_history()
            self.detail_text.clear()
            MessageBox("成功", "协议历史记录已清空！", self.window()).exec()
