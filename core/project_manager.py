# This Python file uses the following encoding: utf-8
"""
项目管理器 - 管理项目和协议文件夹
"""
import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path

from utils import atomic_write_json, safe_load_json


@dataclass
class ProtocolInfo:
    """协议信息"""
    name: str  # 协议名称
    file_path: str  # 协议文件路径
    description: str = ""  # 协议描述
    field_count: int = 0  # 字段数量
    last_modified: str = ""  # 最后修改时间
    relative_folder: str = ""  # 相对于项目根目录的文件夹路径
    
    @classmethod
    def from_file(cls, file_path: str, base_folder: str = "") -> Optional['ProtocolInfo']:
        """从文件加载协议信息"""
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            name = data.get('name', os.path.basename(file_path))
            description = data.get('description', '')
            fields = data.get('fields', [])
            field_count = len(fields)
            
            # 获取文件修改时间
            mtime = os.path.getmtime(file_path)
            last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # 计算相对文件夹路径
            relative_folder = ""
            if base_folder:
                file_dir = os.path.dirname(file_path)
                if file_dir != base_folder:
                    relative_folder = os.path.relpath(file_dir, base_folder)
            
            return cls(
                name=name,
                file_path=file_path,
                description=description,
                field_count=field_count,
                last_modified=last_modified,
                relative_folder=relative_folder
            )
        except Exception as e:
            print(f"加载协议文件失败 {file_path}: {e}")
            return None


@dataclass
class Project:
    """项目定义"""
    id: str  # 项目唯一ID
    name: str  # 项目名称
    folder_path: str  # 协议文件夹路径
    description: str = ""  # 项目描述
    created_time: str = ""  # 创建时间
    last_accessed: str = ""  # 最后访问时间
    protocols: List[ProtocolInfo] = field(default_factory=list)  # 协议列表
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not self.last_accessed:
            self.last_accessed = self.created_time
    
    def scan_protocols(self) -> List[ProtocolInfo]:
        """扫描文件夹中的协议文件"""
        self.protocols = []
        
        if not os.path.exists(self.folder_path):
            return self.protocols
        
        # 支持的协议文件扩展名
        extensions = ['.json']
        
        # 扫描文件夹（包括子文件夹）
        for root, dirs, files in os.walk(self.folder_path):
            # 排除隐藏文件夹和 .removed 文件夹
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                # 排除隐藏文件
                if file.startswith('.'):
                    continue
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    protocol_info = ProtocolInfo.from_file(file_path, self.folder_path)
                    if protocol_info:
                        self.protocols.append(protocol_info)
        
        # 按相对路径和名称排序
        self.protocols.sort(key=lambda p: (p.relative_folder.lower(), p.name.lower()))
        return self.protocols
    
    def get_folder_structure(self) -> Dict[str, List[ProtocolInfo]]:
        """获取按文件夹分组的协议结构
        
        Returns:
            Dict: key是相对文件夹路径（""表示根目录），value是该文件夹下的协议列表
        """
        folder_map: Dict[str, List[ProtocolInfo]] = {}
        
        for protocol in self.protocols:
            folder = protocol.relative_folder
            if folder not in folder_map:
                folder_map[folder] = []
            folder_map[folder].append(protocol)
        
        return folder_map
    
    def update_access_time(self):
        """更新最后访问时间"""
        self.last_accessed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def to_dict(self) -> dict:
        """转换为字典（不包括协议列表，协议列表从文件夹动态扫描）"""
        return {
            'id': self.id,
            'name': self.name,
            'folder_path': self.folder_path,
            'description': self.description,
            'created_time': self.created_time,
            'last_accessed': self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """从字典创建项目"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            folder_path=data.get('folder_path', ''),
            description=data.get('description', ''),
            created_time=data.get('created_time', ''),
            last_accessed=data.get('last_accessed', '')
        )


class ProjectManager:
    """项目管理器"""
    
    def __init__(self):
        self.projects: Dict[str, Project] = {}  # 项目字典，key为项目ID
        self._project_order: List[str] = []  # 项目顺序列表，存储项目ID
        self.current_project: Optional[Project] = None  # 当前选中的项目
        self.current_protocol_path: Optional[str] = None  # 当前选中的协议路径
        
        # 配置文件路径
        self.config_dir = os.path.expanduser('~/.serialdatacompare')
        self.config_file = os.path.join(self.config_dir, 'projects.json')
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 加载项目配置
        self.load_config()
    
    def load_config(self):
        """加载项目配置（带备份恢复）"""
        try:
            data = safe_load_json(self.config_file, default=None)
            if data is None:
                return
            
            # 加载项目列表
            projects_data = data.get('projects', [])
            for proj_data in projects_data:
                project = Project.from_dict(proj_data)
                self.projects[project.id] = project
                self._project_order.append(project.id)
            
            # 恢复当前项目
            current_id = data.get('current_project_id')
            if current_id and current_id in self.projects:
                self.current_project = self.projects[current_id]
                self.current_project.scan_protocols()
            
            # 恢复当前协议
            self.current_protocol_path = data.get('current_protocol_path')
                
        except Exception as e:
            print(f"加载项目配置失败: {e}")
    
    def save_config(self):
        """保存项目配置 - 使用原子写入确保数据安全"""
        try:
            # 按顺序保存项目
            ordered_projects = []
            for proj_id in self._project_order:
                if proj_id in self.projects:
                    ordered_projects.append(self.projects[proj_id].to_dict())
            # 添加不在顺序列表中的项目
            for proj_id, project in self.projects.items():
                if proj_id not in self._project_order:
                    ordered_projects.append(project.to_dict())
            
            data = {
                'projects': ordered_projects,
                'current_project_id': self.current_project.id if self.current_project else None,
                'current_protocol_path': self.current_protocol_path
            }
            
            if not atomic_write_json(str(self.config_file), data):
                print("保存项目配置失败")
                
        except Exception as e:
            print(f"保存项目配置失败: {e}")
    
    def save_projects(self):
        """保存项目配置（别名）"""
        self.save_config()
    
    def generate_project_id(self) -> str:
        """生成唯一项目ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def create_project(self, name: str, folder_path: str, description: str = "") -> Project:
        """创建新项目"""
        project = Project(
            id=self.generate_project_id(),
            name=name,
            folder_path=folder_path,
            description=description
        )
        
        # 扫描协议
        project.scan_protocols()
        
        # 添加到项目列表
        self.projects[project.id] = project
        self._project_order.insert(0, project.id)  # 新项目放在最前面
        
        # 保存配置
        self.save_config()
        
        return project
    
    def update_project(self, project_id: str, name: str = None, 
                       folder_path: str = None, description: str = None) -> Optional[Project]:
        """更新项目信息"""
        if project_id not in self.projects:
            return None
        
        project = self.projects[project_id]
        
        if name is not None:
            project.name = name
        if folder_path is not None:
            project.folder_path = folder_path
            project.scan_protocols()  # 重新扫描协议
        if description is not None:
            project.description = description
        
        self.save_config()
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        if project_id not in self.projects:
            return False
        
        del self.projects[project_id]
        
        # 从顺序列表中移除
        if project_id in self._project_order:
            self._project_order.remove(project_id)
        
        # 如果删除的是当前项目，清空当前项目
        if self.current_project and self.current_project.id == project_id:
            self.current_project = None
            self.current_protocol_path = None
        
        self.save_config()
        return True
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> List[Project]:
        """获取所有项目（按顺序返回）"""
        result = []
        # 按保存的顺序返回
        for proj_id in self._project_order:
            if proj_id in self.projects:
                result.append(self.projects[proj_id])
        # 添加不在顺序列表中的项目
        for proj_id, project in self.projects.items():
            if proj_id not in self._project_order:
                result.append(project)
        return result
    
    def reorder_project(self, project_id: str, target_index: int) -> bool:
        """重新排序项目
        
        Args:
            project_id: 要移动的项目ID
            target_index: 目标位置索引，-1表示移到末尾
            
        Returns:
            是否成功
        """
        if project_id not in self.projects:
            return False
        
        # 从当前位置移除
        if project_id in self._project_order:
            self._project_order.remove(project_id)
        
        # 插入到新位置
        if target_index < 0 or target_index >= len(self._project_order):
            self._project_order.append(project_id)
        else:
            self._project_order.insert(target_index, project_id)
        
        self.save_config()
        return True
    
    def select_project(self, project_id: str) -> Optional[Project]:
        """选择项目"""
        if project_id not in self.projects:
            return None
        
        self.current_project = self.projects[project_id]
        self.current_project.update_access_time()
        self.current_project.scan_protocols()  # 刷新协议列表
        
        self.save_config()
        return self.current_project
    
    def select_protocol(self, protocol_path: str):
        """选择协议"""
        self.current_protocol_path = protocol_path
        self.save_config()
    
    def refresh_current_project(self) -> Optional[Project]:
        """刷新当前项目的协议列表"""
        if self.current_project:
            self.current_project.scan_protocols()
            return self.current_project
        return None
    
    def get_protocol_by_path(self, path: str) -> Optional[ProtocolInfo]:
        """根据路径获取协议信息"""
        if not self.current_project:
            return None
        
        for protocol in self.current_project.protocols:
            if protocol.file_path == path:
                return protocol
        return None
    
    def import_project_from_folder(self, folder_path: str) -> Optional[Project]:
        """从文件夹导入项目（自动使用文件夹名作为项目名）"""
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return None
        
        folder_name = os.path.basename(folder_path)
        return self.create_project(
            name=folder_name,
            folder_path=folder_path,
            description=f"从文件夹导入: {folder_path}"
        )
