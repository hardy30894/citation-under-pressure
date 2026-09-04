#!/usr/bin/env python3
"""What the human reference's strict failures are.

Rescores the clean brief excerpts of the human reference
(src/human_baseline.py) under the literal matcher (the comparison to the
paper's alteration-aware strict standard), and sorts every strict failure by its visible
cause: a bracketed alteration or ellipsis inside the quotation marks, a
near miss without either (the signature of a corrupted character, OCR
or otherwise), or an inaccurate quotation without either. Writes
results/human_alt.json."""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

import human_baseline as hb  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from checker.quote_checker import fragments as literal_fragments  # noqa: E402
from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa: E402
from local_text import ChainTextStore  # noqa: E402

ALTERED = re.compile(r"\[[^\]]*\]|\.\s?\.\s?\.|…")


def score(rows, checker, store):
    verdicts = {}
    quotes = []
    for row in rows:
        try:
            recs, _ = checker.check_text(row["text"])
            res = q2.check_draft(row["text"], recs, eyecite_pass(row["text"]), store)
        except Exception:
            continue
        for r in res:
            verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
            quotes.append((r["quote"], r["verdict"]))
    scored = sum(verdicts.get(v, 0) for v in ("accurate", "near_miss", "inaccurate"))
    return {"verdicts": verdicts, "scored": scored,
            "strict": round(verdicts.get("accurate", 0) / scored, 4) if scored else None,
            "lenient": round((verdicts.get("accurate", 0) + verdicts.get("near_miss", 0)) / scored, 4) if scored else None}, quotes


def main():
    rows = hb.load_clean_excerpts()
    checker = CitationChecker(SqliteIndex(hb.DB))
    store = ChainTextStore(OpinionTextStore(hb.DB, cl_token=None, fetch_budget=0))
    standard, quotes = score(rows, checker, store)
    causes = {"altered_near_miss": 0, "altered_inaccurate": 0,
              "unaltered_near_miss": 0, "unaltered_inaccurate": 0}
    for q, v in quotes:
        if v not in ("near_miss", "inaccurate"):
            continue
        causes[("altered_" if ALTERED.search(q) else "unaltered_") + v] += 1
    q2.fragments = literal_fragments
    alt, _ = score(rows, checker, store)
    out = {"standard": standard, "literal": alt, "failure_causes": causes}
    (HERE / "results" / "human_alt.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
