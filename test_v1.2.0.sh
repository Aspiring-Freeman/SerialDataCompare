#!/bin/bash
# 快速测试脚本 - v1.2.0功能测试

echo "🧪 开始测试 v1.2.0 新功能..."
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 虚拟环境Python路径
PYTHON="./.qtcreator/Python_3_10_12venv/bin/python"

# 检查Python是否存在
if [ ! -f "$PYTHON" ]; then
    echo "❌ 虚拟环境不存在: $PYTHON"
    echo "请先创建虚拟环境"
    exit 1
fi

echo "✅ 找到Python: $PYTHON"
echo ""

# 测试1: 格式转换器测试
echo "=========================================="
echo "测试1: 协议格式转换功能"
echo "=========================================="
$PYTHON test_converter.py
if [ $? -eq 0 ]; then
    echo "✅ 格式转换测试通过"
else
    echo "❌ 格式转换测试失败"
    exit 1
fi
echo ""

# 测试2: 检查文件完整性
echo "=========================================="
echo "测试2: 检查文件完整性"
echo "=========================================="

files=(
    "core/protocol_converter.py"
    "core/protocol_history.py"
    "protocol_extended_example.json"
    "document/功能更新_协议格式兼容_20251101.md"
    "document/测试报告_协议格式兼容_20251101.md"
    "CHANGELOG.md"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 不存在"
        all_exist=false
    fi
done

if [ "$all_exist" = true ]; then
    echo "✅ 所有文件完整"
else
    echo "❌ 文件不完整"
    exit 1
fi
echo ""

# 测试3: 导入测试
echo "=========================================="
echo "测试3: Python模块导入测试"
echo "=========================================="

$PYTHON -c "
try:
    from core.protocol_converter import ProtocolConverter
    from core.protocol_history import ProtocolHistory
    from core import ProtocolManager
    print('✅ 所有模块导入成功')
except Exception as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ 模块导入测试通过"
else
    echo "❌ 模块导入测试失败"
    exit 1
fi
echo ""

# 测试4: 协议加载测试
echo "=========================================="
echo "测试4: 协议文件加载测试"
echo "=========================================="

$PYTHON -c "
from core import ProtocolManager

# 测试标准格式
protocol1 = ProtocolManager.load_protocol('protocol_example.json')
if protocol1:
    print(f'✅ 标准格式加载成功: {protocol1.protocol_name}')
else:
    print('❌ 标准格式加载失败')
    exit(1)

# 测试扩展格式
protocol2 = ProtocolManager.load_protocol('protocol_extended_example.json')
if protocol2:
    print(f'✅ 扩展格式加载成功: {protocol2.protocol_name}')
else:
    print('❌ 扩展格式加载失败')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ 协议加载测试通过"
else
    echo "❌ 协议加载测试失败"
    exit 1
fi
echo ""

# 总结
echo "=========================================="
echo "🎉 所有测试通过！v1.2.0 功能正常"
echo "=========================================="
echo ""
echo "可以运行以下命令启动程序："
echo "  ./run.sh"
echo "或"
echo "  $PYTHON main_window.py"
echo ""
echo "查看文档："
echo "  cat document/v1.2.0_开发完成总结_20251101.md"
echo ""
