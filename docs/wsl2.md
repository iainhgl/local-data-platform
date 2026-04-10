# WSL2 Guide

## Prerequisites

- WSL2 with Ubuntu 22.04+
- Docker Desktop with the WSL2 backend enabled
- 8 GB RAM minimum available to Docker and WSL2

## Docker Desktop settings

In Docker Desktop, open `Settings -> Resources` and enable `Use WSL 2 based engine`. Confirm your Ubuntu distribution is enabled under the WSL integration settings before starting the platform.

## Known limitations

- DuckDB file paths work best when the repository lives inside the WSL2 filesystem. If you keep the repo on Windows storage, use paths under `/mnt/c/...` consistently.
- DuckDB file locking is still local-process based, so avoid running overlapping write-heavy jobs from both Windows and WSL shells at the same time.

## Memory configuration

Create or update `%USERPROFILE%\.wslconfig` with:

```ini
[wsl2]
memory=8GB
```

Increase this if you plan to use the `lakehouse` or `full` profiles regularly.

## Accessing services from Windows

WSL2 forwards container ports to Windows automatically, so `http://localhost:18010`, `http://localhost:18020`, and the other documented local URLs should open from your Windows browser.
