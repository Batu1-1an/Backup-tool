<div align="center">
  <h1>🗄️ Backup Tool</h1>
  <p><strong>Cross-platform CLI engine for automated file backup &amp; restoration to SMB/NFS network shares</strong></p>

  <a href="#"><img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python 3.7+"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-windows%20%7C%20linux-lightgrey?style=flat-square" alt="Platform: Windows | Linux"></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square" alt="Tests: Passing"></a>
  <a href="#"><img src="https://img.shields.io/badge/maintenance-active-%2300b894?style=flat-square" alt="Maintenance: Active"></a>
</div>

<br>

---

## 🔥 The Problem

Manual backups are fragile. Cron jobs with raw `rsync` or `robocopy` scripts lack error handling, logging, and retention management. When a server dies, you discover what _wasn't_ backed up — and the one tape you needed is corrupted.

**Backup Tool** replaces ad-hoc shell scripts with a declarative, protocol-aware backup engine. Define your sources and targets once in YAML, then run on-demand or let the built-in scheduler handle daily/weekly rotations. It handles SMB _and_ NFS on both Windows and Linux, so your heterogeneous environment is covered under a single CLI.

---

## ✨ Features

| Area | Capabilities |
|------|-------------|
| **📋 Declarative Config** | YAML-based — sources, targets, schedules, retention, logging in one file |
| **🔌 Dual Protocol** | Native SMB (CIFS) and NFS on Windows _and_ Linux |
| **⏰ Smart Scheduling** | Built-in daily & weekly scheduler via the `schedule` library |
| **📤 On-Demand Backup** | Manual backup with optional source/target overrides |
| **📥 Point-in-Time Restore** | Restore from any timestamp; `overwrite` or `error` conflict strategy |
| **🔄 Rotation & Pruning** | Configurable `keep_last` policy — auto-prune old backups |
| **📈 Incremental Backups** | File-level incremental via size + mtime comparison |
| **📊 Progress Reporting** | Real-time progress during file copy operations |
| **🔐 Secure Credentials** | `${VAR}` expansion in config — keep secrets out of files |
| **📝 Structured Logging** | Rotating file logger with configurable level and path |
| **🎯 Runtime Overrides** | Override sources or targets via CLI without touching config |
| **🛡️ Graceful Errors** | Per-file failure handling — one bad file never kills a run |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  config.yaml │────▶│  Scheduler    │────▶│   Backup Engine  │────▶│  Network Share   │
│  (sources,   │     │  (daily /     │     │  (full / incr.)  │     │  (SMB / NFS)     │
│   target,    │     │   weekly)     │     │                  │     │                  │
│   retention) │     │              │     │                  │     │                  │
└──────────────┘     └──────────────┘     └─────────────────┘     └─────────────────┘
       │                                                                    │
       │                                                                    │
       ▼                                                                    ▼
┌──────────────┐                                                   ┌─────────────────┐
│  Logger      │                                                   │   Restore       │
│  (file +     │                                                   │   Engine        │
│   console)   │                                                   │   (timestamp)   │
└──────────────┘                                                   └─────────────────┘
```

The `Scheduler` runs as a long-lived process, firing `Backup Engine` on the configured cadence. The engine reads sources from config (or CLI overrides), copies to the target share, then applies the retention policy. The `Restore Engine` reads a timestamped backup directory and reconstructs files to a local destination.

---

## 🚀 Quick Start

<details open>
<summary><strong>Get up and running in 4 steps</strong></summary>

```bash
# 1. Clone & enter
git clone https://github.com/Batu1-1an/Backup-tool.git
cd Backup-tool

# 2. Create virtual environment & install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Copy and edit config
cp config/backup_config.yaml.example config/backup_config.yaml

# 4. Run your first backup
backup_tool backup
```
</details>

> **Prerequisites:** Python 3.7+, network access to an SMB or NFS share, and write permission on the target. Linux users need `cifs-utils` and `sudo` for mounting.

---

## 📖 CLI Reference

```
backup_tool [--config PATH] [--log-level LEVEL] [--log-file PATH] <command> [OPTIONS]
```

### Global Options

| Flag | Default | Description |
|------|---------|-------------|
| `--config PATH` | `config/backup_config.yaml` | Path to YAML configuration file |
| `--log-level LEVEL` | `INFO` | One of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-file PATH` | from config | Override log file destination |

### Commands

| Command | Description |
|---------|-------------|
| `backup` | Execute a manual backup |
| `restore` | Restore files from a specific backup timestamp |
| `schedule` | Start the automated backup scheduler (long-lived) |

---

### `backup` — Manual Backup

```bash
backup_tool backup [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--source PATH [PATH ...]` | from config | Override source paths (space-separated) |
| `--target TYPE:VALUE` | from config | Override target (`smb://server/share` or `nfs://server:/export`) |
| `--incremental` | `false` | Enable file-level incremental mode |

**Examples:**
```bash
# Default config backup
backup_tool backup

# Override sources, debug logging
backup_tool backup --source /etc/nginx /home/user/documents --log-level DEBUG

# Custom config with incremental mode
backup_tool backup --config /etc/backup_tool/prod.yaml --incremental
```

---

### `restore` — Point-in-Time Restore

```bash
backup_tool restore --backup-timestamp <YYYYMMDD_HHMMSS> --destination <PATH> [OPTIONS]
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--backup-timestamp TEXT` | ✅ | — | Timestamp of the backup to restore (`20231027_103000`) |
| `--destination PATH` | ✅ | — | Local directory to restore files into |
| `--conflict-strategy STRATEGY` | — | `overwrite` | `overwrite` or `error` |
| `--incremental-parent TEXT` | — | — | Parent timestamp for incremental restore chain |

**Examples:**
```bash
# Restore with overwrite
backup_tool restore --backup-timestamp 20231027_103000 --destination /tmp/restore

# Safety-first: error on any conflict
backup_tool restore --backup-timestamp 20231027_103000 --destination /tmp/restore --conflict-strategy error
```

---

### `schedule` — Automated Scheduler

```bash
backup_tool schedule [OPTIONS]
```

Runs indefinitely. Define cadence in `config/backup_config.yaml`:

```yaml
schedule:
  daily: "02:00"           # 24-hour format
  weekly: "Sunday 03:00"
```

| Option | Description |
|--------|-------------|
| `--once` | Run scheduled tasks once and exit (useful for systemd timers / cron wrappers) |

---

## ⚙️ Configuration Reference

Full configuration lives in a single YAML file. Environment variables (`${VAR}` syntax) are expanded at runtime.

```yaml
# ── Backup Sources ──────────────────────────────────────────
backup_sources:
  - /var/log/syslog
  - /etc/nginx/nginx.conf
  - /home/user/documents

# ── Backup Target ───────────────────────────────────────────
backup_target:
  path: //your_backup_server/backup_share   # SMB: //server/share  |  NFS: server:/export
  type: smb                                  # "smb" | "nfs"
  credentials:
    username: ${BACKUP_USER}
    password: ${BACKUP_PASS}

# ── Schedule ────────────────────────────────────────────────
schedule:
  daily: "02:00"              # HH:MM (24-hour)
  weekly: "Sunday 03:00"      # Day HH:MM

# ── Retention Policy ────────────────────────────────────────
retention_policy:
  keep_last: 30               # Number of most recent backups to retain

# ── Logging ─────────────────────────────────────────────────
logging:
  log_file: /var/log/backup_tool/backup_tool.log   # or C:\Logs\backup_tool.log
  level: INFO                                       # DEBUG | INFO | WARNING | ERROR | CRITICAL
```

> **🔐 Security:** Never hardcode credentials. Use `${VAR}` references — the loader expands them from the environment at runtime. Pair this with a `.env` file or your secrets manager.

---

## 📁 Project Structure

```
Backup-tool/
├── config/
│   └── backup_config.yaml.example   # Configuration template
├── docs/                             # Extended documentation
│   ├── architecture.md
│   ├── backup_tool_plan.md
│   ├── directory_structure.md
│   ├── error_documentation.md
│   ├── lessons_learned.md
│   ├── memory.md
│   ├── product_requirement_docs.md
│   ├── technical.md
│   └── usage.md
├── src/
│   ├── backup_tool/                  # Core library
│   │   ├── __init__.py
│   │   ├── config.py                 # YAML loader & validator
│   │   ├── backup.py                 # Backup engine (full + incremental)
│   │   ├── restore.py                # Restore engine with conflict resolution
│   │   ├── scheduler.py              # Automated job scheduler
│   │   ├── network.py                # SMB / NFS share connectivity
│   │   └── logger.py                 # Rotating file + console logging
│   └── main.py                       # CLI entry point (argparse)
├── tasks/
│   ├── active_context.md
│   └── tasks_plan.md
├── tests/
│   ├── test_config.py
│   ├── test_backup.py
│   ├── test_restore.py
│   ├── test_network.py
│   ├── test_logger.py
│   └── test_placeholder.py
├── requirements.txt
└── README.md
```

---

## 🧪 Testing

```bash
# Full test suite
pytest -v

# Module-specific
pytest tests/test_config.py -v
pytest tests/test_backup.py -v

# With coverage
pytest --cov=backup_tool tests/
```

Uses **pytest 8.1+** with `unittest.mock` for comprehensive unit coverage.

---

## 🗺️ Roadmap

- [x] YAML configuration with validation & env var expansion
- [x] SMB / NFS network share connectivity (Windows + Linux)
- [x] Full backup with real-time progress reporting
- [x] Point-in-time restore with conflict handling
- [x] Daily & weekly job scheduling
- [x] Backup rotation & pruning (retention policy)
- [x] Incremental backup (file-level size/mtime)
- [ ] Compression (gzip / zstd archive support)
- [ ] Encryption (AES-256-GCM for backup payloads)
- [ ] Notifications (email / Slack / webhook)
- [ ] Daemon mode (run as system service)
- [ ] Web monitoring dashboard
- [ ] Backup verification (checksum integrity checks)

---

## 📄 License

[MIT](LICENSE) — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with Python · Maintained by <a href="https://github.com/Batu1-1an">Batu1-1an</a></sub>
  <br>
  <sub>⭐ Star this repo if you find it useful</sub>
</div>
