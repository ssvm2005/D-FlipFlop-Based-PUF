import csv, re, itertools
from pathlib import Path
import numpy as np
import pandas as pd

# Configuration
CSV_FILE = Path("mc200dis1_excel.csv")
RESPONSE_BITS = 8
OUT_DIR = Path(f"puf_{RESPONSE_BITS}bit_midpoint_results")
VTH, CONTROL_LOW_MAX = 0.9, 0.2
WINDOWS_NS = [(25, 50), (75, 100), (125, 150), (175, 200),
              (225, 250), (275, 300), (325, 350), (375, 385)]
EXPECTED_RUNS = 200

if not CSV_FILE.exists():
    raise FileNotFoundError(f"CSV not found: {CSV_FILE.resolve()}")

with CSV_FILE.open("r", newline="", encoding="utf-8-sig") as f:
    headers = [h.strip() for h in next(csv.reader(f))]

def build_map(pattern):
    result, regex = {}, re.compile(pattern, re.IGNORECASE)
    for i, header in enumerate(headers):
        m = regex.fullmatch(header)
        if m:
            if i == 0:
                raise ValueError(f"Missing time column before {header}")
            run = int(m.group(1))
            if run in result:
                raise ValueError(f"Duplicate matching column for MC{run}")
            result[run] = (i - 1, i)
    return result

clk_map = build_map(r"/clk mcparamset (\d+)\s+\(V\)")
puf_map = build_map(r"/puf mcparamset (\d+)\s+\(V\)")
q_map = {
    b: build_map(rf"/Q<{RESPONSE_BITS-1}:0> bit /Q<{b}> mcparamset (\d+)\s+\(V\)")
    for b in range(RESPONSE_BITS)
}
runs = sorted(set(clk_map) & set(puf_map))
for b in range(RESPONSE_BITS):
    runs = sorted(set(runs) & set(q_map[b]))
if len(runs) != EXPECTED_RUNS:
    raise ValueError(f"Expected {EXPECTED_RUNS} complete MC runs; found {len(runs)}. Check CSV headers.")

needed = set()
for r in runs:
    needed.update(clk_map[r])
    needed.update(puf_map[r])
    for b in range(RESPONSE_BITS):
        needed.update(q_map[b][r])
needed = sorted(needed)
raw = pd.read_csv(CSV_FILE, usecols=needed, low_memory=False, encoding="utf-8-sig").apply(pd.to_numeric, errors="coerce")
col_pos = {original: pos for pos, original in enumerate(needed)}

def get_trace(pair, run):
    ti, vi = pair
    t = raw.iloc[:, col_pos[ti]].to_numpy(float)
    v = raw.iloc[:, col_pos[vi]].to_numpy(float)
    valid = np.isfinite(t) & np.isfinite(v)
    t, v = t[valid], v[valid]
    if not len(t):
        raise ValueError(f"No valid samples for MC{run}")
    if np.any(np.diff(t) < 0):
        raise ValueError(f"Time decreases for MC{run}")
    return t, v

def nearest_idx(t, target):
    right = np.searchsorted(t, target, side="left")
    candidates = [i for i in (right - 1, right) if 0 <= i < len(t)]
    if not candidates:
        raise ValueError("Target is outside the saved waveform.")
    i = min(candidates, key=lambda j: (abs(t[j] - target), -t[j]))
    return int(np.searchsorted(t, t[i], side="right") - 1)

def make_response(qv):
    return "".join("1" if qv[b] >= VTH else "0" for b in range(RESPONSE_BITS - 1, -1, -1))

OUT_DIR.mkdir(parents=True, exist_ok=True)
voltage_rows, validation_rows, metric_rows, alias_rows, pair_rows = [], [], [], [], []
print(f"Input: {CSV_FILE.resolve()}\nMonte Carlo runs: {len(runs)}\nResponse width: {RESPONSE_BITS} bits (Q{RESPONSE_BITS-1} to Q0)")

for wi, (start_ns, end_ns) in enumerate(WINDOWS_NS, 1):
    midpoint_ns = (start_ns + end_ns) / 2
    target_s = midpoint_ns * 1e-9
    responses_by_run, window_valid = {}, True

    for run in runs:
        t_clk, v_clk = get_trace(clk_map[run], run)
        t_puf, v_puf = get_trace(puf_map[run], run)
        q_traces = {b: get_trace(q_map[b][run], run) for b in range(RESPONSE_BITS)}
        same_grid = (len(t_clk) == len(t_puf) and np.allclose(t_clk, t_puf, rtol=0, atol=1e-18))
        for tq, _ in q_traces.values():
            if len(tq) != len(t_clk) or not np.allclose(tq, t_clk, rtol=0, atol=1e-18):
                same_grid = False

