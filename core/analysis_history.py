"""
分析历史记录管理
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class AnalysisHistory:
    """分析历史记录管理器"""
    
    def __init__(self, max_history: int = 20):
        """
        初始化
        
        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self.history_file = Path.home() / '.serialdatacompare' / 'analysis_history.json'
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载分析历史记录失败: {e}")
            return []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存分析历史记录失败: {e}")
    
    def add_analysis(self, protocol_name: str, input_data: str, 
                    total_frames: int, valid_frames: int, error_frames: int,
                    frame_details: List[Dict[str, Any]]):
        """
        添加分析记录
        
        Args:
            protocol_name: 协议名称
            input_data: 输入数据
            total_frames: 总帧数
            valid_frames: 有效帧数
            error_frames: 错误帧数
            frame_details: 帧详情列表
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'protocol_name': protocol_name,
            'input_data': input_data[:200] + '...' if len(input_data) > 200 else input_data,  # 截断长数据
            'total_frames': total_frames,
            'valid_frames': valid_frames,
            'error_frames': error_frames,
            'frame_summary': [
                {
                    'frame_number': f['frame_number'],
                    'has_error': f['has_error'],
                    'checksum_valid': f['checksum_valid'],
                    'raw_data_hex': f['raw_data_hex']
                }
                for f in frame_details[:10]  # 最多保存前10帧的摘要
            ]
        }
        
        # 添加到列表开头
        self.history.insert(0, record)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        self._save_history()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取历史记录列表"""
        return self.history
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self._save_history()
    
    def get_record(self, index: int) -> Dict[str, Any]:
        """获取指定索引的记录"""
        if 0 <= index < len(self.history):
            return self.history[index]
        return {}
    
    def format_timestamp(self, timestamp: str) -> str:
        """格式化时间戳"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
