# 串口数据分析工具

一个用于解析和验证串口通信数据帧的桌面应用程序。

**当前版本：v1.6.0** | **最后更新：2026-02-21**

## 快速开始

```bash
# 运行程序
./.qtcreator/Python_3_10_12venv/bin/python main_window.py

# 运行测试
./test_v1.3.0.sh
```

## 主要特性

### 🎯 核心功能
✅ 支持自定义协议配置  
✅ 灵活的校验算法（累加和、CRC16、CRC32、异或）  
✅ 可自定义校验范围（从第N字节到第M字节）  
✅ 直观的图形界面（Fluent Design）  
✅ 字段可视化解析  
✅ 结果导出（TXT/CSV）  
✅ 点击高亮联动功能  

### 🆕 v1.5.3 最新功能 (2026-01-30) ✨
✅ **HEX日志提取增强** - 支持短横线分隔、冒号分隔、中英文冒号兼容  
✅ **字段边界区分 (Zebra Striping)** - 相邻字段交替底色，一眠辨识字段范围  
✅ **校验配置人性化** - 字节位置从第1字节开始计数，告别 0-based 索引  
✅ **高级字段保护** - UI 保存不再丢失位域、计算表达式等配置  

### 📋 v1.5.0 ~ v1.5.2 (2026-01)
✅ **点击高亮联动** - 点击字节/字段标签实现双向高亮联动  
✅ **HEX日志提取器** - 从串口调试日志提取HEX数据帧  
✅ **Windows 高DPI适配** - Per-Monitor DPI Awareness  
✅ **性能优化** - 预定义样式、状态检查、最小化刷新  

### 📋 v1.4.x 功能 (2025-12)
✅ **Fluent Design UI** - 采用PySide6-Fluent-Widgets实现现代化界面  
✅ **虚拟滚动优化** - 支持大数据量（10000+帧）的流畅显示  
✅ **帧详情面板** - 点击帧可查看详细的字节和字段解析  
✅ **项目管理** - 支持保存/加载完整项目配置  

### 📋 v1.3.1 功能 (2025-11-19)
✅ **简化协议配置** - 全新的绝对位置配置方式，更直观易用  
✅ **固定帧长度支持** - 避免数据中伪帧尾标识导致的解析错误  
✅ **GUI 配置增强** - 新增固定帧长度和绝对位置配置输入控件  
✅ **多策略帧识别** - 固定长度 → 长度字段 → 帧尾搜索，自动选择最佳策略  
✅ **配置向导文档** - 完整的配置指南和实际案例（Langhua 协议）  
✅ **Bug 修复** - 修复多个 UI 和解析相关的问题  

### 📋 v1.3.0 功能 (2025-11-01)
✅ **字段类型下拉选择** - 协议配置中数据类型改为下拉菜单，避免输入错误  
✅ **字段彩色显示** - 可为不同字段类型配置颜色，分析结果以HTML彩色显示  
✅ **分析历史记录** - 自动保存每次分析，支持查看和对比历史记录  
✅ **颜色配置UI** - 在设置Tab中自定义10种字段类型的颜色  
✅ **历史记录对话框** - 查看详细的分析历史，包括时间、协议、统计、帧摘要  

### 📜 v1.2.0 功能
✅ **协议格式自动转换** - 支持标准格式和扩展格式JSON  
✅ **格式说明Tab** - 内置协议JSON格式文档和示例  
✅ **协议历史记录** - 快速切换最近使用的协议  
✅ **AI友好** - 可让AI助手直接生成协议JSON文件  

## 协议配置

### 支持的JSON格式

#### 简化格式（v1.3.1+ 推荐）✨
```json
{
  "protocol_name": "示例协议",
  "version": "1.0",
  "frame_header": "68",
  "frame_tail": "16",
  "frame_length": 106,
  "checksum_config": {
    "checksum_type": "sum",
    "checksum_position": 104,
    "checksum_start": 0,
    "checksum_end": 104,
    "checksum_length": 1
  },
  "fields": [
    {
      "name": "设备地址",
      "byte_count": 1,
      "field_type": "uint8",
      "description": "设备地址",
      "order": 0
    }
  ]
}
```

> 💡 **简化配置优势**：
> - 使用 `frame_length` 指定固定帧长度，避免数据中伪帧尾干扰
> - 使用 `checksum_position` 绝对位置，更直观明确
> - 使用 `checksum_start/end` 绝对范围，无需计算偏移量

#### 标准格式（旧版，仍然支持）
```json
{
  "protocol_name": "示例协议",
  "version": "1.0",
  "frame_header": "68",
  "frame_tail": "16",
  "checksum_config": {
    "checksum_type": "累加和",
    "position": "帧尾前",
    "start_offset": 0,
    "end_offset": -1,
    "checksum_length": 1
  },
  "fields": [...]
}
```

#### 扩展格式（自动转换）
```json
{
  "protocol_name": "工业协议",
  "fields": [
    {
      "index": 0,
      "name": "设备地址",
      "byte_count": 1,
      "field_type": "fixed",
      "format": "HEX"
    }
  ]
}
```

> 💡 **提示**: 可以让ChatGPT/Claude等AI助手根据协议文档生成JSON，程序会自动识别并转换格式！

## 文档

详细文档请查看 `document/` 目录：

- **📖 配置指南**（推荐）：`PROTOCOL_CONFIG_GUIDE.md` - 简化配置完整教程
- **⚡ 快速参考**：`CONFIG_QUICK_REFERENCE.md` - 配置字段速查表
- **🎯 配置示例**：`protocol_simple_example.json` - 简化配置模板
- **📚 使用指南**：`document/使用指南_20251101.md`
- **💡 功能说明**：`document/功能说明.md`
- **🏗️ 架构设计**：`document/架构设计_20251101.md`
- **👨‍💻 开发指南**：`document/QUICKSTART_20251101.md`
- **🔄 格式转换**：`document/功能更新_协议格式兼容_20251101.md`
- **✅ 测试报告**：`document/测试报告_协议格式兼容_20251101.md`

## 版本历史

### V1.6.0 (2026-02-21)
- 🏗️ 架构级代码质量重构 - 14+ 文件全面规范化
- 🎨 主题系统重构 - ThemeHelper 集中管理颜色/样式
- ✨ 高亮联动 7 项 Bug 修复 - 帧切换重置、深色主题可读性、ScrollArea 点击等
- ✨ 用户偏好系统 - 自动切换帧详情开关等持久化设置
- ✨ 协议格式检测增强 - 多数投票代替首字段判断
- ✨ 校验魔法数字常量化 + 旧版 offset 弃用警告
- 🐛 修复 float 精度、QThread 优雅关闭、SQLite 迁移等架构问题
- 📝 文档版本同步与许可证补全

### V1.5.x (2026-01)
- ✨ 点击高亮联动功能
- ✨ HEX日志提取器小工具
- ✨ Windows 高DPI适配优化
- ✨ Zebra Striping 字段边界区分
- ✨ 校验配置 1-based 人性化显示
- 🐛 修复多个解析和UI相关问题

### V1.4.x (2025-12)
- ✨ Fluent Design UI 界面
- ✨ 虚拟滚动支持大数据量
- ✨ 帧详情面板
- ✨ 项目管理功能

### V1.3.1 (2025-11-19)
- ✨ 简化协议配置 - 绝对位置配置方式
- ✨ 固定帧长度支持
- ✨ 多策略帧识别

### V1.2.0 (2025-11-01)
- ✨ 新增协议格式自动转换功能
- ✨ 新增格式说明Tab
- ✨ 新增协议历史记录功能
- 🐛 修复字段类型兼容性问题
- 📝 完善文档和测试

### V1.0 (2025-11-01)
- 🎉 初始版本发布
- ✨ 基础协议解析功能
- ✨ 自定义校验范围
- ✨ 可编辑字段表

## 技术栈

- Python 3.10+
- PySide6 (Qt 6.10)
- 模块化架构设计 (models/core/utils)

## 项目结构

```
SerialDataCompare/
├── main_window.py          # 主窗口
├── models/                 # 数据模型
│   ├── protocol.py         # 协议配置
│   └── data_frame.py       # 数据帧
├── core/                   # 核心逻辑
│   ├── parser.py           # 数据解析器
│   ├── checksum.py         # 校验计算器
│   ├── protocol_manager.py # 协议管理
│   ├── protocol_converter.py  # 格式转换器
│   └── protocol_history.py    # 历史记录
├── utils/                  # 工具函数
│   └── helpers.py          # 辅助函数
└── document/               # 文档

## 许可证

本项目采用 MIT 许可证开源。详情请参见 [LICENSE](LICENSE) 文件。
