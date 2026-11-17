#!/bin/bash
# Bouwt de Mac-app: dist/Brankosn MP4 Converter.app
cd "$(dirname "$0")"
python3 make_icon.py
~/Library/Python/3.9/bin/pyinstaller --noconfirm --windowed --name "Brankosn MP4 Converter" --icon "$PWD/icon.icns" \
  --add-data "$PWD/index.html:." --add-data "$PWD/icon.png:." --collect-all imageio_ffmpeg --hidden-import webview.platforms.cocoa \
  --distpath dist --workpath build --specpath build app.py
