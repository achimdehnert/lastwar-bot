"""
bot/dry_run.py -- Dry-Run Modus fuer Bot-Tests ohne echtes Spiel

Simuliert ADB-Verbindung und Template-Matching.
Testet die gesamte Bot-Logik (Ablauf, Recovery, Metriken)
ohne laufenden Emulator.

Aufruf:
  python3 -m bot.dry_run [--bot-id 1] [--fail-steps 2]
"""
from __future__ import annotations

import argparse
import logging
import random
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

from bot.core import BotConfig, LastWarBot, MatchResult
from bot.metrics import RunMetrics, write_metrics

logger = logging.getLogger(__name__)


def create_mock_bot(
    bot_id: int = 1,
    fail_probability: float = 0.0,
    templates_dir: Path | None = None,
) -> LastWarBot:
    """
    Erstellt einen LastWarBot mit gemocktem ADB-Device.

    Args:
        bot_id: Bot-ID (1-3)
        fail_probability: Wahrscheinlichkeit dass ein Step fehlschlaegt (0.0-1.0)
        templates_dir: Optional, Pfad zu Templates (oder temp-dir mit Fake-Templates)
    """
    config = BotConfig(
        device_serial=f"emulator-{5552 + bot_id * 2}",
        bot_id=bot_id,
        account_name=f"DryRunBot{bot_id}",
        templates_dir=templates_dir or Path("/tmp/lastwar-dry-run/templates"),
        screenshot_dir=Path("/tmp/lastwar-dry-run/screenshots"),
    )

    config.screenshot_dir.mkdir(parents=True, exist_ok=True)
    config.templates_dir.mkdir(parents=True, exist_ok=True)

    # Fake-Templates erstellen damit validate_templates() nicht fehlschlaegt
    for name in LastWarBot.REQUIRED_TEMPLATES:
        tpl = config.templates_dir / f"{name}.png"
        if not tpl.exists():
            tpl.write_bytes(b"\x89PNG fake-template-for-dry-run")

    bot = LastWarBot.__new__(LastWarBot)
    bot.config = config

    # Mock ADB device
    mock_device = MagicMock()
    mock_device.device_info = {
        "model": "DryRun-Emulator", "serial": config.device_serial,
    }
    mock_device.app_current.return_value = {"package": config.package}
    mock_device.screenshot.return_value = MagicMock()  # Fake PIL Image
    bot.d = mock_device

    # Mock template matching -- basierend auf fail_probability
    def mock_find_template(self, name: str, **kwargs) -> MatchResult:
        if random.random() < fail_probability and name != "btn_home":
            logger.debug("DryRun: %s NOT FOUND (simulated)", name)
            return MatchResult(found=False)
        logger.debug("DryRun: %s FOUND (simulated)", name)
        return MatchResult(found=True, confidence=0.95, x=540, y=960)

    # Patch methods
    bot.find_template = lambda name, **kw: mock_find_template(bot, name, **kw)
    bot.wait_for_template = lambda name, **kw: mock_find_template(bot, name, **kw)
    bot.click_template = lambda name, **kw: mock_find_template(bot, name, **kw)
    bot.save_screenshot = lambda prefix="": logger.debug(
        "DryRun: screenshot %s", prefix,
    )
    bot.back = lambda: logger.debug("DryRun: back()")
    bot.tap = lambda x, y: logger.debug("DryRun: tap(%d, %d)", x, y)

    # Mock game actions to simulate work
    def mock_action(action_name: str):
        def _action(*args, **kwargs):
            delay = random.uniform(0.05, 0.15)
            time.sleep(delay)
            if random.random() < fail_probability:
                raise RuntimeError(f"DryRun: simulated failure in {action_name}")
            logger.info(
                "DryRun Bot %d: %s OK (%.0fms)",
                bot_id, action_name, delay * 1000,
            )
        return _action

    bot.collect_daily_rewards = mock_action("collect_daily_rewards")
    bot.collect_resources = mock_action("collect_resources")
    bot.heal_troops = mock_action("heal_troops")
    bot.train_troops = mock_action("train_troops")
    bot.send_gathering = mock_action("send_gathering")
    bot.hunt_zombies = mock_action("hunt_zombies")
    bot.ensure_game_running = mock_action("ensure_game_running")
    bot.is_connected = lambda: True
    bot.reconnect = lambda: logger.info("DryRun: reconnect (noop)")
    bot.validate_templates = lambda: []
    bot._ensure_home_screen = lambda max_attempts=3: True

    return bot


def dry_run(bot_id: int = 1, fail_probability: float = 0.0) -> dict:
    """Fuehrt einen vollstaendigen Dry-Run durch."""
    logger.info(
        "=== DRY RUN Bot %d (fail_prob=%.0f%%) ===",
        bot_id, fail_probability * 100,
    )

    bot = create_mock_bot(bot_id=bot_id, fail_probability=fail_probability)
    metrics = RunMetrics(bot_id=bot_id)

    try:
        results = bot.run_daily_routine()
        metrics.finish(results)
        write_metrics(metrics)

        logger.info("=== DRY RUN ERGEBNIS ===")
        for step, status in results.items():
            marker = "OK" if status == "ok" else "FAIL" if "fail" in status else "SKIP"
            logger.info("  [%s] %s: %s", marker, step, status)
        logger.info(
            "Dauer: %.1fs | OK: %d | Fail: %d | Skip: %d",
            metrics.duration_seconds,
            metrics.steps_ok,
            metrics.steps_failed,
            metrics.steps_skipped,
        )
        return results
    except Exception as exc:
        logger.error("DRY RUN FEHLER: %s", exc)
        metrics.finish({"run": f"fail: {exc}"})
        write_metrics(metrics)
        return {"error": str(exc)}


def main() -> int:
    from bot import setup_logging
    setup_logging(logging.DEBUG)

    parser = argparse.ArgumentParser(description="Last War Bot Dry-Run")
    parser.add_argument("--bot-id", type=int, default=1, help="Bot-ID (1-3)")
    parser.add_argument(
        "--fail-probability",
        type=float,
        default=0.0,
        help="Fehler-Wahrscheinlichkeit pro Step (0.0-1.0, default: 0.0)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Anzahl Durchlaeufe (default: 1)",
    )
    args = parser.parse_args()

    all_results = []
    for run_nr in range(1, args.runs + 1):
        if args.runs > 1:
            logger.info("--- Run %d/%d ---", run_nr, args.runs)
        result = dry_run(bot_id=args.bot_id, fail_probability=args.fail_probability)
        all_results.append(result)

    if args.runs > 1:
        total_ok = sum(
            sum(1 for v in r.values() if v == "ok")
            for r in all_results if "error" not in r
        )
        total_fail = sum(
            sum(1 for v in r.values() if isinstance(v, str) and "fail" in v)
            for r in all_results if "error" not in r
        )
        logger.info(
            "=== %d Runs: %d Steps OK, %d Steps Failed ===",
            args.runs, total_ok, total_fail,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
