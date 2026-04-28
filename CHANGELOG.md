# Changelog

## 0.2.0 (2026-04-28)

### Features

- Add `pyproject.toml` for pip install support (`pip install .`)
- Restructure module with `cli.py` and `__main__.py` for `python -m backup_tool`
- Add Dockerfile for containerized deployment
- Add `.dockerignore` for optimized Docker builds
- Add `__version__` and proper `__all__` exports in `__init__.py`

### Bug Fixes

- Fix missing `import os` in `scheduler.py` causing `NameError` in standalone use

### Documentation

- Add CHANGELOG.md for version tracking
- Add CONTRIBUTING.md for open source contributors

## 0.1.0 (2026-04-27)

### Features

- YAML configuration with validation and env var expansion (`${VAR}` syntax)
- SMB and NFS network share connectivity (Windows + Linux)
- Full backup with real-time progress reporting
- Point-in-time restore with conflict handling (`overwrite` / `error`)
- Daily and weekly job scheduling via the `schedule` library
- Backup rotation and pruning (configurable `keep_last` retention policy)
- Incremental backup (file-level size/mtime comparison)
- Structured rotating file logger with configurable level
- CLI entry point with `backup`, `restore`, and `schedule` commands
- Per-file error handling (one bad file never kills a run)

### Documentation

- README with features, architecture, quick start, CLI reference, and roadmap
- Extended docs in `docs/` directory (architecture, plan, usage, etc.)
- Example configuration file in `config/backup_config.yaml.example`
