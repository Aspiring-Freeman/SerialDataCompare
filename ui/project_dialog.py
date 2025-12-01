# This Python file uses the following encoding: utf-8
"""
项目对话框 - 新建/编辑项目
"""
import os
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
                                QLabel, QFrame, QTableWidgetItem, QHeaderView,
                                QAbstractItemView)
from PySide6.QtCore import Signal, Qt

from qfluentwidgets import (LineEdit, TextEdit, PushButton, ToolButton,
                           TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
                           FluentIcon as FIF, InfoBar, InfoBarPosition,
                           CardWidget, MessageBoxBase, PrimaryPushButton,
                           isDarkTheme, ListWidget, TableWidget, RadioButton)

from core.project_manager import ProjectManager, Project


class ProjectDialog(MessageBoxBase):
    """项目创建/编辑对话框"""
    
    def __init__(self, parent=None, project_manager: ProjectManager = None, 
                 edit_project_id: str = None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.edit_project_id = edit_project_id
        self.edit_project = None
        
        if edit_project_id and project_manager:
            self.edit_project = project_manager.get_project(edit_project_id)
        
        self.init_ui()
        
        # 如果是编辑模式，加载现有数据
        if self.edit_project:
            self.load_project_data()
    
    def init_ui(self):
        """初始化UI"""
        # 设置对话框标题
        if self.edit_project:
            title = "编辑项目"
        else:
            title = "新建项目"
        
        self.titleLabel = SubtitleLabel(title)
        self.viewLayout.addWidget(self.titleLabel)
        
        # 项目名称
        name_layout = QHBoxLayout()
        name_label = BodyLabel("项目名称:")
        name_label.setFixedWidth(80)
        name_layout.addWidget(name_label)
        
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("输入项目名称")
        self.name_edit.setClearButtonEnabled(True)
        name_layout.addWidget(self.name_edit)
        self.viewLayout.addLayout(name_layout)
        
        # 文件夹路径
        folder_layout = QHBoxLayout()
        folder_label = BodyLabel("协议文件夹:")
        folder_label.setFixedWidth(80)
        folder_layout.addWidget(folder_label)
        
        self.folder_edit = LineEdit()
        self.folder_edit.setPlaceholderText("选择包含协议文件的文件夹")
        self.folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.folder_edit)
        
        self.browse_btn = ToolButton(FIF.FOLDER)
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_btn)
        self.viewLayout.addLayout(folder_layout)
        
        # 项目描述
        desc_layout = QVBoxLayout()
        desc_label = BodyLabel("项目描述 (可选):")
        desc_layout.addWidget(desc_label)
        
        self.desc_edit = TextEdit()
        self.desc_edit.setPlaceholderText("输入项目描述...")
        self.desc_edit.setMaximumHeight(80)
        desc_layout.addWidget(self.desc_edit)
        self.viewLayout.addLayout(desc_layout)
        
        # 协议预览
        preview_layout = QVBoxLayout()
        self.preview_label = BodyLabel("检测到的协议文件:")
        preview_layout.addWidget(self.preview_label)
        
        self.preview_list = ListWidget()
        self.preview_list.setMaximumHeight(120)
        preview_layout.addWidget(self.preview_list)
        
        self.preview_hint = CaptionLabel("选择文件夹后将自动扫描协议文件")
        preview_layout.addWidget(self.preview_hint)
        self.viewLayout.addLayout(preview_layout)
        
        # 设置按钮
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")
        
        # 设置最小宽度
        self.widget.setMinimumWidth(500)
        
        # 连接信号
        self.folder_edit.textChanged.connect(self.scan_protocols)
    
    def browse_folder(self):
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择协议文件夹",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder:
            self.folder_edit.setText(folder)
            
            # 如果项目名称为空，自动使用文件夹名
            if not self.name_edit.text().strip():
                self.name_edit.setText(os.path.basename(folder))
    
    def scan_protocols(self):
        """扫描协议文件"""
        self.preview_list.clear()
        
        folder_path = self.folder_edit.text().strip()
        if not folder_path or not os.path.exists(folder_path):
            self.preview_hint.setText("选择文件夹后将自动扫描协议文件")
            return
        
        # 扫描 JSON 文件
        protocols = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.json'):
                    file_path = os.path.join(root, file)
                    # 尝试读取验证是否为协议文件
                    try:
                        import json
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        # 简单验证是否有协议必需字段
                        if 'fields' in data or 'name' in data:
                            rel_path = os.path.relpath(file_path, folder_path)
                            name = data.get('name', file)
                            protocols.append(f"📄 {name} ({rel_path})")
                    except:
                        pass
        
        if protocols:
            for p in protocols:
                self.preview_list.addItem(p)
            self.preview_hint.setText(f"共找到 {len(protocols)} 个协议文件")
        else:
            self.preview_hint.setText("未找到协议文件 (*.json)")
    
    def load_project_data(self):
        """加载现有项目数据"""
        if self.edit_project:
            self.name_edit.setText(self.edit_project.name)
            self.folder_edit.setText(self.edit_project.folder_path)
            self.desc_edit.setPlainText(self.edit_project.description)
    
    def validate(self) -> bool:
        """验证输入"""
        name = self.name_edit.text().strip()
        folder = self.folder_edit.text().strip()
        
        if not name:
            InfoBar.error(
                title="验证失败",
                content="请输入项目名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return False
        
        if not folder:
            InfoBar.error(
                title="验证失败",
                content="请选择协议文件夹",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return False
        
        if not os.path.exists(folder):
            InfoBar.error(
                title="验证失败",
                content="选择的文件夹不存在",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return False
        
        return True
    
    def get_project_data(self) -> dict:
        """获取项目数据"""
        return {
            'name': self.name_edit.text().strip(),
            'folder_path': self.folder_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip()
        }


class DeleteProjectDialog(MessageBoxBase):
    """删除项目确认对话框"""
    
    # 删除选项
    DELETE_RECORD_ONLY = 0  # 仅删除记录
    DELETE_WITH_FILES = 1   # 同时删除文件
    
    def __init__(self, parent=None, project_name: str = "", folder_path: str = ""):
        super().__init__(parent)
        self.project_name = project_name
        self.folder_path = folder_path
        self.delete_option = self.DELETE_RECORD_ONLY
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        from qfluentwidgets import RadioButton
        
        self.titleLabel = SubtitleLabel("删除项目")
        self.viewLayout.addWidget(self.titleLabel)
        
        # 警告图标和消息
        msg_layout = QHBoxLayout()
        
        warning_label = BodyLabel("⚠️")
        warning_label.setStyleSheet("font-size: 24px;")
        msg_layout.addWidget(warning_label)
        
        msg = BodyLabel(f"确定要删除项目 \"{self.project_name}\" 吗？")
        msg.setWordWrap(True)
        msg_layout.addWidget(msg, 1)
        
        self.viewLayout.addLayout(msg_layout)
        
        # 删除选项
        option_layout = QVBoxLayout()
        option_label = BodyLabel("请选择删除方式:")
        option_layout.addWidget(option_label)
        
        self.radio_record_only = RadioButton("仅删除记录 (保留实际文件)")
        self.radio_record_only.setChecked(True)
        self.radio_record_only.clicked.connect(lambda: self.set_delete_option(self.DELETE_RECORD_ONLY))
        option_layout.addWidget(self.radio_record_only)
        
        self.radio_with_files = RadioButton("删除记录并删除文件夹内所有文件 ⚠️")
        self.radio_with_files.clicked.connect(lambda: self.set_delete_option(self.DELETE_WITH_FILES))
        option_layout.addWidget(self.radio_with_files)
        
        # 文件夹路径提示
        folder_hint = CaptionLabel(f"文件夹: {self.folder_path}")
        folder_hint.setWordWrap(True)
        option_layout.addWidget(folder_hint)
        
        self.viewLayout.addLayout(option_layout)
        
        # 设置按钮
        self.yesButton.setText("删除")
        self.cancelButton.setText("取消")
        
        # 设置最小宽度
        self.widget.setMinimumWidth(450)
    
    def set_delete_option(self, option: int):
        """设置删除选项"""
        self.delete_option = option
    
    def get_delete_option(self) -> int:
        """获取删除选项"""
        return self.delete_option


class RenameDialog(MessageBoxBase):
    """重命名对话框 - 用于重命名项目、文件夹或协议"""
    
    TYPE_PROJECT = 'project'
    TYPE_FOLDER = 'folder'
    TYPE_PROTOCOL = 'protocol'
    
    def __init__(self, parent=None, item_type: str = TYPE_PROJECT, 
                 current_name: str = "", file_path: str = ""):
        super().__init__(parent)
        self.item_type = item_type
        self.current_name = current_name
        self.file_path = file_path
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 根据类型设置标题
        type_names = {
            self.TYPE_PROJECT: "项目",
            self.TYPE_FOLDER: "文件夹", 
            self.TYPE_PROTOCOL: "协议"
        }
        type_name = type_names.get(self.item_type, "项目")
        
        self.titleLabel = SubtitleLabel(f"重命名{type_name}")
        self.viewLayout.addWidget(self.titleLabel)
        
        # 当前名称
        current_layout = QHBoxLayout()
        current_label = BodyLabel("当前名称:")
        current_label.setFixedWidth(80)
        current_layout.addWidget(current_label)
        
        current_value = BodyLabel(self.current_name)
        current_layout.addWidget(current_value)
        self.viewLayout.addLayout(current_layout)
        
        # 新名称
        new_layout = QHBoxLayout()
        new_label = BodyLabel("新名称:")
        new_label.setFixedWidth(80)
        new_layout.addWidget(new_label)
        
        self.name_edit = LineEdit()
        self.name_edit.setText(self.current_name)
        self.name_edit.setPlaceholderText(f"输入新的{type_name}名称")
        self.name_edit.setClearButtonEnabled(True)
        self.name_edit.selectAll()
        new_layout.addWidget(self.name_edit)
        self.viewLayout.addLayout(new_layout)
        
        # 如果是文件夹或协议，显示路径提示
        if self.item_type in [self.TYPE_FOLDER, self.TYPE_PROTOCOL] and self.file_path:
            hint_label = CaptionLabel(f"路径: {self.file_path}")
            hint_label.setWordWrap(True)
            self.viewLayout.addWidget(hint_label)
            
            if self.item_type == self.TYPE_PROTOCOL:
                warning = CaptionLabel("⚠️ 重命名将修改实际文件名")
                self.viewLayout.addWidget(warning)
            elif self.item_type == self.TYPE_FOLDER:
                warning = CaptionLabel("⚠️ 重命名将修改实际文件夹名")
                self.viewLayout.addWidget(warning)
        
        # 设置按钮
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")
        
        # 设置最小宽度
        self.widget.setMinimumWidth(400)
    
    def validate(self) -> bool:
        """验证输入"""
        new_name = self.name_edit.text().strip()
        
        if not new_name:
            InfoBar.error(
                title="验证失败",
                content="名称不能为空",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return False
        
        # 检查非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            if char in new_name:
                InfoBar.error(
                    title="验证失败",
                    content=f"名称不能包含特殊字符: {' '.join(illegal_chars)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return False
        
        return True
    
    def get_new_name(self) -> str:
        """获取新名称"""
        return self.name_edit.text().strip()


class ProjectHistoryDialog(MessageBoxBase):
    """项目历史对话框 - 显示项目详细信息和历史记录"""
    
    def __init__(self, parent=None, project: Project = None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()
        self._load_project_info()
        
    def _setup_ui(self):
        """设置UI"""
        self.titleLabel = TitleLabel("项目详情")
        self.viewLayout.addWidget(self.titleLabel)
        
        # 项目基本信息卡片
        info_card = CardWidget()
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(16, 16, 16, 16)
        
        info_title = SubtitleLabel("基本信息")
        info_layout.addWidget(info_title)
        
        # 信息表格
        self.info_table = TableWidget()
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["属性", "值"])
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.info_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.info_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.info_table.setMaximumHeight(200)
        info_layout.addWidget(self.info_table)
        
        self.viewLayout.addWidget(info_card)
        
        # 协议列表卡片
        protocol_card = CardWidget()
        protocol_layout = QVBoxLayout(protocol_card)
        protocol_layout.setSpacing(10)
        protocol_layout.setContentsMargins(16, 16, 16, 16)
        
        protocol_title = SubtitleLabel("协议文件列表")
        protocol_layout.addWidget(protocol_title)
        
        self.protocol_table = TableWidget()
        self.protocol_table.setColumnCount(3)
        self.protocol_table.setHorizontalHeaderLabels(["协议名称", "相对路径", "状态"])
        self.protocol_table.verticalHeader().setVisible(False)
        self.protocol_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.protocol_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.protocol_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.protocol_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.protocol_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.protocol_table.setMaximumHeight(250)
        protocol_layout.addWidget(self.protocol_table)
        
        self.viewLayout.addWidget(protocol_card)
        
        # 设置对话框宽度
        self.widget.setMinimumWidth(550)
        
        # 只显示关闭按钮
        self.yesButton.setText("关闭")
        self.cancelButton.hide()
        
    def _load_project_info(self):
        """加载项目信息"""
        if not self.project:
            return
        
        # 基本信息
        info_items = [
            ("项目名称", self.project.name),
            ("项目路径", self.project.folder_path),
            ("创建时间", self._format_datetime(self.project.created_at)),
            ("最后访问", self._format_datetime(self.project.last_accessed)),
            ("协议数量", str(len(self.project.protocols))),
        ]
        
        # 添加描述（如果有）
        if self.project.description:
            info_items.append(("项目描述", self.project.description))
        
        self.info_table.setRowCount(len(info_items))
        for row, (key, value) in enumerate(info_items):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(Qt.ItemIsEnabled)
            value_item = QTableWidgetItem(value)
            value_item.setFlags(Qt.ItemIsEnabled)
            self.info_table.setItem(row, 0, key_item)
            self.info_table.setItem(row, 1, value_item)
        
        # 协议列表
        protocols = self.project.protocols
        self.protocol_table.setRowCount(len(protocols))
        
        for row, protocol in enumerate(protocols):
            # 协议名称
            name_item = QTableWidgetItem(protocol.name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.protocol_table.setItem(row, 0, name_item)
            
            # 相对路径
            rel_path = os.path.relpath(protocol.file_path, self.project.folder_path)
            path_item = QTableWidgetItem(rel_path)
            path_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.protocol_table.setItem(row, 1, path_item)
            
            # 状态
            if os.path.exists(protocol.file_path):
                status = "✓ 存在"
            else:
                status = "✗ 缺失"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.protocol_table.setItem(row, 2, status_item)
    
    def _format_datetime(self, dt_str: str) -> str:
        """格式化日期时间字符串"""
        if not dt_str:
            return "未知"
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt_str


class DeleteProtocolDialog(MessageBoxBase):
    """删除协议确认对话框"""
    
    # 删除选项
    REMOVE_FROM_PROJECT = 0  # 仅从项目中移除（保留文件）
    DELETE_FILE = 1          # 永久删除文件
    
    def __init__(self, parent=None, protocol_name: str = "", protocol_path: str = ""):
        super().__init__(parent)
        self.protocol_name = protocol_name
        self.protocol_path = protocol_path
        self.delete_option = self.REMOVE_FROM_PROJECT
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.titleLabel = SubtitleLabel("删除协议")
        self.viewLayout.addWidget(self.titleLabel)
        
        # 警告图标和消息
        msg_layout = QHBoxLayout()
        
        warning_label = BodyLabel("⚠️")
        warning_label.setStyleSheet("font-size: 24px;")
        msg_layout.addWidget(warning_label)
        
        msg = BodyLabel(f"确定要删除协议 \"{self.protocol_name}\" 吗？")
        msg.setWordWrap(True)
        msg_layout.addWidget(msg, 1)
        
        self.viewLayout.addLayout(msg_layout)
        
        # 删除选项
        option_layout = QVBoxLayout()
        option_label = BodyLabel("请选择删除方式:")
        option_layout.addWidget(option_label)
        
        self.radio_remove_only = RadioButton("仅从项目中移除 (保留文件)")
        self.radio_remove_only.setChecked(True)
        self.radio_remove_only.clicked.connect(lambda: self.set_delete_option(self.REMOVE_FROM_PROJECT))
        option_layout.addWidget(self.radio_remove_only)
        
        self.radio_delete_file = RadioButton("永久删除文件 ⚠️")
        self.radio_delete_file.clicked.connect(lambda: self.set_delete_option(self.DELETE_FILE))
        option_layout.addWidget(self.radio_delete_file)
        
        # 文件路径提示
        path_hint = CaptionLabel(f"文件: {self.protocol_path}")
        path_hint.setWordWrap(True)
        option_layout.addWidget(path_hint)
        
        self.viewLayout.addLayout(option_layout)
        
        # 设置按钮
        self.yesButton.setText("删除")
        self.cancelButton.setText("取消")
        
        # 设置最小宽度
        self.widget.setMinimumWidth(450)
    
    def set_delete_option(self, option: int):
        """设置删除选项"""
        self.delete_option = option
    
    def get_delete_option(self) -> int:
        """获取删除选项"""
        return self.delete_option
