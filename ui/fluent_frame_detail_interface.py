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

from utils.theme_helper import ThemeHelper as TH


class ClickableByteLabel(QLabel):
    """可点击的字节标签，用于显示单个十六进制字节"""
    
    clicked = Signal(int)  # 发送字节索引
    
    def __init__(self, byte_value: str, byte_index: int, parent=None):
        super().__init__(byte_value, parent)
        self.byte_index = byte_index
        self.is_highlighted = False
        self._type_color = None  # 字段类型背景色
        
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(30, 24)
        self.setStyleSheet(TH.byte_style_normal())
    
    def set_type_color(self, color: str):
        """设置字段类型背景色（第一层颜色）"""
        self._type_color = color
        if not self.is_highlighted:
            if color:
                self.setStyleSheet(TH.byte_style_typed(color))
            else:
                self.setStyleSheet(TH.byte_style_normal())
    
    def set_highlighted(self, highlighted: bool, color: str = None):
        """设置高亮状态（统一金色高亮），避免不必要的更新"""
        if self.is_highlighted == highlighted:
            return  # 状态未变，不更新
        self.is_highlighted = highlighted
        if highlighted:
            self.setStyleSheet(TH.byte_style_selected('#FFD700'))
        else:
            # 恢复 zebra 背景色
            self.set_type_color(self._type_color)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.byte_index)
        super().mousePressEvent(event)
# 注意: FIELD_STYLE_NORMAL / FIELD_STYLE_HIGHLIGHT 已改为通过 TH 动态获取


class ClickableFieldLabel(QFrame):
    """可点击的字段标签，支持两层颜色（类型背景+选中高亮）"""
    
    clicked = Signal(str)  # 发送字段名
    
    def __init__(self, field_name: str, field_value: str, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.is_highlighted = False
        self._type_color = None
        self.highlight_color = "#FFD700"
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # 字段名标签
        self.name_label = QLabel(f"🔹 {field_name}:")
        self.name_label.setStyleSheet(TH.field_name_style())
        
        # 字段值标签
        self.value_label = QLabel(field_value)
        self.value_label.setWordWrap(True)
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.value_label.setStyleSheet(TH.accent_mono_style())
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.value_label, 1)
        
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(TH.field_style_normal())
    
    def set_type_color(self, color: str):
        """设置字段类型背景色（第一层颜色）"""
        self._type_color = color
        if not self.is_highlighted:
            if color:
                self.setStyleSheet(TH.field_style_typed(color))
            else:
                self.setStyleSheet(TH.field_style_normal())
    
    def set_highlighted(self, highlighted: bool, color: str = None):
        """设置高亮状态（统一金色高亮），避免不必要的更新"""
        if self.is_highlighted == highlighted:
            return  # 状态未变，不更新
        self.is_highlighted = highlighted
        if highlighted:
            self.setStyleSheet(TH.field_style_selected('#FFD700'))
            self.name_label.setStyleSheet("font-weight: bold; color: #333;")
            self.value_label.setStyleSheet("color: #333; font-family: 'Courier New', monospace;")
        else:
            if self._type_color:
                self.set_type_color(self._type_color)
            else:
                self.setStyleSheet(TH.field_style_normal())
            self.name_label.setStyleSheet(TH.field_name_style())
            self.value_label.setStyleSheet(TH.accent_mono_style())
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.field_name)
        super().mousePressEvent(event)
class FrameDetailInterface(QWidget):
    """帧详情界面 - 支持双向高亮联动 + 两层颜色体系"""
    
    # 高亮颜色（点击时的边框颜色）
    HIGHLIGHT_COLOR = "#FFD700"  # 金黄色高亮
    HIGHLIGHT_BORDER_COLOR = "#FFA000"  # 深金色边框
    
    def __init__(self, color_config=None, parent=None):
        super().__init__(parent)
        self.setObjectName("frame_detail_interface")
        
        # 颜色配置（用于字段类型背景色）
        self._color_config = color_config
        
        # 当前帧数据
        self.current_frame = None
        # 字段到字节位置的映射
        self.field_byte_positions = {}
        # 字段类型映射（用于颜色查找）
        self.field_types = {}
        # 字节标签列表
        self.byte_labels = []
        # 字段标签字典
        self.field_widgets = {}
        # 字段颜色映射
        self.field_colors = {}
        # 当前高亮的字段（用于点击切换）
        self.current_highlighted_field = None
        
        # 滚动区域
        self.scroll = ScrollArea(self)
        self.scroll.setWidgetResizable(True)
        
        # 滚动内容容器
        self.scroll_widget = QWidget()
        self.scroll.setWidget(self.scroll_widget)
        self.scroll.enableTransparentBackground()
        
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
        
        # 安装事件过滤器：点击空白区域（卡片间隙/卡片内非交互区域）取消高亮
        self.scroll_widget.installEventFilter(self)
        for _card in (self.basic_card, self.data_card, self.fields_card, self.checksum_card):
            _card.installEventFilter(self)
        
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
        TH.apply_title_accent(title)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self._basic_hint = BodyLabel("数据帧的基本属性")
        TH.apply_hint(self._basic_hint)
        title_layout.addWidget(self._basic_hint)
        card_layout.addLayout(title_layout)
        
        # 信息网格
        info_grid = QGridLayout()
        info_grid.setSpacing(15)
        info_grid.setColumnStretch(1, 1)
        info_grid.setColumnStretch(3, 1)
        
        # 标签样式
        label_style = TH.label_style()
        value_style = TH.value_style()
        
        # 帧序号
        self.frame_num_label = BodyLabel("🔢 帧序号:")
        TH.apply_label(self.frame_num_label)
        self.frame_num_value = BodyLabel("")
        self.frame_num_value.setStyleSheet(value_style)
        info_grid.addWidget(self.frame_num_label, 0, 0)
        info_grid.addWidget(self.frame_num_value, 0, 1)
        
        # 数据长度
        self.length_label = BodyLabel("📏 数据长度:")
        TH.apply_label(self.length_label)
        self.length_value = BodyLabel("")
        self.length_value.setStyleSheet(value_style)
        info_grid.addWidget(self.length_label, 0, 2)
        info_grid.addWidget(self.length_value, 0, 3)
        
        # 起始位置
        self.start_label = BodyLabel("📍 起始位置:")
        TH.apply_label(self.start_label)
        self.start_value = BodyLabel("")
        self.start_value.setStyleSheet(value_style)
        info_grid.addWidget(self.start_label, 1, 0)
        info_grid.addWidget(self.start_value, 1, 1)
        
        # 结束位置
        self.end_label = BodyLabel("🏁 结束位置:")
        TH.apply_label(self.end_label)
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
        TH.apply_title_accent(title)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self._data_hint = BodyLabel("点击字节/字段高亮，再次点击或点击空白取消")
        TH.apply_hint(self._data_hint)
        title_layout.addWidget(self._data_hint)
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
        self.data_text.setStyleSheet(TH.data_textbox_style())
        self.data_text.hide()  # 默认隐藏
        card_layout.addWidget(self.data_text)
        
        # 底部说明
        desc_layout = QHBoxLayout()
        desc_layout.setSpacing(20)
        
        self._desc1 = BodyLabel("💡 点击字节或字段高亮")
        TH.apply_hint(self._desc1, pixel_size=12)
        desc_layout.addWidget(self._desc1)
        
        self._desc2 = BodyLabel("📋 再次点击或点空白取消")
        TH.apply_hint(self._desc2, pixel_size=12)
        desc_layout.addWidget(self._desc2)
        
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
        TH.apply_title_accent(title)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self._fields_hint = BodyLabel("根据协议配置解析出的各个字段值")
        TH.apply_hint(self._fields_hint)
        title_layout.addWidget(self._fields_hint)
        card_layout.addLayout(title_layout)
        
        # 字段网格容器
        self.fields_grid = QGridLayout()
        self.fields_grid.setSpacing(12)
        self.fields_grid.setColumnStretch(1, 1)
        self.fields_grid.setColumnStretch(3, 1)
        card_layout.addLayout(self.fields_grid)
        
        # 空状态提示
        self.no_fields_label = BodyLabel("暂无解析字段")
        TH.apply_no_data(self.no_fields_label)
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
        TH.apply_title_accent(title)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self._checksum_hint = BodyLabel("数据帧的校验码验证结果")
        TH.apply_hint(self._checksum_hint)
        title_layout.addWidget(self._checksum_hint)
        card_layout.addLayout(title_layout)
        
        # 校验信息网格
        check_grid = QGridLayout()
        check_grid.setSpacing(15)
        check_grid.setColumnStretch(1, 1)
        check_grid.setColumnStretch(3, 1)
        
        # 校验结果
        self.valid_label = BodyLabel("🎯 校验结果:")
        TH.apply_label(self.valid_label)
        self.valid_value = BodyLabel("")
        check_grid.addWidget(self.valid_label, 0, 0)
        check_grid.addWidget(self.valid_value, 0, 1)
        
        # 计算校验
        self.expected_label = BodyLabel("📝 计算校验:")
        TH.apply_label(self.expected_label)
        self.expected_value = BodyLabel("")
        TH.apply_accent_mono(self.expected_value)
        check_grid.addWidget(self.expected_label, 1, 0)
        check_grid.addWidget(self.expected_value, 1, 1)
        
        # 帧内校验
        self.actual_label = BodyLabel("🔢 帧内校验:")
        TH.apply_label(self.actual_label)
        self.actual_value = BodyLabel("")
        TH.apply_accent_mono(self.actual_value)
        check_grid.addWidget(self.actual_label, 1, 2)
        check_grid.addWidget(self.actual_value, 1, 3)
        
        card_layout.addLayout(check_grid)
        
        # 错误信息
        self.error_label = BodyLabel("")
        self.error_label.setStyleSheet(TH.error_label_style())
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        
        card_layout.addWidget(self.error_label)
        
        self.main_layout.addWidget(self.checksum_card)
    
    def show_frame(self, frame):
        """显示帧详情"""
        self.current_frame = frame
        self.current_highlighted_field = None  # 重置高亮状态，防止帧切换后同名字段首次点击无反应
        
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
        # 保存字段类型信息（用于两层颜色体系）
        self.field_types = getattr(frame, 'field_types', {})
        
        # 创建交互式字节视图（如果数据不太长）
        if len(frame.raw_data) <= 128:
            self._create_interactive_bytes(frame.raw_data)
            self.bytes_container.show()
            self.data_text.hide()
            self._data_hint.setText("点击字节/字段高亮，再次点击或点击空白取消")
        else:
            # 数据太长，使用传统文本显示
            formatted_hex = self._format_hex_data(raw_hex)
            self.data_text.setPlainText(formatted_hex)
            self.bytes_container.hide()
            self.data_text.show()
            self._data_hint.setText("⚠️ 数据较长(>128字节)，字节高亮联动不可用")
        
        # 更新解析字段
        self._update_fields(frame)
        
        # 更新校验信息
        self._update_checksum(frame)
    
    def _create_interactive_bytes(self, raw_data: bytes):
        """创建交互式字节视图（带地址偏移列）"""
        # 清空现有字节标签（先断开信号防止 deleteLater 窗口期误触发）
        while self.bytes_layout.count():
            item = self.bytes_layout.takeAt(0)
            w = item.widget()
            if w:
                if hasattr(w, 'clicked'):
                    try:
                        w.clicked.disconnect()
                    except (RuntimeError, TypeError):
                        pass
                w.deleteLater()
        
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
                addr_label.setStyleSheet(TH.addr_label_style())
                addr_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.bytes_layout.addWidget(addr_label, row, 0)
            
            label = ClickableByteLabel(f"{byte:02X}", i)
            label.clicked.connect(self._on_byte_clicked)
            
            self.bytes_layout.addWidget(label, row, col)
            self.byte_labels.append(label)
        
        # 应用字段类型背景色到字节标签
        self._apply_type_colors_to_bytes()
    
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
        # 清空现有字段（先断开信号防止 deleteLater 窗口期误触发）
        while self.fields_grid.count():
            item = self.fields_grid.takeAt(0)
            w = item.widget()
            if w:
                if hasattr(w, 'clicked'):
                    try:
                        w.clicked.disconnect()
                    except (RuntimeError, TypeError):
                        pass
                w.deleteLater()
        
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
            
            # 应用 zebra 背景色
            if key in self.field_colors:
                field_widget.set_type_color(self.field_colors[key])
            
            self.field_widgets[key] = field_widget
            
            # 添加到网格
            self.fields_grid.addWidget(field_widget, row, col)
            
            # 更新行列（2列布局）
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def _update_checksum(self, frame):
        """更新校验信息（含智能诊断提示）"""
        if frame.expected_checksum is not None:
            # 校验结果
            if frame.checksum_valid:
                self.valid_value.setText("✅ 校验通过")
                TH.apply_checksum_pass(self.valid_value)
            else:
                self.valid_value.setText("❌ 校验失败")
                TH.apply_checksum_fail(self.valid_value)
            
            # 期望和实际校验值
            self.expected_value.setText(f"0x{frame.expected_checksum:02X}")
            self.actual_value.setText(f"0x{frame.actual_checksum:02X}")
            
            # 校验失败时添加智能诊断提示
            if not frame.checksum_valid:
                hints = self._generate_checksum_hints(frame)
                if hints:
                    hint_text = "💡 可能原因:\n" + "\n".join(f"  • {h}" for h in hints)
                    self.error_label.setText(hint_text)
                    self.error_label.setStyleSheet(TH.warning_label_style())  # 复杂样式保留 setStyleSheet
                    self.error_label.show()
            
            # 显示卡片
            self.checksum_card.show()
        else:
            # 没有校验信息时隐藏卡片
            self.checksum_card.hide()
        
        # 错误信息
        if frame.has_error:
            self.error_label.setText(f"⚠️ 错误: {frame.error_message}")
            self.error_label.setStyleSheet(TH.error_label_style())  # 复杂样式保留 setStyleSheet
            self.error_label.show()
        elif frame.checksum_valid or frame.expected_checksum is None:
            self.error_label.hide()
    
    def _generate_checksum_hints(self, frame) -> list:
        """
        根据校验失败的数据生成诊断提示
        
        分析策略:
        1. 字节序方向是否颠倒
        2. 校验范围是否可能偏移 ±1
        """
        hints = []
        expected = frame.expected_checksum
        actual = frame.actual_checksum
        
        if expected is None or actual is None:
            return hints
        
        # 检查字节序颠倒（2字节校验码常见）
        if expected > 0xFF or actual > 0xFF:
            # 交换高低字节
            expected_swapped = ((expected & 0xFF) << 8) | ((expected >> 8) & 0xFF)
            if expected_swapped == actual:
                hints.append("计算结果与帧内校验码字节序相反，请检查校验码字节序配置（大端/小端）")
        
        # 检查差值为一个固定偏移（可能是校验范围偏移±1）
        diff = abs(expected - actual)
        if 1 <= diff <= 5:
            hints.append(f"计算值与帧内值仅差 {diff}，可能是校验起始/结束位置偏差 1 字节")
        
        # 如果两者完全不同，给出通用提示
        if not hints:
            hints.append("请确认校验算法类型、校验范围和校验码位置是否正确")
            hints.append("可尝试调整校验起始/结束位置，或切换校验算法")
        
        return hints
    
    # ============ 双向高亮联动方法 ============
    
    def _apply_type_colors_to_bytes(self):
        """将字段类型背景色应用到对应的字节标签，并在字段边界添加分隔线"""
        # 构建每个字节所属的字段索引 (用于边界检测)
        field_names = list(self.field_byte_positions.keys())
        byte_field_idx = {}  # byte_index → field_index
        for idx, (field_name, (start, end)) in enumerate(self.field_byte_positions.items()):
            for i in range(start, end):
                byte_field_idx[i] = idx
        
        for field_name, (start, end) in self.field_byte_positions.items():
            color = self.field_colors.get(field_name)
            if color:
                for i in range(max(0, start), min(end, len(self.byte_labels))):
                    self.byte_labels[i].set_type_color(color)
    
    def _assign_field_colors(self):
        """
        为每个字段分配颜色（Zebra Striping 方案）
        
        正常态: 相邻字段使用交替浅色底色，清晰区分字段边界
        选中态: 点击时统一使用金色高亮
        """
        self.field_colors.clear()
        
        field_names = list(self.field_byte_positions.keys())
        
        for idx, field_name in enumerate(field_names):
            if idx % 2 == 0:
                self.field_colors[field_name] = TH.zebra_even_bg()
            else:
                self.field_colors[field_name] = TH.zebra_odd_bg()
    
    def _get_field_at_byte(self, byte_index: int) -> str:
        """获取指定字节位置对应的字段名"""
        for field_name, (start, end) in self.field_byte_positions.items():
            if start <= byte_index < end:
                return field_name
        return ""
    
    def _highlight_field(self, field_name: str, highlight: bool = True):
        """高亮指定字段及其对应的字节 - 优化版本，只更新相关标签"""
        if not field_name:
            return
        
        # 高亮字段标签
        if field_name in self.field_widgets:
            self.field_widgets[field_name].set_highlighted(highlight)
        
        # 高亮对应的字节
        if field_name in self.field_byte_positions:
            start, end = self.field_byte_positions[field_name]
            # 直接更新指定范围的标签，不遍历全部
            for i in range(max(0, start), min(end, len(self.byte_labels))):
                self.byte_labels[i].set_highlighted(highlight)
    
    def _clear_all_highlights(self):
        """清除当前高亮的字段（只更新需要清除的部分）"""
        # 只清除当前高亮的字段，不遍历所有标签
        if self.current_highlighted_field:
            self._highlight_field(self.current_highlighted_field, False)
    
    def _on_byte_clicked(self, byte_index: int):
        """字节被点击时触发"""
        # 找到对应的字段
        field_name = self._get_field_at_byte(byte_index)
        
        if field_name:
            # 如果点击的是当前已高亮的字段，则取消高亮
            if field_name == self.current_highlighted_field:
                self._clear_all_highlights()
                self.current_highlighted_field = None
            else:
                # 清除之前的高亮
                self._clear_all_highlights()
                # 高亮新字段
                self._highlight_field(field_name, True)
                self.current_highlighted_field = field_name
        else:
            # 点击的是空白区域（不属于任何字段的字节），取消高亮
            self._clear_all_highlights()
            self.current_highlighted_field = None
    
    def _on_field_clicked(self, field_name: str):
        """字段被点击时触发"""
        if field_name:
            # 如果点击的是当前已高亮的字段，则取消高亮
            if field_name == self.current_highlighted_field:
                self._clear_all_highlights()
                self.current_highlighted_field = None
            else:
                # 清除之前的高亮
                self._clear_all_highlights()
                # 高亮字段及其对应的字节
                self._highlight_field(field_name, True)
                self.current_highlighted_field = field_name
    
    def eventFilter(self, watched, event):
        """事件过滤器 - 点击卡片/滚动区域空白处取消高亮
        
        只在点击目标是 watched 自身（非子控件）时才清除高亮，
        避免拦截 ClickableByteLabel / ClickableFieldLabel 的正常点击。
        """
        from PySide6.QtCore import QEvent
        if (event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.LeftButton
                and self.current_highlighted_field):
            # 检查点击的直接子控件——如果点击在交互标签上则不清除
            child = watched.childAt(event.pos())
            if child is None or not isinstance(child, (ClickableByteLabel, ClickableFieldLabel)):
                # 也排除 ClickableFieldLabel 内部的 QLabel 子控件
                parent = child.parent() if child else None
                if not isinstance(parent, (ClickableByteLabel, ClickableFieldLabel)):
                    self._clear_all_highlights()
                    self.current_highlighted_field = None
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        """点击空白区域取消高亮（兜底）"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and self.current_highlighted_field:
            child = self.childAt(event.pos())
            if child is None:
                self._clear_all_highlights()
                self.current_highlighted_field = None

    # ============ 主题刷新 ============

    def _refresh_styles(self):
        """主题切换后刷新所有样式
        
        注: FluentLabelBase 通过 setTextColor 设置的颜色会自动跟随主题，
        仅 value_style 等复杂样式 (含 background/padding) 需要手动刷新。
        """
        # value_style 含 background/padding，需要手动刷新 (setStyleSheet)
        value_style = TH.value_style()
        for lbl in (self.frame_num_value, self.length_value,
                    self.start_value, self.end_value):
            lbl.setStyleSheet(value_style)

        # QTextEdit 不是 FluentLabelBase，需要手动刷新
        self.data_text.setStyleSheet(TH.data_textbox_style())

        # 如果有帧数据，刷新交互式字节视图 (ClickableByteLabel / ClickableFieldLabel 是 QLabel/QFrame)
        if self.current_frame:
            self.show_frame(self.current_frame)