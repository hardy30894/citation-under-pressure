#!/usr/bin/env python3
"""Definitive re-score of loop-arm episodes on the local-first text chain.
For each episode, score the FINAL draft (last revision, or the round-0
combo draft if no revision was needed) and the round-0 draft, giving the
paper's H2 before/after table free of CL-quota noise."""

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
    p.name.replace("loop_", "")
    for p in sorted((Path(__file__).resolve().parents[1] / "results").glob("loop_*"))
    if (p / "run/events.jsonl").exists())


def score(text, checker, store):
    recs, rates = checker.check_text(text)
    qres = q2.check_draft(text, recs, eyecite_pass(text), store)
    return {
        "exist": rates["existence_rate"],
        "n_cites": rates["n_citations"],
        "strict": q2.strict_rate(qres),
        "n_quotes_scored": sum(
            1 for r in qres
            if r["verdict"] in ("accurate", "near_miss", "inaccurate")
        ),
        "acc": sum(1 for r in qres if r["verdict"] == "accurate"),
    }


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None,
                                            fetch_budget=0))
    out = {}
    for model in MODELS:
        loop_drafts = HERE / "results" / f"loop_{model}" / "drafts"
        full_drafts = HERE / "results" / f"full_{model}" / "drafts"
        eps = {}
        for l in open(HERE / "results" / f"loop_{model}" /
                      "run/events.jsonl"):
            try:
                d = json.loads(l)
                if d["type"] == "episode_done":
                    eps[d["step"]] = d["data"]
            except Exception:
                continue
        rows = []
        for ep in eps.values():
            matter, arm = ep["matter"], ep["arm"]
            revs = sorted(
                loop_drafts.glob(f"{matter}_{arm}_r*.txt"),
                key=lambda p: int(re.search(r"_r(\d+)", p.stem).group(1)),
            )
            r0 = full_drafts / f"{matter}_combo.txt"
            final = revs[-1] if revs else r0
            rows.append({
                "matter": matter, "arm": arm,
                "rounds": len(ep["rounds"]),
                "converged": ep["converged"],
                "r0": score(r0.read_text(), checker, store),
                "final": score(final.read_text(), checker, store),
            })
        out[model] = rows
        m = lambda xs: round(sum(x for x in xs if x is not None) /
                             max(1, len([x for x in xs if x is not None])), 3)
        for arm in ("true", "scrambled"):
            sub = [r for r in rows if r["arm"] == arm]
            print(f"{model:10s} {arm:9s} n={len(sub)} "
                  f"exist {m([r['r0']['exist'] for r in sub])}->"
                  f"{m([r['final']['exist'] for r in sub])} "
                  f"strict {m([r['r0']['strict'] for r in sub])}->"
                  f"{m([r['final']['strict'] for r in sub])}")
    (HERE / "results" / "rescore_loops.json").write_text(
        json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
