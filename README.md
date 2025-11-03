# 串口数据分析工具

一个用于解析和验证串口通信数据帧的桌面应用程序。

**当前版本：v1.3.0** | **最后更新：2025-11-01**

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
✅ 直观的图形界面  
✅ 字段可视化解析  
✅ 结果导出（TXT/CSV）  

### 🆕 v1.3.0 新功能 (2025-11-01) ✨
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

#### 标准格式（推荐）
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

- **快速上手**：`document/使用指南_20251101.md`
- **功能说明**：`document/功能说明.md`
- **架构设计**：`document/架构设计_20251101.md`
- **开发指南**：`document/QUICKSTART_20251101.md`
- **格式转换**：`document/功能更新_协议格式兼容_20251101.md`
- **测试报告**：`document/测试报告_协议格式兼容_20251101.md`

## 版本历史

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

[添加许可证信息]
