#!/usr/bin/env python3
"""
Brankosn MP4 Converter: lokale helper (Mac / Windows / Linux).

Draait op JE EIGEN pc (127.0.0.1:8765) en laat yt-dlp de video's ophalen.
Het scherm (index.html, ook via GitHub Pages) praat met deze helper.
Optioneel "telefoon-modus": je telefoon (zelfde wifi) bedient de helper en bewaart de video in je galerij.
Geen extra pakketten nodig: yt-dlp haalt hij zelf op, ffmpeg zoekt hij zelf.
"""
import ipaddress, json, mimetypes, os, platform, re, secrets, shutil, socket, subprocess, sys, threading, uuid, webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

PORT = 8765
LAN_PORT = 8766
HERE = os.path.dirname(os.path.abspath(__file__))
RES = getattr(sys, "_MEIPASS", HERE)          # waar index.html staat (ook in de gebouwde app)
FROZEN = bool(getattr(sys, "frozen", False))
HOME = os.path.expanduser("~")
APPNAME = "Brankosn MP4 Converter"
if FROZEN:  # in de app: schrijfbare map voor yt-dlp en instellingen
    DATA = (os.path.join(HOME, "Library", "Application Support", APPNAME) if platform.system() == "Darwin"
            else os.path.join(os.environ.get("APPDATA", HOME), APPNAME) if platform.system() == "Windows"
            else os.path.join(HOME, ".local", "share", "brankosn-mp4-converter"))
else:
    DATA = HERE
BIN = os.path.join(DATA, "bin")
os.makedirs(BIN, exist_ok=True)

# ---------- instellingen (gekozen map, telefoon-pincode) ----------
CFG_PATH = os.path.join(DATA, "config.json")
try:
    with open(CFG_PATH) as f: CFG = json.load(f)
except Exception:
    CFG = {}
def save_cfg():
    try:
        with open(CFG_PATH, "w") as f: json.dump(CFG, f)
    except Exception:
        pass
if not CFG.get("pin"):
    CFG["pin"] = secrets.token_urlsafe(9); save_cfg()

OUT = os.environ.get("DL_OUT") or CFG.get("out") or os.path.join(HOME, "Downloads", "MP4-Downloader")
try:
    os.makedirs(OUT, exist_ok=True)
except Exception:
    OUT = os.path.join(HOME, "Downloads", "MP4-Downloader"); os.makedirs(OUT, exist_ok=True)
USED = {os.path.realpath(OUT)}  # mappen waaruit bestanden getoond/geserveerd mogen worden

# Alleen deze websites mogen met de helper praten (tegen misbruik door andere sites).
ALLOWED_ORIGINS = {"http://127.0.0.1:%d" % PORT, "http://localhost:%d" % PORT, "https://brankosn.github.io"}
ALLOWED_ORIGINS |= set(filter(None, os.environ.get("DL_ORIGINS", "").split(",")))
ALLOWED_HOSTS = {"127.0.0.1:%d" % PORT, "localhost:%d" % PORT}

os.environ["PATH"] = os.pathsep.join([BIN, os.path.join(HOME, "bin"), "/usr/local/bin", os.environ.get("PATH", "")])
JOBS, PROCS = {}, {}
STATE = {"ytdlp": None, "ytdlp_version": None, "ffmpeg": None, "setup": "Opstarten…"}
BROWSERS = {"chrome", "safari", "firefox", "edge", "brave"}
LAN = {"srv": None}
FAILS = {}
CHOOSER = None   # functie die een mapkiezer toont (wordt door app.py gezet)


# ---------- setup: yt-dlp en ffmpeg vinden of ophalen ----------
def asset():
    s, m = platform.system(), platform.machine().lower()
    if s == "Darwin": return "yt-dlp_macos"
    if s == "Windows": return "yt-dlp.exe"
    return "yt-dlp_linux_aarch64" if m in ("aarch64", "arm64") else "yt-dlp_linux"

def find_ytdlp():
    local = os.path.join(BIN, "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp")
    if os.path.exists(local): return local
    return shutil.which("yt-dlp")

def version(path):
    try:
        return subprocess.run([path, "--version"], capture_output=True, text=True, timeout=30).stdout.strip() or None
    except Exception:
        return None

def setup():
    try:
        STATE["setup"] = "yt-dlp zoeken…"
        yt = find_ytdlp()
        if not yt:
            STATE["setup"] = "yt-dlp downloaden (eenmalig)…"
            dest = os.path.join(BIN, "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp")
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/" + asset()
            subprocess.run(["curl", "-fsSL", "-o", dest, url], check=True, timeout=300)
            os.chmod(dest, 0o755)
            if platform.system() == "Darwin":
                subprocess.run(["xattr", "-d", "com.apple.quarantine", dest], capture_output=True)
            yt = dest
        STATE["ytdlp"] = yt
        STATE["setup"] = "yt-dlp bijwerken…"
        subprocess.run([yt, "-U"], capture_output=True, timeout=120)  # websites veranderen vaak
        STATE["ytdlp_version"] = version(yt)

        STATE["setup"] = "ffmpeg zoeken…"
        ff = None
        try:  # meegebundelde ffmpeg (in de app) of via pip geinstalleerd
            import imageio_ffmpeg
            ff = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ff = shutil.which("ffmpeg")
        if not ff and not FROZEN:
            STATE["setup"] = "ffmpeg ophalen (eenmalig)…"
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-q", "imageio-ffmpeg"],
                           capture_output=True, timeout=300)
            try:
                import imageio_ffmpeg
                ff = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ff = None
        STATE["ffmpeg"] = ff
        STATE["setup"] = "ok" if ff else "ffmpeg ontbreekt: video en geluid kunnen niet samengevoegd worden"
    except Exception as e:
        STATE["setup"] = "Setup mislukt: %s" % e


# ---------- downloaden ----------
def fmt_args(quality, audio):
    if audio:
        return ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    # Hoogste kwaliteit onder de gekozen grens; bij gelijke resolutie H.264 + AAC (speelt overal, ook in je galerij)
    s = ("res:%s," % quality if quality != "best" else "") + "vcodec:h264,acodec:aac,ext:mp4:m4a"
    return ["-f", "bv*+ba/b", "-S", s, "--merge-output-format", "mp4"]

def run(job_id, url, quality, audio, browser, out):
    j = JOBS[job_id]
    cmd = [STATE["ytdlp"], "--no-playlist", "--newline", "--restrict-filenames", "--no-mtime",
           "-o", os.path.join(out, "%(title).120B [%(id)s].%(ext)s"),
           "--print", "before_dl:TITLE:%(title)s",
           "--print", "before_dl:THUMB:%(thumbnail)s",
           "--print", "before_dl:DUR:%(duration_string)s",
           "--print", "after_move:FILE:%(filepath)s",
           "--progress-template", "download:PROG:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s"]
    if STATE["ffmpeg"]:
        cmd += ["--ffmpeg-location", STATE["ffmpeg"]]
    if browser in BROWSERS:
        cmd += ["--cookies-from-browser", browser]
    cmd += fmt_args(quality, audio) + [url]
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        PROCS[job_id] = p
        for line in p.stdout:
            line = line.strip()
            if line.startswith("PROG:"):
                pct, speed, eta = (line[5:].split("|") + ["", ""])[:3]
                if j["state"] != "merging":
                    j.update(percent=pct.strip(), speed=speed.strip(), eta=eta.strip(), state="downloading")
            elif line.startswith("TITLE:"): j["title"] = line[6:]
            elif line.startswith("THUMB:"): j["thumb"] = line[6:] if line[6:].startswith("http") else ""
            elif line.startswith("DUR:"): j["duration"] = line[4:]
            elif line.startswith("FILE:"): j["file"] = line[5:]
            elif "ERROR" in line: j["error"] = re.sub(r"^ERROR:\s*", "", line)[:300]
            elif "[Merger]" in line or "[ExtractAudio]" in line or "[VideoRemuxer]" in line:
                j["state"] = "merging"
        p.wait()
        if j["state"] == "cancelled": return
        ok = p.returncode == 0 and j.get("file")
        j["state"] = "done" if ok else "error"
        if not ok and not j.get("error"):
            j["error"] = "Download mislukt: link privé, verwijderd of niet beschikbaar?"
    except Exception as e:
        j.update(state="error", error=str(e))
    finally:
        PROCS.pop(job_id, None)

def inside_used(path):
    rp = os.path.realpath(path)
    return any(rp == u or rp.startswith(u + os.sep) for u in USED)

def reveal(path):
    path = os.path.realpath(path)
    if not inside_used(path): path = OUT
    s = platform.system()
    if s == "Darwin": subprocess.Popen(["open", "-R", path] if os.path.isfile(path) else ["open", path])
    elif s == "Windows": subprocess.Popen(["explorer", "/select,", path] if os.path.isfile(path) else ["explorer", path])
    else: subprocess.Popen(["xdg-open", path if os.path.isdir(path) else os.path.dirname(path)])

def choose_folder():
    """Open een echte mapkiezer van het besturingssysteem. Geeft pad of None."""
    if CHOOSER:   # de app geeft zijn eigen, ingebouwde mapkiezer mee
        try:
            p = CHOOSER()
            return p if p and os.path.isdir(p) else None
        except Exception:
            return None
    s = platform.system()
    try:
        if s == "Darwin":
            script = ('tell application "System Events"\nactivate\n'
                      'set f to POSIX path of (choose folder with prompt "Kies de map voor je downloads")\nend tell\nreturn f')
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=900)
        elif s == "Windows":
            ps = ("Add-Type -AssemblyName System.Windows.Forms;$d=New-Object System.Windows.Forms.FolderBrowserDialog;"
                  "$d.Description='Kies de map voor je downloads';$d.ShowNewFolderButton=$true;"
                  "if($d.ShowDialog() -eq 'OK'){Write-Output $d.SelectedPath}")
            r = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps], capture_output=True, text=True, timeout=900)
        else:
            exe = shutil.which("zenity")
            if exe: r = subprocess.run([exe, "--file-selection", "--directory", "--title=Kies de map voor je downloads"], capture_output=True, text=True, timeout=900)
            else: return None
        p = (r.stdout or "").strip()
        return p if r.returncode == 0 and p and os.path.isdir(p) else None
    except Exception:
        return None

def set_out(path):
    global OUT
    OUT = os.path.realpath(path)
    os.makedirs(OUT, exist_ok=True)
    USED.add(OUT)
    CFG["out"] = OUT; save_cfg()


# ---------- telefoon-modus (LAN) ----------
def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))   # stuurt niets, kiest alleen de juiste netwerkkaart
        ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return None

def lan_start():
    if LAN["srv"]: return True
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", LAN_PORT), H)
        srv.lan = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        LAN["srv"] = srv
        return True
    except OSError:
        return False

def lan_stop():
    srv = LAN["srv"]
    if srv:
        LAN["srv"] = None
        threading.Thread(target=lambda: (srv.shutdown(), srv.server_close()), daemon=True).start()

def lan_info():
    ip = lan_ip()
    return {"on": bool(LAN["srv"]), "ip": ip,
            "url": ("http://%s:%d/?pin=%s" % (ip, LAN_PORT, CFG["pin"])) if ip else None}


# ---------- webserver ----------
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass

    @property
    def lan(self): return bool(getattr(self.server, "lan", False))

    def cors(self):
        o = self.headers.get("Origin")
        if not self.lan and o in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

    def send(self, code, body, ctype="application/json", extra=None):
        b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or []): self.send_header(k, v)
        self.cors()
        self.end_headers()
        self.wfile.write(b)

    def host_ok(self):
        host = self.headers.get("Host", "")
        if not self.lan: return host in ALLOWED_HOSTS
        try:
            if not ipaddress.ip_address(self.client_address[0]).is_private: return False
        except ValueError:
            return False
        return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}:%d$" % LAN_PORT, host))

    def pin_ok(self):
        if not self.lan: return True
        ip = self.client_address[0]
        if FAILS.get(ip, 0) >= 20: return False
        try:
            c = SimpleCookie(self.headers.get("Cookie", ""))
            ok = "pin" in c and secrets.compare_digest(c["pin"].value, CFG["pin"])
        except Exception:
            ok = False
        if not ok: FAILS[ip] = FAILS.get(ip, 0) + 1
        return ok

    def allowed(self):
        if not self.host_ok(): return False
        o = self.headers.get("Origin")
        if o is not None:
            if self.lan: return o == "http://" + self.headers.get("Host", "")
            if o not in ALLOWED_ORIGINS: return False
        return self.pin_ok()

    def do_OPTIONS(self):
        if not self.allowed(): return self.send(403, {"error": "niet toegestaan"})
        self.send(204, b"")

    def send_file(self, path, name, download):
        size = os.path.getsize(path)
        start, end, code = 0, size - 1, 200
        m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1))
                if m.group(2): end = min(int(m.group(2)), size - 1)
            else:
                start = max(size - int(m.group(2)), 0)
            if start > end or start >= size:
                self.send_response(416); self.send_header("Content-Range", "bytes */%d" % size)
                self.send_header("Content-Length", "0"); self.end_headers(); return
            code = 206
        self.send_response(code)
        self.send_header("Content-Type", mimetypes.guess_type(path)[0] or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if code == 206: self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.send_header("Content-Disposition", "%s; filename*=UTF-8''%s" % ("attachment" if download else "inline", quote(name)))
        self.end_headers()
        try:
            with open(path, "rb") as f:
                f.seek(start); left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk: break
                    self.wfile.write(chunk); left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        # telefoon opent de QR-link: pincode wordt een cookie
        if self.lan and u.path == "/" and "pin" in q and self.host_ok():
            ip = self.client_address[0]
            if FAILS.get(ip, 0) < 20 and secrets.compare_digest(q["pin"][0], CFG["pin"]):
                return self.send(302, b"", "text/plain", [("Location", "/"),
                    ("Set-Cookie", "pin=%s; Path=/; HttpOnly; SameSite=Strict; Max-Age=31536000" % CFG["pin"])])
            FAILS[ip] = FAILS.get(ip, 0) + 1
            return self.send(403, b"Verkeerde pincode. Scan de QR-code opnieuw.", "text/plain; charset=utf-8")
        if u.path == "/icon.png" and self.host_ok():   # app-icoon (voor "zet op beginscherm"), niet geheim
            try:
                with open(os.path.join(RES, "icon.png"), "rb") as f:
                    return self.send(200, f.read(), "image/png")
            except OSError:
                return self.send(404, {"error": "geen icoon"})
        if not self.allowed(): return self.send(403, {"error": "niet toegestaan"})
        if u.path in ("/", "/index.html"):
            with open(os.path.join(RES, "index.html"), "rb") as f:
                return self.send(200, f.read(), "text/html; charset=utf-8")
        if u.path == "/api/health":
            return self.send(200, {"ok": True, "setup": STATE["setup"], "ytdlp": STATE["ytdlp_version"],
                                   "ffmpeg": bool(STATE["ffmpeg"]), "out": OUT, "remote": self.lan})
        if u.path == "/api/status":
            return self.send(200, {"jobs": JOBS, "out": OUT})
        if u.path == "/api/lan" and not self.lan:
            return self.send(200, lan_info())
        m = re.match(r"^/files/([0-9a-f]{8})$", u.path)
        if m:
            j = JOBS.get(m.group(1))
            f = j.get("file") if j else None
            if f and os.path.isfile(f) and inside_used(f) and j.get("state") == "done":
                return self.send_file(f, os.path.basename(f), "dl" in q)
            return self.send(404, {"error": "bestand niet gevonden"})
        self.send(404, {"error": "niet gevonden"})

    def do_POST(self):
        if not self.allowed(): return self.send(403, {"error": "niet toegestaan"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self.send(400, {"error": "ongeldige aanvraag"})
        if self.path == "/api/download":
            url = str(d.get("url") or "").strip()
            if not re.match(r"^https?://", url):
                return self.send(400, {"error": "Plak een geldige link (begint met https://)"})
            if not STATE["ytdlp"]:
                return self.send(503, {"error": "Helper is nog aan het opstarten: " + STATE["setup"]})
            q = str(d.get("quality", "best"))
            q = q if q in ("best", "2160", "1440", "1080", "720", "480") else "best"
            browser = None if self.lan else d.get("browser")   # login-cookies nooit via de telefoon
            jid = uuid.uuid4().hex[:8]
            JOBS[jid] = {"url": url, "state": "starting", "percent": "0%", "quality": q, "audio": bool(d.get("audio"))}
            threading.Thread(target=run, args=(jid, url, q, bool(d.get("audio")), browser, OUT), daemon=True).start()
            return self.send(200, {"id": jid})
        if self.path == "/api/cancel":
            jid = d.get("id")
            if jid in JOBS and jid in PROCS:
                JOBS[jid]["state"] = "cancelled"
                PROCS[jid].terminate()
            return self.send(200, {"ok": True})
        if self.lan:   # onderstaande acties alleen op de laptop zelf
            return self.send(403, {"error": "alleen op de laptop zelf"})
        if self.path == "/api/reveal":
            reveal(str(d.get("file") or OUT))
            return self.send(200, {"ok": True})
        if self.path == "/api/choose":
            p = choose_folder()
            if p:
                set_out(p)
                return self.send(200, {"out": OUT})
            return self.send(200, {"cancelled": True, "out": OUT})
        if self.path == "/api/lan":
            if d.get("on"):
                if not lan_start(): return self.send(500, {"error": "Poort %d is bezet" % LAN_PORT})
            else:
                lan_stop()
            CFG["lan"] = bool(d.get("on")); save_cfg()
            return self.send(200, lan_info())
        self.send(404, {"error": "niet gevonden"})


def start_extras():
    """Na opstarten: telefoon-modus herstellen als die aan stond."""
    if CFG.get("lan"): lan_start()


if __name__ == "__main__":
    threading.Thread(target=setup, daemon=True).start()
    start_extras()
    print("=" * 58)
    print(" Brankosn MP4 Converter helper draait. Laat dit venster open.")
    print(" Scherm:     http://127.0.0.1:%d" % PORT)
    print(" Downloads:  %s" % OUT)
    print(" Stoppen:    sluit dit venster (of Ctrl+C)")
    print("=" * 58)
    if "--no-open" not in sys.argv:
        threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:%d" % PORT)).start()
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
    except OSError:
        print("Poort %d is al in gebruik: de helper draait waarschijnlijk al." % PORT)
        webbrowser.open("http://127.0.0.1:%d" % PORT)
