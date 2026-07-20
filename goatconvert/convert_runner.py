"""Runs a conversion on a background QThread so the UI never freezes,
streaming diagnostic output back to the main thread for the log pane."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from . import registry


class ConversionWorker(QThread):
    log = Signal(str)
    finished_ok = Signal(str)  # emits output_path on success
    finished_error = Signal(str)  # emits error message on failure

    def __init__(self, input_path: str, output_path: str, detected_format: str, target_format: str):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.detected_format = detected_format
        self.target_format = target_format

    def run(self):
        backend = registry.backend_for_conversion(self.detected_format, self.target_format)
        if backend is None:
            msg = f"No available backend can convert '{self.detected_format}' -> '{self.target_format}'"
            self.log.emit(msg)
            self.finished_error.emit(msg)
            return

        self.log.emit(f"Using backend: {backend.__name__}")
        self.log.emit(f"Converting {self.input_path} -> {self.output_path}")

        try:
            result = backend.convert(self.input_path, self.output_path, self.target_format)
        except Exception as exc:  # noqa: BLE001 - any backend crash must reach the log pane
            msg = f"Conversion crashed: {exc}"
            self.log.emit(msg)
            self.finished_error.emit(msg)
            return

        if result.stdout:
            self.log.emit(result.stdout)
        if result.stderr:
            self.log.emit(result.stderr)

        if result.returncode == 0:
            self.log.emit("Conversion succeeded.")
            self.finished_ok.emit(self.output_path)
        else:
            msg = f"Conversion failed (exit code {result.returncode})"
            self.log.emit(msg)
            self.finished_error.emit(msg)
