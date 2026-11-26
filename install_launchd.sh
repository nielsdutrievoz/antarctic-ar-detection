#!/bin/zsh
# Installe (ou désinstalle avec --uninstall) la tâche launchd qui lance run_forecast.py
# deux fois par jour, après la publication des runs ENS 00 UTC et 12 UTC.
# Usage : ./install_launchd.sh [chemin/vers/python] [--uninstall]
set -e
LABEL="ch.slf.ar-alert"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$1" == "--uninstall" || "$2" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Tâche $LABEL supprimée."
  exit 0
fi

PY="${1:-$(conda run -n ar-alert which python 2>/dev/null || true)}"
[[ -x "$PY" ]] || { echo "Python introuvable. Usage : $0 /chemin/vers/envs/ar-alert/bin/python"; exit 1; }
mkdir -p "$DIR/data/logs" "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>-u</string>
    <string>$DIR/run_forecast.py</string>
    <string>--config</string>
    <string>$DIR/config.yaml</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <!-- Heures locales du Mac. Le run 00 UTC est complet vers 08-09 UTC, le 12 UTC vers 20-21 UTC.
       Si le Mac dort à l'heure prévue, launchd lance la tâche au réveil. -->
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>10</integer><key>Minute</key><integer>30</integer></dict>
    <dict><key>Hour</key><integer>22</integer><key>Minute</key><integer>30</integer></dict>
  </array>
  <key>StandardOutPath</key><string>$DIR/data/logs/ar_alert.log</string>
  <key>StandardErrorPath</key><string>$DIR/data/logs/ar_alert.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Tâche $LABEL installée ($PLIST)."
echo "Lancer tout de suite : launchctl kickstart gui/$(id -u)/$LABEL"
echo "Journal : $DIR/data/logs/ar_alert.log"
