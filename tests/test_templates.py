"""
tests/test_templates.py -- Unit Tests fuer Template-Validierung
Keine ADB-Verbindung noetig -- testet nur Dateisystem-Logik.
"""
from __future__ import annotations

from pathlib import Path

from bot.core import BotConfig, LastWarBot


def _make_config(tmp_path: Path) -> BotConfig:
    """Erstellt BotConfig mit temporaerem templates_dir."""
    return BotConfig(
        device_serial="emulator-5554",
        bot_id=1,
        account_name="TestBot",
        templates_dir=tmp_path / "templates",
        screenshot_dir=tmp_path / "screenshots",
    )


def test_should_detect_all_missing_templates(tmp_path: Path):
    cfg = _make_config(tmp_path)
    cfg.templates_dir.mkdir(parents=True)
    missing = [
        name for name in LastWarBot.REQUIRED_TEMPLATES
        if not (cfg.templates_dir / f"{name}.png").exists()
    ]
    assert len(missing) == len(LastWarBot.REQUIRED_TEMPLATES)


def test_should_detect_no_missing_when_all_present(tmp_path: Path):
    cfg = _make_config(tmp_path)
    cfg.templates_dir.mkdir(parents=True)
    for name in LastWarBot.REQUIRED_TEMPLATES:
        (cfg.templates_dir / f"{name}.png").write_bytes(b"\x89PNG fake")
    missing = [
        name for name in LastWarBot.REQUIRED_TEMPLATES
        if not (cfg.templates_dir / f"{name}.png").exists()
    ]
    assert missing == []


def test_should_detect_partial_missing(tmp_path: Path):
    cfg = _make_config(tmp_path)
    cfg.templates_dir.mkdir(parents=True)
    # Nur die Haelfte anlegen
    for name in LastWarBot.REQUIRED_TEMPLATES[:5]:
        (cfg.templates_dir / f"{name}.png").write_bytes(b"\x89PNG fake")
    missing = [
        name for name in LastWarBot.REQUIRED_TEMPLATES
        if not (cfg.templates_dir / f"{name}.png").exists()
    ]
    assert len(missing) == len(LastWarBot.REQUIRED_TEMPLATES) - 5


def test_should_list_required_templates():
    assert len(LastWarBot.REQUIRED_TEMPLATES) == 17
    assert "btn_home" in LastWarBot.REQUIRED_TEMPLATES
    assert "btn_confirm" in LastWarBot.REQUIRED_TEMPLATES
    assert "result_victory" in LastWarBot.REQUIRED_TEMPLATES
