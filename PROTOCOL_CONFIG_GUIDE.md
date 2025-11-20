# 协议配置简化指南

## 简化后的配置方式（推荐）

现在你可以使用更简单、更直观的方式配置协议！

### 基本配置示例

```json
{
  "protocol_name": "工业通信器物协议",
  "version": "1.2",
  "description": "协议描述",
  "frame_header": "68",
  "frame_tail": "16",
  "frame_length": 106,
  "checksum_config": {
    "checksum_type": "sum",
    "checksum_position": 104,
    "checksum_length": 1,
    "checksum_start": 0,
    "checksum_end": 104
  },
  "fields": [...]
}
```

## 字段说明

### 帧配置

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `frame_header` | string | 是 | 帧头（十六进制） | `"68"` |
| `frame_tail` | string | 是 | 帧尾（十六进制） | `"16"` |
| `frame_length` | int | 推荐 | **固定帧长度**（总字节数，包括帧头帧尾） | `106` |

### 校验配置（checksum_config）

#### 简化配置（推荐）

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `checksum_type` | string | 是 | 校验类型：`sum`/`xor`/`crc16`/`crc32`/`none` | `"sum"` |
| `checksum_position` | int | 是 | **校验码在整帧中的位置**（从0开始） | `104` |
| `checksum_length` | int | 是 | 校验码字节数 | `1` |
| `checksum_start` | int | 是 | **校验计算起始位置**（从0开始） | `0` |
| `checksum_end` | int | 是 | **校验计算结束位置**（不包含，从0开始） | `104` |

## 配置说明

### 1. 固定帧长度 (`frame_length`)

- **含义**: 一个完整数据帧的总字节数（包括帧头、数据、校验码、帧尾）
- **作用**: 避免数据字段中的帧尾标识符导致误判
- **示例**: 你的106字节协议，设置 `"frame_length": 106`

### 2. 校验码位置 (`checksum_position`)

- **含义**: 校验码字节在整个帧中的索引位置（从0开始计数）
- **计算方法**: 
  - 如果校验码在倒数第2个字节：`frame_length - 2`
  - 你的协议：位置104 = 总长106 - 帧尾1字节 - 校验码位置
- **示例**: `"checksum_position": 104`

### 3. 校验范围

#### checksum_start（校验起始位置）
- **含义**: 从第几个字节开始计算校验（从0开始）
- **常见值**:
  - `0`: 从帧头开始（最常见）
  - `1`: 从帧头后第一个字节开始
- **你的协议**: `"checksum_start": 0`（从帧头开始）

#### checksum_end（校验结束位置）
- **含义**: 计算到第几个字节（不包含此位置，从0开始）
- **常见值**: 校验码的位置（不包含校验码本身）
- **你的协议**: `"checksum_end": 104`（到校验码前）

### 4. 校验范围示例

对于106字节的帧（索引0-105）：

```
位置:   0    1    2   ...  103  104  105
内容: [68] [AD] [6A] ... [数据] [E6] [16]
       ↑                          ↑    ↑
     帧头                      校验码 帧尾
```

配置：
```json
{
  "checksum_start": 0,    // 从位置0开始（包含帧头68）
  "checksum_end": 104     // 到位置104前（不包含校验码E6）
}
```

**计算范围**: 字节 0-103（共104字节）

## 完整示例

### 示例1：你的工业协议（106字节）

```json
{
  "protocol_name": "工业通信器物协议",
  "frame_header": "68",
  "frame_tail": "16",
  "frame_length": 106,
  "checksum_config": {
    "checksum_type": "sum",
    "checksum_position": 104,
    "checksum_length": 1,
    "checksum_start": 0,
    "checksum_end": 104
  }
}
```

- 总长度：106字节
- 帧头：位置0（0x68）
- 校验码：位置104（0xE6）
- 帧尾：位置105（0x16）
- 校验范围：0-103（包含帧头，不包含校验码和帧尾）

### 示例2：不包含帧头的校验

```json
{
  "frame_length": 50,
  "checksum_config": {
    "checksum_type": "sum",
    "checksum_position": 48,
    "checksum_length": 1,
    "checksum_start": 1,     // 从位置1开始（跳过帧头）
    "checksum_end": 48
  }
}
```

### 示例3：2字节CRC16校验

```json
{
  "frame_length": 100,
  "checksum_config": {
    "checksum_type": "crc16",
    "checksum_position": 97,    // CRC16占2字节，从97开始
    "checksum_length": 2,
    "checksum_start": 0,
    "checksum_end": 97
  }
}
```

## 旧版配置（兼容）

如果你不想使用新的简化配置，旧版的 `start_offset` 和 `end_offset` 仍然支持：

```json
{
  "checksum_config": {
    "checksum_type": "sum",
    "start_offset": -1,    // -1表示包含帧头
    "end_offset": 0,       // 0表示到校验码前
    "checksum_length": 1
  }
}
```

但**强烈推荐**使用新的简化配置，更清晰易懂！

## 配置验证

配置完成后，使用测试脚本验证：

```bash
python3 analyze_complete_protocol.py
```

查看输出中的"校验信息"部分：
- ✓ 成功：配置正确
- ✗ 失败：检查 `checksum_position`、`checksum_start`、`checksum_end` 配置

## 常见问题

### Q1: 校验总是失败？

检查：
1. `checksum_position` 是否指向正确的校验码位置
2. `checksum_start` 和 `checksum_end` 范围是否正确
3. `checksum_type` 是否匹配协议规范

### Q2: 如何确定校验码位置？

使用十六进制查看器或运行：
```python
data = bytes.fromhex("68 AD 6A ... E6 16")
print(f"第104个字节: 0x{data[104]:02X}")  # 应该是校验码
```

### Q3: 如何计算校验范围？

一般规则：
- **起始**: 通常从帧头开始（position 0）
- **结束**: 到校验码前（checksum_position）

特殊情况请参考协议文档。

## 总结

**新配置的优势**：
- ✅ 直接指定绝对位置，不需要复杂的偏移计算
- ✅ 配置清晰明了，减少出错
- ✅ 支持固定帧长度，避免数据中的帧尾标识干扰
- ✅ 同时兼容旧版配置

**推荐配置模板**：
```json
{
  "frame_length": <总字节数>,
  "checksum_config": {
    "checksum_type": "sum",
    "checksum_position": <校验码位置>,
    "checksum_length": 1,
    "checksum_start": 0,
    "checksum_end": <校验码位置>
  }
}
```

## 实际案例：Langhua 协议配置

### 问题背景
用户遇到一个 106 字节的工业通信帧，校验失败。原配置使用旧版偏移方式，解析时期望校验码为 0xC0，但实际为 0x94。

### 问题诊断
通过枚举不同的校验计算范围，发现以下三种范围都产生 0x94：
- `bytes[0:104]` - 从帧头到校验码前 ✓ **最合理**
- `bytes[1:8]` - 极小范围（不常见）
- `bytes[3:68]` - 中间片段（不常见）

根据工业协议惯例，选择 `bytes[0:104]`（从帧头开始，累加到校验码前一字节）。

### 解决方案
更新 Langhua.json 为简化配置：

```json
{
  "protocol_name": "工业通信器物协议_简化版",
  "version": "1.2",
  "frame_header": "68",
  "frame_tail": "16",
  "frame_length": 106,
  "checksum_config": {
    "checksum_type": "累加和",
    "checksum_position": 104,
    "checksum_start": 0,
    "checksum_end": 104,
    "checksum_length": 1
  },
  "fields": [...]
}
```

### 配置说明
- **frame_length: 106** - 整个数据帧固定长度，包括帧头（1字节）+ 数据（103字节）+ 校验码（1字节）+ 帧尾（1字节）
- **checksum_position: 104** - 校验码在第104个字节（从0开始索引）
- **checksum_start: 0, checksum_end: 104** - 从帧头（位置0）开始累加到校验码前（位置104，不包含）
- **checksum_type: "累加和"** - 使用累加和算法（所有字节相加取低8位）

### 验证结果
使用新配置后：
- ✅ 帧长度正确识别为 106 字节
- ✅ 校验计算范围：bytes[0:104]
- ✅ 期望校验码：0x94
- ✅ 实际校验码：0x94
- ✅ 校验通过！

### 经验总结
1. **优先使用固定帧长度** - 避免数据中的伪帧尾标识导致解析提前终止
2. **使用绝对位置配置** - 比偏移量更直观，减少配置错误
3. **校验范围通常从帧头开始** - 大多数工业协议都是累加整个有效载荷
4. **遇到校验失败时** - 可以枚举常见的校验范围组合，找出实际使用的范围

