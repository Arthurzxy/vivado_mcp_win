"""
Vivado MCP Native - Direct integration with AMD/Xilinx Vivado.

This package provides a Model Context Protocol (MCP) server that allows
AI assistants to interact with AMD/Xilinx Vivado FPGA development tools.

Features:
    - Session Management: Start/stop persistent Vivado Tcl sessions
    - Project Management: Open/close Vivado projects (.xpr files)
    - Design Flow: Run synthesis, implementation, and bitstream generation
    - Reports: Get timing summaries, utilization, and design analysis
    - Design Queries: Explore design hierarchy, ports, nets, and cells
    - Simulation: Control Vivado's integrated simulator (xsim)
    - Raw Tcl: Execute arbitrary Vivado Tcl commands

Installation:
    pip install vivado-mcp-native

    Or install the isolated application with pipx:
    pipx install vivado-mcp-native

Usage:
    The server is typically launched by an MCP client.

    Main commands:
    - vivado-mcp-native
    - vivado-mcp-native-doctor

    Compatibility aliases:
    - vivado-mcp-win
    - vivado-mcp-win-doctor

    The package can also be started with:
    python -m vivado_mcp

Example workflow:
    1. start_session - Launch Vivado
    2. open_project - Open a .xpr file
    3. run_synthesis - Synthesize the design
    4. get_timing_summary - Check if timing is met
    5. get_utilization - Check resource usage
    6. stop_session - Clean up

Requirements:
    - Python 3.10+
    - mcp>=1.0.0
    - psutil>=5.9.0
    - AMD/Xilinx Vivado installed locally

Author: Arthurzxy
License: MIT
Version: 0.2.0
"""

import asyncio

from .server import main as _async_main

__version__ = "0.2.0"


def main():
    """Start the Vivado MCP Native stdio server."""
    asyncio.run(_async_main())


__all__ = ["main", "__version__"]
