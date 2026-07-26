# Vivado MCP — Windows installation and verification

This guide installs the Windows-native Vivado MCP fork and verifies that it can control a real Vivado Tcl process.

## Requirements

- Windows 10 or Windows 11;
- Python 3.10–3.12;
- AMD/Xilinx Vivado installed locally;
- a valid Vivado license for the operations you plan to run.

> [!WARNING]
> The PyPI name `vivado-mcp` belongs to a different project. Do not use a bare `pip install vivado-mcp` for this repository. Install directly from the GitHub URL below.

## Recommended installation: pipx

`pipx` creates an isolated Python environment and exposes the command-line tools globally.

```powershell
py -m pip install --user --upgrade pipx
py -m pipx ensurepath
py -m pipx install "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

Restart PowerShell if the command is not found after `ensurepath`.

Before this pull request is merged, install the current branch instead:

```powershell
py -m pipx install --force "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/agent/windows-native-support.zip"
```

The dedicated commands are:

```text
vivado-mcp-win
vivado-mcp-win-doctor
```

Compatibility aliases are also installed:

```text
vivado-mcp
vivado-mcp-doctor
```

## Alternative: pip in a dedicated virtual environment

```powershell
$venv = "$env:LOCALAPPDATA\vivado-mcp-win"
py -3.11 -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install --upgrade "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

The server can then be started with:

```powershell
& "$venv\Scripts\vivado-mcp-win.exe"
```

The command is a stdio MCP server, so it normally appears idle when launched directly. It expects an MCP client to communicate over stdin/stdout.

## Select the Vivado installation

`VIVADO_PATH` can point to any of the following:

- the complete `vivado.bat` or `vivado.cmd` file;
- the Vivado `bin` directory;
- the Vivado version directory.

Examples:

```powershell
$env:VIVADO_PATH = "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

```powershell
$env:VIVADO_PATH = "D:\Xilinx\Vivado\2025.2"
```

When `VIVADO_PATH` is omitted, the server checks PATH and common locations such as:

```text
C:\Xilinx\Vivado\*\bin\vivado.bat
C:\AMD\Vivado\*\bin\vivado.bat
C:\Program Files\AMD\Vivado\*\bin\vivado.bat
C:\Program Files\Xilinx\Vivado\*\bin\vivado.bat
```

The newest detected version is selected.

## Verify the real Vivado connection

Run the doctor before configuring your MCP client:

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

The doctor checks:

1. Vivado path resolution;
2. native `.bat` launch through `cmd.exe`;
3. persistent Tcl session startup;
4. `version -short`;
5. `info patchlevel`;
6. `pwd`;
7. `expr {6 * 7}` with an expected result of `42`;
8. Chinese Unicode round-trip;
9. session health;
10. clean shutdown.

Machine-readable output:

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2" --json | Tee-Object vivado-doctor.json
```

A `PASS` result confirms that the package can launch and exchange framed Tcl commands with the installed Vivado process. It does not synthesize a project or validate every licensed Vivado feature.

## Configure an MCP client

### pipx installation

Find the absolute command path:

```powershell
(Get-Command vivado-mcp-win).Source
```

Example configuration:

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

Use the actual absolute path returned by your installation. Restart the MCP client after changing its configuration.

## Manual MCP smoke sequence

After the doctor passes, ask the MCP client to execute:

1. `start_session`;
2. `run_tcl` with `version -short`;
3. `run_tcl` with `pwd`;
4. `session_status`;
5. `stop_session`.

## What the hosted Windows CI validates

GitHub's hosted Windows runner does not include Vivado. The automated suite uses a fake Tcl-compatible launcher but exercises the production session code:

- `.bat` startup through `cmd.exe`;
- paths containing spaces and parentheses;
- persistent stdin/stdout communication;
- UUID response framing;
- Windows paths, multiline Tcl, braces, semicolons, Chinese Unicode, and output without a trailing newline;
- Tcl and Vivado-style errors;
- timeouts and process-tree cleanup;
- wheel building;
- installation into a clean virtual environment outside the repository;
- discovery and execution of `vivado-mcp-win-doctor`.

## Real Vivado GitHub Actions workflow

`.github/workflows/real-vivado-windows-smoke.yml` can be started manually on a Windows self-hosted runner labelled:

```text
self-hosted, Windows, X64, vivado
```

That runner must already contain Vivado and its license environment. The workflow installs the package and runs the doctor, then uploads `vivado-doctor.json`.

## Troubleshooting

### Vivado itself does not start

Test it directly:

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

If this fails, repair the Vivado installation, environment, or license before debugging MCP.

### Chinese text is corrupted

The server defaults to the Windows preferred encoding. Override it when the Vivado console uses another encoding:

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2"
```

Common values are `gbk` and `utf-8`.

### The command is not found

```powershell
py -m pipx ensurepath
(Get-Command vivado-mcp-win).Source
```

Restart PowerShell after changing PATH.

### Vivado opens a console window

The server normally uses `CREATE_NO_WINDOW`. Set the following only when debugging process startup:

```powershell
$env:VIVADO_MCP_SHOW_CONSOLE = "1"
```

### A Tcl command times out

The server stops the complete Vivado process tree to prevent a desynchronized session. Start a new session and increase the timeout for long synthesis or implementation commands.

## Development installation

```powershell
git clone https://github.com/Arthurzxy/vivado_mcp_win.git
cd vivado_mcp_win
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check vivado_session.py doctor.py tests
python -m build --wheel
python tests/package_smoke.py dist
```
