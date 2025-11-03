#!/bin/bash
# 串口数据分析工具启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 虚拟环境路径
VENV_PATH="${SCRIPT_DIR}/.qtcreator/Python_3_10_12venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "错误：虚拟环境不存在！"
    echo "路径：$VENV_PATH"
    exit 1
fi

# 启动程序
echo "正在启动串口数据分析工具..."
"${VENV_PATH}/bin/python" "${SCRIPT_DIR}/main_window.py"
