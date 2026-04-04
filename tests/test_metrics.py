"""
tests/test_metrics.py -- Unit Tests fuer RunMetrics und write_metrics
"""
from __future__ import annotations

import json
from pathlib import Path

from bot.metrics import RunMetrics, write_metrics


def test_should_finish_with_all_ok():
    m = RunMetrics(bot_id=1)
    m.finish({"step1": "ok", "step2": "ok", "step3": "ok"})
    assert m.steps_ok == 3
    assert m.steps_failed == 0
    assert m.steps_skipped == 0
    assert m.duration_seconds >= 0
    assert m.errors == []


def test_should_count_failures_and_skips():
    m = RunMetrics(bot_id=2)
    m.finish({
        "step1": "ok",
        "step2": "fail: timeout",
        "step3": "skipped",
    })
    assert m.steps_ok == 1
    assert m.steps_failed == 1
    assert m.steps_skipped == 1
    assert len(m.errors) == 1
    assert "step2" in m.errors[0]


def test_should_serialize_to_json():
    m = RunMetrics(bot_id=1)
    m.finish({"step1": "ok"})
    data = json.loads(m.to_json())
    assert data["bot_id"] == 1
    assert data["steps_ok"] == 1
    assert "started_at" in data
    assert "finished_at" in data


def test_should_write_metrics_file(tmp_path: Path):
    m = RunMetrics(bot_id=1)
    m.finish({"step1": "ok", "step2": "fail: err"})
    out = write_metrics(m, path=tmp_path / "metrics.jsonl")
    assert out.exists()
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["bot_id"] == 1
    assert data["steps_ok"] == 1
    assert data["steps_failed"] == 1


def test_should_append_multiple_metrics(tmp_path: Path):
    outfile = tmp_path / "metrics.jsonl"
    for i in range(3):
        m = RunMetrics(bot_id=i + 1)
        m.finish({"step": "ok"})
        write_metrics(m, path=outfile)
    lines = outfile.read_text().strip().splitlines()
    assert len(lines) == 3
