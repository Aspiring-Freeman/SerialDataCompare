# v1.4.1 - 历史记录UI修复和完善

## 🐛 Bug 修复

### 历史记录对话框主题问题
- **修复**：历史记录对话框文字不可见的问题（黑色背景上显示黑色文字）
- **原因**：标准 Qt 组件不会自动继承 Fluent Design 主题
- **解决方案**：
  - 将 `QDialog` 改为 `MessageBoxBase` 基类
  - 替换所有标准 Qt 组件为 qfluentwidgets 等效组件：
    - QLabel → SubtitleLabel/BodyLabel
    - QPushButton → PushButton
    - QListWidget → ListWidget
    - QTableWidget → TableWidget
    - QTextEdit → TextEdit
    - QMessageBox → MessageBox

### 按钮布局错误修复
- **修复**：`buttonGroup.addWidget()` 导致的 AttributeError
- **解决方案**：使用 `buttonGroup.layout().addWidget()` 正确添加按钮到布局

### 字段端序保存问题
- **修复**：BYTES 和 STRING 类型字段的端序配置无法正确保存
- **原因**：`is_multi_byte_type()` 方法只检查数值类型
- **解决方案**：扩展方法支持 BYTES/STRING 类型（当长度 > 1 时）

## ✨ 功能完善

### 历史记录UI集成
- 在协议配置界面添加"协议历史"按钮
- 在数据分析界面添加"分析历史"按钮
- 支持从历史记录直接加载协议配置
- 支持查看历史分析结果详情
- 支持清空历史记录功能

### 对话框功能增强
- 协议历史对话框：
  - 显示最近使用的协议文件列表
  - 显示协议详细信息（名称、描述、字段数量）
  - 支持双击加载协议
  - 自动清理不存在的文件
  
- 分析历史对话框：
  - 显示历史分析记录（时间、协议、帧统计）
  - 显示帧详细信息
  - 支持清空历史记录

## 📝 技术改进

### 主题一致性
- 所有对话框现在正确继承 Fluent Design 主题
- 支持亮色/暗色主题自动切换
- 文字颜色在所有主题下均可见

### 代码质量
- 重构历史记录对话框（protocol_history_dialog.py 和 history_dialog.py）
- 更新 main_window.py 传递历史管理器
- 改进 models/protocol.py 类型检查逻辑

## 📦 文件变更

### 新增文件
- `ui/protocol_history_dialog.py` - 协议历史对话框

### 修改文件
- `ui/history_dialog.py` - 重构为 Fluent Design
- `ui/fluent_protocol_interface.py` - 添加历史按钮
- `ui/fluent_analysis_interface.py` - 添加历史按钮
- `main_window.py` - 集成历史管理器
- `models/protocol.py` - 修复端序检查

## 🔄 升级说明

从 v1.4.0 升级到 v1.4.1 无需任何额外操作，直接运行新版本即可。

历史记录功能现在可以正常使用，文字在所有主题下均清晰可见。

## 📊 统计信息

- 21 个文件更改
- 3546 行新增代码
- 234 行删除代码
