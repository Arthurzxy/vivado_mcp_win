# Vivado MCP — Windows installation

This patch replaces the Unix-only `pexpect.spawn` session with a persistent
`subprocess` implementation that supports Windows 10/11 and Linux.

## Tested design targets

- Python 3.10–3.12
- Vivado 2023.2 and newer launch conventions
- Native Windows `vivado.bat`
- Linux `vivado`

The implementation is not tied to a particular FPGA family. It can be used
with 7-series devices such as XC7K325T and with newer families supported by the
installed Vivado version.

## Install on Windows PowerShell

```powershell
# Run inside your fork of coreyhahn/vivado_mcp
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

## MCP configuration

Using the virtual environment's Python directly is the most reliable approach:

```json
{
  "mcpServers": {
    "vivado": {
      "command": "C:\\work\\vivado_mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "vivado_mcp"],
      "env": {
        "VIVADO_PATH": "D:\\Xilinx\\Vivado\\2025.2\\bin\\vivado.bat"
      }
    }
  }
}
```

`VIVADO_PATH` may point to:

- the full `vivado.bat` path;
- a Vivado `bin` directory;
- a Vivado version directory.

It can be omitted when Vivado is in `PATH`. The server also searches common
Windows locations such as `C:\Xilinx\Vivado\*\bin\vivado.bat` and
`C:\AMD\Vivado\*\bin\vivado.bat` and selects the newest detected version.

## Quick smoke test

After the MCP server is configured, ask the client to run:

1. `start_session`
2. `run_tcl` with `version -short`
3. `run_tcl` with `pwd`
4. `session_status`
5. `stop_session`

## What changed

- Native Windows process launch through `cmd.exe` for `.bat`/`.cmd` files.
- Native Linux process launch without a shell.
- UUID-framed Tcl protocol instead of waiting for the `Vivado%` prompt.
- UTF-8 hex encoding of commands, preventing quotes, braces, semicolons,
  backslashes, multiline Tcl, and Windows paths from escaping the wrapper.
- Tcl `catch` return code and error stack are returned to the MCP client.
- A background binary pipe reader handles output that does not end in a newline.
- A timed-out command terminates the process tree instead of leaving the session
  silently desynchronized.
- Cross-platform temporary report directory.
- Windows and Linux CI tests using a fake Vivado shell.

## Notes

Vivado itself is not bundled. The installed Vivado version and device licenses
still determine which synthesis, implementation, simulation, and programming
operations are available.
