"""
历史记录查看对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QTextEdit, QSplitter,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from core.analysis_history import AnalysisHistory


class HistoryDialog(QDialog):
    """历史记录对话框"""
    
    def __init__(self, history_manager: AnalysisHistory, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle("分析历史记录")
        self.resize(900, 600)
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 历史记录表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "时间", "协议", "总帧数", "有效帧", "错误帧", "输入数据"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.table)
        
        # 详细信息
        detail_widget = QTextEdit()
        detail_widget.setReadOnly(True)
        self.detail_text = detail_widget
        splitter.addWidget(detail_widget)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.btn_clear = QPushButton("清空历史")
        self.btn_clear.clicked.connect(self.on_clear_clicked)
        btn_layout.addWidget(self.btn_clear)
        
        btn_layout.addStretch()
        
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
    
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
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_history()
            self.load_history()
            self.detail_text.clear()
            QMessageBox.information(self, "成功", "历史记录已清空！")
