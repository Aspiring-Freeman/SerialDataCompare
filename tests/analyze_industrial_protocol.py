#!/usr/bin/env python3
"""
工业协议校验分析脚本
分析106字节数据帧的校验码计算
"""

# 实际数据帧（106字节）
data_hex = """
68 AD 6A 00 C8 0E DE 0D 0B 00 00 00 00 00 00 00 10 0E 00 00 01 01 01 01 
38 36 38 34 38 39 30 38 33 34 31 31 34 36 38 34 36 30 31 33 30 34 30 31 
36 32 39 39 33 32 38 39 38 36 30 38 38 30 31 31 32 35 38 30 35 32 39 39 
33 32 16 01 01 01 10 0E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
01 01 01 00 00 00 01 00 E6 16
""".replace('\n', ' ')

# 转换为字节列表
data_bytes = bytes.fromhex(data_hex)
print(f"总字节数: {len(data_bytes)}")
print(f"帧头: 0x{data_bytes[0]:02X}")
print(f"整包长度: {data_bytes[2]} (0x{data_bytes[2]:02X})")
print(f"实际校验码: 0x{data_bytes[104]:02X} ({data_bytes[104]})")
print(f"帧尾: 0x{data_bytes[105]:02X}")
print()

# 测试不同的校验范围
test_cases = [
    ("包含帧头 (0-103)", 0, 104),      # 从帧头到校验码前
    ("不含帧头 (1-103)", 1, 104),      # 从帧头后到校验码前
    ("原配置 (1-101)", 1, 102),        # 你的配置
    ("到字节102 (1-102)", 1, 103),    # 到102
    ("到字节103 (1-103)", 1, 104),    # 到103
]

print("=" * 70)
print("校验范围测试:")
print("=" * 70)

for desc, start, end in test_cases:
    checksum = sum(data_bytes[start:end]) & 0xFF  # 累加和取低8位
    match = "✓ 匹配!" if checksum == data_bytes[104] else "✗ 不匹配"
    print(f"{desc:25s}: 计算={checksum:3d} (0x{checksum:02X})  {match}")

print()
print("=" * 70)
print("数据帧结构分析:")
print("=" * 70)
print(f"字节0:       帧头 = 0x{data_bytes[0]:02X}")
print(f"字节1:       设备测试标识 = 0x{data_bytes[1]:02X}")
print(f"字节2:       整包长度 = {data_bytes[2]}")
print(f"字节3-103:   数据字段 (101字节)")
print(f"字节104:     校验码 = 0x{data_bytes[104]:02X}")
print(f"字节105:     帧尾 = 0x{data_bytes[105]:02X}")
print()

# 分析字段长度
print("=" * 70)
print("协议字段分析:")
print("=" * 70)

# 定义的字段总字节数
field_bytes = [
    ("字段1-22", 22, "22个1字节字段"),
    ("IMEI", 15, "15字节"),
    ("IMSI", 15, "15字节"),
    ("ICCID", 20, "20字节"),
    ("字段26", 1, "CSQ"),
    ("字段27", 1, "阀门状态"),
    ("字段28", 1, "阀门到位状态"),
    ("字段29", 1, "EEPROM状态"),
    ("字段30-31", 2, "GP30电压"),
    ("loraEUI", 16, "16字节"),
    ("字段33-36", 4, "4个1字节字段"),
    ("字段37-38", 2, "校验码2字节"),
    ("字段39-40", 2, "程序版本号2字节"),
]

total_defined = 0
for name, count, desc in field_bytes:
    total_defined += count
    print(f"{name:15s}: {count:2d}字节  ({desc})")

print(f"\n定义的字段总和: {total_defined}字节")
print(f"实际数据字段:   101字节")
print(f"缺少定义:       {101 - total_defined}字节")
print()

# 显示完整数据
print("=" * 70)
print("完整数据帧 (16进制):")
print("=" * 70)
for i in range(0, len(data_bytes), 16):
    hex_str = ' '.join(f'{b:02X}' for b in data_bytes[i:i+16])
    pos_str = f"{i:03d}-{min(i+15, len(data_bytes)-1):03d}"
    print(f"{pos_str}: {hex_str}")
