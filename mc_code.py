"""
Extracts 8-bit PUF responses (/Q<7:0>) from Monte Carlo CSV (100 chips)
and computes Uniformity, Bit-aliasing, Uniqueness.
"""

import pandas as pd
import numpy as np
import itertools
import re

# ---------------- CONFIG ----------------
MC_FILE_PATH = "mc_100_8bit_excel.csv"
SIGNAL_BASE = "/Q"        # PUF response node (NOT /D, NOT /Qbar)
SEPARATOR = ","
VDD = 1.8
THRESHOLD = VDD / 2
N_BITS = 8
# -----------------------------------------


def extract_mc_bits(path, signal_base, sep, threshold, n_bits):
    raw = pd.read_csv(path, sep=sep, encoding="utf-8")
    ncols = raw.shape[1]

    print("Sample columns found in file:")
    for c in raw.columns[1:6]:
        print(" ", repr(c))
    print("...")

    bit_data = {b: {} for b in range(n_bits)}

    col = 0
    while col < ncols - 1:
        val_col = raw.columns[col + 1]

        # IMPORTANT: exact match on "/Q<n>" — avoids accidentally matching /Qbar
        m = re.search(
            rf"(?<!Qbar){re.escape(signal_base)}<(\d+)>.*mcparamset\s+(\d+)",
            val_col
        )
        if m:
            bit_idx = int(m.group(1))
            run_idx = int(m.group(2))
            if bit_idx in bit_data:
                bit_data[bit_idx][run_idx] = val_col

        col += 2

    total_matches = sum(len(d) for d in bit_data.values())
    print(f"\nTotal signal columns matched: {total_matches}")
    if total_matches == 0:
        raise ValueError(
            f"No columns matched signal_base='{signal_base}'. Check printed sample columns above."
        )

    all_runs = sorted(set().union(*[d.keys() for d in bit_data.values()]))
    n_chips = len(all_runs)
    print(f"Detected {n_chips} chips (mcparamset runs)")

    matrix = np.zeros((n_chips, n_bits), dtype=int)

    for bit_idx in range(n_bits):
        for i, run in enumerate(all_runs):
            col_name = bit_data[bit_idx].get(run)
            if col_name is None:
                continue
            series = pd.to_numeric(raw[col_name], errors="coerce").dropna()
            if len(series) > 0:
                final_val = series.iloc[-1]
                matrix[i, bit_idx] = 1 if final_val >= threshold else 0

    return matrix


def uniformity(bit_matrix):
    per_chip = bit_matrix.mean(axis=1) * 100
    return per_chip.mean(), per_chip


def bit_aliasing(bit_matrix):
    per_bit = bit_matrix.mean(axis=0) * 100
    return per_bit.mean(), per_bit


def uniqueness(bit_matrix):
    n_chips, n_bits = bit_matrix.shape
    total = 0
    count = 0
    for i, j in itertools.combinations(range(n_chips), 2):
        hd = np.sum(bit_matrix[i] != bit_matrix[j])
        total += hd / n_bits
        count += 1
    return (total / count) * 100


if __name__ == "__main__":
    bits = extract_mc_bits(MC_FILE_PATH, SIGNAL_BASE, SEPARATOR, THRESHOLD, N_BITS)
    print(f"\nExtracted matrix shape: {bits.shape}  (chips x bits)")
    print(f"Sample rows:\n{bits[:5]}")

    unif_avg, unif_per_chip = uniformity(bits)
    alias_avg, alias_per_bit = bit_aliasing(bits)
    uniq = uniqueness(bits)

    print(f"\nUniformity   : {unif_avg:.2f}%   (ideal = 50%)")
    print(f"Bit-aliasing : {alias_avg:.2f}%   (ideal = 50%)")
    print(f"  per-bit    : {np.round(alias_per_bit, 2)}")
    print(f"Uniqueness   : {uniq:.2f}%   (ideal = 50%)")
