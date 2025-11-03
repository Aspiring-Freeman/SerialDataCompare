# -*- coding: utf-8 -*-
"""
协议历史记录管理
"""

import json
import os
from typing import List, Dict
from pathlib import Path


class ProtocolHistory:
    """协议历史记录管理器"""
    
    def __init__(self, max_items: int = 10):
        """
        初始化历史记录管理器
        
        Args:
            max_items: 最大保存数量
        """
        self.max_items = max_items
        self.history_file = self._get_history_file()
        self.history: List[Dict[str, str]] = self._load_history()
    
    def _get_history_file(self) -> str:
        """获取历史记录文件路径"""
        # 使用用户主目录下的配置文件夹
        config_dir = Path.home() / '.serialdatacompare'
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / 'protocol_history.json')
    
    def _load_history(self) -> List[Dict[str, str]]:
        """加载历史记录"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('history', [])
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            data = {'history': self.history}
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def add_protocol(self, file_path: str, protocol_name: str = None):
        """
        添加协议到历史记录
        
        Args:
            file_path: 协议文件路径
            protocol_name: 协议名称（可选）
        """
        # 规范化路径
        file_path = os.path.abspath(file_path)
        
        # 如果已存在，先移除
        self.history = [item for item in self.history if item['path'] != file_path]
        
        # 添加到开头
        name = protocol_name or os.path.basename(file_path)
        self.history.insert(0, {
            'path': file_path,
            'name': name
        })
        
        # 限制数量
        if len(self.history) > self.max_items:
            self.history = self.history[:self.max_items]
        
        self._save_history()
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        获取历史记录列表
        
        Returns:
            历史记录列表，每项包含 path 和 name
        """
        # 过滤掉不存在的文件
        valid_history = [
            item for item in self.history 
            if os.path.exists(item['path'])
        ]
        
        # 如果有无效项被过滤掉，更新历史记录
        if len(valid_history) != len(self.history):
            self.history = valid_history
            self._save_history()
        
        return self.history
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self._save_history()
    
    def remove_item(self, file_path: str):
        """
        从历史记录中移除指定项
        
        Args:
            file_path: 要移除的文件路径
        """
        file_path = os.path.abspath(file_path)
        self.history = [item for item in self.history if item['path'] != file_path]
        self._save_history()
