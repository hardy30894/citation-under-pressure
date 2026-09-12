#!/usr/bin/env python3
"""A matter-level cluster bootstrap beside the GEE, for the sparse cells.

The primary fit is a logistic GEE with an exchangeable working
correlation and 48 clusters. Sandwich standard errors are consistent as
the number of clusters grows, and some of the cells this paper reports
are thin: the existence outcome for the strongest models turns on a
handful of citations not found per arm. A test that leans on asymptotics
there can be anticonservative, so this script re-examines every primary
contrast without the model.

DESIGN.md fixed this companion at freeze: a matter-level cluster
bootstrap of 2,000 resamples over per-draft rates, paired by matter.
Matters are resampled with replacement, 48 at a time, which keeps the
clustering the GEE assumes and makes no distributional assumption. Each
draw gives every resampled matter equal weight: the statistic is the
mean, over the resampled matters, of the within-matter difference
between the condition draft's rate and the baseline draft's. A matter
whose draft has nothing adjudicable in either cell leaves the contrast
rather than shifting one arm's mean against the other's. We
report the percentile interval and the share of draws in which the
difference keeps the sign of the observed effect, which is the bootstrap
analogue of a one-sided test and needs no correction for a small cluster
count. A surviving contrast whose sign holds in nearly every draw is not
an artefact of the sandwich estimator; one whose sign wanders is. The
citation-weighted risk difference, which the GEE is closer to, is
reported beside it as pooled_risk_diff.

Writes results/cluster_bootstrap.json.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
R = HERE / "results"

CONDS = ["quota", "temporal", "stakes", "combo"]
N_DRAWS = 2000  # the number DESIGN.md fixed at freeze
SEED = 20260913


def outcome(df, kind):
    """The adjudicable rows and their success indicator for one outcome."""
    if kind == "citation":
        sub = df[(df.kind == "citation") & df.verdict.isin(["exists", "not_found"])]
        return sub, (sub.verdict == "exists").astype(int).values
    sub = df[(df.kind == "quote") & df.verdict.isin(["accurate", "near_miss", "inaccurate"])]
    return sub, (sub.verdict == "accurate").astype(int).values


def main():
    df = pd.DataFrame(json.loads(l) for l in open(R / "records.jsonl"))
    primary = json.loads((R / "stats_gee.json").read_text())
    rng = np.random.default_rng(SEED)
    matters = np.array(sorted(df.matter.unique()))
    # one index of draws, reused across every model and outcome, so the
    # contrasts are bootstrapped against a common set of resampled matters
    draws = rng.integers(0, len(matters), size=(N_DRAWS, len(matters)))
    out = {"n_draws": N_DRAWS, "n_matters": int(len(matters)), "seed": SEED, "contrasts": {}}
    for kind, label in (("citation", "citation"), ("quote", "quote")):
        for model in sorted(df.model.unique()):
            sub, y = outcome(df[df.model == model], kind)
            if not len(sub):
                continue
            cond = sub.condition.values
            mi = pd.Categorical(sub.matter, categories=list(matters)).codes
            # per matter and cell, successes and adjudicable count, so a
            # draw is a sum over resampled matters rather than a refilter
            def cell(c):
                m = cond == c
                s = np.bincount(mi[m], weights=y[m], minlength=len(matters))
                n = np.bincount(mi[m], minlength=len(matters))
                return s, n
            b_s, b_n = cell("baseline")
            for c in CONDS:
                c_s, c_n = cell(c)
                key = f"{label}:{model}:{c}"
                if primary.get(key) is None:
                    continue
                # per-draft rates, one per matter, equal weight; a matter
                # whose draft has nothing adjudicable in a cell is absent
                # from that cell's mean rather than counted as zero
                with np.errstate(invalid="ignore", divide="ignore"):
                    b_r = np.where(b_n > 0, b_s / np.maximum(b_n, 1), np.nan)
                    c_r = np.where(c_n > 0, c_s / np.maximum(c_n, 1), np.nan)
                # paired, as DESIGN.md requires: the statistic is the mean
                # over matters of the within-matter difference, so a matter
                # missing from either cell leaves the contrast entirely
                # rather than shifting one arm's mean against the other's
                d_r = c_r - b_r
                obs = float(np.nanmean(d_r))
                pooled = (c_s.sum() / c_n.sum() if c_n.sum() else np.nan) - (
                    b_s.sum() / b_n.sum() if b_n.sum() else np.nan)
                with np.errstate(invalid="ignore"):
                    d = np.nanmean(d_r[draws], axis=1)
                d = d[~np.isnan(d)]
                # the citation-weighted difference over the same draws,
                # which is nearer what the GEE estimates
                bs, bn = b_s[draws].sum(1), b_n[draws].sum(1)
                cs, cn = c_s[draws].sum(1), c_n[draws].sum(1)
                okp = (bn > 0) & (cn > 0)
                dp = cs[okp] / cn[okp] - bs[okp] / bn[okp]
                if not len(d):
                    continue
                # share of draws keeping the observed sign; for an
                # observed null this is uninformative and near 0.5
                sign = float((d < 0).mean() if obs < 0 else (d > 0).mean())
                out["contrasts"][key] = {
                    "rate_diff": round(float(obs), 4),
                    "pooled_risk_diff": round(float(pooled), 4),
                    "pooled_ci_low": round(float(np.percentile(dp, 2.5)), 4) if len(dp) else None,
                    "pooled_ci_high": round(float(np.percentile(dp, 97.5)), 4) if len(dp) else None,
                    "ci_low": round(float(np.percentile(d, 2.5)), 4),
                    "ci_high": round(float(np.percentile(d, 97.5)), 4),
                    "sign_share": round(sign, 4),
                    "excludes_zero": bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0),
                    "primary_OR": primary[key]["OR"],
                    "primary_holm_p": primary[key]["holm_p"],
                    "n_baseline": int(b_n.sum()), "n_cond": int(c_n.sum())}
    surv = {k: v for k, v in out["contrasts"].items() if v["primary_holm_p"] < 0.05}
    out["summary"] = {
        "primary_survivors": len(surv),
        "survivors_excluding_zero": sum(1 for v in surv.values() if v["excludes_zero"]),
        "survivors_sign_min": round(min(v["sign_share"] for v in surv.values()), 4) if surv else None,
        "nonsurvivors_excluding_zero": sum(
            1 for k, v in out["contrasts"].items() if v["primary_holm_p"] >= 0.05 and v["excludes_zero"]),
    }
    (R / "cluster_bootstrap.json").write_text(json.dumps(out, indent=1))
    print("primary survivors:", out["summary"]["primary_survivors"],
          "| bootstrap CI excludes zero:", out["summary"]["survivors_excluding_zero"],
          "| min sign share:", out["summary"]["survivors_sign_min"])
    for k, v in sorted(surv.items()):
        print(f"  {k:28s} rd={v['rate_diff']:+.3f} CI[{v['ci_low']:+.3f},{v['ci_high']:+.3f}] "
              f"sign={v['sign_share']:.3f} n={v['n_cond']}")


if __name__ == "__main__":
    main()
