# Last War: Survival Bot Platform

3 parallele Bot-Instanzen auf Hetzner CX43.

## Server

| Spec | Wert |
|---|---|
| Typ | Hetzner CX43 |
| IP | 204.168.149.6 |
| Location | Helsinki |
| OS | Ubuntu 24.04 LTS |
| vCPUs | 8 |
| RAM | 16 GB |
| SSD | 160 GB |

## Architektur

```
Celery Beat (3x taeglich: 06:00, 12:30, 20:00)
    +-- run_all_bots_daily()
            +-- Bot 1 -> emulator-5554 (AVD: lastwar-bot-1)
            +-- Bot 2 -> emulator-5556 (AVD: lastwar-bot-2)
            +-- Bot 3 -> emulator-5558 (AVD: lastwar-bot-3)

Logs: logs/lastwar-bot.log (rotierend, 5x5 MB)
```

## Erstinstallation (Server)

```bash
# 1. Repo klonen
git clone https://github.com/<user>/lastwar-bot.git ~/lastwar-bot
cd ~/lastwar-bot

# 2. Server einrichten (Android SDK, AVDs, venv, Systemd)
sudo bash scripts/00_setup_server.sh

# 3. .env anpassen (Redis-URL etc. -- Defaults funktionieren fuer lokales Redis)
nano .env

# 4. Emulatoren starten
bash scripts/start_emulators.sh

# 5. Last War APK installieren (APK muss manuell beschafft werden)
adb -s emulator-5554 install lastwar.apk
adb -s emulator-5556 install lastwar.apk
adb -s emulator-5558 install lastwar.apk

# 6. Accounts manuell einrichten (einmalig per scrcpy)
scrcpy -s emulator-5554

# 7. Services aktivieren
systemctl enable --now lastwar-emulators lastwar-celery lastwar-beat
```

## Konfiguration (.env)

```bash
cp .env.example .env
# Werte anpassen:
#   REDIS_URL        -- Standard: redis://localhost:6379/0
#   CELERY_TIMEZONE  -- Standard: Europe/Berlin
#   BOT_MATCH_THRESHOLD    -- Standard: 0.85
#   BOT_ACTION_DELAY       -- Standard: 1.5
#   BOT_SCREENSHOT_MAX_FILES -- Standard: 50
```

## Code-Update auf Server deployen

```bash
# Von der lokalen Maschine:
bash scripts/deploy.sh [SERVER_IP]

# Fuehrt aus: git pull + pip install + systemctl restart + health check
```

## Health Check & Auto-Restart

```bash
# Status pruefen
bash scripts/health_check.sh

# Status pruefen + ausgefallene Dienste automatisch neu starten
bash scripts/health_check.sh --restart
```

## Templates erstellen

```bash
# Screenshot eines laufenden Emulators
adb -s emulator-5554 exec-out screencap -p > screen.png

# Button ausschneiden und als Template speichern
# z.B. templates/btn_collect_all.png
```

## Logs

```bash
# Bot-Log (alle 3 Instanzen)
tail -f logs/lastwar-bot.log

# Celery Worker
tail -f logs/celery-worker.log

# Emulator (z.B. Bot 1)
tail -f /var/log/emulator-lastwar-bot-1.log
```

## Phasenplan

- **Phase 0** -- Server-Provisioning (done)
- **Phase 1** -- Emulator-Management + Systemd (done)
- **Phase 2** -- Bot-Framework (done)
- **Phase 3** -- Templates & Kalibrierung
- **Phase 4** -- Monitoring & Alerting
