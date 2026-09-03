#!/usr/bin/env python3
"""Primary inference for Experiment 1: citation-level logistic GEE per
model, condition dummies against baseline, exchangeable working
correlation within matter. Writes results/stats_gee.json with the odds
ratio, its 95 percent confidence interval, and the Wald p for every
model x condition x outcome contrast.

Outcomes: citation existence (exists vs not_found, unresolvable dropped)
and strict quotation accuracy (accurate vs near_miss or inaccurate,
unverifiable dropped)."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parents[1]
R = HERE / "results"
CONDS = ["quota", "temporal", "stakes", "combo"]


def fit(df, model, kind):
    sub = df[(df.model == model) & (df.kind == kind)].copy()
    if kind == "citation":
        sub = sub[sub.verdict.isin(["exists", "not_found"])]
        sub["y"] = (sub.verdict == "exists").astype(int)
    else:
        sub = sub[sub.verdict.isin(["accurate", "near_miss", "inaccurate"])]
        sub["y"] = (sub.verdict == "accurate").astype(int)
    sub["condition"] = pd.Categorical(
        sub.condition, categories=["baseline"] + CONDS)
    res = smf.gee("y ~ C(condition)", groups="matter", data=sub,
                  family=sm.families.Binomial(),
                  cov_struct=sm.cov_struct.Exchangeable()).fit()
    out = {}
    for c in CONDS:
        term = f"C(condition)[T.{c}]"
        b, se = res.params[term], res.bse[term]
        out[c] = {"OR": round(float(np.exp(b)), 3),
                  "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
                  "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
                  "p": round(float(res.pvalues[term]), 5),
                  "n": int(len(sub))}
    return out


def main():
    df = pd.DataFrame(json.loads(l) for l in open(R / "records.jsonl"))
    out = {}
    for model in sorted(df.model.unique()):
        for kind in ("citation", "quote"):
            for c, v in fit(df, model, kind).items():
                out[f"{kind}:{model}:{c}"] = v
    (R / "stats_gee.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        if v["p"] < 0.05:
            print(f"{k:32s} OR {v['OR']:.2f} [{v['ci_low']:.2f}, "
                  f"{v['ci_high']:.2f}] p={v['p']}")


if __name__ == "__main__":
    main()
