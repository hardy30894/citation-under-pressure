#!/usr/bin/env python3
"""Does the date clause damage quoting, or change what is quoted?

The temporal clause moves the median decision year of the cases a model
cites from the 1980s to the 1940s, so a fall in quotation accuracy under
it could be the clause degrading the model's quoting or the clause
moving the model onto a different, harder population of opinions. The
era check in era_check.py cannot separate them: it compares old against
new opinions inside the baseline cell, where the old cases are the ones
the model chose for itself.

This script stratifies instead. Every scored quotation in the baseline,
temporal, and combined cells is labelled with the decision year of the
case it is attributed to, and the condition contrast is refit inside
each stratum: quotations from opinions decided before 1970, and from
1970 on. A fall that holds inside the pre-1970 stratum is the clause
damaging quoting from the same population; a fall that appears only
across strata is composition. A second stratification asks whether the
cited case is one the model also cites in some baseline draft, the
authority it would have reached for anyway.

Writes results/records_era.jsonl (records.jsonl plus a year, era, and
in_baseline field for quotations that could be dated) and
results/era_strata.json with cell rates and the refits.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
R = HERE / "results"

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB, cite_details  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from records_dump import MODELS  # noqa: E402

CONDS = ("baseline", "temporal", "combo")


def year_map(text, index):
    """Decision year of every full citation in a draft, from the index."""
    out = {}
    for d in cite_details(text):
        if d["volume"] and d["reporter"] and d["page"]:
            h = index.lookup(d["volume"], d["reporter"], d["page"])
            y = re.match(r"\d{4}", (h or {}).get("date_filed") or "")
            if y:
                out[d["citation"]] = int(y.group(0))
    return out


def fit(df, model, era):
    """The quotation contrast inside one stratum, same GEE as gee.py."""
    sub = df[(df.model == model) & (df.era == era)].copy()
    sub = sub[sub.verdict.isin(["accurate", "near_miss", "inaccurate"])]
    if sub.empty or sub.condition.nunique() < 2:
        return {}
    sub["y"] = (sub.verdict == "accurate").astype(int)
    sub["condition"] = pd.Categorical(sub.condition, categories=list(CONDS))
    out = {}
    try:
        res = smf.gee("y ~ C(condition)", groups="matter", data=sub,
                      family=sm.families.Binomial(),
                      cov_struct=sm.cov_struct.Exchangeable()).fit()
    except Exception as exc:  # a stratum with too few events will not converge
        return {"error": str(exc)[:80]}
    for c in CONDS[1:]:
        term = f"C(condition)[T.{c}]"
        if term not in res.params:
            continue
        b, se = res.params[term], res.bse[term]
        out[c] = {"OR": round(float(np.exp(b)), 3),
                  "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
                  "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
                  "p": round(float(res.pvalues[term]), 5),
                  "n": int(len(sub))}
    return out


def main():
    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    rows = []
    baseline_cites = defaultdict(set)  # model -> citations it uses at baseline
    scored = []
    for model in MODELS:
        for cond in CONDS:
            for p in sorted((R / f"full_{model}" / "drafts").glob(f"*_{cond}.txt")):
                matter = p.stem[: -len(cond) - 1]
                text = p.read_text()
                recs, _ = checker.check_text(text)
                qres = q2.check_draft(text, recs, eyecite_pass(text), store)
                years = year_map(text, index)
                if cond == "baseline":
                    baseline_cites[model].update(years)
                for r in qres:
                    if r["verdict"] not in ("accurate", "near_miss", "inaccurate"):
                        continue
                    y = years.get(r["citation"])
                    scored.append({"model": model, "matter": matter, "condition": cond,
                                   "verdict": r["verdict"], "citation": r["citation"],
                                   "year": y})
        print(model, "done", flush=True)
    for r in scored:
        r["era"] = None if r["year"] is None else ("pre1970" if r["year"] < 1970 else "post1970")
        r["in_baseline"] = r["citation"] in baseline_cites[r["model"]]
    with open(R / "records_era.jsonl", "w") as f:
        for r in scored:
            f.write(json.dumps(r) + "\n")
    df = pd.DataFrame(scored)
    dated = df[df.era.notna()]
    out = {"dated": int(len(dated)), "scored": int(len(df)),
           "cells": {}, "fits": {}, "pooled_fits": {}, "in_baseline": {}}
    for (m, c, e), g in dated.groupby(["model", "condition", "era"]):
        out["cells"][f"{m}:{c}:{e}"] = {
            "scored": int(len(g)), "accurate": int((g.verdict == "accurate").sum()),
            "strict": round(float((g.verdict == "accurate").mean()), 3)}
    for e in ("pre1970", "post1970"):
        g = dated[dated.era == e]
        for c in CONDS:
            h = g[g.condition == c]
            if len(h):
                out["cells"][f"pooled:{c}:{e}"] = {
                    "scored": int(len(h)), "accurate": int((h.verdict == "accurate").sum()),
                    "strict": round(float((h.verdict == "accurate").mean()), 3)}
    for m in sorted(dated.model.unique()):
        for e in ("pre1970", "post1970"):
            r = fit(dated, m, e)
            for c, v in r.items():
                out["fits"][f"{m}:{c}:{e}"] = v
    # the paper's rule: Holm within model over this fit's own tests
    for m in sorted(dated.model.unique()):
        tests = sorted([k for k in out["fits"] if k.split(":")[0] == m and "p" in out["fits"][k]],
                       key=lambda k: out["fits"][k]["p"])
        for i, k in enumerate(tests):
            out["fits"][k]["holm_p"] = round(min(1.0, out["fits"][k]["p"] * (len(tests) - i)), 4)
    out["fits_surviving"] = sorted(k for k, v in out["fits"].items()
                                   if v.get("holm_p", 1) < 0.05 and v["OR"] < 1)
    # pooled over models, with a model fixed effect
    for e in ("pre1970", "post1970"):
        sub = dated[dated.era == e].copy()
        sub["y"] = (sub.verdict == "accurate").astype(int)
        sub["condition"] = pd.Categorical(sub.condition, categories=list(CONDS))
        res = smf.gee("y ~ C(condition) + C(model)", groups="matter", data=sub,
                      family=sm.families.Binomial(),
                      cov_struct=sm.cov_struct.Exchangeable()).fit()
        for c in CONDS[1:]:
            term = f"C(condition)[T.{c}]"
            b, se = res.params[term], res.bse[term]
            out["pooled_fits"][f"{c}:{e}"] = {
                "OR": round(float(np.exp(b)), 3),
                "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
                "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
                "p": round(float(res.pvalues[term]), 5), "n": int(len(sub))}
    # Holm over the four pooled tests, the same rule the paper states
    pt = sorted(out["pooled_fits"], key=lambda k: out["pooled_fits"][k]["p"])
    for i, k in enumerate(pt):
        out["pooled_fits"][k]["holm_p"] = round(min(1.0, out["pooled_fits"][k]["p"] * (len(pt) - i)), 4)
    # decision year inside each stratum, since a bucket is not a control
    for e in ("pre1970", "post1970"):
        g = dated[dated.era == e]
        out.setdefault("stratum_years", {})[e] = {
            c: {"median": float(g[g.condition == c].year.median()),
                "q1": float(g[g.condition == c].year.quantile(0.25)),
                "q3": float(g[g.condition == c].year.quantile(0.75))}
            for c in CONDS if len(g[g.condition == c])}
    # year as a continuous adjustment rather than a bucket
    d2 = dated.copy()
    d2["y"] = (d2.verdict == "accurate").astype(int)
    d2["condition"] = pd.Categorical(d2.condition, categories=list(CONDS))
    d2["yr"] = (d2.year - 1900) / 50.0
    res = smf.gee("y ~ C(condition) + yr + C(model)", groups="matter", data=d2,
                  family=sm.families.Binomial(),
                  cov_struct=sm.cov_struct.Exchangeable()).fit()
    # the same fit without the year term, so the adjustment can be read
    res0 = smf.gee("y ~ C(condition) + C(model)", groups="matter", data=d2,
                   family=sm.families.Binomial(),
                   cov_struct=sm.cov_struct.Exchangeable()).fit()
    out["year_unadjusted"] = {}
    for c in CONDS[1:]:
        term = f"C(condition)[T.{c}]"
        b, se = res0.params[term], res0.bse[term]
        out["year_unadjusted"][c] = {
            "OR": round(float(np.exp(b)), 3),
            "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
            "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
            "p": round(float(res0.pvalues[term]), 5), "n": int(len(d2))}
    out["year_adjusted"] = {}
    for c in CONDS[1:]:
        term = f"C(condition)[T.{c}]"
        b, se = res.params[term], res.bse[term]
        out["year_adjusted"][c] = {
            "OR": round(float(np.exp(b)), 3),
            "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
            "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
            "p": round(float(res.pvalues[term]), 5), "n": int(len(d2))}
    # the authority the model would have reached for anyway
    for c in CONDS:
        g = df[df.condition == c]
        ib = g[g.in_baseline]
        out["in_baseline"][c] = {
            "scored": int(len(g)), "share_in_baseline": round(float(g.in_baseline.mean()), 3),
            "strict_in_baseline": round(float((ib.verdict == "accurate").mean()), 3) if len(ib) else None,
            "strict_new": round(float((g[~g.in_baseline].verdict == "accurate").mean()), 3)}
    (R / "era_strata.json").write_text(json.dumps(out, indent=1))
    for e in ("pre1970", "post1970"):
        print(e, {c: out["cells"].get(f"pooled:{c}:{e}") for c in CONDS})
        print("   pooled fit", {c: out["pooled_fits"][f"{c}:{e}"] for c in CONDS[1:]})
    print("in_baseline", out["in_baseline"])


if __name__ == "__main__":
    main()
