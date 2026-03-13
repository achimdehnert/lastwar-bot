#!/bin/bash
# =============================================================================
# stop_emulators.sh -- Alle Emulatoren sauber herunterfahren
# =============================================================================
set -euo pipefail

export PATH="$PATH:${ANDROID_SDK_ROOT:-$HOME/android-sdk}/platform-tools"

echo "$(date): Stoppe Last War Emulatoren..."

for SERIAL in emulator-5554 emulator-5556 emulator-5558; do
  if adb devices | grep -q "$SERIAL"; then
    echo "  Stoppe $SERIAL..."
    adb -s "$SERIAL" emu kill 2>/dev/null || true
  fi
done

# Warte auf sauberes Beenden
sleep 5
echo "$(date): Alle Emulatoren gestoppt."
adb devices
