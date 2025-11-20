# This Python file uses the following encoding: utf-8
"""
设置界面 - Fluent Design
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal, Qt

from qfluentwidgets import (
    ScrollArea, SettingCardGroup, PushSettingCard,
    HyperlinkCard, CardWidget, TitleLabel, BodyLabel, PushButton,
    setTheme, Theme, FluentIcon as FIF, InfoBar, InfoBarPosition,
    setThemeColor
)


class SettingsInterface(QWidget):
    """设置界面"""
    
    theme_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_interface")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 主题颜色预设 - 扩展到20种颜色
        self.theme_colors = {
            # 蓝色系列
            "微软蓝": "#0078d4",
            "天空蓝": "#00a8e8",
            "深蓝": "#0063b1",
            "湖水蓝": "#0090d1",
            
            # 紫色系列
            "淡紫": "#8764b8",
            "深紫": "#5c2d91",
            "梦幻紫": "#b146c2",
            
            # 粉红系列
            "粉红": "#e3008c",
            "玫瑰红": "#e81123",
            "樱花粉": "#ff6db6",
            
            # 橙红系列
            "橙色": "#f7630c",
            "日落橙": "#ff8c00",
            "珊瑚红": "#ff6347",
            
            # 绿色系列
            "翠绿": "#10893e",
            "薄荷绿": "#00b294",
            "森林绿": "#107c10",
            
            # 青色系列
            "青色": "#038387",
            "碧蓝": "#00b7c3",
            
            # 其他颜色
            "金黄": "#ffb900",
            "深灰": "#5d5a58",
        }
        
        # 创建UI
        self.create_settings_cards()
        
        # 添加弹性空间
        main_layout.addStretch()
    
    def create_settings_cards(self):
        """创建设置卡片"""
        self.create_appearance_group()
        self.create_about_group()
    
    def create_appearance_group(self):
        """创建外观设置组"""
        from qfluentwidgets import ExpandGroupSettingCard, PushSettingCard
        
        group = SettingCardGroup("外观设置")
        
        # 主题模式选择卡片
        self.theme_card = PushSettingCard(
            "切换主题",
            FIF.BRUSH,
            "主题模式",
            "当前: 浅色"
        )
        self.theme_card.clicked.connect(self.show_theme_dialog)
        group.addSettingCard(self.theme_card)
        
        # 主题颜色选择卡片
        self.color_card = PushSettingCard(
            "选择颜色",
            FIF.PALETTE,
            "主题颜色",
            "当前: 微软蓝 (共20种颜色)"
        )
        self.color_card.clicked.connect(self.show_color_dialog)
        group.addSettingCard(self.color_card)
        
        self.layout().addWidget(group)
    
    def show_theme_dialog(self):
        """显示主题选择对话框"""
        from qfluentwidgets import MessageBox, PrimaryPushButton, PushButton
        from PySide6.QtWidgets import QHBoxLayout
        
        # 创建自定义消息框
        w = MessageBox(
            "选择主题",
            "请选择应用的主题模式",
            self.window()
        )
        
        # 清除默认按钮
        w.yesButton.hide()
        w.cancelButton.hide()
        
        # 创建三个主题按钮
        light_btn = PrimaryPushButton("浅色", w)
        dark_btn = PushButton("深色", w)
        auto_btn = PushButton("自动", w)
        
        # 连接按钮信号
        light_btn.clicked.connect(lambda: self._apply_theme("浅色", w))
        dark_btn.clicked.connect(lambda: self._apply_theme("深色", w))
        auto_btn.clicked.connect(lambda: self._apply_theme("自动", w))
        
        # 添加按钮到布局
        w.buttonLayout.addWidget(light_btn)
        w.buttonLayout.addWidget(dark_btn)
        w.buttonLayout.addWidget(auto_btn)
        
        w.exec()
    
    def _apply_theme(self, theme: str, dialog):
        """应用主题并关闭对话框"""
        self.on_theme_changed(theme)
        self.theme_card.setContent(f"当前: {theme}")
        dialog.accept()
    
    def show_color_dialog(self):
        """显示主题颜色选择对话框"""
        from qfluentwidgets import MessageBox, PrimaryPushButton, PushButton
        from PySide6.QtWidgets import QGridLayout, QLabel
        from PySide6.QtCore import Qt
        
        # 创建自定义消息框
        w = MessageBox(
            "选择主题颜色",
            "选择您喜欢的主题色彩",
            self.window()
        )
        
        # 清除默认按钮
        w.yesButton.hide()
        w.cancelButton.hide()
        
        # 创建网格布局放置颜色按钮
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # 为每种颜色创建按钮
        row, col = 0, 0
        for color_name, color_hex in self.theme_colors.items():
            btn = PushButton(color_name, w)
            btn.setFixedSize(120, 45)
            # 设置按钮样式以显示颜色
            btn.setStyleSheet(f"""
                PushButton {{
                    background-color: {color_hex};
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }}
                PushButton:hover {{
                    background-color: {color_hex};
                    border: 2px solid white;
                }}
                PushButton:pressed {{
                    background-color: {color_hex};
                    border: 3px solid white;
                }}
            """)
            btn.clicked.connect(lambda checked, name=color_name, hex=color_hex: self._apply_color(name, hex, w))
            grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col >= 5:  # 每行5个按钮，更好地展示20种颜色
                col = 0
                row += 1
        
        # 添加网格布局到消息框
        w.textLayout.addLayout(grid_layout)
        
        w.exec()
    
    def _apply_color(self, color_name: str, color_hex: str, dialog):
        """应用主题颜色并关闭对话框"""
        setThemeColor(color_hex)
        self.color_card.setContent(f"当前: {color_name}")
        
        InfoBar.success(
            title="成功",
            content=f"主题颜色已切换到 {color_name}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
        dialog.accept()
    
    def create_about_group(self):
        """创建关于设置组"""
        group = SettingCardGroup("关于")
        
        # GitHub链接
        github_card = HyperlinkCard(
            url="https://github.com/Aspiring-Freeman/SerialDataCompare",
            text="GitHub 仓库",
            icon=FIF.GITHUB,
            title="GitHub",
            content="访问项目源代码"
        )
        group.addSettingCard(github_card)
        
        # 版本信息
        version_card = PushSettingCard(
            text="检查更新",
            icon=FIF.INFO,
            title="版本",
            content="SerialDataCompare v2.0.0"
        )
        group.addSettingCard(version_card)
        
        self.layout().addWidget(group)
    
    def on_theme_changed(self, text: str):
        """主题改变"""
        self.theme_changed.emit(text)
        
        InfoBar.success(
            title="成功",
            content=f"主题已切换到 {text}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
