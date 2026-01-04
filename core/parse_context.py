# -*- coding: utf-8 -*-
"""
ParseContext - 解析上下文
用于追踪解析过程中的状态，便于调试和错误定位
"""

from typing import List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class ParseStage(Enum):
    """解析阶段"""
    INIT = "初始化"
    FIND_HEADER = "查找帧头"
    VALIDATE_LENGTH = "验证长度"
    PARSE_FIELDS = "解析字段"
    VERIFY_CHECKSUM = "校验验证"
    COMPLETE = "完成"
    ERROR = "错误"


@dataclass
class ParseWarning:
    """解析警告"""
    stage: ParseStage
    message: str
    position: int
    field_name: Optional[str] = None
    details: Optional[dict] = None


@dataclass
class ParseEvent:
    """解析事件记录"""
    timestamp: float
    stage: ParseStage
    message: str
    position: int
    data_snapshot: Optional[bytes] = None
    
    def format(self) -> str:
        """格式化事件为可读字符串"""
        pos_str = f"@{self.position}" if self.position >= 0 else ""
        return f"[{self.stage.value}]{pos_str} {self.message}"


class ParseContext:
    """
    解析上下文
    追踪解析过程，收集警告和调试信息
    """
    
    def __init__(self, raw_data: bytes, enable_trace: bool = False):
        """
        初始化解析上下文
        
        Args:
            raw_data: 原始数据
            enable_trace: 是否启用详细追踪（调试用）
        """
        self._raw_data = raw_data
        self._position = 0
        self._stage = ParseStage.INIT
        self._enable_trace = enable_trace
        
        # 状态追踪
        self._warnings: List[ParseWarning] = []
        self._events: List[ParseEvent] = []
        self._start_time = time.time()
        
        # 帧信息
        self._current_frame_index = 0
        self._frames_parsed = 0
        self._bytes_consumed = 0
        
        # 错误状态
        self._has_error = False
        self._error_message = ""
        
    # ========== 属性 ==========
    
    @property
    def position(self) -> int:
        """当前解析位置"""
        return self._position
    
    @property
    def remaining(self) -> int:
        """剩余字节数"""
        return len(self._raw_data) - self._position
    
    @property
    def stage(self) -> ParseStage:
        """当前解析阶段"""
        return self._stage
    
    @property
    def warnings(self) -> List[ParseWarning]:
        """所有警告"""
        return self._warnings.copy()
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self._warnings) > 0
    
    @property
    def has_error(self) -> bool:
        """是否有错误"""
        return self._has_error
    
    @property
    def error_message(self) -> str:
        """错误信息"""
        return self._error_message
    
    @property
    def frames_parsed(self) -> int:
        """已解析帧数"""
        return self._frames_parsed
    
    @property
    def elapsed_ms(self) -> float:
        """已用时间（毫秒）"""
        return (time.time() - self._start_time) * 1000
    
    # ========== 状态控制 ==========
    
    def set_stage(self, stage: ParseStage, message: str = ""):
        """设置解析阶段"""
        self._stage = stage
        if self._enable_trace:
            self._add_event(stage, message or f"进入阶段: {stage.value}")
    
    def advance(self, bytes_count: int):
        """推进位置"""
        self._position += bytes_count
        self._bytes_consumed += bytes_count
    
    def seek(self, position: int):
        """设置位置"""
        self._position = position
    
    def frame_completed(self):
        """标记帧完成"""
        self._frames_parsed += 1
        self._current_frame_index += 1
    
    # ========== 数据读取 ==========
    
    def peek(self, size: int) -> Optional[bytes]:
        """
        预览数据（不推进位置）
        
        Args:
            size: 读取字节数
            
        Returns:
            字节数据，如果不足返回 None
        """
        if self._position + size > len(self._raw_data):
            return None
        return self._raw_data[self._position:self._position + size]
    
    def read(self, size: int) -> Optional[bytes]:
        """
        读取数据并推进位置
        
        Args:
            size: 读取字节数
            
        Returns:
            字节数据，如果不足返回 None
        """
        data = self.peek(size)
        if data is not None:
            self.advance(size)
        return data
    
    def read_at(self, offset: int, size: int) -> Optional[bytes]:
        """
        在指定位置读取数据（不改变当前位置）
        
        Args:
            offset: 读取位置
            size: 读取字节数
            
        Returns:
            字节数据，如果不足返回 None
        """
        if offset + size > len(self._raw_data):
            return None
        return self._raw_data[offset:offset + size]
    
    def get_slice(self, start: int, end: int) -> bytes:
        """获取数据切片"""
        return self._raw_data[start:end]
    
    def find_pattern(self, pattern: bytes, start: Optional[int] = None) -> int:
        """
        查找模式
        
        Args:
            pattern: 要查找的模式
            start: 起始位置（默认为当前位置）
            
        Returns:
            找到的位置，未找到返回 -1
        """
        search_start = start if start is not None else self._position
        return self._raw_data.find(pattern, search_start)
    
    # ========== 警告和错误 ==========
    
    def add_warning(self, message: str, field_name: Optional[str] = None,
                    details: Optional[dict] = None):
        """添加警告"""
        warning = ParseWarning(
            stage=self._stage,
            message=message,
            position=self._position,
            field_name=field_name,
            details=details
        )
        self._warnings.append(warning)
        
        if self._enable_trace:
            self._add_event(self._stage, f"警告: {message}")
    
    def set_error(self, message: str):
        """设置错误"""
        self._has_error = True
        self._error_message = message
        self._stage = ParseStage.ERROR
        
        if self._enable_trace:
            self._add_event(ParseStage.ERROR, message)
    
    # ========== 追踪 ==========
    
    def trace(self, message: str, data_snapshot: Optional[bytes] = None):
        """
        记录追踪信息（仅在启用追踪时有效）
        
        Args:
            message: 追踪消息
            data_snapshot: 数据快照
        """
        if self._enable_trace:
            self._add_event(self._stage, message, data_snapshot)
    
    def _add_event(self, stage: ParseStage, message: str, 
                   data_snapshot: Optional[bytes] = None):
        """内部：添加事件"""
        event = ParseEvent(
            timestamp=time.time(),
            stage=stage,
            message=message,
            position=self._position,
            data_snapshot=data_snapshot
        )
        self._events.append(event)
    
    # ========== 报告生成 ==========
    
    def get_summary(self) -> dict:
        """获取解析摘要"""
        return {
            "total_bytes": len(self._raw_data),
            "bytes_consumed": self._bytes_consumed,
            "frames_parsed": self._frames_parsed,
            "warnings_count": len(self._warnings),
            "has_error": self._has_error,
            "error_message": self._error_message,
            "elapsed_ms": self.elapsed_ms,
            "final_stage": self._stage.value
        }
    
    def format_warnings(self) -> str:
        """格式化所有警告"""
        if not self._warnings:
            return "无警告"
        
        lines = [f"共 {len(self._warnings)} 条警告:"]
        for i, w in enumerate(self._warnings, 1):
            field_info = f" [{w.field_name}]" if w.field_name else ""
            lines.append(f"  {i}. @{w.position}{field_info} {w.message}")
        return "\n".join(lines)
    
    def format_trace(self) -> str:
        """格式化追踪日志"""
        if not self._events:
            return "追踪未启用或无事件"
        
        lines = [f"解析追踪 (共 {len(self._events)} 事件):"]
        for event in self._events:
            lines.append(f"  {event.format()}")
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (f"ParseContext(pos={self._position}, stage={self._stage.value}, "
                f"frames={self._frames_parsed}, warnings={len(self._warnings)})")


class ParseContextManager:
    """
    解析上下文管理器
    用于 with 语句自动管理上下文生命周期
    """
    
    def __init__(self, raw_data: bytes, enable_trace: bool = False):
        self.context = ParseContext(raw_data, enable_trace)
    
    def __enter__(self) -> ParseContext:
        self.context.set_stage(ParseStage.INIT, "开始解析")
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.context.set_error(str(exc_val))
        elif not self.context.has_error:
            self.context.set_stage(ParseStage.COMPLETE, "解析完成")
        return False  # 不抑制异常
