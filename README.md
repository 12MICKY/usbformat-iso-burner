# USB Formatter and ISO Burner

A Linux desktop utility for formatting removable USB drives and writing ISO images with a focused PyQt6 interface.

## Overview

This project provides a small Linux-first GUI for two common low-level USB tasks:

- detect USB and removable drives
- format a selected drive as `exFAT`, `FAT32`, `NTFS`, or `ext4`
- flash an `.iso` image directly to a USB drive with `dd`
- show progress and command output in a built-in log panel

The app is designed for local Linux use and asks for elevated privileges with `pkexec` only when a destructive operation starts.

This project is open source and open to improvements, bug reports, and pull requests.

## Quick Start

Download the repository archive or clone the project, then run:

```bash
./run.sh
```

If `PyQt6` is not installed yet:

```bash
pip install -r requirements.txt
./run.sh
```

## Features

- GUI for selecting removable drives
- Manual refresh for device detection
- Confirmation prompt that requires typing the target device path
- Automatic unmount before formatting or flashing
- Built-in log output for progress and errors
- Portable package included in the repository
- Optional local desktop launcher installation via `install.sh`

## Intended Platform

- primary target: Linux desktop systems
- tested flow: Python + PyQt6 + `pkexec`
- not intended for Windows or macOS in its current form

## Requirements

- Linux
- Python 3.10+
- `PyQt6`
- `lsblk`
- `pkexec` from polkit
- `wipefs`
- `umount`
- `sync`
- `dd`

For filesystem formatting support, install the tools you need:

- `mkfs.exfat`
- `mkfs.vfat`
- `mkfs.ntfs`
- `mkfs.ext4`

## Install

Install Python dependency:

```bash
pip install PyQt6
```

On Debian/Ubuntu-based systems, the system tools are typically available from packages such as:

```bash
sudo apt install util-linux polkit exfatprogs dosfstools ntfs-3g e2fsprogs
```

## Download and Use

If you want a ready-to-download package from GitHub, use the portable archive from the repository and run:

```bash
tar -xzf usbformat-iso-burner-portable.tar.gz
cd usbformat-iso-burner-portable
./run.sh
```

For local installation with an application launcher:

```bash
./install.sh
```

## Run

From the project directory:

```bash
python3 iso_gui.py
```

Or use:

```bash
./run.sh
```

## Repository Files

- `iso_gui.py`: main application source
- `run.sh`: simple launcher script
- `install.sh`: local user installation helper
- `usbformat-iso-burner.desktop`: desktop launcher definition
- `usbformat-iso-burner-portable.tar.gz`: portable archive for direct download
- `requirements.txt`: Python dependency list

## Open Source

- License: `MIT`
- Contributions: welcome through issues and pull requests
- Code of conduct: see [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)
- Contribution guide: see [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- Security policy: see [`SECURITY.md`](./SECURITY.md)
- Changelog: see [`CHANGELOG.md`](./CHANGELOG.md)

## How It Works

The application uses:

- `lsblk -J` to discover block devices
- `pkexec` to relaunch the script with root privileges for destructive actions
- `umount` to unmount mounted partitions on the selected target
- `wipefs -a` before formatting
- `mkfs.*` to create the selected filesystem
- `dd` to write an ISO image directly to the whole device

The main GUI lives in [`iso_gui.py`](./iso_gui.py).

## Safety Notes

- Formatting and ISO flashing overwrite the selected target device.
- Always verify the device path, for example `/dev/sdb`, before confirming.
- Flashing an ISO writes to the whole disk, not a single partition.
- Run this only on drives you are prepared to erase.

## Project Structure

```text
.
├── install.sh
├── iso_gui.py
├── requirements.txt
├── run.sh
├── usbformat-iso-burner.desktop
└── README.md
```

## Possible Improvements

- package the app with a desktop entry and icon
- add unit tests for device parsing and validation logic
- support labels and partition table creation explicitly

## License

This project is released under the `MIT` License. See [`LICENSE`](./LICENSE).
