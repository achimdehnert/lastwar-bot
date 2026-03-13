#!/bin/bash
# =============================================================================
# start_emulators.sh -- Alle 3 AVDs headless starten (Software Emulation)
# Kein KVM -- verwendet -accel off + swiftshader_indirect
# Boot-Timeout: 5 Min (laenger wegen Software-Emulation)
# =============================================================================
set -euo pipefail

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/android-sdk}"
export PATH="$PATH:$ANDROID_SDK_ROOT/emulator:$ANDROID_SDK_ROOT/platform-tools"

# AVD -> ADB-Port Mapping
declare -A AVD_PORTS=(
  [lastwar-bot-1]=5554
  [lastwar-bot-2]=5556
  [lastwar-bot-3]=5558
)

echo "$(date): Starte Last War Emulatoren (Software Emulation)..."

for AVD_NAME in "${!AVD_PORTS[@]}"; do
  PORT="${AVD_PORTS[$AVD_NAME]}"
  SERIAL="emulator-${PORT}"

  # Bereits laufend?
  if adb devices 2>/dev/null | grep -q "$SERIAL"; then
    echo "OK: $AVD_NAME (Port $PORT) laeuft bereits"
    continue
  fi

  echo "  Starte $AVD_NAME auf Port $PORT (no-accel)..."
  nohup emulator \
    -avd "$AVD_NAME" \
    -port "$PORT" \
    -no-audio \
    -no-window \
    -no-snapshot \
    -no-boot-anim \
    -accel off \
    -gpu swiftshader_indirect \
    -memory 2048 \
    -cores 2 \
    > "/var/log/emulator-${AVD_NAME}.log" 2>&1 &

  echo "  PID: $!"
  sleep 5
done

echo "Warte auf Boot aller Emulatoren (Software-Emulation, kann 3-5 Min dauern)..."

for AVD_NAME in "${!AVD_PORTS[@]}"; do
  PORT="${AVD_PORTS[$AVD_NAME]}"
  SERIAL="emulator-${PORT}"
  TIMEOUT=300
  ELAPSED=0

  until adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    if [ $ELAPSED -ge $TIMEOUT ]; then
      echo "FEHLER: $AVD_NAME Timeout nach ${TIMEOUT}s"
      echo "  Log: /var/log/emulator-${AVD_NAME}.log"
      tail -20 "/var/log/emulator-${AVD_NAME}.log" 2>/dev/null
      exit 1
    fi
    echo "  Warte auf $AVD_NAME... (${ELAPSED}s / ${TIMEOUT}s)"
  done

  echo "OK: $AVD_NAME bereit (${ELAPSED}s)"
done

echo "$(date): Alle 3 Emulatoren bereit."
adb devices
