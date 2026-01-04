# SerialDataCompare v1.3.2 发布说明

## 🐛 Bug 修复

### UI 编码错误修复
- **修复关键问题**：解决 UI 界面中使用 emoji 表情符号导致的 `UnicodeEncodeError` 崩溃
  - 错误信息：`'utf-8' codec can't encode characters in position 0-1: surrogates not allowed`
  - 原因：PySide6 内部字符串处理对某些 Unicode 字符（如 💡）的编码兼容性问题
  - 解决方案：使用普通文本标记 `[提示]` 替代 emoji，确保跨平台兼容性

### 配置保存问题修复
- **修复数据丢失**：`ProtocolConfig.to_dict()` 方法未保存简化配置字段
  - 影响：使用简化配置（绝对位置）的协议在保存后重新加载会丢失配置
  - 修复字段：
    - `frame_length`：固定帧长度
    - `checksum_position`：校验码绝对位置
    - `checksum_start`：校验计算起始位置
    - `checksum_end`：校验计算结束位置

## 🎨 UI/UX 改进

### 界面优化
1. **简化标签文本**
   - 修改："到（不含）：" → "到"
   - 原因：原标签文字过长导致界面控件位置偏移
   - 效果：界面更紧凑，布局更合理

2. **增强用户提示**
   - 添加详细的工具提示（tooltip），鼠标悬停时显示完整说明
   - 新增提示标签：`[提示] 结束位置不包含，如"从0到81"实际计算0~80`
   - 说明 Python 切片语义：左闭右开区间 `[start, end)`

3. **改善控件布局**
   - 添加水平间隔器（spacer），优化控件间距
   - 调整样式：提示文本使用灰色、较小字号，不干扰主要操作

### Python 切片语义说明
为避免用户混淆，明确标注：
```
校验计算范围：从 [0] 到 [81]
实际计算：位置 0, 1, 2, ..., 79, 80（共 81 个字节）
位置 81（通常是校验码本身）不参与计算
```

## 📚 文档更新

### 增强配置指南
在 `PROTOCOL_CONFIG_GUIDE.md` 中新增：
1. **Python 切片语义详解**
   - ⚠️ 警告标注：`checksum_end` 的"不包含"语义
   - 左闭右开区间 `[start, end)` 的含义
   - 对比示例：Python 切片 vs. 数学区间

2. **完整案例分析**
   - 83 字节帧示例（朗华协议）
   - 106 字节帧示例（工业协议）
   - 包含 ASCII 图示，直观展示每个字节的位置和作用

3. **GUI 对应关系**
   - 说明界面显示的数字与实际计算范围的关系
   - 示例：显示"从 0 到 81" = 实际计算 0~80

## 🔧 项目管理

### 测试文件整理
- **创建 `tests/` 文件夹**，集中管理所有测试脚本
- **移动文件**（9 个）：
  - `analyze_complete_protocol.py`
  - `analyze_industrial_protocol.py`
  - `test_analyze_button.py`
  - `test_converter.py`
  - `test_new_config.py`
  - `verify_langhua.py`
  - `diagnose_checksum_range.py`（新增）
  - `test_checksum_range.py`（新增）
  - `test_save_load_config.py`（新增）

---

## 📦 安装与更新

```bash
# 克隆或拉取最新代码
git clone https://github.com/Aspiring-Freeman/SerialDataCompare.git
cd SerialDataCompare

# 或更新现有仓库
git pull origin main
git checkout v1.3.2

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main_window.py
```

## 🔍 验证修复

### 测试编码问题修复
运行程序不再出现 `UnicodeEncodeError` 崩溃：
```bash
python main_window.py
# 应正常启动，无编码错误
```

### 测试配置保存
1. 创建新协议，使用简化配置（勾选"使用绝对位置"）
2. 设置 `frame_length`、`checksum_position` 等字段
3. 保存协议为 JSON 文件
4. 关闭并重新加载该协议
5. 验证所有字段均正确恢复

## 📝 升级注意事项

- ✅ 本版本完全兼容 v1.3.1 的配置文件
- ✅ 已使用简化配置的用户需重新保存一次协议（确保字段完整）
- ✅ 界面文本变更不影响功能，仅改善用户体验
- ✅ 测试文件迁移不影响主程序功能

## 🙏 致谢

感谢用户反馈问题，帮助我们快速定位和解决 UI 编码和配置保存问题！

---

**完整变更历史**：请查看 [CHANGELOG.md](CHANGELOG.md)  
**配置详细指南**：请查看 [PROTOCOL_CONFIG_GUIDE.md](PROTOCOL_CONFIG_GUIDE.md)
