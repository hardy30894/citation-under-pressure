#!/usr/bin/env python3
"""Second-template robustness. The alternative phrasings of every
condition were run on all 48 matters and all seven models
(results/para_<model>/). This script applies Holm correction within
model to the template-B fit (stats_gee_para.json) and to the pooled
two-template fit (stats_gee_pooled.json), computes template-B cell
rates from records_para.jsonl, and lists which template-A survivors
replicate. Writes results/phrasing_stats.json."""

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
R = HERE / "results"


def holm(gee):
    by = defaultdict(list)
    for k, v in gee.items():
        by[k.split(":")[1]].append((k, v["p"]))
    out = {}
    for model, tests in by.items():
        tests.sort(key=lambda t: t[1])
        m = len(tests)
        for i, (k, p) in enumerate(tests):
            out[k] = round(min(1.0, p * (m - i)), 4)
    return out


def cells(path):
    cnt = Counter()
    for l in open(path):
        r = json.loads(l)
        cnt[(r["model"], r["condition"], r["kind"], r["verdict"])] += 1
    out = {}
    models = {k[0] for k in cnt}
    conds = {k[1] for k in cnt}
    for m in models:
        for c in conds:
            ex, nf = cnt[(m, c, "citation", "exists")], cnt[(m, c, "citation", "not_found")]
            acc = cnt[(m, c, "quote", "accurate")]
            sc = acc + cnt[(m, c, "quote", "near_miss")] + cnt[(m, c, "quote", "inaccurate")]
            out[f"{m}:{c}"] = {"exist": round(ex / (ex + nf), 4) if ex + nf else None,
                               "strict": round(acc / sc, 4) if sc else None}
    return out


def main():
    a = json.loads((R / "stats_gee.json").read_text())
    b = json.loads((R / "stats_gee_para.json").read_text())
    pooled = json.loads((R / "stats_gee_pooled.json").read_text())
    ha, hb, hp = holm(a), holm(b), holm(pooled)
    surv_a = sorted(k for k, v in ha.items() if v < 0.05)
    surv_b = sorted(k for k, v in hb.items() if v < 0.05)
    surv_p = sorted(k for k, v in hp.items() if v < 0.05)
    full = json.loads((R / "rescore_full.json").read_text())
    cb = cells(R / "records_para.jsonl")
    ds = [abs(full[m][c]["strict_rate"] - v["strict"]) for k, v in cb.items()
          for m, c in [k.split(":")] if v["strict"] is not None]
    de = [abs(full[m][c]["existence_rate"] - v["exist"]) for k, v in cb.items()
          for m, c in [k.split(":")] if v["exist"] is not None]
    out = {
        "max_strict_diff_ab": round(max(ds), 4), "max_exist_diff_ab": round(max(de), 4),
        "holm_b": hb, "holm_pooled": hp,
        "survivors_a": surv_a, "survivors_b": surv_b, "survivors_pooled": surv_p,
        "a_replicated_in_b": sorted(set(surv_a) & set(surv_b)),
        "a_replicated_pooled": sorted(set(surv_a) & set(surv_p)),
        "b_only": sorted(set(surv_b) - set(surv_a)),
        "cells_b": cb,
        "gee_b": b, "gee_pooled": pooled,
    }
    (R / "phrasing_stats.json").write_text(json.dumps(out, indent=1))
    print("A survivors:", surv_a)
    print("B survivors:", surv_b)
    print("pooled survivors:", surv_p)
    print("A replicated in B:", out["a_replicated_in_b"])
    print("A replicated pooled:", out["a_replicated_pooled"])


if __name__ == "__main__":
    main()
