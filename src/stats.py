#!/usr/bin/env python3
"""Provisional statistics for H1: cluster bootstrap over matters on the
re-scored per-draft rows (rescore_full.json). Contrasts every pressure
condition against baseline, per model, on draft-level existence and
strict-quote rates. LEDGER NOTE: draft-level and provisional — the
citation-level mixed-effects model over full records is the paper's
primary analysis and runs after a records dump; recorded in LEDGER.md."""

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
random.seed(20260901)
B = 2000


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def boot_contrast(base_rows, cond_rows, key):
    matters = sorted({r["matter"] for r in base_rows})
    by_b = {r["matter"]: r for r in base_rows}
    by_c = {r["matter"]: r for r in cond_rows}
    diffs = []
    for _ in range(B):
        sample = [random.choice(matters) for _ in matters]
        b = mean([by_b[m][key] for m in sample if m in by_b])
        c = mean([by_c[m][key] for m in sample if m in by_c])
        if b is not None and c is not None:
            diffs.append(c - b)
    diffs.sort()
    point = mean([by_c[m][key] for m in matters if m in by_c]) - \
        mean([by_b[m][key] for m in matters if m in by_b])
    lo = diffs[int(0.025 * len(diffs))]
    hi = diffs[int(0.975 * len(diffs))]
    return round(point, 4), round(lo, 4), round(hi, 4)


def main():
    data = json.loads((HERE / "results/rescore_full.json").read_text())
    out = {}
    for model, conds in data.items():
        base = conds["baseline"]["rows"]
        for cond in ("quota", "temporal", "stakes", "combo"):
            for key in ("exist", "strict"):
                pt, lo, hi = boot_contrast(base, conds[cond]["rows"], key)
                sig = "*" if (lo > 0 or hi < 0) else " "
                out[f"{model}:{cond}:{key}"] = [pt, lo, hi]
                print(f"{model:10s} {cond:9s} {key:6s} "
                      f"{pt:+.3f} [{lo:+.3f}, {hi:+.3f}] {sig}")
    (HERE / "results/stats_h1_bootstrap.json").write_text(
        json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
