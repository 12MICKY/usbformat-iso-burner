# Changelog

All notable changes to this project will be documented in this file.

## 2026-04-21

- repository polish and GitHub community files
- added a Linux x86_64 PyInstaller binary release archive
- added checksums for downloadable artifacts
- added release notes for binary distribution
- improved GUI responsiveness by batching log output and throttling progress updates
- sped up ISO writes by switching to a larger `dd` block size and removing extra sync overhead
- preserved the selected device during refresh to make device rescans feel smoother
- updated the release build script to regenerate both binary and portable archives with fresh checksums

## 2026-04-13

- initial public project import
- added README, open source license, contribution guide, and code of conduct
- refined the UI to feel more like a Linux desktop utility
- converted in-app text to English-only
- added portable archive, launcher scripts, and desktop entry
