# 变更日志 (CHANGELOG)

## [1.3.2] - 2025-11-20

### 🐛 Bug 修复
- 修复 UI 中使用 emoji 字符导致的 UTF-8 编码错误（`UnicodeEncodeError: surrogates not allowed`）
- 修复 `ProtocolConfig.to_dict()` 方法未保存简化配置字段的问题（`frame_length`, `checksum_position`, `checksum_start`, `checksum_end`）

### 🎨 UI/UX 改进
- 简化校验范围标签文本（"到（不含）" → "到"），避免界面布局偏移
- 为校验范围控件添加详细的工具提示（tooltip），说明 Python 切片语义
- 新增提示标签："[提示] 结束位置不包含，如'从0到81'实际计算0~80"
- 优化控件间距，添加水平间隔器改善布局

### 📚 文档更新
- 在 `PROTOCOL_CONFIG_GUIDE.md` 中添加 Python 切片语义的详细说明和警告
- 增加两个完整的协议配置案例（83字节和106字节帧）及 ASCII 图示
- 说明 GUI 显示与实际计算范围的对应关系

### 🔧 项目管理
- 整理测试脚本：创建 `tests/` 文件夹，移动 9 个测试文件（`analyze_*.py`, `test_*.py`, `verify_*.py`, `diagnose_*.py`）

## [1.3.1] - 2025-11-19

### 🎉 新增功能

#### 1. 简化协议配置（重大更新）
- **新增绝对位置配置方式**：更直观、更易用的协议配置
  - `frame_length`：直接指定固定帧长度，避免数据中伪帧尾干扰
  - `checksum_position`：校验码在帧中的绝对位置（从0开始索引）
  - `checksum_start` 和 `checksum_end`：校验计算的绝对起止位置
  - 完全兼容旧版 `start_offset` 和 `end_offset` 配置

#### 2. GUI 界面增强
- 协议配置界面新增"固定帧长度"输入框
- 新增"简化配置"选项组
  - "使用绝对位置"复选框
  - 校验码位置绝对索引输入
  - 校验计算范围（从/到）输入
- 简化配置与旧版配置可自由切换，互不干扰

#### 3. 更强壮的帧解析逻辑
- **多策略帧识别**：
  1. 优先使用固定帧长度（`frame_length`）
  2. 其次使用长度字段动态计算（`length_field_name`）
  3. 最后降级到帧头+帧尾搜索
- 避免数据负载中包含帧尾标识导致的错误截断

### 🐛 Bug 修复
- 修复 UI 控件名称错误（`spinBox_checksum_abs_*` 不存在）导致的 AttributeError
- 修复 UI 表单 FormLayout 行号重叠导致的控件显示重叠
- 修复 `ChecksumType` 枚举转换引用不存在的 CRC8 类型
- 修复 `protocol.name` 应为 `protocol.protocol_name` 的属性错误
- 修复校验范围负偏移语义错误（`end_offset=-1` 含义修正）

### 📚 文档更新
- 新增 `PROTOCOL_CONFIG_GUIDE.md`：简化配置完整使用指南
- 新增 `CONFIG_QUICK_REFERENCE.md`：配置字段快速参考表
- 新增 `protocol_simple_example.json`：简化配置示例文件
- 更新 Langhua.json 为简化配置格式（实际案例）
- 在配置指南中添加 Langhua 协议配置诊断和解决过程

### 🔧 代码改进
- 重构 `DataParser.find_frames`：实现多策略帧识别
- 重构 `ChecksumValidator.validate_frame`：支持绝对位置和旧版配置
- 优化 `ProtocolConfig.from_dict`：自动识别并转换配置格式
- 改进 `_convert_checksum_type`：移除不存在的 CRC8 映射，增强容错

### 💡 技术亮点
- **配置优先级**：绝对位置配置 > 偏移量配置（自动判断）
- **帧识别优先级**：固定长度 > 长度字段 > 帧尾搜索
- **UI 状态联动**：简化配置启用时自动禁用旧版配置输入
- **完全向后兼容**：旧版协议配置文件无需修改仍可正常使用

### 📦 配置迁移示例

**旧版配置**：
```json
{
  "checksum_config": {
    "position": "帧尾后",
    "start_offset": 0,
    "end_offset": -1
  }
}
```

**新版简化配置（推荐）**：
```json
{
  "frame_length": 106,
  "checksum_config": {
    "checksum_position": 104,
    "checksum_start": 0,
    "checksum_end": 104
  }
}
```

---

## [1.3.0] - 2025-11-01

### 🎉 新增功能

#### 1. 字段类型下拉选择
- 在协议配置的字段表格中，数据类型列改为下拉选择框
- 新增 `ComboBoxDelegate` 类实现表格单元格下拉框
- 支持10种数据类型选择：uint8, uint16, uint32, int8, int16, int32, float, double, bytes, string
- 避免手动输入导致的拼写错误，提高配置效率

#### 2. 字段类型颜色配置
- 新增 `ColorConfig` 类管理字段类型颜色配置
- 在设置Tab添加"字段类型颜色配置"分组
- 为每种字段类型配置独立的显示颜色
- 使用HTML格式在分析结果中显示彩色字段（字段名背景色）
- 支持自定义颜色和恢复默认颜色
- 颜色配置持久化保存到 `~/.serialdatacompare/color_config.json`
- 默认提供10种协调的颜色方案（绿/蓝/紫/粉/黄/灰色系）

#### 3. 分析历史记录
- 新增 `AnalysisHistory` 类管理分析历史
- 新增 `HistoryDialog` 对话框显示历史记录
- 每次分析完成后自动保存结果
- 在数据分析Tab添加"查看历史记录"按钮
- 历史记录包含：时间戳、协议名称、统计信息、前10帧摘要
- 支持查看详细信息和清空历史
- 最多保存20条记录，自动删除最旧记录
- 历史数据保存到 `~/.serialdatacompare/analysis_history.json`

### 🔧 改进

- 修改 `DataFrame.add_field()` 支持字段类型参数
- 新增 `DataFrame.get_detailed_info_html()` 方法，生成HTML格式的彩色显示
- 修改 `DataParser` 在解析时记录并传递字段类型
- 优化主窗口初始化流程，集成颜色配置和分析历史管理
- 改进帧详细信息显示，使用HTML格式替代纯文本

### 📝 文档更新

- 新增 `document/v1.3.0_完整功能实现_20251101.md` - 详细功能说明（300+行）
- 新增 `document/快速使用指南_v1.3.0.md` - 用户使用指南
- 新增 `test_v1.3.0.sh` - 完整自动化测试脚本（7项测试）

### 🧪 测试

- 新增7项自动化测试：
  1. ✅ 新增文件检查 (5个)
  2. ✅ 修改文件检查 (6个)
  3. ✅ Python模块导入测试
  4. ✅ ComboBox Delegate功能测试
  5. ✅ 颜色配置功能测试
  6. ✅ 分析历史功能测试
  7. ✅ DataFrame HTML输出测试
- 主窗口初始化验证通过
- 所有测试用例通过：7/7 (100%)

### 📦 文件结构

```
新增文件：
  utils/delegates.py              - ComboBox委托 (44行)
  core/color_config.py            - 颜色配置管理 (72行)
  core/analysis_history.py        - 分析历史管理 (110行)
  ui/__init__.py                  - UI模块初始化 (6行)
  ui/history_dialog.py            - 历史记录对话框 (155行)
  test_v1.3.0.sh                  - 自动化测试脚本
  document/v1.3.0_完整功能实现_20251101.md
  document/快速使用指南_v1.3.0.md

修改文件：
  main_window.py                  - 集成所有新功能
  models/data_frame.py            - 添加HTML输出和字段类型存储
  core/parser.py                  - 记录字段类型
  core/__init__.py                - 导出ColorConfig
  form.ui                         - 添加颜色配置UI和历史按钮
  ui_form.py                      - 重新生成
```

### 🎯 版本对比

| 功能 | v1.2.1 | v1.3.0 |
|-----|--------|--------|
| 字段类型输入 | 手动输入 | **下拉选择** ✨ |
| 结果显示 | 纯文本 | **HTML彩色** ✨ |
| 字段颜色 | 无 | **可配置** ✨ |
| 历史记录 | 仅协议历史 | **增加分析历史** ✨ |

---

## [1.2.1] - 2025-11-01

### 🔧 改进

#### 自动清空分析结果
- 每次点击"开始分析"前自动清空之前的结果
- 清空内容包括：文本显示区（textEdit_result）、表格（tableWidget_frames）、解析结果对象（parse_result）
- 避免结果混淆，提供更好的用户体验

#### 优化显示格式
- 在 `DataFrame.get_detailed_info()` 中添加分隔线（=== 和 ---）增强层次结构
- 字段名左对齐，数值右对齐，改善可读性
- bytes类型字段尝试显示ASCII内容（可打印字符显示为 `[text]`）
- 校验失败使用 `⚠️ 警告` 高亮提示，更加醒目

### 📝 文档更新

- 新增 `document/v1.2.1_用户体验改进_20251101.md` - UX改进说明
- 新增 `test_v1.2.1.sh` - 测试脚本

### 🧪 测试

- 所有测试通过：3/3 (100%)
- 验证文件修改、模块导入、显示格式

---

## [1.2.0] - 2025-11-01

### ✨ 新增功能

#### 协议格式自动转换
- 新增 `ProtocolConverter` 类，支持标准格式和扩展格式JSON自动识别和转换
- 支持字段类型映射：fixed→bytes, variable→bytes, command→uint8, array→bytes
- 支持范围索引解析（如 "16-65" → 50字节）
- 自动跳过帧头、帧尾、校验码字段

#### 协议格式说明Tab
- 在UI中新增"协议格式说明"标签页
- 提供两种JSON格式的完整示例和说明
- 包含字段类型映射表和使用提示
- 方便AI助手和用户创建协议JSON

#### 历史记录功能
- 新增 `ProtocolHistory` 类管理最近使用的协议
- 在"文件"菜单中新增"最近的协议"子菜单
- 自动保存最近10个协议文件路径和名称
- 支持快速加载历史协议
- 支持清空历史记录
- 自动过滤已删除的文件

### 🐛 Bug修复
- 修复 `protocol_example.json` 格式不符合最新规范的问题
- 修复协议加载时格式不兼容导致的错误

### 📝 文档更新
- 新增 `功能更新_协议格式兼容_20251101.md` - 详细功能说明
- 新增 `测试报告_协议格式兼容_20251101.md` - 完整测试报告
- 新增 `v1.2.0_开发完成总结_20251101.md` - 开发总结
- 更新 `README.md` - 添加新功能说明和示例
- 更新 `README_文档目录.md` - 更新文档列表

### 🧪 测试
- 新增 `test_converter.py` 单元测试文件
- 测试覆盖率：95%
- 所有测试用例通过：4/4 (100%)

### 📦 文件结构
```
新增文件：
  core/protocol_converter.py      - 格式转换器 (202行)
  core/protocol_history.py        - 历史记录管理 (119行)
  test_converter.py               - 单元测试 (150行)
  protocol_extended_example.json  - 扩展格式示例
  document/功能更新_协议格式兼容_20251101.md
  document/测试报告_协议格式兼容_20251101.md
  document/v1.2.0_开发完成总结_20251101.md

修改文件：
  core/protocol_manager.py        - 集成格式转换器
  main_window.py                  - 添加历史记录功能
  form.ui                         - 新增格式说明Tab
  protocol_example.json           - 更新为标准格式
  README.md                       - 更新项目说明
```

---

## [1.0.0] - 2025-11-01

### 🎉 初始版本

#### 核心功能
- ✅ 串口数据帧解析
- ✅ 自定义协议配置
- ✅ 多种校验算法（累加和、XOR、CRC16、CRC32）
- ✅ 自定义校验范围（start_offset, end_offset）
- ✅ 字段可视化显示
- ✅ 结果导出（TXT/CSV）

#### 架构设计
- 模块化架构：models/core/utils
- 数据模型：ProtocolConfig, DataFrame, ChecksumConfig
- 核心逻辑：DataParser, ChecksumValidator, ProtocolManager
- UI组件：3个Tab（数据分析、协议配置、设置）

#### 文档
- 完整的用户文档和开发文档
- 架构设计说明
- 快速开始指南
- 使用指南

#### 技术栈
- Python 3.10+
- PySide6 (Qt 6.10)
- 虚拟环境：`.qtcreator/Python_3_10_12venv/`

---

## 版本说明

### 语义化版本
遵循 [Semantic Versioning](https://semver.org/) 规范：
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 变更类型
- ✨ **新增功能** (Added)
- 🔄 **功能变更** (Changed)
- ⚠️ **废弃功能** (Deprecated)
- ❌ **移除功能** (Removed)
- 🐛 **Bug修复** (Fixed)
- 🔒 **安全修复** (Security)
