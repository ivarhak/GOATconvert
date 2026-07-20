from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import registry
from ..convert_runner import ConversionWorker
from ..detect import DetectedFile, detect_file
from .icon import ensure_icon


class DropZone(QLabel):
    def __init__(self, on_file_dropped):
        super().__init__("🐐  Drag a file here, or click Choose File below")
        self.on_file_dropped = on_file_dropped
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setStyleSheet(
            "QLabel { border: 2px dashed #999; border-radius: 10px; font-size: 16px; padding: 20px; }"
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.on_file_dropped(path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GOATconvert")
        self.setWindowIcon(QIcon(ensure_icon()))
        self.resize(640, 640)

        self.detected: DetectedFile | None = None
        self.all_targets: list[registry.TargetFormat] = []
        self.worker: ConversionWorker | None = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.drop_zone = DropZone(self.load_file)
        layout.addWidget(self.drop_zone)

        choose_btn = QPushButton("Choose File…")
        choose_btn.clicked.connect(self.choose_file)
        layout.addWidget(choose_btn)

        self.file_label = QLabel("No file selected.")
        layout.addWidget(self.file_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search target formats…")
        self.search_box.textChanged.connect(self.filter_formats)
        self.search_box.setEnabled(False)
        layout.addWidget(self.search_box)

        self.format_list = QListWidget()
        self.format_list.itemSelectionChanged.connect(self.on_format_selected)
        layout.addWidget(self.format_list)

        convert_row = QHBoxLayout()
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self.run_conversion)
        convert_row.addWidget(self.convert_btn)

        self.reveal_btn = QPushButton("Reveal in Finder")
        self.reveal_btn.setEnabled(False)
        self.reveal_btn.clicked.connect(self.reveal_output)
        convert_row.addWidget(self.reveal_btn)
        layout.addLayout(convert_row)

        layout.addWidget(QLabel("Log:"))
        self.log_pane = QPlainTextEdit()
        self.log_pane.setReadOnly(True)
        self.log_pane.setMinimumHeight(160)
        layout.addWidget(self.log_pane)

        self.output_path: str | None = None
        self.selected_target: registry.TargetFormat | None = None

    def log(self, msg: str):
        print(msg)
        self.log_pane.appendPlainText(msg)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a file to convert")
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        if not os.path.isfile(path):
            self.log(f"Not a file: {path}")
            return

        self.detected = detect_file(path)
        self.file_label.setText(f"{os.path.basename(path)}  (detected format: {self.detected.format})")
        self.log(f"Loaded {path} — detected format '{self.detected.format}'")

        self.all_targets = registry.targets_for_file(self.detected.format)
        self.search_box.setEnabled(True)
        self.search_box.clear()
        self.populate_format_list(self.all_targets)

        if not self.all_targets:
            self.log(f"No available backend supports converting '{self.detected.format}'.")

        self.convert_btn.setEnabled(False)
        self.reveal_btn.setEnabled(False)
        self.output_path = None

    def populate_format_list(self, targets: list[registry.TargetFormat]):
        self.format_list.clear()
        for t in targets:
            item = QListWidgetItem(f"{t.category}: {t.format}")
            item.setData(Qt.UserRole, t)
            self.format_list.addItem(item)

    def filter_formats(self, text: str):
        text = text.lower().strip()
        filtered = [t for t in self.all_targets if text in t.format.lower() or text in t.category.lower()]
        self.populate_format_list(filtered)

    def on_format_selected(self):
        items = self.format_list.selectedItems()
        if not items:
            self.selected_target = None
            self.convert_btn.setEnabled(False)
            return
        self.selected_target = items[0].data(Qt.UserRole)
        self.convert_btn.setEnabled(True)

    def run_conversion(self):
        if self.detected is None or self.selected_target is None:
            return

        default_out = os.path.splitext(self.detected.path)[0] + "." + self.selected_target.format
        out_path, _ = QFileDialog.getSaveFileName(self, "Save converted file as", default_out)
        if not out_path:
            return

        self.output_path = out_path
        self.convert_btn.setEnabled(False)
        self.reveal_btn.setEnabled(False)
        self.log(f"Starting conversion: {self.detected.format} -> {self.selected_target.format}")

        self.worker = ConversionWorker(
            input_path=self.detected.path,
            output_path=out_path,
            detected_format=self.detected.format,
            target_format=self.selected_target.format,
        )
        self.worker.log.connect(self.log)
        self.worker.finished_ok.connect(self.on_conversion_ok)
        self.worker.finished_error.connect(self.on_conversion_error)
        self.worker.start()

    def on_conversion_ok(self, output_path: str):
        self.log(f"Done: {output_path}")
        self.convert_btn.setEnabled(True)
        self.reveal_btn.setEnabled(True)

    def on_conversion_error(self, message: str):
        self.convert_btn.setEnabled(True)
        QMessageBox.warning(self, "Conversion failed", message)

    def reveal_output(self):
        if not (self.output_path and os.path.exists(self.output_path)):
            return
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", self.output_path])
        elif sys.platform.startswith("win"):
            subprocess.run(["explorer", f"/select,{self.output_path}"])
        else:
            subprocess.run(["xdg-open", os.path.dirname(self.output_path)])
