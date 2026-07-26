#!/usr/bin/env python3
"""Build-artifact smoke test executed outside the source tree."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def find_wheel(argument: str) -> Path:
    path = Path(argument).resolve()
    if path.is_file() and path.suffix == ".whl":
        return path
    wheels = sorted(path.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected exactly one wheel in {path}, found {len(wheels)}")
    return wheels[0]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/package_smoke.py <wheel-or-dist-directory>")

    wheel = find_wheel(sys.argv[1])
    repository = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="vivado-mcp-package-smoke-") as temporary:
        root = Path(temporary)
        environment = root / "clean environment"
        outside_source = root / "outside source tree"
        outside_source.mkdir()
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)

        if os.name == "nt":
            scripts = environment / "Scripts"
            python = scripts / "python.exe"
            doctor = scripts / "vivado-mcp-doctor.exe"
        else:
            scripts = environment / "bin"
            python = scripts / "python"
            doctor = scripts / "vivado-mcp-doctor"

        subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)],
            check=True,
            cwd=outside_source,
        )
        subprocess.run(
            [str(python), "-c", "import vivado_mcp; print(vivado_mcp.__version__)"],
            check=True,
            cwd=outside_source,
        )

        fake_bin = root / "AMD Tools (Package Smoke)" / "Vivado" / "2025.2" / "bin"
        fake_bin.mkdir(parents=True)
        shutil.copy2(repository / "tests" / "fake_vivado.py", fake_bin / "fake_vivado.py")
        if os.name == "nt":
            launcher = fake_bin / "vivado.bat"
            launcher.write_text(
                '@echo off\r\npython "%~dp0fake_vivado.py" %*\r\n', encoding="utf-8"
            )
        else:
            launcher = fake_bin / "vivado"
            shutil.copy2(repository / "tests" / "fake_vivado.py", launcher)
            launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)

        process_env = os.environ.copy()
        process_env["PATH"] = str(scripts) + os.pathsep + process_env.get("PATH", "")
        completed = subprocess.run(
            [
                str(doctor),
                "--vivado-path",
                str(launcher),
                "--timeout",
                "10",
                "--json",
            ],
            check=False,
            cwd=outside_source,
            env=process_env,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
        if completed.returncode != 0:
            print(completed.stdout)
            print(completed.stderr, file=sys.stderr)
            return completed.returncode

        report = json.loads(completed.stdout)
        if not report.get("success"):
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
