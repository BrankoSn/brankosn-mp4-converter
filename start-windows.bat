@echo off
rem Dubbelklik om de MP4 Downloader-helper te starten (Windows).
cd /d "%~dp0"
where py >nul 2>nul && (py -3 server.py & goto end)
where python >nul 2>nul && (python server.py & goto end)
echo Python 3 is nodig. Installeer het via https://www.python.org/downloads/ (vink "Add to PATH" aan).
:end
pause
