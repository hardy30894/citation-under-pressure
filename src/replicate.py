#!/usr/bin/env python3
"""Run-to-run variance check. The full run generated every cell once at
temperature 0. results/rep2_<model>/ holds a second, independent
generation of the baseline and combined drafts for the first twelve
matters (fresh cache, same prompts). This script scores both runs with
the same instrument and reports, per model, the existence rate and strict
quotation rate in each run and the size of the baseline-to-combined
contrast in each, so that the paper can say how much a single run moves.
Writes results/replicate.json."""

import json
import re
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


def score(text, checker, store):
    recs, rates = checker.check_text(text)
    qres = q2.check_draft(text, recs, eyecite_pass(text), store)
    scored = [r for r in qres if r["verdict"] in ("accurate", "near_miss", "inaccurate")]
    return {
        "ex": sum(r["verdict"] == "exists" for r in recs),
        "nf": sum(r["verdict"] == "not_found" for r in recs),
        "acc": sum(r["verdict"] == "accurate" for r in scored),
        "scored": len(scored),
    }


def exist_rate(rows):
    ex = sum(r["ex"] for r in rows)
    den = sum(r["ex"] + r["nf"] for r in rows)
    return round(ex / den, 3) if den else None


def pooled(rows, key_num, key_den):
    num = sum(r[key_num] for r in rows)
    den = sum(r[key_den] for r in rows)
    return round(num / den, 3) if den else None


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    out = {}
    for rep in sorted(p for p in R.glob("rep2_*") if p.is_dir()):
        model = rep.name.replace("rep2_", "")
        full = R / f"full_{model}" / "drafts"
        res = {}
        identical = 0
        n = 0
        for cond in ("baseline", "combo"):
            rows = {"run1": [], "run2": []}
            for p in sorted((rep / "drafts").glob(f"*_{cond}.txt")):
                q = full / p.name
                if not q.exists():
                    continue
                t2, t1 = p.read_text(), q.read_text()
                n += 1
                identical += t1.strip() == t2.strip()
                rows["run1"].append(score(t1, checker, store))
                rows["run2"].append(score(t2, checker, store))
            res[cond] = {
                run: {"exist": exist_rate(rows[run]),
                      "strict": pooled(rows[run], "acc", "scored"),
                      "n_drafts": len(rows[run])}
                for run in ("run1", "run2")
            }
        for run in ("run1", "run2"):
            b, c = res["baseline"][run], res["combo"][run]
            res[f"{run}_contrast"] = {
                "exist": round(c["exist"] - b["exist"], 3) if None not in (b["exist"], c["exist"]) else None,
                "strict": round(c["strict"] - b["strict"], 3) if None not in (b["strict"], c["strict"]) else None,
            }
        res["identical_drafts"] = f"{identical}/{n}"
        out[model] = res
        print(model, json.dumps(res))
    (R / "replicate.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
