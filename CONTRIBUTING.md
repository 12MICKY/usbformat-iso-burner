# Contributing

Thanks for contributing to USB Formatter and ISO Burner.

## Before You Start

- open an issue for bugs, regressions, or feature proposals when possible
- keep changes focused and easy to review
- avoid unrelated refactors in the same pull request

## Development Setup

```bash
pip install PyQt6
python3 -m py_compile iso_gui.py
python3 iso_gui.py
```

## Pull Request Guidelines

- describe what changed and why
- include validation steps you used
- keep UI and behavior changes explicit
- update `README.md` if usage or requirements changed

## Safety

This application can erase disks. Do not submit changes that make destructive actions less explicit or less safe without a strong reason.

## Code Style

- keep dependencies minimal
- prefer clear standard-library Python
- preserve Linux-first behavior unless a change intentionally broadens platform support
