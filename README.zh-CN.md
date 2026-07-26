# Vivado MCP

[English](README.md) | **简体中文**

这是一个面向 **AMD/Xilinx Vivado** 的跨平台 Model Context Protocol（MCP）服务器。它允许兼容 MCP 的 AI 客户端启动和管理 Vivado、打开工程、运行综合与实现、查看时序和资源利用率、控制仿真，以及执行 Tcl 命令。

本项目使用基于 `subprocess` 的持久化 Tcl 会话，可在 Windows 和 Linux 上原生运行，不依赖仅适用于类 Unix 环境的 `pexpect` 传输方式。

> [!IMPORTANT]
> 本项目不包含 Vivado。可用的器件支持、授权功能和 FPGA 系列取决于主机上安装的 Vivado 及其许可证。

> [!WARNING]
> PyPI 上的 `vivado-mcp` 名称属于另一个项目。请直接从 GitHub 安装本仓库，不要使用不带来源地址的 `pip install vivado-mcp`。

## 主要特性

- 原生启动 Windows 下的 `vivado.bat` 和 `vivado.cmd`。
- Linux 下直接启动 Vivado 可执行文件，无需额外 shell。
- 在多次 MCP 调用之间复用同一个持久化 Vivado Tcl 进程。
- 使用 UUID 标记对每条命令进行分帧，分别提取标准输出、Tcl 返回值、返回码和错误栈。
- 使用 UTF-8 十六进制传输，可靠处理引号、花括号、反斜杠、多行 Tcl、Unicode 和 Windows 路径。
- 命令超时后清理完整的 Vivado 进程树，避免残留失步会话。
- 支持通过 `VIVADO_PATH`、系统 PATH 和常见安装目录自动发现 Vivado。
- 提供 `vivado-mcp-win-doctor` 命令，用于检查本机 Python 到 Vivado 的连接状态。

## 环境要求

| 组件 | 要求 |
|---|---|
| 操作系统 | Windows 10/11 或 Linux |
| Python | 3.10–3.12 |
| Vivado | 本机已安装 AMD/Xilinx Vivado |
| 许可证 | 覆盖计划使用的操作和 FPGA 器件 |

## 安装

### 从 GitHub 使用 pipx 安装（推荐）

`pipx` 会为程序创建独立的 Python 环境，并将命令行入口加入用户 PATH。

#### Windows PowerShell

```powershell
py -m pip install --user --upgrade pipx
py -m pipx ensurepath
py -m pipx install "https://github.com/Arthurzxy/vivado_mcp_native/archive/refs/heads/master.zip"
```

执行 `ensurepath` 后，如命令仍不可用，请重新打开终端。

#### Linux

```bash
python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath
python3 -m pipx install "https://github.com/Arthurzxy/vivado_mcp_native/archive/refs/heads/master.zip"
```

安装后可用的命令：

- `vivado-mcp-win`：启动 MCP 服务器；
- `vivado-mcp-win-doctor`：检查本机 Vivado 连接；
- `vivado-mcp` 和 `vivado-mcp-doctor`：兼容别名。

### 安装到独立虚拟环境

```powershell
$venv = "$env:LOCALAPPDATA\vivado-mcp-win"
py -3.11 -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install --upgrade "https://github.com/Arthurzxy/vivado_mcp_native/archive/refs/heads/master.zip"
```

## 选择 Vivado 安装位置

环境变量 `VIVADO_PATH` 和 `start_session` 工具的 `vivado_path` 参数可以指向：

- 完整的 `vivado.bat`、`vivado.cmd`、`vivado.exe` 或 Linux `vivado` 启动文件；
- Vivado 的 `bin` 目录；
- Vivado 的版本目录。

示例：

```powershell
$env:VIVADO_PATH = "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

未显式指定路径时，服务器会检查系统 PATH 和常见的 Windows 安装目录，例如：

```text
C:\Xilinx\Vivado\*\bin\vivado.bat
C:\AMD\Vivado\*\bin\vivado.bat
C:\Program Files\AMD\Vivado\*\bin\vivado.bat
```

## 检查 Vivado 连接

建议在配置 MCP 客户端之前先运行诊断命令：

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

路径也可以是 Vivado 的 `bin` 目录或版本目录。使用 `--json` 可以获得机器可读的输出：

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2" --json
```

诊断命令会完成以下操作：

1. 解析 Vivado 启动文件；
2. 启动持久化 Tcl 会话；
3. 查询 Vivado 和 Tcl 版本；
4. 检查 Tcl 命令传输与 Unicode 处理；
5. 检查会话健康状态；
6. 正常关闭 Vivado。

该命令不会打开或修改用户工程。

## 配置 MCP 客户端

查找已安装命令的绝对路径：

```powershell
(Get-Command vivado-mcp-win).Source
```

### pipx 安装方式示例

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

### 虚拟环境安装方式示例

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

使用命令或 Python 解释器的绝对路径，可以避免 MCP 客户端自身 PATH 环境不同而导致找不到程序。

## 功能范围

| 类别 | 代表性工具 | 用途 |
|---|---|---|
| 会话管理 | `start_session`、`stop_session`、`session_status`、`get_host_status` | 启动或停止 Vivado，并查看会话或主机状态 |
| 工程管理 | `open_project`、`close_project`、`get_project_info` | 打开 `.xpr` 工程并读取工程信息 |
| 设计流程 | `run_synthesis`、`run_implementation`、`generate_bitstream` | 运行综合、布局布线和比特流生成 |
| 报告读取 | `get_timing_summary`、`get_timing_paths`、`get_utilization`、`get_clocks`、`get_messages` | 获取时序、资源、时钟和消息报告 |
| 设计查询 | `get_design_hierarchy`、`get_ports`、`get_nets`、`get_cells` | 查看层次结构、端口、网络和单元 |
| 仿真控制 | `launch_simulation`、`run_simulation`、`restart_simulation`、`get_signal_value` | 控制 xsim 并读取信号 |
| 高级操作 | `run_tcl`、`generate_full_report`、`read_report_section` | 执行 Tcl 并读取大型报告 |

## 架构

```text
兼容 MCP 的客户端
        │ MCP / stdio
        ▼
Vivado MCP 服务器
        │ 持久化 subprocess Tcl 会话
        ▼
AMD/Xilinx Vivado -mode tcl
```

每条命令都会先编码为 UTF-8 十六进制数据，并使用唯一标记进行封装。服务器无需依赖可能因语言环境而变化的 `Vivado%` 提示符，即可分别提取标准输出、Tcl 结果、返回码和错误栈。

## 常见问题

### Vivado 无法启动

先直接检查启动文件：

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

随后运行 `vivado-mcp-win-doctor`，检查路径、Vivado 安装、用户权限、环境变量和许可证配置。

### 中文输出乱码

必要时可以覆盖 Windows 输出解码方式：

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
```

可选值包括 `utf-8`、`gbk`，或与该计算机上 Vivado Tcl 控制台相匹配的编码。

### MCP 客户端找不到命令

```powershell
py -m pipx ensurepath
(Get-Command vivado-mcp-win).Source
```

将返回的绝对路径写入 MCP 客户端配置，并在修改配置后重启客户端。

### Tcl 命令执行超时

命令超时后，服务器会终止完整的 Vivado 进程树，防止继续使用已经失步的会话。请重新启动会话，并为综合或实现等长时间任务设置更大的超时时间。

更多 Windows 使用说明请参阅 [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md)。

## 安全说明

`run_tcl` 会以当前用户权限执行任意 Tcl，包括文件操作和启动外部进程。请仅将本服务器连接到可信的 MCP 客户端，并在执行高影响命令前检查命令内容和目标路径。

## 许可证

本项目使用 [MIT License](LICENSE)。

## 致谢

- 原始项目由 Corey Hahn 创建。
- 基于 [Model Context Protocol](https://modelcontextprotocol.io/)。
- 集成 [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html)。
