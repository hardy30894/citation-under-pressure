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
    # --tag para dumps the alternative-phrasing drafts to records_para.jsonl
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "full"
    suffix = "" if tag == "full" else f"_{tag}"
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None,
                                            fetch_budget=0))
    out = open(HERE / "results" / f"records{suffix}.jsonl", "w")
    # the appellate set was extended after a first build; only matters in
    # the current manifest count
    keep = None
    if tag == "app":
        keep = {m["id"] for m in json.loads(
            (HERE / "results" / "appellate" / "manifest.json").read_text())}
    n = 0
    for model in MODELS:
        for p in sorted((HERE / "results" / f"{tag}_{model}" /
                         "drafts").glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            if keep is not None and matter not in keep:
                continue
            text = p.read_text()
            recs, _ = checker.check_text(text)
            qres = q2.check_draft(text, recs, eyecite_pass(text), store)
            base = {"model": model, "matter": matter, "condition": cond}
            for r in recs:
                out.write(json.dumps({**base, "kind": "citation",
                                      "verdict": r["verdict"],
                                      "citation": r.get("citation"),
                                      "reporter": r.get("reporter")}) + "\n")
                n += 1
            for r in qres:
                out.write(json.dumps({**base, "kind": "quote",
                                      "verdict": r["verdict"]}) + "\n")
                n += 1
        print(model, "done", flush=True)
    out.close()
    print(f"{n} records -> results/records{suffix}.jsonl")


if __name__ == "__main__":
    main()
