#!/bin/bash
# =============================================================================
# capture_template.sh -- Template-Screenshot von einem Emulator aufnehmen
# Aufruf: bash scripts/capture_template.sh <bot_nr> <template_name> [x y w h]
#
# Ohne Koordinaten: Vollbild-Screenshot + interaktive Crop-Anleitung
# Mit Koordinaten:  Direkt zuschneiden und als Template speichern
#
# Beispiele:
#   bash scripts/capture_template.sh 1 btn_collect_all
#   bash scripts/capture_template.sh 1 btn_collect_all 540 1200 200 80
# =============================================================================
set -euo pipefail

export PATH="$PATH:${ANDROID_SDK_ROOT:-$HOME/android-sdk}/platform-tools"

BOT_NR="${1:-}"
TEMPLATE_NAME="${2:-}"

if [ -z "$BOT_NR" ] || [ -z "$TEMPLATE_NAME" ]; then
  echo "Aufruf: $0 <bot_nr> <template_name> [x y w h]"
  echo "  bot_nr:        1, 2 oder 3"
  echo "  template_name: z.B. btn_collect_all (ohne .png)"
  echo "  x y w h:       optionaler Crop-Bereich in Pixeln"
  exit 1
fi

BOT_DIR="${BOT_DIR:-$(dirname "$(dirname "$(realpath "$0")")")}"
PORT=$((5552 + BOT_NR * 2))
SERIAL="emulator-${PORT}"
TEMPLATES_DIR="$BOT_DIR/templates"
SCREENSHOTS_DIR="$BOT_DIR/screenshots"

mkdir -p "$TEMPLATES_DIR" "$SCREENSHOTS_DIR"

# Verbindung pruefen
if ! adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
  echo "FEHLER: Emulator $SERIAL nicht erreichbar"
  exit 1
fi

# Screenshot aufnehmen
RAW_SHOT="$SCREENSHOTS_DIR/capture_bot${BOT_NR}_$(date +%s).png"
echo "Screenshot von $SERIAL..."
adb -s "$SERIAL" exec-out screencap -p > "$RAW_SHOT"
echo "OK: $RAW_SHOT"

TEMPLATE_FILE="$TEMPLATES_DIR/${TEMPLATE_NAME}.png"

if [ $# -ge 6 ]; then
  # Direkter Crop mit Koordinaten
  X="$3"; Y="$4"; W="$5"; H="$6"
  echo "Schneide aus: x=$X y=$Y w=$W h=$H..."
  if command -v convert &>/dev/null; then
    convert "$RAW_SHOT" -crop "${W}x${H}+${X}+${Y}" +repage "$TEMPLATE_FILE"
    echo "OK: Template gespeichert: $TEMPLATE_FILE"
  elif command -v python3 &>/dev/null; then
    python3 - "$RAW_SHOT" "$TEMPLATE_FILE" "$X" "$Y" "$W" "$H" << 'PYEOF'
import sys
from PIL import Image
src, dst, x, y, w, h = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
img = Image.open(src)
img.crop((x, y, x + w, y + h)).save(dst)
print(f"OK: {dst}")
PYEOF
  else
    echo "FEHLER: weder ImageMagick (convert) noch Python3 verfuegbar"
    exit 1
  fi
else
  # Vollbild -- Anleitung ausgeben
  echo ""
  echo "Vollbild-Screenshot gespeichert: $RAW_SHOT"
  echo ""
  echo "Naechste Schritte:"
  echo "  1. Screenshot oeffnen und Koordinaten des gewuenschten Bereichs notieren"
  echo "     (x, y = obere linke Ecke; w, h = Breite, Hoehe)"
  echo ""
  echo "  2. Template ausschneiden:"
  echo "     bash $0 $BOT_NR $TEMPLATE_NAME <x> <y> <w> <h>"
  echo ""
  echo "  Oder mit ImageMagick manuell:"
  echo "     convert '$RAW_SHOT' -crop WxH+X+Y +repage '$TEMPLATE_FILE'"
fi
