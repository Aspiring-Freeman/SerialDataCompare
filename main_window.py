# This Python file uses the following encoding: utf-8
"""
串口数据分析工具 - 主窗口
"""
import sys
import os
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox,
    QFileDialog, QTableWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QAction

from ui_form import Ui_Main
from models import (
    ProtocolConfig, FieldDefinition, ChecksumConfig,
    ChecksumType, ChecksumPosition, FieldType, ParseResult
)
from core import DataParser, ProtocolManager, ColorConfig
from core.protocol_history import ProtocolHistory
from core.analysis_history import AnalysisHistory
from utils import export_to_txt, export_to_csv
from utils.delegates import ComboBoxDelegate
from ui import HistoryDialog


class ParseThread(QThread):
    """解析线程"""
    finished = Signal(ParseResult)
    error = Signal(str)
    
    def __init__(self, parser: DataParser, hex_string: str):
        super().__init__()
        self.parser = parser
        self.hex_string = hex_string
    
    def run(self):
        try:
            result = self.parser.parse(self.hex_string)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class Main(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Main()
        self.ui.setupUi(self)
        
        # 当前协议配置
        self.current_protocol: Optional[ProtocolConfig] = None
        # 解析结果
        self.parse_result: Optional[ParseResult] = None
        # 解析线程
        self.parse_thread: Optional[ParseThread] = None
        # 历史记录管理器
        self.protocol_history = ProtocolHistory()
        # 分析历史记录管理器
        self.analysis_history = AnalysisHistory()
        # 颜色配置管理器
        self.color_config = ColorConfig()
        # 颜色选择器字典
        self.color_buttons = {}
        
        # 初始化
        self.init_protocol()
        self.setup_connections()
        self.update_ui_from_protocol()
        self.setup_history_menu()
        self.setup_color_config_ui()
        
    def init_protocol(self):
        """初始化协议配置"""
        # 尝试加载示例协议
        example_path = os.path.join(os.path.dirname(__file__), 'protocol_example.json')
        if os.path.exists(example_path):
            self.current_protocol = ProtocolManager.load_protocol(example_path)
        
        # 如果加载失败，使用默认协议
        if self.current_protocol is None:
            self.current_protocol = ProtocolManager.get_default_protocol()
    
    def setup_history_menu(self):
        """设置历史记录菜单"""
        # 在"文件"菜单中添加"最近的协议"子菜单
        self.recent_menu = self.ui.menu_file.addMenu("最近的协议")
        self.update_history_menu()
    
    def update_history_menu(self):
        """更新历史记录菜单"""
        self.recent_menu.clear()
        
        history = self.protocol_history.get_history()
        if not history:
            action = QAction("(无)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return
        
        for item in history:
            action = QAction(item['name'], self)
            action.setData(item['path'])
            action.triggered.connect(lambda checked=False, path=item['path']: self.load_protocol_from_path(path))
            self.recent_menu.addAction(action)
        
        # 添加分隔符和清空历史选项
        self.recent_menu.addSeparator()
        clear_action = QAction("清空历史记录", self)
        clear_action.triggered.connect(self.clear_protocol_history)
        self.recent_menu.addAction(clear_action)
    
    def setup_connections(self):
        """设置信号槽连接"""
        # 数据分析Tab
        self.ui.btn_analyze.clicked.connect(self.on_analyze_clicked)
        self.ui.btn_clear_input.clicked.connect(self.on_clear_input_clicked)
        self.ui.btn_export_result.clicked.connect(self.on_export_result_clicked)
        self.ui.btn_view_history.clicked.connect(self.on_view_history_clicked)
        self.ui.tableWidget_frames.itemSelectionChanged.connect(self.on_frame_selected)
        
        # 协议配置Tab
        self.ui.btn_add_field.clicked.connect(self.on_add_field_clicked)
        self.ui.btn_delete_field.clicked.connect(self.on_delete_field_clicked)
        self.ui.btn_move_up.clicked.connect(self.on_move_up_clicked)
        self.ui.btn_move_down.clicked.connect(self.on_move_down_clicked)
        self.ui.btn_save_protocol.clicked.connect(self.on_save_protocol_clicked)
        self.ui.btn_load_protocol.clicked.connect(self.on_load_protocol_clicked)
        self.ui.btn_reset_protocol.clicked.connect(self.on_reset_protocol_clicked)
        
        # 设置Tab
        self.ui.spinBox_font_size.valueChanged.connect(self.on_font_size_changed)
        self.ui.btn_reset_colors.clicked.connect(self.on_reset_colors_clicked)
    
    def setup_color_config_ui(self):
        """设置颜色配置UI"""
        from PySide6.QtWidgets import QLabel, QPushButton, QColorDialog
        
        grid_layout = self.ui.gridLayout_colors
        
        # 为每种字段类型创建颜色选择器
        field_types = [ft.value for ft in FieldType]
        
        for i, field_type in enumerate(field_types):
            row = i // 2
            col = (i % 2) * 3
            
            # 标签
            label = QLabel(f"{field_type}:")
            grid_layout.addWidget(label, row, col)
            
            # 颜色按钮
            color_btn = QPushButton()
            color_btn.setFixedSize(80, 25)
            color = self.color_config.get_color(field_type)
            color_btn.setStyleSheet(f"background-color: {color};")
            color_btn.clicked.connect(lambda checked=False, ft=field_type: self.on_color_button_clicked(ft))
            grid_layout.addWidget(color_btn, row, col + 1)
            
            self.color_buttons[field_type] = color_btn
    
    # ==================== 数据分析Tab功能 ====================
    
    def on_analyze_clicked(self):
        """分析按钮点击"""
        # 获取输入数据
        input_text = self.ui.textEdit_input.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "警告", "请先输入数据！")
            return
        
        # 清空之前的分析结果
        self.ui.textEdit_frame_detail.clear()
        self.ui.tableWidget_frames.setRowCount(0)
        self.parse_result = None
        
        # 从UI更新协议配置
        self.update_protocol_from_ui()
        
        # 验证协议
        is_valid, error_msg = ProtocolManager.validate_protocol(self.current_protocol)
        if not is_valid:
            QMessageBox.critical(self, "协议错误", f"协议配置无效：\n{error_msg}")
            return
        
        # 禁用按钮
        self.ui.btn_analyze.setEnabled(False)
        self.ui.btn_analyze.setText("正在分析...")
        
        # 创建解析器
        parser = DataParser(self.current_protocol)
        
        # 创建解析线程
        self.parse_thread = ParseThread(parser, input_text)
        self.parse_thread.finished.connect(self.on_parse_finished)
        self.parse_thread.error.connect(self.on_parse_error)
        self.parse_thread.start()
    
    def on_parse_finished(self, result: ParseResult):
        """解析完成"""
        self.parse_result = result
        
        # 更新统计信息
        self.ui.label_total_frames.setText(f"总帧数：{result.get_total_frames()}")
        self.ui.label_valid_frames.setText(f"有效帧：{result.get_valid_frames()}")
        self.ui.label_error_frames.setText(f"错误帧：{result.get_error_frames()}")
        
        # 填充表格
        self.fill_frames_table(result)
        
        # 保存到历史记录
        self.save_analysis_to_history(result)
        
        # 恢复按钮
        self.ui.btn_analyze.setEnabled(True)
        self.ui.btn_analyze.setText("开始分析")
        
        # 显示完成消息
        self.statusBar().showMessage(f"分析完成！{result.get_summary()}", 5000)
    
    def on_parse_error(self, error_msg: str):
        """解析错误"""
        QMessageBox.critical(self, "解析错误", f"解析失败：\n{error_msg}")
        
        # 恢复按钮
        self.ui.btn_analyze.setEnabled(True)
        self.ui.btn_analyze.setText("开始分析")
    
    def fill_frames_table(self, result: ParseResult):
        """填充帧列表表格"""
        table = self.ui.tableWidget_frames
        table.setRowCount(0)
        
        for frame in result.frames:
            row = table.rowCount()
            table.insertRow(row)
            
            # 帧序号
            table.setItem(row, 0, QTableWidgetItem(str(frame.frame_number)))
            
            # 起始位置
            table.setItem(row, 1, QTableWidgetItem(str(frame.start_position)))
            
            # 结束位置
            table.setItem(row, 2, QTableWidgetItem(str(frame.end_position)))
            
            # 原始数据
            table.setItem(row, 3, QTableWidgetItem(frame.get_raw_data_hex()))
            
            # 解析结果
            table.setItem(row, 4, QTableWidgetItem(frame.get_field_summary()))
            
            # 校验状态
            if frame.expected_checksum is not None:
                status = "✓ 通过" if frame.checksum_valid else "✗ 失败"
            else:
                status = "无校验"
            status_item = QTableWidgetItem(status)
            
            # 错误行用红色标记
            if frame.has_error:
                for col in range(6):
                    item = table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 200, 200))
            
            table.setItem(row, 5, status_item)
        
        # 调整列宽
        table.resizeColumnsToContents()
    
    def on_frame_selected(self):
        """帧选择改变"""
        selected_items = self.ui.tableWidget_frames.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        if self.parse_result and row < len(self.parse_result.frames):
            frame = self.parse_result.frames[row]
            # 使用HTML版本显示，带颜色
            self.ui.textEdit_frame_detail.setHtml(frame.get_detailed_info_html(self.color_config))
    
    def save_analysis_to_history(self, result: ParseResult):
        """保存分析结果到历史记录"""
        try:
            input_data = self.ui.textEdit_input.toPlainText().strip()
            
            # 准备帧详情
            frame_details = []
            for frame in result.frames:
                frame_details.append({
                    'frame_number': frame.frame_number,
                    'has_error': frame.has_error,
                    'checksum_valid': frame.checksum_valid,
                    'raw_data_hex': frame.get_raw_data_hex()
                })
            
            # 添加到历史记录
            self.analysis_history.add_analysis(
                protocol_name=self.current_protocol.name,
                input_data=input_data,
                total_frames=result.get_total_frames(),
                valid_frames=result.get_valid_frames(),
                error_frames=result.get_error_frames(),
                frame_details=frame_details
            )
        except Exception as e:
            print(f"保存分析历史失败: {e}")
    
    def on_view_history_clicked(self):
        """查看历史记录按钮点击"""
        dialog = HistoryDialog(self.analysis_history, self)
        dialog.exec()
    
    def on_clear_input_clicked(self):
        """清空输入"""
        self.ui.textEdit_input.clear()
    
    def on_export_result_clicked(self):
        """导出结果"""
        if not self.parse_result or self.parse_result.get_total_frames() == 0:
            QMessageBox.warning(self, "警告", "没有可导出的数据！")
            return
        
        # 选择文件类型
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出结果",
            "",
            "文本文件 (*.txt);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        # 根据选择的类型导出
        if selected_filter == "文本文件 (*.txt)":
            success = export_to_txt(self.parse_result, file_path)
        else:
            success = export_to_csv(self.parse_result, file_path)
        
        if success:
            QMessageBox.information(self, "成功", "导出成功！")
        else:
            QMessageBox.critical(self, "失败", "导出失败！")
    
    # ==================== 协议配置Tab功能 ====================
    
    def update_ui_from_protocol(self):
        """从协议配置更新UI"""
        if not self.current_protocol:
            return
        
        # 基本参数
        self.ui.lineEdit_frame_header.setText(self.current_protocol.frame_header)
        self.ui.lineEdit_frame_tail.setText(self.current_protocol.frame_tail)
        
        # 校验类型
        checksum_type_map = {
            ChecksumType.NONE: 0,
            ChecksumType.SUM: 1,
            ChecksumType.CRC16: 2,
            ChecksumType.CRC32: 3,
            ChecksumType.XOR: 4
        }
        index = checksum_type_map.get(self.current_protocol.checksum_config.checksum_type, 0)
        self.ui.comboBox_checksum_type.setCurrentIndex(index)
        
        # 校验码位置
        if self.current_protocol.checksum_config.position == ChecksumPosition.BEFORE_TAIL:
            self.ui.radioButton_checksum_before_tail.setChecked(True)
        else:
            self.ui.radioButton_checksum_after_tail.setChecked(True)
        
        # 校验范围配置
        self.ui.spinBox_checksum_length.setValue(self.current_protocol.checksum_config.checksum_length)
        self.ui.spinBox_checksum_start_offset.setValue(self.current_protocol.checksum_config.start_offset)
        self.ui.spinBox_checksum_end_offset.setValue(self.current_protocol.checksum_config.end_offset)
        
        # 填充字段表格
        self.fill_fields_table()
    
    def update_protocol_from_ui(self):
        """从UI更新协议配置"""
        # 基本参数
        self.current_protocol.frame_header = self.ui.lineEdit_frame_header.text().strip()
        self.current_protocol.frame_tail = self.ui.lineEdit_frame_tail.text().strip()
        
        # 校验类型
        checksum_types = [
            ChecksumType.NONE,
            ChecksumType.SUM,
            ChecksumType.CRC16,
            ChecksumType.CRC32,
            ChecksumType.XOR
        ]
        self.current_protocol.checksum_config.checksum_type = checksum_types[
            self.ui.comboBox_checksum_type.currentIndex()
        ]
        
        # 校验码位置
        if self.ui.radioButton_checksum_before_tail.isChecked():
            self.current_protocol.checksum_config.position = ChecksumPosition.BEFORE_TAIL
        else:
            self.current_protocol.checksum_config.position = ChecksumPosition.AFTER_TAIL
        
        # 校验范围配置
        self.current_protocol.checksum_config.checksum_length = self.ui.spinBox_checksum_length.value()
        self.current_protocol.checksum_config.start_offset = self.ui.spinBox_checksum_start_offset.value()
        self.current_protocol.checksum_config.end_offset = self.ui.spinBox_checksum_end_offset.value()
        
        # 从表格更新字段信息
        self.update_fields_from_table()
    
    def fill_fields_table(self):
        """填充字段表格"""
        table = self.ui.tableWidget_fields
        
        # 暂时断开信号，避免在填充时触发更新
        table.blockSignals(True)
        table.setRowCount(0)
        
        # 设置数据类型列的下拉框委托
        field_types = [ft.value for ft in FieldType]
        type_delegate = ComboBoxDelegate(field_types, table)
        table.setItemDelegateForColumn(3, type_delegate)  # 第3列是数据类型列
        
        for field in self.current_protocol.fields:
            row = table.rowCount()
            table.insertRow(row)
            
            # 序号（不可编辑）
            item_order = QTableWidgetItem(str(field.order + 1))
            item_order.setFlags(item_order.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 0, item_order)
            
            # 字段名称（可编辑）
            table.setItem(row, 1, QTableWidgetItem(field.name))
            
            # 字节数（可编辑）
            table.setItem(row, 2, QTableWidgetItem(str(field.byte_count)))
            
            # 数据类型（使用ComboBox）
            table.setItem(row, 3, QTableWidgetItem(field.field_type.value))
            
            # 说明（可编辑）
            table.setItem(row, 4, QTableWidgetItem(field.description))
        
        table.resizeColumnsToContents()
        table.blockSignals(False)
        
        # 连接编辑信号
        table.itemChanged.connect(self.on_field_item_changed)
    
    def update_fields_from_table(self):
        """从表格更新字段到协议配置"""
        table = self.ui.tableWidget_fields
        
        for row in range(table.rowCount()):
            if row >= len(self.current_protocol.fields):
                break
            
            field = self.current_protocol.fields[row]
            
            # 更新字段名称
            name_item = table.item(row, 1)
            if name_item:
                field.name = name_item.text().strip()
            
            # 更新字节数
            bytes_item = table.item(row, 2)
            if bytes_item:
                try:
                    field.byte_count = int(bytes_item.text())
                except ValueError:
                    pass
            
            # 更新数据类型
            type_item = table.item(row, 3)
            if type_item:
                try:
                    field.field_type = FieldType(type_item.text())
                except ValueError:
                    pass
            
            # 更新说明
            desc_item = table.item(row, 4)
            if desc_item:
                field.description = desc_item.text().strip()
    
    def on_field_item_changed(self, item: QTableWidgetItem):
        """字段表格项改变"""
        # 实时更新到协议配置
        row = item.row()
        col = item.column()
        
        if row >= len(self.current_protocol.fields):
            return
        
        field = self.current_protocol.fields[row]
        
        try:
            if col == 1:  # 字段名称
                field.name = item.text().strip()
            elif col == 2:  # 字节数
                field.byte_count = int(item.text())
            elif col == 3:  # 数据类型
                field.field_type = FieldType(item.text())
            elif col == 4:  # 说明
                field.description = item.text().strip()
        except (ValueError, KeyError) as e:
            # 如果输入无效，恢复原值
            self.fill_fields_table()
    
    def on_add_field_clicked(self):
        """添加字段"""
        # TODO: 打开对话框编辑字段
        # 临时实现：添加一个默认字段
        field = FieldDefinition(
            name=f"字段{len(self.current_protocol.fields) + 1}",
            byte_count=1,
            field_type=FieldType.UINT8,
            description="新字段"
        )
        self.current_protocol.add_field(field)
        self.fill_fields_table()
    
    def on_delete_field_clicked(self):
        """删除字段"""
        selected_rows = self.ui.tableWidget_fields.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的字段！")
            return
        
        row = selected_rows[0].row()
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除字段 '{self.current_protocol.fields[row].name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_protocol.remove_field(row)
            self.fill_fields_table()
    
    def on_move_up_clicked(self):
        """字段上移"""
        selected_rows = self.ui.tableWidget_fields.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row > 0:
            # 先保存当前表格的修改
            self.update_fields_from_table()
            # 然后移动
            self.current_protocol.move_field_up(row)
            # 重新填充表格
            self.fill_fields_table()
            # 选中移动后的行
            self.ui.tableWidget_fields.selectRow(row - 1)
    
    def on_move_down_clicked(self):
        """字段下移"""
        selected_rows = self.ui.tableWidget_fields.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < len(self.current_protocol.fields) - 1:
            # 先保存当前表格的修改
            self.update_fields_from_table()
            # 然后移动
            self.current_protocol.move_field_down(row)
            # 重新填充表格
            self.fill_fields_table()
            # 选中移动后的行
            self.ui.tableWidget_fields.selectRow(row + 1)
    
    def on_save_protocol_clicked(self):
        """保存协议"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存协议配置",
            "",
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        # 从UI更新协议
        self.update_protocol_from_ui()
        
        if ProtocolManager.save_protocol(self.current_protocol, file_path):
            QMessageBox.information(self, "成功", "协议保存成功！")
        else:
            QMessageBox.critical(self, "失败", "协议保存失败！")
    
    def on_load_protocol_clicked(self):
        """加载协议"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "加载协议配置",
            "",
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        self.load_protocol_from_path(file_path)
    
    def load_protocol_from_path(self, file_path: str):
        """
        从指定路径加载协议
        
        Args:
            file_path: 协议文件路径
        """
        protocol = ProtocolManager.load_protocol(file_path)
        if protocol:
            self.current_protocol = protocol
            self.update_ui_from_protocol()
            # 添加到历史记录
            self.protocol_history.add_protocol(file_path, protocol.protocol_name)
            self.update_history_menu()
            QMessageBox.information(self, "成功", "协议加载成功！")
        else:
            QMessageBox.critical(self, "失败", "协议加载失败！请检查文件格式。")
    
    def clear_protocol_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清空历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.protocol_history.clear_history()
            self.update_history_menu()
            QMessageBox.information(self, "成功", "历史记录已清空！")
    
    def on_reset_protocol_clicked(self):
        """重置协议"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要重置为默认协议吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_protocol = ProtocolManager.get_default_protocol()
            self.update_ui_from_protocol()
    
    # ==================== 设置Tab功能 ====================
    
    def on_font_size_changed(self, value: int):
        """字体大小改变"""
        # TODO: 实现全局字体大小调整
        pass
    
    def on_color_button_clicked(self, field_type: str):
        """颜色按钮点击"""
        from PySide6.QtWidgets import QColorDialog
        
        current_color = self.color_config.get_qcolor(field_type)
        color = QColorDialog.getColor(current_color, self, f"选择 {field_type} 类型的颜色")
        
        if color.isValid():
            color_str = color.name()
            self.color_config.set_color(field_type, color_str)
            self.color_buttons[field_type].setStyleSheet(f"background-color: {color_str};")
    
    def on_reset_colors_clicked(self):
        """重置颜色按钮点击"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复默认颜色配置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.color_config.reset_colors()
            # 更新所有颜色按钮
            for field_type, btn in self.color_buttons.items():
                color = self.color_config.get_color(field_type)
                btn.setStyleSheet(f"background-color: {color};")
            QMessageBox.information(self, "成功", "颜色配置已恢复默认值！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Main()
    widget.show()
    sys.exit(app.exec())
