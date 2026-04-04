"""
tests/test_tasks.py -- Unit Tests fuer Celery Tasks
Testet Task-Konfiguration und Template-Validierung ohne ADB/Redis.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from bot.core import BotConfig
from bot.tasks import BOT_CONFIGS, app

# -- Celery Config ------------------------------------------------------------

def test_should_have_correct_celery_app_name():
    assert app.main == "lastwar_bot"


def test_should_have_json_serializer():
    assert app.conf.task_serializer == "json"


def test_should_have_beat_schedule():
    schedule = app.conf.beat_schedule
    assert "daily-routine-morning" in schedule
    assert "daily-routine-midday" in schedule
    assert "daily-routine-evening" in schedule
    assert "health-check" in schedule


def test_should_have_3_bot_configs():
    assert len(BOT_CONFIGS) == 3


def test_should_have_correct_serials():
    serials = [c.device_serial for c in BOT_CONFIGS]
    assert serials == ["emulator-5554", "emulator-5556", "emulator-5558"]


def test_should_have_sequential_bot_ids():
    ids = [c.bot_id for c in BOT_CONFIGS]
    assert ids == [1, 2, 3]


# -- validate_all_templates (ohne ADB) ----------------------------------------

def test_should_validate_templates_without_adb(tmp_path: Path):
    """validate_all_templates darf KEINE ADB-Verbindung aufbauen."""
    from bot.tasks import validate_all_templates

    fake_configs = [
        BotConfig(
            device_serial="emulator-5554",
            bot_id=1,
            account_name="TestBot",
            templates_dir=tmp_path / "templates",
        ),
    ]
    (tmp_path / "templates").mkdir()

    with patch("bot.tasks.BOT_CONFIGS", fake_configs):
        # Sollte NICHT u2.connect aufrufen
        with patch("bot.core.u2.connect") as mock_connect:
            result = validate_all_templates()
            mock_connect.assert_not_called()

    assert "bot_1" in result
    assert result["bot_1"]["ok"] is False
    assert len(result["bot_1"]["missing"]) == 17


def test_should_skip_bots_without_account_name(tmp_path: Path):
    from bot.tasks import validate_all_templates

    fake_configs = [
        BotConfig(device_serial="emulator-5554", bot_id=1, account_name=""),
    ]
    with patch("bot.tasks.BOT_CONFIGS", fake_configs):
        result = validate_all_templates()
    assert result["bot_1"]["skipped"] is True
