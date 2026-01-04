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
from core.project_manager import ProjectManager
from utils import export_to_txt, export_to_csv, Logger, LogLevel

# 导入 Fluent 界面组件
from ui.fluent_protocol_interface import ProtocolInterface
from ui.fluent_analysis_interface import AnalysisInterface
from ui.fluent_frame_detail_interface import FrameDetailInterface
from ui.fluent_log_interface import LogInterface
from ui.fluent_settings_interface import SettingsInterface
from ui.fluent_project_interface import ProjectInterface
from ui.fluent_tools_interface import ToolsInterface


class ParseThread(QThread):
    """解析线程"""
    finished = Signal(ParseResult)
    error = Signal(str)
    
    def __init__(self, parser: DataParser, hex_string: str):
        super().__init__()
        self.parser = parser
        self.hex_string = hex_string
        self._abort = False
    
    def abort(self):
        """请求中止解析"""
        self._abort = True
    
    def is_aborted(self):
        """检查是否已请求中止"""
        return self._abort
    
    def run(self):
        try:
            # 传递中止检查回调给解析器（如果解析器支持）
            result = self.parser.parse(self.hex_string)
            if not self._abort:
                self.finished.emit(result)
        except Exception as e:
            if not self._abort:
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
        # 项目管理器
        self.project_manager = ProjectManager()
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
        self.setWindowTitle('串口数据分析工具 v2.0 - Fluent Design')
        
        # 设置默认主题 - 使用 LIGHT 而不是 AUTO 避免初始化问题
        setTheme(Theme.LIGHT)
        
        # 确保窗口样式正确应用
        self.setStyleSheet("background-color: transparent;")
        
        # 启动时最大化窗口
        self.showMaximized()
    
    def init_navigation(self):
        """初始化导航栏"""
        # 创建子界面
        self.project_interface = ProjectInterface(self.project_manager, self)
        self.protocol_interface = ProtocolInterface(self.protocol_history, self)
        self.analysis_interface = AnalysisInterface(self.analysis_history, self)
        self.frame_detail_interface = FrameDetailInterface(self)
        self.log_interface = LogInterface(self)
        self.settings_interface = SettingsInterface(self)
        self.tools_interface = ToolsInterface(self)
        
        # 连接信号
        self.setup_connections()
        
        # 添加子界面到导航
        self.addSubInterface(
            self.project_interface,
            FIF.FOLDER,
            '项目管理',
            NavigationItemPosition.TOP
        )
        
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
        
        self.addSubInterface(
            self.tools_interface,
            FIF.APPLICATION,
            '小工具',
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
        # 项目管理界面信号
        self.project_interface.protocol_selected.connect(self.on_project_protocol_selected)
        
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
    
    def on_project_protocol_selected(self, protocol_path: str):
        """从项目管理中选择协议时触发"""
        self.logger.info(f"从项目加载协议: {protocol_path}")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(protocol_path):
                raise FileNotFoundError(f"协议文件不存在: {protocol_path}")
            
            # 加载协议（带验证）
            protocol, warning_msg = ProtocolManager.load_protocol(protocol_path, validate=True)
            
            if protocol is None:
                raise ValueError(warning_msg or "加载协议失败")
            
            # 如果有验证警告，显示提示
            if warning_msg:
                InfoBar.warning(
                    title="协议验证警告",
                    content=warning_msg[:100] + "..." if len(warning_msg) > 100 else warning_msg,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            
            # 更新协议配置界面，同时设置当前文件路径
            self.protocol_interface.set_current_file_path(protocol_path)
            self.protocol_interface.load_protocol_data(protocol)
            
            # 切换到协议配置界面
            self.switchTo(self.protocol_interface)
            
            # 触发协议加载完成的处理
            self.on_protocol_loaded(protocol)
            
        except Exception as e:
            self.logger.error(f"加载协议失败: {str(e)}")
            InfoBar.error(
                title="加载失败",
                content=f"无法加载协议: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def init_protocol(self):
        """初始化协议配置"""
        self.logger.debug("正在初始化协议配置...")
        
        # 尝试加载示例协议
        example_path = os.path.join(os.path.dirname(__file__), 'protocol_example.json')
        if os.path.exists(example_path):
            try:
                self.current_protocol = ProtocolManager.load_protocol_simple(example_path)
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
        
        # 清空之前的解析结果
        self.parse_result = None
        self.analysis_interface.clear_results()
        
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
        
        # 清空之前的解析结果
        self.parse_result = None
        self.analysis_interface.clear_results()
        
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
        
        # 检查是否有正在运行的解析线程
        if self.parse_thread is not None and self.parse_thread.isRunning():
            InfoBar.warning(
                title='警告',
                content='解析正在进行中，请等待完成',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        self.logger.info(f"开始分析数据: {hex_data[:50]}...")
        
        # 禁用分析按钮，防止重复点击
        self.analysis_interface.set_analyzing(True)
        
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
        
        # 重新启用分析按钮
        self.analysis_interface.set_analyzing(False)
        
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
        # 重新启用分析按钮
        self.analysis_interface.set_analyzing(False)
        
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
    
    def closeEvent(self, event):
        """窗口关闭事件，清理资源"""
        # 等待解析线程结束
        if self.parse_thread is not None and self.parse_thread.isRunning():
            self.parse_thread.quit()
            self.parse_thread.wait(2000)  # 最多等待2秒
            if self.parse_thread.isRunning():
                self.parse_thread.terminate()
                self.parse_thread.wait()
        
        self.logger.info("程序正常退出")
        super().closeEvent(event)


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 设置输入法环境变量（支持fcitx等中文输入法）
    # 这需要在创建QApplication之前设置
    os.environ.setdefault('QT_IM_MODULE', 'fcitx')
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
