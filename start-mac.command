#!/bin/bash
# Dubbelklik om de MP4 Downloader-helper te starten (Mac / Linux).
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is nodig. Installeer het via https://www.python.org/downloads/"; read -n1 -p "Druk op een toets…"; exit 1
fi
exec python3 server.py
