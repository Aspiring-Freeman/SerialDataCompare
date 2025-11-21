"""
测试不同的 Qt 主题样式

可用的主题样式（取决于操作系统）：
1. Fusion - Qt 自带的现代跨平台主题（推荐）
2. Windows - Windows 原生风格（仅 Windows）
3. WindowsVista - Windows Vista 风格（仅 Windows）
4. Macintosh - macOS 原生风格（仅 macOS）
5. GTK+ - GTK+ 原生风格（仅 Linux，需要安装 qt6-gtk-platformtheme）

使用方法：
在 main_window.py 的 if __name__ == "__main__": 部分，
将 app.setStyle("Fusion") 改为：
- app.setStyle("Fusion")      # 推荐：现代、跨平台
- app.setStyle("Windows")     # Windows 原生
- app.setStyle("gtk2")        # Linux GTK 风格
"""

from PySide6.QtWidgets import QApplication, QStyleFactory
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 列出当前系统支持的所有样式
    print("当前系统支持的 Qt 样式：")
    for style in QStyleFactory.keys():
        print(f"  - {style}")
    
    print(f"\n当前使用的样式：{app.style().objectName()}")
    
    sys.exit(0)
