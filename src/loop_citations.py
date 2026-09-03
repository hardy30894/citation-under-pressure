#!/usr/bin/env python3
"""Two accountings the loop tables leave implicit.

Citation existence in the loop: for every true-arm episode, each citation
that did not resolve at round 0 is followed to the final draft and counted
as removed (no longer cited) or kept (still cited, still not resolving),
and citations in the final draft that were not in the round-0 draft are
counted as new, resolving or not. A rise in the existence rate that comes
from removal alone is not repair; replacement shows as new resolving
citations.

Lenient quotation accuracy by arm: the loop's final strict rate under
every precision arm, recomputed with near misses counted as correct, so
that the precision curve can be read under the standard a deployer would
enforce. Also per arm, the number of final drafts left with no scored
quotation (they drop out of the rate), and for the true arm the split of
round-0 flags into inaccurate and near miss.

Reads results/rescore_loops.json for the episode list, scores the drafts
locally, and writes results/loop_citations.json. --prefix gloop reads the
grounded loop (results/gloop_<model>/) instead."""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402

ARMS = ("true", "threequarter", "half", "quarter", "scrambled", "none", "passage")


def cites(recs):
    return {r["citation"]: r["verdict"] for r in recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="loop")
    args = ap.parse_args()
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    loops = json.loads((HERE / "results" / (
        "rescore_loops.json" if args.prefix == "loop" else f"rescore_{args.prefix}.json")).read_text())
    out = {}
    for model, rows in loops.items():
        loop_drafts = HERE / "results" / f"{args.prefix}_{model}" / "drafts"
        src = "full" if args.prefix == "loop" else "rag"
        full_drafts = HERE / "results" / f"{src}_{model}" / "drafts"
        cnt = Counter()
        lenient = {a: [] for a in ARMS}
        strict = {a: [] for a in ARMS}
        empty = Counter()
        flags = Counter()
        for ep in rows:
            matter, arm = ep["matter"], ep["arm"]
            revs = sorted(loop_drafts.glob(f"{matter}_{arm}_r*.txt"),
                          key=lambda p: int(re.search(r"_r(\d+)", p.stem).group(1)))
            r0 = (full_drafts / f"{matter}_combo.txt").read_text()
            final = revs[-1].read_text() if revs else r0
            recs1, _ = checker.check_text(final)
            q1 = q2.check_draft(final, recs1, eyecite_pass(final), store)
            scored = [r for r in q1 if r["verdict"] in ("accurate", "near_miss", "inaccurate")]
            if scored and arm in lenient:
                lenient[arm].append(sum(r["verdict"] in ("accurate", "near_miss") for r in scored) / len(scored))
                strict[arm].append(sum(r["verdict"] == "accurate" for r in scored) / len(scored))
            elif arm in lenient:
                empty[arm] += 1
            if arm != "true":
                continue
            recs0, _ = checker.check_text(r0)
            for r in q2.check_draft(r0, recs0, eyecite_pass(r0), store):
                if r["verdict"] in ("inaccurate", "near_miss"):
                    flags[r["verdict"]] += 1
            c0, c1 = cites(recs0), cites(recs1)
            for c, v in c0.items():
                if v != "not_found":
                    continue
                cnt["nf_r0"] += 1
                cnt["nf_removed" if c not in c1 else "nf_kept"] += 1
            for c, v in c1.items():
                if c not in c0:
                    cnt["new"] += 1
                    cnt["new_exists" if v == "exists" else "new_other"] += 1
        m = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
        out[model] = {"existence_trace": dict(cnt),
                      "empty_final_drafts": dict(empty), "r0_flags": dict(flags),
                      "final_lenient": {a: m(v) for a, v in lenient.items() if v},
                      "final_strict": {a: m(v) for a, v in strict.items() if v}}
        print(model, dict(cnt), "lenient", out[model]["final_lenient"])
    (HERE / "results" / (
        "loop_citations.json" if args.prefix == "loop" else f"{args.prefix}_citations.json")
     ).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
