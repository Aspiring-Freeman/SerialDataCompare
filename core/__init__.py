# -*- coding: utf-8 -*-
"""
核心模块初始化
"""

from .checksum import ChecksumCalculator, ChecksumValidator, calculate_checksum, validate_checksum
from .parser import DataParser
from .protocol_manager import ProtocolManager
from .color_config import ColorConfig, ColorConfigValidator, ColorValidationError
from .protocol_validator import ProtocolValidator, ValidationError, ValidationSeverity
from .analysis_history import AnalysisHistory
from .analysis_history_db import AnalysisHistoryDB
from .exceptions import (
    SerialDataCompareError,
    ProtocolError, ProtocolLoadError, ProtocolValidationError, ProtocolConversionError,
    ParseError, FrameNotFoundError, FrameParseError, FieldParseError, DataTruncatedError,
    ChecksumError, ChecksumMismatchError, ChecksumConfigError, ChecksumRangeError,
    ConfigError, ConfigLoadError, ConfigSaveError,
    DataError, InvalidHexDataError, DataLengthError,
    format_exception_chain, wrap_exception
)
from .parse_context import ParseContext, ParseContextManager, ParseStage, ParseWarning
from .analysis_session import AnalysisSession, SessionManager, SessionState, SessionResult, SessionConfig
from .analysis_controller import AnalysisController

__all__ = [
    # 校验
    'ChecksumCalculator',
    'ChecksumValidator',
    'calculate_checksum',
    'validate_checksum',
    # 解析
    'DataParser',
    'ParseContext',
    'ParseContextManager',
    'ParseStage',
    'ParseWarning',
    # 协议
    'ProtocolManager',
    'ProtocolValidator',
    'ValidationError',
    'ValidationSeverity',
    # 会话
    'AnalysisSession',
    'SessionManager',
    'SessionState',
    'SessionResult',
    'SessionConfig',
    # 控制器
    'AnalysisController',
    # 历史
    'AnalysisHistory',
    'AnalysisHistoryDB',
    # 配置
    'ColorConfig',
    'ColorConfigValidator',
    'ColorValidationError',
    # 异常
    'SerialDataCompareError',
    'ProtocolError',
    'ProtocolLoadError',
    'ProtocolValidationError',
    'ProtocolConversionError',
    'ParseError',
    'FrameNotFoundError',
    'FrameParseError',
    'FieldParseError',
    'DataTruncatedError',
    'ChecksumError',
    'ChecksumMismatchError',
    'ChecksumConfigError',
    'ChecksumRangeError',
    'ConfigError',
    'ConfigLoadError',
    'ConfigSaveError',
    'DataError',
    'InvalidHexDataError',
    'DataLengthError',
    'format_exception_chain',
    'wrap_exception',
]
