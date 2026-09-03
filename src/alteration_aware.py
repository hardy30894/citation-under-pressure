#!/usr/bin/env python3
"""The strict standard with quotation alterations read as omissions.

The matcher already ignores case and punctuation, splits a quotation on
ellipses, and reads a bracketed alteration as its contents, so "[t]he
court" matches "the court". What it does not forgive is a bracketed
substitution whose words are not in the opinion ("[the defendant]" for
"he"). This script rescores the full run with a matcher that treats every
bracketed segment as an omission, splitting the quotation there the way
it splits on an ellipsis, and drops an alteration parenthetical
("emphasis added", "citation omitted", "internal quotation marks
omitted", "cleaned up") wherever one sits inside the quotation marks. The
result is records_alt.jsonl in the format of records.jsonl, and a
comparison of the two standards per model and condition. gee.py
--records records_alt.jsonl --out stats_gee_alt.json then fits the
contrasts on it. Writes results/alteration_aware.json."""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore, normalize  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from records_dump import MODELS  # noqa: E402

PAREN = re.compile(r"\((?:emphasis (?:added|in original|omitted)|citations? omitted|"
                   r"internal quotation marks (?:and citations? )?omitted|cleaned up|"
                   r"footnote omitted|alterations? (?:in original|omitted))\)", re.I)


def fragments_alt(quote):
    """Split on ellipses and on bracketed segments; keep fragments of at
    least 15 normalized characters, as the original does."""
    quote = PAREN.sub(" ", quote)
    parts = re.split(r"\.\s?\.\s?\.|…|\[[^\]]*\]", quote)
    return [normalize(p) for p in parts if len(normalize(p)) >= 15]


def main():
    q2.fragments = fragments_alt
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
                  "alteration_aware": round(t["accurate"] / t["scored"], 4) if t["scored"] else None,
                  "scored_strict": s["scored"], "scored_alt": t["scored"]}
    diffs = [abs(v["alteration_aware"] - v["strict"]) for v in cmp.values() if v["strict"] is not None and v["alteration_aware"] is not None]
    summary = {"cells": cmp, "max_cell_diff": round(max(diffs), 4) if diffs else None,
               "mean_cell_diff": round(sum(diffs) / len(diffs), 4) if diffs else None}
    (HERE / "results" / "alteration_aware.json").write_text(json.dumps(summary, indent=1))
    print("max cell difference", summary["max_cell_diff"], "mean", summary["mean_cell_diff"])


if __name__ == "__main__":
    main()
