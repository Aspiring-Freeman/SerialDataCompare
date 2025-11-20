#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试开始分析按钮功能"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from main_window import Main

def test_analyze_button():
    """测试分析按钮"""
    app = QApplication(sys.argv)
    window = Main()
    window.show()
    
    print("=== 测试开始分析按钮 ===")
    
    # 设置测试数据
    test_data = "68 AD 6A 01 D3 0E 8E 0D 0A 00 00 00 00 00 00 00 10 0E 00 00 01 01 01 01 38 36 32 31 31 38 30 36 39 34 34 30 35 37 33 34 36 30 31 31 33 32 38 36 34 35 32 36 34 33 38 39 38 36 31 31 32 34 32 30 37 30 32 32 39 34 39 37 36 33 10 01 01 01 10 0E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 01 01 00 00 00 01 06 94 16"
    window.ui.textEdit_input.setPlainText(test_data)
    print(f"✓ 已设置测试数据（{len(test_data.split())} 字节）")
    
    # 检查按钮状态
    print(f"✓ 分析按钮启用状态: {window.ui.btn_analyze.isEnabled()}")
    print(f"✓ 分析按钮文本: '{window.ui.btn_analyze.text()}'")
    
    # 检查协议配置
    print(f"✓ 当前协议: {window.current_protocol.protocol_name if window.current_protocol else 'None'}")
    
    # 尝试点击按钮
    def click_analyze():
        try:
            print("\n尝试点击分析按钮...")
            window.ui.btn_analyze.click()
            print("✓ 按钮点击成功！")
            
            # 等待一会儿看结果
            QTimer.singleShot(2000, lambda: check_result(window))
        except Exception as e:
            print(f"✗ 点击按钮出错: {e}")
            import traceback
            traceback.print_exc()
            app.quit()
    
    def check_result(window):
        try:
            print("\n检查分析结果:")
            print(f"  按钮文本: '{window.ui.btn_analyze.text()}'")
            print(f"  按钮启用: {window.ui.btn_analyze.isEnabled()}")
            
            if window.parse_result:
                print(f"  ✓ 解析成功!")
                print(f"  总帧数: {window.parse_result.get_total_frames()}")
                print(f"  有效帧: {window.parse_result.get_valid_frames()}")
            else:
                print(f"  ⚠ 还没有解析结果（可能还在处理或出错了）")
        except Exception as e:
            print(f"  ✗ 检查结果出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n=== 测试完成 ===")
            app.quit()
    
    # 1秒后点击按钮
    QTimer.singleShot(1000, click_analyze)
    
    # 最多运行5秒
    QTimer.singleShot(5000, app.quit)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_analyze_button()
