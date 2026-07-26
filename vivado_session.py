"""Cross-platform persistent Vivado Tcl session manager.

This module is a drop-in replacement for the original pexpect-based session
manager in ``coreyhahn/vivado_mcp``.  It uses only the Python standard library
for process management, works on Windows and Linux, and frames every command
with unique UUID sentinels so command completion does not depend on the
interactive ``Vivado%`` prompt.
"""

from __future__ import annotations

import base64
import codecs
import glob
import locale
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from typing_extensions import Self


@dataclass
class CommandResult:
    """Result from executing one Vivado Tcl command."""

    command: str
    output: str
    return_value: str
    success: bool
    elapsed_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ErrorClassification:
    """Classification of messages printed by Vivado."""

    is_tcl_error: bool = False
    is_vivado_error: bool = False
    is_report_content: bool = False
    error_messages: list[str] = field(default_factory=list)

    @property
    def is_actual_failure(self) -> bool:
        return self.is_tcl_error or self.is_vivado_error


def classify_output_errors(output: str, command: str = "") -> ErrorClassification:
    """Separate real Tcl/Vivado errors from words such as ``Timing ERROR: 0``."""

    del command  # Kept for compatibility with the original public function.
    classification = ErrorClassification()
    lines = output.strip().splitlines()

    tcl_error_patterns = (
        r"^invalid command name",
        r"^wrong # args:",
        r'^can\'t read ".*": no such variable',
        r"^expected .* but got",
        r"^couldn\'t open",
        r"^no files matched",
    )
    for line in lines[:8]:
        stripped = line.strip()
        for pattern in tcl_error_patterns:
            if re.match(pattern, stripped, re.IGNORECASE):
                classification.is_tcl_error = True
                classification.error_messages.append(stripped)

    for line in lines:
        stripped = line.strip()
        if re.match(r"^ERROR:\s*\[", stripped):
            classification.is_vivado_error = True
            classification.error_messages.append(stripped)

    report_indicators = (
        "WNS(ns)",
        "TNS(ns)",
        "WHS(ns)",
        "+---------",
        "|------",
        "| Site Type",
        "| Resource",
        "Utilization",
        "Design Timing Summary",
        "Clock Summary",
    )
    classification.is_report_content = any(
        indicator in output for indicator in report_indicators
    )
    return classification


def _version_key(path: str) -> tuple[int, ...]:
    """Return a sortable Vivado version tuple extracted from a path."""

    matches = re.findall(r"(?<!\d)(20\d{2})\.(\d+)(?!\d)", path)
    if not matches:
        return (0,)
    year, minor = matches[-1]
    return (int(year), int(minor))


def _candidate_installations() -> list[str]:
    """Find likely Vivado launchers, newest version first."""

    patterns: list[str] = []
    if os.name == "nt":
        drives = {os.environ.get("SystemDrive", "C:")}
        for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            if os.path.exists(f"{drive}:\\"):
                drives.add(f"{drive}:")
        for drive in drives:
            patterns.extend(
                [
                    rf"{drive}\\Xilinx\\Vivado\\*\\bin\\vivado.bat",
                    rf"{drive}\\AMD\\Vivado\\*\\bin\\vivado.bat",
                    rf"{drive}\\Program Files\\AMD\\Vivado\\*\\bin\\vivado.bat",
                    rf"{drive}\\Program Files\\Xilinx\\Vivado\\*\\bin\\vivado.bat",
                ]
            )
    else:
        patterns.extend(
            [
                "/opt/Xilinx/Vivado/*/bin/vivado",
                "/tools/Xilinx/Vivado/*/bin/vivado",
                "/tools/AMD/Vivado/*/bin/vivado",
                "/opt/AMD/Vivado/*/bin/vivado",
            ]
        )

    candidates: list[str] = []
    for pattern in patterns:
        candidates.extend(glob.glob(pattern))
    return sorted(set(candidates), key=_version_key, reverse=True)


def resolve_vivado_path(vivado_path: str | os.PathLike[str] | None) -> str:
    """Resolve an explicit path, environment variable, PATH entry, or installation."""

    requested = str(vivado_path or "").strip()
    if not requested or requested.lower() == "vivado":
        requested = os.environ.get("VIVADO_PATH", "").strip()

    if requested and requested.lower() != "vivado":
        expanded = Path(os.path.expandvars(os.path.expanduser(requested)))
        if expanded.is_dir():
            directory_candidates = (
                expanded / ("vivado.bat" if os.name == "nt" else "vivado"),
                expanded / "bin" / ("vivado.bat" if os.name == "nt" else "vivado"),
            )
            for candidate in directory_candidates:
                if candidate.is_file():
                    return str(candidate.resolve())
        if expanded.is_file():
            return str(expanded.resolve())
        raise FileNotFoundError(f"Vivado launcher not found: {expanded}")

    path_names = ["vivado"]
    if os.name == "nt":
        path_names = ["vivado.bat", "vivado.cmd", "vivado.exe", "vivado"]
    for name in path_names:
        found = shutil.which(name)
        if found:
            return str(Path(found).resolve())

    installations = _candidate_installations()
    if installations:
        return str(Path(installations[0]).resolve())

    hint = (
        "Set VIVADO_PATH to ...\\Vivado\\<version>\\bin\\vivado.bat"
        if os.name == "nt"
        else "Set VIVADO_PATH to .../Vivado/<version>/bin/vivado"
    )
    raise FileNotFoundError(f"Vivado was not found. {hint}")


def build_launch_command(
    executable: str,
    *,
    platform_name: str | None = None,
    comspec: str | None = None,
) -> str | list[str]:
    """Build the platform-specific subprocess command.

    ``platform_name`` exists primarily so CI can test Windows command building
    while running on Linux. Windows batch launchers require a single command-line
    string so Python does not escape the nested quotes as literal backslashes.
    """

    platform_name = platform_name or os.name
    args = [executable, "-mode", "tcl", "-nojournal", "-nolog"]
    suffix = Path(executable).suffix.lower()
    if platform_name == "nt" and suffix in {".bat", ".cmd"}:
        shell = comspec or os.environ.get("COMSPEC", "cmd.exe")
        shell_command = subprocess.list2cmdline([shell])
        batch_command = subprocess.list2cmdline(args)
        return f'{shell_command} /d /s /c "{batch_command}"'
    return args


class VivadoSession:
    """Maintain one persistent, cross-platform Vivado Tcl process."""

    def __init__(self, vivado_path: str = "vivado", timeout: float = 300.0):
        self.vivado_path = vivado_path
        self.timeout = timeout
        self.process: subprocess.Popen[bytes] | None = None
        # ``child`` is retained as a compatibility alias for callers that only
        # check whether a process object exists.
        self.child: subprocess.Popen[bytes] | None = None
        self.is_running = False
        self.current_project: str | None = None

        self._lock = threading.Lock()
        self._condition = threading.Condition()
        self._read_buffer = ""
        self._reader_thread: threading.Thread | None = None
        self._reader_error: str | None = None
        self.output_encoding = os.environ.get("VIVADO_MCP_OUTPUT_ENCODING") or (
            locale.getpreferredencoding(False) if os.name == "nt" else "utf-8"
        )
        self._decoder = codecs.getincrementaldecoder(self.output_encoding)(errors="replace")

        self.stats = {
            "session_start": None,
            "commands_run": 0,
            "total_command_time_ms": 0,
            "errors": 0,
            "command_history": [],
            "platform": os.name,
            "resolved_vivado_path": None,
            "output_encoding": self.output_encoding,
        }

    def _record_result(self, result: CommandResult) -> CommandResult:
        self.stats["commands_run"] += 1
        self.stats["total_command_time_ms"] += result.elapsed_ms
        if not result.success:
            self.stats["errors"] += 1
        self.stats["command_history"].append(
            {
                "command": result.command,
                "success": result.success,
                "elapsed_ms": result.elapsed_ms,
                "timestamp": result.timestamp,
            }
        )
        self.stats["command_history"] = self.stats["command_history"][-100:]
        return result

    def _reader_loop(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        fd = self.process.stdout.fileno()
        try:
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    tail = self._decoder.decode(b"", final=True)
                    if tail:
                        with self._condition:
                            self._read_buffer += tail
                            self._condition.notify_all()
                    break
                text = self._decoder.decode(chunk)
                with self._condition:
                    self._read_buffer += text
                    self._condition.notify_all()
        except Exception as exc:  # pragma: no cover - OS pipe failures are rare.
            with self._condition:
                self._reader_error = str(exc)
                self._condition.notify_all()
        finally:
            with self._condition:
                self._condition.notify_all()

    def _write(self, text: str) -> None:
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("Vivado process stdin is unavailable")
        self.process.stdin.write(text.encode("utf-8"))
        self.process.stdin.flush()

    def _wait_for_marker(self, marker: str, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        with self._condition:
            while True:
                index = self._read_buffer.find(marker)
                if index >= 0:
                    captured = self._read_buffer[:index]
                    self._read_buffer = self._read_buffer[index + len(marker) :]
                    return captured

                if self._reader_error:
                    raise RuntimeError(f"Vivado output reader failed: {self._reader_error}")
                if self.process is None or self.process.poll() is not None:
                    exit_code = None if self.process is None else self.process.poll()
                    tail = self._read_buffer
                    self._read_buffer = ""
                    raise RuntimeError(
                        f"Vivado exited before marker {marker!r} (code={exit_code}). "
                        f"Output tail: {tail[-2000:]}"
                    )

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"Timed out waiting for Vivado marker {marker!r}")
                self._condition.wait(timeout=min(remaining, 0.25))

    @staticmethod
    def _make_wrapper(command: str, token: str) -> tuple[str, dict[str, str]]:
        command_hex = command.encode("utf-8").hex()
        markers = {
            "begin": f"__VIVADO_MCP_BEGIN_{token}__",
            "meta": f"__VIVADO_MCP_META_{token}__",
            "error": f"__VIVADO_MCP_ERROR_{token}__",
            "rc": f"__VIVADO_MCP_RC_{token}__",
            "end": f"__VIVADO_MCP_END_{token}__",
        }
        suffix = token.replace("-", "_")
        cmd_var = f"__mcp_cmd_{suffix}"
        rc_var = f"__mcp_rc_{suffix}"
        result_var = f"__mcp_result_{suffix}"
        opts_var = f"__mcp_opts_{suffix}"

        # The user command is transported as UTF-8 hex, so quotes, braces,
        # semicolons, backslashes, newlines, and Windows paths cannot escape the
        # wrapper.  Base64 metadata is emitted on one line (-maxlen 0).
        script = (
            f"set {cmd_var} [encoding convertfrom utf-8 [binary decode hex {command_hex}]];"
            f'puts "{markers["begin"]}"; flush stdout;'
            f"set {rc_var} [catch {{uplevel #0 [set {cmd_var}]}} {result_var} {opts_var}];"
            f'puts "{markers["meta"]}[binary encode base64 -maxlen 0 '
            f'[encoding convertto utf-8 [set {result_var}]]]";'
            f"if {{[set {rc_var}] != 0 && [dict exists [set {opts_var}] -errorinfo]}} {{"
            f'puts "{markers["error"]}[binary encode base64 -maxlen 0 '
            f'[encoding convertto utf-8 [dict get [set {opts_var}] -errorinfo]]]"}};'
            f'puts "{markers["rc"]}[set {rc_var}]";'
            f'puts "{markers["end"]}"; flush stdout\n'
        )
        return script, markers

    @staticmethod
    def _decode_base64(value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        try:
            return base64.b64decode(value, validate=True).decode(
                "utf-8", errors="replace"
            )
        except (ValueError, base64.binascii.Error):
            return value

    def _execute_locked(self, command: str, timeout: float) -> CommandResult:
        start_time = time.monotonic()
        token = uuid.uuid4().hex
        script, markers = self._make_wrapper(command, token)
        self._write(script)

        # Discard startup banners/prompts before this command's begin marker.
        self._wait_for_marker(markers["begin"], timeout)
        payload = self._wait_for_marker(markers["end"], timeout)

        meta_index = payload.rfind(markers["meta"])
        rc_index = payload.rfind(markers["rc"])
        error_index = payload.rfind(markers["error"])
        if meta_index < 0 or rc_index < 0 or rc_index < meta_index:
            raise RuntimeError(f"Malformed Vivado MCP response: {payload[-4000:]}")

        stdout_text = payload[:meta_index].strip("\r\n")
        metadata_start = meta_index + len(markers["meta"])
        metadata_end = error_index if error_index > meta_index else rc_index
        result_text = self._decode_base64(payload[metadata_start:metadata_end])

        error_info = ""
        if error_index > meta_index:
            error_start = error_index + len(markers["error"])
            error_info = self._decode_base64(payload[error_start:rc_index])

        rc_start = rc_index + len(markers["rc"])
        rc_text = payload[rc_start:].strip().splitlines()[0] if payload[rc_start:].strip() else "1"
        success_by_tcl = rc_text == "0"

        output_parts = [part for part in (stdout_text, result_text) if part]
        if not success_by_tcl and error_info and error_info not in output_parts:
            output_parts.append(error_info)
        output = "\n".join(output_parts).strip()

        classification = classify_output_errors(output, command)
        success = success_by_tcl and not classification.is_actual_failure
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return CommandResult(
            command=command,
            output=output,
            return_value=rc_text,
            success=success,
            elapsed_ms=elapsed_ms,
        )

    def start(self) -> CommandResult:
        if self.is_running and self.process is not None and self.process.poll() is None:
            return CommandResult(
                command="start",
                output="Session already running",
                return_value="0",
                success=True,
                elapsed_ms=0,
            )

        start_time = time.monotonic()
        try:
            resolved = resolve_vivado_path(self.vivado_path)
            launch_command = build_launch_command(resolved)
            creationflags = 0
            popen_kwargs: dict[str, object] = {}
            if os.name == "nt":
                creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                if os.environ.get("VIVADO_MCP_SHOW_CONSOLE", "0") != "1":
                    creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
                popen_kwargs["creationflags"] = creationflags
            else:
                popen_kwargs["start_new_session"] = True

            self._read_buffer = ""
            self._reader_error = None
            self._decoder = codecs.getincrementaldecoder(self.output_encoding)(errors="replace")
            self.process = subprocess.Popen(
                launch_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                **popen_kwargs,
            )
            self.child = self.process
            self._reader_thread = threading.Thread(
                target=self._reader_loop,
                name="vivado-mcp-output-reader",
                daemon=True,
            )
            self._reader_thread.start()

            # Do not depend on a localized startup banner or the Vivado prompt.
            # The command can be queued while Vivado initializes and confirms
            # readiness through the same framed protocol used later.
            self.is_running = True
            with self._lock:
                handshake = self._execute_locked(
                    "set __vivado_mcp_handshake READY", timeout=120.0
                )
            if not handshake.success or "READY" not in handshake.output:
                raise RuntimeError(f"Vivado handshake failed: {handshake.output}")

            self.stats["session_start"] = datetime.now().isoformat()
            self.stats["platform"] = os.name
            self.stats["resolved_vivado_path"] = resolved
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return CommandResult(
                command="start",
                output=f"Vivado session started successfully ({resolved})",
                return_value="0",
                success=True,
                elapsed_ms=elapsed_ms,
            )
        except Exception as exc:
            self._force_stop()
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return CommandResult(
                command="start",
                output=f"Failed to start Vivado: {exc}",
                return_value="1",
                success=False,
                elapsed_ms=elapsed_ms,
            )

    def run_tcl(self, command: str, timeout_override: float | None = None) -> CommandResult:
        if not self.is_running or self.process is None or self.process.poll() is not None:
            return CommandResult(
                command=command,
                output="Vivado session not running. Call start() first.",
                return_value="1",
                success=False,
                elapsed_ms=0,
            )

        effective_timeout = (
            float(timeout_override) if timeout_override is not None else self.timeout
        )
        with self._lock:
            try:
                return self._record_result(
                    self._execute_locked(command, timeout=effective_timeout)
                )
            except TimeoutError:
                elapsed_ms = effective_timeout * 1000
                self._force_stop_unlocked()
                return self._record_result(
                    CommandResult(
                        command=command,
                        output=(
                            f"Command timed out after {effective_timeout:g}s. "
                            "The Vivado process was stopped to avoid a desynchronized session."
                        ),
                        return_value="1",
                        success=False,
                        elapsed_ms=elapsed_ms,
                    )
                )
            except Exception as exc:
                self._force_stop_unlocked()
                elapsed_ms = 0.0
                return self._record_result(
                    CommandResult(
                        command=command,
                        output=f"Error executing command: {exc}",
                        return_value="1",
                        success=False,
                        elapsed_ms=elapsed_ms,
                    )
                )

    def _force_stop_unlocked(self) -> None:
        process = self.process
        if process is None:
            self.is_running = False
            self.child = None
            return
        try:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                else:
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        process.kill()
        finally:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            self.process = None
            self.child = None
            self.is_running = False
            self.current_project = None

    def _force_stop(self) -> None:
        with self._lock:
            self._force_stop_unlocked()

    def stop(self) -> CommandResult:
        if self.process is None or self.process.poll() is not None:
            self.process = None
            self.child = None
            self.is_running = False
            self.current_project = None
            return CommandResult(
                command="stop",
                output="Session not running",
                return_value="0",
                success=True,
                elapsed_ms=0,
            )

        start_time = time.monotonic()
        with self._lock:
            try:
                self._write("exit\n")
                self.process.wait(timeout=30)
            except Exception:
                self._force_stop_unlocked()
            else:
                self.process = None
                self.child = None
                self.is_running = False
                self.current_project = None
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return CommandResult(
            command="stop",
            output="Vivado session stopped",
            return_value="0",
            success=True,
            elapsed_ms=elapsed_ms,
        )

    def get_stats(self) -> dict:
        stats = self.stats.copy()
        stats["command_history"] = list(self.stats["command_history"])
        stats["is_running"] = bool(
            self.is_running and self.process is not None and self.process.poll() is None
        )
        stats["current_project"] = self.current_project
        if self.stats["commands_run"]:
            stats["avg_command_time_ms"] = (
                self.stats["total_command_time_ms"] / self.stats["commands_run"]
            )
        else:
            stats["avg_command_time_ms"] = 0.0
        return stats

    def is_healthy(self) -> bool:
        if not self.is_running or self.process is None or self.process.poll() is not None:
            return False
        result = self.run_tcl("set __vivado_mcp_health HEALTH_OK", timeout_override=5)
        return result.success and "HEALTH_OK" in result.output

    def ensure_healthy(self) -> CommandResult:
        if self.is_healthy():
            return CommandResult(
                command="health_check",
                output="Session healthy",
                return_value="0",
                success=True,
                elapsed_ms=0,
            )
        self.stop()
        return self.start()

    def __enter__(self) -> Self:
        result = self.start()
        if not result.success:
            raise RuntimeError(result.output)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


_session: VivadoSession | None = None


def get_session() -> VivadoSession:
    global _session
    if _session is None:
        _session = VivadoSession()
    return _session


def reset_session() -> None:
    global _session
    if _session is not None and _session.is_running:
        _session.stop()
    _session = None
