# nexora simulation evidence (one page)

status: the results folder was emptied — the earlier k6 txt summaries are
gone. regenerate everything in one session (~35 min, your own console,
progress visible). any number cited in the defense must come from the txt
files this session produces.

label (same rules as the deck): local stub run — not aws, not vps.
it measures the harness, not the architecture.

## the one session (in this order, one at a time)

window 1 — stub, leave open the whole time:

    cd "E:\University\cloud architecture\Final Project\Kit\simulation"
    python stub_api.py

window 2 — k6, with task manager open on performance > cpu:

    cd "E:\University\cloud architecture\Final Project\Kit\iac"

    k6 run -e BASE_URL=http://127.0.0.1:8080 .\normal-load.js 2>&1 |
      Tee-Object -FilePath ..\simulation\results\normal-results.txt
    # 10 min. let it finish. screenshot task manager mid-run.

    k6 run -e BASE_URL=http://127.0.0.1:8080 .\peak-load.js 2>&1 |
      Tee-Object -FilePath ..\simulation\results\peak-results.txt
    # ~15 min. let it finish — this laptop already held 200 VUs once.

    k6 run -e BASE_URL=http://127.0.0.1:8080 .\spike-load.js 2>&1 |
      Tee-Object -FilePath ..\simulation\results\spike-results.txt
    # ~6 min. if the machine struggles: ctrl+c. the summary still prints
    # and tee still saves the txt. either outcome is a valid result —
    # just record which one you got.

short on time: ctrl+c normal and peak after 3–4 min each. k6 prints the
full summary on interrupt and tee saves it. minimum viable set =
one full normal run + one task-manager screenshot.

## evidence set when done

    results/
        normal-results.txt
        peak-results.txt
        spike-results.txt
        laptop-cpu.png   (task manager, taken during the peak run)

## fill in after the runs (copy from each END OF TEST summary)

measured 26 Nov 2026, ~22:00–22:40, via run_with_stub.py (stub 25 ms latency,
loopback 127.0.0.1:8080). all three profiles passed their thresholds.

| run | duration | requests | req/s | p95 | p99 | failures | thresholds | verdict |
|---|---|---|---|---|---|---|---|---|
| normal | 10m01s | 33,420 | 55.6 | 27.32 ms | — | 0.01% (4) | p95 < 500 ms, fail < 1% | PASS |
| peak | 15m02s | 329,484 | 365.4 | 26.62 ms | 29.49 ms | 0.00% (5) | p95 < 800 ms, p99 < 1500, fail < 2% | PASS |
| spike | 6m13s | 191,721 | 514.5 | 26.02 ms | — | 0.00% (5) | p95 < 2000 ms, fail < 5% | PASS — 400 VUs reached and held |

files: results/normal-results.txt + normal.json, peak-results.txt + peak.json,
spike-results.txt + spike.json. still to add: one task-manager screenshot
taken during a run.

## demo day (runbook section 5 has the full version)

live demo = normal profile only, one command:

    cd "E:\University\cloud architecture\Final Project\Kit\simulation"
    python run_with_stub.py ..\iac\normal-load.js results\demo.json

let it run 40–60 s while speaking, ctrl+c once, summary prints.
never run peak or spike live. everything is 127.0.0.1 — venue wifi
cannot break it. fallback: the saved txts in results/.
