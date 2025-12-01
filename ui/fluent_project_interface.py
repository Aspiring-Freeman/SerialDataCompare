# This Python file uses the following encoding: utf-8
"""
项目管理界面 - Fluent Design
"""
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PySide6.QtCore import Signal, Qt

from qfluentwidgets import (
    CardWidget, PushButton, TitleLabel, SubtitleLabel,
    BodyLabel, FluentIcon as FIF, InfoBar, InfoBarPosition,
    PrimaryPushButton, ToolButton
)

from core.project_manager import ProjectManager
from ui.project_navigation import ProjectNavigationWidget
from ui.project_dialog import ProjectDialog, DeleteProjectDialog


class ProjectInterface(QWidget):
    """项目管理界面"""
    
    # 信号：当协议被选中时发射，携带协议文件路径
    protocol_selected = Signal(str)
    
    def __init__(self, project_manager: ProjectManager = None, parent=None):
        super().__init__(parent)
        self.setObjectName("project_interface")
        
        # 使用传入的项目管理器或创建新的
        self.project_manager = project_manager or ProjectManager()
        
        # 当前选中的协议路径
        self.selected_protocol_path = None
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题区域
        title_layout = QHBoxLayout()
        
        title_label = TitleLabel("项目管理")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 加载协议按钮
        self.load_btn = PrimaryPushButton("加载协议", self, FIF.PLAY)
        self.load_btn.clicked.connect(self.load_selected_protocol)
        self.load_btn.setEnabled(False)  # 默认禁用，选中协议后启用
        title_layout.addWidget(self.load_btn)
        
        # 快速操作按钮
        self.import_btn = PushButton("导入项目", self, FIF.FOLDER_ADD)
        self.import_btn.clicked.connect(self.import_project_from_folder)
        title_layout.addWidget(self.import_btn)
        
        self.new_btn = PushButton("新建项目", self, FIF.ADD)
        self.new_btn.clicked.connect(self.show_new_project_dialog)
        title_layout.addWidget(self.new_btn)
        
        main_layout.addLayout(title_layout)
        
        # 说明文字
        desc_label = BodyLabel(
            "在这里管理您的项目。每个项目对应一个文件夹，可以包含多个协议文件。\n"
            "选中协议后点击「加载协议」按钮，或双击协议快速加载。"
        )
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # 项目导航组件
        self.project_navigation = ProjectNavigationWidget(self.project_manager, self)
        main_layout.addWidget(self.project_navigation, 1)
        
        # 连接信号
        self.connect_signals()
    
    def connect_signals(self):
        """连接信号"""
        # 项目导航信号 - 注意：单击选中，双击才加载
        self.project_navigation.tree.itemClicked.connect(self.on_tree_item_clicked)
        self.project_navigation.protocol_selected.connect(self.on_protocol_load_requested)
        self.project_navigation.request_new_project.connect(self.show_new_project_dialog)
        self.project_navigation.request_edit_project.connect(self.show_edit_project_dialog)
        self.project_navigation.request_delete_project.connect(self.show_delete_project_dialog)
    
    def on_tree_item_clicked(self, item, column):
        """树形项目被单击选中"""
        item_data = item.data(0, Qt.UserRole)
        
        if item_data and item_data.get('type') == 'protocol':
            # 选中协议，启用加载按钮
            self.selected_protocol_path = item_data.get('path')
            self.load_btn.setEnabled(True)
            self.load_btn.setText(f"加载协议")
        else:
            # 选中项目或其他，禁用加载按钮
            self.selected_protocol_path = None
            self.load_btn.setEnabled(False)
            self.load_btn.setText("加载协议")
    
    def load_selected_protocol(self):
        """加载选中的协议"""
        if self.selected_protocol_path:
            self.protocol_selected.emit(self.selected_protocol_path)
    
    def on_protocol_load_requested(self, protocol_path: str):
        """协议加载请求（双击触发）"""
        # 转发信号给主窗口
        self.protocol_selected.emit(protocol_path)
    
    def show_new_project_dialog(self):
        """显示新建项目对话框"""
        dialog = ProjectDialog(self.window())
        
        if dialog.exec():
            project_data = dialog.get_project_data()
            project = self.project_manager.create_project(
                name=project_data['name'],
                folder_path=project_data['folder_path'],
                description=project_data['description']
            )
            
            # 刷新列表
            self.project_navigation.refresh_tree()
            
            # 选中新建的项目
            self.project_navigation.select_project_by_id(project.id)
            
            InfoBar.success(
                title="创建成功",
                content=f"项目 '{project.name}' 已创建，包含 {len(project.protocols)} 个协议",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
    
    def show_edit_project_dialog(self, project_id: str):
        """显示编辑项目对话框"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        dialog = ProjectDialog(self.window(), project_manager=self.project_manager, edit_project_id=project_id)
        
        if dialog.exec():
            project_data = dialog.get_project_data()
            updated_project = self.project_manager.update_project(
                project_id=project_id,
                name=project_data['name'],
                folder_path=project_data['folder_path'],
                description=project_data['description']
            )
            
            if updated_project:
                # 刷新列表
                self.project_navigation.refresh_tree()
                
                InfoBar.success(
                    title="更新成功",
                    content=f"项目 '{updated_project.name}' 已更新",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.window()
                )
    
    def show_delete_project_dialog(self, project_id: str):
        """显示删除项目确认对话框"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        dialog = DeleteProjectDialog(self.window(), project_name=project.name)
        
        if dialog.exec():
            project_name = project.name
            if self.project_manager.delete_project(project_id):
                # 刷新列表
                self.project_navigation.refresh_tree()
                
                InfoBar.success(
                    title="删除成功",
                    content=f"项目 '{project_name}' 已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.window()
                )
    
    def import_project_from_folder(self):
        """从文件夹导入项目"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择协议文件夹",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        if folder_path:
            project = self.project_manager.import_project_from_folder(folder_path)
            
            if project:
                # 刷新列表
                self.project_navigation.refresh_tree()
                
                # 选中新导入的项目
                self.project_navigation.select_project_by_id(project.id)
                
                InfoBar.success(
                    title="导入成功",
                    content=f"项目 '{project.name}' 已导入，包含 {len(project.protocols)} 个协议",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
            else:
                InfoBar.error(
                    title="导入失败",
                    content="无法导入项目，请检查文件夹是否有效",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
    
    def refresh(self):
        """刷新项目列表"""
        self.project_navigation.refresh_tree()
    
    def get_current_project(self):
        """获取当前选中的项目"""
        return self.project_manager.current_project
    
    def get_current_protocol_path(self):
        """获取当前选中的协议路径"""
        return self.project_manager.current_protocol_path
