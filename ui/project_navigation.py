# This Python file uses the following encoding: utf-8
"""
项目导航界面 - 左侧项目和协议树形导航
支持拖拽功能：
- 拖拽协议到其他项目
- 拖拽协议到文件夹
- 拖拽调整项目顺序
"""
import os
import shutil
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                                QTreeWidgetItem, QFrame, QMenu, QApplication,
                                QFileDialog, QAbstractItemView)
from PySide6.QtCore import Signal, Qt, QMimeData, QByteArray
from PySide6.QtGui import QCursor, QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent

from qfluentwidgets import (PushButton, ToolButton, TitleLabel, BodyLabel,
                           SearchLineEdit, FluentIcon as FIF, 
                           InfoBar, InfoBarPosition, CardWidget,
                           SubtitleLabel, CaptionLabel, isDarkTheme,
                           TreeWidget, Action, RoundMenu, MessageBox)

from core.project_manager import ProjectManager, Project, ProtocolInfo
from ui.project_dialog import RenameDialog, DeleteProjectDialog, DeleteProtocolDialog, ProjectHistoryDialog


class ProjectNavigationWidget(QWidget):
    """项目导航组件"""
    
    # 信号
    protocol_selected = Signal(str)  # 选择协议时发出，传递协议文件路径
    project_selected = Signal(str)   # 选择项目时发出，传递项目ID
    request_new_project = Signal()   # 请求新建项目
    request_edit_project = Signal(str)  # 请求编辑项目，传递项目ID
    request_delete_project = Signal(str)  # 请求删除项目，传递项目ID
    
    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self._clipboard_protocol = None  # 剪贴板：复制的协议路径
        self._clipboard_is_cut = False   # 是否是剪切操作
        self._drag_item = None           # 当前拖拽的项目
        self._drag_source_project_id = None  # 拖拽源项目ID
        self.init_ui()
        self.refresh_tree()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 标题栏
        title_layout = QHBoxLayout()
        self.title_label = SubtitleLabel("项目管理")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # 刷新按钮
        self.refresh_btn = ToolButton(FIF.SYNC)
        self.refresh_btn.clicked.connect(self.refresh_tree)
        title_layout.addWidget(self.refresh_btn)
        
        # 新建项目按钮
        self.add_btn = ToolButton(FIF.ADD)
        self.add_btn.clicked.connect(lambda: self.request_new_project.emit())
        title_layout.addWidget(self.add_btn)
        
        layout.addLayout(title_layout)
        
        # 搜索框
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索项目或协议...")
        self.search_edit.textChanged.connect(self.filter_tree)
        layout.addWidget(self.search_edit)
        
        # 项目树
        self.tree = TreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # 启用拖拽功能
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDrop)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        
        # 重写拖拽相关方法
        self.tree.startDrag = self._start_drag
        self.tree.dragEnterEvent = self._drag_enter_event
        self.tree.dragMoveEvent = self._drag_move_event
        self.tree.dropEvent = self._drop_event
        
        layout.addWidget(self.tree, 1)
        
        # 底部提示
        self.hint_label = CaptionLabel("拖拽移动文件/夹 | Ctrl+拖拽复制 | 双击加载协议")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)
        
        # 记录展开状态的字典
        self._expanded_states = {}
    
    def _save_expanded_states(self):
        """保存当前的展开状态"""
        self._expanded_states = {}
        
        def save_item_state(item):
            data = item.data(0, Qt.UserRole)
            if data:
                # 使用类型和ID/路径作为唯一标识
                if data.get('type') == 'project':
                    key = f"project:{data.get('id')}"
                elif data.get('type') == 'folder':
                    key = f"folder:{data.get('project_id')}:{data.get('path')}"
                else:
                    return
                self._expanded_states[key] = item.isExpanded()
            
            for i in range(item.childCount()):
                save_item_state(item.child(i))
        
        for i in range(self.tree.topLevelItemCount()):
            save_item_state(self.tree.topLevelItem(i))
    
    def _restore_expanded_states(self):
        """恢复之前的展开状态"""
        if not self._expanded_states:
            return
        
        def restore_item_state(item):
            data = item.data(0, Qt.UserRole)
            if data:
                if data.get('type') == 'project':
                    key = f"project:{data.get('id')}"
                elif data.get('type') == 'folder':
                    key = f"folder:{data.get('project_id')}:{data.get('path')}"
                else:
                    return
                
                if key in self._expanded_states:
                    item.setExpanded(self._expanded_states[key])
            
            for i in range(item.childCount()):
                restore_item_state(item.child(i))
        
        for i in range(self.tree.topLevelItemCount()):
            restore_item_state(self.tree.topLevelItem(i))
    
    def refresh_tree(self):
        """刷新项目树"""
        # 保存当前展开状态
        self._save_expanded_states()
        
        self.tree.clear()
        
        projects = self.project_manager.get_all_projects()
        
        if not projects:
            # 显示空状态提示
            empty_item = QTreeWidgetItem(self.tree)
            empty_item.setText(0, "暂无项目，点击+创建")
            empty_item.setFlags(Qt.NoItemFlags)
            return
        
        for project in projects:
            # 刷新项目的协议列表
            project.scan_protocols()
            
            # 创建项目节点
            project_item = QTreeWidgetItem(self.tree)
            project_item.setText(0, f"📁 {project.name}")
            # 不设置 tooltip，避免黑框问题
            project_item.setData(0, Qt.UserRole, {'type': 'project', 'id': project.id})
            # 默认展开（如果没有保存的状态）
            is_new = f"project:{project.id}" not in self._expanded_states
            project_item.setExpanded(is_new or self._expanded_states.get(f"project:{project.id}", True))
            
            # 获取按文件夹分组的协议结构
            folder_structure = project.get_folder_structure()
            
            if not folder_structure:
                # 显示空协议提示
                empty_protocol = QTreeWidgetItem(project_item)
                empty_protocol.setText(0, "（无协议文件）")
                empty_protocol.setFlags(Qt.NoItemFlags)
                continue
            
            # 用于存储文件夹节点的字典，支持多级文件夹
            folder_items = {}
            
            # 按文件夹路径排序
            sorted_folders = sorted(folder_structure.keys())
            
            for folder_path in sorted_folders:
                protocols = folder_structure[folder_path]
                
                if folder_path == "":
                    # 根目录下的协议直接添加到项目节点
                    parent_item = project_item
                else:
                    # 创建文件夹层级结构
                    parts = folder_path.split(os.sep)
                    current_path = ""
                    parent_item = project_item
                    
                    for part in parts:
                        current_path = os.path.join(current_path, part) if current_path else part
                        
                        if current_path not in folder_items:
                            # 创建新的文件夹节点
                            folder_item = QTreeWidgetItem(parent_item)
                            folder_item.setText(0, f"📂 {part}")
                            # 不设置 tooltip，避免黑框问题
                            folder_item.setData(0, Qt.UserRole, {'type': 'folder', 'path': current_path, 'project_id': project.id})
                            # 默认展开（如果没有保存的状态）
                            folder_key = f"folder:{project.id}:{current_path}"
                            is_new_folder = folder_key not in self._expanded_states
                            folder_item.setExpanded(is_new_folder or self._expanded_states.get(folder_key, True))
                            folder_items[current_path] = folder_item
                        
                        parent_item = folder_items[current_path]
                
                # 添加协议到对应的父节点
                for protocol in protocols:
                    protocol_item = QTreeWidgetItem(parent_item)
                    protocol_item.setText(0, f"📄 {protocol.name}")
                    # 不设置 tooltip，避免黑框问题
                    protocol_item.setData(0, Qt.UserRole, {'type': 'protocol', 'path': protocol.file_path})
        
        # 高亮当前选中的项目和协议
        self.highlight_current_selection()
    
    def highlight_current_selection(self):
        """高亮当前选中的项目和协议"""
        current_project = self.project_manager.current_project
        current_protocol_path = self.project_manager.current_protocol_path
        
        if not current_project:
            return
        
        # 遍历树找到当前项目和协议
        for i in range(self.tree.topLevelItemCount()):
            project_item = self.tree.topLevelItem(i)
            item_data = project_item.data(0, Qt.UserRole)
            
            if item_data and item_data.get('type') == 'project':
                if item_data.get('id') == current_project.id:
                    # 展开当前项目
                    project_item.setExpanded(True)
                    
                    # 查找当前协议
                    if current_protocol_path:
                        for j in range(project_item.childCount()):
                            child = project_item.child(j)
                            child_data = child.data(0, Qt.UserRole)
                            if child_data and child_data.get('path') == current_protocol_path:
                                self.tree.setCurrentItem(child)
                                return
                    
                    # 如果没有选中协议，选中项目
                    self.tree.setCurrentItem(project_item)
                    return
    
    def filter_tree(self, text: str):
        """过滤树形视图"""
        text = text.lower().strip()
        
        for i in range(self.tree.topLevelItemCount()):
            project_item = self.tree.topLevelItem(i)
            project_visible = False
            
            # 检查项目名是否匹配
            if text in project_item.text(0).lower():
                project_visible = True
            
            # 检查子项
            for j in range(project_item.childCount()):
                child = project_item.child(j)
                child_visible = text in child.text(0).lower() or not text
                child.setHidden(not child_visible)
                
                if child_visible:
                    project_visible = True
            
            # 如果搜索为空或项目/子项匹配，显示项目
            project_item.setHidden(not (project_visible or not text))
            
            # 如果有匹配的子项，展开项目
            if project_visible and text:
                project_item.setExpanded(True)
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.tree.itemAt(pos)
        
        menu = RoundMenu(parent=self)
        
        if item:
            item_data = item.data(0, Qt.UserRole)
            
            if item_data and item_data.get('type') == 'project':
                project_id = item_data.get('id')
                
                # 项目菜单
                menu.addAction(Action(FIF.FOLDER, "打开文件夹", triggered=lambda: self.open_project_folder(project_id)))
                menu.addSeparator()
                # 粘贴选项
                paste_action = Action(FIF.PASTE, "粘贴协议", triggered=lambda: self.paste_protocol_to_project(project_id))
                paste_action.setEnabled(self._clipboard_protocol is not None)
                menu.addAction(paste_action)
                menu.addSeparator()
                menu.addAction(Action(FIF.EDIT, "重命名项目", triggered=lambda: self.rename_project(project_id)))
                menu.addAction(Action(FIF.SETTING, "编辑项目设置", triggered=lambda: self.request_edit_project.emit(project_id)))
                menu.addAction(Action(FIF.SYNC, "刷新协议", triggered=lambda: self.refresh_project(project_id)))
                menu.addAction(Action(FIF.HISTORY, "查看项目历史", triggered=lambda: self.show_project_history(project_id)))
                menu.addSeparator()
                menu.addAction(Action(FIF.DELETE, "删除项目", triggered=lambda: self.delete_project_dialog(project_id)))
            
            elif item_data and item_data.get('type') == 'folder':
                folder_path = item_data.get('path')
                project_id = item_data.get('project_id')
                
                # 文件夹菜单
                menu.addAction(Action(FIF.FOLDER, "打开文件夹", triggered=lambda: self.open_subfolder(project_id, folder_path)))
                menu.addSeparator()
                # 粘贴选项
                paste_action = Action(FIF.PASTE, "粘贴协议", triggered=lambda: self.paste_protocol_to_folder(project_id, folder_path))
                paste_action.setEnabled(self._clipboard_protocol is not None)
                menu.addAction(paste_action)
                menu.addSeparator()
                menu.addAction(Action(FIF.EDIT, "重命名文件夹", triggered=lambda: self.rename_folder(project_id, folder_path)))
            
            elif item_data and item_data.get('type') == 'protocol':
                protocol_path = item_data.get('path')
                
                # 协议菜单
                menu.addAction(Action(FIF.DOCUMENT, "加载协议", triggered=lambda: self.load_protocol(protocol_path)))
                menu.addAction(Action(FIF.FOLDER, "打开所在文件夹", triggered=lambda: self.open_protocol_folder(protocol_path)))
                menu.addSeparator()
                menu.addAction(Action(FIF.COPY, "复制协议", triggered=lambda: self.copy_protocol(protocol_path)))
                menu.addAction(Action(FIF.CUT, "剪切协议", triggered=lambda: self.cut_protocol(protocol_path)))
                menu.addSeparator()
                menu.addAction(Action(FIF.EDIT, "重命名协议文件", triggered=lambda: self.rename_protocol(protocol_path)))
                menu.addAction(Action(FIF.DELETE, "删除协议文件", triggered=lambda: self.delete_protocol(protocol_path)))
        
        # 通用菜单项
        menu.addSeparator()
        menu.addAction(Action(FIF.ADD, "新建项目", triggered=lambda: self.request_new_project.emit()))
        menu.addAction(Action(FIF.SYNC, "刷新全部", triggered=self.refresh_tree))
        
        menu.exec(QCursor.pos())
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """单击项目"""
        item_data = item.data(0, Qt.UserRole)
        
        if not item_data:
            return
        
        if item_data.get('type') == 'project':
            project_id = item_data.get('id')
            self.project_manager.select_project(project_id)
            self.project_selected.emit(project_id)
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击加载协议"""
        item_data = item.data(0, Qt.UserRole)
        
        if not item_data:
            return
        
        if item_data.get('type') == 'protocol':
            protocol_path = item_data.get('path')
            self.load_protocol(protocol_path)
        elif item_data.get('type') == 'project':
            # 双击项目展开/折叠
            item.setExpanded(not item.isExpanded())
    
    def load_protocol(self, protocol_path: str):
        """加载协议"""
        self.project_manager.select_protocol(protocol_path)
        self.protocol_selected.emit(protocol_path)
        
        # 显示提示
        InfoBar.success(
            title="协议已加载",
            content=f"已加载协议: {protocol_path.split('/')[-1]}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self.window()
        )
    
    def refresh_project(self, project_id: str):
        """刷新指定项目的协议列表"""
        project = self.project_manager.get_project(project_id)
        if project:
            project.scan_protocols()
            self.refresh_tree()
            
            InfoBar.success(
                title="刷新成功",
                content=f"已刷新项目 '{project.name}'，找到 {len(project.protocols)} 个协议",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
    
    def open_project_folder(self, project_id: str):
        """打开项目文件夹"""
        import subprocess
        import sys
        
        project = self.project_manager.get_project(project_id)
        if project and project.folder_path:
            try:
                if sys.platform == 'win32':
                    subprocess.Popen(['explorer', project.folder_path])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', project.folder_path])
                else:
                    subprocess.Popen(['xdg-open', project.folder_path])
            except Exception as e:
                InfoBar.error(
                    title="打开失败",
                    content=f"无法打开文件夹: {e}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )
    
    def open_protocol_folder(self, protocol_path: str):
        """打开协议所在文件夹"""
        import subprocess
        import sys
        import os
        
        folder_path = os.path.dirname(protocol_path)
        if folder_path:
            try:
                if sys.platform == 'win32':
                    subprocess.Popen(['explorer', folder_path])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', folder_path])
                else:
                    subprocess.Popen(['xdg-open', folder_path])
            except Exception as e:
                InfoBar.error(
                    title="打开失败",
                    content=f"无法打开文件夹: {e}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.window()
                )

    def open_subfolder(self, project_id: str, relative_folder: str):
        """打开项目子文件夹"""
        import subprocess
        import sys
        
        project = self.project_manager.get_project(project_id)
        if project:
            full_path = os.path.join(project.folder_path, relative_folder)
            if os.path.exists(full_path):
                try:
                    if sys.platform == 'win32':
                        subprocess.Popen(['explorer', full_path])
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', full_path])
                    else:
                        subprocess.Popen(['xdg-open', full_path])
                except Exception as e:
                    InfoBar.error(
                        title="打开失败",
                        content=f"无法打开文件夹: {e}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )

    def rename_project(self, project_id: str):
        """重命名项目"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        dialog = RenameDialog(
            parent=self.window(),
            item_type=RenameDialog.TYPE_PROJECT,
            current_name=project.name
        )
        
        if dialog.exec() and dialog.validate():
            new_name = dialog.get_new_name()
            if new_name and new_name != project.name:
                project.name = new_name
                self.project_manager.save_projects()
                self.refresh_tree()
                
                InfoBar.success(
                    title="重命名成功",
                    content=f"项目已重命名为: {new_name}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.window()
                )

    def rename_folder(self, project_id: str, relative_folder: str):
        """重命名文件夹"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        full_path = os.path.join(project.folder_path, relative_folder)
        folder_name = os.path.basename(relative_folder)
        
        dialog = RenameDialog(
            parent=self.window(),
            item_type=RenameDialog.TYPE_FOLDER,
            current_name=folder_name,
            file_path=full_path
        )
        
        if dialog.exec() and dialog.validate():
            new_name = dialog.get_new_name()
            if new_name and new_name != folder_name:
                parent_dir = os.path.dirname(full_path)
                new_path = os.path.join(parent_dir, new_name)
                
                try:
                    # 尝试直接重命名，失败则使用复制+删除
                    try:
                        os.rename(full_path, new_path)
                    except OSError:
                        shutil.copytree(full_path, new_path)
                        shutil.rmtree(full_path)
                    project.scan_protocols()  # 重新扫描
                    self.refresh_tree()
                    
                    InfoBar.success(
                        title="重命名成功",
                        content=f"文件夹已重命名为: {new_name}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self.window()
                    )
                except Exception as e:
                    InfoBar.error(
                        title="重命名失败",
                        content=f"无法重命名文件夹: {e}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )

    def rename_protocol(self, protocol_path: str):
        """重命名协议文件"""
        if not os.path.exists(protocol_path):
            return
        
        file_name = os.path.basename(protocol_path)
        name_without_ext = os.path.splitext(file_name)[0]
        
        dialog = RenameDialog(
            parent=self.window(),
            item_type=RenameDialog.TYPE_PROTOCOL,
            current_name=name_without_ext,
            file_path=protocol_path
        )
        
        if dialog.exec() and dialog.validate():
            new_name = dialog.get_new_name()
            if new_name and new_name != name_without_ext:
                parent_dir = os.path.dirname(protocol_path)
                new_path = os.path.join(parent_dir, f"{new_name}.json")
                
                if os.path.exists(new_path):
                    InfoBar.error(
                        title="重命名失败",
                        content="目标文件已存在",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )
                    return
                
                try:
                    # 尝试直接重命名，失败则使用复制+删除
                    try:
                        os.rename(protocol_path, new_path)
                    except OSError:
                        shutil.copy2(protocol_path, new_path)
                        os.remove(protocol_path)
                    
                    # 更新协议文件内的名称字段
                    try:
                        import json
                        with open(new_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if 'name' in data:
                            data['name'] = new_name
                            with open(new_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                    except:
                        pass  # 忽略JSON更新失败
                    
                    # 刷新树
                    self.refresh_tree()
                    
                    InfoBar.success(
                        title="重命名成功",
                        content=f"协议已重命名为: {new_name}.json",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self.window()
                    )
                except Exception as e:
                    InfoBar.error(
                        title="重命名失败",
                        content=f"无法重命名文件: {e}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )

    def delete_protocol(self, protocol_path: str):
        """删除协议文件"""
        if not os.path.exists(protocol_path):
            return
        
        file_name = os.path.basename(protocol_path)
        
        # 确认对话框 - 支持两种删除方式
        dialog = DeleteProtocolDialog(
            self.window(),
            protocol_name=file_name,
            protocol_path=protocol_path
        )
        
        if dialog.exec():
            delete_option = dialog.get_delete_option()
            
            if delete_option == DeleteProtocolDialog.DELETE_FILE:
                # 永久删除文件
                try:
                    os.remove(protocol_path)
                    self.refresh_tree()
                    
                    InfoBar.success(
                        title="删除成功",
                        content=f"协议文件 {file_name} 已永久删除",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self.window()
                    )
                except Exception as e:
                    InfoBar.error(
                        title="删除失败",
                        content=f"无法删除文件: {e}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )
            else:
                # 仅从项目中移除（将文件移动到项目文件夹外或标记为隐藏）
                # 这里采用刷新树但不删除文件的方式，文件仍存在于磁盘
                # 注：由于当前架构是基于文件夹扫描的，"移除"实际上需要移动文件
                # 为简化实现，这里将文件移动到项目文件夹的 .removed 子文件夹
                try:
                    removed_dir = os.path.join(os.path.dirname(protocol_path), ".removed")
                    os.makedirs(removed_dir, exist_ok=True)
                    new_path = os.path.join(removed_dir, file_name)
                    
                    # 如果目标已存在，添加时间戳
                    if os.path.exists(new_path):
                        import time
                        base, ext = os.path.splitext(file_name)
                        new_path = os.path.join(removed_dir, f"{base}_{int(time.time())}{ext}")
                    
                    # 使用复制+删除以支持跨设备移动
                    shutil.copy2(protocol_path, new_path)
                    os.remove(protocol_path)
                    self.refresh_tree()
                    
                    InfoBar.success(
                        title="移除成功",
                        content=f"协议 {file_name} 已从项目中移除\n文件已移至 .removed 文件夹",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )
                except Exception as e:
                    InfoBar.error(
                        title="移除失败",
                        content=f"无法移除文件: {e}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )

    def delete_project_dialog(self, project_id: str):
        """显示删除项目对话框"""
        import shutil
        
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        dialog = DeleteProjectDialog(
            parent=self.window(),
            project_name=project.name,
            folder_path=project.folder_path
        )
        
        if dialog.exec():
            delete_option = dialog.get_delete_option()
            
            # 删除记录
            self.project_manager.delete_project(project_id)
            
            # 如果选择同时删除文件
            if delete_option == DeleteProjectDialog.DELETE_WITH_FILES:
                try:
                    if os.path.exists(project.folder_path):
                        shutil.rmtree(project.folder_path)
                        InfoBar.success(
                            title="删除成功",
                            content=f"项目 '{project.name}' 及其文件夹已删除",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=2000,
                            parent=self.window()
                        )
                except Exception as e:
                    InfoBar.warning(
                        title="部分成功",
                        content=f"项目记录已删除，但文件夹删除失败: {e}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )
            else:
                InfoBar.success(
                    title="删除成功",
                    content=f"项目 '{project.name}' 已从列表中移除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.window()
                )
            
            self.refresh_tree()

    def show_project_history(self, project_id: str):
        """显示项目历史"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        # 创建项目历史对话框
        dialog = ProjectHistoryDialog(
            parent=self.window(),
            project=project
        )
        dialog.exec()

    def copy_protocol(self, protocol_path: str):
        """复制协议到剪贴板"""
        if os.path.exists(protocol_path):
            self._clipboard_protocol = protocol_path
            self._clipboard_is_cut = False
            
            protocol_name = os.path.basename(protocol_path)
            InfoBar.success(
                title="已复制",
                content=f"协议 '{protocol_name}' 已复制到剪贴板",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
    
    def cut_protocol(self, protocol_path: str):
        """剪切协议到剪贴板"""
        if os.path.exists(protocol_path):
            self._clipboard_protocol = protocol_path
            self._clipboard_is_cut = True
            
            protocol_name = os.path.basename(protocol_path)
            InfoBar.success(
                title="已剪切",
                content=f"协议 '{protocol_name}' 已剪切到剪贴板",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
    
    def paste_protocol_to_project(self, project_id: str):
        """粘贴协议到项目根目录"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        self._paste_protocol_to_path(project.folder_path, project_id)
    
    def paste_protocol_to_folder(self, project_id: str, relative_folder: str):
        """粘贴协议到文件夹"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return
        
        target_path = os.path.join(project.folder_path, relative_folder)
        self._paste_protocol_to_path(target_path, project_id)
    
    def _paste_protocol_to_path(self, target_dir: str, project_id: str):
        """粘贴协议到指定目录"""
        if not self._clipboard_protocol:
            return
        
        if not os.path.exists(self._clipboard_protocol):
            InfoBar.error(
                title="粘贴失败",
                content="源协议文件不存在",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
            self._clipboard_protocol = None
            return
        
        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)
        
        # 生成目标文件名
        src_name = os.path.basename(self._clipboard_protocol)
        target_path = os.path.join(target_dir, src_name)
        
        # 如果目标文件已存在，添加后缀
        if os.path.exists(target_path):
            base, ext = os.path.splitext(src_name)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(target_dir, f"{base}_副本{counter}{ext}")
                counter += 1
        
        try:
            if self._clipboard_is_cut:
                # 剪切 - 使用复制+删除以支持跨设备移动
                shutil.copy2(self._clipboard_protocol, target_path)
                os.remove(self._clipboard_protocol)
                self._clipboard_protocol = None  # 清空剪贴板
                
                InfoBar.success(
                    title="移动成功",
                    content=f"协议已移动到 {os.path.basename(target_path)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.window()
                )
            else:
                # 复制 - 复制文件
                shutil.copy2(self._clipboard_protocol, target_path)
                
                # 更新复制后的协议名称（在JSON文件内）
                self._update_protocol_name_in_file(target_path)
                
                InfoBar.success(
                    title="粘贴成功",
                    content=f"协议已复制到 {os.path.basename(target_path)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.window()
                )
            
            # 刷新项目
            self.refresh_project(project_id)
            
        except Exception as e:
            InfoBar.error(
                title="操作失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
    
    def _update_protocol_name_in_file(self, protocol_path: str):
        """更新复制后的协议文件中的名称字段"""
        try:
            with open(protocol_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新名称字段
            base_name = os.path.splitext(os.path.basename(protocol_path))[0]
            if 'name' in data:
                data['name'] = base_name
            
            with open(protocol_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass  # 忽略更新名称失败的情况

    # ==================== 拖拽功能 ====================
    
    def _start_drag(self, supported_actions):
        """开始拖拽"""
        item = self.tree.currentItem()
        if not item:
            return
        
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        item_type = item_data.get('type')
        
        # 允许拖拽项目、文件夹和协议
        if item_type not in ('project', 'protocol', 'folder'):
            return
        
        self._drag_item = item
        
        # 记录源项目ID
        if item_type == 'protocol' or item_type == 'folder':
            # 查找所属的项目
            parent = item.parent()
            while parent:
                parent_data = parent.data(0, Qt.UserRole)
                if parent_data and parent_data.get('type') == 'project':
                    self._drag_source_project_id = parent_data.get('id')
                    break
                parent = parent.parent()
        elif item_type == 'project':
            self._drag_source_project_id = item_data.get('id')
        
        # 创建拖拽对象
        drag = QDrag(self.tree)
        mime_data = QMimeData()
        
        # 将拖拽数据序列化
        drag_data = {
            'type': item_type,
            'data': item_data,
            'source_project_id': self._drag_source_project_id
        }
        mime_data.setData('application/x-project-navigation', 
                         QByteArray(json.dumps(drag_data).encode('utf-8')))
        mime_data.setText(item.text(0))
        
        drag.setMimeData(mime_data)
        
        # 设置拖拽图标提示
        result = drag.exec(Qt.MoveAction | Qt.CopyAction)
    
    def _drag_enter_event(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasFormat('application/x-project-navigation'):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def _drag_move_event(self, event: QDragMoveEvent):
        """拖拽移动事件"""
        if not event.mimeData().hasFormat('application/x-project-navigation'):
            event.ignore()
            return
        
        # 获取目标项目
        target_item = self.tree.itemAt(event.position().toPoint())
        
        if not target_item:
            # 拖到空白区域 - 对于项目，允许调整顺序
            event.acceptProposedAction()
            return
        
        target_data = target_item.data(0, Qt.UserRole)
        if not target_data:
            event.ignore()
            return
        
        # 解析拖拽数据
        try:
            drag_data = json.loads(event.mimeData().data('application/x-project-navigation').data().decode('utf-8'))
            drag_type = drag_data.get('type')
        except:
            event.ignore()
            return
        
        target_type = target_data.get('type')
        
        # 判断是否允许放置
        if drag_type == 'protocol':
            # 协议可以放到：项目、文件夹、另一个协议（放到同级目录）
            if target_type in ('project', 'folder', 'protocol'):
                event.acceptProposedAction()
            else:
                event.ignore()
        elif drag_type == 'folder':
            # 文件夹可以放到：项目、另一个文件夹
            if target_type in ('project', 'folder'):
                event.acceptProposedAction()
            else:
                event.ignore()
        elif drag_type == 'project':
            # 项目可以放到：另一个项目（调整顺序）
            if target_type == 'project':
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def _drop_event(self, event: QDropEvent):
        """放置事件"""
        if not event.mimeData().hasFormat('application/x-project-navigation'):
            event.ignore()
            return
        
        # 解析拖拽数据
        try:
            drag_data = json.loads(event.mimeData().data('application/x-project-navigation').data().decode('utf-8'))
            drag_type = drag_data.get('type')
            drag_item_data = drag_data.get('data')
            source_project_id = drag_data.get('source_project_id')
        except:
            event.ignore()
            return
        
        # 获取目标项目
        target_item = self.tree.itemAt(event.position().toPoint())
        
        if drag_type == 'protocol':
            self._handle_protocol_drop(drag_item_data, target_item, event, source_project_id)
        elif drag_type == 'folder':
            self._handle_folder_drop(drag_item_data, target_item, event, source_project_id)
        elif drag_type == 'project':
            self._handle_project_drop(drag_item_data, target_item, event)
        
        self._drag_item = None
        self._drag_source_project_id = None
    
    def _get_target_info(self, target_item: QTreeWidgetItem) -> tuple:
        """获取目标位置信息
        
        Returns:
            (target_dir, target_project_id) 或 (None, None)
        """
        if not target_item:
            return None, None
        
        target_data = target_item.data(0, Qt.UserRole)
        if not target_data:
            return None, None
        
        target_type = target_data.get('type')
        target_dir = None
        target_project_id = None
        
        if target_type == 'project':
            target_project_id = target_data.get('id')
            project = self.project_manager.get_project(target_project_id)
            if project:
                target_dir = project.folder_path
        elif target_type == 'folder':
            target_project_id = target_data.get('project_id')
            project = self.project_manager.get_project(target_project_id)
            if project:
                relative_folder = target_data.get('path')
                target_dir = os.path.join(project.folder_path, relative_folder)
        elif target_type == 'protocol':
            # 放到协议上 = 放到协议所在的目录
            protocol_path = target_data.get('path')
            if protocol_path:
                target_dir = os.path.dirname(protocol_path)
                # 找到所属项目
                parent = target_item.parent()
                while parent:
                    parent_data = parent.data(0, Qt.UserRole)
                    if parent_data and parent_data.get('type') == 'project':
                        target_project_id = parent_data.get('id')
                        break
                    parent = parent.parent()
        
        return target_dir, target_project_id

    def _handle_protocol_drop(self, drag_item_data: dict, target_item: QTreeWidgetItem, 
                              event: QDropEvent, source_project_id: str):
        """处理协议拖放"""
        protocol_path = drag_item_data.get('path')
        if not protocol_path or not os.path.exists(protocol_path):
            event.ignore()
            return
        
        target_dir, target_project_id = self._get_target_info(target_item)
        
        if not target_dir:
            event.ignore()
            return
        
        # 检查是否是同一个位置
        src_dir = os.path.dirname(protocol_path)
        if os.path.normpath(src_dir) == os.path.normpath(target_dir):
            event.ignore()
            return
        
        # 确定操作类型（按住Ctrl复制，否则移动）
        is_copy = event.modifiers() & Qt.ControlModifier
        
        # 执行操作
        try:
            os.makedirs(target_dir, exist_ok=True)
            
            src_name = os.path.basename(protocol_path)
            target_path = os.path.join(target_dir, src_name)
            
            # 如果目标文件已存在，添加后缀
            if os.path.exists(target_path):
                base, ext = os.path.splitext(src_name)
                counter = 1
                while os.path.exists(target_path):
                    target_path = os.path.join(target_dir, f"{base}_副本{counter}{ext}")
                    counter += 1
            
            if is_copy:
                shutil.copy2(protocol_path, target_path)
                self._update_protocol_name_in_file(target_path)
                action_text = "复制"
            else:
                # 使用复制+删除以支持跨设备移动
                shutil.copy2(protocol_path, target_path)
                os.remove(protocol_path)
                action_text = "移动"
            
            event.acceptProposedAction()
            
            # 刷新树
            self.refresh_tree()
            
            InfoBar.success(
                title=f"{action_text}成功",
                content=f"协议已{action_text}到目标位置",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
            
        except Exception as e:
            event.ignore()
            InfoBar.error(
                title="操作失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
    
    def _handle_folder_drop(self, drag_item_data: dict, target_item: QTreeWidgetItem, 
                            event: QDropEvent, source_project_id: str):
        """处理文件夹拖放"""
        relative_path = drag_item_data.get('path')
        drag_project_id = drag_item_data.get('project_id')
        
        if not relative_path or not drag_project_id:
            event.ignore()
            return
        
        source_project = self.project_manager.get_project(drag_project_id)
        if not source_project:
            event.ignore()
            return
        
        src_folder = os.path.join(source_project.folder_path, relative_path)
        if not os.path.exists(src_folder):
            event.ignore()
            return
        
        target_dir, target_project_id = self._get_target_info(target_item)
        
        if not target_dir:
            event.ignore()
            return
        
        # 不能移动到自己内部
        if os.path.normpath(target_dir).startswith(os.path.normpath(src_folder)):
            InfoBar.warning(
                title="无法移动",
                content="不能将文件夹移动到自身内部",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
            event.ignore()
            return
        
        # 检查是否是同一个位置
        src_parent = os.path.dirname(src_folder)
        if os.path.normpath(src_parent) == os.path.normpath(target_dir):
            event.ignore()
            return
        
        # 确定操作类型（按住Ctrl复制，否则移动）
        is_copy = event.modifiers() & Qt.ControlModifier
        
        # 执行操作
        try:
            folder_name = os.path.basename(src_folder)
            target_path = os.path.join(target_dir, folder_name)
            
            # 如果目标文件夹已存在，添加后缀
            if os.path.exists(target_path):
                counter = 1
                base_name = folder_name
                while os.path.exists(target_path):
                    target_path = os.path.join(target_dir, f"{base_name}_副本{counter}")
                    counter += 1
                folder_name = os.path.basename(target_path)
            
            if is_copy:
                shutil.copytree(src_folder, target_path)
                action_text = "复制"
            else:
                # 使用 copytree + rmtree 替代 move，以处理跨设备移动
                shutil.copytree(src_folder, target_path)
                shutil.rmtree(src_folder)
                action_text = "移动"
            
            event.acceptProposedAction()
            
            # 刷新树
            self.refresh_tree()
            
            InfoBar.success(
                title=f"{action_text}成功",
                content=f"文件夹已{action_text}到目标位置",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
            
        except Exception as e:
            event.ignore()
            InfoBar.error(
                title="操作失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
    
    def _handle_project_drop(self, drag_item_data: dict, target_item: QTreeWidgetItem, event: QDropEvent):
        """处理项目拖放（调整顺序）"""
        drag_project_id = drag_item_data.get('id')
        if not drag_project_id:
            event.ignore()
            return
        
        # 计算目标位置
        target_index = -1
        
        if target_item:
            target_data = target_item.data(0, Qt.UserRole)
            if target_data and target_data.get('type') == 'project':
                target_project_id = target_data.get('id')
                
                # 不能放到自己身上
                if target_project_id == drag_project_id:
                    event.ignore()
                    return
                
                # 获取目标项目的索引
                projects = self.project_manager.get_all_projects()
                for i, p in enumerate(projects):
                    if p.id == target_project_id:
                        target_index = i
                        break
        
        # 调整项目顺序
        if self.project_manager.reorder_project(drag_project_id, target_index):
            event.acceptProposedAction()
            self.refresh_tree()
            
            InfoBar.success(
                title="调整成功",
                content="项目顺序已更新",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
        else:
            event.ignore()
    
    def select_project_by_id(self, project_id: str):
        """根据项目ID选中项目"""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.get('type') == 'project' and item_data.get('id') == project_id:
                self.tree.setCurrentItem(item)
                item.setExpanded(True)
                break

