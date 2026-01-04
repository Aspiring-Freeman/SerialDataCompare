# -*- coding: utf-8 -*-
"""
AnalysisSession - 分析会话
封装一次完整的数据分析过程，解耦 GUI 与核心逻辑
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import uuid

from models.protocol import ProtocolConfig as Protocol
from models.data_frame import DataFrame
from core.parse_context import ParseContext, ParseStage


class SessionState(Enum):
    """会话状态"""
    IDLE = "空闲"
    LOADING = "加载中"
    PARSING = "解析中"
    COMPLETED = "完成"
    ERROR = "错误"
    CANCELLED = "已取消"


@dataclass
class SessionResult:
    """会话结果"""
    success: bool
    frames: List[DataFrame]
    warnings: List[str]
    error_message: str = ""
    parse_time_ms: float = 0.0
    bytes_processed: int = 0
    
    @property
    def frame_count(self) -> int:
        return len(self.frames)
    
    @property
    def valid_frame_count(self) -> int:
        return sum(1 for f in self.frames if f.is_valid)


@dataclass
class SessionConfig:
    """会话配置"""
    enable_trace: bool = False  # 启用详细追踪
    auto_save_history: bool = True  # 自动保存到历史
    max_frames: int = 10000  # 最大帧数限制
    timeout_ms: int = 30000  # 超时时间


class AnalysisSession:
    """
    分析会话
    封装完整的数据分析流程，包含协议、数据、结果和状态
    """
    
    def __init__(self, config: Optional[SessionConfig] = None):
        """
        初始化分析会话
        
        Args:
            config: 会话配置
        """
        self._id = str(uuid.uuid4())[:8]
        self._config = config or SessionConfig()
        self._state = SessionState.IDLE
        self._lock = threading.RLock()
        
        # 核心数据
        self._protocol: Optional[Protocol] = None
        self._raw_data: bytes = b""
        self._raw_data_source: str = ""  # 数据来源描述
        self._frames: List[DataFrame] = []
        
        # 解析上下文
        self._parse_context: Optional[ParseContext] = None
        
        # 结果
        self._result: Optional[SessionResult] = None
        self._warnings: List[str] = []
        
        # 时间戳
        self._created_at = datetime.now()
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        
        # 回调
        self._state_callbacks: List[Callable[[SessionState], None]] = []
        self._progress_callbacks: List[Callable[[int, int], None]] = []
    
    # ========== 属性 ==========
    
    @property
    def id(self) -> str:
        """会话 ID"""
        return self._id
    
    @property
    def state(self) -> SessionState:
        """当前状态"""
        return self._state
    
    @property
    def protocol(self) -> Optional[Protocol]:
        """协议"""
        return self._protocol
    
    @property
    def raw_data(self) -> bytes:
        """原始数据"""
        return self._raw_data
    
    @property
    def frames(self) -> List[DataFrame]:
        """解析后的帧列表"""
        return self._frames.copy()
    
    @property
    def frame_count(self) -> int:
        """帧数量"""
        return len(self._frames)
    
    @property
    def result(self) -> Optional[SessionResult]:
        """会话结果"""
        return self._result
    
    @property
    def is_ready(self) -> bool:
        """是否准备好进行解析"""
        return self._protocol is not None and len(self._raw_data) > 0
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self._state == SessionState.COMPLETED
    
    @property
    def has_error(self) -> bool:
        """是否有错误"""
        return self._state == SessionState.ERROR
    
    @property
    def warnings(self) -> List[str]:
        """警告列表"""
        return self._warnings.copy()
    
    @property
    def parse_context(self) -> Optional[ParseContext]:
        """解析上下文（调试用）"""
        return self._parse_context
    
    # ========== 状态管理 ==========
    
    def _set_state(self, state: SessionState):
        """设置状态并通知回调"""
        with self._lock:
            old_state = self._state
            self._state = state
            
        # 通知回调（在锁外执行）
        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception:
                pass
    
    def add_state_callback(self, callback: Callable[[SessionState], None]):
        """添加状态变化回调"""
        self._state_callbacks.append(callback)
    
    def add_progress_callback(self, callback: Callable[[int, int], None]):
        """添加进度回调 (current, total)"""
        self._progress_callbacks.append(callback)
    
    def _notify_progress(self, current: int, total: int):
        """通知进度"""
        for callback in self._progress_callbacks:
            try:
                callback(current, total)
            except Exception:
                pass
    
    # ========== 数据设置 ==========
    
    def set_protocol(self, protocol: Protocol):
        """
        设置协议
        
        Args:
            protocol: 协议对象
        """
        with self._lock:
            if self._state not in (SessionState.IDLE, SessionState.COMPLETED, SessionState.ERROR):
                raise RuntimeError("无法在解析过程中更改协议")
            self._protocol = protocol
            self._reset_results()
    
    def set_raw_data(self, data: bytes, source: str = ""):
        """
        设置原始数据
        
        Args:
            data: 原始字节数据
            source: 数据来源描述
        """
        with self._lock:
            if self._state not in (SessionState.IDLE, SessionState.COMPLETED, SessionState.ERROR):
                raise RuntimeError("无法在解析过程中更改数据")
            self._raw_data = data
            self._raw_data_source = source
            self._reset_results()
    
    def set_raw_data_hex(self, hex_string: str, source: str = ""):
        """
        从十六进制字符串设置原始数据
        
        Args:
            hex_string: 十六进制字符串
            source: 数据来源描述
        """
        # 清理并转换
        cleaned = hex_string.replace(" ", "").replace("\n", "").replace("\r", "")
        data = bytes.fromhex(cleaned)
        self.set_raw_data(data, source)
    
    def _reset_results(self):
        """重置结果"""
        self._frames = []
        self._result = None
        self._warnings = []
        self._parse_context = None
        self._started_at = None
        self._completed_at = None
        self._set_state(SessionState.IDLE)
    
    # ========== 解析执行 ==========
    
    def parse(self, parser=None) -> SessionResult:
        """
        执行解析
        
        Args:
            parser: 解析器实例（可选，默认创建新实例）
            
        Returns:
            解析结果
        """
        from core.parser import DataParser
        
        # 检查状态
        if not self.is_ready:
            return SessionResult(
                success=False,
                frames=[],
                warnings=[],
                error_message="协议或数据未设置"
            )
        
        with self._lock:
            if self._state == SessionState.PARSING:
                return SessionResult(
                    success=False,
                    frames=[],
                    warnings=[],
                    error_message="解析正在进行中"
                )
            self._set_state(SessionState.PARSING)
            self._started_at = datetime.now()
        
        try:
            # 创建解析上下文
            self._parse_context = ParseContext(
                self._raw_data, 
                enable_trace=self._config.enable_trace
            )
            
            # 创建解析器
            if parser is None:
                parser = DataParser(self._protocol)
            
            # 执行解析
            self._frames = parser.parse(self._raw_data)
            
            # 收集警告
            self._warnings = []
            if self._parse_context.has_warnings:
                for w in self._parse_context.warnings:
                    self._warnings.append(f"@{w.position}: {w.message}")
            
            # 计算时间
            self._completed_at = datetime.now()
            elapsed_ms = (self._completed_at - self._started_at).total_seconds() * 1000
            
            # 构建结果
            self._result = SessionResult(
                success=True,
                frames=self._frames,
                warnings=self._warnings,
                parse_time_ms=elapsed_ms,
                bytes_processed=len(self._raw_data)
            )
            
            self._set_state(SessionState.COMPLETED)
            return self._result
            
        except Exception as e:
            self._completed_at = datetime.now()
            elapsed_ms = 0
            if self._started_at:
                elapsed_ms = (self._completed_at - self._started_at).total_seconds() * 1000
            
            self._result = SessionResult(
                success=False,
                frames=self._frames,
                warnings=self._warnings,
                error_message=str(e),
                parse_time_ms=elapsed_ms,
                bytes_processed=len(self._raw_data)
            )
            
            self._set_state(SessionState.ERROR)
            return self._result
    
    def cancel(self):
        """取消解析（如果正在进行）"""
        with self._lock:
            if self._state == SessionState.PARSING:
                self._set_state(SessionState.CANCELLED)
    
    # ========== 帧访问 ==========
    
    def get_frame(self, index: int) -> Optional[DataFrame]:
        """
        获取指定索引的帧
        
        Args:
            index: 帧索引
            
        Returns:
            帧对象，如果索引无效返回 None
        """
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None
    
    def get_valid_frames(self) -> List[DataFrame]:
        """获取所有有效帧"""
        return [f for f in self._frames if f.is_valid]
    
    def get_invalid_frames(self) -> List[DataFrame]:
        """获取所有无效帧"""
        return [f for f in self._frames if not f.is_valid]
    
    def find_frames_by_field(self, field_name: str, 
                             value: Any = None) -> List[DataFrame]:
        """
        按字段查找帧
        
        Args:
            field_name: 字段名
            value: 字段值（可选，None 表示只检查字段存在）
            
        Returns:
            匹配的帧列表
        """
        result = []
        for frame in self._frames:
            field_value = frame.get_field_value(field_name)
            if field_value is not None:
                if value is None or field_value == value:
                    result.append(frame)
        return result
    
    # ========== 导出和序列化 ==========
    
    def to_dict(self) -> dict:
        """导出会话信息为字典"""
        return {
            "id": self._id,
            "state": self._state.value,
            "protocol_name": self._protocol.name if self._protocol else None,
            "data_source": self._raw_data_source,
            "data_size": len(self._raw_data),
            "frame_count": len(self._frames),
            "valid_frames": sum(1 for f in self._frames if f.is_valid),
            "warnings_count": len(self._warnings),
            "created_at": self._created_at.isoformat(),
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "config": {
                "enable_trace": self._config.enable_trace,
                "max_frames": self._config.max_frames
            }
        }
    
    def get_statistics(self) -> dict:
        """获取解析统计信息"""
        if not self._frames:
            return {
                "frame_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "total_bytes": len(self._raw_data),
                "parsed_bytes": 0,
                "parse_rate": 0.0
            }
        
        valid_count = sum(1 for f in self._frames if f.is_valid)
        parsed_bytes = sum(len(f.raw_data) for f in self._frames)
        
        return {
            "frame_count": len(self._frames),
            "valid_count": valid_count,
            "invalid_count": len(self._frames) - valid_count,
            "total_bytes": len(self._raw_data),
            "parsed_bytes": parsed_bytes,
            "parse_rate": parsed_bytes / len(self._raw_data) * 100 if self._raw_data else 0,
            "average_frame_size": parsed_bytes / len(self._frames) if self._frames else 0
        }
    
    def __repr__(self) -> str:
        return (f"AnalysisSession(id={self._id}, state={self._state.value}, "
                f"frames={len(self._frames)})")


class SessionManager:
    """
    会话管理器
    管理多个分析会话
    """
    
    def __init__(self, max_sessions: int = 10):
        """
        初始化会话管理器
        
        Args:
            max_sessions: 最大保留会话数
        """
        self._sessions: Dict[str, AnalysisSession] = {}
        self._current_session: Optional[AnalysisSession] = None
        self._max_sessions = max_sessions
        self._lock = threading.RLock()
    
    @property
    def current(self) -> Optional[AnalysisSession]:
        """当前会话"""
        return self._current_session
    
    @property
    def sessions(self) -> List[AnalysisSession]:
        """所有会话"""
        return list(self._sessions.values())
    
    def create_session(self, config: Optional[SessionConfig] = None) -> AnalysisSession:
        """
        创建新会话
        
        Args:
            config: 会话配置
            
        Returns:
            新创建的会话
        """
        with self._lock:
            session = AnalysisSession(config)
            self._sessions[session.id] = session
            self._current_session = session
            
            # 清理旧会话
            self._cleanup_old_sessions()
            
            return session
    
    def get_session(self, session_id: str) -> Optional[AnalysisSession]:
        """
        获取指定会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话对象，如果不存在返回 None
        """
        return self._sessions.get(session_id)
    
    def set_current(self, session_id: str) -> bool:
        """
        设置当前会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功
        """
        session = self._sessions.get(session_id)
        if session:
            self._current_session = session
            return True
        return False
    
    def remove_session(self, session_id: str) -> bool:
        """
        移除会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                if self._current_session and self._current_session.id == session_id:
                    self._current_session = None
                return True
            return False
    
    def _cleanup_old_sessions(self):
        """清理旧会话"""
        if len(self._sessions) <= self._max_sessions:
            return
        
        # 按创建时间排序，保留最新的
        sorted_sessions = sorted(
            self._sessions.values(),
            key=lambda s: s._created_at,
            reverse=True
        )
        
        # 删除超出限制的旧会话
        for session in sorted_sessions[self._max_sessions:]:
            if session != self._current_session:
                del self._sessions[session.id]
    
    def clear_all(self):
        """清除所有会话"""
        with self._lock:
            self._sessions.clear()
            self._current_session = None
