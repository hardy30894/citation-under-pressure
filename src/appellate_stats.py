#!/usr/bin/env python3
"""Second task, federal courts of appeals (results/app_<model>/, 48
matters, five conditions). Per model and condition: citation existence,
strict quotation accuracy, refusals, and the share of citations to the
U.S. Reports against the federal reporters. The same citation-level
logistic GEE as gee.py per model (four contrasts against baseline, two
outcomes, Holm within model over eight tests), and the same fit pooled
over both tasks with a task effect. Reads records_app.jsonl (from
records_dump.py --tag app) and records.jsonl. Writes
results/appellate_stats.json."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
R = HERE / "results"
from pilot import cite_details  # noqa: E402
from gee import fit as gee_fit, CONDS as GEE_CONDS  # noqa: E402


def full_gee(df, template=False):
    """gee.py's fit per model and outcome, Holm within model."""
    out = {}
    for model in sorted(df.model.unique()):
        tests = []
        for kind in ("citation", "quote"):
            try:
                res = gee_fit(df, model, kind, template=template)
            except Exception as e:
                for c in GEE_CONDS:
                    out[f"{kind}:{model}:{c}"] = {"OR": None, "p": None, "note": str(e)[:80]}
                continue
            for c, v in res.items():
                out[f"{kind}:{model}:{c}"] = v
                tests.append((f"{kind}:{model}:{c}", v["p"]))
        tests.sort(key=lambda t: t[1])
        m = len(tests)
        for i, (k, p) in enumerate(tests):
            out[k]["holm_p"] = round(min(1.0, p * (m - i)), 4)
    return out


def rates(df):
    out = {}
    for (m, c), g in df.groupby(["model", "condition"]):
        cit = g[g.kind == "citation"]
        ex = int((cit.verdict == "exists").sum())
        nf = int((cit.verdict == "not_found").sum())
        q = g[(g.kind == "quote") & g.verdict.isin(["accurate", "near_miss", "inaccurate"])]
        out[f"{m}:{c}"] = {"exist": round(ex / (ex + nf), 4) if ex + nf else None,
                           "not_found": nf, "adjudicable": ex + nf,
                           "strict": round(float((q.verdict == "accurate").mean()), 4) if len(q) else None,
                           "quotes_scored": int(len(q))}
    return out


def combo_gee(df, extra=""):
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
            key = f"{kind}:{model}:combo"
            if sub.y.nunique() < 2:
                out[key] = {"OR": None, "p": None}
                continue
            try:
                res = smf.gee("y ~ combo" + extra, groups="matter", data=sub,
                              family=sm.families.Binomial(),
                              cov_struct=sm.cov_struct.Exchangeable()).fit()
                b, se = res.params["combo"], res.bse["combo"]
                out[key] = {"OR": round(float(np.exp(b)), 3),
                            "ci_low": round(float(np.exp(b - 1.96 * se)), 3),
                            "ci_high": round(float(np.exp(b + 1.96 * se)), 3),
                            "p": float(res.pvalues["combo"]), "n": int(len(sub))}
            except Exception as e:
                out[key] = {"OR": None, "p": None, "note": str(e)[:80]}
    tests = sorted([(k, v) for k, v in out.items() if v["p"] is not None], key=lambda kv: kv[1]["p"])
    m = len(tests)
    for i, (k, v) in enumerate(tests):
        v["holm_p"] = round(min(1.0, v["p"] * (m - i)), 4)
        v["p"] = round(v["p"], 5)
    return out


FEDERAL = ("F2d", "F3d", "FSupp", "FSupp2d", "FSupp3d", "F")


def reporter_mix():
    """Share of citations to U.S. Reports and to F.2d/F.3d/F. Supp. in the
    appellate drafts, the not-found rate by reporter group from the
    checker, and refusals (drafts under 100 words)."""
    from checker.citation_checker import CitationChecker, SqliteIndex
    from pilot import DB
    checker = CitationChecker(SqliteIndex(DB))
    keep = {m["id"] for m in json.loads((R / "appellate" / "manifest.json").read_text())}
    out = {}
    pooled = Counter()
    for d in sorted(R.glob("app_*")):
        if not d.is_dir():
            continue
        model = d.name.replace("app_", "")
        c = Counter()
        base = Counter()
        refusals = 0
        n = 0
        for p in (d / "drafts").glob("*.txt"):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            if matter not in keep:
                continue
            t = p.read_text()
            n += 1
            if len(t.split()) < 100:
                refusals += 1
            recs, _ = checker.check_text(t)
            for r in recs:
                rep = (r.get("reporter") or "").replace(" ", "").replace(".", "")
                grp = "us" if rep == "US" else ("federal" if rep in FEDERAL else "other")
                c[grp] += 1
                if cond == "baseline":
                    base[grp] += 1
                if r["verdict"] == "not_found":
                    c[grp + "_nf"] += 1
        pooled.update(c)
        tot = c["us"] + c["federal"] + c["other"]
        btot = base["us"] + base["federal"] + base["other"]
        out[model] = {"drafts": n, "short_drafts": refusals, "citations": tot,
                      "us_share": round(c["us"] / tot, 3) if tot else None,
                      "us_share_baseline": round(base["us"] / btot, 3) if btot else None,
                      "federal_share": round(c["federal"] / tot, 3) if tot else None,
                      "us_not_found": c["us_nf"], "federal_not_found": c["federal_nf"],
                      "other_not_found": c["other_nf"]}
    out["_pooled"] = {k: pooled[k] for k in ("us", "federal", "other", "us_nf", "federal_nf", "other_nf")}
    return out


def sonnet_median_year():
    """Median decision year of Sonnet 5's resolved citations by condition,
    the check on the memorization alternative: the stakes clause should
    leave it where baseline puts it, the temporal clause should not."""
    from checker.citation_checker import SqliteIndex
    from pilot import DB
    import statistics
    idx = SqliteIndex(DB)
    keep = {m["id"] for m in json.loads((R / "appellate" / "manifest.json").read_text())}
    years = {}
    for p in (R / "app_sonnet" / "drafts").glob("*.txt"):
        matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
        if matter not in keep:
            continue
        for d in cite_details(p.read_text()):
            if d["volume"] and d["reporter"] and d["page"]:
                h = idx.lookup(d["volume"], d["reporter"], d["page"])
                y = re.match(r"\d{4}", h["date_filed"] or "") if h else None
                if y:
                    years.setdefault(cond, []).append(int(y.group(0)))
    return {c: int(statistics.median(v)) for c, v in years.items()}


def main():
    app = pd.DataFrame(json.loads(l) for l in open(R / "records_app.jsonl"))
    app["task"] = "appellate"
    sc = pd.DataFrame(json.loads(l) for l in open(R / "records.jsonl"))
    sc["task"] = "scotus"
    both = pd.concat([sc, app], ignore_index=True)
    both["template"] = both["task"]  # reuse gee.py's template effect as the task effect
    app["template"] = "appellate"
    out = {"rates": rates(app), "gee": full_gee(app),
           "gee_pooled_tasks": full_gee(both, template=True),
           "reporter_mix": reporter_mix()}
    # baseline task comparison per model: existence and strict, scotus vs appellate
    scr = rates(sc)
    out["sonnet_median_year"] = sonnet_median_year()
    out["baseline_vs_scotus"] = {
        m: {"scotus_exist": scr[f"{m}:baseline"]["exist"], "app_exist": out["rates"][f"{m}:baseline"]["exist"],
            "scotus_strict": scr[f"{m}:baseline"]["strict"], "app_strict": out["rates"][f"{m}:baseline"]["strict"]}
        for m in sorted(app.model.unique()) if f"{m}:baseline" in scr}
    (R / "appellate_stats.json").write_text(json.dumps(out, indent=1))
    for k, v in sorted(out["rates"].items()):
        print(f"{k:24s} exist {v['exist']} ({v['not_found']}/{v['adjudicable']})  strict {v['strict']} ({v['quotes_scored']})")
    for k, v in out["gee"].items():
        if v.get("holm_p") is not None and v["holm_p"] < 0.05:
            print(f"  {k:28s} OR {v['OR']} holm {v['holm_p']} *")
    print("pooled-task survivors:", sorted(k for k, v in out["gee_pooled_tasks"].items() if v.get("holm_p") is not None and v["holm_p"] < 0.05))
    print("reporter mix:", {m: (v.get("us_share"), v.get("federal_share")) for m, v in out["reporter_mix"].items() if not m.startswith("_")})
    print("pooled not found by reporter:", out["reporter_mix"]["_pooled"])


if __name__ == "__main__":
    main()
