<p align="center">
  <strong>简体中文</strong> | <a href="README.en.md">English</a>
</p>

<!-- mcp-name: io.github.Arthurzxy/vivado-mcp-native -->

<h1 align="center">Vivado MCP Native</h1>

<p align="center">
  让 Claude、Cursor、Cline、Cherry Studio 等兼容 MCP 的 AI 客户端<br/>
  在 Windows 和 Linux 上直接启动、控制并分析 AMD/Xilinx Vivado。
</p>

<p align="center">
  <a href="https://pypi.org/project/vivado-mcp-native/"><img src="https://img.shields.io/pypi/v/vivado-mcp-native?label=PyPI" alt="PyPI"/></a>
  <img src="https://img.shields.io/pypi/pyversions/vivado-mcp-native" alt="Python"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue" alt="Platform"/>
  <img src="https://img.shields.io/badge/transport-MCP%20stdio-7c3aed" alt="MCP stdio"/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/></a>
</p>

> **让 AI 处理 Vivado 的重复操作、报告读取和 Tcl 调用，你可以把精力放在 FPGA 架构、约束和问题判断上。**

Vivado MCP Native 是一个面向 **AMD/Xilinx Vivado** 的本地 Model Context Protocol（MCP）服务器。它通过持久化 Vivado Tcl 会话，让 AI 客户端能够打开工程、运行综合与实现、生成比特流、读取时序和资源报告、控制仿真，并执行高级 Tcl 命令。

项目使用 Python `subprocess` 原生管理 Vivado 进程，可直接运行于 Windows 和 Linux，不依赖仅适用于类 Unix 环境的 `pexpect`。MCP 与 Vivado 都运行在用户本机，工程文件不会因为使用本项目而自动上传到云端。

> [!IMPORTANT]
> 本项目不包含 Vivado。可用器件、IP、综合/实现功能和许可证能力，取决于本机安装的 AMD/Xilinx Vivado。

> [!WARNING]
> PyPI 上的 `vivado-mcp` 属于另一个项目。本项目的安装包名称是 **`vivado-mcp-native`**。

---

## 它可以做什么

| 类别 | 主要能力 | 典型用途 |
|---|---|---|
| Vivado 会话 | 启动、停止、健康检查、状态统计、异常恢复 | 让 AI 复用同一个 Vivado Tcl 进程，避免每条命令都重新启动 Vivado |
| 工程管理 | 打开/关闭 `.xpr` 工程、读取工程信息 | 检查目标器件、顶层模块、工程目录和当前工程状态 |
| 设计流程 | 运行综合、实现、生成比特流 | 自动执行 `synth_1`、`impl_1` 和 bitstream 流程，并核对实际运行状态 |
| 时序分析 | 获取 WNS、TNS、WHS、THS 和关键路径 | 判断是否满足时序，定位 setup/hold 违例及跨时钟问题 |
| 资源分析 | 查询 LUT、FF、BRAM、DSP、IO 使用率 | 判断设计是否放得下，分析资源热点和层次化占用 |
| 消息诊断 | 获取 ERROR、CRITICAL WARNING、WARNING | 汇总综合和实现阶段的问题，辅助确定排查顺序 |
| 设计查询 | 查询层次结构、端口、网络和单元 | 核对综合后的连接关系、模块实例和信号名称 |
| Vivado 仿真 | 启动/重启/步进仿真、读取信号、设置断点 | 运行 xsim，查看 testbench、波形对象和指定信号值 |
| Tcl 扩展 | 执行任意 Vivado Tcl 命令 | 调用尚未封装为专用 MCP 工具的 Vivado 能力 |
| 大型报告 | 生成完整报告并按区段读取 | 避免超长报告一次性占满 AI 上下文窗口 |

### 可以直接对 AI 这样说

```text
启动 Vivado，并检查当前会话是否健康。

打开 D:\FPGA\my_project\my_project.xpr，告诉我目标器件、顶层模块和当前运行状态。

运行综合，使用 8 个并行任务。完成后汇总 ERROR、CRITICAL WARNING 和资源利用率。

分析当前设计的时序，告诉我 WNS/TNS 是否满足，并列出最差的 10 条 setup 路径。

只分析 clk_250m 时钟域中经过 u_tdc 的失败路径，并给出可能的优化方向。

运行实现并生成 bitstream；每一步都确认 Vivado 的真实 STATUS 和 PROGRESS。

启动行为级仿真，运行 1 us，然后读取 /tb/dut/data_out 和 /tb/dut/valid。

执行 Tcl：report_drc -ruledecks default，并总结需要优先处理的问题。
```

---

## 为什么使用这个项目

| 常见问题 | Vivado MCP Native 的处理方式 |
|---|---|
| Windows 下传统 `pexpect` 方案难以直接运行 | 使用原生 `subprocess` 启动 `vivado.bat`、`vivado.cmd` 或 Linux `vivado` |
| Vivado 启动慢 | 多次 MCP 调用复用同一个持久 Tcl 会话 |
| Tcl 中包含引号、花括号、反斜杠或中文路径 | 使用 UTF-8 十六进制传输和唯一命令标记进行可靠分帧 |
| 本地化 Vivado 提示符可能变化 | 不依赖 `Vivado%` 提示符解析命令边界 |
| 长命令超时后容易留下 Vivado 子进程 | 超时后清理完整进程树，避免残留失步会话 |
| 报告太长，AI 无法一次读完 | 支持完整报告落盘并按行或正则表达式分段读取 |
| 不确定 Vivado 路径和编码是否正确 | 提供 `vivado-mcp-native-doctor` 一键诊断 |

---

## 环境要求

| 组件 | 要求 |
|---|---|
| 操作系统 | Windows 10/11 或 Linux |
| Python | 3.10–3.12 |
| Vivado | 本机已经安装 AMD/Xilinx Vivado |
| 许可证 | 覆盖计划使用的器件、IP 和设计流程 |
| MCP 客户端 | 支持本地 `stdio` MCP Server |

---

## 安装

### 方式一：使用 pip 安装

Windows PowerShell：

```powershell
py -m pip install --upgrade vivado-mcp-native
```

Linux：

```bash
python3 -m pip install --upgrade vivado-mcp-native
```

检查安装结果：

```powershell
py -m pip show vivado-mcp-native
vivado-mcp-native-doctor --help
```

### 方式二：使用 pipx 安装（推荐）

`pipx` 会为 MCP Server 创建独立 Python 环境，减少与其他 Python 包的依赖冲突。

Windows：

```powershell
py -m pip install --user --upgrade pipx
py -m pipx ensurepath
py -m pipx install vivado-mcp-native
```

Linux：

```bash
python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath
python3 -m pipx install vivado-mcp-native
```

升级：

```powershell
py -m pipx upgrade vivado-mcp-native
```

### 方式三：直接从 GitHub 安装

安装 `master` 分支最新源码：

```powershell
py -m pip install --upgrade "git+https://github.com/Arthurzxy/vivado_mcp_native.git@master"
```

使用 pipx：

```powershell
py -m pipx install --force "git+https://github.com/Arthurzxy/vivado_mcp_native.git@master"
```

不依赖本机 Git，也可以安装 GitHub ZIP：

```powershell
py -m pip install --upgrade "https://github.com/Arthurzxy/vivado_mcp_native/archive/refs/heads/master.zip"
```

用于开发或修改源码：

```powershell
git clone https://github.com/Arthurzxy/vivado_mcp_native.git
cd vivado_mcp_native
py -m pip install -e .
```

### 安装后提供的命令

| 命令 | 作用 |
|---|---|
| `vivado-mcp-native` | 启动 MCP stdio Server |
| `vivado-mcp-native-doctor` | 检查 Python、Vivado、Tcl 和 Unicode 通信 |
| `vivado-mcp-win` | 兼容旧配置的 Server 别名 |
| `vivado-mcp-win-doctor` | 兼容旧配置的 Doctor 别名 |

---

## 快速开始

### 第一步：确认 Vivado 启动文件

`VIVADO_PATH` 可以指向：

- 完整启动文件：`vivado.bat`、`vivado.cmd`、`vivado.exe` 或 Linux `vivado`；
- Vivado 的 `bin` 目录；
- Vivado 版本目录。

Windows 示例：

```powershell
$env:VIVADO_PATH = "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat"
```

Linux 示例：

```bash
export VIVADO_PATH="/tools/Xilinx/Vivado/2025.2/bin/vivado"
```

未显式配置时，Server 会检查系统 PATH 和常见安装目录。

### 第二步：运行 Doctor

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat"
```

机器可读 JSON 输出：

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Software\Xilinx\2025.2.1" --json
```

Doctor 会依次检查：

1. Vivado 启动文件解析；
2. 持久 Tcl 会话启动；
3. Vivado 和 Tcl 版本查询；
4. Tcl 表达式执行；
5. 中文 Unicode 往返；
6. 会话健康状态；
7. Vivado 正常关闭。

Doctor 不会打开或修改用户工程。

### 第三步：配置 MCP 客户端

先查找安装后的命令路径：

```powershell
(Get-Command vivado-mcp-native).Source
```

#### 使用已安装的命令

把下面的 `command` 和 `VIVADO_PATH` 替换为你的实际路径：

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\Users\\you\\.local\\bin\\vivado-mcp-native.exe",
      "env": {
        "VIVADO_PATH": "D:\\Software\\Xilinx\\2025.2.1\\Vivado\\bin\\vivado.bat"
      }
    }
  }
}
```

#### 使用 Python 模块启动

适用于虚拟环境或 `pip install` 后不方便定位命令的情况：

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\Users\\you\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": ["-m", "vivado_mcp"],
      "env": {
        "VIVADO_PATH": "D:\\Software\\Xilinx\\2025.2.1\\Vivado\\bin\\vivado.bat"
      }
    }
  }
}
```

建议使用可执行文件的**绝对路径**，避免 MCP 客户端与终端使用不同 PATH。

配置保存后，完全退出并重新启动 MCP 客户端，然后让 AI 执行：

```text
检查 Vivado MCP 的主机状态，启动会话并返回 Vivado 版本。
```

---

## 推荐使用流程

```text
1. vivado-mcp-native-doctor     检查本机环境
2. start_session                启动持久 Vivado Tcl 会话
3. open_project                 打开 .xpr 工程
4. get_project_info             确认器件、工程和顶层信息
5. run_synthesis                运行综合
6. get_messages                 查看错误和警告
7. get_timing_summary           检查 WNS/TNS/WHS/THS
8. get_utilization              检查 LUT/FF/BRAM/DSP/IO
9. run_implementation           运行布局布线
10. get_timing_paths            分析最差路径
11. generate_bitstream          生成比特流
12. stop_session                关闭 Vivado 并释放资源
```

综合和实现可能耗时较长。大型工程应在调用时增加 `timeout`，并根据 CPU 和内存情况设置合适的 `jobs`。

---

## MCP 工具说明

### 会话管理

- `start_session`：启动持久 Vivado Tcl 会话；
- `stop_session`：正常关闭 Vivado；
- `session_status`：查看命令数、错误数和会话统计；
- `check_session_health`：检查会话响应并按需恢复；
- `get_host_status`：查看主机名、可用内存和会话状态。

### 工程与设计流程

- `open_project` / `close_project`：打开或关闭 `.xpr` 工程；
- `get_project_info`：获取当前工程信息；
- `run_synthesis`：运行综合并验证 Vivado 的实际状态；
- `run_implementation`：运行 place and route；
- `generate_bitstream`：为已实现设计生成 bitstream。

### 报告与设计查询

- `get_timing_summary`：返回 WNS、TNS、WHS、THS 等结构化指标；
- `get_timing_paths`：按时钟、起点、终点或 through 对象过滤关键路径；
- `get_utilization`：返回 LUT、FF、BRAM、DSP 和 IO 使用率；
- `get_clocks`：获取时钟与约束信息；
- `get_messages`：分类读取 ERROR、CRITICAL WARNING 和 WARNING；
- `get_design_hierarchy`：读取综合后设计层次；
- `get_ports` / `get_nets` / `get_cells`：查询端口、网络和单元。

### 仿真

- `set_simulation_top`：设置 testbench 顶层；
- `launch_simulation`：启动行为级或综合/实现后仿真；
- `run_simulation` / `step_simulation` / `restart_simulation`：运行、步进或重启；
- `get_signal_value` / `get_signal_values`：读取一个或一组信号；
- `get_scopes` / `get_simulation_objects`：浏览仿真层次和对象；
- `add_signals_to_wave`：添加波形信号；
- `add_breakpoint` / `remove_breakpoints`：管理仿真断点；
- `get_simulation_messages`：读取仿真日志；
- `close_simulation`：关闭仿真。

### 高级能力

- `run_tcl`：执行任意 Vivado Tcl；
- `generate_full_report`：生成 timing、utilization、power、DRC 等完整报告；
- `read_report_section`：按行范围或正则表达式读取大型报告；
- `request_feature` / `list_feature_requests`：记录当前未覆盖的功能需求。

---

## 工作原理

```text
Claude / Cursor / Cline / Cherry Studio / 其他 MCP 客户端
                         │
                         │ MCP stdio / JSON-RPC
                         ▼
                 Vivado MCP Native
                         │
                         │ 持久 subprocess Tcl 会话
                         ▼
              AMD/Xilinx Vivado -mode tcl
                         │
                         ▼
                 本机 FPGA 工程与报告
```

每条 Tcl 命令会使用 UTF-8 十六进制编码并附加唯一标记。Server 分别提取标准输出、Tcl 返回值、返回码和错误栈，不依赖可能随语言环境变化的 `Vivado%` 提示符。

---

## 常见问题

### 找不到 `vivado-mcp-native` 命令

```powershell
py -m pipx ensurepath
(Get-Command vivado-mcp-native).Source
```

重启终端或把返回的绝对路径直接写入 MCP 客户端配置。

### 找不到 Vivado

先验证启动文件：

```powershell
& "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat" -mode tcl
```

随后运行：

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat"
```

### 中文输出乱码

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
```

可设置为 `utf-8`、`gbk`，或与本机 Vivado Tcl 控制台一致的编码。

### 综合或实现超时

超时后 Server 会终止完整 Vivado 进程树，防止继续使用已经失步的会话。重新启动会话，并为大型工程设置更长的 `timeout`。

### `vivado-mcp` 和 `vivado-mcp-native` 是同一个包吗

不是。安装本项目请始终使用：

```powershell
py -m pip install vivado-mcp-native
```

更多 Windows 配置说明参见 [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md)。

---

## 安全说明

`run_tcl` 可以按当前用户权限执行任意 Tcl，包括读写文件和启动外部程序。请注意：

- 只连接可信的 MCP 客户端和模型；
- 执行删除文件、重置工程或覆盖输出前检查目标路径；
- 对重要工程使用版本控制并保留备份；
- 不要把没有鉴权和隔离的 Vivado MCP 直接暴露到公网。

---

## 官方 MCP Registry

官方 Registry 标识：

```text
io.github.Arthurzxy/vivado-mcp-native
```

注册元数据位于 [`server.json`](server.json)，当前发布版本为 `0.2.1`，传输方式为本地 `stdio`。

---

## 贡献

欢迎通过 Issue 或 Pull Request：

- 补充新的 Vivado 工具；
- 改进不同 Vivado 版本的兼容性；
- 增强报告解析；
- 补充 MCP 客户端配置示例；
- 修正文档或翻译。

---

## 许可证与致谢

本项目使用 [MIT License](LICENSE)。

- 原始项目由 Corey Hahn 创建；
- 基于 [Model Context Protocol](https://modelcontextprotocol.io/)；
- 集成 [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html)。
