#!/usr/bin/env python3
"""
Royal Handsome — Servidor Web
Sirve el frontend y proxea las llamadas a Replicate (evita CORS).

Local:  python3 server.py
Render: Se configura automáticamente via PORT env var.

Token de Replicate: pon REPLICATE_API_TOKEN en .env (local) o en la
variable de entorno del servicio en Render.com.
"""
import http.server
import urllib.request
import urllib.error
import json
import os
import sys
from pathlib import Path

BASE_DIR    = Path(__file__).parent
HTML_FILE   = BASE_DIR / "index.html"
ASSETS_DIR  = BASE_DIR / "rh-assets"
REPLICATE   = "https://api.replicate.com"
PORT        = int(os.environ.get("PORT", 8080))

# ── Cargar token desde .env si existe (solo para dev local) ───────────────────
def _load_dotenv():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())

_load_dotenv()
REPLICATE_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")

MIME = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".json": "application/json",
    ".js":   "application/javascript",
    ".css":  "text/css",
    ".html": "text/html; charset=utf-8",
}


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        status = args[1] if len(args) > 1 else "?"
        print(f"  {self.command:5}  {self.path}  →  {status}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Prefer")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._serve_file(HTML_FILE, "text/html; charset=utf-8")
        elif path == "/catalog.json":
            self._serve_file(BASE_DIR / "catalog.json", "application/json")
        elif path.startswith("/rh-assets/"):
            filename = path[len("/rh-assets/"):]
            ext = Path(filename).suffix.lower()
            self._serve_file(ASSETS_DIR / filename, MIME.get(ext, "application/octet-stream"))
        elif path.startswith("/replicate/"):
            self._proxy("GET")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        if self.path.startswith("/replicate/"):
            self._proxy("POST")
        else:
            self.send_error(404, "Not found")

    def _serve_file(self, filepath: Path, content_type: str):
        try:
            data = filepath.read_bytes()
        except FileNotFoundError:
            self.send_error(404, f"File not found: {filepath.name}")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        # HTML nunca se cachea; assets (imágenes) sí pueden cachearse 1h
        if content_type.startswith("text/html"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
        else:
            self.send_header("Cache-Control", "public, max-age=3600")
        self.send_cors()
        self.end_headers()
        self.wfile.write(data)

    def _proxy(self, method: str):
        suffix = self.path[len("/replicate"):]

        if suffix == "/account":
            target = f"{REPLICATE}/v1/account"
        elif suffix == "/predictions":
            target = f"{REPLICATE}/v1/models/yisol/idm-vton/predictions"
        elif suffix.startswith("/predictions/"):
            pred_id = suffix[len("/predictions/"):]
            target = f"{REPLICATE}/v1/predictions/{pred_id}"
        else:
            self.send_error(404, f"Unknown proxy path: {self.path}")
            return

        body = None
        if method == "POST":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b""

        # Token viene del servidor, no del browser
        token = REPLICATE_TOKEN or self.headers.get("Authorization", "")
        if REPLICATE_TOKEN and not token.startswith("Token "):
            token = f"Token {REPLICATE_TOKEN}"

        fwd_headers = {
            "Content-Type":  "application/json",
            "Authorization": token,
        }
        prefer = self.headers.get("Prefer", "")
        if prefer:
            fwd_headers["Prefer"] = prefer

        req = urllib.request.Request(target, data=body, headers=fwd_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                status, data = resp.status, resp.read()
                ct = resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            status, data = e.code, e.read()
            ct = e.headers.get("Content-Type", "application/json")
        except urllib.error.URLError as e:
            self._json_err(502, f"No se pudo conectar con Replicate: {e.reason}")
            return
        except Exception as e:
            self._json_err(500, str(e))
            return

        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(data)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(data)

    def _json_err(self, code: int, msg: str):
        body = json.dumps({"detail": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    if not HTML_FILE.exists():
        print(f"\n  ⚠️  No se encontró '{HTML_FILE.name}' en {BASE_DIR}")
        sys.exit(1)

    if not REPLICATE_TOKEN:
        print("\n  ⚠️  REPLICATE_API_TOKEN no está definido.")
        print("     Crea un archivo .env con:  REPLICATE_API_TOKEN=r8_xxxx")
        print("     El probador virtual no funcionará sin él.\n")

    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print()
    print("  👑  Royal Handsome — Servidor Web")
    print(f"  ➜   http://localhost:{PORT}")
    if REPLICATE_TOKEN:
        print(f"  ✅  Token Replicate cargado ({REPLICATE_TOKEN[:8]}...)")
    print()
    print("  Ctrl+C para detener.")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.")
        sys.exit(0)
