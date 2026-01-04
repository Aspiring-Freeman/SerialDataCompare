# This Python file uses the following encoding: utf-8
"""
帧详情界面 - Fluent Design
支持解析字段与原始字节的双向高亮联动
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor

from qfluentwidgets import (
    ScrollArea, CardWidget, TextEdit, TitleLabel, BodyLabel, StrongBodyLabel
)


class ClickableByteLabel(QLabel):
    """可点击的字节标签，用于显示单个十六进制字节"""
    
    clicked = Signal(int)  # 发送字节索引
    hovered = Signal(int)  # 发送字节索引
    
    def __init__(self, byte_value: str, byte_index: int, parent=None):
        super().__init__(byte_value, parent)
        self.byte_index = byte_index
        self.is_highlighted = False
        self.highlight_color = "#FFF3CD"  # 默认高亮颜色
        
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(30, 24)
        self._update_style()
    
    def _update_style(self):
        if self.is_highlighted:
            self.setStyleSheet(f"""
                QLabel {{
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 13px;
                    background: {self.highlight_color};
                    border: 1px solid #FFC107;
                    border-radius: 3px;
                    color: #333;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 13px;
                    background: #F5F5F5;
                    border: 1px solid #D0D0D0;
                    border-radius: 3px;
                    color: #333333;
                }
                QLabel:hover {
                    background: #E8F4FD;
                    border-color: #0078D4;
                }
            """)
    
    def set_highlighted(self, highlighted: bool, color: str = "#FFF3CD"):
        self.is_highlighted = highlighted
        self.highlight_color = color
        self._update_style()
    
    def enterEvent(self, event):
        self.hovered.emit(self.byte_index)
        super().enterEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.byte_index)
        super().mousePressEvent(event)


class ClickableFieldLabel(QFrame):
    """可点击的字段标签，支持高亮"""
    
    clicked = Signal(str)  # 发送字段名
    hovered = Signal(str)  # 发送字段名
    
    def __init__(self, field_name: str, field_value: str, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.is_highlighted = False
        self.highlight_color = "#FFF3CD"
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # 字段名标签
        self.name_label = QLabel(f"🔹 {field_name}:")
        self.name_label.setStyleSheet("font-weight: bold; color: #333333;")
        
        # 字段值标签
        self.value_label = QLabel(field_value)
        self.value_label.setWordWrap(True)
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.value_label, 1)
        
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._update_style()
    
    def _update_style(self):
        if self.is_highlighted:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {self.highlight_color};
                    border: 2px solid #FFC107;
                    border-radius: 6px;
                }}
            """)
            self.value_label.setStyleSheet("color: #333; font-family: 'Courier New', monospace;")
        else:
            self.setStyleSheet("""
                QFrame {
                    background: #F8F8F8;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                }
                QFrame:hover {
                    background: #E8F4FD;
                    border-color: #0078D4;
                }
            """)
            self.value_label.setStyleSheet("color: #0078D4; font-family: 'Courier New', monospace;")
    
    def set_highlighted(self, highlighted: bool, color: str = "#FFF3CD"):
        self.is_highlighted = highlighted
        self.highlight_color = color
        self._update_style()
    
    def enterEvent(self, event):
        self.hovered.emit(self.field_name)
        super().enterEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.field_name)
        super().mousePressEvent(event)


class FrameDetailInterface(QWidget):
    """帧详情界面 - 支持双向高亮联动"""
    
    # 字段颜色映射（用于区分不同字段）
    FIELD_COLORS = [
        "#FFF3CD",  # 黄色
        "#D4EDDA",  # 绿色
        "#D1ECF1",  # 蓝色
        "#F8D7DA",  # 红色
        "#E2D5F5",  # 紫色
        "#FFE5D0",  # 橙色
        "#D5E8D4",  # 浅绿
        "#DAE8FC",  # 浅蓝
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("frame_detail_interface")
        
        # 当前帧数据
        self.current_frame = None
        # 字段到字节位置的映射
        self.field_byte_positions = {}
        # 字节标签列表
        self.byte_labels = []
        # 字段标签字典
        self.field_widgets = {}
        # 字段颜色映射
        self.field_colors = {}
        
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
        """创建原始数据卡片 - 支持交互式高亮"""
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
        
        hint = BodyLabel("点击字节查看对应字段，悬停显示高亮")
        hint.setStyleSheet("color: #606060; font-size: 13px;")
        title_layout.addWidget(hint)
        card_layout.addLayout(title_layout)
        
        # 字节网格容器
        self.bytes_container = QWidget()
        self.bytes_layout = QGridLayout(self.bytes_container)
        self.bytes_layout.setSpacing(2)
        self.bytes_layout.setContentsMargins(10, 10, 10, 10)
        self.bytes_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        card_layout.addWidget(self.bytes_container)
        
        # 备用：传统文本框（用于显示长数据）
        self.data_text = TextEdit()
        self.data_text.setReadOnly(True)
        self.data_text.setMinimumHeight(60)
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
        self.data_text.hide()  # 默认隐藏
        card_layout.addWidget(self.data_text)
        
        # 底部说明
        desc_layout = QHBoxLayout()
        desc_layout.setSpacing(20)
        
        desc1 = BodyLabel("💡 点击字节高亮对应字段")
        desc1.setStyleSheet("color: #606060; font-size: 12px;")
        desc_layout.addWidget(desc1)
        
        desc2 = BodyLabel("📋 悬停字段高亮对应字节")
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
        self.current_frame = frame
        
        # 处理原始数据显示
        raw_hex = frame.raw_data.hex().upper() if isinstance(frame.raw_data, bytes) else str(frame.raw_data)
        
        # 更新基本信息
        self.frame_num_value.setText(f"#{frame.frame_number}")
        # 使用实际数据长度，避免计算偏差
        data_length = len(frame.raw_data)
        self.length_value.setText(f"{data_length} 字节")
        self.start_value.setText(f"0x{frame.start_position:04X} ({frame.start_position})")
        # 结束位置是最后一个字节的索引（包含）
        self.end_value.setText(f"0x{frame.end_position:04X} ({frame.end_position})")
        
        # 保存字段位置信息
        self.field_byte_positions = getattr(frame, 'field_byte_positions', {})
        
        # 创建交互式字节视图（如果数据不太长）
        if len(frame.raw_data) <= 128:
            self._create_interactive_bytes(frame.raw_data)
            self.bytes_container.show()
            self.data_text.hide()
        else:
            # 数据太长，使用传统文本显示
            formatted_hex = self._format_hex_data(raw_hex)
            self.data_text.setPlainText(formatted_hex)
            self.bytes_container.hide()
            self.data_text.show()
        
        # 更新解析字段
        self._update_fields(frame)
        
        # 更新校验信息
        self._update_checksum(frame)
    
    def _create_interactive_bytes(self, raw_data: bytes):
        """创建交互式字节视图（带地址偏移列）"""
        # 清空现有字节标签
        while self.bytes_layout.count():
            item = self.bytes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.byte_labels.clear()
        
        # 为字段分配颜色
        self._assign_field_colors()
        
        # 每行16个字节，第0列为地址偏移
        bytes_per_row = 16
        
        for i, byte in enumerate(raw_data):
            row = i // bytes_per_row
            col = (i % bytes_per_row) + 1  # +1 为地址列留出空间
            
            # 每行开头添加地址偏移标签
            if i % bytes_per_row == 0:
                addr_label = QLabel(f"{row * bytes_per_row:04X}:")
                addr_label.setStyleSheet("""
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 13px;
                    font-weight: bold;
                    color: #0078D4;
                    padding: 3px 8px 3px 3px;
                    min-width: 50px;
                """)
                addr_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.bytes_layout.addWidget(addr_label, row, 0)
            
            label = ClickableByteLabel(f"{byte:02X}", i)
            label.clicked.connect(self._on_byte_clicked)
            label.hovered.connect(self._on_byte_hovered)
            
            self.bytes_layout.addWidget(label, row, col)
            self.byte_labels.append(label)
        
        # 初始高亮：为每个字段的字节设置颜色
        self._apply_field_colors_to_bytes()
    
    def _format_hex_data(self, hex_str):
        """格式化十六进制数据，每行16字节，带地址偏移"""
        # 移除所有空格
        hex_str = hex_str.replace(" ", "")
        
        # 每2个字符(1字节)添加空格，每16字节换行，添加地址偏移
        formatted = []
        line_bytes = []
        
        for i in range(0, len(hex_str), 2):
            byte_index = i // 2
            byte_hex = hex_str[i:i+2]
            
            # 行首添加地址偏移
            if byte_index % 16 == 0:
                if line_bytes:
                    # 添加上一行
                    formatted.append(" ".join(line_bytes))
                    formatted.append("\n")
                    line_bytes = []
                # 添加地址偏移前缀
                line_bytes.append(f"{byte_index:04X}:")
            
            line_bytes.append(byte_hex)
        
        # 添加最后一行
        if line_bytes:
            formatted.append(" ".join(line_bytes))
        
        return "".join(formatted).strip()
    
    def _update_fields(self, frame):
        """更新解析字段显示 - 支持交互式高亮和缩放值显示"""
        # 清空现有字段
        while self.fields_grid.count():
            item = self.fields_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.field_widgets.clear()
        
        fields = frame.fields
        if not fields:
            self.no_fields_label.show()
            return
        
        self.no_fields_label.hide()
        
        # 导入格式化函数
        from models.protocol import format_field_value
        
        # 添加字段（2列布局）
        row = 0
        col = 0
        for key, value in fields.items():
            # 跳过内部字段
            if key.startswith('_'):
                continue
            
            # 格式化字段值
            formatted_value = format_field_value(value)
            
            # 检查是否有缩放后的值
            scaled_value = frame.get_field_scaled_value(key)
            if scaled_value:
                # 显示原始值和缩放后的值
                formatted_value = f"{formatted_value} → {scaled_value}"
            
            # 创建可交互的字段标签
            field_widget = ClickableFieldLabel(key, formatted_value)
            field_widget.clicked.connect(self._on_field_clicked)
            field_widget.hovered.connect(self._on_field_hovered)
            
            # 如果有颜色分配，设置背景色
            if key in self.field_colors:
                field_widget.highlight_color = self.field_colors[key]
            
            self.field_widgets[key] = field_widget
            
            # 添加到网格
            self.fields_grid.addWidget(field_widget, row, col)
            
            # 更新行列（2列布局）
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
    
    # ============ 双向高亮联动方法 ============
    
    def _assign_field_colors(self):
        """为每个字段分配唯一颜色"""
        self.field_colors.clear()
        color_index = 0
        
        for field_name in self.field_byte_positions.keys():
            self.field_colors[field_name] = self.FIELD_COLORS[color_index % len(self.FIELD_COLORS)]
            color_index += 1
    
    def _apply_field_colors_to_bytes(self):
        """将字段颜色应用到对应的字节标签"""
        for field_name, (start, end) in self.field_byte_positions.items():
            color = self.field_colors.get(field_name, "#FFF3CD")
            for i in range(start, end):
                if 0 <= i < len(self.byte_labels):
                    self.byte_labels[i].set_highlighted(True, color)
    
    def _get_field_at_byte(self, byte_index: int) -> str:
        """获取指定字节位置对应的字段名"""
        for field_name, (start, end) in self.field_byte_positions.items():
            if start <= byte_index < end:
                return field_name
        return ""
    
    def _highlight_field(self, field_name: str, highlight: bool = True):
        """高亮指定字段及其对应的字节"""
        if not field_name:
            return
        
        color = self.field_colors.get(field_name, "#FFF3CD")
        
        # 高亮字段标签
        if field_name in self.field_widgets:
            self.field_widgets[field_name].set_highlighted(highlight, color)
        
        # 高亮对应的字节
        if field_name in self.field_byte_positions:
            start, end = self.field_byte_positions[field_name]
            for i in range(start, end):
                if 0 <= i < len(self.byte_labels):
                    # 使用更强的高亮色
                    highlight_color = "#FFD700" if highlight else color
                    self.byte_labels[i].set_highlighted(True, highlight_color)
    
    def _clear_all_highlights(self):
        """清除所有临时高亮（恢复到字段颜色）"""
        self._apply_field_colors_to_bytes()
        for widget in self.field_widgets.values():
            widget.set_highlighted(False)
    
    def _on_byte_clicked(self, byte_index: int):
        """字节被点击时触发"""
        # 清除之前的高亮
        self._clear_all_highlights()
        
        # 找到对应的字段并高亮
        field_name = self._get_field_at_byte(byte_index)
        if field_name:
            self._highlight_field(field_name, True)
    
    def _on_byte_hovered(self, byte_index: int):
        """字节被悬停时触发"""
        # 找到对应的字段
        field_name = self._get_field_at_byte(byte_index)
        if field_name and field_name in self.field_widgets:
            # 临时高亮字段标签
            self.field_widgets[field_name].set_highlighted(True)
    
    def _on_field_clicked(self, field_name: str):
        """字段被点击时触发"""
        # 清除之前的高亮
        self._clear_all_highlights()
        
        # 高亮字段及其对应的字节
        self._highlight_field(field_name, True)
    
    def _on_field_hovered(self, field_name: str):
        """字段被悬停时触发"""
        if field_name in self.field_byte_positions:
            # 临时高亮对应的字节
            start, end = self.field_byte_positions[field_name]
            for i in range(start, end):
                if 0 <= i < len(self.byte_labels):
                    self.byte_labels[i].set_highlighted(True, "#FFD700")
    
    def leaveEvent(self, event):
        """鼠标离开界面时恢复默认状态"""
        self._apply_field_colors_to_bytes()
        super().leaveEvent(event)