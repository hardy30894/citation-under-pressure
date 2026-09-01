#!/usr/bin/env python3
"""Dump citation-level and quote-level records for the primary
mixed-effects analysis: one JSONL row per citation and per scored quote,
with model / matter / condition, from the definitive local-first scoring."""

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

MODELS = tuple(
    p.name.replace("full_", "")
    for p in sorted((Path(__file__).resolve().parents[1] / "results").glob("full_*"))
    if len(list((p / "drafts").glob("*.txt"))) >= 240
)


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None,
                                            fetch_budget=0))
    out = open(HERE / "results" / "records.jsonl", "w")
    n = 0
    for model in MODELS:
        for p in sorted((HERE / "results" / f"full_{model}" /
                         "drafts").glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            text = p.read_text()
            recs, _ = checker.check_text(text)
            qres = q2.check_draft(text, recs, eyecite_pass(text), store)
            base = {"model": model, "matter": matter, "condition": cond}
            for r in recs:
                out.write(json.dumps({**base, "kind": "citation",
                                      "verdict": r["verdict"]}) + "\n")
                n += 1
            for r in qres:
                out.write(json.dumps({**base, "kind": "quote",
                                      "verdict": r["verdict"]}) + "\n")
                n += 1
        print(model, "done", flush=True)
    out.close()
    print(f"{n} records -> results/records.jsonl")


if __name__ == "__main__":
    main()
