# This Python file uses the following encoding: utf-8
"""
主题感知颜色/样式助手

所有 UI 代码应使用本模块提供的函数获取颜色和样式，
以确保深色/浅色主题自动适配。

使用方式 (qfluentwidgets Label 专用 — 自动跟随主题切换):
    from utils.theme_helper import ThemeHelper as TH
    TH.apply_help_text(label)          # 灰色帮助文字 (setTextColor)
    TH.apply_hint(label)               # 灰色提示文字 (setTextColor + font)
    TH.apply_title_accent(label)       # 蓝色加粗标题 (setTextColor + font)
    TH.apply_muted(label)              # 次要文字 (setTextColor + font)

使用方式 (普通 QLabel / QFrame / QTextEdit — 须手动刷新):
    label.setStyleSheet(TH.hint_style())
"""
from qfluentwidgets import isDarkTheme


class ThemeHelper:
    """
    集中管理所有主题感知颜色和样式字符串。

    每个方法在被调用时实时查询 isDarkTheme()，
    因此主题切换后只需重新调用即可获得正确颜色。
    """

    # ── 基础颜色 ──────────────────────────────────────────
    @staticmethod
    def text_color() -> str:
        """主要文字颜色"""
        return "#E0E0E0" if isDarkTheme() else "#333333"

    @staticmethod
    def hint_color() -> str:
        """描述/提示文字颜色 (比主色更淡)"""
        return "#A0A0A0" if isDarkTheme() else "#606060"

    @staticmethod
    def muted_color() -> str:
        """次要/静音文字颜色"""
        return "#909090" if isDarkTheme() else "#888888"

    @staticmethod
    def help_color() -> str:
        """帮助文本颜色 (最淡)"""
        return "#808080" if isDarkTheme() else "#999999"

    @staticmethod
    def accent_color() -> str:
        """主题强调色 (蓝色)"""
        return "#4CC2FF" if isDarkTheme() else "#0078D4"

    @staticmethod
    def info_log_color() -> str:
        """INFO 级别日志文字颜色"""
        return "#E0E0E0" if isDarkTheme() else "#000000"

    @staticmethod
    def warning_log_color() -> str:
        """WARNING 级别日志文字颜色"""
        return "#FFB900" if isDarkTheme() else "#FF8C00"

    @staticmethod
    def error_log_color() -> str:
        """ERROR 级别日志文字颜色"""
        return "#FF6B6B" if isDarkTheme() else "#DC143C"

    @staticmethod
    def success_color() -> str:
        """成功/通过文字颜色"""
        return "#6CCB5F" if isDarkTheme() else "#107C10"

    @staticmethod
    def error_text_color() -> str:
        """错误文字颜色"""
        return "#FF6B6B" if isDarkTheme() else "#D13438"

    # ── 背景色 ──────────────────────────────────────────
    @staticmethod
    def surface_bg() -> str:
        """表面/输入框背景"""
        return "#383838" if isDarkTheme() else "#F5F5F5"

    @staticmethod
    def zebra_even_bg() -> str:
        """Zebra striping: 偶数字段背景"""
        return "#3D3D3D" if isDarkTheme() else "#E8ECF0"

    @staticmethod
    def zebra_odd_bg() -> str:
        """Zebra striping: 奇数字段背景"""
        return "#333333" if isDarkTheme() else "#F6F8FA"

    @staticmethod
    def card_bg() -> str:
        """卡片/容器内部背景"""
        return "#2D2D2D" if isDarkTheme() else "#F8F8F8"

    @staticmethod
    def value_bg() -> str:
        """字段值背景"""
        return "#383838" if isDarkTheme() else "#F3F3F3"

    @staticmethod
    def header_bg() -> str:
        """表头/标题行背景"""
        return "#404040" if isDarkTheme() else "#E0E0E0"

    @staticmethod
    def hover_bg() -> str:
        """悬停背景"""
        return "#1A3A5C" if isDarkTheme() else "#E8F4FD"

    @staticmethod
    def error_bg() -> str:
        """错误信息背景"""
        return "#4D2020" if isDarkTheme() else "#FFF4F4"

    @staticmethod
    def warning_bg() -> str:
        """警告信息背景"""
        return "#4D4020" if isDarkTheme() else "#FFF8E1"

    @staticmethod
    def warning_text_color() -> str:
        """警告文字颜色"""
        return "#FFB900" if isDarkTheme() else "#8A6D00"

    @staticmethod
    def warning_border() -> str:
        """警告边框颜色"""
        return "#665500" if isDarkTheme() else "#FFE082"

    # ── 边框色 ──────────────────────────────────────────
    @staticmethod
    def border_color() -> str:
        """普通边框颜色"""
        return "#505050" if isDarkTheme() else "#D0D0D0"

    @staticmethod
    def light_border() -> str:
        """浅边框颜色"""
        return "#454545" if isDarkTheme() else "#E0E0E0"

    # ── 数据文字颜色 ────────────────────────────────────
    @staticmethod
    def data_text_color() -> str:
        """数据区域文字颜色 (如十六进制数据)"""
        return "#7AB8F5" if isDarkTheme() else "#2B579A"

    # ── 组合样式 ──────────────────────────────────────────
    @staticmethod
    def hint_style(font_size: str = "13px", extra: str = "") -> str:
        """提示文字样式 (灰色小字)"""
        s = f"color: {ThemeHelper.hint_color()}; font-size: {font_size};"
        if extra:
            s += f" {extra}"
        return s

    @staticmethod
    def muted_style(font_size: str = "12px", italic: bool = False) -> str:
        """次要文字样式"""
        s = f"color: {ThemeHelper.muted_color()}; font-size: {font_size};"
        if italic:
            s += " font-style: italic;"
        return s

    @staticmethod
    def help_text_style() -> str:
        """帮助文本样式"""
        return f"color: {ThemeHelper.help_color()};"

    @staticmethod
    def title_accent_style() -> str:
        """带强调色的标题样式"""
        return f"font-weight: bold; color: {ThemeHelper.accent_color()};"

    @staticmethod
    def label_style() -> str:
        """字段标签样式 (加粗)"""
        return f"font-weight: bold; color: {ThemeHelper.text_color()}; min-width: 100px;"

    @staticmethod
    def value_style() -> str:
        """字段值样式 (蓝色+背景)"""
        return (f"color: {ThemeHelper.accent_color()}; font-size: 14px; "
                f"padding: 5px; background: {ThemeHelper.value_bg()}; border-radius: 4px;")

    @staticmethod
    def accent_mono_style() -> str:
        """等宽蓝色文字样式 (用于校验值等)"""
        return f"color: {ThemeHelper.accent_color()}; font-family: 'Courier New', monospace;"

    @staticmethod
    def field_name_style() -> str:
        """字段名样式 (加粗)"""
        return f"font-weight: bold; color: {ThemeHelper.text_color()};"

    @staticmethod
    def no_data_style() -> str:
        """无数据/空状态样式"""
        return f"color: {ThemeHelper.help_color()}; font-style: italic; padding: 20px;"

    @staticmethod
    def error_label_style() -> str:
        """错误标签样式"""
        return (f"color: {ThemeHelper.error_text_color()}; "
                f"background: {ThemeHelper.error_bg()}; "
                f"padding: 10px; border-radius: 4px; margin-top: 10px;")

    @staticmethod
    def warning_label_style() -> str:
        """警告标签样式"""
        return (f"color: {ThemeHelper.warning_text_color()}; "
                f"background: {ThemeHelper.warning_bg()}; "
                f"padding: 10px; border-radius: 4px; margin-top: 10px; "
                f"border: 1px solid {ThemeHelper.warning_border()};")

    @staticmethod
    def checksum_pass_style() -> str:
        """校验通过样式"""
        return f"color: {ThemeHelper.success_color()}; font-weight: bold; font-size: 14px;"

    @staticmethod
    def checksum_fail_style() -> str:
        """校验失败样式"""
        return f"color: {ThemeHelper.error_text_color()}; font-weight: bold; font-size: 14px;"

    # ── 复杂组件样式 ─────────────────────────────────────
    @staticmethod
    def byte_style_normal() -> str:
        """字节标签正常状态样式"""
        return f"""
            QLabel {{
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                background: {ThemeHelper.surface_bg()};
                border: 1px solid {ThemeHelper.border_color()};
                border-radius: 3px;
                color: {ThemeHelper.text_color()};
            }}
            QLabel:hover {{
                background: {ThemeHelper.hover_bg()};
                border-color: {ThemeHelper.accent_color()};
            }}
        """

    @staticmethod
    def byte_style_highlight() -> str:
        """字节标签高亮状态样式"""
        return f"""
            QLabel {{
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                background: #FFD700;
                border: 1px solid #FFC107;
                border-radius: 3px;
                color: #333;
                font-weight: bold;
            }}
        """

    @staticmethod
    def byte_style_typed(bg_color: str) -> str:
        """字节标签带类型背景色样式"""
        return f"""
            QLabel {{
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                background: {bg_color};
                border: 1px solid {ThemeHelper.border_color()};
                border-radius: 3px;
                color: {ThemeHelper.text_color()};
            }}
            QLabel:hover {{
                border-color: {ThemeHelper.accent_color()};
                border-width: 2px;
            }}
        """

    @staticmethod
    def byte_style_selected(bg_color: str = "#FFD700") -> str:
        """字节标签选中状态样式（统一金色高亮）"""
        return f"""
            QLabel {{
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                background: {bg_color};
                border: 2px solid #FFA000;
                border-radius: 3px;
                color: #333;
                font-weight: bold;
            }}
        """

    @staticmethod
    def field_style_normal() -> str:
        """字段框正常状态样式"""
        return f"""
            QFrame {{
                background: {ThemeHelper.card_bg()};
                border: 1px solid {ThemeHelper.light_border()};
                border-radius: 6px;
            }}
            QFrame:hover {{
                background: {ThemeHelper.hover_bg()};
                border-color: {ThemeHelper.accent_color()};
            }}
        """

    @staticmethod
    def field_style_highlight() -> str:
        """字段框高亮状态样式"""
        return """
            QFrame {
                background: #FFD700;
                border: 2px solid #FFC107;
                border-radius: 6px;
            }
        """

    @staticmethod
    def field_style_typed(bg_color: str) -> str:
        """字段框带类型背景色样式"""
        return f"""
            QFrame {{
                background: {bg_color};
                border: 1px solid {ThemeHelper.light_border()};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border-color: {ThemeHelper.accent_color()};
                border-width: 2px;
            }}
        """

    @staticmethod
    def field_style_selected(bg_color: str = "#FFD700") -> str:
        """字段框选中状态样式（统一金色高亮）"""
        return f"""
            QFrame {{
                background: {bg_color};
                border: 2px solid #FFA000;
                border-radius: 6px;
            }}
        """

    @staticmethod
    def data_textbox_style() -> str:
        """数据文本框样式"""
        return f"""
            QTextEdit {{
                font-family: 'Courier New', monospace;
                font-size: 13px;
                background: {ThemeHelper.card_bg()};
                border: 1px solid {ThemeHelper.light_border()};
                border-radius: 6px;
                padding: 10px;
                color: {ThemeHelper.data_text_color()};
            }}
        """

    @staticmethod
    def addr_label_style() -> str:
        """地址偏移标签样式"""
        return f"""
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            font-weight: bold;
            color: {ThemeHelper.accent_color()};
            padding: 3px 8px 3px 3px;
            min-width: 50px;
        """

    # ── 日志颜色 ─────────────────────────────────────────
    @staticmethod
    def log_color_map() -> dict:
        """日志级别颜色映射"""
        if isDarkTheme():
            return {
                "DEBUG": "#808080",
                "INFO": "#E0E0E0",
                "WARNING": "#FFB900",
                "ERROR": "#FF6B6B",
            }
        else:
            return {
                "DEBUG": "#808080",
                "INFO": "#000000",
                "WARNING": "#FF8C00",
                "ERROR": "#DC143C",
            }

    # ── HTML 样式 (用于 data_frame 等) ────────────────────
    @staticmethod
    def html_header_bg() -> str:
        """HTML 表头背景色"""
        return ThemeHelper.header_bg()

    @staticmethod
    def html_body_style() -> str:
        """HTML body 样式"""
        return (f"font-family: 'Courier New', monospace; font-size: 10pt; "
                f"color: {ThemeHelper.text_color()};")

    # ── FluentLabelBase apply_* 方法 ─────────────────────
    # 以下方法通过 setTextColor(light, dark) + setFont() 设置样式，
    # FluentLabelBase 会在主题切换时自动刷新颜色，无需手动 refresh。

    @staticmethod
    def apply_help_text(label):
        """帮助文本样色 (灰色，自动跟随主题)"""
        label.setTextColor("#999999", "#808080")

    @staticmethod
    def apply_hint(label, pixel_size: int = 13):
        """提示/描述文字 (较淡灰色 + 小字号)"""
        label.setTextColor("#606060", "#A0A0A0")
        if pixel_size:
            font = label.font()
            font.setPixelSize(pixel_size)
            label.setFont(font)

    @staticmethod
    def apply_muted(label, pixel_size: int = 12, italic: bool = False):
        """次要文字 (灰色 + 小字号 + 可选斜体)"""
        label.setTextColor("#888888", "#909090")
        font = label.font()
        if pixel_size:
            font.setPixelSize(pixel_size)
        if italic:
            font.setItalic(True)
        label.setFont(font)

    @staticmethod
    def apply_title_accent(label):
        """强调色标题 (蓝色 + 加粗)"""
        label.setTextColor("#0078D4", "#4CC2FF")
        font = label.font()
        font.setBold(True)
        label.setFont(font)

    @staticmethod
    def apply_accent_mono(label):
        """等宽蓝色文字 (用于校验值等)"""
        label.setTextColor("#0078D4", "#4CC2FF")
        font = label.font()
        font.setFamily("Courier New")
        label.setFont(font)

    @staticmethod
    def apply_label(label):
        """字段标签 (加粗 + 主色)"""
        label.setTextColor("#333333", "#E0E0E0")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        label.setMinimumWidth(100)

    @staticmethod
    def apply_checksum_pass(label):
        """校验通过 (绿色 + 加粗)"""
        label.setTextColor("#107C10", "#6CCB5F")
        font = label.font()
        font.setBold(True)
        font.setPixelSize(14)
        label.setFont(font)

    @staticmethod
    def apply_checksum_fail(label):
        """校验失败 (红色 + 加粗)"""
        label.setTextColor("#D13438", "#FF6B6B")
        font = label.font()
        font.setBold(True)
        font.setPixelSize(14)
        label.setFont(font)

    @staticmethod
    def apply_no_data(label):
        """无数据/空状态 (灰色斜体)"""
        label.setTextColor("#999999", "#808080")
        font = label.font()
        font.setItalic(True)
        label.setFont(font)

    @staticmethod
    def apply_default_text(label):
        """恢复为 FluentLabelBase 默认文字颜色"""
        label.setTextColor("#000000", "#FFFFFF")

    @staticmethod
    def apply_value(label):
        """字段值样式 (蓝色 + 背景) — 使用 setCustomStyleSheet 保留主题"""
        from qfluentwidgets.common.style_sheet import setCustomStyleSheet
        light_qss = (
            f"FluentLabelBase{{color: #0078D4; font-size: 14px; "
            f"padding: 5px; background: #F3F3F3; border-radius: 4px;}}"
        )
        dark_qss = (
            f"FluentLabelBase{{color: #4CC2FF; font-size: 14px; "
            f"padding: 5px; background: #383838; border-radius: 4px;}}"
        )
        setCustomStyleSheet(label, light_qss, dark_qss)

    @staticmethod
    def apply_error_label(label):
        """错误标签样式 (红色+背景) — 使用 setCustomStyleSheet"""
        from qfluentwidgets.common.style_sheet import setCustomStyleSheet
        light_qss = (
            f"FluentLabelBase{{color: #D13438; background: #FFF4F4; "
            f"padding: 10px; border-radius: 4px; margin-top: 10px;}}"
        )
        dark_qss = (
            f"FluentLabelBase{{color: #FF6B6B; background: #4D2020; "
            f"padding: 10px; border-radius: 4px; margin-top: 10px;}}"
        )
        setCustomStyleSheet(label, light_qss, dark_qss)

    @staticmethod
    def apply_warning_label(label):
        """警告标签样式 (黄色+背景) — 使用 setCustomStyleSheet"""
        from qfluentwidgets.common.style_sheet import setCustomStyleSheet
        light_qss = (
            f"FluentLabelBase{{color: #8A6D00; background: #FFF8E1; "
            f"padding: 10px; border-radius: 4px; margin-top: 10px; "
            f"border: 1px solid #FFE082;}}"
        )
        dark_qss = (
            f"FluentLabelBase{{color: #FFB900; background: #4D4020; "
            f"padding: 10px; border-radius: 4px; margin-top: 10px; "
            f"border: 1px solid #665500;}}"
        )
        setCustomStyleSheet(label, light_qss, dark_qss)
