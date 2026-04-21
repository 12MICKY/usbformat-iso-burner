# USB Formatter and ISO Burner

Linux desktop utility for:

- formatting removable USB drives as `exFAT`, `FAT32`, `NTFS`, or `ext4`
- writing `.iso` images directly to USB drives
- showing operation logs and live write progress in a focused PyQt6 GUI

This project is Linux-first, open source, and intended for local desktop use with explicit confirmation before destructive actions.

## Download

Latest release:

- Release page: `https://github.com/12MICKY/usbformat-iso-burner/releases/tag/v0.2.1`
- Linux binary: `usbformat-iso-burner-linux-x86_64.tar.gz`
- Portable Python package: `usbformat-iso-burner-portable.tar.gz`
- Checksums: `SHA256SUMS`

Release archives are published as GitHub release assets. They are not kept in the main branch to avoid oversized repository files.

## Quick Start

### Option 1: Linux binary

```bash
tar -xzf usbformat-iso-burner-linux-x86_64.tar.gz
cd usbformat-iso-burner-linux-x86_64
./usbformat-iso-burner
```

### Option 2: Portable Python package

```bash
tar -xzf usbformat-iso-burner-portable.tar.gz
cd usbformat-iso-burner-portable
./run.sh
```

### Option 3: Run from source

```bash
pip install -r requirements.txt
./run.sh
```

## Verify Downloads

```bash
sha256sum -c SHA256SUMS
```

Current checksums:

```text
0568c9e4eae584bec1908bc38644c8946f4b567fe33016cb212a5b45feae75f9  usbformat-iso-burner-linux-x86_64.tar.gz
5b461839062b0184cc20bf91df2f94ad3addcf7a1349a4562a33bf54599cf2b5  usbformat-iso-burner-portable.tar.gz
```

## Features

- detects USB and removable drives via `lsblk`
- formats selected devices as `exFAT`, `FAT32`, `NTFS`, or `ext4`
- writes ISO images with `dd`
- automatically unmounts mounted target partitions first
- requires typed confirmation of the target device path
- shows log output inside the app
- shows live progress while writing ISO images
- batches log/progress updates to keep the GUI responsive during long operations
- uses faster `dd` defaults for better ISO write throughput
- includes a Python portable package and a Linux binary release

## Runtime Requirements

- Linux desktop environment
- `pkexec` from polkit
- `lsblk`
- `umount`
- `wipefs`
- `sync`
- `dd`

Filesystem tools used when formatting:

- `mkfs.exfat`
- `mkfs.vfat`
- `mkfs.ntfs`
- `mkfs.ext4`

On Debian/Ubuntu-based systems:

```bash
sudo apt install util-linux polkit exfatprogs dosfstools ntfs-3g e2fsprogs
```

If running from source or the portable Python package:

```bash
pip install -r requirements.txt
```

## Safety

- formatting and ISO writing overwrite the selected target device
- ISO writing targets the whole disk, not a single partition
- the app asks you to type the target device path before destructive actions
- always verify the selected device, for example `/dev/sdb`, before confirming
- never use this tool on a drive you are not prepared to erase

## How It Works

The application uses:

- `lsblk -J` to discover block devices
- `pkexec` to relaunch worker operations with root privileges
- `umount` to detach mounted target partitions
- `wipefs -a` before formatting
- `mkfs.*` for filesystem creation
- `dd` for direct ISO-to-device writes
- a GUI progress bar that parses `dd` byte progress output
- throttled UI updates so progress rendering does not overwhelm the interface during writes

Main source file:

- [`iso_gui.py`](./iso_gui.py)

## Install As Desktop App

To install for the current user with a desktop launcher:

```bash
./install.sh
```

This installs files into:

- `~/.local/share/usbformat-iso-burner`
- `~/.local/share/applications/usbformat-iso-burner.desktop`

## Development

Basic local validation:

```bash
python3 -m py_compile iso_gui.py
python3 -m unittest discover -s tests -p "test_*.py"
```

Rebuild the Linux binary release:

```bash
./build-binary-release.sh
```

That script also rebuilds the portable archive and refreshes `SHA256SUMS`.

## Repository Files

- `iso_gui.py`: main application source
- `run.sh`: source launcher
- `install.sh`: local installer
- `build-binary-release.sh`: rebuild script for the Linux binary release
- `usbformat-iso-burner.desktop`: desktop launcher definition
- `requirements.txt`: Python dependency list
- `SHA256SUMS`: checksums for downloadable artifacts
- `release-notes.md`: short binary release notes

## Open Source

- License: `MIT`
- Changelog: [`CHANGELOG.md`](./CHANGELOG.md)
- Contribution guide: [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- Code of conduct: [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md)
- Security policy: [`SECURITY.md`](./SECURITY.md)

Issues and pull requests are welcome.

## License

Released under the `MIT` License. See [`LICENSE`](./LICENSE).
