# SerialDataCompare v1.4.4 架构改进报告

## 概述

本次更新根据深度架构审计反馈，对核心模块进行了重构和增强，提升了代码的可维护性、可测试性和调试能力。

## 新增模块

### 1. 自定义异常体系 (`core/exceptions.py`)

提供细粒度的错误处理，替代通用 Exception：

```python
# 异常层次结构
SerialDataCompareError (基类)
├── ProtocolError (协议相关)
│   ├── ProtocolLoadError
│   ├── ProtocolValidationError
│   └── ProtocolConversionError
├── ParseError (解析相关)
│   ├── FrameNotFoundError
│   ├── FrameParseError
│   ├── FieldParseError
│   └── DataTruncatedError
├── ChecksumError (校验相关)
│   ├── ChecksumMismatchError
│   ├── ChecksumConfigError
│   └── ChecksumRangeError
├── ConfigError (配置相关)
│   ├── ConfigLoadError
│   └── ConfigSaveError
└── DataError (数据相关)
    ├── InvalidHexDataError
    └── DataLengthError
```

**特性**：
- 每个异常携带详细上下文 (details 字典)
- 支持异常链追踪 (`format_exception_chain`)
- 可将普通异常包装为自定义异常 (`wrap_exception`)

### 2. 解析上下文 (`core/parse_context.py`)

追踪解析过程，便于调试和错误定位：

```python
class ParseContext:
    # 核心功能
    - position: 当前解析位置
    - stage: 解析阶段 (INIT/FIND_HEADER/PARSE_FIELDS/VERIFY_CHECKSUM/...)
    - warnings: 警告列表
    - trace(): 记录追踪信息
    
    # 数据读取
    - peek(size): 预览数据
    - read(size): 读取并推进
    - find_pattern(pattern): 查找模式
    
    # 报告生成
    - get_summary(): 解析摘要
    - format_warnings(): 格式化警告
    - format_trace(): 追踪日志
```

**使用示例**：
```python
with ParseContextManager(raw_data, enable_trace=True) as ctx:
    ctx.set_stage(ParseStage.FIND_HEADER)
    header_pos = ctx.find_pattern(b'\x68')
    if header_pos < 0:
        ctx.add_warning("未找到帧头")
    # ...
print(ctx.format_trace())
```

### 3. 分析会话 (`core/analysis_session.py`)

封装完整的数据分析流程，解耦 GUI 与核心逻辑：

```python
class AnalysisSession:
    # 状态
    - state: SessionState (IDLE/LOADING/PARSING/COMPLETED/ERROR)
    - protocol: Protocol
    - raw_data: bytes
    - frames: List[DataFrame]
    
    # 操作
    - set_protocol(protocol)
    - set_raw_data(data, source)
    - parse() -> SessionResult
    - get_frame(index)
    - get_statistics()
    
    # 回调
    - add_state_callback(callback)
    - add_progress_callback(callback)

class SessionManager:
    - create_session(config) -> AnalysisSession
    - get_session(id)
    - switch_session(id)
    - sessions: List[AnalysisSession]
```

### 4. 分析控制器 (`core/analysis_controller.py`)

从 main_window 提取的核心分析逻辑，作为 GUI 与核心模块的桥梁：

```python
class AnalysisController(QObject):
    # 信号
    protocol_loaded = Signal(object)
    analysis_started = Signal()
    analysis_completed = Signal(object)
    analysis_failed = Signal(str)
    frame_selected = Signal(int, object)
    warning_occurred = Signal(str)
    
    # 核心方法
    - load_protocol(file_path) -> bool
    - analyze_hex_string(hex_string) -> bool
    - analyze_bytes(raw_data) -> bool
    - get_frame(index) -> DataFrame
    - export_frames_to_csv(file_path)
    - export_session_report(file_path)
```

## 增强模块

### 1. 协议转换器增强 (`core/protocol_converter.py`)

新增语义类型保留和智能类型推断：

```python
class SemanticType(Enum):
    HEADER, TAIL, ADDRESS, COMMAND, LENGTH,
    DATA, CHECKSUM, TIMESTAMP, COUNTER, STATUS, ...

class TypeMapping:
    field_type: FieldType
    semantic_type: SemanticType
    confidence: float  # 置信度
    source_hint: str   # 来源提示

# 增强的转换方法
convert_field_type_enhanced(field_type_str, field_name, byte_count) -> TypeMapping
infer_semantic_type(field_name, field_type_str, byte_count) -> (SemanticType, float)
```

**特性**：
- 从字段名关键词推断语义类型
- 根据字节数智能选择数据类型
- 保留缩放信息 (multiplier, unit) 和位域定义
- 转换置信度评估

### 2. 颜色配置增强 (`core/color_config.py`)

新增配置验证、迁移和类型安全：

```python
class ColorConfigValidator:
    - is_valid_color(color_str) -> bool
    - normalize_color(color_str) -> str  # -> #RRGGBB
    - validate_config(config) -> (bool, List[ColorValidationError])

class ColorConfig:
    # 新增功能
    - has_load_errors: bool
    - load_errors: List[ColorValidationError]
    - set_colors_batch(colors) -> (bool, List[str])
    - reset_color(field_type)
    - export_config(file_path)
    - import_config(file_path) -> (bool, List[str])
    
    # 版本迁移
    CONFIG_VERSION = 2
    _migrate_config(colors, from_version)
```

## 架构改进对照

| 审计问题 | 解决方案 |
|---------|---------|
| 通用 Exception 粒度不足 | 创建 `exceptions.py` 异常体系 |
| 解析过程难以调试 | 创建 `ParseContext` 追踪上下文 |
| 缺少核心数据流抽象 | 创建 `AnalysisSession` 封装会话 |
| main_window 职责过重 | 创建 `AnalysisController` 分离逻辑 |
| 类型映射丢失语义信息 | `SemanticType` + `TypeMapping` 增强 |
| 配置校验能力弱 | `ColorConfigValidator` + 版本迁移 |

## 文件变更

### 新增文件
- `core/exceptions.py` - 自定义异常体系
- `core/parse_context.py` - 解析上下文
- `core/analysis_session.py` - 分析会话
- `core/analysis_controller.py` - 分析控制器

### 修改文件
- `core/__init__.py` - 导出新模块
- `core/protocol_converter.py` - 语义类型增强
- `core/color_config.py` - 配置验证增强

## 使用示例

### 使用分析控制器

```python
from core import AnalysisController

controller = AnalysisController()

# 连接信号
controller.protocol_loaded.connect(on_protocol_loaded)
controller.analysis_completed.connect(on_analysis_done)
controller.warning_occurred.connect(on_warning)

# 加载协议
controller.load_protocol("protocol.json")

# 分析数据
controller.analyze_hex_string("68 00 01 02 03 16")

# 获取结果
for frame in controller.frames:
    print(f"帧 {frame.frame_index}: {frame.is_valid}")
```

### 使用解析上下文调试

```python
from core import ParseContextManager, ParseStage

with ParseContextManager(data, enable_trace=True) as ctx:
    ctx.set_stage(ParseStage.FIND_HEADER)
    # ... 解析逻辑
    ctx.trace("找到帧头", data[:5])
    
# 输出调试信息
if ctx.has_warnings:
    print(ctx.format_warnings())
print(ctx.format_trace())
```

### 使用自定义异常

```python
from core import FieldParseError, ChecksumMismatchError

try:
    parse_field(data, field_def)
except FieldParseError as e:
    print(f"字段 '{e.field_name}' 解析失败")
    print(f"位置: {e.position}, 期望 {e.expected_bytes} 字节")
except ChecksumMismatchError as e:
    print(f"校验失败: 期望 {e.expected:02X}, 实际 {e.actual:02X}")
```

## 后续计划

1. **渐进式迁移 main_window**：逐步将 main_window 中的分析逻辑迁移到 AnalysisController
2. **单元测试覆盖**：为新模块添加完整的单元测试
3. **性能优化**：ParseContext 的追踪功能可选启用以避免性能影响
4. **文档完善**：为新的 API 添加详细文档

## 兼容性

- 所有更改向后兼容
- 现有代码无需修改即可继续工作
- 新功能可按需逐步采用
