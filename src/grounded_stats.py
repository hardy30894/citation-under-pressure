#!/usr/bin/env python3
"""The grounded condition against closed-book drafting.

results/rag_<model>/ holds baseline and combined drafts written with ten
retrieved, verified U.S. Reports authorities in the prompt. This script
compares them with the closed-book drafts of the same matters
(results/full_<model>/): per model and condition, citation existence and
strict quotation accuracy in both settings; a citation-level logistic GEE
per model, clustered by matter, for the grounding effect within each
condition (Holm over the 28 tests: seven models, two conditions, two
outcomes); the share of citations that are retrieved authorities; and,
for every model, the decomposition of inaccurate quotations in the
grounded drafts (paraphrase of the cited case, nothing matching, out of
scope). Writes results/grounded_stats.json."""

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

from pilot import cite_details  # noqa: E402

CONDS = ("baseline", "combo")


def rates(df):
    out = {}
    for (m, c), g in df.groupby(["model", "condition"]):
        cit = g[g.kind == "citation"]
        ex = (cit.verdict == "exists").sum()
        nf = (cit.verdict == "not_found").sum()
        q = g[(g.kind == "quote") & g.verdict.isin(["accurate", "near_miss", "inaccurate"])]
        out[f"{m}:{c}"] = {
            "exist": round(ex / (ex + nf), 4) if ex + nf else None,
            "not_found": int(nf), "adjudicable": int(ex + nf),
            "strict": round((q.verdict == "accurate").mean(), 4) if len(q) else None,
            "quotes_scored": int(len(q)),
        }
    return out


def gee(df):
    out = {}
    for model in sorted(df.model.unique()):
        for cond in CONDS:
            for kind in ("citation", "quote"):
                sub = df[(df.model == model) & (df.condition == cond) & (df.kind == kind)].copy()
                if kind == "citation":
                    sub = sub[sub.verdict.isin(["exists", "not_found"])]
                    sub["y"] = (sub.verdict == "exists").astype(int)
                else:
                    sub = sub[sub.verdict.isin(["accurate", "near_miss", "inaccurate"])]
                    sub["y"] = (sub.verdict == "accurate").astype(int)
                sub["g"] = (sub.setting == "grounded").astype(int)
                if sub.y.nunique() < 2 or sub.g.nunique() < 2:
                    out[f"{kind}:{model}:{cond}"] = {"OR": None, "p": None, "note": "no variation"}
                    continue
                try:
                    res = smf.gee("y ~ g", groups="matter", data=sub,
                                  family=sm.families.Binomial(),
                                  cov_struct=sm.cov_struct.Exchangeable()).fit()
                    b, se = res.params["g"], res.bse["g"]
                    out[f"{kind}:{model}:{cond}"] = {
                        "OR": round(float(np.exp(b)), 3),
                        "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
                        "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
                        "p": float(res.pvalues["g"])}
                except Exception as e:  # separation or convergence
                    out[f"{kind}:{model}:{cond}"] = {"OR": None, "p": None, "note": str(e)[:80]}
    tests = sorted([(k, v) for k, v in out.items() if v["p"] is not None], key=lambda kv: kv[1]["p"])
    m = len(tests)
    for i, (k, v) in enumerate(tests):
        v["holm_p"] = round(min(1.0, v["p"] * (m - i)), 4)
        v["p"] = round(v["p"], 5)
    return out


def retrieved_share():
    """Share of adjudicable citations in grounded drafts that are among the
    ten retrieved authorities for that matter and condition."""
    share = {}
    for d in sorted(R.glob("rag_*")):
        model = d.name.replace("rag_", "")
        hit = tot = 0
        for p in (d / "drafts").glob("*.txt"):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            lists = json.loads((R / "retrieval" / f"{matter}.json").read_text())
            allowed = {it["citation"] for it in lists["pre1970" if cond in ("temporal", "combo") else "all"]}
            for c in cite_details(p.read_text()):
                if c["volume"] and c["reporter"] and c["page"]:
                    tot += 1
                    rep = c["reporter"].replace(" ", "").replace(".", "")
                    if rep == "US" and f"{c['volume']} U.S. {c['page']}" in allowed:
                        hit += 1
        share[model] = {"retrieved": hit, "citations": tot,
                        "share": round(hit / tot, 3) if tot else None}
    return share


def main():
    full = pd.DataFrame(json.loads(l) for l in open(R / "records.jsonl"))
    full = full[full.condition.isin(CONDS)].copy()
    full["setting"] = "closed"
    rag = pd.DataFrame(json.loads(l) for l in open(R / "records_rag.jsonl"))
    rag["setting"] = "grounded"
    df = pd.concat([full, rag], ignore_index=True)
    out = {"closed": rates(full), "grounded": rates(rag), "gee": gee(df),
           "retrieved_share": retrieved_share()}
    dec = R / "notincorpus_decomposition_rag.json"
    if dec.exists():
        out["decomposition_grounded"] = json.loads(dec.read_text())
    (R / "grounded_stats.json").write_text(json.dumps(out, indent=1))
    for k in sorted(out["grounded"]):
        c, g = out["closed"][k], out["grounded"][k]
        print(f"{k:24s} exist {c['exist']} -> {g['exist']}   strict {c['strict']} -> {g['strict']}")
    for k, v in out["gee"].items():
        if v.get("holm_p") is not None and v["holm_p"] < 0.05:
            print(f"  {k:28s} OR {v['OR']} holm {v['holm_p']}")
    print("retrieved share:", {m: v["share"] for m, v in out["retrieved_share"].items()})


if __name__ == "__main__":
    main()
