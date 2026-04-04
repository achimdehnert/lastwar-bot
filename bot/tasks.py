"""
bot/tasks.py -- Celery Tasks fuer Last War Bot
Zeitgesteuerte Ausfuehrung aller 3 Bot-Instanzen
"""
from __future__ import annotations

import logging
import os
import subprocess

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

from bot import setup_logging
from bot.core import BotConfig, LastWarBot
from bot.metrics import RunMetrics, write_metrics

load_dotenv()
setup_logging()

logger = logging.getLogger(__name__)

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_TIMEZONE = os.getenv("CELERY_TIMEZONE", "Europe/Berlin")

app = Celery(
    "lastwar_bot",
    broker=_REDIS_URL,
    backend=_REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    result_expires=3600,
    timezone=_TIMEZONE,
    enable_utc=True,
)


# -- Bot-Konfigurationen ------------------------------------------------------
# Netcup vServer 8GB RAM -> max 2 Emulatoren stabil (je 1.5GB + System-Overhead)

BOT_CONFIGS = [
    BotConfig(device_serial="emulator-5556", bot_id=1, account_name="JuniorCat"),
    BotConfig(device_serial="emulator-5558", bot_id=2, account_name=""),
]

_BOT_MAP: dict[int, BotConfig] = {c.bot_id: c for c in BOT_CONFIGS}

# -- Tasks ---------------------------------------------------------------------


@app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_bot_daily(self, bot_id: int) -> dict:
    """Daily Routine fuer einen Bot."""
    config = _BOT_MAP[bot_id]
    metrics = RunMetrics(bot_id=bot_id)
    try:
        with LastWarBot(config) as bot:
            results = bot.run_daily_routine()
        metrics.finish(results)
        write_metrics(metrics)
        return {"bot_id": bot_id, "status": "success", "results": results}
    except Exception as exc:
        logger.error("Bot %d: Fehler -- %s", bot_id, exc)
        metrics.finish({"run": f"fail: {exc}"})
        write_metrics(metrics)
        raise self.retry(exc=exc) from exc


@app.task
def run_all_bots_daily() -> None:
    """Startet alle aktiven Bots (account_name gesetzt) parallel."""
    for config in BOT_CONFIGS:
        if config.account_name:
            run_bot_daily.delay(config.bot_id)
        else:
            logger.info(
                "Bot %d: uebersprungen (kein account_name konfiguriert)",
                config.bot_id,
            )


@app.task
def validate_all_templates() -> dict:
    """Pre-flight: prueft ob alle Templates vorhanden sind (ohne ADB-Verbindung)."""
    results = {}
    for config in BOT_CONFIGS:
        if not config.account_name:
            results[f"bot_{config.bot_id}"] = {
                "ok": None, "missing": [], "skipped": True
            }
            continue
        missing = [
            name for name in LastWarBot.REQUIRED_TEMPLATES
            if not (config.templates_dir / f"{name}.png").exists()
        ]
        results[f"bot_{config.bot_id}"] = {
            "ok": len(missing) == 0,
            "missing": missing,
            "skipped": False,
        }
    logger.info("Template-Validierung: %s", results)
    return results


@app.task
def health_check() -> dict:
    """Prueft ADB-Verbindung aller 3 Emulatoren."""
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    devices = [
        line.split("\t")[0]
        for line in result.stdout.strip().splitlines()[1:]
        if "device" in line
    ]
    status = {
        f"bot_{i+1}": (config.device_serial in devices)
        for i, config in enumerate(BOT_CONFIGS)
    }
    logger.info("Health Check: %s", status)
    return status


# -- Celery Beat Schedule ------------------------------------------------------

app.conf.beat_schedule = {
    # Morgendliche Routine: 06:00 Uhr
    "daily-routine-morning": {
        "task": "bot.tasks.run_all_bots_daily",
        "schedule": crontab(hour=6, minute=0),
    },
    # Mittag-Routine: 12:30 Uhr (Ressourcen + Heilen)
    "daily-routine-midday": {
        "task": "bot.tasks.run_all_bots_daily",
        "schedule": crontab(hour=12, minute=30),
    },
    # Abend-Routine: 20:00 Uhr
    "daily-routine-evening": {
        "task": "bot.tasks.run_all_bots_daily",
        "schedule": crontab(hour=20, minute=0),
    },
    # Health Check alle 15 Minuten
    "health-check": {
        "task": "bot.tasks.health_check",
        "schedule": crontab(minute="*/15"),
    },
}
