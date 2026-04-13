#!/usr/bin/env python3
"""Unified USB utility for formatting drives and flashing ISO images on Linux."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QStyleFactory,
)


APP_VERSION = "0.2.0"
LSBLK_COLUMNS = "NAME,PATH,TYPE,SIZE,MODEL,TRAN,HOTPLUG,RM,MOUNTPOINTS"
DD_PROGRESS_RE = re.compile(r"^\s*(\d+)\s+bytes")
APP_STYLESHEET = """
QWidget {
    background: #f6f7f8;
    color: #202223;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 14px;
}
QTabWidget::pane {
    border: 1px solid #cfd4dc;
    border-radius: 8px;
    background: #ffffff;
    margin-top: 6px;
}
QTabBar::tab {
    background: #e9edf2;
    border: 1px solid #cfd4dc;
    border-bottom: none;
    padding: 8px 14px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #1c4f80;
}
QListWidget, QTextEdit {
    background: #ffffff;
    border: 1px solid #cfd4dc;
    border-radius: 8px;
    padding: 8px;
}
QListWidget::item {
    padding: 10px;
    margin: 2px 0;
    border-radius: 6px;
}
QListWidget::item:selected {
    background: #dbeafe;
    color: #202223;
}
QPushButton {
    background: #eef1f5;
    color: #202223;
    border: 1px solid #c7cfd8;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 500;
}
QPushButton:hover {
    background: #e4e9ef;
}
QPushButton:pressed {
    background: #dbe2ea;
}
QPushButton:disabled {
    background: #f3f4f6;
    color: #95a0ad;
    border: 1px solid #dde2e8;
}
QPushButton[primary="true"] {
    background: #1f6feb;
    color: white;
    border: 1px solid #1a61ce;
}
QPushButton[primary="true"]:hover {
    background: #1a61ce;
}
QPushButton[danger="true"] {
    background: #fff5f5;
    color: #b42318;
    border: 1px solid #f0c7c2;
}
QPushButton[danger="true"]:hover {
    background: #fdecec;
}
QLabel[card="true"] {
    background: #ffffff;
    border: 1px solid #cfd4dc;
    border-radius: 8px;
    padding: 14px;
}
QLabel[muted="true"] {
    color: #667085;
}
QLabel[status="ready"] {
    background: #ecfdf3;
    color: #067647;
    border: 1px solid #abefc6;
    border-radius: 999px;
    padding: 4px 10px;
    font-weight: 600;
}
QLabel[status="busy"] {
    background: #eff8ff;
    color: #175cd3;
    border: 1px solid #b2ddff;
    border-radius: 999px;
    padding: 4px 10px;
    font-weight: 600;
}
QLabel[status="warn"] {
    background: #fffaeb;
    color: #b54708;
    border: 1px solid #fedf89;
    border-radius: 999px;
    padding: 4px 10px;
    font-weight: 600;
}
QProgressBar {
    background: #ffffff;
    border: 1px solid #cfd4dc;
    border-radius: 6px;
    text-align: center;
    min-height: 18px;
}
QProgressBar::chunk {
    background: #1f6feb;
    border-radius: 5px;
}
"""


def load_block_devices() -> list[dict]:
    result = subprocess.run(
        ["lsblk", "-J", "-o", LSBLK_COLUMNS],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    return payload.get("blockdevices", [])


def iter_usb_disks() -> list[dict]:
    devices = []
    for device in load_block_devices():
        if device.get("type") != "disk":
            continue
        if device.get("tran") == "usb" or device.get("hotplug") or device.get("rm"):
            devices.append(device)
    return devices


def mounted_partitions(device: dict) -> list[str]:
    items = []
    for child in device.get("children", []) or []:
        for mountpoint in child.get("mountpoints") or []:
            if mountpoint:
                items.append(child["path"])
                break
    return items


def format_device(device: dict) -> str:
    model = (device.get("model") or "-").strip() or "-"
    flag_text = device_flags_text(device)
    return f"{model}  |  {device['size']}\n{device['path']}  |  {flag_text}"


def device_flags_text(device: dict) -> str:
    tran = device.get("tran") or "-"
    flags = []
    if device.get("rm"):
        flags.append("removable")
    if device.get("hotplug"):
        flags.append("hotplug")
    if tran == "usb":
        flags.append("usb")
    return ", ".join(flags) if flags else "fixed"


def device_summary_html(device: dict | None) -> str:
    if device is None:
        return (
            "<b>No drive selected</b><br>"
            "<span style='color:#5d6b7a'>Select a removable drive to see details here.</span>"
        )

    model = (device.get("model") or "-").strip() or "-"
    transport = device.get("tran") or "-"
    mounted = mounted_partitions(device)
    mounted_text = ", ".join(mounted) if mounted else "none"
    return (
        f"<b>{model}</b><br>"
        f"Path: <code>{device['path']}</code><br>"
        f"Size: {device['size']}<br>"
        f"Transport: {transport}<br>"
        f"Flags: {device_flags_text(device)}<br>"
        f"Mounted partitions: {mounted_text}"
    )


def extract_dd_progress_bytes(line: str) -> int | None:
    match = DD_PROGRESS_RE.match(line.strip())
    if not match:
        return None
    return int(match.group(1))


def run_root_command(command: list[str]) -> int:
    process = subprocess.Popen(command)
    return process.wait()


def find_device(device_path: str) -> dict | None:
    devices = {device["path"]: device for device in iter_usb_disks()}
    return devices.get(device_path)


def worker_flash(iso_path: str, device_path: str) -> int:
    if os.geteuid() != 0:
        print("This worker must run as root.", file=sys.stderr)
        return 1

    iso_file = Path(iso_path)
    if not iso_file.is_file():
        print(f"ISO file not found: {iso_file}", file=sys.stderr)
        return 1

    device = find_device(device_path)
    if not device:
        print(f"Target device not found or not removable: {device_path}", file=sys.stderr)
        return 1

    partitions = mounted_partitions(device)
    for partition in partitions:
        print(f"Unmounting {partition} ...", flush=True)
        rc = run_root_command(["umount", partition])
        if rc != 0:
            return rc

    print("Writing ISO. This may take several minutes ...", flush=True)
    dd = subprocess.Popen(
        [
            "dd",
            f"if={iso_file}",
            f"of={device_path}",
            "bs=4M",
            "status=progress",
            "oflag=sync",
            "conv=fsync",
        ],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert dd.stdout is not None
    for line in dd.stdout:
        print(line, end="", flush=True)

    rc = dd.wait()
    if rc != 0:
        return rc

    print("Syncing disk ...", flush=True)
    rc = run_root_command(["sync"])
    if rc != 0:
        return rc

    print("Flash complete.", flush=True)
    return 0


def worker_format(device_path: str, filesystem: str) -> int:
    if os.geteuid() != 0:
        print("This worker must run as root.", file=sys.stderr)
        return 1

    supported_filesystems = {
        "exfat": ["mkfs.exfat"],
        "fat32": ["mkfs.vfat", "-F", "32"],
        "ntfs": ["mkfs.ntfs", "-f"],
        "ext4": ["mkfs.ext4", "-F"],
    }
    command = supported_filesystems.get(filesystem)
    if command is None:
        print(f"Unsupported filesystem: {filesystem}", file=sys.stderr)
        return 1

    if shutil.which(command[0]) is None:
        print(f"Missing formatter command: {command[0]}", file=sys.stderr)
        return 1

    device = find_device(device_path)
    if not device:
        print(f"Target device not found or not removable: {device_path}", file=sys.stderr)
        return 1

    partitions = mounted_partitions(device)
    for partition in partitions:
        print(f"Unmounting {partition} ...", flush=True)
        rc = run_root_command(["umount", partition])
        if rc != 0:
            return rc

    print("Removing existing signatures ...", flush=True)
    rc = run_root_command(["wipefs", "-a", device_path])
    if rc != 0:
        return rc

    print(f"Creating {filesystem} filesystem on {device_path} ...", flush=True)
    rc = run_root_command(command + [device_path])
    if rc != 0:
        return rc

    print("Syncing disk ...", flush=True)
    rc = run_root_command(["sync"])
    if rc != 0:
        return rc

    print("Format complete.", flush=True)
    return 0


class UsbUtilityWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.iso_path: str = ""
        self.devices: list[dict] = []
        self.process: QProcess | None = None
        self.progress_total_bytes: int | None = None
        self.progress_mode = "idle"

        self.setWindowTitle(f"USB Formatter and ISO Flasher {APP_VERSION}")
        self.resize(920, 720)
        self.setStyleSheet(APP_STYLESHEET)

        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        title = QLabel("USB Formatter and ISO Flasher")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #202223;")
        layout.addWidget(title)

        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setProperty("muted", True)
        layout.addWidget(version_label)

        help_text = QLabel(
            "Select a target USB drive for formatting or ISO writing. All operations erase data on the selected drive."
        )
        help_text.setWordWrap(True)
        help_text.setProperty("muted", True)
        layout.addWidget(help_text)

        disk_row = QHBoxLayout()
        disk_label = QLabel("USB Drives")
        disk_row.addWidget(disk_label)

        disk_row.addStretch(1)

        self.status_badge = QLabel("Ready")
        self.status_badge.setProperty("status", "ready")
        disk_row.addWidget(self.status_badge)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setProperty("primary", True)
        self.refresh_btn.clicked.connect(self.load_devices)
        disk_row.addWidget(self.refresh_btn)
        layout.addLayout(disk_row)

        self.disk_list = QListWidget()
        self.disk_list.currentItemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.disk_list)

        self.selection_summary = QLabel()
        self.selection_summary.setProperty("card", True)
        self.selection_summary.setWordWrap(True)
        self.selection_summary.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.selection_summary)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_format_tab(), "Format USB")
        self.tabs.addTab(self.build_flash_tab(), "Flash ISO")
        layout.addWidget(self.tabs)

        progress_label = QLabel("Progress")
        layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        self.progress_detail = QLabel("Idle")
        self.progress_detail.setProperty("muted", True)
        layout.addWidget(self.progress_detail)

        log_label = QLabel("Log")
        layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output, 1)

        self.setLayout(layout)
        self.load_devices()
        self.update_status("ready", "Ready")
        self.update_selection_summary()

    def build_format_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        format_help = QLabel(
            "Create a new filesystem directly on the selected device. Supported: exFAT, FAT32, NTFS, and ext4."
        )
        format_help.setWordWrap(True)
        format_help.setProperty("muted", True)
        layout.addWidget(format_help)

        fs_row = QHBoxLayout()
        self.fs_buttons: dict[str, QPushButton] = {}
        for filesystem in ("exfat", "fat32", "ntfs", "ext4"):
            button = QPushButton(f"Format as {filesystem.upper()}")
            button.setProperty("danger", True)
            button.clicked.connect(
                lambda _checked=False, fs=filesystem: self.start_format(fs)
            )
            self.fs_buttons[filesystem] = button
            fs_row.addWidget(button)
        layout.addLayout(fs_row)

        tab.setLayout(layout)
        return tab

    def build_flash_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        flash_help = QLabel(
            "Choose an ISO image and write it to the entire USB device with dd."
        )
        flash_help.setWordWrap(True)
        flash_help.setProperty("muted", True)
        layout.addWidget(flash_help)

        iso_row = QHBoxLayout()
        self.iso_label = QLabel("ISO: No file selected")
        self.iso_label.setProperty("card", True)
        self.iso_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        iso_row.addWidget(self.iso_label, 1)

        self.browse_btn = QPushButton("Choose ISO")
        self.browse_btn.setProperty("primary", True)
        self.browse_btn.clicked.connect(self.choose_iso)
        iso_row.addWidget(self.browse_btn)
        layout.addLayout(iso_row)

        self.flash_btn = QPushButton("Write ISO to USB")
        self.flash_btn.setProperty("danger", True)
        self.flash_btn.clicked.connect(self.start_flash)
        layout.addWidget(self.flash_btn)

        tab.setLayout(layout)
        return tab

    def append_log(self, text: str) -> None:
        self.log_output.moveCursor(self.log_output.textCursor().MoveOperation.End)
        self.log_output.insertPlainText(text)
        self.log_output.moveCursor(self.log_output.textCursor().MoveOperation.End)

    def choose_iso(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose ISO File",
            str(Path.home()),
            "ISO Files (*.iso);;All Files (*)",
        )
        if filename:
            self.iso_path = filename
            size_text = self.human_size(Path(filename).stat().st_size) if Path(filename).is_file() else "unknown size"
            self.iso_label.setText(f"ISO: {filename}\nSize: {size_text}")
            self.update_action_state()

    def update_status(self, kind: str, text: str) -> None:
        self.status_badge.setProperty("status", kind)
        self.status_badge.setText(text)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def update_selection_summary(self) -> None:
        self.selection_summary.setText(device_summary_html(self.selected_device()))

    def update_progress(self, value: int | None, detail: str) -> None:
        if value is None:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(max(0, min(100, value)))
        self.progress_detail.setText(detail)

    def reset_progress(self) -> None:
        self.progress_total_bytes = None
        self.progress_mode = "idle"
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_detail.setText("Idle")

    def human_size(self, size: int) -> str:
        value = float(size)
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{size} B"

    def update_action_state(self) -> None:
        device_selected = self.selected_device() is not None
        self.flash_btn.setEnabled(bool(self.iso_path) and device_selected and self.process is None)
        for button in self.fs_buttons.values():
            button.setEnabled(device_selected and self.process is None)

    def on_selection_changed(self) -> None:
        self.update_selection_summary()
        self.update_action_state()

    def load_devices(self) -> None:
        self.disk_list.clear()
        try:
            self.devices = iter_usb_disks()
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            self.devices = []
            self.disk_list.addItem("Failed to query block devices")
            self.append_log(f"Device scan failed: {exc}\n")
            self.update_status("warn", "Device scan failed")
            self.update_selection_summary()
            self.update_action_state()
            return

        if not self.devices:
            self.disk_list.addItem("No USB/removable drives detected")
            self.update_status("warn", "No drive detected")
            self.update_selection_summary()
            self.update_action_state()
            return

        for device in self.devices:
            item = QListWidgetItem(format_device(device))
            item.setData(Qt.ItemDataRole.UserRole, device["path"])
            self.disk_list.addItem(item)
        self.disk_list.setCurrentRow(0)
        self.update_status("ready", f"{len(self.devices)} drive(s) available")
        self.update_selection_summary()
        self.update_action_state()

    def selected_device(self) -> dict | None:
        item = self.disk_list.currentItem()
        if item is None:
            return None
        path = item.data(Qt.ItemDataRole.UserRole)
        for device in self.devices:
            if device["path"] == path:
                return device
        return None

    def set_busy(self, busy: bool) -> None:
        self.refresh_btn.setEnabled(not busy)
        self.disk_list.setEnabled(not busy)
        self.browse_btn.setEnabled(not busy)
        self.update_status("busy" if busy else "ready", "Working..." if busy else "Ready")
        self.update_action_state()
        if busy and self.progress_mode != "flash":
            self.update_progress(None, "Running privileged operation...")
        if not busy and self.progress_mode == "idle":
            self.reset_progress()

    def confirm_device(self, device: dict, action_text: str) -> bool:
        typed, ok = QInputDialog.getText(
            self,
            "Confirm Target",
            f'Type {device["path"]} to confirm {action_text}',
        )
        return ok and typed.strip() == device["path"]

    def start_process(
        self,
        arguments: list[str],
        summary_lines: list[str],
        *,
        progress_mode: str,
        progress_total_bytes: int | None = None,
    ) -> None:
        self.log_output.clear()
        for line in summary_lines:
            self.append_log(f"{line}\n")
        self.append_log("Starting privileged process ...\n")
        self.progress_mode = progress_mode
        self.progress_total_bytes = progress_total_bytes
        if progress_mode == "flash" and progress_total_bytes:
            self.update_progress(0, f"Preparing to write {self.human_size(progress_total_bytes)} ...")
        else:
            self.update_progress(None, "Running privileged operation...")

        self.process = QProcess(self)
        self.process.setProgram("pkexec")
        self.process.setArguments([sys.executable, str(Path(__file__).resolve()), *arguments])
        self.process.readyReadStandardOutput.connect(self.on_ready_output)
        self.process.readyReadStandardError.connect(self.on_ready_error)
        self.process.finished.connect(self.on_finished)
        self.process.start()
        self.set_busy(True)

    def start_flash(self) -> None:
        if not self.iso_path:
            QMessageBox.warning(self, "Missing ISO", "Select an ISO file first.")
            return

        iso_file = Path(self.iso_path)
        if not iso_file.is_file():
            QMessageBox.warning(self, "Missing ISO", "The selected ISO file was not found.")
            return

        device = self.selected_device()
        if device is None:
            QMessageBox.warning(self, "Missing Drive", "Select a target USB drive first.")
            return

        if not self.confirm_device(device, "erasing all data and writing the ISO to this drive"):
            return

        self.start_process(
            ["--worker-flash", self.iso_path, device["path"]],
            [f"ISO: {self.iso_path}", f"Target: {device['path']}"],
            progress_mode="flash",
            progress_total_bytes=iso_file.stat().st_size,
        )

    def start_format(self, filesystem: str) -> None:
        device = self.selected_device()
        if device is None:
            QMessageBox.warning(self, "Missing Drive", "Select a USB drive to format first.")
            return

        if not self.confirm_device(
            device,
            f"erasing all data and formatting as {filesystem.upper()}",
        ):
            return

        self.start_process(
            ["--worker-format", device["path"], filesystem],
            [f"Operation: format {filesystem.upper()}", f"Target: {device['path']}"],
            progress_mode="format",
        )

    def on_ready_output(self) -> None:
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
        self.append_log(data)
        if self.progress_mode == "flash" and self.progress_total_bytes:
            for line in data.splitlines():
                copied = extract_dd_progress_bytes(line)
                if copied is None:
                    continue
                percent = int((copied / self.progress_total_bytes) * 100)
                detail = f"Wrote {self.human_size(copied)} of {self.human_size(self.progress_total_bytes)}"
                self.update_progress(percent, detail)

    def on_ready_error(self) -> None:
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardError()).decode(errors="replace")
        self.append_log(data)

    def on_finished(self, exit_code: int, _exit_status) -> None:
        self.process = None
        self.set_busy(False)
        self.load_devices()
        if exit_code == 0:
            self.update_status("ready", "Operation complete")
            self.update_progress(100, "Operation complete")
            self.progress_mode = "idle"
            QMessageBox.information(self, "Done", "Operation complete")
            return
        self.update_status("warn", "Operation failed")
        self.update_progress(0, "Operation failed")
        self.progress_mode = "idle"
        QMessageBox.warning(
            self,
            "Failed",
            "Operation failed or was cancelled. Check the log below for details.",
        )


def run_gui() -> int:
    if shutil.which("pkexec") is None:
        print("Missing pkexec. Install polkit to use the GUI app.", file=sys.stderr)
        return 1

    app = QApplication(sys.argv)
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))
    window = UsbUtilityWindow()
    window.show()
    return app.exec()


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker-flash":
        return worker_flash(sys.argv[2], sys.argv[3])
    if len(sys.argv) == 4 and sys.argv[1] == "--worker-format":
        return worker_format(sys.argv[2], sys.argv[3])
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
