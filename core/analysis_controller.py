# -*- coding: utf-8 -*-
"""
AnalysisController - 分析控制器
从 main_window.py 提取的核心分析逻辑
负责协调协议、解析、会话管理
"""

from typing import Optional, List, Callable, Any
from PySide6.QtCore import QObject, Signal
import logging

from models.protocol import ProtocolConfig as Protocol
from models.data_frame import DataFrame
from core.parser import DataParser
from core.protocol_manager import ProtocolManager
from core.analysis_session import AnalysisSession, SessionManager, SessionConfig, SessionState
from core.analysis_history import AnalysisHistory
from core.exceptions import (
    SerialDataCompareError,
    ProtocolLoadError,
    ParseError,
    InvalidHexDataError
)

logger = logging.getLogger(__name__)


class AnalysisController(QObject):
    """
    分析控制器
    封装核心分析逻辑，解耦 GUI 与业务逻辑
    """
    
    # 信号
    protocol_loaded = Signal(object)        # Protocol 对象
    protocol_load_failed = Signal(str)      # 错误消息
    analysis_started = Signal()
    analysis_completed = Signal(object)     # SessionResult 对象
    analysis_failed = Signal(str)           # 错误消息
    frame_selected = Signal(int, object)    # (index, DataFrame)
    session_changed = Signal(object)        # AnalysisSession 对象
    warning_occurred = Signal(str)          # 警告消息
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # 管理器
        self._protocol_manager = ProtocolManager()
        self._session_manager = SessionManager(max_sessions=5)
        self._history = AnalysisHistory()
        
        # 当前状态
        self._current_protocol: Optional[Protocol] = None
        self._current_session: Optional[AnalysisSession] = None
        
        # 配置
        self._auto_save_history = True
        self._enable_trace = False
    
    # ========== 属性 ==========
    
    @property
    def protocol(self) -> Optional[Protocol]:
        """当前协议"""
        return self._current_protocol
    
    @property
    def session(self) -> Optional[AnalysisSession]:
        """当前会话"""
        return self._current_session
    
    @property
    def frames(self) -> List[DataFrame]:
        """当前帧列表"""
        if self._current_session:
            return self._current_session.frames
        return []
    
    @property
    def frame_count(self) -> int:
        """帧数量"""
        return len(self.frames)
    
    @property
    def is_ready(self) -> bool:
        """是否准备好进行分析"""
        return self._current_protocol is not None
    
    @property
    def history(self) -> AnalysisHistory:
        """历史记录管理器"""
        return self._history
    
    # ========== 协议管理 ==========
    
    def load_protocol(self, file_path: str) -> bool:
        """
        加载协议文件
        
        Args:
            file_path: 协议文件路径
            
        Returns:
            是否成功
        """
        try:
            result = self._protocol_manager.load_protocol(file_path)
            
            # 处理返回结果（可能是元组或单个对象）
            if isinstance(result, tuple):
                protocol, warning_msg = result
                if warning_msg:
                    self.warning_occurred.emit(warning_msg)
            else:
                protocol = result
            
            if protocol:
                self._current_protocol = protocol
                self._create_new_session()
                self.protocol_loaded.emit(protocol)
                logger.info(f"协议加载成功: {protocol.name}")
                return True
            else:
                self.protocol_load_failed.emit("协议加载失败")
                return False
                
        except ProtocolLoadError as e:
            error_msg = str(e)
            self.protocol_load_failed.emit(error_msg)
            logger.error(f"协议加载失败: {error_msg}")
            return False
        except Exception as e:
            error_msg = f"未知错误: {e}"
            self.protocol_load_failed.emit(error_msg)
            logger.exception("协议加载时发生未知错误")
            return False
    
    def set_protocol(self, protocol: Protocol):
        """
        直接设置协议对象
        
        Args:
            protocol: 协议对象
        """
        self._current_protocol = protocol
        self._create_new_session()
        self.protocol_loaded.emit(protocol)
    
    def clear_protocol(self):
        """清除当前协议"""
        self._current_protocol = None
        self._current_session = None
        self.session_changed.emit(None)
    
    # ========== 会话管理 ==========
    
    def _create_new_session(self) -> AnalysisSession:
        """创建新的分析会话"""
        config = SessionConfig(
            enable_trace=self._enable_trace,
            auto_save_history=self._auto_save_history
        )
        session = self._session_manager.create_session(config)
        
        if self._current_protocol:
            session.set_protocol(self._current_protocol)
        
        self._current_session = session
        self.session_changed.emit(session)
        return session
    
    def get_session_history(self) -> List[AnalysisSession]:
        """获取会话历史"""
        return self._session_manager.sessions
    
    def switch_session(self, session_id: str) -> bool:
        """切换到指定会话"""
        if self._session_manager.set_current(session_id):
            self._current_session = self._session_manager.current
            self.session_changed.emit(self._current_session)
            return True
        return False
    
    # ========== 数据分析 ==========
    
    def analyze_hex_string(self, hex_string: str, source: str = "") -> bool:
        """
        分析十六进制字符串
        
        Args:
            hex_string: 十六进制字符串
            source: 数据来源描述
            
        Returns:
            是否成功
        """
        if not self._current_protocol:
            self.analysis_failed.emit("请先加载协议")
            return False
        
        try:
            # 清理并验证十六进制字符串
            cleaned = self._clean_hex_string(hex_string)
            if not cleaned:
                self.analysis_failed.emit("请输入有效的十六进制数据")
                return False
            
            # 转换为字节
            try:
                raw_data = bytes.fromhex(cleaned)
            except ValueError as e:
                self.analysis_failed.emit(f"十六进制格式错误: {e}")
                return False
            
            return self.analyze_bytes(raw_data, source)
            
        except Exception as e:
            error_msg = f"分析失败: {e}"
            self.analysis_failed.emit(error_msg)
            logger.exception("分析十六进制字符串时发生错误")
            return False
    
    def analyze_bytes(self, raw_data: bytes, source: str = "") -> bool:
        """
        分析字节数据
        
        Args:
            raw_data: 原始字节数据
            source: 数据来源描述
            
        Returns:
            是否成功
        """
        if not self._current_protocol:
            self.analysis_failed.emit("请先加载协议")
            return False
        
        if not raw_data:
            self.analysis_failed.emit("数据为空")
            return False
        
        # 确保有会话
        if not self._current_session:
            self._create_new_session()
        
        # 设置数据
        self._current_session.set_raw_data(raw_data, source)
        
        # 发出开始信号
        self.analysis_started.emit()
        
        try:
            # 执行解析
            result = self._current_session.parse()
            
            if result.success:
                # 保存到历史
                if self._auto_save_history:
                    self._save_to_history(raw_data, result.frames)
                
                self.analysis_completed.emit(result)
                logger.info(f"分析完成: {result.frame_count} 帧, "
                           f"耗时 {result.parse_time_ms:.1f}ms")
                
                # 发出警告
                for warning in result.warnings:
                    self.warning_occurred.emit(warning)
                
                return True
            else:
                self.analysis_failed.emit(result.error_message or "分析失败")
                return False
                
        except ParseError as e:
            self.analysis_failed.emit(str(e))
            logger.error(f"解析错误: {e}")
            return False
        except Exception as e:
            error_msg = f"分析失败: {e}"
            self.analysis_failed.emit(error_msg)
            logger.exception("分析时发生未知错误")
            return False
    
    def _clean_hex_string(self, hex_string: str) -> str:
        """清理十六进制字符串"""
        # 移除常见分隔符和空白
        cleaned = hex_string.replace(" ", "")
        cleaned = cleaned.replace("\n", "")
        cleaned = cleaned.replace("\r", "")
        cleaned = cleaned.replace("\t", "")
        cleaned = cleaned.replace("-", "")
        cleaned = cleaned.replace(":", "")
        cleaned = cleaned.replace(",", "")
        cleaned = cleaned.replace("0x", "")
        cleaned = cleaned.replace("0X", "")
        cleaned = cleaned.upper()
        
        # 验证字符
        valid_chars = set("0123456789ABCDEF")
        if not all(c in valid_chars for c in cleaned):
            invalid_chars = [c for c in cleaned if c not in valid_chars]
            raise InvalidHexDataError(
                hex_string, 
                cleaned.find(invalid_chars[0]) if invalid_chars else 0,
                invalid_chars[0] if invalid_chars else ""
            )
        
        return cleaned
    
    def _save_to_history(self, raw_data: bytes, frames: List[DataFrame]):
        """保存到历史记录"""
        try:
            protocol_name = self._current_protocol.name if self._current_protocol else "未知"
            self._history.add_record(
                protocol_name=protocol_name,
                raw_data=raw_data.hex().upper(),
                frame_count=len(frames),
                valid_count=sum(1 for f in frames if f.is_valid)
            )
        except Exception as e:
            logger.warning(f"保存历史记录失败: {e}")
    
    # ========== 帧访问 ==========
    
    def get_frame(self, index: int) -> Optional[DataFrame]:
        """获取指定索引的帧"""
        if self._current_session:
            return self._current_session.get_frame(index)
        return None
    
    def select_frame(self, index: int):
        """选择帧并发出信号"""
        frame = self.get_frame(index)
        if frame:
            self.frame_selected.emit(index, frame)
    
    def get_valid_frames(self) -> List[DataFrame]:
        """获取所有有效帧"""
        if self._current_session:
            return self._current_session.get_valid_frames()
        return []
    
    def get_invalid_frames(self) -> List[DataFrame]:
        """获取所有无效帧"""
        if self._current_session:
            return self._current_session.get_invalid_frames()
        return []
    
    # ========== 统计信息 ==========
    
    def get_statistics(self) -> dict:
        """获取当前会话统计信息"""
        if self._current_session:
            return self._current_session.get_statistics()
        return {
            "frame_count": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "total_bytes": 0,
            "parsed_bytes": 0,
            "parse_rate": 0.0
        }
    
    # ========== 配置 ==========
    
    def set_auto_save_history(self, enabled: bool):
        """设置是否自动保存历史"""
        self._auto_save_history = enabled
    
    def set_enable_trace(self, enabled: bool):
        """设置是否启用详细追踪"""
        self._enable_trace = enabled
    
    # ========== 导出 ==========
    
    def export_frames_to_csv(self, file_path: str) -> bool:
        """导出帧数据到 CSV"""
        if not self.frames:
            return False
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入表头
                headers = ['帧序号', '起始位置', '长度', '校验状态', '原始数据']
                if self.frames:
                    # 添加字段名作为列
                    for field_name in self.frames[0].fields.keys():
                        headers.append(field_name)
                writer.writerow(headers)
                
                # 写入数据
                for i, frame in enumerate(self.frames):
                    row = [
                        i + 1,
                        frame.start_position,
                        len(frame.raw_data),
                        '有效' if frame.is_valid else '无效',
                        frame.raw_data.hex().upper()
                    ]
                    for field_name, field_data in frame.fields.items():
                        row.append(field_data.get('hex_value', ''))
                    writer.writerow(row)
            
            logger.info(f"导出 CSV 成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出 CSV 失败: {e}")
            return False
    
    def export_session_report(self, file_path: str) -> bool:
        """导出会话报告"""
        if not self._current_session:
            return False
        
        try:
            stats = self.get_statistics()
            session_info = self._current_session.to_dict()
            
            report_lines = [
                "=" * 60,
                "SerialDataCompare 分析报告",
                "=" * 60,
                "",
                f"会话 ID: {session_info['id']}",
                f"协议: {session_info['protocol_name']}",
                f"数据来源: {session_info['data_source']}",
                f"创建时间: {session_info['created_at']}",
                "",
                "统计信息:",
                f"  总帧数: {stats['frame_count']}",
                f"  有效帧: {stats['valid_count']}",
                f"  无效帧: {stats['invalid_count']}",
                f"  总字节: {stats['total_bytes']}",
                f"  解析率: {stats['parse_rate']:.1f}%",
                "",
            ]
            
            # 添加帧详情
            report_lines.append("帧详情:")
            for i, frame in enumerate(self.frames):
                status = "✓" if frame.is_valid else "✗"
                report_lines.append(
                    f"  [{i+1}] {status} @{frame.start_position} "
                    f"({len(frame.raw_data)} bytes)"
                )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(report_lines))
            
            logger.info(f"导出报告成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出报告失败: {e}")
            return False
