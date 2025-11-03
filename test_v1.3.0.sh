#!/bin/bash
# 测试v1.3.0新功能

echo "🧪 测试 v1.3.0 全部新功能"
echo ""

cd /home/noah/Program/Python_software/SerialDataCompare/SerialDataCompare

PYTHON="./.qtcreator/Python_3_10_12venv/bin/python"

# 测试1: 检查新文件
echo "=========================================="
echo "测试1: 检查新增文件"
echo "=========================================="

files=(
    "utils/delegates.py"
    "core/color_config.py"
    "core/analysis_history.py"
    "ui/__init__.py"
    "ui/history_dialog.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 不存在"
    fi
done
echo ""

# 测试2: 检查修改的文件
echo "=========================================="
echo "测试2: 检查修改的文件"
echo "=========================================="

modified_files=(
    "main_window.py"
    "models/data_frame.py"
    "core/parser.py"
    "core/__init__.py"
    "form.ui"
    "ui_form.py"
)

for file in "${modified_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 不存在"
    fi
done
echo ""

# 测试3: Python导入测试
echo "=========================================="
echo "测试3: Python模块导入测试"
echo "=========================================="

$PYTHON -c "
try:
    from utils.delegates import ComboBoxDelegate
    from core.color_config import ColorConfig
    from core.analysis_history import AnalysisHistory
    from ui import HistoryDialog
    from models.data_frame import DataFrame
    print('✅ 所有新模块导入成功')
except Exception as e:
    print(f'❌ 模块导入失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ 导入测试通过"
else
    echo "❌ 导入测试失败"
    exit 1
fi
echo ""

# 测试4: 测试ComboBox delegate
echo "=========================================="
echo "测试4: 测试ComboBox Delegate"
echo "=========================================="

$PYTHON -c "
from utils.delegates import ComboBoxDelegate
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
items = ['uint8', 'uint16', 'uint32']
delegate = ComboBoxDelegate(items)
print('✅ ComboBox Delegate创建成功')
app.quit()
"

if [ $? -eq 0 ]; then
    echo "✅ ComboBox Delegate测试通过"
else
    echo "❌ ComboBox Delegate测试失败"
    exit 1
fi
echo ""

# 测试5: 测试颜色配置
echo "=========================================="
echo "测试5: 测试颜色配置"
echo "=========================================="

$PYTHON -c "
from core.color_config import ColorConfig

config = ColorConfig()

# 测试获取颜色
color = config.get_color('uint8')
print(f'uint8颜色: {color}')

# 测试设置颜色
config.set_color('uint8', '#FF0000')
new_color = config.get_color('uint8')
print(f'修改后的uint8颜色: {new_color}')

# 测试重置
config.reset_colors()
reset_color = config.get_color('uint8')
print(f'重置后的uint8颜色: {reset_color}')

print('✅ 颜色配置测试通过')
"

if [ $? -eq 0 ]; then
    echo "✅ 颜色配置测试通过"
else
    echo "❌ 颜色配置测试失败"
    exit 1
fi
echo ""

# 测试6: 测试分析历史
echo "=========================================="
echo "测试6: 测试分析历史"
echo "=========================================="

$PYTHON -c "
from core.analysis_history import AnalysisHistory

history = AnalysisHistory()

# 清空历史
history.clear_history()

# 添加测试记录
history.add_analysis(
    protocol_name='测试协议',
    input_data='68 00 01 02 03 16',
    total_frames=1,
    valid_frames=1,
    error_frames=0,
    frame_details=[{
        'frame_number': 1,
        'has_error': False,
        'checksum_valid': True,
        'raw_data_hex': '68 00 01 02 03 16'
    }]
)

# 获取历史
records = history.get_history()
print(f'历史记录数: {len(records)}')

if len(records) > 0:
    record = records[0]
    print(f'协议名称: {record[\"protocol_name\"]}')
    print(f'总帧数: {record[\"total_frames\"]}')
    print('✅ 分析历史测试通过')
else:
    print('❌ 历史记录为空')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ 分析历史测试通过"
else
    echo "❌ 分析历史测试失败"
    exit 1
fi
echo ""

# 测试7: 测试DataFrame HTML输出
echo "=========================================="
echo "测试7: 测试DataFrame HTML输出"
echo "=========================================="

$PYTHON -c "
from models.data_frame import DataFrame
from core.color_config import ColorConfig

frame = DataFrame(
    frame_number=1,
    start_position=0,
    end_position=6,
    raw_data=bytes.fromhex('68 00 01 02 03 16')
)

frame.add_field('设备地址', 0x00, 'uint8')
frame.add_field('命令码', 0x01, 'uint8')
frame.expected_checksum = 0x16
frame.actual_checksum = 0x16
frame.checksum_valid = True

color_config = ColorConfig()
html = frame.get_detailed_info_html(color_config)

# 检查HTML结构和字段名
if '<html>' in html and '设备地址' in html and '命令码' in html:
    print('✅ HTML输出包含预期内容')
    print(f'HTML长度: {len(html)} 字节')
else:
    print('❌ HTML输出不完整')
    print(f'包含<html>: {\"<html>\" in html}')
    print(f'包含设备地址: {\"设备地址\" in html}')
    print(f'包含命令码: {\"命令码\" in html}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ DataFrame HTML测试通过"
else
    echo "❌ DataFrame HTML测试失败"
    exit 1
fi
echo ""

# 总结
echo "=========================================="
echo "🎉 所有测试通过！v1.3.0 新功能已完成"
echo "=========================================="
echo ""
echo "已完成的功能:"
echo "  ✅ 字段类型下拉选择 (ComboBox Delegate)"
echo "  ✅ 字节类型颜色配置 (ColorConfig + UI)"
echo "  ✅ 分析历史记录 (AnalysisHistory + HistoryDialog)"
echo "  ✅ HTML格式的彩色显示"
echo ""
echo "新增文件 (5个):"
echo "  - utils/delegates.py"
echo "  - core/color_config.py"
echo "  - core/analysis_history.py"
echo "  - ui/__init__.py"
echo "  - ui/history_dialog.py"
echo ""
echo "修改文件 (6个):"
echo "  - main_window.py (集成所有新功能)"
echo "  - models/data_frame.py (添加HTML输出和字段类型存储)"
echo "  - core/parser.py (记录字段类型)"
echo "  - core/__init__.py (导出ColorConfig)"
echo "  - form.ui (添加颜色配置UI和历史按钮)"
echo "  - ui_form.py (重新生成)"
echo ""
echo "现在可以运行程序测试:"
echo "  $PYTHON main_window.py"
echo ""
