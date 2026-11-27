#!/usr/bin/env python3
"""NEXORA local stub API for k6 harness runs (laptop only).

Serves the three endpoints the shipped k6 profiles target, plus /health.
stdlib only - no pip installs needed.

    python stub_api.py                 (port 8080, ~25 ms simulated latency)
    python stub_api.py --port 18080    (if 8080 is busy)
    python stub_api.py --latency-ms 0  (pure in-memory speed)

This measures the harness, not the architecture. Label every result
"local stub run". Never present it as AWS or VPS capacity evidence.
"""
import argparse
import json
import random
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ARGS = None
START = time.time()
LOCK = threading.Lock()
S = {
    "total": 0,
    "status": {},
    "paths": {},
    "lat": deque(maxlen=8000),    # (ts, seconds) recent requests
    "buckets": deque(maxlen=60),  # per-second request counts, last 60 s
    "lastb": 0,
    "cur": None,
}


def rec(dur, path, code):
    """Record one handled request (cheap; needed for the live dashboard)."""
    ts = time.time()
    with LOCK:
        S["total"] += 1
        S["status"][code] = S["status"].get(code, 0) + 1
        S["paths"][path] = S["paths"].get(path, 0) + 1
        S["lat"].append((ts, dur))
        b = int(ts)
        if b == S["lastb"] and S["cur"] is not None:
            S["cur"][1] += 1
        else:
            S["lastb"] = b
            S["cur"] = [b, 1]
            S["buckets"].append(S["cur"])


_CSS = """
*{box-sizing:border-box}
body{background:#0B101B;color:#F2F4F8;font-family:'Segoe UI',Arial,sans-serif;margin:0;padding:0 0 28px}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
.top{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #2C3A57;background:#0E1420;padding:18px 0 14px;margin-bottom:22px}
.top .inner{display:flex;justify-content:space-between;align-items:center;max-width:1080px;width:100%;margin:0 auto;padding:0 24px}
h1{font-family:Georgia,serif;font-size:26px;letter-spacing:3px;margin:0;color:#fff}
h1 span.dot{color:#F0A72E}
.sub{color:#9AA6B8;font-size:12px;margin-top:3px}
.badge{background:#3a2b10;color:#F0A72E;border:1px solid #b37b1d;border-radius:999px;padding:5px 14px;font-size:11px;letter-spacing:.5px;white-space:nowrap}
.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:20px}
.card{background:linear-gradient(180deg,#182136 0%,#141d30 100%);border:1px solid #2C3A57;border-radius:10px;padding:14px 16px}
.card .n{font-family:Consolas,monospace;font-size:24px;font-weight:700;color:#fff}
.card .n small{font-size:13px;color:#9AA6B8;font-weight:400}
.card .l{font-size:10.5px;color:#9AA6B8;margin-top:4px;text-transform:uppercase;letter-spacing:1px}
.panel{background:#182136;border:1px solid #2C3A57;border-radius:10px;padding:16px 18px;margin-bottom:16px}
.panel h2{font-size:12px;color:#F0A72E;margin:0 0 12px;text-transform:uppercase;letter-spacing:1.5px}
.panel h2 span{color:#9AA6B8;float:right;text-transform:none;letter-spacing:0;font-family:Consolas,monospace}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
svg.chartsvg{width:100%;height:170px;display:block}
svg .line{fill:none;stroke:#F0A72E;stroke-width:2.5;stroke-linejoin:round}
svg .grid{stroke:#2C3A57;stroke-width:1;stroke-dasharray:3 4}
svg .dot{fill:#F0A72E;stroke:#0B101B;stroke-width:2}
table{border-collapse:collapse;width:100%}
td,th{border-bottom:1px solid #243252;padding:7px 10px;font-size:12.5px;text-align:left}
tr:last-child td{border-bottom:none}
th{color:#9AA6B8;font-size:10.5px;text-transform:uppercase;letter-spacing:1px;font-weight:600}
tr:hover td{background:#1E2A42}
td.num,th.num{text-align:right;font-family:Consolas,monospace}
.barcell{width:38%}
.bar{height:6px;background:#F0A72E;border-radius:3px;min-width:2px}
.pill{display:inline-block;border-radius:999px;padding:2px 10px;font-size:11px;font-family:Consolas,monospace;margin-right:6px}
.pill.ok{background:#12331f;color:#5bd08a;border:1px solid #2c6b44}
.pill.cre{background:#332711;color:#F0A72E;border:1px solid #8a6520}
.pill.err{background:#3a1a18;color:#E0655E;border:1px solid #7a3a36}
.strow{display:flex;justify-content:space-between;align-items:center;padding:8px 2px;border-bottom:1px solid #243252;font-size:13px}
.strow:last-child{border-bottom:none}
.foot{color:#7d8aa0;font-size:11px;margin-top:20px;text-align:center}
"""

CATALOGUE = {
    "page": 1,
    "pageSize": 24,
    "total": 500,
    "items": [
        {
            "sku": f"SKU-{n}",
            "title": f"NEXORA product {n}",
            "price": round(random.uniform(4.5, 250.0), 2),
            "stock": random.randint(0, 40),
        }
        for n in range(1, 25)
    ],
}


def bump():
    global COUNT
    with LOCK:
        COUNT += 1


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # silence the per-request access log
        pass

    # k6 force-closes idle keep-alive sockets at shutdown; stdlib prints a
    # traceback for each. Swallow them - they are noise, not failures.
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, TimeoutError):
            self.close_connection = True

    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        rec(time.perf_counter() - self._t0, self.path.split("?")[0], code)

    def _dashboard(self):
        now = time.time()
        with LOCK:
            total = S["total"]
            status = dict(S["status"])
            paths = sorted(S["paths"].items(), key=lambda kv: -kv[1])
            recent = list(S["lat"])
            buckets = list(S["buckets"])
        rps10 = sum(1 for ts, _ in recent if ts > now - 10) / 10.0
        lat = sorted(d for _, d in recent[-500:])
        avg_ms = (sum(lat) / len(lat)) * 1000 if lat else 0.0
        p95_ms = lat[min(len(lat) - 1, int(len(lat) * 0.95))] * 1000 if lat else 0.0
        s200 = status.get(200, 0)
        s201 = status.get(201, 0)
        s404 = status.get(404, 0)
        succ = (s200 + s201) / total * 100 if total else 100.0
        up = int(now - START)
        uptime = f"{up // 3600}h {(up // 60) % 60:02d}m {up % 60:02d}s" if up >= 3600 else f"{up // 60}m {up % 60:02d}s"

        # svg area chart of req/s over the last 60 s
        W, H = 860, 150
        base, top = H - 16, 12
        n = len(buckets)
        maxb = max((c for _, c in buckets), default=1) or 1
        if n == 1:
            buckets = buckets + buckets  # single second of traffic: draw flat line
            n = 2
        if n >= 2:
            coords = [(i * (W / (n - 1)), base - (c / maxb) * (base - top)) for i, (_, c) in enumerate(buckets)]
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
            lx, ly = coords[-1]
            chart = (f"<defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'>"
                     f"<stop offset='0' stop-color='#F0A72E' stop-opacity='0.30'/>"
                     f"<stop offset='1' stop-color='#F0A72E' stop-opacity='0'/></linearGradient></defs>"
                     f"<line class='grid' x1='0' y1='{(base + top) / 2:.0f}' x2='{W}' y2='{(base + top) / 2:.0f}'/>"
                     f"<line class='grid' x1='0' y1='{top}' x2='{W}' y2='{top}'/>"
                     f"<path d='M0,{base} L{pts} L{W},{base}' fill='url(#g)' stroke='none'/>"
                     f"<polyline class='line' points='{pts}'/>")
            chart += f"<circle class='dot' cx='{lx:.1f}' cy='{ly:.1f}' r='4'/>"
        else:
            chart = f"<text x='430' y='80' text-anchor='middle' fill='#9AA6B8' font-size='13'>waiting for traffic</text>"

        peak = max((c for _, c in buckets), default=0)
        top_path = max((n for _, n in paths), default=1) or 1
        shown, agg = [], {}
        for p, n in paths:  # collapse per-sku product paths into one row
            if p.startswith("/api/products/"):
                agg["/api/products/*"] = agg.get("/api/products/*", 0) + n
            else:
                shown.append((p, n))
        shown += sorted(agg.items())
        ep = "".join(
            f"<tr><td>{p}</td><td class='num'>{n}</td>"
            f"<td class='barcell'><div class='bar' style='width:{int(n / top_path * 100)}%'></div></td></tr>"
            for p, n in shown)
        items = "".join(
            f"<tr><td class='num'>{i['sku']}</td><td>{i['title']}</td>"
            f"<td class='num'>RM {i['price']:.2f}</td><td class='num'>{i['stock']}</td></tr>"
            for i in CATALOGUE["items"])

        def card(v, l, unit=""):
            return (f"<div class='card'><div class='n'>{v}<small>{unit}</small></div>"
                    f"<div class='l'>{l}</div></div>")

        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<meta http-equiv='refresh' content='2'>"
            "<title>NEXORA stub - live status</title>"
            f"<style>{_CSS}</style></head><body>"
            "<div class='top'><div class='inner'>"
            "<div><h1>NEXORA<span class='dot'>.</span></h1>"
            "<div class='sub'>omnichannel retail API - live stub status &middot; auto-refresh 2 s</div></div>"
            "<span class='badge'>LOCAL STUB RUN &middot; NOT AWS &middot; NOT VPS</span></div></div>"
            "<div class='wrap'>"
            "<div class='cards'>"
            + card(total, "total requests")
            + card(f"{rps10:.1f}", "req/s last 10 s")
            + card(f"{avg_ms:.1f}", "avg latency", " ms")
            + card(f"{p95_ms:.1f}", "p95 latency", " ms")
            + card(f"{succ:.2f}", "success rate", " %")
            + card(uptime, "stub uptime")
            + "</div>"
            "<div class='panel'><h2>throughput <span>requests per second - last 60 s &middot; peak "
            f"{peak}</span></h2>"
            f"<svg class='chartsvg' viewBox='0 0 {W} {H}' preserveAspectRatio='none'>{chart}</svg></div>"
            "<div class='grid2'>"
            "<div class='panel'><h2>endpoints</h2>"
            f"<table><tr><th>path</th><th class='num'>requests</th><th></th></tr>{ep}</table></div>"
            "<div class='panel'><h2>responses</h2>"
            f"<div class='strow'><span><span class='pill ok'>200 OK</span>catalogue, product, health</span>"
            f"<span class='num'>{s200}</span></div>"
            f"<div class='strow'><span><span class='pill cre'>201 CREATED</span>orders accepted</span>"
            f"<span class='num'>{s201}</span></div>"
            f"<div class='strow'><span><span class='pill err'>404</span>unknown paths</span>"
            f"<span class='num'>{s404}</span></div></div>"
            "</div>"
            "<div class='panel'><h2>catalogue page 1 <span>served data &middot; "
            f"{CATALOGUE['total']} products total</span></h2>"
            "<table><tr><th class='num'>sku</th><th>title</th><th class='num'>price</th>"
            f"<th class='num'>stock</th></tr>{items}</table></div>"
            "<div class='foot'>NEXORA local stub &middot; stdlib python, no frameworks &middot; "
            "evidence label: local stub run - never present as AWS or VPS capacity</div>"
            "</div></body></html>"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        rec(time.perf_counter() - self._t0, "/", 200)

    def _throttle(self):
        if ARGS.latency_ms:
            time.sleep(ARGS.latency_ms / 1000.0)

    def do_GET(self):
        self._t0 = time.perf_counter()
        self._throttle()
        path, _, _ = self.path.partition("?")
        if path == "/":
            return self._dashboard()
        if path == "/health":
            return self._send(200, {"status": "ok", "service": "nexora-stub"})
        if path == "/api/catalogue":
            return self._send(200, CATALOGUE)
        if path.startswith("/api/products/"):
            sku = path.rsplit("/", 1)[-1]
            return self._send(200, {"sku": sku, "title": f"NEXORA product {sku}",
                                    "price": 19.99, "stock": 7})
        return self._send(404, {"error": "not found", "path": path})

    def do_POST(self):
        self._t0 = time.perf_counter()
        self._throttle()
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        if self.path == "/api/orders":
            return self._send(201, {
                "orderId": f"ORD-{random.randint(100000, 999999)}",
                "status": "accepted",
                "idempotencyKey": self.headers.get("Idempotency-Key"),
            })
        return self._send(404, {"error": "not found", "path": self.path})


def serve(port, latency_ms, quiet=True):
    """Start the stub server (blocking). Used by run_with_stub.py and main()."""
    global ARGS
    ARGS = argparse.Namespace(port=port, latency_ms=latency_ms)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    if not quiet:
        print(f"nexora stub listening on http://127.0.0.1:{port} "
              f"(latency {latency_ms} ms) - ctrl+c to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        with LOCK:
            if not quiet:
                print(f"stub stopped - {S['total']} requests handled", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--latency-ms", type=int, default=25)
    args = parser.parse_args()
    serve(args.port, args.latency_ms, quiet=False)


if __name__ == "__main__":
    main()
