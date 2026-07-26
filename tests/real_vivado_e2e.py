"""Real Windows Vivado end-to-end validation for a self-hosted runner.

This script never opens a user project. It creates an isolated temporary project,
exercises one persistent Tcl session, runs synthesis, and validates timeout cleanup.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import types
import typing
from pathlib import Path
from time import monotonic
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

try:
    import typing_extensions  # noqa: F401
except ImportError:
    compatibility = types.ModuleType("typing_extensions")
    compatibility.Self = typing.Self
    sys.modules["typing_extensions"] = compatibility

package = types.ModuleType("vivado_mcp")
package.__path__ = [str(ROOT)]
package.__package__ = "vivado_mcp"
sys.modules.setdefault("vivado_mcp", package)

from vivado_mcp.vivado_session import CommandResult, VivadoSession


def _result_summary(result: CommandResult, *, output_limit: int = 4000) -> dict[str, Any]:
    output = result.output
    return {
        "success": result.success,
        "return_value": result.return_value,
        "elapsed_ms": round(result.elapsed_ms, 3),
        "output_length": len(output),
        "output": output if len(output) <= output_limit else output[:output_limit] + "...",
    }


def _run_check(
    session: VivadoSession,
    name: str,
    command: str,
    *,
    expected: str | None = None,
    timeout: float | None = None,
) -> tuple[bool, dict[str, Any]]:
    result = session.run_tcl(command, timeout_override=timeout)
    expected_ok = expected is None or expected in result.output
    success = result.success and expected_ok
    details = {
        "name": name,
        "command": command,
        "expected": expected,
        **_result_summary(result),
    }
    details["success"] = success
    return success, details


def _tcl_path(path: Path) -> str:
    return "{" + path.resolve().as_posix().replace("}", "\\}") + "}"


def _write_test_design(project_root: Path) -> Path:
    source = project_root / "top.v"
    source.write_text(
        """module top (
    input  wire       clk,
    input  wire       rst,
    output reg  [7:0] q
);

always @(posedge clk) begin
    if (rst)
        q <= 8'h00;
    else
        q <= q + 1'b1;
end

endmodule
""",
        encoding="utf-8",
    )
    return source


def _run_transport_and_synthesis(
    vivado_path: str,
    work_root: Path,
    part: str,
) -> tuple[bool, dict[str, Any]]:
    section: dict[str, Any] = {
        "success": False,
        "part": part,
        "checks": [],
        "stress": {},
        "synthesis": {},
    }
    session = VivadoSession(vivado_path, timeout=600.0)
    all_ok = True

    try:
        started = session.start()
        section["start"] = _result_summary(started)
        if not started.success:
            return False, section

        basic_checks = (
            ("version", "version -short", "2025.2.1"),
            ("tcl_version", "info patchlevel", "8.6"),
            ("expression", "expr {6 * 7}", "42"),
            (
                "windows_unicode_path",
                r"set __mcp_path_test {C:\Work Area (Test)\中文工程\top.xpr}",
                r"C:\Work Area (Test)\中文工程\top.xpr",
            ),
            (
                "multiline_special_characters",
                "set __mcp_multiline_test {第一行\n第二行; [brackets] {braces} \\backslash}",
                "第二行; [brackets] {braces}",
            ),
            ("no_trailing_newline", "puts -nonewline {no trailing newline}", "no trailing newline"),
        )
        for name, command, expected in basic_checks:
            success, details = _run_check(session, name, command, expected=expected)
            section["checks"].append(details)
            all_ok = all_ok and success

        stress_start = monotonic()
        failures: list[dict[str, Any]] = []
        for index in range(100):
            result = session.run_tcl(f"expr {{{index} + 1}}", timeout_override=30)
            expected = str(index + 1)
            if not result.success or result.output.strip() != expected:
                failures.append(
                    {
                        "index": index,
                        "expected": expected,
                        **_result_summary(result, output_limit=500),
                    }
                )
        section["stress"] = {
            "success": not failures,
            "commands": 100,
            "elapsed_ms": round((monotonic() - stress_start) * 1000, 3),
            "failures": failures,
        }
        all_ok = all_ok and not failures

        long_result = session.run_tcl("string repeat X 100000", timeout_override=60)
        long_ok = (
            long_result.success
            and len(long_result.output) == 100000
            and long_result.output.startswith("X")
            and long_result.output.endswith("X")
        )
        section["long_output"] = {
            "success": long_ok,
            "length": len(long_result.output),
            "return_value": long_result.return_value,
            "elapsed_ms": round(long_result.elapsed_ms, 3),
        }
        all_ok = all_ok and long_ok

        intentional = session.run_tcl("error {intentional MCP test error}", timeout_override=30)
        error_ok = (not intentional.success) and "intentional MCP test error" in intentional.output
        recovery = session.run_tcl("expr {20 + 22}", timeout_override=30)
        recovery_ok = recovery.success and recovery.output.strip() == "42" and session.is_healthy()
        section["error_recovery"] = {
            "success": error_ok and recovery_ok,
            "intentional_error": _result_summary(intentional, output_limit=1500),
            "recovery": _result_summary(recovery, output_limit=500),
            "healthy_after_error": recovery_ok,
        }
        all_ok = all_ok and error_ok and recovery_ok

        project_root = work_root / "temporary-project"
        project_root.mkdir(parents=True, exist_ok=True)
        source = _write_test_design(project_root)
        project_dir = project_root / "mcp_real_smoke"

        part_result = session.run_tcl(
            f"llength [get_parts -quiet {part}]",
            timeout_override=60,
        )
        part_available = part_result.success and part_result.output.strip() not in {"", "0"}
        synthesis: dict[str, Any] = {
            "part_available": part_available,
            "part_query": _result_summary(part_result),
            "project_dir": str(project_dir),
            "commands": [],
        }
        section["synthesis"] = synthesis
        if not part_available:
            synthesis["success"] = False
            synthesis["status"] = "BLOCKED_PART_NOT_INSTALLED"
            return False, section

        synthesis_commands = (
            (
                "create_project",
                f"create_project -force mcp_real_smoke {_tcl_path(project_dir)} -part {part}",
                120.0,
            ),
            ("add_files", f"add_files {_tcl_path(source)}", 60.0),
            ("set_top", "set_property top top [current_fileset]", 30.0),
            ("update_compile_order", "update_compile_order -fileset sources_1", 60.0),
            ("launch_synthesis", "launch_runs synth_1 -jobs 2", 120.0),
            ("wait_synthesis", "wait_on_run synth_1", 600.0),
        )
        synthesis_ok = True
        for name, command, timeout in synthesis_commands:
            result = session.run_tcl(command, timeout_override=timeout)
            command_ok = result.success
            synthesis["commands"].append(
                {"name": name, "command": command, **_result_summary(result)}
            )
            synthesis_ok = synthesis_ok and command_ok
            if not command_ok:
                break

        if synthesis_ok:
            status = session.run_tcl("get_property STATUS [get_runs synth_1]", timeout_override=60)
            progress = session.run_tcl(
                "get_property PROGRESS [get_runs synth_1]",
                timeout_override=60,
            )
            synthesis["status"] = _result_summary(status)
            synthesis["progress"] = _result_summary(progress)
            status_ok = status.success and "Complete" in status.output
            progress_ok = progress.success and "100%" in progress.output
            synthesis_ok = synthesis_ok and status_ok and progress_ok

        if synthesis_ok:
            open_run = session.run_tcl("open_run synth_1", timeout_override=180)
            cells = session.run_tcl("llength [get_cells -hier -quiet]", timeout_override=60)
            ports = session.run_tcl("llength [get_ports -quiet]", timeout_override=60)
            utilization = session.run_tcl("report_utilization -return_string", timeout_override=120)
            synthesis["open_run"] = _result_summary(open_run)
            synthesis["cell_count"] = _result_summary(cells)
            synthesis["port_count"] = _result_summary(ports)
            synthesis["utilization"] = _result_summary(utilization, output_limit=12000)
            synthesis_ok = synthesis_ok and all(
                result.success for result in (open_run, cells, ports, utilization)
            )

        close_project = session.run_tcl("close_project", timeout_override=60)
        synthesis["close_project"] = _result_summary(close_project)
        synthesis_ok = synthesis_ok and close_project.success
        synthesis["success"] = synthesis_ok
        all_ok = all_ok and synthesis_ok

        section["stats"] = session.get_stats()
        section["success"] = all_ok
        return all_ok, section
    finally:
        stopped = session.stop()
        section["stop"] = _result_summary(stopped)
        if not stopped.success:
            section["success"] = False


def _run_timeout_cleanup(vivado_path: str) -> tuple[bool, dict[str, Any]]:
    session = VivadoSession(vivado_path, timeout=60.0)
    details: dict[str, Any] = {}
    try:
        started = session.start()
        details["start"] = _result_summary(started)
        if not started.success:
            details["success"] = False
            return False, details

        process_id = session.process.pid if session.process is not None else None
        result = session.run_tcl("after 5000", timeout_override=0.2)
        success = (
            not result.success
            and "timed out" in result.output.lower()
            and not session.is_running
            and session.process is None
        )
        details.update(
            {
                "success": success,
                "process_id": process_id,
                "result": _result_summary(result),
                "session_running_after_timeout": session.is_running,
            }
        )
        return success, details
    finally:
        details["stop"] = _result_summary(session.stop())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado-path", required=True)
    parser.add_argument("--output", default="vivado-real-e2e.json")
    parser.add_argument("--work-root")
    parser.add_argument("--part", default="xc7k325tffg900-2")
    args = parser.parse_args()

    work_root = Path(
        args.work_root
        or tempfile.mkdtemp(prefix="vivado-mcp-real-e2e-", dir=os.environ.get("RUNNER_TEMP"))
    )
    work_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "success": False,
        "vivado_path": args.vivado_path,
        "part": args.part,
        "work_root": str(work_root),
    }

    try:
        main_ok, main_section = _run_transport_and_synthesis(
            args.vivado_path,
            work_root,
            args.part,
        )
        timeout_ok, timeout_section = _run_timeout_cleanup(args.vivado_path)
        report["transport_and_synthesis"] = main_section
        report["timeout_cleanup"] = timeout_section
        report["success"] = main_ok and timeout_ok
    except Exception as exc:  # noqa: BLE001
        report["unexpected_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        report["success"] = False
    finally:
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report.get("success"):
            shutil.rmtree(work_root, ignore_errors=True)

    return 0 if report.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
