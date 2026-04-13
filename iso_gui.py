#!/usr/bin/env python3
"""Unified USB utility for formatting drives and flashing ISO images on Linux."""

from __future__ import annotations

import json
import os
from pathlib import Path
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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


LSBLK_COLUMNS = "NAME,PATH,TYPE,SIZE,MODEL,TRAN,HOTPLUG,RM,MOUNTPOINTS"


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
    tran = device.get("tran") or "-"
    flags = []
    if device.get("rm"):
        flags.append("removable")
    if device.get("hotplug"):
        flags.append("hotplug")
    if tran == "usb":
        flags.append("usb")
    flag_text = ", ".join(flags) if flags else "fixed"
    return f'{device["path"]}  {device["size"]}  {model}  [{flag_text}]'


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

        self.setWindowTitle("USB Formatter and ISO Flasher")
        self.resize(820, 620)

        layout = QVBoxLayout()

        title = QLabel("USB Formatter and ISO Flasher")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        help_text = QLabel(
            "เลือกแฟลชไดรฟ์ปลายทางสำหรับฟอร์แมตหรือแฟลช ISO ทุกการทำงานจะลบข้อมูลบนไดรฟ์ที่เลือก"
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        disk_row = QHBoxLayout()
        disk_label = QLabel("USB Drives")
        disk_row.addWidget(disk_label)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_devices)
        disk_row.addWidget(self.refresh_btn)
        layout.addLayout(disk_row)

        self.disk_list = QListWidget()
        layout.addWidget(self.disk_list)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_format_tab(), "Format USB")
        self.tabs.addTab(self.build_flash_tab(), "Flash ISO")
        layout.addWidget(self.tabs)

        log_label = QLabel("Log")
        layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output, 1)

        self.setLayout(layout)
        self.load_devices()

    def build_format_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        format_help = QLabel(
            "รองรับ exFAT, FAT32, NTFS และ ext4 โดยจะฟอร์แมตลงทั้งอุปกรณ์ที่เลือกโดยตรง"
        )
        format_help.setWordWrap(True)
        layout.addWidget(format_help)

        fs_row = QHBoxLayout()
        self.fs_buttons: dict[str, QPushButton] = {}
        for filesystem in ("exfat", "fat32", "ntfs", "ext4"):
            button = QPushButton(f"Format as {filesystem.upper()}")
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
            "เลือกไฟล์ ISO แล้วแฟลชลงแฟลชไดรฟ์ด้วย dd แบบทั้งดิสก์"
        )
        flash_help.setWordWrap(True)
        layout.addWidget(flash_help)

        iso_row = QHBoxLayout()
        self.iso_label = QLabel("ISO: ยังไม่ได้เลือกไฟล์")
        self.iso_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        iso_row.addWidget(self.iso_label, 1)

        self.browse_btn = QPushButton("Choose ISO")
        self.browse_btn.clicked.connect(self.choose_iso)
        iso_row.addWidget(self.browse_btn)
        layout.addLayout(iso_row)

        self.flash_btn = QPushButton("Flash ISO")
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
            self.iso_label.setText(f"ISO: {filename}")

    def load_devices(self) -> None:
        self.disk_list.clear()
        self.devices = iter_usb_disks()

        if not self.devices:
            self.disk_list.addItem("No USB/removable drives detected")
            return

        for device in self.devices:
            item = QListWidgetItem(format_device(device))
            item.setData(Qt.ItemDataRole.UserRole, device["path"])
            self.disk_list.addItem(item)

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
        self.flash_btn.setEnabled(not busy)
        for button in self.fs_buttons.values():
            button.setEnabled(not busy)

    def confirm_device(self, device: dict, action_text: str) -> bool:
        typed, ok = QInputDialog.getText(
            self,
            "Confirm Target",
            f'พิมพ์ {device["path"]} เพื่อยืนยัน{action_text}',
        )
        return ok and typed.strip() == device["path"]

    def start_process(self, arguments: list[str], summary_lines: list[str]) -> None:
        self.log_output.clear()
        for line in summary_lines:
            self.append_log(f"{line}\n")
        self.append_log("Starting privileged process ...\n")

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
            QMessageBox.warning(self, "Missing ISO", "เลือกไฟล์ ISO ก่อน")
            return

        iso_file = Path(self.iso_path)
        if not iso_file.is_file():
            QMessageBox.warning(self, "Missing ISO", "ไม่พบไฟล์ ISO ที่เลือกไว้")
            return

        device = self.selected_device()
        if device is None:
            QMessageBox.warning(self, "Missing Drive", "เลือกแฟลชไดรฟ์เป้าหมายก่อน")
            return

        if not self.confirm_device(device, "การลบข้อมูลทั้งหมดและแฟลช ISO ลงไดรฟ์นี้"):
            return

        self.start_process(
            ["--worker-flash", self.iso_path, device["path"]],
            [f"ISO: {self.iso_path}", f"Target: {device['path']}"],
        )

    def start_format(self, filesystem: str) -> None:
        device = self.selected_device()
        if device is None:
            QMessageBox.warning(self, "Missing Drive", "เลือกแฟลชไดรฟ์ที่จะฟอร์แมตก่อน")
            return

        if not self.confirm_device(
            device,
            f"การลบข้อมูลทั้งหมดและฟอร์แมตเป็น {filesystem.upper()}",
        ):
            return

        self.start_process(
            ["--worker-format", device["path"], filesystem],
            [f"Operation: format {filesystem.upper()}", f"Target: {device['path']}"],
        )

    def on_ready_output(self) -> None:
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
        self.append_log(data)

    def on_ready_error(self) -> None:
        if self.process is None:
            return
        data = bytes(self.process.readAllStandardError()).decode(errors="replace")
        self.append_log(data)

    def on_finished(self, exit_code: int, _exit_status) -> None:
        self.set_busy(False)
        self.load_devices()
        if exit_code == 0:
            QMessageBox.information(self, "Done", "Operation complete")
            return
        QMessageBox.warning(
            self,
            "Failed",
            "Operation failed or was cancelled. ตรวจ log ด้านล่างเพื่อดูรายละเอียด",
        )


def run_gui() -> int:
    if shutil.which("pkexec") is None:
        print("Missing pkexec. Install polkit to use the GUI app.", file=sys.stderr)
        return 1

    app = QApplication(sys.argv)
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
