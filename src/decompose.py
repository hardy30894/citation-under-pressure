#!/usr/bin/env python3
"""Decompose the not-in-corpus inaccurate-quote bucket for the frontier
tiers: out-of-scope (cited authority isn't a U.S. Reports case, so the
SCOTUS corpus can't contain it), paraphrase-in-quotes (substantial token
overlap with the cited case's own text), or fabricated language."""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore, normalize, \
    fragments, token_coverage  # noqa: E402
from local_text import ChainTextStore, _norm_rep  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402

MODELS = ("gpt54mini", "sonnet")


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None,
                                            fetch_budget=0))
    out = {}
    for model in MODELS:
        tally = {"out_of_scope_non_us": 0, "paraphrase_in_quotes": 0,
                 "fabricated_language": 0, "no_text": 0}
        for p in sorted((HERE / "results" / f"full_{model}" /
                         "drafts").glob("*.txt")):
            text = p.read_text()
            recs, _ = checker.check_text(text)
            qres = q2.check_draft(text, recs, eyecite_pass(text), store)
            by_cite = {r["citation"]: r for r in recs}
            for r in qres:
                if r["verdict"] != "inaccurate" or not r["citation"]:
                    continue
                rec = by_cite.get(r["citation"], {})
                if _norm_rep(rec.get("reporter")) != "US":
                    tally["out_of_scope_non_us"] += 1
                    continue
                op = store.get(rec.get("cluster_id"),
                               volume=rec.get("volume"),
                               reporter=rec.get("reporter"),
                               page=rec.get("page"))
                if not op:
                    tally["no_text"] += 1
                    continue
                frags = fragments(r["quote"]) or [normalize(r["quote"])]
                cov = max(token_coverage(f, normalize(op)) for f in frags)
                if cov >= 0.5:
                    tally["paraphrase_in_quotes"] += 1
                else:
                    tally["fabricated_language"] += 1
        out[model] = tally
        print(model, tally, flush=True)
    (HERE / "results/notincorpus_decomposition.json").write_text(
        json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
