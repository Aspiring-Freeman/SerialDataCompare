# This Python file uses the following encoding: utf-8
"""
串口数据分析工具 - Fluent Design 简化测试版本
"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition,
    setTheme, Theme, FluentIcon as FIF,
    PushButton, LineEdit, TextEdit, CardWidget,
    TitleLabel, BodyLabel
)


class SimpleInterface(QWidget):
    """简单的测试界面"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(f"interface_{title}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 卡片
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        
        # 标题
        title_label = TitleLabel(title)
        card_layout.addWidget(title_label)
        
        # 内容
        content = BodyLabel(f"这是 {title} 界面的内容")
        card_layout.addWidget(content)
        
        # 测试按钮
        btn = PushButton(FIF.SEND, "测试按钮")
        btn.clicked.connect(lambda: print(f"{title} 按钮被点击"))
        card_layout.addWidget(btn)
        
        layout.addWidget(card)
        layout.addStretch()


class MainWindow(FluentWindow):
    """Fluent Design 主窗口 - 测试版本"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化界面
        self.init_window()
        self.init_navigation()
    
    def init_window(self):
        """初始化窗口"""
        self.resize(1400, 900)
        self.setWindowTitle('串口数据分析工具 - Fluent Design (测试版)')
        
        # 设置主题
        setTheme(Theme.AUTO)
    
    def init_navigation(self):
        """初始化导航栏"""
        # 创建测试界面
        self.protocol_interface = SimpleInterface("协议配置", self)
        self.analysis_interface = SimpleInterface("数据分析", self)
        self.frame_interface = SimpleInterface("帧详情", self)
        self.log_interface = SimpleInterface("日志", self)
        self.settings_interface = SimpleInterface("设置", self)
        
        # 添加到导航
        self.addSubInterface(
            self.protocol_interface,
            FIF.SETTING,
            '协议配置'
        )
        
        self.addSubInterface(
            self.analysis_interface,
            FIF.SEARCH,
            '数据分析'
        )
        
        self.addSubInterface(
            self.frame_interface,
            FIF.DOCUMENT,
            '帧详情'
        )
        
        self.addSubInterface(
            self.log_interface,
            FIF.HISTORY,
            '日志'
        )
        
        # 设置添加到底部
        self.addSubInterface(
            self.settings_interface,
            FIF.SETTING,
            '设置',
            NavigationItemPosition.BOTTOM
        )


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
