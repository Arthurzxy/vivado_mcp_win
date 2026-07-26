#!/usr/bin/env python3
"""Tiny Vivado Tcl-shell simulator used by unit and package-install tests."""

from __future__ import annotations

import base64
import os
import re
import sys
import time


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


print("Fake Vivado 2025.2")
print("Vivado%", flush=True)

for line in sys.stdin:
    if line.strip() == "exit":
        break

    token_match = re.search(r"__VIVADO_MCP_BEGIN_([0-9a-f]+)__", line)
    hex_match = re.search(r"binary decode hex ([0-9a-f]+)", line)
    if not token_match or not hex_match:
        print("Vivado%", flush=True)
        continue

    token = token_match.group(1)
    command = bytes.fromhex(hex_match.group(1)).decode("utf-8")
    begin = f"__VIVADO_MCP_BEGIN_{token}__"
    meta = f"__VIVADO_MCP_META_{token}__"
    error = f"__VIVADO_MCP_ERROR_{token}__"
    rc_marker = f"__VIVADO_MCP_RC_{token}__"
    end = f"__VIVADO_MCP_END_{token}__"

    stdout = ""
    stdout_no_newline = False
    result = ""
    error_info = ""
    rc = 0

    if "__vivado_mcp_handshake" in command:
        result = "READY"
    elif "__vivado_mcp_health" in command:
        result = "HEALTH_OK"
    elif command == "version -short":
        result = "2025.2"
    elif command == "info patchlevel":
        result = "8.6.13"
    elif command == "pwd":
        result = os.getcwd().replace("\\", "/")
    elif command == "expr {6 * 7}":
        result = "42"
    elif command.startswith("puts -nonewline "):
        payload = command[len("puts -nonewline "):].strip()
        if payload.startswith("{") and payload.endswith("}"):
            payload = payload[1:-1]
        stdout = payload
        stdout_no_newline = True
    elif command.startswith("puts "):
        payload = command[5:].strip()
        if payload.startswith("{") and payload.endswith("}"):
            payload = payload[1:-1]
        stdout = payload
    elif command.startswith("error "):
        payload = command[6:].strip()
        if payload.startswith("{") and payload.endswith("}"):
            payload = payload[1:-1]
        result = payload
        error_info = f'{payload}\n    while executing\n"{command}"'
        rc = 1
    elif command.startswith("after "):
        milliseconds = int(command.split()[1])
        time.sleep(milliseconds / 1000)
    elif command.startswith("set "):
        parts = command.split(maxsplit=2)
        result = parts[2] if len(parts) == 3 else ""
        if result.startswith("{") and result.endswith("}"):
            result = result[1:-1]
    else:
        result = command

    print(begin)
    if stdout:
        if stdout_no_newline:
            sys.stdout.write(stdout)
        else:
            print(stdout)
    print(f"{meta}{b64(result)}")
    if error_info:
        print(f"{error}{b64(error_info)}")
    print(f"{rc_marker}{rc}")
    print(end)
    print("Vivado%", flush=True)
