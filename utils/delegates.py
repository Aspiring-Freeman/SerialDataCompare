"""
自定义表格委托
"""
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox
from PySide6.QtCore import Qt


class ComboBoxDelegate(QStyledItemDelegate):
    """下拉框委托，用于表格单元格"""
    
    def __init__(self, items, parent=None):
        """
        初始化
        
        Args:
            items: 下拉框选项列表
            parent: 父对象
        """
        super().__init__(parent)
        self.items = items
    
    def createEditor(self, parent, option, index):
        """创建编辑器"""
        combo = QComboBox(parent)
        combo.addItems(self.items)
        return combo
    
    def setEditorData(self, editor, index):
        """设置编辑器数据"""
        if isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.ItemDataRole.EditRole)
            idx = editor.findText(value)
            if idx >= 0:
                editor.setCurrentIndex(idx)
    
    def setModelData(self, editor, model, index):
        """从编辑器获取数据并设置到模型"""
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
    
    def updateEditorGeometry(self, editor, option, index):
        """更新编辑器几何形状"""
        editor.setGeometry(option.rect)
