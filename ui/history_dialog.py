"""
历史记录查看对话框
"""
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QTableWidgetItem
from PySide6.QtCore import Qt
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, BodyLabel,
    TableWidget, PushButton, TextEdit, MessageBox
)


class HistoryDialog(MessageBoxBase):
    """历史记录对话框"""
    
    def __init__(self, history_manager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.titleLabel = SubtitleLabel("分析历史记录", self)
        self.setup_ui()
        self.load_history()
        
        # 设置对话框大小
        self.widget.setMinimumWidth(900)
        self.widget.setMinimumHeight(600)
    
    def setup_ui(self):
        """设置UI"""
        # 历史记录表格
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "时间", "协议", "总帧数", "有效帧", "错误帧", "输入数据"
        ])
        self.table.setEditEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.setMinimumHeight(300)
        self.viewLayout.addWidget(self.table)
        
        # 详细信息标题
        detail_label = BodyLabel("详细信息:")
        font = detail_label.font()
        font.setBold(True)
        detail_label.setFont(font)
        self.viewLayout.addWidget(detail_label)
        
        # 详细信息文本
        self.detail_text = TextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(150)
        self.viewLayout.addWidget(self.detail_text)
        
        # 添加按钮
        self.btn_clear = PushButton("清空历史")
        self.btn_clear.clicked.connect(self.on_clear_clicked)
        
        # 添加按钮到底部
        self.yesButton.setText("关闭")
        self.yesButton.clicked.connect(lambda: self.accept())
        
        self.buttonGroup.layout().addWidget(self.btn_clear)
    
    def load_history(self):
        """加载历史记录"""
        history = self.history_manager.get_history()
        self.table.setRowCount(len(history))
        
        for row, record in enumerate(history):
            # 时间
            timestamp = self.history_manager.format_timestamp(record.get('timestamp', ''))
            self.table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # 协议
            self.table.setItem(row, 1, QTableWidgetItem(record.get('protocol_name', '')))
            
            # 总帧数
            self.table.setItem(row, 2, QTableWidgetItem(str(record.get('total_frames', 0))))
            
            # 有效帧
            self.table.setItem(row, 3, QTableWidgetItem(str(record.get('valid_frames', 0))))
            
            # 错误帧
            self.table.setItem(row, 4, QTableWidgetItem(str(record.get('error_frames', 0))))
            
            # 输入数据（截断显示）
            input_data = record.get('input_data', '')
            self.table.setItem(row, 5, QTableWidgetItem(input_data))
        
        self.table.resizeColumnsToContents()
    
    def on_selection_changed(self):
        """选择改变"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        # 兼容 AnalysisHistoryDB（按索引获取）和旧 AnalysisHistory（直接索引）
        if hasattr(self.history_manager, 'get_record_by_index'):
            record = self.history_manager.get_record_by_index(row)
        else:
            record = self.history_manager.get_record(row)
        
        if record:
            # 显示详细信息
            details = []
            details.append(f"分析时间: {self.history_manager.format_timestamp(record.get('timestamp', ''))}")
            details.append(f"协议名称: {record.get('protocol_name', '')}")
            details.append(f"总帧数: {record.get('total_frames', 0)}")
            details.append(f"有效帧: {record.get('valid_frames', 0)}")
            details.append(f"错误帧: {record.get('error_frames', 0)}")
            details.append("")
            details.append("输入数据:")
            details.append(record.get('input_data', ''))
            details.append("")
            details.append("帧摘要:")
            
            for frame_summary in record.get('frame_summary', []):
                frame_num = frame_summary.get('frame_number', 0)
                has_error = frame_summary.get('has_error', False)
                checksum_valid = frame_summary.get('checksum_valid', True)
                raw_data = frame_summary.get('raw_data_hex', '')
                
                status = "❌ 错误" if has_error else ("✓ 正常" if checksum_valid else "⚠ 校验失败")
                details.append(f"  帧#{frame_num}: {status}")
                details.append(f"    数据: {raw_data}")
            
            self.detail_text.setText('\n'.join(details))
    
    def on_clear_clicked(self):
        """清空历史"""
        w = MessageBox("确认", "确定要清空所有历史记录吗？", self.window())
        if w.exec():
            self.history_manager.clear_history()
            self.load_history()
            self.detail_text.clear()
            MessageBox("成功", "历史记录已清空！", self.window()).exec()
