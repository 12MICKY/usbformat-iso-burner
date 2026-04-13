# Security Policy

## Supported Versions

This project is currently maintained on the `main` branch only.

## Reporting a Vulnerability

If you discover a security issue, do not open a public issue with exploit details first.

Instead:

1. describe the issue clearly
2. include affected file paths and reproduction steps
3. explain whether the issue can lead to unintended disk erasure, privilege misuse, or unsafe command execution

Open a private report through GitHub security reporting if available for the repository. If private reporting is not enabled, contact the maintainer directly before publishing details.

## Scope

Security-sensitive areas in this project include:

- device detection and selection
- privilege escalation flow through `pkexec`
- command execution for `dd`, `wipefs`, `umount`, and `mkfs.*`
- any logic that could target the wrong block device
