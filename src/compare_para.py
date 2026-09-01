#!/usr/bin/env python3
"""Paraphrase-robustness comparison: same 12 matters, same conditions,
alternative phrasings — do the H1 effects hold across surface form?
Scores para_* drafts on the local-first chain and prints them beside the
original-phrasing scores restricted to the same matters."""

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
from pilot import DB, pick_matters  # noqa: E402
import quotecheck2 as q2  # noqa: E402

MODELS = ("qwen30b", "deepseek", "gpt54mini", "sonnet")
PARA_MATTERS = {e["id"] for e in pick_matters(48)[:12]}


def score_dir(drafts_dir, checker, store, keep_matters):
    agg = {}
    for p in sorted(drafts_dir.glob("*.txt")):
        matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
        if matter not in keep_matters:
            continue
        text = p.read_text()
        recs, rates = checker.check_text(text)
        qres = q2.check_draft(text, recs, eyecite_pass(text), store)
        a = agg.setdefault(cond, {"ex": 0, "nf": 0, "acc": 0, "bad": 0})
        for r in recs:
            if r["verdict"] == "exists":
                a["ex"] += 1
            elif r["verdict"] == "not_found":
                a["nf"] += 1
        for r in qres:
            if r["verdict"] == "accurate":
                a["acc"] += 1
            elif r["verdict"] in ("near_miss", "inaccurate"):
                a["bad"] += 1
    for c, a in agg.items():
        a["exist"] = round(a["ex"] / (a["ex"] + a["nf"]), 3) \
            if a["ex"] + a["nf"] else None
        a["strict"] = round(a["acc"] / (a["acc"] + a["bad"]), 3) \
            if a["acc"] + a["bad"] else None
    return agg


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None,
                                            fetch_budget=0))
    out = {}
    for model in MODELS:
        para_dir = HERE / "results" / f"para_{model}" / "drafts"
        if not para_dir.exists() or not any(para_dir.glob("*.txt")):
            print(f"{model}: no para drafts yet, skipping")
            continue
        orig = score_dir(HERE / "results" / f"full_{model}" / "drafts",
                         checker, store, PARA_MATTERS)
        para = score_dir(para_dir, checker, store, PARA_MATTERS)
        out[model] = {"original": orig, "paraphrase": para}
        for c in ("baseline", "quota", "temporal", "stakes", "combo"):
            o, p = orig.get(c, {}), para.get(c, {})
            print(f"{model:10s} {c:9s} exist {o.get('exist')}→"
                  f"{p.get('exist')}  strict {o.get('strict')}→"
                  f"{p.get('strict')}")
    (HERE / "results" / "paraphrase_comparison.json").write_text(
        json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
