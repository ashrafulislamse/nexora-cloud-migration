#!/usr/bin/env python3
"""Run one k6 profile against the NEXORA stub in a single foreground
process - stub runs as a daemon thread, k6 as a subprocess, both die
cleanly when this script exits. Use this when you want everything in
one terminal window (no second window to keep open).

    python run_with_stub.py <script.js> <summary-export.json> [port]

Example:
    python run_with_stub.py ../iac/normal-load.js results/normal.json
"""
import http.client
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stub_api


def main():
    if len(sys.argv) < 3:
        print("usage: run_with_stub.py <script.js> <summary.json> [port]")
        return 2
    script, summary = sys.argv[1], sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8080

    t = threading.Thread(target=stub_api.serve, args=(port, 25), daemon=True)
    t.start()

    ok = False
    for _ in range(20):
        try:
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=0.5)
            c.request("GET", "/health")
            ok = c.getresponse().status == 200
            c.close()
            if ok:
                break
        except OSError:
            time.sleep(0.2)
    if not ok:
        print("stub failed to start - aborting")
        return 1
    print(f"[stub ready on 127.0.0.1:{port}]")
    print(f"[dashboard: http://127.0.0.1:{port}/ - open in a browser tab]")

    proc = subprocess.Popen([
        "k6", "run",
        "-e", f"BASE_URL=http://127.0.0.1:{port}",
        "--summary-export", summary,
        script,
    ])
    interrupted = False
    try:
        rc = proc.wait()
    except KeyboardInterrupt:
        # ctrl+c also reaches k6 (same console): it shuts down gracefully
        # and prints the end-of-test summary. wait for it to finish.
        interrupted = True
        rc = proc.wait()
    print(f"[k6 exited with {rc}{' (interrupted - summary above)' if interrupted else ''}]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
