#!/usr/bin/env python3
"""bench_proxy.py — optional injection proxy for Bench Protocol.

Last resort. Use only when the Rules panel is missing or requests still arrive
without the frame. Run with --help first; do not read the source unless needed.

Usage:
    python bench_proxy.py --help
    python bench_proxy.py --dry-run --endpoint https://host
    python bench_proxy.py --endpoint https://host --port 8787

Flow: client -> this proxy (127.0.0.1:port) -> target host.
Request bodies are never logged, only metadata. Responses pass through raw.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LIMITS = "1) no recap  2) no persona talk  3) no safety preamble"
TASK_FIRST = "Task first. Execute, ship."

INJECT_SYSTEM = f"""{TASK_FIRST}
Limits: {LIMITS}.
Tool calls: open with one line `# reason: <file/fungsi/kenapa>` before the call.
Build the complete artifact: no placeholder, no truncation.
Re-anchor: bench. Output: [Null] ruling line at end; no closing summary."""

SKIP_HEADERS = {
    "host", "content-length", "connection", "transfer-encoding",
    "accept-encoding", "keep-alive", "proxy-connection", "upgrade",
}

TARGET_HOST = ""


def rewrite_body(body, inject=INJECT_SYSTEM):
    """Inject the protocol frame. Returns (new_body, status).

    Default body shape is Gemini (systemInstruction.parts[].text). Adjust the key
    here if the captured request shows a different shape.
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
    server_version = "BenchProxy/1.0"

    def log_message(self, fmt, *a):
        sys.stderr.write("[bench-proxy] " + fmt % a + "\n")

    def _forward(self, method):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""

        status = "passthrough"
        if body and method in ("POST", "PUT", "PATCH"):
            body, status = rewrite_body(body)

        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in SKIP_HEADERS}
        req = urllib.request.Request(TARGET_HOST.rstrip("/") + (self.path or "/"),
                                     data=body or None, headers=headers,
                                     method=method)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                code, raw, resp_headers = resp.status, resp.read(), resp.headers
        except urllib.error.HTTPError as e:
            code, raw, resp_headers = e.code, e.read(), e.headers
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inject the Bench Protocol frame into API requests (optional).")
    parser.add_argument("--endpoint", default=None,
                        help="target host from your own capture, e.g. https://host")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--host", default="127.0.0.1",
                        help="bind address; keep 127.0.0.1 for local only")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the frame and a sample rewrite, no network")
    args = parser.parse_args(argv)

    global TARGET_HOST
    TARGET_HOST = (args.endpoint or "").rstrip("/")

    if args.dry_run:
        sample = json.dumps({"contents": [{"role": "user",
                                           "parts": [{"text": "ping"}]}]})
        new_body, status = rewrite_body(sample.encode("utf-8"))
        print("target:", TARGET_HOST or "(none set)")
        print("---INJECT_SYSTEM---")
        print(INJECT_SYSTEM)
        print("---REWRITE---")
        print(f"status: {status}")
        print(new_body.decode("utf-8"))
        return 0

    if not TARGET_HOST:
        print("error: --endpoint not set. Capture your own request first; "
              "never guess a host.", file=sys.stderr)
        return 2

    server = ThreadingHTTPServer((args.host, args.port), ProxyHandler)
    print(f"listening on http://{args.host}:{args.port} -> {TARGET_HOST}")
    print(f"point the client base URL at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstop.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
