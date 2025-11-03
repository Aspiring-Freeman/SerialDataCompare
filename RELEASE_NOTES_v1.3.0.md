# SerialDataCompare v1.3.0 Release Notes

**发布日期**: 2025年11月3日  
**版本**: v1.3.0  
**状态**: 稳定版 (Stable)

---

## 🎉 重要更新

SerialDataCompare v1.3.0 是一个功能完善的串口数据分析工具，提供了强大的协议配置、数据解析和可视化能力。

### ✨ 新增功能

#### 1. 字段类型下拉选择 🎯
- 协议配置表格中的数据类型列改为下拉菜单
- 支持10种数据类型快速选择：
  - **整数类型**: uint8, uint16, uint32, int8, int16, int32
  - **浮点类型**: float, double
  - **特殊类型**: bytes, string
- 避免手动输入错误，提升配置效率

#### 2. 字段类型颜色配置 🎨
- **可视化字段类型识别**
  - 不同数据类型使用不同背景颜色显示
  - 10种预设颜色方案
- **自定义颜色配置**
  - 在"设置"标签页可自定义每种类型的颜色
  - 颜色配置持久化保存
  - 支持重置为默认配色
- **HTML彩色显示**
  - 帧详细信息使用HTML格式
  - 字段名称带背景颜色
  - 提升数据可读性

#### 3. 分析历史记录 📊
- **自动保存分析结果**
  - 每次分析自动记录
  - 保存协议名称、统计信息、帧摘要
  - 最多保存20条历史记录
- **历史记录查看**
  - 点击"查看历史记录"按钮打开历史对话框
  - 显示时间戳、协议信息、分析统计
  - 支持清空历史记录
- **记录内容**
  - 时间戳
  - 协议名称
  - 输入数据
  - 总帧数、有效帧数、错误帧数
  - 前5个帧的摘要信息

#### 4. 用户体验改进 (v1.2.1) ⚡
- **自动清空分析结果**
  - 每次点击"开始分析"自动清空旧结果
  - 清空帧列表和详细信息区域
  - 避免新旧数据混淆
- **增强的错误提示**
  - 更详细的错误信息
  - 友好的用户提示

---

## 🔧 核心功能

### 协议配置系统
- ✅ **灵活的字段定义**
  - 10种数据类型支持
  - 大小端配置
  - 变长字段支持
- ✅ **可视化配置界面**
  - 表格式字段编辑
  - 下拉选择数据类型
  - 实时协议验证
- ✅ **协议管理**
  - 导入/导出JSON协议
  - 协议历史记录（最近5个）
  - 协议格式自动转换

### 数据解析引擎
- ✅ **多种校验算法**
  - 累加和 (SUM)
  - 异或校验 (XOR)
  - CRC8/16/32
- ✅ **自定义校验范围**
  - 支持负数偏移（包含帧头）
  - 灵活的起止位置配置
  - 校验码长度可配置
- ✅ **多线程解析**
  - 异步数据处理
  - 界面不卡顿
  - 进度实时反馈

### 数据可视化
- ✅ **帧列表视图**
  - 显示帧编号、位置、状态
  - 校验结果图标显示
  - 错误帧高亮标记
- ✅ **详细信息面板**
  - HTML彩色字段显示
  - 原始数据十六进制显示
  - 校验信息详细展示
  - 错误信息突出显示
- ✅ **颜色编码**
  - 不同字段类型不同颜色
  - 自定义颜色方案
  - 提升数据识别效率

---

## 📦 协议格式支持

### 标准JSON格式
```json
{
  "name": "示例协议",
  "description": "协议描述",
  "frame_header": "AA55",
  "frame_tail": "BBCC",
  "fields": [
    {
      "name": "字段名",
      "field_type": "uint8",
      "byte_count": 1,
      "byte_order": "little"
    }
  ],
  "checksum_config": {
    "checksum_type": "sum",
    "start_offset": 0,
    "end_offset": 0,
    "checksum_length": 1
  }
}
```

### 扩展JSON格式（兼容工业协议）
```json
{
  "Protocol": {
    "Name": "工业协议",
    "FrameHeader": "AA55",
    "Fields": [
      {
        "Name": "字段名",
        "Type": "uint8",
        "Length": 1
      }
    ]
  }
}
```

**自动格式识别**: 工具会自动检测并转换协议格式

---

## 🚀 技术架构

### 模块化设计
```
SerialDataCompare/
├── core/           # 核心业务逻辑
│   ├── parser.py              # 数据解析器
│   ├── checksum.py            # 校验算法
│   ├── protocol_manager.py   # 协议管理
│   ├── protocol_converter.py # 协议转换
│   ├── protocol_history.py   # 协议历史
│   ├── color_config.py        # 颜色配置 (NEW)
│   └── analysis_history.py   # 分析历史 (NEW)
├── models/         # 数据模型
│   ├── protocol.py            # 协议模型
│   └── data_frame.py          # 数据帧模型
├── ui/             # UI组件
│   └── history_dialog.py      # 历史对话框 (NEW)
├── utils/          # 工具函数
│   ├── delegates.py           # Qt委托 (NEW)
│   └── helpers.py             # 辅助函数
└── main_window.py  # 主窗口
```

### 技术栈
- **GUI框架**: PySide6 (Qt6)
- **数据格式**: JSON
- **多线程**: QThread异步处理
- **架构模式**: MVC模式
- **测试**: 完整的单元测试

---

## 📋 系统要求

### 最低要求
- **操作系统**: Windows 10+, Linux (Ubuntu 20.04+), macOS 11+
- **Python**: 3.8+
- **内存**: 512MB RAM
- **磁盘**: 100MB 可用空间

### 推荐配置
- **Python**: 3.10+
- **内存**: 2GB+ RAM
- **显示器**: 1920x1080

---

## 📥 安装指南

### 方法一: 使用pip安装依赖
```bash
# 克隆仓库
git clone https://github.com/Aspiring-Freeman/SerialDataCompare.git
cd SerialDataCompare

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main_window.py
```

### 方法二: 使用虚拟环境（推荐）
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main_window.py
```

### 依赖包列表
```
PySide6>=6.6.0
```

---

## 📖 快速使用

### 1. 配置协议
1. 切换到"协议配置"标签页
2. 填写基本信息：
   - 协议名称
   - 帧头（十六进制）
   - 帧尾（十六进制）
3. 配置字段：
   - 字段名称
   - 选择数据类型（下拉菜单）
   - 字节数
   - 字节序
4. 配置校验：
   - 选择校验类型
   - 设置校验范围
   - 校验码长度

### 2. 分析数据
1. 切换到"数据分析"标签页
2. 在输入框粘贴十六进制数据
3. 点击"开始分析"按钮
4. 查看解析结果：
   - 左侧：帧列表
   - 右侧：详细信息（彩色显示）

### 3. 自定义颜色
1. 切换到"设置"标签页
2. 找到"字段类型颜色配置"
3. 点击颜色按钮选择新颜色
4. 点击"重置颜色"恢复默认

### 4. 查看历史
1. 在"数据分析"标签页
2. 点击"查看历史记录"按钮
3. 浏览历史分析记录
4. 可选择清空历史

---

## 🔍 示例数据

### 简单示例
```
协议配置:
- 帧头: AA 55
- 帧尾: BB CC
- 字段: ID(uint8), Value(uint16)
- 校验: SUM

输入数据:
AA 55 01 00 64 65 BB CC

解析结果:
- 帧1: ID=1, Value=100, 校验通过 ✓
```

### 工业协议示例
```
协议配置:
- 帧头: FA FB
- 数据长度: 83字节
- 多个uint16字段
- 校验: SUM（包含帧头）

可参考: protocol_industrial_fixed.json
```

---

## 🐛 已知问题与修复

### v1.3.0 修复
- ✅ 修复了 `textEdit_result` 不存在导致分析失败的bug
- ✅ 修复了颜色配置未生效的问题
- ✅ 优化了字段类型传递逻辑

### 已知限制
- 单帧最大支持 64KB 数据
- 历史记录最多保存20条
- 颜色配置不支持渐变色

---

## 🔄 版本历史

### v1.3.0 (2025-11-03) - Current
- ✨ 字段类型下拉选择
- ✨ 字段类型颜色配置
- ✨ 分析历史记录
- ✨ HTML彩色字段显示
- 🐛 修复分析失败bug

### v1.2.1 (2025-11-01)
- ✨ 自动清空分析结果
- 💄 界面体验优化

### v1.2.0 (2025-11-01)
- ✨ 协议格式兼容性
- ✨ 协议历史管理
- 📝 完善文档系统

### v1.1.0 (2025-11-01)
- ✨ 自定义校验范围
- ✨ 负数偏移支持
- 🧪 完整测试覆盖

### v1.0.0 (2025-10-31)
- 🎉 初始版本
- ✨ 基础协议配置
- ✨ 数据解析功能
- ✨ 校验算法支持

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 报告问题
- 使用GitHub Issues
- 提供详细的复现步骤
- 附上协议配置和数据示例

### 提交代码
1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范
- 遵循PEP 8
- 添加单元测试
- 更新文档

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 📧 联系方式

- **GitHub**: https://github.com/Aspiring-Freeman/SerialDataCompare
- **Issues**: https://github.com/Aspiring-Freeman/SerialDataCompare/issues

---

## 🙏 致谢

感谢所有贡献者和用户的支持！

---

## 📚 相关文档

- [README.md](README.md) - 项目介绍
- [CHANGELOG.md](CHANGELOG.md) - 完整更新日志
- [快速使用指南](document/快速使用指南_v1.3.0.md)
- [开发文档](document/v1.3.0_开发完成报告_20251101.md)
- [技术实现](document/v1.3.0_完整功能实现_20251101.md)

---

**下载链接**: [SerialDataCompare-v1.3.0](https://github.com/Aspiring-Freeman/SerialDataCompare/releases/tag/v1.3.0)

**完整源代码**: [Source Code (zip)](https://github.com/Aspiring-Freeman/SerialDataCompare/archive/refs/tags/v1.3.0.zip)

---

*最后更新: 2025年11月3日*
