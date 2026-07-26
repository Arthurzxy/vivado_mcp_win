# Vivado MCP

**English** | [简体中文](README.zh-CN.md)

[![Tests](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/test.yml/badge.svg)](https://github.com/Arthurzxy/vivado_mcp_win/actions/workflows/test.yml)

A cross-platform Model Context Protocol (MCP) server for **AMD/Xilinx Vivado**. It lets MCP-compatible AI clients start and manage Vivado, open projects, run synthesis and implementation, inspect timing and utilization, control simulation, and execute Tcl commands.

This fork uses a persistent `subprocess` Tcl session that works natively on Windows and Linux. It does not depend on the Unix-only `pexpect` transport.

> [!IMPORTANT]
> Vivado is not included. Device support, design features, and licensing capabilities are determined by the Vivado installation on the host machine.

> [!WARNING]
> The name `vivado-mcp` on PyPI belongs to a different project. Do **not** use a bare `pip install vivado-mcp` when you intend to install this repository. Use one of the GitHub URL commands below.

## Highlights

- Native launch of Windows `vivado.bat` and `vivado.cmd` files.
- Direct Linux executable launch without an intermediate shell.
- One persistent Vivado Tcl process reused across MCP calls.
- UUID-framed command protocol that separates stdout, Tcl return values, return codes, and error stacks.
- UTF-8 hex transport for quotes, braces, backslashes, multiline Tcl, Unicode, and Windows paths.
- Full process-tree cleanup after timeouts.
- Automatic Vivado discovery through `VIVADO_PATH`, PATH, and common install directories.
- A `vivado-mcp-win-doctor` command for testing a real Vivado installation.
- Windows and Ubuntu CI for Python 3.10–3.12, plus clean wheel-install tests.

## Supported environment

| Component | Supported range |
|---|---|
| Operating system | Windows 10/11 and Linux |
| Python | 3.10, 3.11, and 3.12 |
| Vivado | Designed around Vivado 2023.2+ launch conventions; other versions may also work |
| FPGA families | Determined by the installed Vivado version and licenses |

## Fast installation

### Option 1: pipx from GitHub — recommended

This installs the server in an isolated environment and exposes dedicated commands without cloning the repository.

#### Windows PowerShell

```powershell
py -m pip install --user --upgrade pipx
py -m pipx ensurepath
py -m pipx install "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

Restart the terminal after `ensurepath` if the command is not found.

To test the current pull-request branch before it is merged:

```powershell
py -m pipx install --force "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/agent/windows-native-support.zip"
```

#### Linux

```bash
python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath
python3 -m pipx install "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

Installed commands:

- `vivado-mcp-win` — start the MCP server;
- `vivado-mcp-win-doctor` — test the Python-to-Vivado connection;
- `vivado-mcp` and `vivado-mcp-doctor` — compatibility aliases.

### Option 2: pip into a dedicated virtual environment

This option also avoids cloning and is convenient when an MCP configuration needs an absolute Python path.

```powershell
$venv = "$env:LOCALAPPDATA\vivado-mcp-win"
py -3.11 -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install --upgrade "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

Linux equivalent:

```bash
python3 -m venv ~/.local/share/vivado-mcp-win
~/.local/share/vivado-mcp-win/bin/python -m pip install --upgrade pip
~/.local/share/vivado-mcp-win/bin/python -m pip install --upgrade \
  "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

### Option 3: source installation for development

```bash
git clone https://github.com/Arthurzxy/vivado_mcp_win.git
cd vivado_mcp_win
python -m pip install -e ".[dev]"
```

## Test a real Vivado installation

Run the doctor before configuring an MCP client:

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

The path may also be a Vivado `bin` directory or version directory:

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2"
```

The doctor performs these checks against the actual Vivado Tcl process:

1. resolve the Vivado launcher;
2. start a persistent Tcl session;
3. run `version -short`;
4. run `info patchlevel`;
5. run `pwd`;
6. evaluate `expr {6 * 7}` and verify the result is `42`;
7. round-trip a Chinese Unicode string;
8. run the session health check;
9. stop Vivado cleanly.

Use JSON output for automation or bug reports:

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2" --json
```

A `PASS` result confirms the package can locate, launch, exchange framed Tcl commands with, and stop the installed Vivado instance. It does not run synthesis or implementation on a user project.

## Configure an MCP client

### pipx installation

Find the absolute executable path:

```powershell
(Get-Command vivado-mcp-win).Source
```

Use that path in the MCP configuration:

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

### Virtual-environment installation

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

Using an absolute executable or Python path avoids depending on the MCP client's PATH environment.

## Vivado path resolution

`VIVADO_PATH` and the `start_session` tool's `vivado_path` argument may point to:

- a complete `vivado.bat`, `vivado.cmd`, `vivado.exe`, or Linux `vivado` file;
- a Vivado `bin` directory;
- a Vivado version directory.

Without an explicit path, the server checks PATH and common locations. On Windows it searches paths such as:

```text
C:\Xilinx\Vivado\*\bin\vivado.bat
C:\AMD\Vivado\*\bin\vivado.bat
C:\Program Files\AMD\Vivado\*\bin\vivado.bat
```

The newest detected version is preferred.

## What the automated Windows tests cover

GitHub-hosted Windows runners do not include Vivado. The hosted suite therefore uses a Tcl-compatible fake launcher to exercise the same process and framing code used with Vivado:

- `.bat` launch through `cmd.exe`;
- launcher paths containing spaces and parentheses;
- version-directory and environment-variable resolution;
- persistent command execution;
- stdout with and without a trailing newline;
- Windows paths, braces, semicolons, multiline data, and Chinese Unicode;
- Tcl errors and Vivado-style error messages;
- timeout handling and process-tree termination;
- wheel build, installation into a clean environment outside the source tree, console-script discovery, and doctor execution.

A separate manual workflow, `.github/workflows/real-vivado-windows-smoke.yml`, targets a self-hosted Windows runner labelled `vivado`. It runs the doctor against an installed, licensed Vivado distribution. This workflow cannot run on GitHub's standard hosted runner because Vivado is not preinstalled there.

## Capabilities

| Category | Representative tools | Purpose |
|---|---|---|
| Session management | `start_session`, `stop_session`, `session_status`, `get_host_status` | Start or stop Vivado and inspect session or host state |
| Project management | `open_project`, `close_project`, `get_project_info` | Open `.xpr` projects and read project information |
| Design flow | `run_synthesis`, `run_implementation`, `generate_bitstream` | Run synthesis, place-and-route, and bitstream generation |
| Reports | `get_timing_summary`, `get_timing_paths`, `get_utilization`, `get_clocks`, `get_messages` | Read timing, resource, clock, and message reports |
| Design queries | `get_design_hierarchy`, `get_ports`, `get_nets`, `get_cells` | Inspect hierarchy, ports, nets, and cells |
| Simulation | `launch_simulation`, `run_simulation`, `restart_simulation`, `get_signal_value` | Control xsim and inspect signals |
| Advanced | `run_tcl`, `generate_full_report`, `read_report_section` | Execute arbitrary Tcl and read large reports |

## Architecture

```text
┌────────────────────┐      MCP / stdio       ┌────────────────────┐
│ MCP-compatible     │ ◄────────────────────► │ Vivado MCP Server  │
│ client             │                         └─────────┬──────────┘
└────────────────────┘                                   │ subprocess
                                                         │ persistent Tcl
                                                         ▼
                                               ┌────────────────────┐
                                               │ AMD/Xilinx Vivado  │
                                               │     -mode tcl      │
                                               └────────────────────┘
```

Each command is transported as UTF-8 hex and wrapped with unique markers. The server extracts stdout, the Tcl result, return code, and error stack without relying on the localized `Vivado%` prompt.

## Troubleshooting

### Vivado does not start

Verify the launcher directly:

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

Then run `vivado-mcp-win-doctor` and inspect the failed step. Check the path, Vivado installation, permissions, environment, and license configuration.

### Chinese output is corrupted

The Windows decoder defaults to the system preferred encoding. Override it when necessary:

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2"
```

Use `utf-8`, `gbk`, or the encoding that matches the Vivado Tcl console on that computer.

### The MCP client cannot find the command

Use `(Get-Command vivado-mcp-win).Source` and put the returned absolute path in the client configuration. Restart the client after editing its configuration.

### A command times out

The server terminates the Vivado process tree after a timeout to avoid a desynchronized session. Start a new session and use a larger timeout for long synthesis or implementation runs.

More Windows guidance is available in [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md).

## Security

`run_tcl` can execute arbitrary Tcl with the current user's permissions, including file operations and external process launches. Expose this server only to trusted MCP clients and review high-impact commands and paths.

## Development

```bash
python -m pip install -e ".[dev]"
python -m compileall -q .
python -m pytest -q
python -m ruff check vivado_session.py doctor.py tests
python -m build --wheel
python tests/package_smoke.py dist
```

## License

This project is available under the [MIT License](LICENSE).

## Acknowledgments

- Original project created by Corey Hahn.
- Built on the [Model Context Protocol](https://modelcontextprotocol.io/).
- Integrates with [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html).
