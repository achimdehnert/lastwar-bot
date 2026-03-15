#!/bin/bash
# =============================================================================
# deploy.sh -- Code-Updates auf den Server pushen und Services neu starten
# Aufruf: bash scripts/deploy.sh [SERVER_IP]
# Voraussetzung: SSH-Key ist auf dem Server hinterlegt
# =============================================================================
set -euo pipefail

SERVER_IP="${1:-204.168.149.6}"
SERVER_USER="${SERVER_USER:-root}"
BOT_DIR="${BOT_DIR:-/root/lastwar-bot}"
BRANCH="${BRANCH:-main}"

echo "=== Last War Bot Deploy === $(date)"
echo "Server: ${SERVER_USER}@${SERVER_IP}"
echo "Dir:    ${BOT_DIR}"
echo "Branch: ${BRANCH}"
echo ""

SSH="ssh -o StrictHostKeyChecking=accept-new ${SERVER_USER}@${SERVER_IP}"

# -----------------------------------------------------------------------------
# 1. Code auf Server aktualisieren
# -----------------------------------------------------------------------------
echo "[1/4] Code-Update (git pull)..."
$SSH bash << REMOTE
  set -euo pipefail
  cd "${BOT_DIR}"
  git fetch origin
  git checkout "${BRANCH}"
  git pull origin "${BRANCH}"
  echo "OK: $(git log -1 --oneline)"
REMOTE

# -----------------------------------------------------------------------------
# 2. Python Dependencies aktualisieren
# -----------------------------------------------------------------------------
echo "[2/4] Dependencies aktualisieren..."
$SSH bash << REMOTE
  set -euo pipefail
  cd "${BOT_DIR}"
  source .venv/bin/activate
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  echo "OK: Dependencies aktuell"
REMOTE

# -----------------------------------------------------------------------------
# 3. Celery Worker + Beat neu starten
# -----------------------------------------------------------------------------
echo "[3/4] Services neu starten..."
$SSH bash << REMOTE
  set -euo pipefail
  systemctl restart lastwar-celery
  systemctl restart lastwar-beat
  sleep 3
  systemctl is-active lastwar-celery && echo "OK: Celery Worker laeuft"
  systemctl is-active lastwar-beat   && echo "OK: Celery Beat laeuft"
REMOTE

# -----------------------------------------------------------------------------
# 4. Health Check
# -----------------------------------------------------------------------------
echo "[4/4] Health Check..."
$SSH bash "${BOT_DIR}/scripts/health_check.sh" || true

echo ""
echo "=== Deploy abgeschlossen ==="
