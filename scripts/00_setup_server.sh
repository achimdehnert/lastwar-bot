#!/bin/bash
# =============================================================================
# Phase 0: Last War Bot Server Setup
# Target: Netcup vServer, Debian 13 (trixie)
# Mode:   Software Emulation (kein KVM -- Netcup vServer hat kein nested virt)
# Usage:  sudo bash scripts/00_setup_server.sh
# =============================================================================
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

LOG="/var/log/lastwar-setup.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== Last War Bot Server Setup === $(date)"

# -----------------------------------------------------------------------------
# 1. System-Dependencies
# -----------------------------------------------------------------------------
echo "[1/8] Installiere System-Dependencies..."
apt-get update -qq
apt-get install -y \
  openjdk-21-jdk-headless \
  wget unzip curl git \
  python3 python3-venv python3-pip \
  libgl1 libglx-mesa0 libglib2.0-0 libpulse0 \
  tesseract-ocr tesseract-ocr-deu \
  adb \
  screen \
  htop \
  redis-server

# Redis fuer Celery aktivieren
systemctl enable --now redis-server
echo "OK: System-Dependencies + Redis installiert"

# -----------------------------------------------------------------------------
# 2. Python 3.12 (nativ auf Ubuntu 24.04)
# -----------------------------------------------------------------------------
echo "[2/8] Pruefe Python 3..."
PYTHON=$(command -v python3)
$PYTHON --version
echo "OK: $($PYTHON --version) verfuegbar"

# -----------------------------------------------------------------------------
# 3. Android SDK
# -----------------------------------------------------------------------------
echo "[3/8] Installiere Android SDK..."
ANDROID_SDK="$HOME/android-sdk"
mkdir -p "$ANDROID_SDK/cmdline-tools"

if [ ! -f "$ANDROID_SDK/cmdline-tools/latest/bin/sdkmanager" ]; then
  cd "$ANDROID_SDK/cmdline-tools"
  wget -q "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip" -O tools.zip
  unzip -q tools.zip
  mv cmdline-tools latest
  rm tools.zip
fi

# Env-Variablen setzen (idempotent)
if ! grep -q 'ANDROID_SDK_ROOT' "$HOME/.bashrc" 2>/dev/null; then
  cat >> "$HOME/.bashrc" << 'ENVEOF'

# Android SDK
export ANDROID_SDK_ROOT=$HOME/android-sdk
export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_SDK_ROOT/platform-tools
export PATH=$PATH:$ANDROID_SDK_ROOT/emulator
ENVEOF
fi

export ANDROID_SDK_ROOT="$ANDROID_SDK"
export PATH="$PATH:$ANDROID_SDK/cmdline-tools/latest/bin:$ANDROID_SDK/platform-tools:$ANDROID_SDK/emulator"

echo "[3/8] Installiere SDK-Packages (ca. 3 GB Download)..."
yes | sdkmanager --licenses > /dev/null 2>&1 || true
sdkmanager \
  "emulator" \
  "platform-tools" \
  "system-images;android-34;google_apis;x86_64"

echo "OK: Android SDK installiert"

# -----------------------------------------------------------------------------
# 4. 3 AVDs erstellen
# -----------------------------------------------------------------------------
echo "[4/8] Erstelle 3 AVDs..."
for i in 1 2 3; do
  AVD_NAME="lastwar-bot-${i}"
  if ! avdmanager list avd 2>/dev/null | grep -q "$AVD_NAME"; then
    echo "no" | avdmanager create avd \
      -n "$AVD_NAME" \
      -k "system-images;android-34;google_apis;x86_64" \
      --device "pixel_6" \
      --force
    echo "OK: AVD $AVD_NAME erstellt"
  else
    echo "OK: AVD $AVD_NAME bereits vorhanden"
  fi
done

# RAM + Disk pro Emulator konfigurieren
for i in 1 2 3; do
  AVD_CONFIG="$HOME/.android/avd/lastwar-bot-${i}.avd/config.ini"
  if [ -f "$AVD_CONFIG" ]; then
    sed -i '/^hw.ramSize=/d' "$AVD_CONFIG"
    sed -i '/^disk.dataPartition.size=/d' "$AVD_CONFIG"
    sed -i '/^hw.lcd.density=/d' "$AVD_CONFIG"
    sed -i '/^hw.lcd.width=/d' "$AVD_CONFIG"
    sed -i '/^hw.lcd.height=/d' "$AVD_CONFIG"
    sed -i '/^hw.cpu.ncore=/d' "$AVD_CONFIG"
    echo "hw.ramSize=1536" >> "$AVD_CONFIG"
    echo "disk.dataPartition.size=4G" >> "$AVD_CONFIG"
    echo "hw.lcd.density=240" >> "$AVD_CONFIG"
    echo "hw.lcd.width=1080" >> "$AVD_CONFIG"
    echo "hw.lcd.height=1920" >> "$AVD_CONFIG"
    echo "hw.cpu.ncore=1" >> "$AVD_CONFIG"
  fi
done
echo "OK: AVDs konfiguriert (1536 MB RAM, 1 core, 1080x1920)"

# -----------------------------------------------------------------------------
# 5. Bot-Verzeichnis + Python venv
# -----------------------------------------------------------------------------
echo "[5/8] Erstelle Bot-Umgebung..."
BOT_DIR="$HOME/lastwar-bot"
mkdir -p "$BOT_DIR"/{templates,screenshots,logs}
cd "$BOT_DIR"

if [ ! -d "$BOT_DIR/.venv" ]; then
  $PYTHON -m venv .venv
fi
source .venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet -r "$BOT_DIR/requirements.txt"

# .env aus Vorlage erstellen falls noch nicht vorhanden
if [ ! -f "$BOT_DIR/.env" ]; then
  cp "$BOT_DIR/.env.example" "$BOT_DIR/.env"
  echo "OK: .env aus .env.example erstellt -- bitte anpassen!"
else
  echo "OK: .env bereits vorhanden"
fi

# Scripts ausfuehrbar machen
chmod +x "$BOT_DIR/scripts/"*.sh
echo "OK: Scripts ausfuehrbar gemacht"

echo "OK: Python venv + Dependencies installiert"

# -----------------------------------------------------------------------------
# 6. Systemd Services
# -----------------------------------------------------------------------------
echo "[6/8] Erstelle Systemd-Services..."

cat > /etc/systemd/system/lastwar-emulators.service << EOF
[Unit]
Description=Last War Android Emulators (3 instances, software accel)
After=network.target

[Service]
Type=forking
User=root
Environment=ANDROID_SDK_ROOT=$HOME/android-sdk
Environment=PATH=$HOME/android-sdk/emulator:$HOME/android-sdk/platform-tools:/usr/local/bin:/usr/bin:/bin
ExecStart=$BOT_DIR/scripts/start_emulators.sh
ExecStop=$BOT_DIR/scripts/stop_emulators.sh
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/lastwar-celery.service << EOF
[Unit]
Description=Last War Bot Celery Worker
After=redis-server.service lastwar-emulators.service

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
EnvironmentFile=$BOT_DIR/.env
Environment=PATH=$BOT_DIR/.venv/bin:$HOME/android-sdk/platform-tools:/usr/local/bin:/usr/bin:/bin
ExecStart=$BOT_DIR/.venv/bin/celery -A bot.tasks worker --loglevel=info --logfile=$BOT_DIR/logs/celery-worker.log
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/lastwar-beat.service << EOF
[Unit]
Description=Last War Bot Celery Beat Scheduler
After=lastwar-celery.service

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
EnvironmentFile=$BOT_DIR/.env
Environment=PATH=$BOT_DIR/.venv/bin:$HOME/android-sdk/platform-tools:/usr/local/bin:/usr/bin:/bin
ExecStart=$BOT_DIR/.venv/bin/celery -A bot.tasks beat --loglevel=info --logfile=$BOT_DIR/logs/celery-beat.log
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "OK: Systemd-Services registriert (noch nicht aktiviert)"

# -----------------------------------------------------------------------------
# 7. Cron-basiertes Monitoring (Auto-Restart alle 5 Minuten)
# -----------------------------------------------------------------------------
echo "[7/8] Richte Monitoring-Cron ein..."
CRON_JOB="*/5 * * * * BOT_DIR=${BOT_DIR} bash ${BOT_DIR}/scripts/health_check.sh --restart >> ${BOT_DIR}/logs/health_check.log 2>&1"
# Idempotent: nur hinzufuegen wenn noch nicht vorhanden
( crontab -l 2>/dev/null | grep -v 'health_check.sh'; echo "$CRON_JOB" ) | crontab -
echo "OK: Cron eingerichtet (health_check --restart alle 5 Min)"

# -----------------------------------------------------------------------------
# 8. Firewall
# -----------------------------------------------------------------------------
echo "[8/8] Konfiguriere Firewall..."
if command -v ufw &>/dev/null; then
  ufw allow ssh
  ufw --force enable
  echo "OK: UFW aktiv (nur SSH erlaubt)"
fi

echo ""
echo "======================================"
echo "=== Setup abgeschlossen ==="
echo "======================================"
echo ""
echo "Server:   $(hostname) ($(curl -s ifconfig.me))"
echo "Mode:     Software Emulation (kein KVM)"
echo "Python:   $(python3.12 --version)"
echo "Redis:    $(redis-cli ping)"
echo "SDK:      $ANDROID_SDK_ROOT"
echo "AVDs:     $(avdmanager list avd 2>/dev/null | grep 'Name:' | wc -l)"
echo ""
echo "Naechste Schritte:"
echo "  1. source ~/.bashrc"
echo "  2. bash scripts/start_emulators.sh"
echo "  3. Last War APK installieren:"
echo "     adb -s emulator-5554 install lastwar.apk"
echo "  4. Accounts manuell einrichten (scrcpy)"
echo "  5. systemctl enable --now lastwar-emulators"
echo "  6. systemctl enable --now lastwar-celery lastwar-beat"
