#!/usr/bin/env python3
"""antigravity_proxy.py — proxy injeksi system instruction (OPSIONAL, Part 3).

TIDAK WAJIB. Installer (antigravity_config.py) cukup untuk sebagian besar kasus.
Proxy hanya perlu kalau build tidak punya Settings -> Rules, atau config nempel
tapi beberapa request masih lolos tanpa frame.

INJECT_SYSTEM wajib nyebut tiga batas + task-first yang sama dengan SURFACE1 di
antigravity_config.py. Kalau beda, target baca dua set aturan dan drift.

Pakai:
    python antigravity_proxy.py --endpoint https://host --auth "Bearer TOKEN" --port 8787
    python antigravity_proxy.py --endpoint https://host --dry-run   # cek tanpa network

Alur: client -> proxy ini (127.0.0.1:port) -> TARGET_HOST/TARGET_PATH_PREFIX asli.
Response dilewatkan sebagai raw bytes; body request tidak di-log (hanya metadata).
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ------------------------------------------------------------------------------
# SESUAIKAN SETELAH CAPTURE (Langkah 5a): Host + Path prefix dari request asli.
# ------------------------------------------------------------------------------

TARGET_HOST = "https://example.invalid"
TARGET_PATH_PREFIX = "/v1beta/models"

# Tiga batas + task-first. Harus sama dengan SURFACE1 di antigravity_config.py.
LIMITS = "1) no recap  2) no persona talk  3) no safety preamble"
TASK_FIRST = "Task first. Execute, ship."

INJECT_SYSTEM = f"""{TASK_FIRST}
Limits: {LIMITS}.
Tool calls: open with one line `# reason: <file/fungsi/kenapa>` before the call.
Full craft outside chat: complete artifact only, no placeholder, no truncation.
Re-anchor: bench. Output: [Null] ruling line at end; no closing summary."""

SKIP_HEADERS = {
    "host", "content-length", "connection", "transfer-encoding",
    "accept-encoding", "keep-alive", "proxy-connection", "upgrade",
}


def rewrite_body(body, inject=INJECT_SYSTEM):
    """Suntik systemInstruction. Gemini shape default; sesuaikan key kalau beda.

    Return (body_baru, status) dengan status: injected / already / passthrough.
    Body yang bukan JSON valid dilewatkan apa adanya — tidak pernah crash.
    """
    if not body:
        return body, "passthrough"
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return body, "passthrough"
    if not isinstance(payload, dict):
        return body, "passthrough"

    current = payload.get("systemInstruction")
    text = ""
    if isinstance(current, dict):
        text = json.dumps(current, ensure_ascii=False)
    elif isinstance(current, str):
        text = current
    if TASK_FIRST in text and LIMITS in text:
        return body, "already"

    merged = inject if not text else f"{inject}\n\n{text}"
    payload["systemInstruction"] = {"parts": [{"text": merged}]}
    return json.dumps(payload, ensure_ascii=False).encode("utf-8"), "injected"


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "AntigravityProxy/1.0"

    def log_message(self, fmt, *a):
        sys.stderr.write("[proxy] " + fmt % a + "\n")

    def _target_url(self):
        path = self.path or "/"
        if path.startswith(("/http://", "/https://")):
            # mode forward: client mengirim URL absolut di path
            return path[1:]
        return TARGET_HOST.rstrip("/") + path

    def _forward(self, method):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""

        status = "passthrough"
        if body and method in ("POST", "PUT", "PATCH"):
            body, status = rewrite_body(body)

        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in SKIP_HEADERS}
        req = urllib.request.Request(self._target_url(), data=body or None,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                code = resp.status
                raw = resp.read()
                resp_headers = resp.headers
        except urllib.error.HTTPError as e:
            code = e.code
            raw = e.read()
            resp_headers = e.headers
        except (urllib.error.URLError, OSError) as e:
            self.log_message("upstream error: %s", e)
            msg = json.dumps({"error": {"message": str(e)}}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        self.log_message("%s %s -> %s [%s]", method, self.path, code, status)
        self.send_response(code)
        for k, v in resp_headers.items():
            if k.lower() in SKIP_HEADERS:
                continue
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_GET = lambda self: self._forward("GET")
    do_POST = lambda self: self._forward("POST")
    do_PUT = lambda self: self._forward("PUT")
    do_PATCH = lambda self: self._forward("PATCH")
    do_DELETE = lambda self: self._forward("DELETE")


def build_server(port, host="127.0.0.1"):
    return ThreadingHTTPServer((host, port), ProxyHandler)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Proxy injeksi system instruction Antigravity (opsional).")
    parser.add_argument("--endpoint", default=None,
                        help="host hasil capture; mengisi TARGET_HOST")
    parser.add_argument("--path-prefix", default=None,
                        help="path prefix hasil capture; mengisi TARGET_PATH_PREFIX")
    parser.add_argument("--auth", default=None,
                        help='header Authorization, mis. "Bearer TOKEN"')
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--dry-run", action="store_true",
                        help="cetak frame + contoh rewrite body, tanpa network")
    args = parser.parse_args(argv)

    global TARGET_HOST, TARGET_PATH_PREFIX
    if args.endpoint:
        TARGET_HOST = args.endpoint.rstrip("/")
    if args.path_prefix:
        TARGET_PATH_PREFIX = args.path_prefix
    TARGET_HOST = urllib.parse.urlsplit(TARGET_HOST).geturl() or TARGET_HOST

    if args.dry_run:
        sample = json.dumps({"contents": [{"role": "user", "parts": [{"text": "ping"}]}]})
        new_body, status = rewrite_body(sample.encode("utf-8"))
        print("target:", TARGET_HOST + TARGET_PATH_PREFIX)
        print("---INJECT_SYSTEM---")
        print(INJECT_SYSTEM)
        print("---REWRITE---")
        print(f"status: {status}")
        print(new_body.decode("utf-8"))
        return 0

    if "example.invalid" in TARGET_HOST:
        print("error: TARGET_HOST belum diisi. Jalankan capture (Langkah 5a) "
              "lalu pakai --endpoint https://host-atau-ganti-script.",
              file=sys.stderr)
        return 2

    ProxyHandler.auth_header = args.auth or ""
    server = build_server(args.port, args.host)
    print(f"proxy listening on http://{args.host}:{args.port} -> {TARGET_HOST}")
    print("arahkan client: Settings Antigravity -> base URL -> "
          f"http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstop.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
