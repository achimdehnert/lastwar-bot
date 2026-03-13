#!/bin/bash
# =============================================================================
# health_check.sh -- ADB-Verbindung und Emulator-Status pruefen
# =============================================================================

export PATH="$PATH:${ANDROID_SDK_ROOT:-$HOME/android-sdk}/platform-tools"

echo "=== Last War Bot Health Check === $(date)"
echo ""

FAILED=0

for i in 1 2 3; do
  PORT=$((5552 + i * 2))
  SERIAL="emulator-${PORT}"
  AVD="lastwar-bot-${i}"

  if adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
    UPTIME=$(adb -s "$SERIAL" shell uptime 2>/dev/null | head -1)
    echo "OK: Bot $i ($SERIAL): RUNNING -- $UPTIME"
  else
    echo "FAIL: Bot $i ($SERIAL): DOWN"
    FAILED=$((FAILED + 1))
  fi
done

echo ""

# Redis
if redis-cli ping 2>/dev/null | grep -q PONG; then
  echo "OK: Redis"
else
  echo "FAIL: Redis DOWN"
  FAILED=$((FAILED + 1))
fi

# Celery
if systemctl is-active --quiet lastwar-celery 2>/dev/null; then
  echo "OK: Celery Worker"
else
  echo "FAIL: Celery Worker DOWN"
  FAILED=$((FAILED + 1))
fi

if systemctl is-active --quiet lastwar-beat 2>/dev/null; then
  echo "OK: Celery Beat"
else
  echo "FAIL: Celery Beat DOWN"
  FAILED=$((FAILED + 1))
fi

echo ""
if [ $FAILED -eq 0 ]; then
  echo "=== ALL OK ==="
  exit 0
else
  echo "=== $FAILED FAILURES ==="
  exit 1
fi
