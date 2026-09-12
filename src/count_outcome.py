#!/usr/bin/env python3
"""Accurate quotations per draft, as an outcome in its own right.

The strict rate is conditional on quoting: it is computed over the
quotations a draft attributes to a case, and the size of that set moves
with the condition. This script reports, for every model and condition,
quotations per draft, the paired share (attributed and scored over all
extracted), accurate and inaccurate quotations per draft, and then tests
the count of accurate quotations per draft against baseline with a
Wilcoxon signed-rank test paired by matter (n = 48), Holm within model
over the four conditions. For the strongest model it also reports the
mean length in words of the accurate and the inaccurate quotations by
condition, the check on the reading that the model dropped inaccurate
quotations rather than shortening them. Reads results/records.jsonl and
results/records_quotes.jsonl when present; writes
results/count_outcome.json."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from scipy import stats

HERE = Path(__file__).resolve().parents[1]
R = HERE / "results"
CONDS = ["baseline", "quota", "temporal", "stakes", "combo"]
N_MATTERS = 48


def main():
    cell = defaultdict(Counter)
    per = defaultdict(lambda: defaultdict(Counter))
    import sys as _s
    rec = _s.argv[_s.argv.index("--records") + 1] if "--records" in _s.argv else "records.jsonl"
    outname = _s.argv[_s.argv.index("--out") + 1] if "--out" in _s.argv else "count_outcome.json"
    for l in open(R / rec):
        r = json.loads(l)
        if r["kind"] != "quote":
            continue
        c = cell[(r["model"], r["condition"])]
        c["all"] += 1
        per[r["model"]][r["matter"]][r["condition"] + "_all"] += 1
        if r["verdict"] in ("accurate", "near_miss", "inaccurate"):
            c["scored"] += 1
            c["acc"] += r["verdict"] == "accurate"
            c["inacc"] += r["verdict"] != "accurate"
            per[r["model"]][r["matter"]][r["condition"] + "_acc"] += r["verdict"] == "accurate"
    out = {"cells": {}, "tests": {}}
    for model in sorted(per):
        for cond in CONDS:
            x = cell[(model, cond)]
            out["cells"][f"{model}:{cond}"] = {
                "quotes": x["all"], "scored": x["scored"], "accurate": x["acc"], "inaccurate": x["inacc"],
                "quotes_per_draft": round(x["all"] / N_MATTERS, 2),
                "paired_share": round(x["scored"] / x["all"], 3) if x["all"] else None,
                "acc_per_draft": round(x["acc"] / N_MATTERS, 2),
                "inacc_per_draft": round(x["inacc"] / N_MATTERS, 2),
                "rate": round(x["acc"] / x["scored"], 3) if x["scored"] else None}
        tests = {}
        matters = sorted(per[model])
        base = [per[model][m]["baseline_acc"] for m in matters]
        for cond in CONDS[1:]:
            other = [per[model][m][cond + "_acc"] for m in matters]
            d = [b - a for a, b in zip(base, other)]
            try:
                p = float(stats.wilcoxon(d, zero_method="wilcox").pvalue)
            except ValueError:
                p = 1.0
            tests[cond] = {"base_mean": round(sum(base) / len(base), 3), "cond_mean": round(sum(other) / len(other), 3),
                           "mean_diff": round(sum(d) / len(d), 3), "p": round(p, 4), "n_pairs": len(d)}
        ranked = sorted(tests, key=lambda c: tests[c]["p"])
        for i, c in enumerate(ranked):
            tests[c]["holm_p"] = round(min(1.0, tests[c]["p"] * (len(ranked) - i)), 4)
        for c in CONDS[1:]:
            out["tests"][f"{model}:{c}"] = tests[c]
    # quotation length for the strongest model, by verdict and condition
    qfile = R / "records_quotes.jsonl"
    if qfile.exists():
        ln = defaultdict(list)
        for l in open(qfile):
            r = json.loads(l)
            if r["model"] == "sonnet" and r["verdict"] in ("accurate", "near_miss", "inaccurate"):
                ln[(r["condition"], "accurate" if r["verdict"] == "accurate" else "inaccurate")].append(len(r["quote"].split()))
        out["sonnet_length"] = {f"{c}:{v}": round(sum(x) / len(x), 1) for (c, v), x in ln.items() if x}
    (R / outname).write_text(json.dumps(out, indent=1))
    surv = [k for k, v in out["tests"].items() if v["holm_p"] < 0.05]
    print("count contrasts surviving Holm within model:", len(surv), surv)
    for k, v in out["tests"].items():
        print(f"{k:24s} {v['base_mean']:.2f} -> {v['cond_mean']:.2f} p={v['p']:.4f} holm={v['holm_p']:.4f} n={v['n_pairs']}")


if __name__ == "__main__":
    main()
