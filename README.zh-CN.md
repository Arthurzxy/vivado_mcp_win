# Vivado MCP

[English](README.md) | **简体中文**

[![Tests](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/tests.yml/badge.svg)](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/tests.yml)

一个面向 **AMD/Xilinx Vivado** 的跨平台 Model Context Protocol（MCP）服务器。它让支持 MCP 的 AI 客户端能够通过自然语言启动和管理 Vivado、打开工程、运行综合与实现、查询时序和资源利用率、控制仿真，以及执行 Tcl 命令。

本分支使用持久化 `subprocess` 会话，同时支持原生 Windows 和 Linux，不再依赖仅适用于类 Unix 环境的 `pexpect`。

> [!IMPORTANT]
> 本项目不包含 Vivado。可用器件、设计功能和许可证能力均由本机安装的 Vivado 决定。

## 主要特性

- **原生 Windows 支持**：可直接启动 `vivado.bat` 或 `vivado.cmd`。
- **Linux 支持**：直接启动 Vivado 可执行文件，不经过 shell。
- **持久化 Tcl 会话**：Vivado 仅启动一次，后续命令复用同一进程和设计状态。
- **可靠的命令分帧**：使用 UUID 标记区分每条命令的输出、返回值和错误信息。
- **安全传输 Tcl 文本**：命令以 UTF-8 十六进制编码传入 Tcl 包装器，能够处理引号、花括号、反斜杠、多行脚本和 Windows 路径。
- **超时恢复**：命令超时后终止整个 Vivado 进程树，避免继续使用已经失步的会话。
- **结构化结果**：常用时序、资源和消息报告会转换为更适合 AI 客户端处理的 JSON。
- **跨平台测试**：GitHub Actions 覆盖 Windows、Ubuntu 和 Python 3.10–3.12。

## 支持环境

| 项目 | 支持范围 |
|---|---|
| 操作系统 | Windows 10/11、Linux |
| Python | 3.10、3.11、3.12 |
| Vivado | 按 Vivado 2023.2 及更新版本的启动方式设计；其他版本可能同样可用 |
| FPGA 系列 | 不限定器件系列，由已安装的 Vivado 和许可证决定 |

CI 使用模拟 Vivado Tcl shell 验证会话管理、命令分帧、错误处理和 Windows/Linux 启动逻辑；CI 不会安装或运行真实 Vivado。

## 快速安装

### Windows PowerShell

```powershell
git clone https://github.com/Arthurzxy/vivado_mcp_win.git
cd vivado_mcp_win

py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

需要运行测试或参与开发时：

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check vivado_session.py tests
```

### Linux

```bash
git clone https://github.com/Arthurzxy/vivado_mcp_win.git
cd vivado_mcp_win

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

## 配置 MCP 客户端

推荐直接使用虚拟环境中的 Python 绝对路径，这样不依赖终端的 PATH 或虚拟环境激活状态。

### Windows 示例

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\work\\vivado_mcp_win\\.venv\\Scripts\\python.exe",
      "args": ["-m", "vivado_mcp"],
      "env": {
        "VIVADO_PATH": "D:\\Xilinx\\Vivado\\2025.2\\bin\\vivado.bat"
      }
    }
  }
}
```

### Linux 示例

```json
{
  "mcpServers": {
    "vivado": {
      "command": "/home/user/vivado_mcp_win/.venv/bin/python",
      "args": ["-m", "vivado_mcp"],
      "env": {
        "VIVADO_PATH": "/opt/Xilinx/Vivado/2025.2/bin/vivado"
      }
    }
  }
}
```

安装后也可以把 `vivado-mcp` 作为启动命令，但使用虚拟环境 Python 的绝对路径通常更稳定。

## 指定 Vivado 路径

推荐设置 `VIVADO_PATH`。它可以指向：

- 完整的 `vivado.bat`、`vivado.cmd` 或 `vivado` 文件；
- Vivado 的 `bin` 目录；
- 某个 Vivado 版本目录。

也可以在调用 `start_session` 时传入 `vivado_path`。当没有显式指定路径时，服务器会尝试从 PATH 和常见安装目录中查找 Vivado。在 Windows 上，它会检查类似下面的位置并优先选择检测到的较新版本：

```text
C:\Xilinx\Vivado\*\bin\vivado.bat
C:\AMD\Vivado\*\bin\vivado.bat
```

## 首次连通性测试

配置完成后，让 MCP 客户端依次执行：

1. `start_session`
2. `run_tcl`，命令为 `version -short`
3. `run_tcl`，命令为 `pwd`
4. `session_status`
5. `stop_session`

如果这些步骤成功，说明 MCP 客户端、Python 环境和 Vivado Tcl 会话之间的基本链路已经打通。

## 可用能力

| 类别 | 代表性工具 | 用途 |
|---|---|---|
| 会话管理 | `start_session`、`stop_session`、`session_status`、`get_host_status` | 启停 Vivado、检查状态和主机资源 |
| 工程管理 | `open_project`、`close_project`、`get_project_info` | 打开 `.xpr` 工程并读取工程信息 |
| 设计流程 | `run_synthesis`、`run_implementation`、`generate_bitstream` | 执行综合、布局布线和比特流生成 |
| 报告分析 | `get_timing_summary`、`get_timing_paths`、`get_utilization`、`get_clocks`、`get_messages` | 获取时序、资源、时钟和消息报告 |
| 设计查询 | `get_design_hierarchy`、`get_ports`、`get_nets`、`get_cells` | 查询层级、端口、网络和单元 |
| 仿真控制 | `launch_simulation`、`run_simulation`、`restart_simulation`、`get_signal_value`、`add_signals_to_wave` | 控制 xsim 并读取信号 |
| 高级操作 | `run_tcl`、`generate_full_report`、`read_report_section` | 执行任意 Tcl，并分段读取大型报告 |

具体参数以 MCP 客户端显示的工具 schema 和 [`server.py`](server.py) 为准。

## 典型工作流

```text
start_session
  → open_project
  → run_synthesis
  → get_timing_summary / get_utilization
  → run_implementation
  → get_timing_summary
  → generate_bitstream
  → stop_session
```

由于 Vivado 会话是持久化的，打开的工程、设计阶段和仿真状态可以在多次 MCP 调用之间保留。

## 架构

```text
┌────────────────────┐      MCP / stdio       ┌────────────────────┐
│  支持 MCP 的客户端  │ ◄────────────────────► │  Vivado MCP Server │
└────────────────────┘                         └─────────┬──────────┘
                                                       │ subprocess
                                                       │ 持久化 Tcl 会话
                                                       ▼
                                             ┌────────────────────┐
                                             │   AMD/Xilinx       │
                                             │   Vivado -mode tcl │
                                             └────────────────────┘
```

每条 Tcl 命令都会被包装在独立的 UUID 分帧协议中。服务器分别提取标准输出、Tcl 返回值、返回码和错误堆栈，因此不需要依赖简单的 `Vivado%` 提示符匹配。

## 故障排查

### 无法启动 Vivado

先在普通终端中验证 Vivado 本身可以启动：

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

```bash
/opt/Xilinx/Vivado/2025.2/bin/vivado -mode tcl
```

随后检查 `VIVADO_PATH`、文件权限、Vivado 环境变量和许可证配置。

### MCP 客户端提示找不到 Python 或模块

- 在配置中使用虚拟环境 Python 的绝对路径；
- 确认在同一个虚拟环境中执行过 `python -m pip install -e .`；
- 修改配置后重启 MCP 客户端。

### Windows 路径包含空格或反斜杠

JSON 中的反斜杠必须写成 `\\`。服务器本身支持带空格的 `.bat`、`.cmd` 和目录路径。

### 命令超时

超时会终止 Vivado 进程树。确认当前会话状态后重新调用 `start_session`。长时间综合或实现任务需要设置合理的超时时间。

更多 Windows 说明见 [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md)。

## 安全说明

`run_tcl` 能够以当前用户权限执行任意 Vivado Tcl 命令，包括读写文件和启动外部流程。只应向可信 MCP 客户端开放本服务器，并在执行高影响命令前检查参数和目标路径。

## 开发与测试

```bash
python -m pip install -e ".[dev]"
python -m compileall -q .
python -m pytest -q
python -m ruff check vivado_session.py tests
```

GitHub Actions 会在 Ubuntu 和 Windows 上分别使用 Python 3.10、3.11 和 3.12 执行测试与 Ruff 检查。

## 项目状态

当前版本为 `0.2.0`，处于 Beta 阶段。建议在重要工程中使用前先完成上述连通性测试，并保留工程和生成文件的版本控制或备份。

## 贡献

欢迎提交 Issue 和 Pull Request。涉及会话协议或进程管理的修改应同时补充 Windows 与 Linux 测试。

## 许可证

本项目使用 [MIT License](LICENSE)。

## 致谢

- 原始项目由 Corey Hahn 创建；
- 使用 [Model Context Protocol](https://modelcontextprotocol.io/)；
- 集成 [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html)。
