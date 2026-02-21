# This Python file uses the following encoding: utf-8
"""
日志管理器 - 用于记录程序运行日志
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor

from utils.theme_helper import ThemeHelper as TH


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Logger(QObject):
    """日志管理器"""
    # 信号：当有新日志时触发
    log_added = Signal(str, str)  # (level, message)
    
    def __init__(self):
        super().__init__()
        self.logs = []  # 存储所有日志
        self.enabled = True
        
        # 日志级别对应的颜色 (动态获取，支持主题切换)
        # 注意: level_colors 已改为通过 TH.log_color_map() 动态获取
    
    def _format_log(self, level: LogLevel, message: str) -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        color_map = TH.log_color_map()
        color = color_map.get(level.value, TH.info_log_color())
        
        # 使用 HTML 格式化，带颜色和时间戳
        html_log = f'<span style="color: {color};">[{timestamp}] [{level.value}] {message}</span>'
        return html_log
    
    def _log(self, level: LogLevel, message: str):
        """内部日志记录方法"""
        if not self.enabled:
            return
        
        formatted_log = self._format_log(level, message)
        self.logs.append((level, formatted_log))
        
        # 发送信号
        self.log_added.emit(level.value, formatted_log)
    
    def debug(self, message: str):
        """记录 DEBUG 级别日志"""
        self._log(LogLevel.DEBUG, message)
    
    def info(self, message: str):
        """记录 INFO 级别日志"""
        self._log(LogLevel.INFO, message)
    
    def warning(self, message: str):
        """记录 WARNING 级别日志"""
        self._log(LogLevel.WARNING, message)
    
    def error(self, message: str):
        """记录 ERROR 级别日志"""
        self._log(LogLevel.ERROR, message)
    
    def clear(self):
        """清空所有日志"""
        self.logs.clear()
        self.info("日志已清空")
    
    def get_logs(self, level: Optional[LogLevel] = None) -> list:
        """
        获取日志
        
        Args:
            level: 如果指定，只返回该级别的日志；否则返回所有日志
        
        Returns:
            日志列表
        """
        if level is None:
            return [log[1] for log in self.logs]
        else:
            return [log[1] for log in self.logs if log[0] == level]
    
    def export_to_text(self) -> str:
        """导出纯文本格式的日志（不含 HTML 标签）"""
        from html.parser import HTMLParser
        
        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.strict = False
                self.convert_charrefs = True
                self.text = []
            
            def handle_data(self, d):
                self.text.append(d)
            
            def get_data(self):
                return ''.join(self.text)
        
        plain_logs = []
        for level, html_log in self.logs:
            stripper = MLStripper()
            stripper.feed(html_log)
            plain_logs.append(stripper.get_data())
        
        return '\n'.join(plain_logs)
    
    def set_enabled(self, enabled: bool):
        """启用或禁用日志记录"""
        self.enabled = enabled
        if enabled:
            self.info("日志记录已启用")
        else:
            self.info("日志记录已禁用")
