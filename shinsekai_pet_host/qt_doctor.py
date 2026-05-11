from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class QtDoctorResult:
    ok: bool
    lines: list[str]


def run_qt_doctor() -> QtDoctorResult:
    lines: list[str] = []
    try:
        import PySide6
        from PySide6.QtCore import QLibraryInfo, QPluginLoader
    except ImportError as exc:
        return QtDoctorResult(
            False,
            [
                f"PySide6 import failed: {exc}",
                "Run: uv run --extra desktop python -m shinsekai_pet_host.cli doctor",
            ],
        )

    plugins_path = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))
    cocoa_path = plugins_path / "platforms" / "libqcocoa.dylib"
    lines.append(f"PySide6: {Path(PySide6.__file__).resolve()}")
    lines.append(f"Qt plugins: {plugins_path}")
    lines.append(f"cocoa plugin exists: {cocoa_path.is_file()}")
    if not cocoa_path.is_file():
        return QtDoctorResult(False, lines + [_repair_hint()])

    loader = QPluginLoader(str(cocoa_path))
    loaded = loader.load()
    lines.append(f"cocoa plugin loadable: {loaded}")
    if not loaded:
        lines.append(f"loader error: {loader.errorString()}")
        return QtDoctorResult(False, lines + [_repair_hint()])

    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "from PySide6.QtWidgets import QApplication; app=QApplication([]); print('QApplication ok')",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    lines.append(f"QApplication probe returncode: {probe.returncode}")
    if probe.stdout.strip():
        lines.append(probe.stdout.strip())
    if probe.returncode != 0:
        if probe.stderr.strip():
            lines.append(probe.stderr.strip())
        return QtDoctorResult(False, lines + [_repair_hint()])
    return QtDoctorResult(True, lines)


def _repair_hint() -> str:
    return (
        "Repair: uv sync --extra desktop --reinstall-package PySide6 "
        "--reinstall-package PySide6-Addons --reinstall-package PySide6-Essentials "
        "--reinstall-package shiboken6"
    )

