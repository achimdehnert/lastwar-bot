"""
bot/metrics.py -- Structured Run Metrics (Phase 4 Prep)
Schreibt JSON-Lines Log fuer einfaches Monitoring und Alerting.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_METRICS_DIR = Path(__file__).parent.parent / "logs"


@dataclass
class RunMetrics:
    """Metriken einer einzelnen Bot-Run-Ausfuehrung."""
    bot_id: int
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    duration_seconds: float = 0.0
    steps_ok: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def finish(self, results: dict[str, str]) -> None:
        """Ergebnis-Dict von run_daily_routine auswerten."""
        self.finished_at = time.time()
        self.duration_seconds = round(self.finished_at - self.started_at, 1)
        for step_name, status in results.items():
            if status == "ok":
                self.steps_ok += 1
            elif status == "skipped":
                self.steps_skipped += 1
            else:
                self.steps_failed += 1
                self.errors.append(f"{step_name}: {status}")

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def write_metrics(metrics: RunMetrics, path: Path | None = None) -> Path:
    """Metriken als JSON-Line an metrics.jsonl anhaengen."""
    _METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out = path or (_METRICS_DIR / "metrics.jsonl")
    line = metrics.to_json() + "\n"
    with open(out, "a", encoding="utf-8") as f:
        f.write(line)
    logger.info(
        "Bot %d: Metriken geschrieben (%.1fs, %d ok, %d fail, %d skipped)",
        metrics.bot_id,
        metrics.duration_seconds,
        metrics.steps_ok,
        metrics.steps_failed,
        metrics.steps_skipped,
    )
    return out
