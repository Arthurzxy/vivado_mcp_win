# Vivado MCP

[English](README.md) | **简体中文**

[![Tests](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/test.yml/badge.svg)](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/test.yml)

一个面向 **AMD/Xilinx Vivado** 的跨平台 Model Context Protocol（MCP）服务器。它让支持 MCP 的 AI 客户端能够启动和管理 Vivado、打开工程、运行综合与实现、查询时序与资源利用率、控制仿真，以及执行 Tcl 命令。

本分支使用持久化 `subprocess` Tcl 会话，原生支持 Windows 和 Linux，不再依赖仅适用于类 Unix 环境的 `pexpect`。

> [!IMPORTANT]
> 本项目不包含 Vivado。可用器件、设计功能和许可证能力由本机安装的 Vivado 决定。

> [!WARNING]
> PyPI 上的 `vivado-mcp` 名称已经属于另一个项目。需要安装本仓库时，不要直接执行 `pip install vivado-mcp`，请使用下面给出的 GitHub URL 安装命令。

## 主要特性

- 原生启动 Windows 的 `vivado.bat` 和 `vivado.cmd`；
- Linux 下直接启动 Vivado 可执行文件；
- 一个持久化 Vivado Tcl 进程复用于多次 MCP 调用；
- 使用 UUID 分帧，分别提取标准输出、Tcl 返回值、返回码和错误堆栈；
- Tcl 命令通过 UTF-8 十六进制传输，支持引号、花括号、反斜杠、多行文本、中文和 Windows 路径；
- 命令超时后终止完整 Vivado 进程树；
- 支持通过 `VIVADO_PATH`、PATH 和常见安装目录自动查找 Vivado；
- 提供 `vivado-mcp-win-doctor`，用于验证本机真实 Vivado；
- CI 覆盖 Windows、Ubuntu、Python 3.10–3.12，并测试干净 wheel 安装。

## 支持环境

| 项目 | 支持范围 |
|---|---|
| 操作系统 | Windows 10/11、Linux |
| Python | 3.10、3.11、3.12 |
| Vivado | 按 Vivado 2023.2 及更新版本的启动方式设计；其他版本也可能可用 |
| FPGA 系列 | 由本机 Vivado 版本、器件包和许可证决定 |

## 快速安装

### 方式一：pipx 从 GitHub 安装——推荐

这种方式会创建隔离环境，不需要克隆仓库，并直接提供可执行命令。

#### Windows PowerShell

```powershell
py -m pip install --user --upgrade pipx
py -m pipx ensurepath
py -m pipx install "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

执行 `ensurepath` 后如果命令仍无法识别，请重新打开终端。

在 PR 合并前测试当前分支：

```powershell
py -m pipx install --force "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/agent/windows-native-support.zip"
```

#### Linux

```bash
python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath
python3 -m pipx install "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

安装后提供以下命令：

- `vivado-mcp-win`：启动 MCP 服务器；
- `vivado-mcp-win-doctor`：测试 Python 到 Vivado 的链路；
- `vivado-mcp`、`vivado-mcp-doctor`：兼容旧配置的别名。

### 方式二：pip 安装到独立虚拟环境

适合需要在 MCP 配置中填写 Python 绝对路径的情况，同样不需要克隆仓库。

```powershell
$venv = "$env:LOCALAPPDATA\vivado-mcp-win"
py -3.11 -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install --upgrade "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

Linux：

```bash
python3 -m venv ~/.local/share/vivado-mcp-win
~/.local/share/vivado-mcp-win/bin/python -m pip install --upgrade pip
~/.local/share/vivado-mcp-win/bin/python -m pip install --upgrade \
  "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

### 方式三：源码开发安装

```bash
git clone https://github.com/Arthurzxy/vivado_mcp_win.git
cd vivado_mcp_win
python -m pip install -e ".[dev]"
```

## 测试真实 Vivado

在配置 MCP 客户端之前，建议先运行诊断器：

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

也可以填写 Vivado 的版本目录或 `bin` 目录：

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2"
```

诊断器会针对真实 Vivado Tcl 进程执行：

1. 解析 Vivado 启动文件；
2. 启动持久化 Tcl 会话；
3. 执行 `version -short`；
4. 执行 `info patchlevel`；
5. 执行 `pwd`；
6. 计算 `expr {6 * 7}` 并确认结果为 `42`；
7. 往返传输中文字符串；
8. 检查会话健康状态；
9. 正常关闭 Vivado。

输出 JSON，便于保存或提交问题：

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2" --json
```

显示 `PASS` 说明该 Python 环境能够找到、启动、控制并关闭本机 Vivado。该测试不会对用户工程执行综合或实现。

## 配置 MCP 客户端

### pipx 安装

先查找命令绝对路径：

```powershell
(Get-Command vivado-mcp-win).Source
```

将输出路径写入 MCP 配置：

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\Users\\you\\.local\\bin\\vivado-mcp-win.exe",
      "env": {
        "VIVADO_PATH": "D:\\Xilinx\\Vivado\\2025.2\\bin\\vivado.bat"
      }
    }
  }
}
```

### 独立虚拟环境安装

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\Users\\you\\AppData\\Local\\vivado-mcp-win\\Scripts\\python.exe",
      "args": ["-m", "vivado_mcp"],
      "env": {
        "VIVADO_PATH": "D:\\Xilinx\\Vivado\\2025.2\\bin\\vivado.bat"
      }
    }
  }
}
```

使用绝对路径可以避免 MCP 客户端的 PATH 与普通终端不一致。

## Vivado 路径解析

`VIVADO_PATH` 和 `start_session` 的 `vivado_path` 参数均可指向：

- 完整的 `vivado.bat`、`vivado.cmd`、`vivado.exe` 或 Linux `vivado`；
- Vivado 的 `bin` 目录；
- 某个 Vivado 版本目录。

没有显式路径时，服务器会检查 PATH 和常见安装目录。Windows 搜索位置包括：

```text
C:\Xilinx\Vivado\*\bin\vivado.bat
C:\AMD\Vivado\*\bin\vivado.bat
C:\Program Files\AMD\Vivado\*\bin\vivado.bat
```

检测到多个版本时优先选择较新版本。

## Windows 自动测试覆盖范围

GitHub 托管的 Windows Runner 不包含 Vivado，因此自动测试使用兼容 Tcl 的模拟启动器，执行与真实 Vivado 相同的进程启动和命令分帧代码：

- 通过 `cmd.exe` 启动 `.bat`；
- 启动文件路径包含空格和括号；
- 通过版本目录和环境变量解析 Vivado；
- 持久化执行多条 Tcl 命令；
- 处理有换行和无换行输出；
- 处理 Windows 路径、花括号、分号、多行文本和中文；
- 处理 Tcl 错误和 Vivado 风格错误信息；
- 超时后终止进程树；
- 构建 wheel，在源码目录之外的干净环境安装，检查控制台命令并运行诊断器。

另外提供 `.github/workflows/real-vivado-windows-smoke.yml` 手动工作流。它要求一台安装了 Vivado、带许可证并标记为 `vivado` 的 Windows 自托管 Runner。GitHub 标准托管 Runner 无法执行该测试，因为其中没有预装 Vivado。

## 可用能力

| 类别 | 代表性工具 | 用途 |
|---|---|---|
| 会话管理 | `start_session`、`stop_session`、`session_status`、`get_host_status` | 启停 Vivado、检查会话与主机状态 |
| 工程管理 | `open_project`、`close_project`、`get_project_info` | 打开 `.xpr` 工程并读取信息 |
| 设计流程 | `run_synthesis`、`run_implementation`、`generate_bitstream` | 执行综合、布局布线和比特流生成 |
| 报告分析 | `get_timing_summary`、`get_timing_paths`、`get_utilization`、`get_clocks`、`get_messages` | 获取时序、资源、时钟和消息报告 |
| 设计查询 | `get_design_hierarchy`、`get_ports`、`get_nets`、`get_cells` | 查询层级、端口、网络和单元 |
| 仿真控制 | `launch_simulation`、`run_simulation`、`restart_simulation`、`get_signal_value` | 控制 xsim 并读取信号 |
| 高级操作 | `run_tcl`、`generate_full_report`、`read_report_section` | 执行任意 Tcl，并读取大型报告 |

## 架构

```text
┌────────────────────┐      MCP / stdio       ┌────────────────────┐
│  支持 MCP 的客户端  │ ◄────────────────────► │  Vivado MCP Server │
└────────────────────┘                         └─────────┬──────────┘
                                                       │ subprocess
                                                       │ 持久化 Tcl
                                                       ▼
                                             ┌────────────────────┐
                                             │ AMD/Xilinx Vivado  │
                                             │     -mode tcl      │
                                             └────────────────────┘
```

每条命令都以 UTF-8 十六进制传输，并使用唯一标记分帧。服务器分别提取标准输出、Tcl 返回值、返回码和错误堆栈，不依赖本地化的 `Vivado%` 提示符。

## 故障排查

### 无法启动 Vivado

先直接验证启动文件：

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

再运行 `vivado-mcp-win-doctor`，查看具体失败步骤，并检查路径、Vivado 安装、权限、环境变量和许可证。

### 中文输出乱码

Windows 默认使用系统首选编码。必要时可显式指定：

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2"
```

根据本机 Vivado Tcl 控制台使用 `utf-8`、`gbk` 或其他编码。

### MCP 客户端找不到命令

运行 `(Get-Command vivado-mcp-win).Source`，将返回的绝对路径写入配置。修改配置后重启 MCP 客户端。

### 命令超时

为避免会话失步，超时后会终止 Vivado 进程树。重新启动会话，并为综合或实现等长任务设置更大的超时时间。

更多 Windows 说明见 [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md)。

## 安全说明

`run_tcl` 能够以当前用户权限执行任意 Tcl，包括文件读写和启动外部进程。只应向可信 MCP 客户端开放，并在执行高影响命令前检查参数和目标路径。

## 开发与测试

```bash
python -m pip install -e ".[dev]"
python -m compileall -q .
python -m pytest -q
python -m ruff check vivado_session.py doctor.py tests
python -m build --wheel
python tests/package_smoke.py dist
```

## 许可证

本项目使用 [MIT License](LICENSE)。

## 致谢

- 原始项目由 Corey Hahn 创建；
- 使用 [Model Context Protocol](https://modelcontextprotocol.io/)；
- 集成 [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html)。
