# Linux Binary Release

This repository includes a built Linux x86_64 executable:

- `usbformat-iso-burner-linux-x86_64.tar.gz`

Contents:

- `usbformat-iso-burner`: standalone PyInstaller-built executable
- `LICENSE`
- `README.md`
- `usbformat-iso-burner.desktop`

Usage:

```bash
tar -xzf usbformat-iso-burner-linux-x86_64.tar.gz
cd usbformat-iso-burner-linux-x86_64
./usbformat-iso-burner
```

Notes:

- target platform: Linux x86_64
- built on Linux with PyInstaller
- `pkexec` and system disk utilities are still required at runtime
