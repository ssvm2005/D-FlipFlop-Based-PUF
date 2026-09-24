"""
Reliability calculation for 8-bit DFF PUF (/Q<7:0>) across PVT corners.
Reference = nominal (tt_18, vdd=1.8, temp=27).
Reliability = 100% - average Hamming distance across all 36 non-nominal corners.
“””

import pandas as pd
import numpy as np
import re

# ---------------- CONFIG ----------------
PVT_FILE_PATH = "pvt_excel.csv"
SIGNAL_BASE = "/Q"
N_BITS = 8
VDD_NOMINAL = 1.8
TEMP_NOMINAL = 27
NOMINAL_CORNER = "tt_18"
# -----------------------------------------


def parse_condition(col_name):
    m = re.search(
        r"ts18sl_scl(?:_mat)?\.lib:(\w+)\s+vdd\s+([\d.]+)\s+temperature\s+(-?\d+)",
        col_name
    )
    if not m:
        return None
    return m.group(1), float(m.group(2)), int(m.group(3))


def parse_bit(col_name, signal_base):
    m = re.search(rf"(?<!Qbar){re.escape(signal_base)}<(\d+)>", col_name)
    if not m:
        return None
    return int(m.group(1))


# ---------------- LOAD FILE ----------------
raw = pd.read_csv(PVT_FILE_PATH, sep=',', engine="python", encoding="utf-8")

print(f"DEBUG: shape = {raw.shape}")
if raw.shape[1] < 10:
    raise ValueError(
        f"Only {raw.shape[1]} columns parsed — separator detection failed."
    )


# ---------------- BUILD condition -> {bit: column} MAP ----------------
conditions = {}

for col in raw.columns:
    bit = parse_bit(str(col), SIGNAL_BASE)
    if bit is None or not (0 <= bit < N_BITS):
        continue

    cond = parse_condition(str(col))
    if cond is None:
        continue

    conditions.setdefault(cond, {})[bit] = col

print(f"Detected {len(conditions)} PVT conditions")


# ---------------- EXTRACT FINAL BIT VALUE ----------------
def get_final_bit(col_name, vdd_used):
    series = pd.to_numeric(raw[col_name], errors="coerce").dropna()

    if len(series) == 0:
        raise ValueError(f"No numeric data in column: {col_name}")

    final_val = series.iloc[-1]

    # FIXED THRESHOLD = 0.9 V FOR ALL PVT CONDITIONS
    return 1 if final_val >= 0.9 else 0


def extract_response(condition):
    process, vdd, temp = condition

    bits = np.zeros(N_BITS, dtype=int)

    for bit in range(N_BITS):
        col = conditions[condition].get(bit)

        if col is None:
            raise ValueError(
                f"Missing Q<{bit}> for condition {condition}"
            )

        bits[bit] = get_final_bit(col, vdd)

    return bits


# ---------------- NOMINAL REFERENCE ----------------
nominal_condition = (
    NOMINAL_CORNER,
    VDD_NOMINAL,
    TEMP_NOMINAL
)

if nominal_condition not in conditions:
    print(
        "Available conditions (sample):",
        sorted(conditions)[:10]
    )
    raise ValueError(
        f"Nominal condition {nominal_condition} not found."
    )

reference = extract_response(nominal_condition)

print(
    f"\nNominal reference bits: {reference.tolist()}"
)


# ---------------- ALL NON-NOMINAL CORNERS ----------------
test_conditions = sorted(
    c for c in conditions
    if c != nominal_condition
)

print(
    f"Non-nominal test corners: {len(test_conditions)}  (expect 36)"
)


# ---------------- HAMMING DISTANCE ACROSS ALL CORNERS ----------------
hd_values = []

print("\nPer-corner results:")
print("-" * 80)

for condition in test_conditions:

    process, vdd, temp = condition

    response = extract_response(condition)

    hd = np.sum(reference != response)

    hd_percent = (hd / N_BITS) * 100

    hd_values.append(hd_percent)

    print(
        f"{process:6s} | "
        f"VDD={vdd:.2f}V | "
        f"T={temp:4d}C | "
        f"Response={response.tolist()} | "
        f"HD={hd_percent:5.1f}%"
    )


if len(hd_values) == 0:
    raise ValueError(
        "No test conditions collected — cannot compute reliability."
    )


HD_INTRA = np.mean(hd_values)

RELIABILITY = 100 - HD_INTRA


print("\n" + "=" * 80)

print(
    f"Number of corners : {len(hd_values)}"
)

print(
    f"HD_INTRA           : {HD_INTRA:.2f}%"
)

print(
    f"RELIABILITY        : {RELIABILITY:.2f}%   (ideal = 100%)"
)

print("=" * 80)
