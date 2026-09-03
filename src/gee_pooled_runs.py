#!/usr/bin/env python3
"""Robustness fit over the three generations of the baseline and combined
conditions (full, rep2, rep3): the same citation-level logistic GEE as
gee.py, clustered by matter, with a fixed effect for the run, on the
combined-versus-baseline contrast only. Holm correction is over the 14
tests (seven models, two outcomes). Writes results/stats_gee_runs.json."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parents[1]
R = HERE / "results"


def main():
    frames = []
    for run, fn in (("full", "records.jsonl"), ("rep2", "records_rep2.jsonl"),
                    ("rep3", "records_rep3.jsonl")):
        df = pd.DataFrame(json.loads(l) for l in open(R / fn))
        df = df[df.condition.isin(["baseline", "combo"])]
        df["run"] = run
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    out = {}
    for model in sorted(df.model.unique()):
        for kind in ("citation", "quote"):
            sub = df[(df.model == model) & (df.kind == kind)].copy()
            if kind == "citation":
                sub = sub[sub.verdict.isin(["exists", "not_found"])]
                sub["y"] = (sub.verdict == "exists").astype(int)
            else:
                sub = sub[sub.verdict.isin(["accurate", "near_miss", "inaccurate"])]
                sub["y"] = (sub.verdict == "accurate").astype(int)
            sub["combo"] = (sub.condition == "combo").astype(int)
            res = smf.gee("y ~ combo + C(run)", groups="matter", data=sub,
                          family=sm.families.Binomial(),
                          cov_struct=sm.cov_struct.Exchangeable()).fit()
            b, se = res.params["combo"], res.bse["combo"]
            out[f"{kind}:{model}:combo"] = {
                "OR": round(float(np.exp(b)), 3),
                "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
                "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
                "p": float(res.pvalues["combo"]), "n": int(len(sub))}
    tests = sorted(out.items(), key=lambda kv: kv[1]["p"])
    m = len(tests)
    for i, (k, v) in enumerate(tests):
        v["holm_p"] = round(min(1.0, v["p"] * (m - i)), 4)
        v["p"] = round(v["p"], 5)
    (R / "stats_gee_runs.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        print(f"{k:28s} OR {v['OR']:.2f} [{v['ci_low']:.2f}, {v['ci_high']:.2f}] "
              f"p={v['p']} holm={v['holm_p']}{' *' if v['holm_p'] < 0.05 else ''}")


if __name__ == "__main__":
    main()
