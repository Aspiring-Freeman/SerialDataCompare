# 快速开始指南

## VS Code 配置说明

项目已经配置好了VS Code开发环境，包括：

### 1. Python 解释器
- 自动使用虚拟环境：`.qtcreator/Python_3_10_12venv/`
- 无需手动激活虚拟环境

### 2. 可用任务（Tasks）

在VS Code中按 `Ctrl+Shift+P` 然后输入 `Tasks: Run Task`，可以运行以下任务：

- **生成UI文件**: 将 `form.ui` 转换为 `ui_form.py`
- **运行主程序**: 启动应用程序
- **安装依赖**: 安装 requirements.txt 中的依赖包

### 3. 调试配置

按 `F5` 可以直接调试程序，已配置两个调试配置：
- **Python: 当前文件** - 调试当前打开的Python文件
- **Python: 主程序** - 调试 main_window.py

### 4. 自动格式化

保存Python文件时会自动：
- 格式化代码
- 整理导入语句

## 开发流程

### 第一次运行

1. **确保依赖已安装**
   ```bash
   ./.qtcreator/Python_3_10_12venv/bin/pip install -r requirements.txt
   ```
   或使用VS Code任务：`Tasks: Run Task` -> `安装依赖`

2. **生成UI文件**
   ```bash
   ./.qtcreator/Python_3_10_12venv/bin/pyside6-uic form.ui -o ui_form.py
   ```
   或使用VS Code任务：`Tasks: Run Task` -> `生成UI文件`

3. **运行程序**
   ```bash
   ./.qtcreator/Python_3_10_12venv/bin/python main_window.py
   ```
   或使用VS Code任务：`Tasks: Run Task` -> `运行主程序`
   或直接按 `F5` 调试运行

### 修改UI后

每次修改 `form.ui` 后，需要重新生成 `ui_form.py`：

**方法1：使用VS Code任务**
- `Ctrl+Shift+P` -> `Tasks: Run Task` -> `生成UI文件`

**方法2：使用终端**
```bash
./.qtcreator/Python_3_10_12venv/bin/pyside6-uic form.ui -o ui_form.py
```

**方法3：使用Qt Creator**
- Qt Creator会自动生成

## 常用命令

所有命令都在项目根目录执行：

```bash
# 激活虚拟环境（可选，VS Code会自动处理）
source ./.qtcreator/Python_3_10_12venv/bin/activate

# 安装/更新依赖
./.qtcreator/Python_3_10_12venv/bin/pip install -r requirements.txt

# 生成UI文件
./.qtcreator/Python_3_10_12venv/bin/pyside6-uic form.ui -o ui_form.py

# 运行程序
./.qtcreator/Python_3_10_12venv/bin/python main_window.py

# 查看已安装的包
./.qtcreator/Python_3_10_12venv/bin/pip list

# 安装新包
./.qtcreator/Python_3_10_12venv/bin/pip install 包名
```

## 项目结构

```
SerialDataCompare/
├── .vscode/                    # VS Code配置（已配置）
│   ├── settings.json          # 编辑器设置
│   ├── launch.json            # 调试配置
│   └── tasks.json             # 任务配置
├── .qtcreator/                # Qt Creator环境
│   └── Python_3_10_12venv/    # Python虚拟环境
├── document/                   # 文档目录
│   └── 功能说明.md            # 详细功能说明
├── form.ui                    # Qt Designer UI文件（源文件）
├── ui_form.py                 # 生成的UI Python文件（自动生成，不要手动编辑）
├── main_window.py             # 主程序入口
├── requirements.txt           # Python依赖列表
├── protocol_example.json      # 示例协议配置
├── README.md                  # 项目说明
└── QUICKSTART.md             # 本文件
```

## 常见问题

### Q: 为什么UI修改后没有生效？
A: 需要重新生成 `ui_form.py` 文件。

### Q: 如何在Qt Designer中编辑UI？
A: 直接打开 `form.ui` 文件，Qt Creator会自动使用Qt Designer打开。

### Q: 可以手动编辑 ui_form.py 吗？
A: 不建议。这个文件是自动生成的，每次重新生成都会覆盖。如果需要自定义，应该在 `main_window.py` 中进行。

### Q: 如何添加新的Python依赖？
A: 
1. 安装包：`./.qtcreator/Python_3_10_12venv/bin/pip install 包名`
2. 更新requirements.txt：`./.qtcreator/Python_3_10_12venv/bin/pip freeze > requirements.txt`

### Q: VS Code不识别虚拟环境？
A: 
1. 按 `Ctrl+Shift+P`
2. 输入 `Python: Select Interpreter`
3. 选择 `./.qtcreator/Python_3_10_12venv/bin/python`

## 下一步

1. 阅读 [功能说明文档](document/功能说明.md)
2. 阅读 [README.md](README.md)
3. 运行程序并开始使用！
