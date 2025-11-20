# This Python file uses the following encoding: utf-8
"""
串口数据分析工具 - Fluent Design 主窗口
Version 2.0.0 - 完整功能版本
"""
import sys
import os
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QThread, Signal

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition,
    setTheme, Theme, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)

from models import (
    ProtocolConfig, FieldDefinition, ChecksumConfig,
    ChecksumType, ChecksumPosition, FieldType, ParseResult
)
from core import DataParser, ProtocolManager, ColorConfig
from core.protocol_history import ProtocolHistory
from core.analysis_history import AnalysisHistory
from utils import export_to_txt, export_to_csv, Logger, LogLevel

# 导入 Fluent 界面组件
from ui.fluent_protocol_interface import ProtocolInterface
from ui.fluent_analysis_interface import AnalysisInterface
from ui.fluent_frame_detail_interface import FrameDetailInterface
from ui.fluent_log_interface import LogInterface
from ui.fluent_settings_interface import SettingsInterface


class ParseThread(QThread):
    """解析线程"""
    finished = Signal(ParseResult)
    error = Signal(str)
    
    def __init__(self, parser: DataParser, hex_string: str):
        super().__init__()
        self.parser = parser
        self.hex_string = hex_string
    
    def run(self):
        try:
            result = self.parser.parse(self.hex_string)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(FluentWindow):
    """Fluent Design 主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 当前协议配置
        self.current_protocol: Optional[ProtocolConfig] = None
        # 解析结果
        self.parse_result: Optional[ParseResult] = None
        # 解析线程
        self.parse_thread: Optional[ParseThread] = None
        # 历史记录管理器
        self.protocol_history = ProtocolHistory()
        # 分析历史记录管理器
        self.analysis_history = AnalysisHistory()
        # 颜色配置管理器
        self.color_config = ColorConfig()
        # 日志管理器
        self.logger = Logger()
        
        # 初始化界面
        self.init_window()
        self.init_navigation()
        self.init_protocol()
        
        # 记录启动日志
        self.logger.info("串口数据分析工具 v2.0 启动成功")
    
    def init_window(self):
        """初始化窗口"""
        self.resize(1600, 1000)
        self.setWindowTitle('串口数据分析工具 v2.0 - Fluent Design')
        
        # 设置默认主题 - 使用 LIGHT 而不是 AUTO 避免初始化问题
        setTheme(Theme.LIGHT)
        
        # 确保窗口样式正确应用
        self.setStyleSheet("background-color: transparent;")
    
    def init_navigation(self):
        """初始化导航栏"""
        # 创建子界面
        self.protocol_interface = ProtocolInterface(self)
        self.analysis_interface = AnalysisInterface(self)
        self.frame_detail_interface = FrameDetailInterface(self)
        self.log_interface = LogInterface(self)
        self.settings_interface = SettingsInterface(self)
        
        # 连接信号
        self.setup_connections()
        
        # 添加子界面到导航
        self.addSubInterface(
            self.protocol_interface,
            FIF.DOCUMENT,
            '协议配置',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.analysis_interface,
            FIF.SEARCH,
            '数据分析',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.frame_detail_interface,
            FIF.LABEL,
            '帧详情',
            NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.log_interface,
            FIF.HISTORY,
            '日志',
            NavigationItemPosition.TOP
        )
        
        # 设置界面添加到底部
        self.addSubInterface(
            self.settings_interface,
            FIF.SETTING,
            '设置',
            NavigationItemPosition.BOTTOM
        )
    
    def setup_connections(self):
        """设置信号连接"""
        # 协议配置界面信号
        self.protocol_interface.protocol_loaded.connect(self.on_protocol_loaded)
        self.protocol_interface.protocol_saved.connect(self.on_protocol_saved)
        
        # 数据分析界面信号
        self.analysis_interface.analysis_started.connect(self.on_analysis_started)
        self.analysis_interface.frame_selected.connect(self.on_frame_selected)
        
        # 设置界面信号
        self.settings_interface.theme_changed.connect(self.on_theme_changed)
        
        # 日志信号
        self.logger.log_added.connect(self.log_interface.add_log)
    
    def init_protocol(self):
        """初始化协议配置"""
        self.logger.debug("正在初始化协议配置...")
        
        # 尝试加载示例协议
        example_path = os.path.join(os.path.dirname(__file__), 'protocol_example.json')
        if os.path.exists(example_path):
            try:
                self.current_protocol = ProtocolManager.load_protocol(example_path)
                self.logger.info(f"已加载示例协议：{example_path}")
                # 更新界面
                self.protocol_interface.load_protocol_data(self.current_protocol)
                self.analysis_interface.set_protocol(self.current_protocol)
            except Exception as e:
                self.logger.warning(f"加载示例协议失败：{str(e)}")
        
        # 如果加载失败，使用默认协议
        if self.current_protocol is None:
            self.current_protocol = ProtocolManager.get_default_protocol()
            self.logger.info("已加载默认协议配置")
            try:
                self.protocol_interface.load_protocol_data(self.current_protocol)
                self.analysis_interface.set_protocol(self.current_protocol)
            except Exception as e:
                self.logger.error(f"加载默认协议失败：{str(e)}")
    
    def on_protocol_loaded(self, protocol: ProtocolConfig):
        """协议加载完成"""
        self.current_protocol = protocol
        self.logger.info(f"协议已加载: {protocol.protocol_name}")
        
        # 更新分析界面
        self.analysis_interface.set_protocol(protocol)
        
        # 添加到历史记录（如果有文件路径）
        if hasattr(protocol, 'file_path') and protocol.file_path:
            self.protocol_history.add_protocol(protocol.file_path, protocol.protocol_name)
        
        # 显示成功消息
        InfoBar.success(
            title="成功",
            content=f"协议 '{protocol.protocol_name}' 已加载",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def on_protocol_saved(self, protocol: ProtocolConfig):
        """协议保存完成"""
        self.current_protocol = protocol
        self.logger.info(f"协议已保存: {protocol.protocol_name}")
        
        # 添加到历史记录（如果有文件路径）
        if hasattr(protocol, 'file_path') and protocol.file_path:
            self.protocol_history.add_protocol(protocol.file_path, protocol.protocol_name)
        
        # 更新分析界面
        self.analysis_interface.set_protocol(protocol)
    
    def on_analysis_started(self, hex_data: str):
        """开始数据分析"""
        if not self.current_protocol:
            InfoBar.error(
                title='错误',
                content='请先配置或加载协议',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.logger.error("分析失败: 未配置协议")
            return
        
        self.logger.info(f"开始分析数据: {hex_data[:50]}...")
        
        # 创建解析器
        parser = DataParser(self.current_protocol)
        
        # 创建并启动解析线程
        self.parse_thread = ParseThread(parser, hex_data)
        self.parse_thread.finished.connect(self.on_parse_finished)
        self.parse_thread.error.connect(self.on_parse_error)
        self.parse_thread.start()
        
        # 显示分析中
        InfoBar.info(
            title='分析中',
            content='正在解析数据...',
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        )
    
    def on_parse_finished(self, result: ParseResult):
        """解析完成"""
        self.parse_result = result
        
        # 更新分析界面
        self.analysis_interface.show_result(result)
        
        # 添加到历史记录
        if self.current_protocol:
            # 统计有效和错误帧数
            valid_frames = sum(1 for frame in result.frames if not frame.has_error)
            error_frames = sum(1 for frame in result.frames if frame.has_error)
            
            # 转换帧详情格式
            frame_details = [
                {
                    'frame_number': frame.frame_number,
                    'has_error': frame.has_error,
                    'checksum_valid': frame.checksum_valid,
                    'raw_data_hex': frame.raw_data.hex() if isinstance(frame.raw_data, bytes) else str(frame.raw_data)
                }
                for frame in result.frames
            ]
            
            self.analysis_history.add_analysis(
                protocol_name=self.current_protocol.protocol_name,
                input_data=result.input_data,
                total_frames=len(result.frames),
                valid_frames=valid_frames,
                error_frames=error_frames,
                frame_details=frame_details
            )
        
        self.logger.info(f"分析完成: 找到 {len(result.frames)} 个数据帧")
        
        # 显示成功消息
        InfoBar.success(
            title="成功",
            content=f"分析完成，找到 {len(result.frames)} 个数据帧",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def on_parse_error(self, error: str):
        """解析错误"""
        InfoBar.error(
            title='解析错误',
            content=error,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        self.logger.error(f"解析错误: {error}")
    
    def on_frame_selected(self, frame_index: int):
        """帧被选中"""
        if self.parse_result and 0 <= frame_index < len(self.parse_result.frames):
            frame = self.parse_result.frames[frame_index]
            
            # 更新帧详情界面
            self.frame_detail_interface.show_frame(frame)
            
            # 自动切换到帧详情页面
            self.switchTo(self.frame_detail_interface)
    
    def on_theme_changed(self, theme: str):
        """主题改变"""
        if theme == "浅色":
            setTheme(Theme.LIGHT)
        elif theme == "深色":
            setTheme(Theme.DARK)
        elif theme == "自动":
            setTheme(Theme.AUTO)
        
        self.logger.info(f"主题已切换: {theme}")


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
