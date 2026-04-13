# USB Formatter and ISO Burner

Simple PyQt6 desktop app for Linux that can:

- detect USB and removable drives
- format a selected drive as `exFAT`, `FAT32`, `NTFS`, or `ext4`
- flash an `.iso` image directly to a USB drive with `dd`
- show progress and command output in a built-in log panel

The app is designed for local Linux use and asks for elevated privileges with `pkexec` only when a destructive operation starts.

This project is open source and open to improvements, bug reports, and pull requests.

## Features

- GUI for selecting removable drives
- Manual refresh for device detection
- Confirmation prompt that requires typing the target device path
- Automatic unmount before formatting or flashing
- Built-in log output for progress and errors

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

## Run

From the project directory:

```bash
python3 iso_gui.py
```

## Open Source

- License: `MIT`
- Contributions: welcome through issues and pull requests
- Code of conduct: see [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)
- Contribution guide: see [`CONTRIBUTING.md`](./CONTRIBUTING.md)

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
├── iso_gui.py
└── README.md
```

## Possible Improvements

- package the app with a desktop entry and icon
- add a requirements file
- add unit tests for device parsing and validation logic
- support labels and partition table creation explicitly

## License

This project is released under the `MIT` License. See [`LICENSE`](./LICENSE).
