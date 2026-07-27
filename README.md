# Vivado MCP Native

**English** | [简体中文](https://github.com/Arthurzxy/vivado_mcp_native/blob/master/README.zh-CN.md)

A cross-platform Model Context Protocol (MCP) server for **AMD/Xilinx Vivado**. It lets MCP-compatible AI clients start and manage Vivado, open projects, run synthesis and implementation, inspect timing and utilization, control simulation, and execute Tcl commands.

This project uses a persistent `subprocess` Tcl session that works natively on Windows and Linux. It does not depend on the Unix-only `pexpect` transport.

> [!IMPORTANT]
> Vivado is not included. Device support, licensed features, and available FPGA families are determined by the Vivado installation on the host machine.

> [!WARNING]
> The name `vivado-mcp` on PyPI belongs to a different project. Install this project as `vivado-mcp-native`.

## Highlights

- Native launch of Windows `vivado.bat` and `vivado.cmd` files.
- Direct Linux executable launch without an intermediate shell.
- One persistent Vivado Tcl process reused across MCP calls.
- UUID-framed command protocol that separates stdout, Tcl return values, return codes, and error stacks.
- UTF-8 hex transport for quotes, braces, backslashes, multiline Tcl, Unicode, and Windows paths.
- Full process-tree cleanup after command timeouts.
- Vivado discovery through `VIVADO_PATH`, PATH, and common installation directories.
- A `vivado-mcp-native-doctor` command for checking the local Python-to-Vivado connection.

## Requirements

| Component | Requirement |
|---|---|
| Operating system | Windows 10/11 or Linux |
| Python | 3.10–3.12 |
| Vivado | Local AMD/Xilinx Vivado installation |
| License | Appropriate for the operations and FPGA devices you use |

## Installation

### From PyPI — recommended

Install the isolated command-line application with `pipx`:

```powershell
py -m pip install --user --upgrade pipx
py -m pipx ensurepath
py -m pipx install vivado-mcp-native
```

Linux:

```bash
python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath
python3 -m pipx install vivado-mcp-native
```

Installed commands:

- `vivado-mcp-native` — start the MCP server;
- `vivado-mcp-native-doctor` — check the local Vivado connection;
- `vivado-mcp-win` and `vivado-mcp-win-doctor` — compatibility aliases.

### Install the latest source from GitHub

```powershell
py -m pipx install --force "https://github.com/Arthurzxy/vivado_mcp_native/archive/refs/heads/master.zip"
```

### Dedicated virtual environment

```powershell
$venv = "$env:LOCALAPPDATA\vivado-mcp-native"
py -3.11 -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install --upgrade vivado-mcp-native
```

## Select the Vivado installation

`VIVADO_PATH` and the `start_session` tool's `vivado_path` argument may point to:

- the complete `vivado.bat`, `vivado.cmd`, `vivado.exe`, or Linux `vivado` launcher;
- the Vivado `bin` directory;
- the Vivado version directory.

Example:

```powershell
$env:VIVADO_PATH = "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

Without an explicit path, the server checks PATH and common Windows locations such as:

```text
C:\Xilinx\Vivado\*\bin\vivado.bat
C:\AMD\Vivado\*\bin\vivado.bat
C:\Program Files\AMD\Vivado\*\bin\vivado.bat
```

## Check the Vivado connection

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

The path may also be a Vivado `bin` directory or version directory. Machine-readable output is available with `--json`:

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Xilinx\Vivado\2025.2" --json
```

The diagnostic command resolves the launcher, starts a persistent Tcl session, queries Vivado and Tcl versions, checks Tcl command transport and Unicode handling, verifies session health, and closes Vivado cleanly. It does not open or modify a user project.

## Configure an MCP client

Find the installed executable:

```powershell
(Get-Command vivado-mcp-native).Source
```

Example configuration for a pipx installation:

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\Users\\you\\.local\\bin\\vivado-mcp-native.exe",
      "env": {
        "VIVADO_PATH": "D:\\Xilinx\\Vivado\\2025.2\\bin\\vivado.bat"
      }
    }
  }
}
```

Example configuration for a virtual environment:

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\Users\\you\\AppData\\Local\\vivado-mcp-native\\Scripts\\python.exe",
      "args": ["-m", "vivado_mcp"],
      "env": {
        "VIVADO_PATH": "D:\\Xilinx\\Vivado\\2025.2\\bin\\vivado.bat"
      }
    }
  }
}
```

Using an absolute executable or Python path avoids depending on the MCP client's PATH environment.

## Capabilities

| Category | Representative tools | Purpose |
|---|---|---|
| Session management | `start_session`, `stop_session`, `session_status`, `get_host_status` | Start or stop Vivado and inspect session or host state |
| Project management | `open_project`, `close_project`, `get_project_info` | Open `.xpr` projects and read project information |
| Design flow | `run_synthesis`, `run_implementation`, `generate_bitstream` | Run synthesis, place-and-route, and bitstream generation |
| Reports | `get_timing_summary`, `get_timing_paths`, `get_utilization`, `get_clocks`, `get_messages` | Read timing, resource, clock, and message reports |
| Design queries | `get_design_hierarchy`, `get_ports`, `get_nets`, `get_cells` | Inspect hierarchy, ports, nets, and cells |
| Simulation | `launch_simulation`, `run_simulation`, `restart_simulation`, `get_signal_value` | Control xsim and inspect signals |
| Advanced | `run_tcl`, `generate_full_report`, `read_report_section` | Execute Tcl and read large reports |

## Architecture

```text
MCP-compatible client
        │ MCP / stdio
        ▼
Vivado MCP server
        │ persistent subprocess Tcl session
        ▼
AMD/Xilinx Vivado -mode tcl
```

Each command is transported as UTF-8 hex and wrapped with unique markers. The server extracts stdout, the Tcl result, return code, and error stack without relying on the localized `Vivado%` prompt.

## Troubleshooting

### Vivado does not start

Verify the launcher directly:

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

Then run `vivado-mcp-native-doctor` and check the path, installation, permissions, environment, and license configuration.

### Chinese output is corrupted

Override the Windows output decoder when necessary:

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
```

Use `utf-8`, `gbk`, or the encoding that matches the Vivado Tcl console.

### A command times out

The server terminates the Vivado process tree after a timeout to avoid a desynchronized session. Start a new session and use a larger timeout for long synthesis or implementation runs.

More Windows guidance is available in [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md).

## Security

`run_tcl` can execute arbitrary Tcl with the current user's permissions, including file operations and external process launches. Expose this server only to trusted MCP clients and review high-impact commands and paths.

## License

This project is available under the [MIT License](LICENSE).

## Acknowledgments

- Original project created by Corey Hahn.
- Built on the [Model Context Protocol](https://modelcontextprotocol.io/).
- Integrates with [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html).
