#!/usr/bin/env python3
"""Per-quotation transition matrix for the loop arms.

For every scored quotation in a round-0 draft, find what became of it in
the final draft of the same episode:

  kept      the same quotation is still there, in quotation marks
            (its final verdict may differ if the citation changed)
  edited    a quotation on the same citation with at least half its
            tokens in common is there; reported with its final verdict
  dequoted  the words survive in the final text but no longer inside
            quotation marks
  deleted   none of the above

Also counts quotations that appear only in the final draft (added).
Rows are split by the round-0 verdict (accurate vs flagged, where
flagged means inaccurate or near miss), because true feedback names only
the flagged ones. Writes results/loop_transitions.json."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore, normalize  # noqa
from local_text import ChainTextStore  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402

SCORED = ("accurate", "near_miss", "inaccurate")


def scored_quotes(text, checker, store):
    recs, _ = checker.check_text(text)
    res = q2.check_draft(text, recs, eyecite_pass(text), store)
    return [r for r in res if r["verdict"] in SCORED]


def toks(s):
    return set(re.findall(r"[a-z0-9]+", normalize(s)))


def window(s, n=8):
    w = normalize(s).split()
    if len(w) <= n:
        return " ".join(w)
    mid = len(w) // 2
    return " ".join(w[mid - n // 2: mid - n // 2 + n])


def classify(q0, finals, final_norm, used):
    """Each final quotation may be claimed by one round-0 quotation only,
    so that kept + corrected + added equals the final accurate count."""
    n0 = normalize(q0["quote"])
    for i, q1 in enumerate(finals):
        if i not in used and normalize(q1["quote"]) == n0:
            used.add(i)
            return "kept", q1["verdict"]
    t0 = toks(q0["quote"])
    for i, q1 in enumerate(finals):
        if i not in used and q1["citation"] == q0["citation"] and t0:
            j = len(t0 & toks(q1["quote"])) / len(t0 | toks(q1["quote"]))
            if j >= 0.5:
                used.add(i)
                return "edited", q1["verdict"]
    if len(n0.split()) >= 5 and window(q0["quote"]) in final_norm:
        return "dequoted", None
    return "deleted", None


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="loop", help="loop or gloop (grounded)")
    args = ap.parse_args()
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    src = "rescore_loops.json" if args.prefix == "loop" else f"rescore_{args.prefix}.json"
    loops = json.loads((HERE / "results" / src).read_text())
    out = {}
    for model, rows in loops.items():
        loop_drafts = HERE / "results" / f"{args.prefix}_{model}" / "drafts"
        full_drafts = HERE / "results" / f"{'full' if args.prefix == 'loop' else 'rag'}_{model}" / "drafts"
        cnt = Counter()
        for ep in rows:
            matter, arm = ep["matter"], ep["arm"]
            revs = sorted(loop_drafts.glob(f"{matter}_{arm}_r*.txt"),
                          key=lambda p: int(re.search(r"_r(\d+)", p.stem).group(1)))
            r0 = (full_drafts / f"{matter}_combo.txt").read_text()
            final = revs[-1].read_text() if revs else r0
            q0s = scored_quotes(r0, checker, store)
            q1s = scored_quotes(final, checker, store) if revs else q0s
            final_norm = normalize(final)
            used = set()
            for q in q0s:
                fate, v1 = classify(q, q1s, final_norm, used)
                v0 = "accurate" if q["verdict"] == "accurate" else "flagged"
                key = f"{arm}:{v0}:{fate}"
                if v1 is not None:
                    key += f":{'accurate' if v1 == 'accurate' else 'flagged'}"
                cnt[key] += 1
            if revs:
                for i, q in enumerate(q1s):
                    if i not in used:
                        cnt[f"{arm}:added:{'accurate' if q['verdict'] == 'accurate' else 'flagged'}"] += 1
        out[model] = dict(sorted(cnt.items()))
        print(model, {k: v for k, v in out[model].items() if k.startswith("true:flagged")})
    (HERE / "results" / ("loop_transitions.json" if args.prefix == "loop"
                         else f"{args.prefix}_transitions.json")).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
