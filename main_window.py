# This Python file uses the following encoding: utf-8
"""
串口数据分析工具 - Fluent Design 主窗口
Version 2.0.0 - 完整功能版本
"""
import sys
import os
import json
import ctypes
import threading
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

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
from core.analysis_history_db import AnalysisHistoryDB
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
        self._abort_event = threading.Event()  # 线程安全的中止标志
    
    def abort(self):
        """请求中止解析（线程安全）"""
        self._abort_event.set()
    
    def is_aborted(self):
        """检查是否已请求中止（线程安全）"""
        return self._abort_event.is_set()
    
    def run(self):
        try:
            # 传递中止检查回调给解析器（如果解析器支持）
            result = self.parser.parse(self.hex_string)
            if not self._abort_event.is_set():
                self.finished.emit(result)
        except Exception as e:
            if not self._abort_event.is_set():
                self.error.emit(str(e))


class MainWindow(FluentWindow):
    """Fluent Design 主窗口"""
    
    # 窗口状态配置路径
    _window_state_path = os.path.join(
        os.path.expanduser('~'), '.serialdatacompare', 'window_state.json'
    )
    # 用户偏好配置路径
    _user_prefs_path = os.path.join(
        os.path.expanduser('~'), '.serialdatacompare', 'user_prefs.json'
    )
    
    def __init__(self):
        super().__init__()
        
        # 当前协议配置
        self.current_protocol: Optional[ProtocolConfig] = None
        # 解析结果
        self.parse_result: Optional[ParseResult] = None
        # 解析线程
        self.parse_thread: Optional[ParseThread] = None
        # 解析状态
        self._is_parsing = False
        # 历史记录管理器
        self.protocol_history = ProtocolHistory()
        # 分析历史记录管理器（SQLite）
        self.analysis_history = AnalysisHistoryDB()
        # 颜色配置管理器
        self.color_config = ColorConfig()
        # 项目管理器
        self.project_manager = ProjectManager()
        # 日志管理器
        self.logger = Logger()
        
        # 加载用户偏好设置
        self._user_prefs = self._load_user_prefs()
        
        # 一次性从旧JSON迁移（如果存在，需在 logger 之后）
        self._migrate_json_history()
        
        # 启动健康检查
        self._startup_health_check()
        
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
        
        # 根据屏幕大小自适应窗口 + 恢复上次位置
        self._init_window_geometry()
    
    def _init_window_geometry(self):
        """根据屏幕自适应窗口大小，并恢复上次保存的位置"""
        # 尝试加载上次的窗口位置
        if not self._load_window_geometry():
            # 没有保存的状态，使用自适应大小
            screen = QApplication.primaryScreen().availableGeometry()
            default_w = min(int(screen.width() * 0.85), 1600)
            default_h = min(int(screen.height() * 0.85), 1000)
            # 居中显示
            x = (screen.width() - default_w) // 2
            y = (screen.height() - default_h) // 2
            self.setGeometry(x, y, default_w, default_h)
    
    def _save_window_geometry(self):
        """保存窗口几何信息到配置文件"""
        try:
            config = {
                "x": self.x(), "y": self.y(),
                "width": self.width(), "height": self.height(),
                "maximized": self.isMaximized()
            }
            from utils import atomic_write_json
            atomic_write_json(self._window_state_path, config)
        except Exception as e:
            self.logger.warning(f"保存窗口状态失败: {e}")
    
    def _load_window_geometry(self) -> bool:
        """恢复上次的窗口位置，并验证是否还在屏幕范围内"""
        try:
            if not os.path.exists(self._window_state_path):
                return False
            with open(self._window_state_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if not config:
                return False
            if config.get("maximized"):
                self.showMaximized()
                return True
            # 验证位置是否在当前屏幕范围内
            screen = QApplication.primaryScreen().availableGeometry()
            x = max(0, min(config.get("x", 0), screen.width() - 200))
            y = max(0, min(config.get("y", 0), screen.height() - 200))
            w = min(config.get("width", 1200), screen.width())
            h = min(config.get("height", 800), screen.height())
            self.setGeometry(x, y, w, h)
            return True
        except Exception:
            return False
    
    def _load_user_prefs(self) -> dict:
        """加载用户偏好设置"""
        try:
            if os.path.exists(self._user_prefs_path):
                with open(self._user_prefs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_user_prefs(self):
        """保存用户偏好设置"""
        try:
            from utils import atomic_write_json
            atomic_write_json(self._user_prefs_path, self._user_prefs)
        except Exception as e:
            self.logger.warning(f"保存用户偏好失败: {e}")
    
    def get_pref(self, key: str, default=None):
        """获取用户偏好"""
        return self._user_prefs.get(key, default)
    
    def set_pref(self, key: str, value):
        """设置并保存用户偏好"""
        self._user_prefs[key] = value
        self._save_user_prefs()
    
    def init_navigation(self):
        """初始化导航栏"""
        # 创建子界面
        self.project_interface = ProjectInterface(self.project_manager, self)
        self.protocol_interface = ProtocolInterface(self.protocol_history, self)
        self.analysis_interface = AnalysisInterface(self.analysis_history, self)
        self.frame_detail_interface = FrameDetailInterface(color_config=self.color_config, parent=self)
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
        self.settings_interface.init_prefs(self)
        
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
    
    def _set_parsing_state(self, parsing: bool):
        """统一管理解析状态，禁用/启用所有可能冲突的操作"""
        self._is_parsing = parsing
        # 禁用/启用分析按钮
        self.analysis_interface.set_analyzing(parsing)
        # 禁用/启用项目管理界面中的协议选择
        self.project_interface.setEnabled(not parsing)
    
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
        if self._is_parsing:
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
        
        # 智能预处理输入（清洗日志格式等）
        from utils.helpers import preprocess_hex_input
        cleaned = preprocess_hex_input(hex_data)
        if cleaned != hex_data.strip():
            self.logger.info("输入数据已自动清洗（移除日志标记和格式化）")
        
        # 禁用所有可能冲突的操作
        self._set_parsing_state(True)
        
        # 创建解析器
        parser = DataParser(self.current_protocol)
        
        # 创建并启动解析线程
        self.parse_thread = ParseThread(parser, cleaned)
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
        
        # 重新启用所有操作
        self._set_parsing_state(False)
        
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
        # 重新启用所有操作
        self._set_parsing_state(False)
        
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
            
            # 根据用户偏好决定是否自动切换到帧详情页面
            if self.get_pref('auto_switch_to_detail', True):
                self.switchTo(self.frame_detail_interface)
    
    def on_theme_changed(self, theme: str):
        """主题改变"""
        if theme == "浅色":
            setTheme(Theme.LIGHT)
        elif theme == "深色":
            setTheme(Theme.DARK)
        elif theme == "自动":
            setTheme(Theme.AUTO)
        
        # 刷新各界面的自定义样式以适配新主题
        self._refresh_all_styles()
        
        self.logger.info(f"主题已切换: {theme}")
    
    def _refresh_all_styles(self):
        """刷新所有界面的自定义样式（主题切换后调用）
        
        注: 使用 setTextColor 设置的 FluentLabelBase 控件会自动刷新，
        仅含 background/padding 的复杂样式和非 FluentLabel 控件需要手动刷新。
        """
        for interface in (self.analysis_interface, self.frame_detail_interface):
            if hasattr(interface, '_refresh_styles'):
                try:
                    interface._refresh_styles()
                except Exception:
                    pass  # 样式刷新失败不影响功能
    
    def _migrate_json_history(self):
        """一次性将旧 JSON 历史记录迁移到 SQLite，迁移后重命名为 .bak"""
        json_path = os.path.expanduser('~/.serialdatacompare/analysis_history.json')
        if not os.path.exists(json_path):
            return
        try:
            count = self.analysis_history.migrate_from_json(json_path)
            if count > 0:
                bak_path = json_path + '.bak'
                os.rename(json_path, bak_path)
                self.logger.info(f"已从 JSON 迁移 {count} 条历史记录到 SQLite，原文件已备份为 .bak")
            else:
                # JSON 为空或格式异常，直接归档
                os.rename(json_path, json_path + '.bak')
                self.logger.info("JSON 历史记录为空，已归档为 .bak")
        except Exception as e:
            self.logger.warning(f"JSON 历史记录迁移失败（不影响使用）: {e}")

    def _startup_health_check(self):
        """程序启动时检查环境"""
        config_dir = os.path.expanduser('~/.serialdatacompare')
        issues = []
        
        # 检查配置目录可写
        os.makedirs(config_dir, exist_ok=True)
        if not os.access(config_dir, os.W_OK):
            issues.append(f"配置目录不可写: {config_dir}")
        
        # 检查关键配置文件完整性（不再检查 analysis_history.json，已迁移至 SQLite）
        for config_name in ['color_config.json', 'projects.json']:
            config_file = os.path.join(config_dir, config_name)
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    issues.append(f"配置文件损坏: {config_name}（将使用默认值）")
        
        if issues:
            log = logging.getLogger(__name__)
            log.warning("启动检查发现问题:\n" + "\n".join(issues))
    
    def closeEvent(self, event):
        """窗口关闭事件，清理资源"""
        # 保存窗口状态
        self._save_window_geometry()
        
        # 安全清理解析线程
        if self.parse_thread is not None and self.parse_thread.isRunning():
            # 先断开信号，防止线程结束后回调已销毁的 Qt 对象
            try:
                self.parse_thread.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.parse_thread.error.disconnect()
            except (RuntimeError, TypeError):
                pass
            
            self.parse_thread.abort()
            # 最多等 3 秒
            if not self.parse_thread.wait(3000):
                self.logger.warning("解析线程未能在 3 秒内结束，强制终止")
                self.parse_thread.terminate()
                self.parse_thread.wait(1000)
        
        self.logger.info("程序正常退出")
        super().closeEvent(event)


def main():
    """主函数"""
    # Windows 高DPI适配设置 - 必须在创建 QApplication 之前设置
    if sys.platform == 'win32':
        # Windows DPI 感知设置
        try:
            # Windows 10 1607+ 支持 Per-Monitor DPI Awareness V2
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Windows 8.1 支持 Per-Monitor DPI Awareness
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                try:
                    # Windows Vista+ 支持 System DPI Awareness
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
    
    # 启用高DPI缩放
    os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '1')
    # 使用高DPI图标
    os.environ.setdefault('QT_SCALE_FACTOR_ROUNDING_POLICY', 'Round')
    # 自动检测缩放因子
    os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '1')
    
    # Windows 中文输入法支持
    if sys.platform == 'win32':
        # Windows 使用系统默认输入法 - 不设置 QT_IM_MODULE，让系统自动处理
        # 这样可以正常使用搜狗、微软等中文输入法
        pass
    else:
        # Linux 支持 fcitx/ibus 等中文输入法
        os.environ.setdefault('QT_IM_MODULE', 'fcitx')
    
    # 设置高DPI缩放策略
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.Round
    )
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()