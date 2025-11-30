#!/bin/bash
# 使用 GitHub CLI 创建 Release
# 需要先安装 gh: https://cli.github.com/

# 检查是否安装了 gh
if ! command -v gh &> /dev/null
then
    echo "GitHub CLI (gh) 未安装"
    echo "请访问 https://cli.github.com/ 安装"
    echo ""
    echo "或者手动创建 Release："
    echo "1. 访问 https://github.com/Aspiring-Freeman/SerialDataCompare/releases/new"
    echo "2. 选择标签: v1.4.1"
    echo "3. 复制 RELEASE_v1.4.1.md 的内容到描述框"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null
then
    echo "请先登录 GitHub CLI:"
    echo "gh auth login"
    exit 1
fi

# 创建 Release
echo "创建 GitHub Release v1.4.1..."

gh release create v1.4.1 \
    --title "v1.4.1 - 历史记录UI修复和完善" \
    --notes-file RELEASE_v1.4.1.md \
    --target main

echo ""
echo "✅ Release 创建成功！"
echo "查看: https://github.com/Aspiring-Freeman/SerialDataCompare/releases/tag/v1.4.1"
