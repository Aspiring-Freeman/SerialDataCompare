# SerialDataCompare v1.5.0 发布说明

## 📅 发布日期：2025-11-22

## 🎯 版本亮点

本版本带来了**点击高亮联动功能**，大幅提升了数据帧分析的交互体验，让用户能够直观地理解字节与字段之间的对应关系。

---

## ✨ 新功能

### 点击高亮联动功能

在帧详情界面，现在支持双向点击联动：

| 操作 | 效果 |
|------|------|
| 点击十六进制字节 | 自动高亮对应的字段标签 |
| 点击字段标签 | 自动高亮对应的十六进制字节范围 |

**特点**：
- 🎨 使用金色高亮（#FFD700），视觉效果清晰
- 📍 支持多字节字段的完整高亮
- ⚡ 响应即时，无延迟感

---

## 🎨 界面优化

### 简化颜色方案

- **统一高亮色**：采用单一金色高亮替代多色彩方案
- **灰色默认态**：未选中元素使用统一灰色背景
- **高对比度**：选中与未选中状态区分明显

**效果对比**：
```
之前：多种颜色，视觉较杂乱
现在：金色高亮 + 灰色默认，简洁清晰
```

---

## ⚡ 性能优化

### 高亮响应优化

针对点击高亮功能进行了专项性能优化：

1. **预定义样式**：常量定义高亮/默认样式字符串
2. **状态检查**：跳过已处于目标状态的元素
3. **最小化刷新**：仅更新实际改变的组件
4. **内存友好**：避免重复创建样式对象

---

## 🐛 Bug 修复

### 修复 FIELD_COLORS 属性错误

- **问题描述**：选择数据帧时出现 `AttributeError: 'FrameDetailInterface' object has no attribute 'FIELD_COLORS'`
- **影响范围**：帧详情显示功能
- **根本原因**：简化颜色方案时删除了 `FIELD_COLORS` 常量，但 `_assign_field_colors()` 方法仍在引用
- **修复方案**：更新方法使用 `HIGHLIGHT_COLOR` 常量

---

## 📝 技术细节

### 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `ui/fluent_frame_detail_interface.py` | 点击联动功能、颜色方案简化、性能优化、Bug修复 |
| `pyproject.toml` | 版本号更新至 1.5.0 |
| `CHANGELOG.md` | 添加 v1.5.0 变更记录 |

### 核心代码变更

```python
# 点击字节 → 高亮字段
def _on_byte_clicked(self, byte_index: int):
    field_name = self._find_field_for_byte(byte_index)
    if field_name:
        self._highlight_field_by_name(field_name)
        self._highlight_bytes_for_field(field_name)

# 点击字段 → 高亮字节
def _on_field_clicked(self, field_name: str):
    self._highlight_field_by_name(field_name)
    self._highlight_bytes_for_field(field_name)
```

---

## 📥 安装/升级

```bash
# 克隆或更新仓库
git pull origin main

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main_window.py
```

---

## 🔗 相关链接

- **GitHub 仓库**：[SerialDataCompare](https://github.com/Aspiring-Freeman/SerialDataCompare)
- **完整变更日志**：[CHANGELOG.md](CHANGELOG.md)
- **使用文档**：[document/使用指南_20251101.md](document/使用指南_20251101.md)

---

## 🙏 致谢

感谢所有使用和反馈的用户，你们的建议推动了这个功能的实现！
