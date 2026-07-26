# Vivado MCP — Windows installation

This guide installs the Windows-native Vivado MCP server and configures it to control a local Vivado Tcl process.

## Requirements

- Windows 10 or Windows 11;
- Python 3.10–3.12;
- AMD/Xilinx Vivado installed locally;
- a valid Vivado license for the operations you plan to run.

> [!WARNING]
> The PyPI name `vivado-mcp` belongs to a different project. Install this repository directly from GitHub.

## Recommended installation: pipx

```powershell
py -m pip install --user --upgrade pipx
py -m pipx ensurepath
py -m pipx install "https://github.com/Arthurzxy/vivado_mcp_win/archive/refs/heads/master.zip"
```

Restart PowerShell if the command is not found after `ensurepath`.

Installed commands:

```text
vivado-mcp-win
vivado-mcp-win-doctor
vivado-mcp
vivado-mcp-doctor
```

## Alternative: dedicated virtual environment

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

`VIVADO_PATH` can point to:

- the complete `vivado.bat` or `vivado.cmd` launcher;
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

## Check the local Vivado connection

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2\bin\vivado.bat"
```

Machine-readable output:

```powershell
vivado-mcp-win-doctor --vivado-path "D:\Xilinx\Vivado\2025.2" --json
```

The diagnostic command resolves the launcher, starts Vivado in Tcl mode, queries the Vivado and Tcl versions, checks command transport and Unicode handling, verifies session health, and closes Vivado cleanly. It does not open or modify a user project.

## Configure an MCP client

Find the absolute command path:

```powershell
(Get-Command vivado-mcp-win).Source
```

Example configuration for a pipx installation:

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

Example configuration for a virtual environment:

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

Restart the MCP client after changing its configuration.

## Troubleshooting

### Vivado itself does not start

```powershell
& "D:\Xilinx\Vivado\2025.2\bin\vivado.bat" -mode tcl
```

If this fails, repair the Vivado installation, environment, or license before debugging MCP.

### Chinese text is corrupted

```powershell
$env:VIVADO_MCP_OUTPUT_ENCODING = "gbk"
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
