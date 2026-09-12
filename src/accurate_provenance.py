#!/usr/bin/env python3
"""How much of the accurate bucket could attribution error be inflating?

The count outcome K_d is the number of quotations scored accurate in a
draft, so anything that inflates that bucket inflates the paper's
strongest result. The sensitivity in audit_sensitivity.py cannot see
this: it reclassifies inaccurate verdicts and leaves the accurate ones
alone, which is exactly why K_d is insulated there.

A quotation scores accurate when its language is verbatim in the case
the draft attributes it to, so the draft as filed is right whatever the
model privately meant. The way that verdict can still mislead is if the
language is not distinctive: stock phrases that appear in dozens of
opinions would resolve against the attributed case no matter which case
the model had in mind, and the attribution rule would get credit for
nothing.

This searches every accurate quotation against the same Caselaw Access
Project U.S. Reports corpus the inaccurate bucket is searched against,
and asks, of the ones the search can speak to, whether the language
leads back to the case the draft attributed it to.

Two kinds of quotation fall outside the check rather than into doubt. A
probe under six words is a short quotation, not a claim about any
particular case, and would match half the corpus whatever its source.
Language absent from the corpus is almost always a citation to a
reporter the U.S. Reports archive does not carry, which is a coverage
limit of this search and not a fault in the quotation. Neither is
evidence of anything, and neither is counted as if it were.

For the rest, one matching opinion means the language identifies its
source and a handful means the opinion is quoted by later cases, which
is ordinary; either way the question is whether the attributed case is
among them. This is a deterministic check on the instrument, not a
reading of what any model intended, and caption matching makes it
conservative: a case whose name the index renders differently from the
archive will not be recognised among its own sources.

Writes results/accurate_provenance.json.
"""

import json
import sys
from bisect import bisect_right
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
R = HERE / "results"

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa: E402
from checker.quote_checker import OpinionTextStore, normalize  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from quotecheck2 import fragments  # noqa: E402
from provenance import PILOTS, SEP, load_corpus_cap, cap_tokens  # noqa: E402

# a phrase in more than this many opinions is treated as boilerplate
GENERIC_AT = 6
CAP_COUNT = 25  # stop counting hits here; the exact number stops mattering


def count_sources(big, bounds, captions, frag_norm):
    """Distinct opinions holding this fragment, and whether the probe that
    matched is long enough to identify a source rather than a stock
    phrase. Mirrors provenance.find_case, but counts instead of stopping
    at three, since the question here is how common the language is."""
    probe = frag_norm
    if probe not in big:
        words = frag_norm.split()
        if len(words) >= 10:
            mid = len(words) // 2
            probe = " ".join(words[max(0, mid - 5): mid + 5])
        if probe not in big:
            return [], False, 0
    hits, start, n = [], 0, 0
    while n < CAP_COUNT:
        i = big.find(probe, start)
        if i < 0:
            break
        cap = captions[bisect_right(bounds, i) - 1]
        if cap not in hits:
            hits.append(cap)
        n += 1
        start = i + 1
    return hits, len(probe.split()) >= 6, n


def main():
    print("loading corpus (few minutes)...", flush=True)
    big, bounds, captions = load_corpus_cap()
    print(f"{len(captions)} documents indexed", flush=True)

    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))

    rows = []
    for model, drafts_dir in PILOTS.items():
        for p in sorted(drafts_dir.glob("*.txt")):
            text = p.read_text()
            recs, _ = checker.check_text(text)
            res = q2.check_draft(text, recs, eyecite_pass(text), store)
            full_quotes = {q["quote"][:120]: q for q in (
                {"quote": e["quote"], "start": e["start"]}
                for e in q2.extract_quotes(text))}
            for r in res:
                if r["verdict"] != "accurate":
                    continue
                fq = full_quotes.get(r["quote"], {"quote": r["quote"]})
                frags = fragments(fq["quote"]) or [normalize(fq["quote"])]
                frag = max(frags, key=len)
                hits, distinctive, n = count_sources(big, bounds, captions, frag)
                att_name = ""
                rec = next((x for x in recs if x["citation"] == r["citation"]), None)
                if rec and rec.get("cluster_id"):
                    hit = index.lookup(rec["volume"], rec["reporter"], rec["page"])
                    att_name = (hit or {}).get("case_name") or ""
                in_att = any(cap_tokens(h) & cap_tokens(att_name) for h in hits)
                rows.append({
                    "model": model, "draft": p.stem, "citation": r["citation"],
                    "attributed": att_name[:70], "sources": len(hits),
                    "occurrences": n, "distinctive": distinctive,
                    "attributed_among_sources": in_att,
                    "words": len(frag.split())})
        print(model, "done", len(rows), flush=True)

    # Two things put a quotation outside this check rather than in
    # doubt: a probe under six words, which is a short quotation and not
    # a claim about any case, and language absent from this corpus, which
    # is mostly a citation to a reporter the U.S. Reports archive does
    # not carry. The checkable set is the rest, and the question there is
    # whether the language leads back to the attributed case.
    checkable = [x for x in rows if x["distinctive"] and x["sources"] >= 1]
    hit = sum(1 for x in checkable if x["attributed_among_sources"])
    short = sum(1 for x in rows if not x["distinctive"])
    absent = sum(1 for x in rows if x["sources"] == 0)
    absent_nonus = sum(1 for x in rows if x["sources"] == 0 and "U.S." not in x["citation"])
    n = len(rows)
    spread = {}
    for x in checkable:
        k = "one" if x["sources"] == 1 else ("few" if x["sources"] <= GENERIC_AT else "many")
        spread[k] = spread.get(k, 0) + 1
    out = {
        "n_accurate": n, "generic_at": GENERIC_AT,
        "checkable": len(checkable),
        "traced_to_attributed": hit,
        "traced_pct": round(100 * hit / len(checkable), 1) if checkable else None,
        "not_traced": len(checkable) - hit,
        "short_probe": short,
        "absent_from_corpus": absent,
        "absent_and_non_us_reporter": absent_nonus,
        "spread_over_opinions": spread,
    }
    (R / "accurate_provenance.json").write_text(json.dumps(out, indent=1))
    (R / "accurate_provenance_rows.jsonl").write_text(
        "\n".join(json.dumps(x) for x in rows) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
