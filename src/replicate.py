#!/usr/bin/env python3
"""Run-to-run variance. The full run (results/full_<model>/) generated
every cell once at temperature 0; results/rep2_<model>/ and
results/rep3_<model>/ hold two further independent generations of the
baseline and combined drafts (fresh cache, same prompts). This script
scores all three runs with the same instrument and reports, per model
and condition, the pooled existence and strict quotation rates in each
run, their mean and spread across runs, the baseline-to-combined
contrast in each run, and how many drafts were byte-identical across
runs. Writes results/replicate.json."""

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402

R = HERE / "results"
RUNS = ("full", "rep2", "rep3")
CONDS = ("baseline", "combo")


def score(text, checker, store):
    recs, _ = checker.check_text(text)
    qres = q2.check_draft(text, recs, eyecite_pass(text), store)
    scored = [r for r in qres if r["verdict"] in ("accurate", "near_miss", "inaccurate")]
    return {"ex": sum(r["verdict"] == "exists" for r in recs),
            "nf": sum(r["verdict"] == "not_found" for r in recs),
            "acc": sum(r["verdict"] == "accurate" for r in scored),
            "scored": len(scored)}


def exist_rate(rows):
    d = sum(r["ex"] + r["nf"] for r in rows)
    return round(sum(r["ex"] for r in rows) / d, 3) if d else None


def strict_rate(rows):
    d = sum(r["scored"] for r in rows)
    return round(sum(r["acc"] for r in rows) / d, 3) if d else None


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    models = sorted(p.name.replace("rep3_", "") for p in R.glob("rep3_*") if p.is_dir())
    out = {}
    for model in models:
        res = {}
        texts = {}
        for run in RUNS:
            d = R / f"{run}_{model}" / "drafts"
            for cond in CONDS:
                for p in sorted(d.glob(f"*_{cond}.txt")):
                    texts.setdefault((cond, p.name), {})[run] = p.read_text()
        identical = 0
        n_triples = 0
        per = {run: {c: [] for c in CONDS} for run in RUNS}
        for (cond, name), by_run in texts.items():
            if len(by_run) < len(RUNS):
                continue
            n_triples += 1
            identical += len({by_run[r].strip() for r in RUNS}) < len(RUNS)
            for run in RUNS:
                per[run][cond].append(score(by_run[run], checker, store))
        for cond in CONDS:
            res[cond] = {}
            for run in RUNS:
                rows = per[run][cond]
                res[cond][run] = {"exist": exist_rate(rows), "strict": strict_rate(rows),
                                  "n_drafts": len(rows)}
            for key in ("exist", "strict"):
                vals = [res[cond][run][key] for run in RUNS if res[cond][run][key] is not None]
                res[cond][f"{key}_mean"] = round(statistics.mean(vals), 3) if vals else None
                res[cond][f"{key}_sd"] = round(statistics.stdev(vals), 3) if len(vals) > 1 else None
                res[cond][f"{key}_range"] = round(max(vals) - min(vals), 3) if vals else None
        for run in RUNS:
            b, c = res["baseline"][run], res["combo"][run]
            res[f"{run}_contrast"] = {
                k: round(c[k] - b[k], 3) if None not in (b[k], c[k]) else None
                for k in ("exist", "strict")}
        res["identical_any_pair"] = identical
        res["n_drafts_per_run"] = n_triples
        out[model] = res
        print(model, "exist sd", res["baseline"]["exist_sd"], res["combo"]["exist_sd"],
              "strict sd", res["baseline"]["strict_sd"], res["combo"]["strict_sd"],
              "strict contrasts", [res[f"{r}_contrast"]["strict"] for r in RUNS], flush=True)
    (R / "replicate.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
