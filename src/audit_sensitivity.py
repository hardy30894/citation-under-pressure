#!/usr/bin/env python3
"""Carry the audited checker error into the quotation contrasts.

The hand reading of 160 inaccurate verdicts (results/attribution_sample_
reading.json) found a share of them on the checker's side, and the share
differs by condition. This script asks what the pre-registered quotation
contrasts look like once that error is removed. In each of N draws every
inaccurate verdict in records.jsonl is reclassified as unpaired (dropped
from the scored set) with the probability the audit measured for its
condition, the citation records are left as they are, and gee.fit is
rerun for every model with Holm over the same family of eight tests as
the primary fit. Two variants are run: the observed shares, and the
upper end of each condition's 95 percent Wilson interval, which is the
pessimistic case. For each quotation contrast the output gives the share
of draws in which it survives Holm, the median odds ratio, and the
survival of the citation contrasts is reported for the record (they do
not move). Writes results/audit_sensitivity.json."""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
R = HERE / "results"
from gee import fit, CONDS  # noqa: E402

N = 200


def wilson_high(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c + h


def holm(out, model):
    tests = sorted([k for k in out if k.split(":")[1] == model], key=lambda k: out[k]["p"])
    m = len(tests)
    for i, k in enumerate(tests):
        out[k]["holm_p"] = min(1.0, out[k]["p"] * (m - i))


def main():
    audit = json.loads((R / "attribution_sample_reading.json").read_text())
    shares = {c: v["checker_side"] / v["read"] for c, v in audit["by_condition"].items()}
    highs = {c: wilson_high(v["checker_side"], v["read"]) for c, v in audit["by_condition"].items()}
    df = pd.DataFrame(json.loads(l) for l in open(R / "records.jsonl"))
    df["template"] = "A"
    primary = json.loads((R / "stats_gee.json").read_text())
    rng = np.random.default_rng(20260904)
    models = sorted(df.model.unique())
    # citation fits do not change between draws
    cit = {}
    for model in models:
        for c, v in fit(df, model, "citation").items():
            cit[f"citation:{model}:{c}"] = v
    result = {"n_draws": N, "shares": shares, "wilson_high": highs, "variants": {}}
    inacc = (df.kind == "quote") & (df.verdict == "inaccurate")
    for name, share in (("observed", shares), ("upper", highs)):
        surv = {}
        ors = {}
        for _ in range(N):
            p = df.condition.map(share).fillna(0).values
            drop = inacc.values & (rng.random(len(df)) < p)
            d = df[~drop]
            out = dict(cit)
            for model in models:
                for c, v in fit(d, model, "quote").items():
                    out[f"quote:{model}:{c}"] = v
                holm(out, model)
            for k, v in out.items():
                surv[k] = surv.get(k, 0) + (v["holm_p"] < 0.05)
                ors.setdefault(k, []).append(v["OR"])
        result["variants"][name] = {
            k: {"survival": round(surv[k] / N, 3), "median_OR": round(float(np.median(ors[k])), 3),
                "primary_OR": primary[k]["OR"], "primary_holm_p": primary[k]["holm_p"]}
            for k in sorted(surv)}
        print(name, {k: v for k, v in result["variants"][name].items() if v["primary_holm_p"] < 0.05 or v["survival"] > 0}, flush=True)
    (R / "audit_sensitivity.json").write_text(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
