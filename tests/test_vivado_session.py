from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import pytest
from vivado_mcp.doctor import run_diagnostics
from vivado_mcp.vivado_session import (
    VivadoSession,
    build_launch_command,
    classify_output_errors,
    resolve_vivado_path,
)

FAKE_VIVADO = Path(__file__).with_name(
    "fake_vivado.cmd" if os.name == "nt" else "fake_vivado.py"
)
FAKE_VIVADO_PY = Path(__file__).with_name("fake_vivado.py")


def make_executable(path: Path) -> None:
    if os.name != "nt":
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_windows_batch_launch_command() -> None:
    command = build_launch_command(
        r"C:\Xilinx\Vivado\2025.2\bin\vivado.bat",
        platform_name="nt",
        comspec=r"C:\Windows\System32\cmd.exe",
    )
    assert isinstance(command, str)
    assert command.startswith(r"C:\Windows\System32\cmd.exe /d /s /c ")
    assert command.endswith('"')
    assert r"C:\Xilinx\Vivado\2025.2\bin\vivado.bat" in command
    assert "-mode tcl" in command


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


def test_resolve_version_directory_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    version_dir = tmp_path / "AMD Tools" / "Vivado" / "2025.2"
    bin_dir = version_dir / "bin"
    bin_dir.mkdir(parents=True)
    launcher = bin_dir / ("vivado.bat" if os.name == "nt" else "vivado")
    launcher.write_text(
        "@echo off\r\n" if os.name == "nt" else "#!/bin/sh\n",
        encoding="utf-8",
    )
    make_executable(launcher)

    monkeypatch.setenv("VIVADO_PATH", str(version_dir))
    assert resolve_vivado_path("vivado") == str(launcher.resolve())


def test_error_classification_ignores_report_wording() -> None:
    report = "Design Timing Summary\nWNS(ns): 0.100\nTiming ERROR: 0"
    classification = classify_output_errors(report)
    assert classification.is_report_content
    assert not classification.is_actual_failure


def test_error_classification_detects_vivado_error() -> None:
    classification = classify_output_errors("ERROR: [Synth 8-87] cannot read file")
    assert classification.is_actual_failure


def test_persistent_session_and_framing() -> None:
    make_executable(FAKE_VIVADO)
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


@pytest.mark.skipif(os.name != "nt", reason="Windows cmd.exe quoting test")
def test_windows_vivado_batch_path_with_spaces(tmp_path: Path) -> None:
    bin_dir = tmp_path / "AMD Tools (Test)" / "Vivado" / "2025.2" / "bin"
    bin_dir.mkdir(parents=True)
    shutil.copy2(FAKE_VIVADO_PY, bin_dir / "fake_vivado.py")
    launcher = bin_dir / "vivado.bat"
    launcher.write_text(
        '@echo off\r\npython "%~dp0fake_vivado.py" %*\r\n',
        encoding="utf-8",
    )

    session = VivadoSession(str(launcher), timeout=5)
    started = session.start()
    assert started.success, started.output
    result = session.run_tcl("version -short")
    assert result.success
    assert result.output == "2025.2"
    assert session.stop().success


def test_doctor_runs_full_smoke_sequence() -> None:
    make_executable(FAKE_VIVADO)
    report = run_diagnostics(str(FAKE_VIVADO), timeout=5)
    assert report["success"], report
    steps = {step["name"]: step for step in report["steps"]}
    assert steps["vivado_version"]["output"] == "2025.2"
    assert steps["tcl_expression"]["output"] == "42"
    assert steps["unicode_round_trip"]["output"] == "中文路径测试"
    assert steps["session_health"]["success"]
    assert steps["stop_session"]["success"]


def test_timeout_stops_desynchronized_process() -> None:
    make_executable(FAKE_VIVADO)
    session = VivadoSession(str(FAKE_VIVADO), timeout=0.05)
    assert session.start().success
    result = session.run_tcl("after 500")
    assert not result.success
    assert "timed out" in result.output.lower()
    assert not session.is_running
