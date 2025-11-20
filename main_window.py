# This Python file uses the following encoding: utf-8
"""
串口数据分析工具 - 主窗口
"""
import sys
import os
from datetime import datetime
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
from utils import export_to_txt, export_to_csv, Logger, LogLevel
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
        # 日志管理器
        self.logger = Logger()
        
        # 初始化
        self.init_protocol()
        self.setup_connections()
        self.setup_checksum_ui_logic()  # 设置校验UI逻辑
        self.setup_table_columns()  # 设置表格列宽
        self.setup_logger()  # 设置日志
        self.update_ui_from_protocol()
        self.setup_history_menu()
        self.setup_color_config_ui()
        
        # 记录启动日志
        self.logger.info("程序启动成功")
    
    def setup_checksum_ui_logic(self):
        """设置校验配置UI逻辑"""
        # 连接复选框信号，控制简化配置的启用/禁用
        self.ui.checkBox_use_absolute_position.stateChanged.connect(self.on_absolute_position_changed)
    
    def setup_table_columns(self):
        """设置表格列宽"""
        from PySide6.QtWidgets import QHeaderView
        
        header = self.ui.tableWidget_frames.horizontalHeader()
        # 帧序号 - 固定宽度
        header.resizeSection(0, 80)
        # 起始位置 - 固定宽度
        header.resizeSection(1, 90)
        # 结束位置 - 固定宽度
        header.resizeSection(2, 90)
        # 原始数据 - 自适应内容，但允许拉伸
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        # 解析结果 - 自适应内容，但允许拉伸
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        # 校验状态 - 固定宽度
        header.resizeSection(5, 100)
        
        # 设置最小列宽，避免数据被截断
        self.ui.tableWidget_frames.setColumnWidth(3, 400)  # 原始数据最小宽度
        self.ui.tableWidget_frames.setColumnWidth(4, 300)  # 解析结果最小宽度
    
    def setup_logger(self):
        """设置日志系统"""
        # 连接日志信号到 UI
        self.logger.log_added.connect(self.on_log_added)
        
        # 连接日志控制按钮
        self.ui.btn_clear_log.clicked.connect(self.on_clear_log)
        self.ui.btn_export_log.clicked.connect(self.on_export_log)
        self.ui.comboBox_log_level.currentTextChanged.connect(self.on_log_level_changed)
    
    def on_log_added(self, level: str, message: str):
        """新日志添加时的处理"""
        # 获取当前选择的日志级别过滤
        current_filter = self.ui.comboBox_log_level.currentText()
        
        # 如果是"全部"或匹配当前级别，则显示
        if current_filter == "全部" or current_filter == level:
            self.ui.textEdit_log.append(message)
    
    def on_clear_log(self):
        """清空日志"""
        self.ui.textEdit_log.clear()
        self.logger.clear()
    
    def on_export_log(self):
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.logger.export_to_text())
                self.logger.info(f"日志已导出到：{file_path}")
                QMessageBox.information(self, "成功", "日志导出成功！")
            except Exception as e:
                self.logger.error(f"导出日志失败：{str(e)}")
                QMessageBox.critical(self, "错误", f"导出日志失败：{str(e)}")
    
    def on_log_level_changed(self, level: str):
        """日志级别过滤改变"""
        self.ui.textEdit_log.clear()
        
        if level == "全部":
            logs = self.logger.get_logs()
        else:
            level_enum = LogLevel[level]
            logs = self.logger.get_logs(level_enum)
        
        for log in logs:
            self.ui.textEdit_log.append(log)
        
        self.logger.debug(f"日志过滤级别已更改为：{level}")
    
    def on_absolute_position_changed(self, state):
        """简化配置复选框状态改变"""
        enabled = (state == 2)  # Qt.Checked = 2
        self.ui.spinBox_checksum_position.setEnabled(enabled)
        self.ui.spinBox_checksum_start.setEnabled(enabled)
        self.ui.spinBox_checksum_end.setEnabled(enabled)
        
        # 禁用旧配置
        self.ui.spinBox_checksum_start_offset.setEnabled(not enabled)
        self.ui.spinBox_checksum_end_offset.setEnabled(not enabled)
        
    def init_protocol(self):
        """初始化协议配置"""
        self.logger.debug("正在初始化协议配置...")
        
        # 尝试加载示例协议
        example_path = os.path.join(os.path.dirname(__file__), 'protocol_example.json')
        if os.path.exists(example_path):
            self.current_protocol = ProtocolManager.load_protocol(example_path)
            self.logger.info(f"已加载示例协议：{example_path}")
        
        # 如果加载失败，使用默认协议
        if self.current_protocol is None:
            self.current_protocol = ProtocolManager.get_default_protocol()
            self.logger.info("已加载默认协议配置")
    
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
        self.ui.btn_apply_theme.clicked.connect(self.on_apply_theme_clicked)
        
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
        self.logger.info("========== 开始分析数据 ==========")
        
        # 获取输入数据
        input_text = self.ui.textEdit_input.toPlainText().strip()
        if not input_text:
            self.logger.warning("输入数据为空")
            QMessageBox.warning(self, "警告", "请先输入数据！")
            return
        
        self.logger.info(f"输入数据长度：{len(input_text)} 字符")
        
        # 清空之前的分析结果
        self.ui.textEdit_frame_detail.clear()
        self.ui.tableWidget_frames.setRowCount(0)
        self.parse_result = None
        
        # 从UI更新协议配置
        self.update_protocol_from_ui()
        self.logger.debug(f"协议配置：{self.current_protocol.protocol_name}")
        
        # 验证协议
        is_valid, error_msg = ProtocolManager.validate_protocol(self.current_protocol)
        if not is_valid:
            self.logger.error(f"协议配置无效：{error_msg}")
            QMessageBox.critical(self, "协议错误", f"协议配置无效：\n{error_msg}")
            return
        
        self.logger.info("协议配置验证通过")
        
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
        
        self.logger.info(f"解析完成！总帧数：{result.get_total_frames()}，有效帧：{result.get_valid_frames()}，错误帧：{result.get_error_frames()}")
        
        # 更新统计信息
        self.ui.label_total_frames.setText(f"总帧数：{result.get_total_frames()}")
        self.ui.label_valid_frames.setText(f"有效帧：{result.get_valid_frames()}")
        self.ui.label_error_frames.setText(f"错误帧：{result.get_error_frames()}")
        
        # 填充表格
        self.fill_frames_table(result)
        self.logger.debug("帧数据表格已填充")
        
        # 保存到历史记录
        self.save_analysis_to_history(result)
        self.logger.debug("分析结果已保存到历史记录")
        
        # 恢复按钮
        self.ui.btn_analyze.setEnabled(True)
        self.ui.btn_analyze.setText("开始分析")
        
        # 显示完成消息
        self.statusBar().showMessage(f"分析完成！{result.get_summary()}", 5000)
        self.logger.info("========== 分析完成 ==========")
    
    def on_parse_error(self, error_msg: str):
        """解析错误"""
        self.logger.error(f"解析失败：{error_msg}")
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
            # 自动切换到帧详情标签页（索引1，在数据分析之后）
            self.ui.tabWidget.setCurrentIndex(1)
    
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
                protocol_name=self.current_protocol.protocol_name,
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
        
        # 固定帧长度
        if self.current_protocol.frame_length:
            self.ui.spinBox_frame_length.setValue(self.current_protocol.frame_length)
        else:
            self.ui.spinBox_frame_length.setValue(0)
        
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
        
        # 校验码字节数
        self.ui.spinBox_checksum_length.setValue(self.current_protocol.checksum_config.checksum_length)
        
        # 检查是否使用简化配置
        use_absolute = (self.current_protocol.checksum_config.checksum_position is not None or
                       self.current_protocol.checksum_config.checksum_start is not None or
                       self.current_protocol.checksum_config.checksum_end is not None)
        
        self.ui.checkBox_use_absolute_position.setChecked(use_absolute)
        
        if use_absolute:
            # 简化配置
            if self.current_protocol.checksum_config.checksum_position is not None:
                self.ui.spinBox_checksum_position.setValue(
                    self.current_protocol.checksum_config.checksum_position)
            if self.current_protocol.checksum_config.checksum_start is not None:
                self.ui.spinBox_checksum_start.setValue(
                    self.current_protocol.checksum_config.checksum_start)
            if self.current_protocol.checksum_config.checksum_end is not None:
                self.ui.spinBox_checksum_end.setValue(
                    self.current_protocol.checksum_config.checksum_end)
        else:
            # 旧版配置
            self.ui.spinBox_checksum_start_offset.setValue(
                self.current_protocol.checksum_config.start_offset)
            self.ui.spinBox_checksum_end_offset.setValue(
                self.current_protocol.checksum_config.end_offset)
        
        # 填充字段表格
        self.fill_fields_table()
    
    def update_protocol_from_ui(self):
        """从UI更新协议配置"""
        # 基本参数
        self.current_protocol.frame_header = self.ui.lineEdit_frame_header.text().strip()
        self.current_protocol.frame_tail = self.ui.lineEdit_frame_tail.text().strip()
        
        # 固定帧长度
        frame_length = self.ui.spinBox_frame_length.value()
        self.current_protocol.frame_length = frame_length if frame_length > 0 else None
        
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
        
        # 校验码字节数
        self.current_protocol.checksum_config.checksum_length = self.ui.spinBox_checksum_length.value()
        
        # 根据是否使用简化配置来设置不同的值
        if self.ui.checkBox_use_absolute_position.isChecked():
            # 使用简化配置
            self.current_protocol.checksum_config.checksum_position = self.ui.spinBox_checksum_position.value()
            self.current_protocol.checksum_config.checksum_start = self.ui.spinBox_checksum_start.value()
            self.current_protocol.checksum_config.checksum_end = self.ui.spinBox_checksum_end.value()
            # 清除旧配置（设为默认值）
            self.current_protocol.checksum_config.start_offset = 0
            self.current_protocol.checksum_config.end_offset = -1
        else:
            # 使用旧版配置
            self.current_protocol.checksum_config.start_offset = self.ui.spinBox_checksum_start_offset.value()
            self.current_protocol.checksum_config.end_offset = self.ui.spinBox_checksum_end_offset.value()
            # 清除简化配置
            self.current_protocol.checksum_config.checksum_position = None
            self.current_protocol.checksum_config.checksum_start = None
            self.current_protocol.checksum_config.checksum_end = None
        
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
        self.logger.info("开始保存协议配置...")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存协议配置",
            "",
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            self.logger.debug("用户取消了保存操作")
            return
        
        # 从UI更新协议
        self.update_protocol_from_ui()
        
        if ProtocolManager.save_protocol(self.current_protocol, file_path):
            self.logger.info(f"协议保存成功：{file_path}")
            QMessageBox.information(self, "成功", "协议保存成功！")
        else:
            self.logger.error(f"协议保存失败：{file_path}")
            QMessageBox.critical(self, "失败", "协议保存失败！")
    
    def on_load_protocol_clicked(self):
        """加载协议"""
        self.logger.info("开始加载协议配置...")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "加载协议配置",
            "",
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            self.logger.debug("用户取消了加载操作")
            return
        
        self.load_protocol_from_path(file_path)
    
    def load_protocol_from_path(self, file_path: str):
        """
        从指定路径加载协议
        
        Args:
            file_path: 协议文件路径
        """
        self.logger.info(f"正在加载协议文件：{file_path}")
        
        protocol = ProtocolManager.load_protocol(file_path)
        if protocol:
            self.current_protocol = protocol
            self.logger.info(f"协议加载成功：{protocol.protocol_name}")
            self.logger.debug(f"协议详情：帧头={protocol.frame_header}, 帧尾={protocol.frame_tail}, 字段数={len(protocol.fields)}")
            
            self.update_ui_from_protocol()
            # 添加到历史记录
            self.protocol_history.add_protocol(file_path, protocol.protocol_name)
            self.update_history_menu()
            QMessageBox.information(self, "成功", "协议加载成功！")
        else:
            self.logger.error(f"协议加载失败：{file_path}")
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
    
    def on_apply_theme_clicked(self):
        """应用主题"""
        theme_name = self.ui.comboBox_theme.currentText()
        self.logger.info(f"正在切换主题：{theme_name}")
        
        try:
            self.apply_theme(theme_name)
            self.logger.info(f"主题切换成功：{theme_name}")
            QMessageBox.information(self, "成功", f"主题已切换为：{theme_name}")
        except Exception as e:
            self.logger.error(f"主题切换失败：{str(e)}")
            QMessageBox.warning(self, "警告", f"主题切换失败：{str(e)}")
    
    def apply_theme(self, theme_name: str):
        """
        应用主题
        
        Args:
            theme_name: 主题名称
        """
        from PySide6.QtGui import QPalette, QColor
        
        app = QApplication.instance()
        
        if theme_name == "Fusion - 浅色":
            app.setStyle("Fusion")
            # 浅色调色板
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
            app.setPalette(palette)
            
        elif theme_name == "Fusion - 深色":
            app.setStyle("Fusion")
            # 深色调色板
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
            # 禁用状态的颜色
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
            app.setPalette(palette)
            
        elif theme_name == "Windows":
            app.setStyle("Windows")
            app.setPalette(app.style().standardPalette())
            
        elif theme_name == "系统默认":
            app.setStyle("")  # 空字符串使用系统默认
            app.setPalette(app.style().standardPalette())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 使用 Qt Fusion 主题（跨平台一致的现代外观）
    app.setStyle("Fusion")
    
    # 设置调色板以获得更好的视觉效果
    from PySide6.QtGui import QPalette
    palette = QPalette()
    
    # 可选：设置浅色主题（注释掉则使用系统默认）
    # palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    # palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    # palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    # palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    # palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    # palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    # palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    # app.setPalette(palette)
    
    widget = Main()
    widget.show()
    sys.exit(app.exec())
