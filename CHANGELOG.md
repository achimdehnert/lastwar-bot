# Changelog

All notable changes to **lastwar-bot** will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **ADB retry decorator** (`_adb_retry`) with exponential backoff for resilient emulator connections
- **Connection health check** (`is_connected()`, `reconnect()`) for proactive connection management
- **Home-screen recovery** (`_ensure_home_screen()`) with app restart fallback
- **Consecutive failure abort** -- 3 failures in a row skip remaining steps
- **Structured run metrics** (`bot/metrics.py`) -- JSON-Lines log for monitoring (Phase 4 prep)
- **Unit tests** -- 20 tests covering config, templates, tasks (no ADB required)
- **Proper pyproject.toml** with hatchling build, dev extras, pytest config

### Changed
- `BotConfig` env defaults now use `field(default_factory=...)` instead of `os.getenv()` at class definition time (testability)
- `run_daily_routine()` returns `dict` with per-step results instead of `None`
- `validate_all_templates` task no longer creates ADB connections (file-existence check only)
- Server info corrected: Netcup vServer / Debian 13 (was Hetzner / Ubuntu)
- Setup script updated for Debian 13 (python3 instead of python3.12)
- Deploy script default IP corrected to 152.53.142.4
- Ruff lint rules expanded: added I (isort), UP (pyupgrade), B (bugbear)

### Fixed
- Hardcoded wrong server IP in deploy.sh (204.168.149.6 -> 152.53.142.4)
- setup.cfg cleaned up (flake8 config moved to pyproject.toml ruff section)

## [0.0.0] - 2025-01-01

### Added
- Initial CHANGELOG

