"""
帧数据表格模型 - 基于 QAbstractTableModel 实现虚拟滚动
提供高性能的大数据量表格显示
"""

from typing import List, Optional, Any
from dataclasses import dataclass
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QBrush

from models.data_frame import DataFrame
from models.protocol import format_field_value


@dataclass
class ColumnConfig:
    """列配置"""
    name: str
    width: int
    alignment: Qt.AlignmentFlag = Qt.AlignLeft


class FrameTableModel(QAbstractTableModel):
    """
    帧数据表格模型
    
    使用 QAbstractTableModel 实现虚拟滚动，只在需要时才计算显示数据。
    相比 QTableWidget 可以显著提升大数据量下的性能。
    """
    
    # 列配置
    COLUMNS = [
        ColumnConfig("帧序号", 80, Qt.AlignCenter),
        ColumnConfig("起始位置", 90, Qt.AlignCenter),
        ColumnConfig("结束位置", 90, Qt.AlignCenter),
        ColumnConfig("原始数据", 400, Qt.AlignLeft),
        ColumnConfig("解析结果", 300, Qt.AlignLeft),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._frames: List[DataFrame] = []
        self._display_cache: dict = {}  # 缓存已计算的显示数据
        self._highlight_row: int = -1  # 高亮行
        self._alternate_row_colors = True
        
    def set_frames(self, frames: List[DataFrame]):
        """设置帧数据"""
        self.beginResetModel()
        self._frames = frames if frames else []
        self._display_cache.clear()  # 清空缓存
        self.endResetModel()
    
    def get_frame(self, row: int) -> Optional[DataFrame]:
        """获取指定行的帧数据"""
        if 0 <= row < len(self._frames):
            return self._frames[row]
        return None
    
    def get_frames(self) -> List[DataFrame]:
        """获取所有帧数据"""
        return self._frames
    
    def clear(self):
        """清空数据"""
        self.beginResetModel()
        self._frames.clear()
        self._display_cache.clear()
        self._highlight_row = -1
        self.endResetModel()
    
    def set_highlight_row(self, row: int):
        """设置高亮行"""
        old_row = self._highlight_row
        self._highlight_row = row
        # 只更新变化的行
        if old_row >= 0:
            self.dataChanged.emit(
                self.index(old_row, 0),
                self.index(old_row, self.columnCount() - 1)
            )
        if row >= 0:
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, self.columnCount() - 1)
            )
    
    # ==================== QAbstractTableModel 必须实现的方法 ====================
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回行数"""
        if parent.isValid():
            return 0
        return len(self._frames)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回列数"""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        返回单元格数据
        这是虚拟滚动的核心 - 只在需要显示时才计算数据
        """
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if row < 0 or row >= len(self._frames):
            return None
        
        frame = self._frames[row]
        
        if role == Qt.DisplayRole:
            return self._get_display_data(row, col, frame)
        
        elif role == Qt.TextAlignmentRole:
            return self.COLUMNS[col].alignment
        
        elif role == Qt.BackgroundRole:
            # 高亮行
            if row == self._highlight_row:
                return QBrush(QColor(0, 120, 212, 50))  # 半透明蓝色
            # 交替行颜色
            if self._alternate_row_colors and row % 2 == 1:
                return QBrush(QColor(245, 245, 245))
        
        elif role == Qt.ForegroundRole:
            # 校验失败的帧显示红色
            if hasattr(frame, 'checksum_valid') and frame.checksum_valid is False:
                return QBrush(QColor(255, 0, 0))
        
        elif role == Qt.ToolTipRole:
            # 为原始数据列提供完整的tooltip
            if col == 3:
                raw_hex = self._get_raw_hex(frame)
                if len(raw_hex) > 50:
                    return raw_hex
        
        elif role == Qt.UserRole:
            # 返回原始帧数据
            return frame
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """返回表头数据"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal and 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section].name
            elif orientation == Qt.Vertical:
                return str(section + 1)
        
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        
        return None
    
    # ==================== 辅助方法 ====================
    
    def _get_display_data(self, row: int, col: int, frame: DataFrame) -> str:
        """
        获取显示数据，带缓存
        """
        cache_key = (row, col)
        if cache_key in self._display_cache:
            return self._display_cache[cache_key]
        
        value = self._calculate_display_data(col, frame)
        self._display_cache[cache_key] = value
        return value
    
    def _calculate_display_data(self, col: int, frame: DataFrame) -> str:
        """计算显示数据"""
        if col == 0:
            # 帧序号
            return str(frame.frame_number)
        elif col == 1:
            # 起始位置
            return str(frame.start_position)
        elif col == 2:
            # 结束位置
            return str(frame.end_position)
        elif col == 3:
            # 原始数据
            return self._get_raw_hex(frame)
        elif col == 4:
            # 解析结果
            return self._get_parsed_result(frame)
        return ""
    
    def _get_raw_hex(self, frame: DataFrame) -> str:
        """获取原始数据的十六进制字符串"""
        if isinstance(frame.raw_data, bytes):
            return frame.raw_data.hex().upper()
        return str(frame.raw_data)
    
    def _get_parsed_result(self, frame: DataFrame) -> str:
        """获取格式化的解析结果"""
        if not frame.fields:
            return ""
        return ", ".join([
            f"{k}: {format_field_value(v)}" 
            for k, v in frame.fields.items()
        ])
    
    # ==================== 扩展功能 ====================
    
    def get_column_widths(self) -> List[int]:
        """获取推荐的列宽"""
        return [col.width for col in self.COLUMNS]
    
    def set_alternate_row_colors(self, enabled: bool):
        """设置是否启用交替行颜色"""
        self._alternate_row_colors = enabled
        self.layoutChanged.emit()
    
    def refresh(self):
        """刷新显示（清空缓存）"""
        self._display_cache.clear()
        self.layoutChanged.emit()
    
    def get_export_data(self) -> List[List[str]]:
        """获取导出数据"""
        result = []
        # 表头
        result.append([col.name for col in self.COLUMNS])
        # 数据
        for i, frame in enumerate(self._frames):
            row = [
                str(frame.frame_number),
                str(frame.start_position),
                str(frame.end_position),
                self._get_raw_hex(frame),
                self._get_parsed_result(frame)
            ]
            result.append(row)
        return result


class SortableFrameTableModel(FrameTableModel):
    """
    支持排序的帧数据表格模型
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder
        self._original_frames: List[DataFrame] = []
    
    def set_frames(self, frames: List[DataFrame]):
        """设置帧数据"""
        self._original_frames = frames.copy() if frames else []
        super().set_frames(frames)
        # 如果有排序，重新排序
        if self._sort_column >= 0:
            self.sort(self._sort_column, self._sort_order)
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """排序"""
        if not self._frames:
            return
        
        self._sort_column = column
        self._sort_order = order
        
        self.beginResetModel()
        
        # 根据列获取排序键
        if column == 0:
            key_func = lambda f: f.frame_number
        elif column == 1:
            key_func = lambda f: f.start_position
        elif column == 2:
            key_func = lambda f: f.end_position
        elif column == 3:
            key_func = lambda f: self._get_raw_hex(f)
        elif column == 4:
            key_func = lambda f: self._get_parsed_result(f)
        else:
            key_func = lambda f: 0
        
        self._frames.sort(key=key_func, reverse=(order == Qt.DescendingOrder))
        self._display_cache.clear()
        
        self.endResetModel()
    
    def reset_sort(self):
        """重置排序"""
        self.beginResetModel()
        self._frames = self._original_frames.copy()
        self._sort_column = -1
        self._display_cache.clear()
        self.endResetModel()
