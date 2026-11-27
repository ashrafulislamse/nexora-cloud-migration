# nexora local simulation runbook (laptop only)

goal: run the three shipped k6 profiles against a local stub api so the
harness is demonstrated end to end. the evidence claim is "the harness
works and thresholds behave as design targets" — not aws capacity numbers.

honesty labels (same rules as the deck):
- the stub returns static json. it measures the harness, not the architecture.
- say "local stub run" in every mention. never "aws", never "vps".
- nothing here changes the shipped deck or the shipped zip.

## prerequisites (one install)

- python 3.12 — already installed (check: `python --version`)
- k6 — `winget install k6 --source winget`, then reopen powershell,
  `k6 version` should print a version

no docker, no mockoon desktop, no vps needed.

## 1. start the stub

```powershell
cd "E:\University\cloud architecture\Final Project\Kit\simulation"
python stub_api.py
```

leave this window open. it listens on 127.0.0.1:8080 and serves:
- GET /health → 200
- GET /api/catalogue?page=1 → 200
- GET /api/products/SKU-123 → 200
- POST /api/orders → 201 (echoes the idempotency key)

if port 8080 is busy: `python stub_api.py --port 18080` and use
`-e BASE_URL=http://127.0.0.1:18080` in every k6 command below.

## 2. smoke test (30 seconds)

second powershell window:

```powershell
curl.exe http://127.0.0.1:8080/health
curl.exe "http://127.0.0.1:8080/api/catalogue?page=1"
```

both should return json. if not, fix the stub window first.

## 3. run the three profiles (one at a time, stub window stays open)

from the `Kit\iac` folder (the shipped scripts, unmodified):

```powershell
cd "E:\University\cloud architecture\Final Project\Kit\iac"
mkdir -Force ..\simulation\results | Out-Null

k6 run -e BASE_URL=http://127.0.0.1:8080 .\normal-load.js 2>&1 |
  Tee-Object -FilePath ..\simulation\results\normal-results.txt
```

then peak, then spike (never in parallel):

```powershell
k6 run -e BASE_URL=http://127.0.0.1:8080 .\peak-load.js 2>&1 |
  Tee-Object -FilePath ..\simulation\results\peak-results.txt

k6 run -e BASE_URL=http://127.0.0.1:8080 .\spike-load.js 2>&1 |
  Tee-Object -FilePath ..\simulation\results\spike-results.txt
```

| profile | script | duration | expect |
|---|---|---|---|
| normal trading | normal-load.js | 10 min | thresholds pass |
| campaign ramp | peak-load.js | ~15 min | thresholds pass, rps grows |
| flash spike | spike-load.js | ~6 min | thresholds may breach — that is the finding, record where it crosses |

short on time: ctrl+c each run after 2–3 min. k6 prints the full
end-of-test summary on interrupt. an interrupted run is still a
demonstration, just say so.

## 4. capture laptop resource evidence

while the peak run is going: task manager → performance → cpu and memory
screenshots into `Kit\simulation\results\`. one screenshot is enough —
this is supporting colour, not the headline.

evidence set = 3 k6 txt summaries + 1 task manager png.

## 5. the live demo during the presentation

one window only (the wrapper runs stub + k6 together):

```powershell
cd "E:\University\cloud architecture\Final Project\Kit\simulation"
python run_with_stub.py ..\iac\normal-load.js results\demo.json
```

**before the session starts (not during):**
- open this window, recall the command with arrow-up so it is ready
- terminal font big (ctrl+= in windows terminal, or properties > font 22+)
- laptop plugged in, browser/word/chrome closed
- results folder open in explorer as backup

**during slide 15 (M4, ~60 seconds):**
1. alt-tab out of the slideshow to the terminal
2. enter - the progress bar appears live (20 VUs, ~56 req/s)
3. let it run 40-60 s while you speak
4. ctrl+c - k6 shuts down gracefully and prints the summary
5. point at the three numbers: req rate, p95, failures
6. alt-tab back to the slideshow

**the line to say while it runs:**
"harness demo - this is the shipped normal-trading profile against our
stub server: 20 virtual users, about 56 requests a second, p95 in the
high 20s of milliseconds, error rate under 0.01 percent. the thresholds
on the slide are the design targets and the harness holds them. the
numbers describe the stub, not the aws architecture - the terraform
stays a labelled prototype."

**if the panel asks for bigger numbers:** switch to the saved files and
show peak-results.txt - 328,278 requests, 365 req/s at 200 VUs,
p95 26 ms - "run from yesterday, same profile that ships in the zip."

**if the panel asks for the spike:** show the saved spike-results.txt -
400 VUs reached, five failed requests in 191,721 (startup refusals before
the stub was listening), interrupted at 2m40s on a small laptop. say "the
400-VU hold needs the target hardware, not this laptop" - which is exactly
the autoscaling argument.

**tonight, test the interrupt once:** start the demo command, ctrl+c
after 30 s, confirm the summary prints. that is the whole rehearsal.

**never run the spike profile live** - it will lag the machine in front
of the panel. spike is a saved file, normal is the live demo.

## 6. defense lines (one per likely question)

- "is this aws?" — no. it is the load harness verified end to end against
  a stub server. the aws terraform remains a prototype, unapplied, per the
  assumptions register.
- "what did you measure?" — that the profile shapes, thresholds and error
  handling behave as designed. stub latency is in-memory, so absolute
  numbers are not capacity claims.
- "why no aws run?" — the brief accepts load-generation scripts "(if any)".
  we kept the prototype labelled and unapplied rather than claim
  production evidence.

## do not

- do not touch the digitalocean droplet, coolify or any live site
- do not edit the shipped k6 scripts — they are canonical and shipped in
  the zip
- do not add stub numbers to any slide — speak to the demo instead
- do not label any of this aws, ecs, or vps evidence

## weak laptop / minimum viable

k6 (light go binary) + the stdlib stub stay under ~1 GB RAM even at 400 VUs.
- normal profile: ~30 req/s — trivial, any laptop
- peak: ctrl+c after 2 min is fine (only 60 VUs in at that point)
- spike: a small laptop will saturate — that is the spike profile doing
  its job. record where the error rate crosses the threshold, then stop.
- minimum viable evidence: one 60-90 s normal run + saved txt + one
  task-manager screenshot.

presentation day on a weak laptop: pre-run the profile before the
session, show the saved txt — do not run it live.

## stop conditions

laptop cpu pegged and k6 error rate climbing on the spike profile:
expected — that is the spike profile doing its job on a small machine.
record the crossover point and move on. nothing is failing.
