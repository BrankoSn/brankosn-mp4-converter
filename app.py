#!/usr/bin/env python3
"""Brankosn MP4 Converter als app: helper + eigen venster in één. Dubbelklik en klaar."""
import threading, time, urllib.request
from http.server import ThreadingHTTPServer
import webview
import server


def run_server():
    try:
        ThreadingHTTPServer(("127.0.0.1", server.PORT), server.H).serve_forever()
    except OSError:
        pass  # poort bezet: er draait al een helper, die gebruiken we gewoon


if __name__ == "__main__":
    threading.Thread(target=server.setup, daemon=True).start()
    server.start_extras()
    threading.Thread(target=run_server, daemon=True).start()
    url = "http://127.0.0.1:%d" % server.PORT
    for _ in range(60):
        try:
            urllib.request.urlopen(url + "/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    window = webview.create_window("Brankosn MP4 Converter", url, width=1100, height=900,
                                   min_size=(420, 640), background_color="#0a0620")

    def pick_folder():
        r = window.create_file_dialog(webview.FOLDER_DIALOG)
        return r[0] if r else None
    server.CHOOSER = pick_folder
    webview.start()
