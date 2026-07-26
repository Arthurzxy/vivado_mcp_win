# Vivado MCP

**English** | [简体中文](README.zh-CN.md)

[![Tests](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/tests.yml/badge.svg)](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/tests.yml)

A cross-platform Model Context Protocol (MCP) server for **AMD/Xilinx Vivado**. It allows MCP-compatible AI clients to start and manage Vivado, open projects, run synthesis and implementation, inspect timing and utilization, control simulation, and execute Tcl commands through natural-language workflows.

This fork uses a persistent `subprocess` session that works natively on Windows and Linux. It no longer depends on the Unix-only `pexpect` transport.

> [!IMPORTANT]
> Vivado is not included. Device support, design features, and licensing capabilities are determined by the Vivado installation on the host machine.

## Highlights

- **Native Windows support**: launches `vivado.bat` and `vivado.cmd` directly.
- **Linux support**: starts the Vivado executable without an intermediate shell.
- **Persistent Tcl session**: Vivado starts once, while later commands reuse the same process and design state.
- **Reliable command framing**: UUID markers separate command output, return values, and error information.
- **Safe Tcl transport**: commands are UTF-8 hex encoded before entering the Tcl wrapper, preserving quotes, braces, backslashes, multiline scripts, and Windows paths.
- **Timeout recovery**: a timed-out command terminates the full Vivado process tree instead of leaving a desynchronized session alive.
- **Structured results**: common timing, utilization, and message reports are converted into JSON-friendly data.
- **Cross-platform tests**: GitHub Actions covers Windows, Ubuntu, and Python 3.10–3.12.

## Supported environment

| Component | Supported range |
|---|---|
| Operating system | Windows 10/11 and Linux |
| Python | 3.10, 3.11, and 3.12 |
| Vivado | Designed around Vivado 2023.2+ launch conventions; other versions may also work |
| FPGA families | Not restricted by this server; determined by the installed Vivado version and licenses |

CI uses a fake Vivado Tcl shell to validate session management, command framing, error handling, and Windows/Linux launch behavior. CI does not install or run a real Vivado distribution.

## Quick installation

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

For development and tests:

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

## Configure an MCP client

Using the absolute path to the virtual environment's Python interpreter is recommended. It avoids depending on terminal PATH state or virtual-environment activation.

### Windows example

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

### Linux example

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

The installed `vivado-mcp` console command may also be used, but an absolute virtual-environment Python path is usually more reliable.

## Select the Vivado installation

Setting `VIVADO_PATH` is recommended. It may point to:

- a complete `vivado.bat`, `vivado.cmd`, or `vivado` file;
- a Vivado `bin` directory;
- a Vivado version directory.

A path may also be supplied through the `vivado_path` argument of `start_session`. Without an explicit path, the server tries PATH and common installation directories. On Windows, it checks locations such as the following and prefers a newer detected version:

```text
C:\Xilinx\Vivado\*\bin\vivado.bat
C:\AMD\Vivado\*\bin\vivado.bat
```

## First smoke test

After configuring the MCP client, run these tools in order:

1. `start_session`
2. `run_tcl` with `version -short`
3. `run_tcl` with `pwd`
4. `session_status`
5. `stop_session`

If all five steps succeed, the basic connection between the MCP client, Python environment, and Vivado Tcl process is working.

## Capabilities

| Category | Representative tools | Purpose |
|---|---|---|
| Session management | `start_session`, `stop_session`, `session_status`, `get_host_status` | Start or stop Vivado and inspect session or host state |
| Project management | `open_project`, `close_project`, `get_project_info` | Open `.xpr` projects and read project information |
| Design flow | `run_synthesis`, `run_implementation`, `generate_bitstream` | Run synthesis, place-and-route, and bitstream generation |
| Reports and analysis | `get_timing_summary`, `get_timing_paths`, `get_utilization`, `get_clocks`, `get_messages` | Read timing, resource, clock, and message reports |
| Design queries | `get_design_hierarchy`, `get_ports`, `get_nets`, `get_cells` | Inspect hierarchy, ports, nets, and cells |
| Simulation | `launch_simulation`, `run_simulation`, `restart_simulation`, `get_signal_value`, `add_signals_to_wave` | Control xsim and inspect signals |
| Advanced operations | `run_tcl`, `generate_full_report`, `read_report_section` | Execute arbitrary Tcl and read large reports in sections |

For exact parameters, use the tool schemas displayed by the MCP client and refer to [`server.py`](server.py).

## Typical workflow

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

Because the Vivado process is persistent, the open project, design stage, and simulation state can survive across multiple MCP calls.

## Architecture

```text
┌────────────────────┐      MCP / stdio       ┌────────────────────┐
│ MCP-compatible     │ ◄────────────────────► │ Vivado MCP Server  │
│ client             │                         └─────────┬──────────┘
└────────────────────┘                                   │ subprocess
                                                         │ persistent Tcl session
                                                         ▼
                                               ┌────────────────────┐
                                               │ AMD/Xilinx Vivado  │
                                               │     -mode tcl      │
                                               └────────────────────┘
```

Each Tcl command is wrapped in an independent UUID-framed protocol. The server extracts standard output, the Tcl return value, the return code, and the error stack separately, so it does not rely on simple `Vivado%` prompt matching.

## Troubleshooting

### Vivado does not start

First confirm that Vivado itself can start from a normal terminal:

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

```bash
/opt/Xilinx/Vivado/2025.2/bin/vivado -mode tcl
```

Then check `VIVADO_PATH`, filesystem permissions, the Vivado environment, and license configuration.

### The MCP client cannot find Python or the package

- Use the absolute path to the virtual environment's Python interpreter.
- Confirm that `python -m pip install -e .` was run in that same environment.
- Restart the MCP client after changing its configuration.

### Windows paths contain spaces or backslashes

Backslashes in JSON must be escaped as `\\`. The server itself supports spaces in `.bat`, `.cmd`, executable, and directory paths.

### A command times out

A timeout terminates the Vivado process tree. Check session state and call `start_session` again. Long synthesis or implementation operations require a suitable timeout value.

More Windows-specific guidance is available in [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md).

## Security

`run_tcl` can execute arbitrary Vivado Tcl with the permissions of the current user, including file operations and external process launches. Expose this server only to trusted MCP clients, and review high-impact commands and target paths before execution.

## Development and tests

```bash
python -m pip install -e ".[dev]"
python -m compileall -q .
python -m pytest -q
python -m ruff check vivado_session.py tests
```

GitHub Actions runs the tests and Ruff checks on Ubuntu and Windows with Python 3.10, 3.11, and 3.12.

## Project status

The current version is `0.2.0` and is considered Beta. Before using it with an important project, complete the smoke test above and keep project files and generated outputs under version control or backed up.

## Contributing

Issues and pull requests are welcome. Changes to the session protocol or process management should include tests for both Windows and Linux behavior.

## License

This project is available under the [MIT License](LICENSE).

## Acknowledgments

- Original project created by Corey Hahn.
- Built on the [Model Context Protocol](https://modelcontextprotocol.io/).
- Integrates with [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html).
