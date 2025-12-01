# SerialDataCompare v1.4.3 发布说明

**发布日期**: 2025-11-30

## 🎯 版本亮点

本版本主要修复了文件操作的稳定性问题，增强了删除协议的用户体验，并修复了UI显示问题。

## ✨ 新功能

### 1. 删除协议两种选项
- **仅从项目中移除**: 将协议文件移动到 `.removed` 文件夹，保留文件不删除
- **永久删除文件**: 彻底删除磁盘上的文件
- 默认选择"仅移除"，更加安全

## 🐛 问题修复

### 1. 帧详情结束位置显示错误
- **问题**: 24字节数据显示结束位置为22，应该是23
- **修复**: 正确显示最后一个字节的索引（包含）

### 2. 文件夹移动后出现重复
- **问题**: 跨设备/文件系统移动文件夹时，旧文件夹未被删除
- **修复**: 使用 `copytree + rmtree` 替代 `shutil.move`

### 3. 协议扫描显示已移除的文件
- **问题**: `.removed` 文件夹中的协议仍被扫描显示
- **修复**: 排除所有以 `.` 开头的隐藏文件夹和文件

### 4. 跨设备文件操作失败
- **问题**: 在不同分区/设备间移动文件可能失败
- **修复**: 所有文件移动操作改用 `copy + remove` 模式

### 5. 按钮提示出现黑框
- **问题**: 鼠标悬停在刷新、新建等按钮上时出现黑色边框
- **修复**: 移除原生 Qt tooltip，避免主题兼容性问题

## 🔧 技术改进

### 文件操作健壮性
- 协议拖放移动: `shutil.copy2 + os.remove`
- 协议剪贴板粘贴: `shutil.copy2 + os.remove`
- 文件夹拖放移动: `shutil.copytree + shutil.rmtree`
- 重命名操作: 添加 `os.rename` 失败时的回退机制

### 协议扫描优化
```python
# 排除隐藏文件夹
dirs[:] = [d for d in dirs if not d.startswith('.')]

# 排除隐藏文件
if file.startswith('.'):
    continue
```

## 📁 修改的文件

- `ui/project_navigation.py` - 删除协议对话框、文件操作修复、移除tooltip
- `ui/project_dialog.py` - 新增 `DeleteProtocolDialog` 类、移除tooltip
- `ui/fluent_protocol_interface.py` - 移除tooltip
- `ui/fluent_analysis_interface.py` - 移除tooltip
- `core/project_manager.py` - 扫描排除隐藏文件夹
- `ui/fluent_frame_detail_interface.py` - 结束位置显示修复
- `ui/fluent_project_interface.py` - 编辑项目对话框参数修复

## 📥 升级建议

建议所有用户升级到此版本，特别是：
- 经常移动/删除协议文件的用户
- 使用外部存储或网络驱动器的用户
- 遇到文件操作失败或UI黑框问题的用户

## 🔄 兼容性

- 完全向后兼容 v1.4.x
- 协议配置文件格式无变化
- 项目数据格式无变化
