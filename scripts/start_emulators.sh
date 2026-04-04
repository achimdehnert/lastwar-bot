#!/bin/bash
# =============================================================================
# start_emulators.sh -- Alle 3 AVDs headless starten (Software Emulation)
# Kein KVM -- verwendet -accel off + swiftshader_indirect
# Boot-Timeout: 5 Min (laenger wegen Software-Emulation)
# =============================================================================
set -euo pipefail

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/android-sdk}"
export PATH="$PATH:$ANDROID_SDK_ROOT/emulator:$ANDROID_SDK_ROOT/platform-tools"

# AVD -> ADB-Port Mapping (geordnet: Index 0=bot1/5554, 1=bot2/5556, 2=bot3/5558)
AVD_NAMES=("lastwar-bot-1" "lastwar-bot-2" "lastwar-bot-3")
AVD_PORTS=(5554 5556 5558)

echo "$(date): Starte Last War Emulatoren (Software Emulation)..."

for i in 0 1 2; do
  AVD_NAME="${AVD_NAMES[$i]}"
  PORT="${AVD_PORTS[$i]}"
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
    -memory 1536 \
    -cores 1 \
    > "/var/log/emulator-${AVD_NAME}.log" 2>&1 &

  echo "  PID: $!"
  sleep 5
done

echo "Warte auf Boot aller Emulatoren (Software-Emulation, kann 3-5 Min dauern)..."

for i in 0 1 2; do
  AVD_NAME="${AVD_NAMES[$i]}"
  PORT="${AVD_PORTS[$i]}"
  SERIAL="emulator-${PORT}"
  TIMEOUT=300
  ELAPSED=0

  # Android 34 + Software-Emulation setzt sys.boot_completed nicht zuverlaessig.
  # Pruefe stattdessen ob bootanim gestoppt ist (= UI bereit).
  until adb -s "$SERIAL" shell getprop init.svc.bootanim 2>/dev/null | grep -q "stopped"; do
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
