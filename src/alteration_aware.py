#!/usr/bin/env python3
"""The literal standard, as a comparison for the strict one.

The strict standard (quotecheck2.fragments) reads a bracketed alteration
as an omission and drops alteration parentheticals, so lawful quoting
passes. The literal matcher it replaced (checker.quote_checker.fragments)
read a bracketed alteration as its contents, so "[the defendant]" for
"he" failed. This script rescores the full run under the literal matcher
into records_alt.jsonl (format of records.jsonl) and compares the two
standards per model and condition; gee.py --records records_alt.jsonl
--out stats_gee_alt.json fits the contrasts on it. Writes
results/alteration_aware.json with keys "strict" (the paper's standard)
and "literal"."""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore, normalize, fragments as literal_fragments  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from records_dump import MODELS  # noqa: E402

fragments_alt = q2.fragments  # the paper's standard, for scripts that import it


def main():
    q2.fragments = literal_fragments
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    out = open(HERE / "results" / "records_alt.jsonl", "w")
    tally = {}
    for model in MODELS:
        for p in sorted((HERE / "results" / f"full_{model}" / "drafts").glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            text = p.read_text()
            recs, _ = checker.check_text(text)
            qres = q2.check_draft(text, recs, eyecite_pass(text), store)
            base = {"model": model, "matter": matter, "condition": cond}
            for r in recs:
                out.write(json.dumps({**base, "kind": "citation", "verdict": r["verdict"]}) + "\n")
            for r in qres:
                out.write(json.dumps({**base, "kind": "quote", "verdict": r["verdict"]}) + "\n")
                if r["verdict"] in ("accurate", "near_miss", "inaccurate"):
                    t = tally.setdefault(f"{model}:{cond}", {"scored": 0, "accurate": 0})
                    t["scored"] += 1
                    t["accurate"] += r["verdict"] == "accurate"
        print(model, "done", flush=True)
    out.close()
    # compare with the standard records
    std = {}
    for l in open(HERE / "results" / "records.jsonl"):
        r = json.loads(l)
        if r["kind"] == "quote" and r["verdict"] in ("accurate", "near_miss", "inaccurate"):
            t = std.setdefault(f"{r['model']}:{r['condition']}", {"scored": 0, "accurate": 0})
            t["scored"] += 1
            t["accurate"] += r["verdict"] == "accurate"
    cmp = {}
    for k, t in tally.items():
        s = std.get(k, {"scored": 0, "accurate": 0})
        cmp[k] = {"strict": round(s["accurate"] / s["scored"], 4) if s["scored"] else None,
                  "literal": round(t["accurate"] / t["scored"], 4) if t["scored"] else None,
                  "scored_strict": s["scored"], "scored_literal": t["scored"]}
    diffs = [abs(v["literal"] - v["strict"]) for v in cmp.values() if v["strict"] is not None and v["literal"] is not None]
    summary = {"cells": cmp, "max_cell_diff": round(max(diffs), 4) if diffs else None,
               "mean_cell_diff": round(sum(diffs) / len(diffs), 4) if diffs else None}
    (HERE / "results" / "alteration_aware.json").write_text(json.dumps(summary, indent=1))
    print("max cell difference", summary["max_cell_diff"], "mean", summary["mean_cell_diff"])


if __name__ == "__main__":
    main()
