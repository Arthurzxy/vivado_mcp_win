"""Command-line diagnostics for validating a real Vivado installation."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from typing import Any

from .vivado_session import VivadoSession, resolve_vivado_path


def run_diagnostics(vivado_path: str = "vivado", timeout: float = 300.0) -> dict[str, Any]:
    """Resolve Vivado, start a session, run smoke commands, and stop cleanly."""

    report: dict[str, Any] = {
        "success": False,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "requested_vivado_path": vivado_path,
        "resolved_vivado_path": None,
        "output_encoding": None,
        "steps": [],
    }
    session: VivadoSession | None = None

    try:
        resolved = resolve_vivado_path(vivado_path)
        report["resolved_vivado_path"] = resolved
        report["steps"].append(
            {"name": "resolve_vivado", "success": True, "output": resolved}
        )

        session = VivadoSession(resolved, timeout=timeout)
        report["output_encoding"] = session.output_encoding
        started = session.start()
        report["steps"].append(
            {
                "name": "start_session",
                "success": started.success,
                "output": started.output,
                "elapsed_ms": round(started.elapsed_ms, 3),
            }
        )
        if not started.success:
            return report

        checks = (
            ("vivado_version", "version -short", None),
            ("tcl_version", "info patchlevel", None),
            ("working_directory", "pwd", None),
            ("tcl_expression", "expr {6 * 7}", "42"),
            (
                "unicode_round_trip",
                "set __mcp_unicode_test {中文路径测试}",
                "中文路径测试",
            ),
        )

        all_commands_ok = True
        for name, command, expected in checks:
            result = session.run_tcl(command, timeout_override=timeout)
            expected_ok = expected is None or expected in result.output
            success = result.success and expected_ok
            all_commands_ok = all_commands_ok and success
            step: dict[str, Any] = {
                "name": name,
                "command": command,
                "success": success,
                "output": result.output,
                "return_value": result.return_value,
                "elapsed_ms": round(result.elapsed_ms, 3),
            }
            if expected is not None:
                step["expected"] = expected
            report["steps"].append(step)

        healthy = session.is_healthy()
        report["steps"].append(
            {"name": "session_health", "success": healthy, "output": str(healthy)}
        )
        report["success"] = all_commands_ok and healthy
        return report
    except (FileNotFoundError, OSError, RuntimeError, TimeoutError, ValueError) as exc:
        report["steps"].append(
            {"name": "unexpected_error", "success": False, "output": str(exc)}
        )
        return report
    finally:
        if session is not None:
            stopped = session.stop()
            report["steps"].append(
                {
                    "name": "stop_session",
                    "success": stopped.success,
                    "output": stopped.output,
                    "elapsed_ms": round(stopped.elapsed_ms, 3),
                }
            )
            if not stopped.success:
                report["success"] = False


def _print_human(report: dict[str, Any]) -> None:
    status = "PASS" if report["success"] else "FAIL"
    print(f"Vivado MCP doctor: {status}")
    print(f"Platform: {report['platform']}")
    print(f"Python: {report['python']}")
    print(f"Vivado: {report.get('resolved_vivado_path') or 'not resolved'}")
    print(f"Output encoding: {report.get('output_encoding') or 'unknown'}")
    print()
    for step in report["steps"]:
        marker = "OK" if step.get("success") else "ERROR"
        print(f"[{marker}] {step['name']}")
        output = str(step.get("output", "")).strip()
        if output:
            print(f"  {output}")


def _configure_output_streams() -> None:
    """Use deterministic UTF-8 output even on legacy Windows code pages."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _configure_output_streams()
    parser = argparse.ArgumentParser(
        description="Verify that Vivado MCP can locate and control a Vivado Tcl session."
    )
    parser.add_argument(
        "--vivado-path",
        default=os.environ.get("VIVADO_PATH", "vivado"),
        help="Vivado launcher, bin directory, or version directory.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="Timeout in seconds for startup and each smoke command.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    report = run_diagnostics(args.vivado_path, args.timeout)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
