<p align="center">
  <a href="README.md">简体中文</a> | <strong>English</strong>
</p>

<h1 align="center">Vivado MCP Native</h1>

<p align="center">
  Let Claude, Cursor, Cline, Cherry Studio, and other MCP-compatible AI clients<br/>
  launch, control, and analyze AMD/Xilinx Vivado natively on Windows and Linux.
</p>

<p align="center">
  <a href="https://pypi.org/project/vivado-mcp-native/"><img src="https://img.shields.io/pypi/v/vivado-mcp-native?label=PyPI" alt="PyPI"/></a>
  <img src="https://img.shields.io/pypi/pyversions/vivado-mcp-native" alt="Python"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue" alt="Platform"/>
  <img src="https://img.shields.io/badge/transport-MCP%20stdio-7c3aed" alt="MCP stdio"/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/></a>
</p>

> **Let AI handle repetitive Vivado operations, report extraction, and Tcl calls so you can focus on FPGA architecture, constraints, and engineering decisions.**

Vivado MCP Native is a local Model Context Protocol server for **AMD/Xilinx Vivado**. It maintains a persistent Vivado Tcl session so an AI client can open projects, run synthesis and implementation, generate bitstreams, inspect timing and utilization, control simulation, and execute advanced Tcl commands.

The project uses Python `subprocess` to manage Vivado natively on Windows and Linux. It does not depend on the Unix-only `pexpect` transport. Both the MCP server and Vivado run on the user's machine; this project does not automatically upload FPGA projects to a cloud service.

> [!IMPORTANT]
> Vivado is not included. Device support, IP availability, licensed features, and supported FPGA families depend on the Vivado installation on the host machine.

> [!WARNING]
> The PyPI name `vivado-mcp` belongs to another project. Install this project as **`vivado-mcp-native`**.

---

## What it can do

| Category | Main capabilities | Typical use |
|---|---|---|
| Vivado sessions | Start, stop, health-check, recover, and inspect session statistics | Reuse one Vivado Tcl process instead of restarting Vivado for every request |
| Project management | Open/close `.xpr` projects and read project information | Inspect the target part, top module, project directory, and current run state |
| Design flow | Run synthesis, implementation, and bitstream generation | Automate `synth_1`, `impl_1`, and bitstream tasks while checking actual Vivado status |
| Timing analysis | Read WNS, TNS, WHS, THS, and critical paths | Determine whether timing is met and inspect setup/hold violations |
| Utilization analysis | Read LUT, FF, BRAM, DSP, and IO usage | Check whether the design fits and locate resource hot spots |
| Message diagnosis | Collect ERROR, CRITICAL WARNING, and WARNING messages | Summarize build issues and prioritize debugging |
| Design queries | Inspect hierarchy, ports, nets, and cells | Verify synthesized connectivity, module instances, and signal names |
| Vivado simulation | Launch, restart, step, inspect signals, and manage breakpoints | Control xsim and inspect testbench behavior |
| Tcl escape hatch | Execute arbitrary Vivado Tcl commands | Access Vivado functions that do not yet have a dedicated MCP tool |
| Large reports | Generate complete reports and read selected sections | Avoid flooding the AI context with very large Vivado reports |

### Example prompts

```text
Start Vivado and verify that the session is healthy.

Open D:\FPGA\my_project\my_project.xpr and report the target device, top module, and current run status.

Run synthesis with 8 parallel jobs. When it finishes, summarize all errors, critical warnings, and resource usage.

Analyze timing and tell me whether WNS/TNS are met. List the 10 worst setup paths.

Only analyze failing paths in the clk_250m domain that pass through u_tdc.

Run implementation and generate the bitstream. Confirm the actual STATUS and PROGRESS of every step.

Launch behavioral simulation, run for 1 us, and read /tb/dut/data_out and /tb/dut/valid.

Execute Tcl: report_drc -ruledecks default, then summarize the highest-priority problems.
```

---

## Why use this project

| Common problem | Vivado MCP Native approach |
|---|---|
| Traditional `pexpect` solutions are difficult to run natively on Windows | Launches `vivado.bat`, `vivado.cmd`, or Linux `vivado` with native `subprocess` handling |
| Vivado startup is slow | Reuses one persistent Tcl session across MCP calls |
| Tcl contains quotes, braces, backslashes, multiline text, or Unicode paths | Uses UTF-8 hex transport and unique framing markers |
| Localized Vivado prompts vary | Does not rely on parsing the `Vivado%` prompt |
| Timed-out commands can leave child processes behind | Terminates the full Vivado process tree after a timeout |
| Reports are too large for one AI response | Writes full reports to files and reads them by line range or regular expression |
| Vivado path or output encoding is uncertain | Includes the `vivado-mcp-native-doctor` diagnostic command |

---

## Requirements

| Component | Requirement |
|---|---|
| Operating system | Windows 10/11 or Linux |
| Python | 3.10–3.12 |
| Vivado | AMD/Xilinx Vivado installed locally |
| License | Appropriate for the devices, IP, and design flow being used |
| MCP client | Supports local `stdio` MCP servers |

---

## Installation

### Option 1: Install with pip

Windows PowerShell:

```powershell
py -m pip install --upgrade vivado-mcp-native
```

Linux:

```bash
python3 -m pip install --upgrade vivado-mcp-native
```

Verify the installation:

```powershell
py -m pip show vivado-mcp-native
vivado-mcp-native-doctor --help
```

### Option 2: Install with pipx (recommended)

`pipx` creates an isolated environment for the MCP server and reduces dependency conflicts with other Python applications.

Windows:

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

Upgrade later with:

```powershell
py -m pipx upgrade vivado-mcp-native
```

### Option 3: Install directly from GitHub

Install the latest `master` branch:

```powershell
py -m pip install --upgrade "git+https://github.com/Arthurzxy/vivado_mcp_native.git@master"
```

With pipx:

```powershell
py -m pipx install --force "git+https://github.com/Arthurzxy/vivado_mcp_native.git@master"
```

Install the GitHub ZIP without requiring Git:

```powershell
py -m pip install --upgrade "https://github.com/Arthurzxy/vivado_mcp_native/archive/refs/heads/master.zip"
```

For development or source modification:

```powershell
git clone https://github.com/Arthurzxy/vivado_mcp_native.git
cd vivado_mcp_native
py -m pip install -e .
```

### Installed commands

| Command | Purpose |
|---|---|
| `vivado-mcp-native` | Start the MCP stdio server |
| `vivado-mcp-native-doctor` | Check Python, Vivado, Tcl, and Unicode communication |
| `vivado-mcp-win` | Compatibility alias for the server |
| `vivado-mcp-win-doctor` | Compatibility alias for the doctor command |

---

## Quick start

### 1. Select the Vivado installation

`VIVADO_PATH` may point to:

- a complete `vivado.bat`, `vivado.cmd`, `vivado.exe`, or Linux `vivado` launcher;
- the Vivado `bin` directory;
- the Vivado version directory.

Windows:

```powershell
$env:VIVADO_PATH = "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat"
```

Linux:

```bash
export VIVADO_PATH="/tools/Xilinx/Vivado/2025.2/bin/vivado"
```

Without an explicit value, the server checks PATH and common installation locations.

### 2. Run the doctor command

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat"
```

Machine-readable output:

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Software\Xilinx\2025.2.1" --json
```

The doctor checks launcher resolution, persistent Tcl startup, Vivado/Tcl versions, Tcl execution, Unicode round-trip handling, session health, and clean shutdown. It does not open or modify a user project.

### 3. Configure an MCP client

Find the installed executable:

```powershell
(Get-Command vivado-mcp-native).Source
```

#### Use the installed console command

Replace the paths below with values from your machine:

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

#### Start through the Python module

Useful for a virtual environment or a normal `pip install`:

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

Use absolute executable paths whenever possible because an MCP client may have a different PATH from your terminal.

Restart the MCP client after saving the configuration, then ask:

```text
Check the Vivado MCP host status, start a session, and report the Vivado version.
```

---

## Recommended workflow

```text
1. vivado-mcp-native-doctor     Validate the local environment
2. start_session                Start the persistent Vivado Tcl session
3. open_project                 Open the .xpr project
4. get_project_info             Confirm device, top, and project information
5. run_synthesis                Run synthesis
6. get_messages                 Review errors and warnings
7. get_timing_summary           Check WNS/TNS/WHS/THS
8. get_utilization              Check LUT/FF/BRAM/DSP/IO usage
9. run_implementation           Run place and route
10. get_timing_paths            Analyze the worst paths
11. generate_bitstream          Generate the bitstream
12. stop_session                Close Vivado and release resources
```

Large synthesis and implementation runs may require a larger `timeout` and an appropriate `jobs` value for the host CPU and memory.

---

## MCP tool overview

### Session management

- `start_session`, `stop_session`, `session_status`;
- `check_session_health` for health checks and recovery;
- `get_host_status` for hostname, memory, and session state.

### Project and design flow

- `open_project`, `close_project`, `get_project_info`;
- `run_synthesis`, `run_implementation`, `generate_bitstream`.

### Reports and design queries

- `get_timing_summary`, `get_timing_paths`, `get_utilization`;
- `get_clocks`, `get_messages`;
- `get_design_hierarchy`, `get_ports`, `get_nets`, `get_cells`.

### Simulation

- `set_simulation_top`, `launch_simulation`, `close_simulation`;
- `run_simulation`, `step_simulation`, `restart_simulation`;
- `get_signal_value`, `get_signal_values`;
- `get_scopes`, `get_simulation_objects`, `add_signals_to_wave`;
- `add_breakpoint`, `remove_breakpoints`, `get_simulation_messages`.

### Advanced operations

- `run_tcl` executes arbitrary Vivado Tcl;
- `generate_full_report` writes complete timing, utilization, power, or DRC reports;
- `read_report_section` reads large reports by line range or regular expression;
- `request_feature` and `list_feature_requests` record missing capabilities.

---

## Architecture

```text
Claude / Cursor / Cline / Cherry Studio / another MCP client
                         │
                         │ MCP stdio / JSON-RPC
                         ▼
                 Vivado MCP Native
                         │
                         │ persistent subprocess Tcl session
                         ▼
              AMD/Xilinx Vivado -mode tcl
                         │
                         ▼
                 Local FPGA projects and reports
```

Each Tcl command is encoded as UTF-8 hex and wrapped with unique markers. The server extracts stdout, the Tcl result, return code, and error stack without relying on a localized `Vivado%` prompt.

---

## Troubleshooting

### `vivado-mcp-native` is not found

```powershell
py -m pipx ensurepath
(Get-Command vivado-mcp-native).Source
```

Restart the terminal or use the returned absolute path in the MCP configuration.

### Vivado is not found

Verify the launcher directly:

```powershell
& "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat" -mode tcl
```

Then run:

```powershell
vivado-mcp-native-doctor --vivado-path "D:\Software\Xilinx\2025.2.1\Vivado\bin\vivado.bat"
```

### Chinese output is corrupted

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
```

Use `utf-8`, `gbk`, or the encoding used by the local Vivado Tcl console.

### Synthesis or implementation times out

The server terminates the full Vivado process tree after a timeout to avoid reusing a desynchronized session. Start a new session and increase the `timeout` for large designs.

### Are `vivado-mcp` and `vivado-mcp-native` the same package?

No. Install this project with:

```powershell
py -m pip install vivado-mcp-native
```

See [`WINDOWS_INSTALL.md`](WINDOWS_INSTALL.md) for additional Windows guidance.

---

## Security

`run_tcl` can execute arbitrary Tcl with the current user's permissions, including file operations and external program launches.

- Connect only trusted MCP clients and models;
- review target paths before destructive or overwrite operations;
- keep important FPGA projects under version control and backed up;
- do not expose a local Vivado MCP server directly to the public internet without authentication and isolation.

---

## Official MCP Registry

Registry identity:

```text
io.github.Arthurzxy/vivado-mcp-native
```

Registry metadata is stored in [`server.json`](server.json). The current release is `0.2.1` and uses the local `stdio` transport.

---

## Contributing

Issues and pull requests are welcome for:

- additional Vivado tools;
- compatibility improvements across Vivado versions;
- better report parsing;
- more MCP client configuration examples;
- documentation corrections and translations.

---

## License and acknowledgments

This project is available under the [MIT License](LICENSE).

- Original project created by Corey Hahn;
- built on the [Model Context Protocol](https://modelcontextprotocol.io/);
- integrates with [AMD/Xilinx Vivado](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado.html).
