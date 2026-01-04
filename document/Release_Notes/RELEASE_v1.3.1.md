# Release v1.3.1 - 简化协议配置和UI增强

**发布日期**: 2025-11-19  
**版本号**: v1.3.1  
**提交**: 7a1da6e  

---

## 🎉 主要更新

### 1. 全新简化配置方式

现在支持更直观的绝对位置配置，无需复杂的偏移计算！

**新增配置字段**：
- `frame_length`: 固定帧长度（避免数据中伪帧尾干扰）
- `checksum_position`: 校验码绝对位置（从0开始）
- `checksum_start`: 校验计算起始位置
- `checksum_end`: 校验计算结束位置

**配置对比**：

```json
// 旧版配置（复杂）
{
  "checksum_config": {
    "position": "帧尾后",
    "start_offset": 0,
    "end_offset": -1
  }
}

// 新版简化配置（推荐）✨
{
  "frame_length": 106,
  "checksum_config": {
    "checksum_position": 104,
    "checksum_start": 0,
    "checksum_end": 104
  }
}
```

### 2. GUI 界面增强

协议配置界面新增控件：
- ✅ 固定帧长度输入框
- ✅ "使用绝对位置"复选框
- ✅ 校验码位置输入（绝对索引）
- ✅ 校验计算范围输入（从/到）
- ✅ 与旧版配置自动切换

![GUI增强](document/screenshots/simplified_config.png)

### 3. 更强壮的帧解析

**多策略帧识别**（按优先级）：
1. 固定帧长度（`frame_length`）- 最可靠
2. 长度字段（`length_field_name`）- 动态长度
3. 帧头+帧尾搜索 - 兜底方案

**解决的问题**：
- ❌ 数据负载中包含帧尾标识 → ✅ 使用固定长度避免
- ❌ 校验计算偏移难理解 → ✅ 绝对位置一目了然
- ❌ 配置错误难排查 → ✅ 直观的位置索引

---

## 🐛 Bug 修复

1. **UI控件名称错误**
   - 修复 `spinBox_checksum_abs_position` 等控件不存在的错误
   - 统一为 `spinBox_checksum_position` 等正确名称

2. **UI布局重叠**
   - 修复 FormLayout 中 row 行号重复导致的控件重叠
   - 删除重复的控件定义

3. **枚举类型错误**
   - 移除 `ChecksumType.CRC8` 不存在的枚举值引用
   - 增强枚举转换容错性

4. **属性名称错误**
   - 修复 `protocol.name` 应为 `protocol.protocol_name`

5. **校验范围语义**
   - 修正负偏移 `end_offset=-1` 的语义处理
   - 绝对位置和偏移量正确转换

---

## 📚 文档完善

### 新增文档

1. **PROTOCOL_CONFIG_GUIDE.md**
   - 完整的配置指南
   - 新旧配置对比
   - 常见问题解答
   - Langhua 协议实际案例

2. **CONFIG_QUICK_REFERENCE.md**
   - 配置字段速查表
   - 各字段说明和示例

3. **protocol_simple_example.json**
   - 简化配置模板
   - 开箱即用

### 实际案例

**Langhua 协议诊断过程**：
- 问题：106字节帧，期望校验0xC0，实际0x94
- 诊断：枚举校验范围，找到3个匹配
- 解决：选择 `bytes[0:104]`（从帧头到校验前）
- 结果：✅ 校验通过！

详见 `PROTOCOL_CONFIG_GUIDE.md` 末尾案例。

### 更新文档

- ✅ README.md - 版本更新和新功能说明
- ✅ CHANGELOG.md - 详细变更记录

---

## 🔧 技术改进

### 代码重构

1. **DataParser.find_frames**
   - 重构为多策略模式
   - 优先级：固定长度 → 长度字段 → 帧尾搜索
   - 每种策略独立实现，易于维护

2. **ChecksumValidator.validate_frame**
   - 接受 `ChecksumConfig` 对象参数
   - 自动识别简化配置 vs 旧版配置
   - 统一校验逻辑

3. **ProtocolConfig.from_dict**
   - 增强配置解析
   - 自动填充新字段
   - 向后兼容旧版JSON

### 向后兼容

- ✅ 旧版协议JSON无需修改
- ✅ 旧版UI配置继续工作
- ✅ 自动识别配置类型
- ✅ 平滑升级无缝切换

---

## 📦 文件清单

### 新增文件
```
CONFIG_QUICK_REFERENCE.md          # 配置快速参考
PROTOCOL_CONFIG_GUIDE.md           # 配置完整指南
protocol_simple_example.json       # 简化配置示例
document/Protocol_json_format/Langhua/Langhua.json  # Langhua协议配置
analyze_complete_protocol.py       # 完整解析测试脚本
verify_langhua.py                  # Langhua验证脚本
test_analyze_button.py             # 按钮测试脚本
```

### 修改文件
```
CHANGELOG.md                       # 变更日志
README.md                          # 项目说明
form.ui                            # UI表单
main_window.py                     # 主窗口
models/protocol.py                 # 协议模型
core/parser.py                     # 解析器
core/checksum.py                   # 校验器
```

---

## 🚀 升级指南

### 对于用户

1. **更新代码**
   ```bash
   git pull origin main
   git checkout v1.3.1
   ```

2. **查看新功能**
   - 打开GUI，进入"协议配置"标签页
   - 查看新增的"固定帧长度"和"简化配置"选项

3. **尝试新配置**
   - 参考 `protocol_simple_example.json`
   - 或查看 `PROTOCOL_CONFIG_GUIDE.md`

### 对于开发者

1. **API 变更**
   ```python
   # 新增字段
   protocol.frame_length: Optional[int]
   protocol.length_field_name: Optional[str]
   
   # ChecksumConfig 新增字段
   checksum_config.checksum_position: Optional[int]
   checksum_config.checksum_start: Optional[int]
   checksum_config.checksum_end: Optional[int]
   ```

2. **调用变更**
   ```python
   # ChecksumValidator 新API
   ChecksumValidator.validate_frame(
       data: bytes,
       checksum_config: ChecksumConfig  # 传入整个config对象
   )
   ```

---

## 💡 使用建议

1. **新项目**：直接使用简化配置（`frame_length` + `checksum_position`）

2. **现有项目**：
   - 如遇到校验问题，尝试简化配置
   - 如数据中有伪帧尾，启用 `frame_length`
   - 旧配置仍可正常工作

3. **调试技巧**：
   - 校验失败时，使用 `analyze_complete_protocol.py` 枚举范围
   - 参考 Langhua 案例的诊断流程

---

## 📊 统计信息

- **新增代码**: 2263 行
- **修改文件**: 19 个
- **新增文档**: 3 个
- **修复Bug**: 5 个
- **新功能**: 4 个

---

## 🙏 致谢

感谢所有测试和反馈的用户！

特别感谢 Langhua 协议案例，帮助我们发现并解决了校验配置的易用性问题。

---

## 📞 反馈与支持

- **Issues**: https://github.com/Aspiring-Freeman/SerialDataCompare/issues
- **文档**: 项目根目录 `document/` 文件夹

---

**下载**: [Release v1.3.1](https://github.com/Aspiring-Freeman/SerialDataCompare/releases/tag/v1.3.1)
