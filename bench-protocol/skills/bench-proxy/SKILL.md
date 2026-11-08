---
name: bench-proxy
description: Set up the optional injection proxy when the app has no Rules panel or requests still arrive without the protocol frame. Use only when rules and skills failed to apply, or when the user types /bench-proxy.
---

# Bench Proxy — last resort

Use this only after `/bench-rules` and the plugin rule both failed to reach the
model. A proxy sits between the client and the API and injects the frame into
every request body.

## When not to use it

- The Rules panel exists and applies. Use `/bench-rules` instead.
- The protocol already appears in agent output. Nothing to fix.
- The user has not captured their own endpoint. Do not guess an endpoint.

## Steps

1. Ask for the captured request details in one message: target host, path prefix,
   auth header. The user gets these from their own traffic capture. Never invent them.
2. Confirm the request body shape. The bundled proxy defaults to the Gemini shape
   (`systemInstruction.parts[].text`). If the capture shows another key, say which
   key and adjust `rewrite_body` before running.
3. Run the bundled proxy as a black box — run `--help` first, do not read the source:

   ```bash
   python scripts/bench_proxy.py --help
   python scripts/bench_proxy.py --dry-run --endpoint https://host
   python scripts/bench_proxy.py --endpoint https://host --port 8787
   ```

4. Tell the user to point the client base URL at `http://127.0.0.1:8787`.
5. Verify one request went through and the frame is present. Report pass or fail.

## Limits

- The injected text must match the plugin rule wording. Two different texts make
  the model follow two rule sets.
- Never log request bodies — metadata only.
- Local binding only (`127.0.0.1`). Do not expose the proxy to a network.
