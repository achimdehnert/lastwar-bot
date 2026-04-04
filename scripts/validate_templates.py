#!/usr/bin/env python3
"""
validate_templates.py -- CLI Template-Validierung + Qualitaets-Report

Prueft ob alle 17 Required Templates vorhanden sind,
analysiert Bildqualitaet (Groesse, Aufloesung, Kontrast).

Aufruf:
  python3 scripts/validate_templates.py [--templates-dir templates/]
  python3 scripts/validate_templates.py --create-checklist
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Required templates aus bot/core.py
REQUIRED_TEMPLATES = [
    "btn_home",
    "btn_collect_all",
    "btn_confirm",
    "btn_world_map",
    "icon_resource_tile",
    "btn_gather",
    "btn_march",
    "icon_zombie",
    "btn_attack",
    "result_victory",
    "btn_barracks",
    "btn_train_max",
    "btn_daily_tasks",
    "btn_collect_rewards",
    "icon_wounded_indicator",
    "btn_hospital",
    "btn_heal_all",
]

# Empfohlene Mindestgroessen (Breite x Hoehe in Pixeln)
MIN_WIDTH = 30
MIN_HEIGHT = 30
MAX_WIDTH = 400
MAX_HEIGHT = 400


def check_image_quality(path: Path) -> dict:
    """Bildqualitaet pruefen (Groesse, Format, Dimensionen)."""
    result = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return result

    size_bytes = path.stat().st_size
    result["size_bytes"] = size_bytes
    result["size_ok"] = size_bytes > 100  # Nicht leer / korrupt

    try:
        import cv2
        img = cv2.imread(str(path))
        if img is None:
            result["readable"] = False
            return result
        result["readable"] = True
        h, w = img.shape[:2]
        result["width"] = w
        result["height"] = h
        result["dimensions_ok"] = (
            MIN_WIDTH <= w <= MAX_WIDTH and MIN_HEIGHT <= h <= MAX_HEIGHT
        )

        # Kontrast-Check (Standardabweichung der Grauwerte)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        std_dev = float(gray.std())
        result["contrast_std"] = round(std_dev, 1)
        result["contrast_ok"] = std_dev > 15  # Zu wenig Kontrast = schlechtes Template

    except ImportError:
        # OpenCV nicht verfuegbar -- nur Datei-Checks
        try:
            from PIL import Image
            img = Image.open(path)
            w, h = img.size
            result["readable"] = True
            result["width"] = w
            result["height"] = h
            result["dimensions_ok"] = (
                MIN_WIDTH <= w <= MAX_WIDTH and MIN_HEIGHT <= h <= MAX_HEIGHT
            )
        except Exception:
            result["readable"] = False

    return result


def validate(templates_dir: Path) -> int:
    """Alle Templates pruefen. Return: Anzahl Fehler."""
    print(f"Templates-Verzeichnis: {templates_dir}")
    print(f"Erforderliche Templates: {len(REQUIRED_TEMPLATES)}")
    print("-" * 60)

    errors = 0
    warnings = 0

    for name in REQUIRED_TEMPLATES:
        path = templates_dir / f"{name}.png"
        info = check_image_quality(path)

        if not info.get("exists"):
            print(f"  FEHLT   {name}.png")
            errors += 1
            continue

        if not info.get("readable"):
            print(f"  DEFEKT  {name}.png (nicht lesbar)")
            errors += 1
            continue

        issues = []
        if not info.get("size_ok"):
            issues.append("zu klein (<100 bytes)")
        if not info.get("dimensions_ok", True):
            w, h = info.get("width", 0), info.get("height", 0)
            issues.append(f"Groesse {w}x{h} ausserhalb {MIN_WIDTH}-{MAX_WIDTH}px")
        if not info.get("contrast_ok", True):
            issues.append(f"geringer Kontrast (std={info.get('contrast_std', 0)})")

        if issues:
            print(f"  WARN    {name}.png -- {', '.join(issues)}")
            warnings += 1
        else:
            w = info.get("width", "?")
            h = info.get("height", "?")
            print(f"  OK      {name}.png ({w}x{h})")

    print("-" * 60)
    total = len(REQUIRED_TEMPLATES)
    ok = total - errors - warnings
    print(f"Ergebnis: {ok}/{total} OK, {warnings} Warnungen, {errors} Fehler")

    if errors > 0:
        print(f"\n{errors} fehlende/defekte Templates -- Bot kann NICHT starten!")
        return 1
    if warnings > 0:
        print(f"\n{warnings} Warnungen -- Bot startet, Erkennung evtl. unzuverlaessig")
    else:
        print("\nAlle Templates OK -- Bot startbereit!")
    return 0


def create_checklist(templates_dir: Path) -> None:
    """Checklist-Datei fuer Template-Erstellung ausgeben."""
    print("# Template-Erstellungs-Checkliste")
    print(f"# Zielverzeichnis: {templates_dir}")
    print("#")
    print("# Workflow pro Template:")
    print("#   1. Spiel auf gewuenschten Screen navigieren")
    print("#   2. bash scripts/capture_template.sh 1 <name>")
    print("#   3. Koordinaten notieren (x y w h)")
    print("#   4. bash scripts/capture_template.sh 1 <name> x y w h")
    print("#   5. Template validieren: python3 scripts/validate_templates.py")
    print("#")
    for name in REQUIRED_TEMPLATES:
        path = templates_dir / f"{name}.png"
        status = "vorhanden" if path.exists() else "FEHLT"
        category = "Button" if name.startswith("btn_") else (
            "Icon" if name.startswith("icon_") else "Screen"
        )
        print(f"- [ ] {name}.png  ({category})  [{status}]")


def main() -> int:
    parser = argparse.ArgumentParser(description="Template-Validierung")
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=Path(__file__).parent.parent / "templates",
        help="Pfad zum Templates-Verzeichnis",
    )
    parser.add_argument(
        "--create-checklist",
        action="store_true",
        help="Checklist fuer Template-Erstellung ausgeben",
    )
    args = parser.parse_args()

    if args.create_checklist:
        create_checklist(args.templates_dir)
        return 0

    return validate(args.templates_dir)


if __name__ == "__main__":
    sys.exit(main())
