"""
bot -- Last War: Survival Bot Package
"""
import logging
import logging.handlers
from pathlib import Path

__all__ = ["BotConfig", "LastWarBot", "MatchResult", "RunMetrics"]

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(level: int = logging.INFO) -> None:
    """Zentrales Logging-Setup: Console + rotierendes File-Log."""
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s -- %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_DIR / "lastwar-bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(console)
        root.addHandler(file_handler)
