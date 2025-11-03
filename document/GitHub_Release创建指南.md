# GitHub Release 创建指南

## ✅ 已完成的准备工作

1. ✅ 创建了 v1.3.0 Git标签
2. ✅ 推送标签到GitHub
3. ✅ 创建了详细的Release Notes文档
4. ✅ 推送所有文档到仓库

## 🎯 在GitHub上创建Release

### 方法一：通过GitHub网页界面（推荐）

#### 步骤1: 访问Releases页面
1. 打开浏览器，访问: https://github.com/Aspiring-Freeman/SerialDataCompare
2. 点击右侧的 **"Releases"** 链接
3. 或直接访问: https://github.com/Aspiring-Freeman/SerialDataCompare/releases

#### 步骤2: 创建新Release
1. 点击 **"Draft a new release"** 按钮
2. 在 "Choose a tag" 下拉框中选择 **v1.3.0**（标签已存在）

#### 步骤3: 填写Release信息

**Release title (标题):**
```
SerialDataCompare v1.3.0 - 完整的串口数据分析工具
```

**描述 (Description):**
复制 `GITHUB_RELEASE_v1.3.0.md` 文件的内容，或使用以下简化版本：

```markdown
# SerialDataCompare v1.3.0 🎉

完整的串口数据分析工具，支持灵活的协议配置、多种校验算法和可视化数据展示。

## ✨ What's New

### 主要新功能

🎯 **字段类型下拉选择**
- 协议配置表格支持10种数据类型下拉选择
- 避免手动输入错误，提升配置效率

🎨 **字段类型颜色配置**
- 不同数据类型使用不同背景颜色显示
- 支持自定义颜色方案
- HTML彩色字段展示，提升可读性

📊 **分析历史记录**
- 自动保存每次分析结果
- 查看历史分析记录（最多20条）
- 包含时间戳、协议信息、统计数据

⚡ **用户体验改进**
- 自动清空旧的分析结果
- 增强的错误提示和反馈

## 🔧 Core Features

- ✅ 灵活的协议配置系统（10种数据类型）
- ✅ 多种校验算法（SUM, XOR, CRC8/16/32）
- ✅ 自定义校验范围
- ✅ 协议格式兼容（标准+扩展JSON）
- ✅ 可视化数据展示
- ✅ 多线程解析

## 📦 Installation

```bash
# 克隆仓库
git clone https://github.com/Aspiring-Freeman/SerialDataCompare.git
cd SerialDataCompare

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main_window.py
```

## 🐛 Bug Fixes

- ✅ 修复 `textEdit_result` 不存在导致分析失败的bug
- ✅ 修复颜色配置未生效的问题

## 📚 Documentation

- [完整 Release Notes](RELEASE_NOTES_v1.3.0.md)
- [快速使用指南](document/快速使用指南_v1.3.0.md)
- [开发文档](document/v1.3.0_开发完成报告_20251101.md)

---

**Full Changelog**: https://github.com/Aspiring-Freeman/SerialDataCompare/commits/v1.3.0
```

#### 步骤4: 设置选项
- ✅ 勾选 **"Set as the latest release"** （设为最新版本）
- ⚠️ 不要勾选 "Set as a pre-release"（不是预发布版）
- ℹ️ 可选：勾选 "Create a discussion for this release"（创建讨论）

#### 步骤5: 发布
1. 预览Release内容确认无误
2. 点击 **"Publish release"** 按钮
3. 完成！🎉

---

### 方法二：使用GitHub CLI（命令行）

如果你安装了GitHub CLI工具：

```bash
cd /home/noah/Program/Python_software/SerialDataCompare/SerialDataCompare

# 读取Release说明
gh release create v1.3.0 \
  --title "SerialDataCompare v1.3.0 - 完整的串口数据分析工具" \
  --notes-file GITHUB_RELEASE_v1.3.0.md \
  --latest
```

---

### 方法三：使用GitHub API

如果你熟悉API调用：

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/Aspiring-Freeman/SerialDataCompare/releases \
  -d '{
    "tag_name": "v1.3.0",
    "name": "SerialDataCompare v1.3.0",
    "body": "内容从 GITHUB_RELEASE_v1.3.0.md 复制",
    "draft": false,
    "prerelease": false
  }'
```

---

## 📋 Release检查清单

在发布前确认：

- [x] Git标签已创建并推送
- [x] Release Notes文档已创建
- [x] 所有文档已推送到仓库
- [ ] 在GitHub上创建Release
- [ ] 设置为最新版本
- [ ] Release描述清晰完整
- [ ] 验证下载链接可用

---

## 🔗 相关链接

- **仓库主页**: https://github.com/Aspiring-Freeman/SerialDataCompare
- **标签页面**: https://github.com/Aspiring-Freeman/SerialDataCompare/releases/tag/v1.3.0
- **提交历史**: https://github.com/Aspiring-Freeman/SerialDataCompare/commits/v1.3.0

---

## 📸 Release发布后的效果

发布后，用户可以：

1. **查看Release信息**
   - 在 Releases 页面看到 v1.3.0
   - 阅读详细的功能说明

2. **下载源代码**
   - Source code (zip)
   - Source code (tar.gz)

3. **克隆特定版本**
   ```bash
   git clone --branch v1.3.0 https://github.com/Aspiring-Freeman/SerialDataCompare.git
   ```

4. **获取更新通知**
   - Watch仓库的用户会收到Release通知
   - RSS订阅更新

---

## 💡 提示

### Release描述技巧
- 使用Emoji增强视觉效果 🎉
- 突出新功能和重要变更 ✨
- 提供清晰的安装指南 📦
- 链接到详细文档 📚
- 列出Bug修复 🐛

### 版本标签规范
- 使用语义化版本: `v主版本.次版本.修订号`
- 主版本：不兼容的API修改
- 次版本：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

---

## 🎓 下次发布流程

为下一个版本做准备：

```bash
# 1. 更新代码
git add .
git commit -m "feat: new feature"
git push origin main

# 2. 创建标签
git tag -a v1.4.0 -m "Release v1.4.0"
git push origin v1.4.0

# 3. 创建Release Notes
# 编辑 RELEASE_NOTES_v1.4.0.md

# 4. 在GitHub创建Release
# 按照上述步骤操作
```

---

**创建时间**: 2025年11月3日  
**文档版本**: v1.0  
**适用范围**: SerialDataCompare v1.3.0
