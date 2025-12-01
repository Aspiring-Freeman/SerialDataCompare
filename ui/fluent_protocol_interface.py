# This Python file uses the following encoding: utf-8
"""
协议配置界面 - Fluent Design
"""
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PySide6.QtCore import Signal, Qt

from qfluentwidgets import (
    ScrollArea, CardWidget, PushButton, LineEdit, SpinBox,
    ComboBox, CheckBox, TextEdit, TitleLabel, SubtitleLabel,
    BodyLabel, FluentIcon as FIF, InfoBar, InfoBarPosition
)

from models import ProtocolConfig, FieldDefinition, ChecksumConfig, ChecksumType, FieldType, Endianness
from ui.protocol_history_dialog import ProtocolHistoryDialog


class ProtocolInterface(QWidget):
    """协议配置界面"""
    
    protocol_loaded = Signal(ProtocolConfig)
    protocol_saved = Signal(ProtocolConfig)
    
    def __init__(self, protocol_history=None, parent=None):
        super().__init__(parent)
        self.setObjectName("protocol_interface")
        self.protocol_history = protocol_history
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 创建滚动区域
        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none}")
        
        # 滚动区域内容
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建UI
        self.create_basic_info_card()
        self.create_fields_card()
        self.create_checksum_card()
        self.create_action_buttons()
        
        # 设置滚动区域
        scroll.setWidget(self.scroll_widget)
        main_layout.addWidget(scroll)
    
    def create_basic_info_card(self):
        """创建基本信息卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = TitleLabel("协议基本信息")
        card_layout.addWidget(title)
        
        # 协议名称
        name_layout = QHBoxLayout()
        name_layout.setSpacing(15)
        name_label = BodyLabel("协议名称:")
        name_label.setFixedWidth(120)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("请输入协议名称")
        self.name_edit.setMinimumWidth(300)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit, 1)
        card_layout.addLayout(name_layout)
        
        # 协议描述
        desc_label = BodyLabel("协议描述:")
        self.desc_edit = TextEdit()
        self.desc_edit.setPlaceholderText("请输入协议描述（可选）")
        self.desc_edit.setFixedHeight(100)
        card_layout.addWidget(desc_label)
        card_layout.addWidget(self.desc_edit)
        
        # 帧头
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        header_label = BodyLabel("帧头 (Hex):")
        header_label.setFixedWidth(120)
        self.header_edit = LineEdit()
        self.header_edit.setPlaceholderText("例如: AA BB")
        self.header_edit.setMinimumWidth(300)
        header_layout.addWidget(header_label)
        header_layout.addWidget(self.header_edit, 1)
        card_layout.addLayout(header_layout)
        
        # 帧尾
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(15)
        footer_label = BodyLabel("帧尾 (Hex):")
        footer_label.setFixedWidth(120)
        self.footer_edit = LineEdit()
        self.footer_edit.setPlaceholderText("例如: 0D 0A")
        self.footer_edit.setMinimumWidth(300)
        footer_layout.addWidget(footer_label)
        footer_layout.addWidget(self.footer_edit, 1)
        card_layout.addLayout(footer_layout)
        
        self.scroll_layout.addWidget(card)
    
    def create_fields_card(self):
        """创建字段定义卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        
        # 标题
        title_layout = QHBoxLayout()
        title = TitleLabel("字段定义")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 全部锁定按钮
        lock_all_btn = PushButton(FIF.ACCEPT, "全部锁定")
        lock_all_btn.clicked.connect(self.lock_all_fields)
        title_layout.addWidget(lock_all_btn)
        
        # 全部解锁按钮
        unlock_all_btn = PushButton(FIF.CANCEL, "全部解锁")
        unlock_all_btn.clicked.connect(self.unlock_all_fields)
        title_layout.addWidget(unlock_all_btn)
        
        # 添加字段按钮
        add_btn = PushButton(FIF.ADD, "添加字段")
        add_btn.clicked.connect(self.add_field)
        title_layout.addWidget(add_btn)
        card_layout.addLayout(title_layout)
        
        # 字段列表容器
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setSpacing(10)
        card_layout.addWidget(self.fields_container)
        
        self.scroll_layout.addWidget(card)
    
    def create_checksum_card(self):
        """创建校验配置卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = TitleLabel("校验配置")
        card_layout.addWidget(title)
        
        # 启用校验
        self.checksum_enable = CheckBox("启用校验")
        card_layout.addWidget(self.checksum_enable)
        
        # 校验类型
        type_layout = QHBoxLayout()
        type_layout.setSpacing(15)
        type_label = BodyLabel("校验类型:")
        type_label.setFixedWidth(120)
        self.checksum_type = ComboBox()
        self.checksum_type.addItems([
            "无校验",
            "累加和", "累加和16位",
            "异或校验", "异或校验16位",
            "CRC-8", "CRC-8/ITU", "CRC-8/ROHC", "CRC-8/MAXIM",
            "CRC-16/MODBUS", "CRC-16/IBM", "CRC-16/CCITT", "CRC-16/CCITT-FALSE",
            "CRC-16/XMODEM", "CRC-16/X25", "CRC-16/DNP", "CRC-16/USB", "CRC-16/MAXIM",
            "CRC-32", "CRC-32/MPEG-2", "CRC-32/POSIX",
            "LRC", "BCC", "Fletcher-16", "Fletcher-32", "Adler-32"
        ])
        self.checksum_type.setMinimumWidth(200)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.checksum_type, 1)
        card_layout.addLayout(type_layout)
        
        # 校验码位置（在整帧中的索引）
        checksum_pos_layout = QHBoxLayout()
        checksum_pos_layout.setSpacing(15)
        checksum_pos_label = BodyLabel("校验码位置:")
        checksum_pos_label.setFixedWidth(120)
        self.checksum_byte_position = SpinBox()
        self.checksum_byte_position.setRange(0, 1000)
        self.checksum_byte_position.setValue(0)
        self.checksum_byte_position.setMinimumWidth(100)
        checksum_pos_help = BodyLabel("(从0开始的字节索引)")
        checksum_pos_help.setStyleSheet("color: #999999;")
        checksum_pos_layout.addWidget(checksum_pos_label)
        checksum_pos_layout.addWidget(self.checksum_byte_position)
        checksum_pos_layout.addWidget(checksum_pos_help)
        checksum_pos_layout.addStretch()
        card_layout.addLayout(checksum_pos_layout)
        
        # 连接校验码位置变化信号，检查是否需要同步字节序
        self.checksum_byte_position.valueChanged.connect(self._on_checksum_position_changed)
        
        # 校验码长度
        checksum_len_layout = QHBoxLayout()
        checksum_len_layout.setSpacing(15)
        checksum_len_label = BodyLabel("校验码长度:")
        checksum_len_label.setFixedWidth(120)
        self.checksum_length = SpinBox()
        self.checksum_length.setRange(1, 8)
        self.checksum_length.setValue(1)
        self.checksum_length.setMinimumWidth(100)
        checksum_len_help = BodyLabel("(字节数)")
        checksum_len_help.setStyleSheet("color: #999999;")
        checksum_len_layout.addWidget(checksum_len_label)
        checksum_len_layout.addWidget(self.checksum_length)
        checksum_len_layout.addWidget(checksum_len_help)
        checksum_len_layout.addStretch()
        card_layout.addLayout(checksum_len_layout)
        
        # 连接校验码长度变化信号，同步到关联字段
        self.checksum_length.valueChanged.connect(self._on_checksum_length_changed)
        
        # 校验码字节序
        checksum_endian_layout = QHBoxLayout()
        checksum_endian_layout.setSpacing(15)
        checksum_endian_label = BodyLabel("校验码字节序:")
        checksum_endian_label.setFixedWidth(120)
        self.checksum_endianness = ComboBox()
        self.checksum_endianness.addItems(["小端(低字节在前)", "大端(高字节在前)"])
        self.checksum_endianness.setCurrentIndex(0)  # 默认小端（MODBUS常用）
        self.checksum_endianness.setMinimumWidth(200)
        checksum_endian_help = BodyLabel("(如CRC16 0x1234: 小端=34 12, 大端=12 34)")
        checksum_endian_help.setStyleSheet("color: #999999;")
        checksum_endian_layout.addWidget(checksum_endian_label)
        checksum_endian_layout.addWidget(self.checksum_endianness)
        checksum_endian_layout.addWidget(checksum_endian_help)
        checksum_endian_layout.addStretch()
        card_layout.addLayout(checksum_endian_layout)
        
        # 关联字段名（用于字节序和长度联动）
        link_field_layout = QHBoxLayout()
        link_field_layout.setSpacing(15)
        link_field_label = BodyLabel("关联字段名:")
        link_field_label.setFixedWidth(120)
        self.checksum_link_field = LineEdit()
        self.checksum_link_field.setPlaceholderText("输入字段名以同步长度和字节序，留空则自动匹配")
        self.checksum_link_field.setMinimumWidth(300)
        link_field_help = BodyLabel("(与上方字段定义联动)")
        link_field_help.setStyleSheet("color: #999999;")
        link_field_layout.addWidget(link_field_label)
        link_field_layout.addWidget(self.checksum_link_field, 1)
        link_field_layout.addWidget(link_field_help)
        card_layout.addLayout(link_field_layout)
        
        # 连接校验配置字节序变化信号，同步到匹配的字段
        self.checksum_endianness.currentTextChanged.connect(self._on_checksum_endianness_changed)
        
        # 校验范围起始
        start_layout = QHBoxLayout()
        start_layout.setSpacing(15)
        start_label = BodyLabel("校验起始位置:")
        start_label.setFixedWidth(120)
        self.checksum_start = SpinBox()
        self.checksum_start.setRange(0, 1000)
        self.checksum_start.setValue(0)
        self.checksum_start.setMinimumWidth(100)
        start_help = BodyLabel("(0=从帧头开始, 1=从帧头后第1字节)")
        start_help.setStyleSheet("color: #999999;")
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.checksum_start)
        start_layout.addWidget(start_help)
        start_layout.addStretch()
        card_layout.addLayout(start_layout)
        
        # 校验范围结束
        end_layout = QHBoxLayout()
        end_layout.setSpacing(15)
        end_label = BodyLabel("校验结束位置:")
        end_label.setFixedWidth(120)
        self.checksum_end = SpinBox()
        self.checksum_end.setRange(0, 1000)
        self.checksum_end.setValue(0)
        self.checksum_end.setMinimumWidth(100)
        end_help = BodyLabel("(不包含,空表示到校验码前)")
        end_help.setStyleSheet("color: #999999;")
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.checksum_end)
        end_layout.addWidget(end_help)
        end_layout.addStretch()
        card_layout.addLayout(end_layout)
        
        # 校验位置（相对位置，保留用于向后兼容）
        pos_layout = QHBoxLayout()
        pos_layout.setSpacing(15)
        pos_label = BodyLabel("相对位置:")
        pos_label.setFixedWidth(120)
        self.checksum_position = ComboBox()
        self.checksum_position.addItems([
            "帧尾前", "帧尾后"
        ])
        self.checksum_position.setMinimumWidth(200)
        pos_help = BodyLabel("(仅当绝对位置未设置时使用)")
        pos_help.setStyleSheet("color: #999999;")
        pos_layout.addWidget(pos_label)
        pos_layout.addWidget(self.checksum_position, 1)
        pos_layout.addWidget(pos_help)
        card_layout.addLayout(pos_layout)
        
        self.scroll_layout.addWidget(card)
    
    def create_action_buttons(self):
        """创建操作按钮"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 加载协议
        load_btn = PushButton(FIF.FOLDER, "加载协议")
        load_btn.clicked.connect(self.load_protocol)
        button_layout.addWidget(load_btn)
        
        # 保存协议
        save_btn = PushButton(FIF.SAVE, "保存协议")
        save_btn.clicked.connect(self.save_protocol)
        button_layout.addWidget(save_btn)
        
        # 应用协议（使当前配置生效）
        apply_btn = PushButton(FIF.ACCEPT, "应用协议")
        apply_btn.clicked.connect(self.apply_protocol)
        button_layout.addWidget(apply_btn)
        
        # 协议历史
        history_btn = PushButton(FIF.HISTORY, "协议历史")
        history_btn.clicked.connect(self.show_protocol_history)
        button_layout.addWidget(history_btn)
        
        # 清空
        clear_btn = PushButton(FIF.DELETE, "清空")
        clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        self.scroll_layout.addLayout(button_layout)
    
    def add_field(self):
        """添加字段"""
        field_card = CardWidget()
        field_layout = QHBoxLayout(field_card)
        field_layout.setSpacing(15)
        field_layout.setContentsMargins(15, 15, 15, 15)
        
        # 字段名
        name_label = BodyLabel("字段名:")
        name_label.setFixedWidth(80)
        name_edit = LineEdit()
        name_edit.setPlaceholderText("请输入字段名")
        name_edit.setMinimumWidth(200)
        field_layout.addWidget(name_label)
        field_layout.addWidget(name_edit, 2)
        
        # 字段类型
        type_label = BodyLabel("类型:")
        type_label.setFixedWidth(60)
        type_combo = ComboBox()
        type_combo.addItems(["整数", "浮点数", "字符串", "十六进制"])
        type_combo.setMinimumWidth(150)
        field_layout.addWidget(type_label)
        field_layout.addWidget(type_combo, 1)
        
        # 起始位置
        start_label = BodyLabel("起始:")
        start_label.setFixedWidth(60)
        start_spin = SpinBox()
        start_spin.setRange(0, 1000)
        start_spin.setMinimumWidth(100)
        field_layout.addWidget(start_label)
        field_layout.addWidget(start_spin, 1)
        
        # 长度
        length_label = BodyLabel("长度:")
        length_label.setFixedWidth(60)
        length_spin = SpinBox()
        length_spin.setRange(1, 100)
        length_spin.setValue(1)
        length_spin.setMinimumWidth(100)
        field_layout.addWidget(length_label)
        field_layout.addWidget(length_spin, 1)
        
        # 字节序（仅多字节类型可用）
        endian_label = BodyLabel("字节序:")
        endian_label.setFixedWidth(70)
        endian_combo = ComboBox()
        endian_combo.addItems(["大端", "小端"])
        endian_combo.setMinimumWidth(100)
        endian_combo.setEnabled(True)  # 默认启用
        field_layout.addWidget(endian_label)
        field_layout.addWidget(endian_combo, 1)
        
        # 根据类型和长度决定是否启用字节序选择
        def update_endian_state():
            length = length_spin.value()
            # 所有类型（包括字符串）在长度>1时都可以选择字节序
            if length > 1:
                endian_combo.setEnabled(True)
                endian_label.setStyleSheet("")  # 正常颜色
            else:
                # 长度为1时也启用，但显示为灰色提示
                endian_combo.setEnabled(True)
                endian_label.setStyleSheet("color: #999999;")
        
        type_combo.currentTextChanged.connect(update_endian_state)
        length_spin.valueChanged.connect(update_endian_state)
        update_endian_state()  # 初始化状态
        
        # 锁定按钮
        lock_btn = PushButton("🔓 解锁")
        lock_btn.setFixedWidth(80)
        
        # 锁定状态存储（使用列表避免闭包问题）
        lock_state = [False]
        
        # 使用默认参数捕获当前控件引用，避免闭包问题
        def make_toggle_lock(btn, state, n_edit, t_combo, s_spin, l_spin, e_combo, e_label, update_fn):
            def toggle():
                state[0] = not state[0]
                if state[0]:
                    btn.setText("🔒 已锁定")
                    n_edit.setEnabled(False)
                    t_combo.setEnabled(False)
                    s_spin.setEnabled(False)
                    l_spin.setEnabled(False)
                    e_combo.setEnabled(False)
                else:
                    btn.setText("🔓 解锁")
                    n_edit.setEnabled(True)
                    t_combo.setEnabled(True)
                    s_spin.setEnabled(True)
                    l_spin.setEnabled(True)
                    # 解锁时根据当前长度判断是否启用字节序
                    length = l_spin.value()
                    if length > 1:
                        e_combo.setEnabled(True)
                        e_label.setStyleSheet("")
                    else:
                        e_combo.setEnabled(True)
                        e_label.setStyleSheet("color: #999999;")
            return toggle
        
        toggle_lock = make_toggle_lock(lock_btn, lock_state, name_edit, type_combo, 
                                       start_spin, length_spin, endian_combo, endian_label, update_endian_state)
        lock_btn.clicked.connect(toggle_lock)
        field_layout.addWidget(lock_btn)
        
        # 删除按钮
        del_btn = PushButton(FIF.DELETE, "删除")
        del_btn.setFixedWidth(80)
        del_btn.clicked.connect(lambda: self.remove_field(field_card))
        field_layout.addWidget(del_btn)
        
        # 保存控件引用到field_card，以便save_protocol时使用
        field_card.name_edit = name_edit
        field_card.type_combo = type_combo
        field_card.endian_combo = endian_combo
        field_card.start_spin = start_spin
        field_card.length_spin = length_spin
        
        # 连接字段字节序变化信号，同步到校验配置（如果位置匹配）
        endian_combo.currentTextChanged.connect(
            lambda text, fc=field_card: self._on_field_endianness_changed(fc, text)
        )
        # 当起始位置或长度变化时，检查是否需要同步
        start_spin.valueChanged.connect(
            lambda: self._check_field_checksum_sync(field_card)
        )
        length_spin.valueChanged.connect(
            lambda: self._check_field_checksum_sync(field_card)
        )
        field_card.lock_btn = lock_btn
        field_card.lock_state = lock_state
        field_card.is_locked = lambda s=lock_state: s[0]
        field_card.toggle_lock = toggle_lock
        
        self.fields_layout.addWidget(field_card)
    
    def _is_checksum_field_by_position(self, field_card) -> bool:
        """判断字段是否与校验配置关联（用于字节序联动）
        
        判断依据（按优先级）：
        1. 如果设置了"关联字段名"，则精确匹配字段名
        2. 否则，检查字段起始位置和长度是否与校验配置匹配
        3. 否则，检查字段名是否包含校验相关关键字且长度匹配
        
        Returns:
            bool: 如果匹配返回True，否则返回False
        """
        if not hasattr(field_card, 'start_spin') or not hasattr(field_card, 'length_spin'):
            return False
        
        field_start = field_card.start_spin.value()
        field_length = field_card.length_spin.value()
        field_name = field_card.name_edit.text() if hasattr(field_card, 'name_edit') else ""
        field_name_lower = field_name.lower()
        
        # 获取校验配置的位置和长度
        checksum_pos = self.checksum_byte_position.value() if hasattr(self, 'checksum_byte_position') else 0
        checksum_len = self.checksum_length.value() if hasattr(self, 'checksum_length') else 1
        
        # 获取手动指定的关联字段名
        link_field_name = ""
        if hasattr(self, 'checksum_link_field'):
            link_field_name = self.checksum_link_field.text().strip()
        
        # 方法1：如果指定了关联字段名，精确匹配
        if link_field_name:
            is_match = field_name == link_field_name
            print(f"[联动] 精确匹配'{link_field_name}': 字段'{field_name}' -> {is_match}")
            return is_match
        
        # 方法2：位置和长度都匹配
        position_match = field_start == checksum_pos and field_length == checksum_len
        if position_match:
            print(f"[联动] 位置匹配: 字段'{field_name}' 位置={field_start}, 长度={field_length}")
            return True
        
        # 方法3：字段名包含校验关键字且长度匹配
        checksum_keywords = ['crc', '校验', 'checksum', 'check', 'xor', 'lrc', 'bcc']
        name_match = any(keyword in field_name_lower for keyword in checksum_keywords) and field_length == checksum_len
        if name_match:
            print(f"[联动] 名称匹配: 字段'{field_name}' 包含校验关键字，长度={field_length}")
        return name_match
    
    def _on_field_endianness_changed(self, field_card, endian_text: str):
        """当字段的字节序改变时，同步到校验配置（如果位置匹配）
        
        Args:
            field_card: 字段卡片控件
            endian_text: 新的字节序文本（"大端" 或 "小端"）
        """
        # 只有当校验启用且字段匹配时才同步
        if not self.checksum_enable.isChecked():
            return
        
        if not self._is_checksum_field_by_position(field_card):
            return
        
        # 同步到校验配置的字节序
        if hasattr(self, 'checksum_endianness'):
            new_endian = "大端(高字节在前)" if endian_text == "大端" else "小端(低字节在前)"
            field_name = field_card.name_edit.text() if hasattr(field_card, 'name_edit') else "未知"
            print(f"[联动] 字段'{field_name}'字节序 -> 校验配置: {new_endian}")
            self.checksum_endianness.blockSignals(True)
            self.checksum_endianness.setCurrentText(new_endian)
            self.checksum_endianness.blockSignals(False)
    
    def _on_checksum_endianness_changed(self, endian_text: str):
        """当校验配置的字节序改变时，同步到匹配位置的字段
        
        Args:
            endian_text: 新的字节序文本
        """
        # 遍历所有字段，找到匹配的字段并同步
        for i in range(self.fields_layout.count()):
            field_card = self.fields_layout.itemAt(i).widget()
            if field_card and hasattr(field_card, 'endian_combo'):
                if self._is_checksum_field_by_position(field_card):
                    new_endian = "大端" if "大端" in endian_text else "小端"
                    field_name = field_card.name_edit.text() if hasattr(field_card, 'name_edit') else "未知"
                    print(f"[联动] 校验配置字节序 -> 字段'{field_name}': {new_endian}")
                    field_card.endian_combo.blockSignals(True)
                    field_card.endian_combo.setCurrentText(new_endian)
                    field_card.endian_combo.blockSignals(False)
    
    def _on_checksum_length_changed(self, new_length: int):
        """当校验码长度改变时，同步到关联的字段
        
        Args:
            new_length: 新的校验码长度
        """
        # 获取手动指定的关联字段名
        link_field_name = ""
        if hasattr(self, 'checksum_link_field'):
            link_field_name = self.checksum_link_field.text().strip()
        
        # 校验码相关关键字
        checksum_keywords = ['crc', '校验', 'checksum', 'check', 'xor', 'lrc', 'bcc']
        
        # 遍历所有字段，找到关联的字段并同步长度
        for i in range(self.fields_layout.count()):
            field_card = self.fields_layout.itemAt(i).widget()
            if field_card and hasattr(field_card, 'length_spin') and hasattr(field_card, 'name_edit'):
                field_name = field_card.name_edit.text()
                field_name_lower = field_name.lower()
                
                # 判断是否是关联的校验码字段
                is_linked = False
                if link_field_name:
                    # 如果指定了关联字段名，精确匹配
                    is_linked = field_name == link_field_name
                else:
                    # 否则通过关键字匹配
                    is_linked = any(keyword in field_name_lower for keyword in checksum_keywords)
                
                if is_linked:
                    print(f"[联动] 校验配置长度 -> 字段'{field_name}': {new_length}")
                    field_card.length_spin.blockSignals(True)
                    field_card.length_spin.setValue(new_length)
                    field_card.length_spin.blockSignals(False)
                    break  # 只同步一个匹配的字段
    
    def _on_checksum_position_changed(self, value=None):
        """当校验码位置或长度改变时，检查是否有匹配的字段需要同步字节序
        
        Args:
            value: 变化后的值（未使用，只是接收信号参数）
        """
        # 遍历所有字段，检查是否有匹配的字段
        for i in range(self.fields_layout.count()):
            field_card = self.fields_layout.itemAt(i).widget()
            if field_card and hasattr(field_card, 'endian_combo'):
                if self._is_checksum_field_by_position(field_card):
                    # 位置匹配，同步字节序（以校验配置的字节序为准）
                    if hasattr(self, 'checksum_endianness'):
                        endian_text = self.checksum_endianness.currentText()
                        field_card.endian_combo.blockSignals(True)
                        if "大端" in endian_text:
                            field_card.endian_combo.setCurrentText("大端")
                        else:
                            field_card.endian_combo.setCurrentText("小端")
                        field_card.endian_combo.blockSignals(False)
    
    def _check_field_checksum_sync(self, field_card):
        """当字段位置或长度改变时，检查是否需要同步到校验配置
        
        如果字段是关联的校验码字段，则同步长度和字节序到校验配置
        
        Args:
            field_card: 字段卡片控件
        """
        if not self.checksum_enable.isChecked():
            return
        
        if self._is_checksum_field_by_position(field_card):
            field_name = field_card.name_edit.text() if hasattr(field_card, 'name_edit') else "未知"
            
            # 同步长度到校验配置
            if hasattr(self, 'checksum_length') and hasattr(field_card, 'length_spin'):
                new_length = field_card.length_spin.value()
                print(f"[联动] 字段'{field_name}'长度 -> 校验配置: {new_length}")
                self.checksum_length.blockSignals(True)
                self.checksum_length.setValue(new_length)
                self.checksum_length.blockSignals(False)
            
            # 同步字节序到校验配置
            if hasattr(self, 'checksum_endianness') and hasattr(field_card, 'endian_combo'):
                endian_text = field_card.endian_combo.currentText()
                new_endian = "大端(高字节在前)" if endian_text == "大端" else "小端(低字节在前)"
                print(f"[联动] 字段'{field_name}'字节序 -> 校验配置: {new_endian}")
                self.checksum_endianness.blockSignals(True)
                self.checksum_endianness.setCurrentText(new_endian)
                self.checksum_endianness.blockSignals(False)
    
    def remove_field(self, field_card):
        """移除字段"""
        # 断开所有信号连接，避免内存泄漏
        try:
            if hasattr(field_card, 'endian_combo'):
                field_card.endian_combo.currentTextChanged.disconnect()
            if hasattr(field_card, 'start_spin'):
                field_card.start_spin.valueChanged.disconnect()
            if hasattr(field_card, 'length_spin'):
                field_card.length_spin.valueChanged.disconnect()
        except (RuntimeError, TypeError):
            pass  # 信号可能已断开或未连接
        
        self.fields_layout.removeWidget(field_card)
        field_card.deleteLater()
    
    def lock_all_fields(self):
        """锁定所有字段"""
        for i in range(self.fields_layout.count()):
            field_card = self.fields_layout.itemAt(i).widget()
            if field_card and hasattr(field_card, 'lock_state'):
                # 直接检查并设置锁定状态（lock_state现在是列表）
                if not field_card.lock_state[0]:
                    # 调用toggle_lock来锁定
                    if hasattr(field_card, 'toggle_lock'):
                        field_card.toggle_lock()
    
    def unlock_all_fields(self):
        """解锁所有字段"""
        for i in range(self.fields_layout.count()):
            field_card = self.fields_layout.itemAt(i).widget()
            if field_card and hasattr(field_card, 'lock_state'):
                # 直接检查并设置解锁状态（lock_state现在是列表）
                if field_card.lock_state[0]:
                    # 调用toggle_lock来解锁
                    if hasattr(field_card, 'toggle_lock'):
                        field_card.toggle_lock()
    
    def load_protocol(self):
        """加载协议"""
        from PySide6.QtWidgets import QFileDialog
        from core.protocol_manager import ProtocolManager
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择协议文件",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                protocol = ProtocolManager.load_protocol(file_path)
                if protocol:
                    self.load_protocol_data(protocol)
                    self.protocol_loaded.emit(protocol)
                    InfoBar.success(
                        title="成功",
                        content=f"协议加载成功: {protocol.protocol_name}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title="错误",
                        content="协议加载失败，文件格式可能不正确",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"加载失败: {str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def validate_checksum_field_consistency(self, fields, checksum_endian):
        """验证校验码字段与校验配置的字节序一致性
        
        Args:
            fields: 字段列表
            checksum_endian: 校验配置中的字节序
            
        Returns:
            tuple: (是否有冲突, 字段名, 字段字节序)
        """
        # 获取手动指定的关联字段名
        link_field_name = ""
        if hasattr(self, 'checksum_link_field'):
            link_field_name = self.checksum_link_field.text().strip()
        
        # 校验码相关关键字
        checksum_keywords = ['crc', '校验', 'checksum', 'check', 'xor', 'lrc', 'bcc']
        
        # 获取校验配置的长度
        checksum_len = self.checksum_length.value() if hasattr(self, 'checksum_length') else 1
        
        for idx, field_card in enumerate(fields):
            # 跳过 None 或无效的 widget
            if field_card is None:
                continue
            if not hasattr(field_card, 'name_edit') or not hasattr(field_card, 'endian_combo') or not hasattr(field_card, 'length_spin'):
                continue
            
            field_name = field_card.name_edit.text()
            field_name_lower = field_name.lower()
            field_endian_text = field_card.endian_combo.currentText()
            field_endian = Endianness.BIG if field_endian_text == "大端" else Endianness.LITTLE
            field_length = field_card.length_spin.value()
            
            # 只检查长度大于1字节的字段（单字节字段不受字节序影响）
            if field_length <= 1:
                continue
            
            # 判断是否是关联的校验码字段
            is_linked = False
            if link_field_name:
                # 如果指定了关联字段名，精确匹配
                is_linked = field_name == link_field_name
            else:
                # 否则通过关键字匹配且长度一致
                is_linked = any(keyword in field_name_lower for keyword in checksum_keywords) and field_length == checksum_len
            
            if is_linked:
                # 发现关联的校验码字段，检查字节序是否一致
                if field_endian != checksum_endian:
                    return True, field_name, field_endian_text
                break  # 只检查一个匹配的字段
        
        return False, None, None
    
    def save_protocol(self):
        """保存协议"""
        if not self.name_edit.text():
            InfoBar.warning(
                title="警告",
                content="请输入协议名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        try:
            from core.protocol_manager import ProtocolManager
            
            # 收集字段信息
            fields = []
            for i in range(self.fields_layout.count()):
                field_card = self.fields_layout.itemAt(i).widget()
                if not field_card or not hasattr(field_card, 'name_edit'):
                    continue
                
                # 获取字段信息
                name = field_card.name_edit.text()
                type_text = field_card.type_combo.currentText()
                endian_text = field_card.endian_combo.currentText()
                start = field_card.start_spin.value()
                length = field_card.length_spin.value()
                
                # 类型映射
                type_map = {
                    "整数": FieldType.UINT8 if length == 1 else (FieldType.UINT16 if length == 2 else FieldType.UINT32),
                    "浮点数": FieldType.FLOAT if length == 4 else FieldType.DOUBLE,
                    "字符串": FieldType.STRING,
                    "十六进制": FieldType.BYTES
                }
                field_type = type_map.get(type_text, FieldType.UINT8)
                
                # 字节序映射
                endianness = Endianness.BIG if endian_text == "大端" else Endianness.LITTLE
                
                # 获取锁定状态
                locked = field_card.lock_state[0] if hasattr(field_card, 'lock_state') else False
                
                # 创建字段定义
                field_def = FieldDefinition(
                    name=name,
                    byte_count=length,
                    field_type=field_type,
                    order=start,
                    endianness=endianness,
                    locked=locked
                )
                fields.append(field_def)
            
            # 收集校验信息
            checksum_config = None
            if self.checksum_enable.isChecked():
                # 校验类型映射
                checksum_type_map = {
                    "无校验": ChecksumType.NONE,
                    "累加和": ChecksumType.SUM,
                    "累加和16位": ChecksumType.SUM16,
                    "异或校验": ChecksumType.XOR,
                    "异或校验16位": ChecksumType.XOR16,
                    "CRC-8": ChecksumType.CRC8,
                    "CRC-8/ITU": ChecksumType.CRC8_ITU,
                    "CRC-8/ROHC": ChecksumType.CRC8_ROHC,
                    "CRC-8/MAXIM": ChecksumType.CRC8_MAXIM,
                    "CRC-16/MODBUS": ChecksumType.CRC16_MODBUS,
                    "CRC-16/IBM": ChecksumType.CRC16_IBM,
                    "CRC-16/CCITT": ChecksumType.CRC16_CCITT,
                    "CRC-16/CCITT-FALSE": ChecksumType.CRC16_CCITT_FALSE,
                    "CRC-16/XMODEM": ChecksumType.CRC16_XMODEM,
                    "CRC-16/X25": ChecksumType.CRC16_X25,
                    "CRC-16/DNP": ChecksumType.CRC16_DNP,
                    "CRC-16/USB": ChecksumType.CRC16_USB,
                    "CRC-16/MAXIM": ChecksumType.CRC16_MAXIM,
                    "CRC-32": ChecksumType.CRC32,
                    "CRC-32/MPEG-2": ChecksumType.CRC32_MPEG2,
                    "CRC-32/POSIX": ChecksumType.CRC32_POSIX,
                    "LRC": ChecksumType.LRC,
                    "BCC": ChecksumType.BCC,
                    "Fletcher-16": ChecksumType.FLETCHER16,
                    "Fletcher-32": ChecksumType.FLETCHER32,
                    "Adler-32": ChecksumType.ADLER32,
                    # 兼容旧版本
                    "CRC16": ChecksumType.CRC16_MODBUS,
                    "CRC32": ChecksumType.CRC32,
                    "异或": ChecksumType.XOR
                }
                checksum_type = checksum_type_map.get(self.checksum_type.currentText(), ChecksumType.SUM)
                
                # 校验位置映射
                from models.protocol import ChecksumPosition
                position_map = {
                    "帧尾前": ChecksumPosition.BEFORE_TAIL,
                    "帧尾后": ChecksumPosition.AFTER_TAIL
                }
                position = position_map.get(self.checksum_position.currentText(), ChecksumPosition.BEFORE_TAIL)
                
                # 获取校验配置详细信息
                checksum_pos = self.checksum_byte_position.value() if hasattr(self, 'checksum_byte_position') else None
                checksum_len = self.checksum_length.value() if hasattr(self, 'checksum_length') else 1
                checksum_start_val = self.checksum_start.value() if hasattr(self, 'checksum_start') else None
                checksum_end_val = self.checksum_end.value() if hasattr(self, 'checksum_end') else None
                
                # 获取校验码字节序
                checksum_endian = Endianness.LITTLE  # 默认小端
                if hasattr(self, 'checksum_endianness'):
                    endian_text = self.checksum_endianness.currentText()
                    checksum_endian = Endianness.BIG if "大端" in endian_text else Endianness.LITTLE
                
                # 如果checksum_pos为0则设为None（表示使用相对位置）
                if checksum_pos == 0:
                    checksum_pos = None
                
                checksum_config = ChecksumConfig(
                    checksum_type=checksum_type,
                    position=position,
                    checksum_position=checksum_pos,
                    checksum_length=checksum_len,
                    checksum_start=checksum_start_val,
                    checksum_end=checksum_end_val,
                    checksum_endianness=checksum_endian
                )
                
                # 验证字段定义与校验配置的字节序一致性
                field_widgets = [self.fields_layout.itemAt(i).widget() 
                                for i in range(self.fields_layout.count())]
                has_conflict, conflict_field, conflict_endian = self.validate_checksum_field_consistency(
                    field_widgets, checksum_endian
                )
                
                if has_conflict:
                    checksum_endian_text = "大端" if checksum_endian == Endianness.BIG else "小端"
                    # 显示警告，询问用户是否继续
                    from qfluentwidgets import MessageBox
                    msg_box = MessageBox(
                        "字节序不一致警告",
                        f"检测到字段'{conflict_field}'的字节序为'{conflict_endian}'，"
                        f"但校验配置中的字节序为'{checksum_endian_text}'。\n\n"
                        f"这可能导致校验计算不正确。建议统一两处的字节序设置。\n\n"
                        f"是否仍要继续保存？",
                        self
                    )
                    msg_box.yesButton.setText("继续保存")
                    msg_box.cancelButton.setText("返回修改")
                    if msg_box.exec() != 1:  # 用户选择返回修改
                        return
            
            # 创建协议配置
            protocol = ProtocolConfig(
                protocol_name=self.name_edit.text(),
                description=self.desc_edit.toPlainText(),
                frame_header=self.header_edit.text() if self.header_edit.text() else None,
                frame_tail=self.footer_edit.text() if self.footer_edit.text() else None,
                fields=fields,
                checksum_config=checksum_config
            )
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存协议文件",
                f"{protocol.protocol_name}.json",
                "JSON Files (*.json)"
            )
            
            if file_path:
                # 保存协议
                if ProtocolManager.save_protocol(protocol, file_path):
                    # 设置文件路径（用于历史记录）
                    protocol.file_path = os.path.abspath(file_path)
                    self.protocol_saved.emit(protocol)
                    InfoBar.success(
                        title="成功",
                        content=f"协议已保存到: {file_path}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title="错误",
                        content="协议保存失败",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"保存失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            import traceback
            traceback.print_exc()
    
    def apply_protocol(self):
        """应用当前协议配置（不保存文件，直接使配置生效）"""
        if not self.name_edit.text():
            InfoBar.warning(
                title="警告",
                content="请输入协议名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        try:
            from core.protocol_manager import ProtocolManager
            
            # 收集字段信息（与save_protocol相同的逻辑）
            fields = []
            for i in range(self.fields_layout.count()):
                field_card = self.fields_layout.itemAt(i).widget()
                if not field_card or not hasattr(field_card, 'name_edit'):
                    continue
                
                # 获取字段信息
                name = field_card.name_edit.text()
                type_text = field_card.type_combo.currentText()
                endian_text = field_card.endian_combo.currentText()
                start = field_card.start_spin.value()
                length = field_card.length_spin.value()
                
                # 类型映射
                type_map = {
                    "整数": FieldType.UINT8 if length == 1 else (FieldType.UINT16 if length == 2 else FieldType.UINT32),
                    "浮点数": FieldType.FLOAT if length == 4 else FieldType.DOUBLE,
                    "字符串": FieldType.STRING,
                    "十六进制": FieldType.BYTES
                }
                field_type = type_map.get(type_text, FieldType.UINT8)
                
                # 字节序映射
                endianness = Endianness.BIG if endian_text == "大端" else Endianness.LITTLE
                
                # 获取锁定状态
                locked = field_card.lock_state[0] if hasattr(field_card, 'lock_state') else False
                
                # 创建字段定义
                field_def = FieldDefinition(
                    name=name,
                    byte_count=length,
                    field_type=field_type,
                    order=start,
                    endianness=endianness,
                    locked=locked
                )
                fields.append(field_def)
            
            # 收集校验信息
            checksum_config = None
            if self.checksum_enable.isChecked():
                # 校验类型映射
                checksum_type_map = {
                    "无校验": ChecksumType.NONE,
                    "累加和": ChecksumType.SUM,
                    "累加和16位": ChecksumType.SUM16,
                    "异或校验": ChecksumType.XOR,
                    "异或校验16位": ChecksumType.XOR16,
                    "CRC-8": ChecksumType.CRC8,
                    "CRC-8/ITU": ChecksumType.CRC8_ITU,
                    "CRC-8/ROHC": ChecksumType.CRC8_ROHC,
                    "CRC-8/MAXIM": ChecksumType.CRC8_MAXIM,
                    "CRC-16/MODBUS": ChecksumType.CRC16_MODBUS,
                    "CRC-16/IBM": ChecksumType.CRC16_IBM,
                    "CRC-16/CCITT": ChecksumType.CRC16_CCITT,
                    "CRC-16/CCITT-FALSE": ChecksumType.CRC16_CCITT_FALSE,
                    "CRC-16/XMODEM": ChecksumType.CRC16_XMODEM,
                    "CRC-16/X25": ChecksumType.CRC16_X25,
                    "CRC-16/DNP": ChecksumType.CRC16_DNP,
                    "CRC-16/USB": ChecksumType.CRC16_USB,
                    "CRC-16/MAXIM": ChecksumType.CRC16_MAXIM,
                    "CRC-32": ChecksumType.CRC32,
                    "CRC-32/MPEG-2": ChecksumType.CRC32_MPEG2,
                    "CRC-32/POSIX": ChecksumType.CRC32_POSIX,
                    "LRC": ChecksumType.LRC,
                    "BCC": ChecksumType.BCC,
                    "Fletcher-16": ChecksumType.FLETCHER16,
                    "Fletcher-32": ChecksumType.FLETCHER32,
                    "Adler-32": ChecksumType.ADLER32,
                    # 兼容旧版本
                    "CRC16": ChecksumType.CRC16_MODBUS,
                    "CRC32": ChecksumType.CRC32,
                    "异或": ChecksumType.XOR
                }
                checksum_type = checksum_type_map.get(self.checksum_type.currentText(), ChecksumType.SUM)
                
                # 校验位置映射
                from models.protocol import ChecksumPosition
                position_map = {
                    "帧尾前": ChecksumPosition.BEFORE_TAIL,
                    "帧尾后": ChecksumPosition.AFTER_TAIL
                }
                position = position_map.get(self.checksum_position.currentText(), ChecksumPosition.BEFORE_TAIL)
                
                # 获取校验配置详细信息
                checksum_pos = self.checksum_byte_position.value() if hasattr(self, 'checksum_byte_position') else None
                checksum_len = self.checksum_length.value() if hasattr(self, 'checksum_length') else 1
                checksum_start_val = self.checksum_start.value() if hasattr(self, 'checksum_start') else None
                checksum_end_val = self.checksum_end.value() if hasattr(self, 'checksum_end') else None
                
                # 获取校验码字节序
                checksum_endian = Endianness.LITTLE  # 默认小端
                if hasattr(self, 'checksum_endianness'):
                    endian_text = self.checksum_endianness.currentText()
                    checksum_endian = Endianness.BIG if "大端" in endian_text else Endianness.LITTLE
                
                # 如果checksum_pos为0则设为None（表示使用相对位置）
                if checksum_pos == 0:
                    checksum_pos = None
                
                checksum_config = ChecksumConfig(
                    checksum_type=checksum_type,
                    position=position,
                    checksum_position=checksum_pos,
                    checksum_length=checksum_len,
                    checksum_start=checksum_start_val,
                    checksum_end=checksum_end_val,
                    checksum_endianness=checksum_endian
                )
                
                # 验证字段定义与校验配置的字节序一致性
                field_widgets = [self.fields_layout.itemAt(i).widget() 
                                for i in range(self.fields_layout.count())]
                has_conflict, conflict_field, conflict_endian = self.validate_checksum_field_consistency(
                    field_widgets, checksum_endian
                )
                
                if has_conflict:
                    checksum_endian_text = "大端" if checksum_endian == Endianness.BIG else "小端"
                    # 显示警告，询问用户是否继续
                    from qfluentwidgets import MessageBox
                    msg_box = MessageBox(
                        "字节序不一致警告",
                        f"检测到字段'{conflict_field}'的字节序为'{conflict_endian}'，"
                        f"但校验配置中的字节序为'{checksum_endian_text}'。\n\n"
                        f"这可能导致校验计算不正确。建议统一两处的字节序设置。\n\n"
                        f"是否仍要继续应用？",
                        self
                    )
                    msg_box.yesButton.setText("继续应用")
                    msg_box.cancelButton.setText("返回修改")
                    if msg_box.exec() != 1:  # 用户选择返回修改
                        return
            
            # 创建协议配置
            protocol = ProtocolConfig(
                protocol_name=self.name_edit.text(),
                description=self.desc_edit.toPlainText(),
                frame_header=self.header_edit.text() if self.header_edit.text() else None,
                frame_tail=self.footer_edit.text() if self.footer_edit.text() else None,
                fields=fields,
                checksum_config=checksum_config
            )
            
            # 发送信号，使协议生效
            self.protocol_loaded.emit(protocol)
            
            InfoBar.success(
                title="成功",
                content=f"协议 '{protocol.protocol_name}' 已应用，可以开始分析数据",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"应用失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            import traceback
            traceback.print_exc()
    
    def clear_form(self):
        """清空表单"""
        self.name_edit.clear()
        self.desc_edit.clear()
        self.header_edit.clear()
        self.footer_edit.clear()
        
        # 清空所有字段（先断开信号再删除）
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            widget = item.widget()
            if widget:
                # 断开信号连接，避免内存泄漏
                try:
                    if hasattr(widget, 'endian_combo'):
                        widget.endian_combo.currentTextChanged.disconnect()
                    if hasattr(widget, 'start_spin'):
                        widget.start_spin.valueChanged.disconnect()
                    if hasattr(widget, 'length_spin'):
                        widget.length_spin.valueChanged.disconnect()
                except (RuntimeError, TypeError):
                    pass  # 信号可能已断开或未连接
                widget.deleteLater()
        
        # 重置校验配置
        self.checksum_enable.setChecked(False)
        self.checksum_type.setCurrentIndex(0)
        if hasattr(self, 'checksum_byte_position'):
            self.checksum_byte_position.setValue(0)
        if hasattr(self, 'checksum_length'):
            self.checksum_length.setValue(1)
        if hasattr(self, 'checksum_start'):
            self.checksum_start.setValue(0)
        if hasattr(self, 'checksum_end'):
            self.checksum_end.setValue(0)
        if hasattr(self, 'checksum_endianness'):
            self.checksum_endianness.setCurrentIndex(0)
        if hasattr(self, 'checksum_position'):
            self.checksum_position.setCurrentIndex(0)
        # 清空关联字段名
        if hasattr(self, 'checksum_link_field'):
            self.checksum_link_field.clear()
    
    def load_protocol_data(self, protocol: ProtocolConfig):
        """加载协议数据到界面"""
        try:
            # 清空现有内容
            self.clear_form()
            
            # 设置基本信息
            if hasattr(protocol, 'protocol_name'):
                self.name_edit.setText(protocol.protocol_name)
            if hasattr(protocol, 'description') and protocol.description:
                self.desc_edit.setPlainText(protocol.description)
            
            # 设置帧头帧尾
            if hasattr(protocol, 'frame_header') and protocol.frame_header:
                self.header_edit.setText(protocol.frame_header)
            if hasattr(protocol, 'frame_tail') and protocol.frame_tail:
                self.footer_edit.setText(protocol.frame_tail)
            
            # 【重要】先设置校验配置，再设置字段
            # 这样字段的联动信号触发时，校验配置已经有正确的值
            self._load_checksum_config(protocol)
            
            # 设置字段
            self._load_fields(protocol)
                
        except Exception as e:
            print(f"加载协议数据时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_checksum_config(self, protocol: ProtocolConfig):
        """加载校验配置到界面"""
        if hasattr(protocol, 'checksum_config') and protocol.checksum_config:
            checksum = protocol.checksum_config
            from models.protocol import ChecksumType, ChecksumPosition
            
            # 阻止信号触发，避免加载时的不必要联动
            self.checksum_endianness.blockSignals(True)
            self.checksum_byte_position.blockSignals(True)
            self.checksum_length.blockSignals(True)
            
            try:
                # 根据checksum_type判断是否启用校验
                is_enabled = checksum.checksum_type != ChecksumType.NONE
                self.checksum_enable.setChecked(is_enabled)
                
                if is_enabled:
                    # 设置校验类型
                    type_map = {
                        ChecksumType.NONE: "无校验",
                        ChecksumType.SUM: "累加和",
                        ChecksumType.SUM16: "累加和16位",
                        ChecksumType.XOR: "异或校验",
                        ChecksumType.XOR16: "异或校验16位",
                        ChecksumType.CRC8: "CRC-8",
                        ChecksumType.CRC8_ITU: "CRC-8/ITU",
                        ChecksumType.CRC8_ROHC: "CRC-8/ROHC",
                        ChecksumType.CRC8_MAXIM: "CRC-8/MAXIM",
                        ChecksumType.CRC16: "CRC-16/MODBUS",
                        ChecksumType.CRC16_IBM: "CRC-16/IBM",
                        ChecksumType.CRC16_MODBUS: "CRC-16/MODBUS",
                        ChecksumType.CRC16_CCITT: "CRC-16/CCITT",
                        ChecksumType.CRC16_CCITT_FALSE: "CRC-16/CCITT-FALSE",
                        ChecksumType.CRC16_XMODEM: "CRC-16/XMODEM",
                        ChecksumType.CRC16_X25: "CRC-16/X25",
                        ChecksumType.CRC16_DNP: "CRC-16/DNP",
                        ChecksumType.CRC16_USB: "CRC-16/USB",
                        ChecksumType.CRC16_MAXIM: "CRC-16/MAXIM",
                        ChecksumType.CRC32: "CRC-32",
                        ChecksumType.CRC32_MPEG2: "CRC-32/MPEG-2",
                        ChecksumType.CRC32_POSIX: "CRC-32/POSIX",
                        ChecksumType.LRC: "LRC",
                        ChecksumType.BCC: "BCC",
                        ChecksumType.FLETCHER16: "Fletcher-16",
                        ChecksumType.FLETCHER32: "Fletcher-32",
                        ChecksumType.ADLER32: "Adler-32",
                    }
                    type_text = type_map.get(checksum.checksum_type, "累加和")
                    self.checksum_type.setCurrentText(type_text)
                    
                    # 设置校验位置
                    pos_map = {
                        ChecksumPosition.BEFORE_TAIL: "帧尾前",
                        ChecksumPosition.AFTER_TAIL: "帧尾后"
                    }
                    pos_text = pos_map.get(checksum.position, "帧尾前")
                    self.checksum_position.setCurrentText(pos_text)
                    
                    # 设置校验详细配置
                    if hasattr(checksum, 'checksum_position') and checksum.checksum_position is not None:
                        self.checksum_byte_position.setValue(checksum.checksum_position)
                    
                    if hasattr(checksum, 'checksum_length'):
                        self.checksum_length.setValue(checksum.checksum_length)
                    
                    if hasattr(checksum, 'checksum_start') and checksum.checksum_start is not None:
                        self.checksum_start.setValue(checksum.checksum_start)
                    
                    if hasattr(checksum, 'checksum_end') and checksum.checksum_end is not None:
                        self.checksum_end.setValue(checksum.checksum_end)
                    
                    # 设置校验码字节序
                    if hasattr(checksum, 'checksum_endianness'):
                        endian_text = "大端(高字节在前)" if checksum.checksum_endianness == Endianness.BIG else "小端(低字节在前)"
                        self.checksum_endianness.setCurrentText(endian_text)
            finally:
                # 恢复信号
                self.checksum_endianness.blockSignals(False)
                self.checksum_byte_position.blockSignals(False)
                self.checksum_length.blockSignals(False)
    
    def _load_fields(self, protocol: ProtocolConfig):
        """加载字段定义到界面"""
        if not hasattr(protocol, 'fields') or not protocol.fields:
            return
            
        for field_config in protocol.fields:
            # 创建字段卡片
            field_card = CardWidget()
            field_layout = QHBoxLayout(field_card)
            field_layout.setSpacing(15)
            field_layout.setContentsMargins(15, 10, 15, 10)
            
            # 字段名称部分
            name_label = BodyLabel("字段名:")
            name_label.setMinimumWidth(80)
            field_layout.addWidget(name_label)
            
            name_edit = LineEdit()
            name_edit.setText(field_config.name)
            name_edit.setMinimumWidth(200)
            field_layout.addWidget(name_edit, 2)
            
            # 类型部分
            type_label = BodyLabel("类型:")
            type_label.setMinimumWidth(60)
            field_layout.addWidget(type_label)
            
            type_combo = ComboBox()
            type_combo.addItems(["整数", "浮点数", "字符串", "十六进制"])
            # 设置当前类型
            type_map = {
                "int": "整数",
                "uint": "整数",
                "float": "浮点数",
                "string": "字符串",
                "hex": "十六进制",
                "bytes": "十六进制"
            }
            field_type_str = field_config.field_type.value if hasattr(field_config.field_type, 'value') else str(field_config.field_type)
            type_text = type_map.get(field_type_str, "整数")
            type_combo.setCurrentText(type_text)
            type_combo.setMinimumWidth(150)
            field_layout.addWidget(type_combo, 1)
            
            # 字节序部分
            endian_label = BodyLabel("字节序:")
            endian_label.setFixedWidth(70)
            endian_combo = ComboBox()
            endian_combo.addItems(["大端", "小端"])
            # 设置当前字节序
            if hasattr(field_config, 'endianness'):
                endian_text = "大端" if field_config.endianness == Endianness.BIG else "小端"
                endian_combo.setCurrentText(endian_text)
            endian_combo.setMinimumWidth(100)
            field_layout.addWidget(endian_label)
            field_layout.addWidget(endian_combo, 1)
            
            # 起始位置部分（这里只显示顺序，实际位置在解析时计算）
            start_label = BodyLabel("起始:")
            start_label.setMinimumWidth(60)
            field_layout.addWidget(start_label)
            
            start_spin = SpinBox()
            start_spin.setRange(0, 1000)
            start_spin.setValue(field_config.order)
            start_spin.setMinimumWidth(100)
            field_layout.addWidget(start_spin, 1)
            
            # 长度部分（字节数）
            length_label = BodyLabel("长度:")
            length_label.setMinimumWidth(60)
            field_layout.addWidget(length_label)
            
            length_spin = SpinBox()
            length_spin.setRange(1, 100)
            length_spin.setValue(field_config.byte_count)
            length_spin.setMinimumWidth(100)
            field_layout.addWidget(length_spin, 1)
            
            # 根据类型和长度决定是否启用字节序选择
            def update_endian_state():
                length = length_spin.value()
                # 所有类型在长度>1时都可以选择字节序
                if length > 1:
                    endian_combo.setEnabled(True)
                    endian_label.setStyleSheet("")
                else:
                    endian_combo.setEnabled(True)
                    endian_label.setStyleSheet("color: #999999;")
            
            type_combo.currentTextChanged.connect(update_endian_state)
            length_spin.valueChanged.connect(update_endian_state)
            update_endian_state()  # 初始化状态
            
            # 锁定按钮
            lock_btn = PushButton("🔓 解锁")
            lock_btn.setFixedWidth(80)
            
            # 锁定状态存储（从配置中恢复，使用列表避免闭包问题）
            initial_locked = field_config.locked if hasattr(field_config, 'locked') else False
            lock_state = [initial_locked]
            
            # 使用默认参数捕获当前控件引用，避免闭包问题
            def make_toggle_lock_loaded(btn, state, n_edit, t_combo, s_spin, l_spin, e_combo, e_label, update_fn):
                def toggle():
                    state[0] = not state[0]
                    if state[0]:
                        btn.setText("🔒 已锁定")
                        n_edit.setEnabled(False)
                        t_combo.setEnabled(False)
                        s_spin.setEnabled(False)
                        l_spin.setEnabled(False)
                        e_combo.setEnabled(False)
                    else:
                        btn.setText("🔓 解锁")
                        n_edit.setEnabled(True)
                        t_combo.setEnabled(True)
                        s_spin.setEnabled(True)
                        l_spin.setEnabled(True)
                        # 解锁时根据当前长度判断是否启用字节序
                        length = l_spin.value()
                        if length > 1:
                            e_combo.setEnabled(True)
                            e_label.setStyleSheet("")
                        else:
                            e_combo.setEnabled(True)
                            e_label.setStyleSheet("color: #999999;")
                return toggle
            
            toggle_lock = make_toggle_lock_loaded(lock_btn, lock_state, name_edit, type_combo,
                                                  start_spin, length_spin, endian_combo, endian_label, update_endian_state)
            lock_btn.clicked.connect(toggle_lock)
            field_layout.addWidget(lock_btn)
            
            # 如果字段已锁定，应用锁定状态
            if initial_locked:
                lock_btn.setText("🔒 已锁定")
                name_edit.setEnabled(False)
                type_combo.setEnabled(False)
                start_spin.setEnabled(False)
                length_spin.setEnabled(False)
                endian_combo.setEnabled(False)
            
            # 删除按钮
            del_btn = PushButton(FIF.DELETE, "删除")
            del_btn.clicked.connect(lambda checked, card=field_card: self.remove_field(card))
            field_layout.addWidget(del_btn)
            
            # 保存控件引用
            field_card.name_edit = name_edit
            field_card.type_combo = type_combo
            field_card.endian_combo = endian_combo
            field_card.start_spin = start_spin
            field_card.length_spin = length_spin
            field_card.lock_btn = lock_btn
            field_card.lock_state = lock_state
            field_card.is_locked = lambda s=lock_state: s[0]
            field_card.toggle_lock = toggle_lock
            
            # 连接字段字节序变化信号，同步到校验配置（如果位置匹配）
            endian_combo.currentTextChanged.connect(
                lambda text, fc=field_card: self._on_field_endianness_changed(fc, text)
            )
            # 当起始位置或长度变化时，检查是否需要同步
            start_spin.valueChanged.connect(
                lambda val, fc=field_card: self._check_field_checksum_sync(fc)
            )
            length_spin.valueChanged.connect(
                lambda val, fc=field_card: self._check_field_checksum_sync(fc)
            )
            
            self.fields_layout.addWidget(field_card)
    
    def show_protocol_history(self):
        """显示协议历史记录"""
        if not self.protocol_history:
            InfoBar.warning(
                title="未初始化",
                content="协议历史功能未初始化",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        # 创建并显示协议历史对话框
        dialog = ProtocolHistoryDialog(self.protocol_history, self)
        dialog.protocol_selected.connect(self.load_protocol_from_path)
        dialog.exec()
    
    def load_protocol_from_path(self, file_path: str):
        """从指定路径加载协议"""
        try:
            from core import ProtocolManager
            protocol = ProtocolManager.load_protocol(file_path)
            self.load_protocol_data(protocol)
            self.protocol_loaded.emit(protocol)
            
            InfoBar.success(
                title="成功",
                content=f"已加载协议：{protocol.protocol_name}",
                parent=self,
                position=InfoBarPosition.TOP
            )
        except Exception as e:
            InfoBar.error(
                title="加载失败",
                content=f"加载协议失败：{str(e)}",
                parent=self,
                position=InfoBarPosition.TOP
            )
