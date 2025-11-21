# This Python file uses the following encoding: utf-8
"""
帧详情界面 - Fluent Design
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt

from qfluentwidgets import (
    ScrollArea, CardWidget, TextEdit, TitleLabel, BodyLabel, StrongBodyLabel
)


class FrameDetailInterface(QWidget):
    """帧详情界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("frame_detail_interface")
        
        # 滚动区域
        self.scroll = ScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # 滚动内容容器
        self.scroll_widget = QWidget()
        self.scroll.setWidget(self.scroll_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.scroll_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 创建UI
        self.create_basic_info_card()
        self.create_data_card()
        self.create_fields_card()
        self.create_checksum_card()
        
        # 添加弹性空间
        self.main_layout.addStretch()
        
        # 设置滚动区域为主widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)
    
    def create_basic_info_card(self):
        """创建基本信息卡片"""
        self.basic_card = CardWidget(self)
        card_layout = QVBoxLayout(self.basic_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # 标题和说明
        title_layout = QHBoxLayout()
        title = TitleLabel("📊 基本信息")
        title.setStyleSheet("font-weight: bold; color: #0078D4;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        hint = BodyLabel("数据帧的基本属性")
        hint.setStyleSheet("color: #606060; font-size: 13px;")
        title_layout.addWidget(hint)
        card_layout.addLayout(title_layout)
        
        # 信息网格
        info_grid = QGridLayout()
        info_grid.setSpacing(15)
        info_grid.setColumnStretch(1, 1)
        info_grid.setColumnStretch(3, 1)
        
        # 标签样式
        label_style = "font-weight: bold; color: #333333; min-width: 100px;"
        value_style = "color: #0078D4; font-size: 14px; padding: 5px; background: #F3F3F3; border-radius: 4px;"
        
        # 帧序号
        self.frame_num_label = BodyLabel("🔢 帧序号:")
        self.frame_num_label.setStyleSheet(label_style)
        self.frame_num_value = BodyLabel("")
        self.frame_num_value.setStyleSheet(value_style)
        info_grid.addWidget(self.frame_num_label, 0, 0)
        info_grid.addWidget(self.frame_num_value, 0, 1)
        
        # 数据长度
        self.length_label = BodyLabel("📏 数据长度:")
        self.length_label.setStyleSheet(label_style)
        self.length_value = BodyLabel("")
        self.length_value.setStyleSheet(value_style)
        info_grid.addWidget(self.length_label, 0, 2)
        info_grid.addWidget(self.length_value, 0, 3)
        
        # 起始位置
        self.start_label = BodyLabel("📍 起始位置:")
        self.start_label.setStyleSheet(label_style)
        self.start_value = BodyLabel("")
        self.start_value.setStyleSheet(value_style)
        info_grid.addWidget(self.start_label, 1, 0)
        info_grid.addWidget(self.start_value, 1, 1)
        
        # 结束位置
        self.end_label = BodyLabel("🏁 结束位置:")
        self.end_label.setStyleSheet(label_style)
        self.end_value = BodyLabel("")
        self.end_value.setStyleSheet(value_style)
        info_grid.addWidget(self.end_label, 1, 2)
        info_grid.addWidget(self.end_value, 1, 3)
        
        card_layout.addLayout(info_grid)
        self.main_layout.addWidget(self.basic_card)
    
    def create_data_card(self):
        """创建原始数据卡片"""
        self.data_card = CardWidget(self)
        card_layout = QVBoxLayout(self.data_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # 标题和说明
        title_layout = QHBoxLayout()
        title = TitleLabel("📦 原始数据")
        title.setStyleSheet("font-weight: bold; color: #0078D4;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        hint = BodyLabel("以十六进制格式显示完整的原始数据帧")
        hint.setStyleSheet("color: #606060; font-size: 13px;")
        title_layout.addWidget(hint)
        card_layout.addLayout(title_layout)
        
        # 数据文本框
        self.data_text = TextEdit()
        self.data_text.setReadOnly(True)
        self.data_text.setMinimumHeight(120)
        self.data_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 13px;
                background: #F8F8F8;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 10px;
                color: #2B579A;
            }
        """)
        card_layout.addWidget(self.data_text)
        
        # 底部说明
        desc_layout = QHBoxLayout()
        desc_layout.setSpacing(20)
        
        desc1 = BodyLabel("💡 数据格式为十六进制字节序列")
        desc1.setStyleSheet("color: #606060; font-size: 12px;")
        desc_layout.addWidget(desc1)
        
        desc2 = BodyLabel("📋 每个字节以两位十六进制数表示")
        desc2.setStyleSheet("color: #606060; font-size: 12px;")
        desc_layout.addWidget(desc2)
        
        desc_layout.addStretch()
        card_layout.addLayout(desc_layout)
        
        self.main_layout.addWidget(self.data_card)
    
    def create_fields_card(self):
        """创建解析字段卡片"""
        self.fields_card = CardWidget(self)
        card_layout = QVBoxLayout(self.fields_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # 标题和说明
        title_layout = QHBoxLayout()
        title = TitleLabel("🔍 解析字段")
        title.setStyleSheet("font-weight: bold; color: #0078D4;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        hint = BodyLabel("根据协议配置解析出的各个字段值")
        hint.setStyleSheet("color: #606060; font-size: 13px;")
        title_layout.addWidget(hint)
        card_layout.addLayout(title_layout)
        
        # 字段网格容器
        self.fields_grid = QGridLayout()
        self.fields_grid.setSpacing(12)
        self.fields_grid.setColumnStretch(1, 1)
        self.fields_grid.setColumnStretch(3, 1)
        card_layout.addLayout(self.fields_grid)
        
        # 空状态提示
        self.no_fields_label = BodyLabel("暂无解析字段")
        self.no_fields_label.setStyleSheet("color: #999999; font-style: italic; padding: 20px;")
        self.no_fields_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.no_fields_label)
        
        self.main_layout.addWidget(self.fields_card)
    
    def create_checksum_card(self):
        """创建校验信息卡片"""
        self.checksum_card = CardWidget(self)
        card_layout = QVBoxLayout(self.checksum_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # 标题和说明
        title_layout = QHBoxLayout()
        title = TitleLabel("✔️ 校验信息")
        title.setStyleSheet("font-weight: bold; color: #0078D4;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        hint = BodyLabel("数据帧的校验码验证结果")
        hint.setStyleSheet("color: #606060; font-size: 13px;")
        title_layout.addWidget(hint)
        card_layout.addLayout(title_layout)
        
        # 校验信息网格
        check_grid = QGridLayout()
        check_grid.setSpacing(15)
        check_grid.setColumnStretch(1, 1)
        check_grid.setColumnStretch(3, 1)
        
        label_style = "font-weight: bold; color: #333333; min-width: 100px;"
        
        # 校验结果
        self.valid_label = BodyLabel("🎯 校验结果:")
        self.valid_label.setStyleSheet(label_style)
        self.valid_value = BodyLabel("")
        check_grid.addWidget(self.valid_label, 0, 0)
        check_grid.addWidget(self.valid_value, 0, 1)
        
        # 计算校验
        self.expected_label = BodyLabel("📝 计算校验:")
        self.expected_label.setStyleSheet(label_style)
        self.expected_value = BodyLabel("")
        self.expected_value.setStyleSheet("color: #0078D4; font-family: 'Courier New', monospace;")
        check_grid.addWidget(self.expected_label, 1, 0)
        check_grid.addWidget(self.expected_value, 1, 1)
        
        # 帧内校验
        self.actual_label = BodyLabel("🔢 帧内校验:")
        self.actual_label.setStyleSheet(label_style)
        self.actual_value = BodyLabel("")
        self.actual_value.setStyleSheet("color: #0078D4; font-family: 'Courier New', monospace;")
        check_grid.addWidget(self.actual_label, 1, 2)
        check_grid.addWidget(self.actual_value, 1, 3)
        
        card_layout.addLayout(check_grid)
        
        # 错误信息
        self.error_label = BodyLabel("")
        self.error_label.setStyleSheet("color: #D13438; background: #FFF4F4; padding: 10px; border-radius: 4px; margin-top: 10px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        
        card_layout.addWidget(self.error_label)
        
        self.main_layout.addWidget(self.checksum_card)
    
    def show_frame(self, frame):
        """显示帧详情"""
        # 处理原始数据显示
        raw_hex = frame.raw_data.hex().upper() if isinstance(frame.raw_data, bytes) else str(frame.raw_data)
        
        # 更新基本信息
        self.frame_num_value.setText(f"#{frame.frame_number}")
        # 使用实际数据长度，避免计算偏差
        data_length = len(frame.raw_data)
        self.length_value.setText(f"{data_length} 字节")
        self.start_value.setText(f"0x{frame.start_position:04X} ({frame.start_position})")
        # 结束位置应该是最后一个字节的位置（不包含）
        self.end_value.setText(f"0x{frame.end_position-1:04X} ({frame.end_position-1})")
        
        # 更新原始数据（格式化为每行16字节）
        formatted_hex = self._format_hex_data(raw_hex)
        self.data_text.setPlainText(formatted_hex)
        
        # 更新解析字段
        self._update_fields(frame.fields, frame.field_types)
        
        # 更新校验信息
        self._update_checksum(frame)
    
    def _format_hex_data(self, hex_str):
        """格式化十六进制数据，每行16字节"""
        # 移除所有空格
        hex_str = hex_str.replace(" ", "")
        
        # 每2个字符(1字节)添加空格，每16字节换行
        formatted = []
        for i in range(0, len(hex_str), 2):
            byte_hex = hex_str[i:i+2]
            formatted.append(byte_hex)
            
            # 每16字节换行
            if (i // 2 + 1) % 16 == 0 and i + 2 < len(hex_str):
                formatted.append("\n")
            else:
                formatted.append(" ")
        
        return "".join(formatted).strip()
    
    def _update_fields(self, fields, field_types):
        """更新解析字段显示"""
        # 清空现有字段
        while self.fields_grid.count():
            item = self.fields_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not fields:
            self.no_fields_label.show()
            return
        
        self.no_fields_label.hide()
        
        # 标签样式
        name_style = "font-weight: bold; color: #333333; min-width: 120px;"
        value_style = "color: #0078D4; font-size: 13px; padding: 8px; background: #F8F8F8; border-radius: 4px; font-family: 'Courier New', monospace;"
        type_style = "color: #888888; font-size: 11px; font-style: italic;"
        
        # 导入格式化函数
        from models.protocol import format_field_value
        
        # 添加字段（2列布局）
        row = 0
        col = 0
        for key, value in fields.items():
            # 字段名和类型
            field_type = field_types.get(key, "")
            type_str = f" ({field_type})" if field_type else ""
            
            name_label = BodyLabel(f"🔹 {key}:")
            name_label.setStyleSheet(name_style)
            
            # 格式化字段值显示
            value_label = BodyLabel(format_field_value(value))
            value_label.setStyleSheet(value_style)
            value_label.setWordWrap(True)
            # 允许文本选择和复制
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            # 添加到网格
            self.fields_grid.addWidget(name_label, row, col * 2)
            self.fields_grid.addWidget(value_label, row, col * 2 + 1)
            
            # 更新行列
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def _update_checksum(self, frame):
        """更新校验信息"""
        if frame.expected_checksum is not None:
            # 校验结果
            if frame.checksum_valid:
                self.valid_value.setText("✅ 校验通过")
                self.valid_value.setStyleSheet("color: #107C10; font-weight: bold; font-size: 14px;")
            else:
                self.valid_value.setText("❌ 校验失败")
                self.valid_value.setStyleSheet("color: #D13438; font-weight: bold; font-size: 14px;")
            
            # 期望和实际校验值
            self.expected_value.setText(f"0x{frame.expected_checksum:02X}")
            self.actual_value.setText(f"0x{frame.actual_checksum:02X}")
            
            # 显示卡片
            self.checksum_card.show()
        else:
            # 没有校验信息时隐藏卡片
            self.checksum_card.hide()
        
        # 错误信息
        if frame.has_error:
            self.error_label.setText(f"⚠️ 错误: {frame.error_message}")
            self.error_label.show()
        else:
            self.error_label.hide()
