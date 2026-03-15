#!/bin/bash
# =============================================================================
# health_check.sh -- ADB-Verbindung und Emulator-Status pruefen + Auto-Restart
# Aufruf: bash scripts/health_check.sh [--restart]
# =============================================================================

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/android-sdk}"
export PATH="$PATH:$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/emulator"

BOT_DIR="${BOT_DIR:-$HOME/lastwar-bot}"
AUTO_RESTART=0
[[ "${1:-}" == "--restart" ]] && AUTO_RESTART=1

echo "=== Last War Bot Health Check === $(date)"
echo ""

FAILED=0

AVD_NAMES=("lastwar-bot-1" "lastwar-bot-2" "lastwar-bot-3")
AVD_PORTS=(5554 5556 5558)

for i in 0 1 2; do
  AVD="${AVD_NAMES[$i]}"
  PORT="${AVD_PORTS[$i]}"
  SERIAL="emulator-${PORT}"
  BOT_NUM=$((i + 1))

  if adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
    UPTIME=$(adb -s "$SERIAL" shell uptime 2>/dev/null | head -1)
    echo "OK: Bot $BOT_NUM ($SERIAL): RUNNING -- $UPTIME"
  else
    echo "FAIL: Bot $BOT_NUM ($SERIAL): DOWN"
    FAILED=$((FAILED + 1))
    if [ $AUTO_RESTART -eq 1 ]; then
      echo "  --> Starte $AVD neu..."
      nohup emulator \
        -avd "$AVD" \
        -port "$PORT" \
        -no-audio -no-window -no-snapshot -no-boot-anim \
        -accel off -gpu swiftshader_indirect \
        -memory 2048 -cores 2 \
        > "/var/log/emulator-${AVD}.log" 2>&1 &
      echo "  --> PID: $! (Boot kann 3-5 Min dauern)"
    fi
  fi
done

echo ""

# Redis
if redis-cli ping 2>/dev/null | grep -q PONG; then
  echo "OK: Redis"
else
  echo "FAIL: Redis DOWN"
  FAILED=$((FAILED + 1))
  if [ $AUTO_RESTART -eq 1 ]; then
    echo "  --> Starte Redis neu..."
    systemctl restart redis-server
  fi
fi

# Celery Worker
if systemctl is-active --quiet lastwar-celery 2>/dev/null; then
  echo "OK: Celery Worker"
else
  echo "FAIL: Celery Worker DOWN"
  FAILED=$((FAILED + 1))
  if [ $AUTO_RESTART -eq 1 ]; then
    echo "  --> Starte Celery Worker neu..."
    systemctl restart lastwar-celery
  fi
fi

# Celery Beat
if systemctl is-active --quiet lastwar-beat 2>/dev/null; then
  echo "OK: Celery Beat"
else
  echo "FAIL: Celery Beat DOWN"
  FAILED=$((FAILED + 1))
  if [ $AUTO_RESTART -eq 1 ]; then
    echo "  --> Starte Celery Beat neu..."
    systemctl restart lastwar-beat
  fi
fi

echo ""
if [ $FAILED -eq 0 ]; then
  echo "=== ALL OK ==="
  exit 0
else
  echo "=== $FAILED FAILURES ==="
  [ $AUTO_RESTART -eq 1 ] && echo "(Auto-Restart wurde ausgefuehrt)"
  exit 1
fi
