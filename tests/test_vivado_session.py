from __future__ import annotations

import os
import stat
from pathlib import Path

from vivado_session import (
    VivadoSession,
    build_launch_command,
    classify_output_errors,
    resolve_vivado_path,
)

FAKE_VIVADO = Path(__file__).with_name("fake_vivado.cmd" if os.name == "nt" else "fake_vivado.py")


def test_windows_batch_launch_command() -> None:
    command = build_launch_command(
        r"C:\Xilinx\Vivado\2025.2\bin\vivado.bat",
        platform_name="nt",
        comspec=r"C:\Windows\System32\cmd.exe",
    )
    assert command[:4] == [
        r"C:\Windows\System32\cmd.exe",
        "/d",
        "/s",
        "/c",
    ]
    assert "call" in command[4]
    assert "vivado.bat" in command[4]
    assert "-mode tcl" in command[4]


def test_direct_executable_launch_command() -> None:
    assert build_launch_command("/opt/Xilinx/Vivado/2025.2/bin/vivado") == [
        "/opt/Xilinx/Vivado/2025.2/bin/vivado",
        "-mode",
        "tcl",
        "-nojournal",
        "-nolog",
    ]


def test_resolve_explicit_file() -> None:
    assert resolve_vivado_path(str(FAKE_VIVADO)) == str(FAKE_VIVADO.resolve())


def test_error_classification_ignores_report_wording() -> None:
    report = "Design Timing Summary\nWNS(ns): 0.100\nTiming ERROR: 0"
    classification = classify_output_errors(report)
    assert classification.is_report_content
    assert not classification.is_actual_failure


def test_error_classification_detects_vivado_error() -> None:
    classification = classify_output_errors("ERROR: [Synth 8-87] cannot read file")
    assert classification.is_actual_failure


def test_persistent_session_and_framing() -> None:
    if os.name != "nt":
        FAKE_VIVADO.chmod(FAKE_VIVADO.stat().st_mode | stat.S_IXUSR)
    session = VivadoSession(str(FAKE_VIVADO), timeout=2)
    started = session.start()
    assert started.success, started.output

    result = session.run_tcl("set answer 42")
    assert result.success
    assert result.output == "42"

    printed = session.run_tcl("puts {hello from stdout}")
    assert printed.success
    assert printed.output == "hello from stdout"

    no_newline = session.run_tcl("puts -nonewline {no trailing newline}")
    assert no_newline.success
    assert no_newline.output == "no trailing newline"

    windows_path = session.run_tcl(r"set project_path {C:\Work Area\tdc\top.xpr}")
    assert windows_path.success
    assert windows_path.output == r"C:\Work Area\tdc\top.xpr"

    complex_value = "第一行\n第二行; [brackets] {braces} \\path"
    complex_result = session.run_tcl(f"set complex_value {{{complex_value}}}")
    assert complex_result.success
    assert complex_result.output == complex_value

    printed_error = session.run_tcl("puts {ERROR: [Synth 8-87] simulated failure}")
    assert not printed_error.success

    failed = session.run_tcl("error {boom}")
    assert not failed.success
    assert failed.return_value == "1"
    assert "boom" in failed.output

    assert session.is_healthy()
    stopped = session.stop()
    assert stopped.success
    assert not session.is_running


def test_timeout_stops_desynchronized_process() -> None:
    if os.name != "nt":
        FAKE_VIVADO.chmod(FAKE_VIVADO.stat().st_mode | stat.S_IXUSR)
    session = VivadoSession(str(FAKE_VIVADO), timeout=0.05)
    assert session.start().success
    result = session.run_tcl("after 500")
    assert not result.success
    assert "timed out" in result.output.lower()
    assert not session.is_running
