"""
tests/test_config.py -- Unit Tests fuer BotConfig und MatchResult
Keine ADB-Verbindung noetig -- testet reine Datenklassen-Logik.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from bot.core import BotConfig, MatchResult, _env_float, _env_int

# -- _env_float / _env_int ---------------------------------------------------

def test_should_return_default_when_env_not_set():
    with patch.dict(os.environ, {}, clear=True):
        assert _env_float("BOT_MATCH_THRESHOLD", 0.85) == 0.85
        assert _env_int("BOT_SCREENSHOT_MAX_FILES", 50) == 50


def test_should_read_env_override():
    with patch.dict(os.environ, {"BOT_MATCH_THRESHOLD": "0.90"}):
        assert _env_float("BOT_MATCH_THRESHOLD", 0.85) == 0.90


def test_should_read_env_int_override():
    with patch.dict(os.environ, {"BOT_SCREENSHOT_MAX_FILES": "100"}):
        assert _env_int("BOT_SCREENSHOT_MAX_FILES", 50) == 100


# -- BotConfig ----------------------------------------------------------------

def test_should_create_config_with_defaults():
    cfg = BotConfig(device_serial="emulator-5554", bot_id=1)
    assert cfg.device_serial == "emulator-5554"
    assert cfg.bot_id == 1
    assert cfg.account_name == ""
    assert cfg.package == "com.fun.lastwar.gp"
    assert isinstance(cfg.templates_dir, Path)
    assert isinstance(cfg.screenshot_dir, Path)
    assert cfg.match_threshold > 0
    assert cfg.action_delay > 0
    assert cfg.screenshot_max_files > 0


def test_should_allow_custom_config_values():
    cfg = BotConfig(
        device_serial="emulator-5556",
        bot_id=2,
        account_name="TestPlayer",
        match_threshold=0.95,
        action_delay=2.0,
        screenshot_max_files=20,
    )
    assert cfg.account_name == "TestPlayer"
    assert cfg.match_threshold == 0.95
    assert cfg.action_delay == 2.0
    assert cfg.screenshot_max_files == 20


def test_should_use_env_for_config_defaults():
    with patch.dict(os.environ, {"BOT_MATCH_THRESHOLD": "0.75"}):
        cfg = BotConfig(device_serial="emulator-5554", bot_id=1)
        assert cfg.match_threshold == 0.75


# -- MatchResult --------------------------------------------------------------

def test_should_create_match_result_found():
    m = MatchResult(found=True, confidence=0.92, x=100, y=200)
    assert m.found is True
    assert m.confidence == 0.92
    assert m.x == 100
    assert m.y == 200


def test_should_create_match_result_not_found():
    m = MatchResult(found=False)
    assert m.found is False
    assert m.confidence == 0.0
    assert m.x == 0
    assert m.y == 0
