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
Project U.S. Reports corpus the inaccurate bucket is searched against
and counts how many distinct opinions hold its longest fragment. One
opinion means the language identifies its source. A handful usually
means the opinion is quoted by later cases, which is ordinary. Many
means the phrase is boilerplate and the verdict rests on nothing
specific. It is a deterministic bound on the exposure, not a reading of
what any model intended.

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

    # a quotation is at risk of crediting nothing only when its language
    # is spread across many opinions, or the probe was too short to be a
    # source at all
    def bucket(x):
        if not x["distinctive"]:
            return "short_probe"
        if x["sources"] == 0:
            return "corpus_gap"
        if x["sources"] == 1:
            return "single_opinion"
        if x["sources"] <= GENERIC_AT:
            return "few_opinions"
        return "boilerplate"

    for x in rows:
        x["bucket"] = bucket(x)
    n = len(rows)
    counts = {}
    for x in rows:
        counts[x["bucket"]] = counts.get(x["bucket"], 0) + 1
    by_model = {}
    for x in rows:
        d = by_model.setdefault(x["model"], {})
        d[x["bucket"]] = d.get(x["bucket"], 0) + 1
    # the exposure: accurate verdicts whose language is not distinctive
    at_risk = counts.get("boilerplate", 0) + counts.get("short_probe", 0)
    out = {
        "n_accurate": n, "generic_at": GENERIC_AT, "counts": counts,
        "by_model": by_model,
        "at_risk": at_risk,
        "at_risk_pct": round(100 * at_risk / n, 1) if n else None,
        "single_or_few_pct": round(
            100 * (counts.get("single_opinion", 0) + counts.get("few_opinions", 0)) / n, 1) if n else None,
        "in_corpus": sum(1 for x in rows if x["sources"] > 0),
        "attributed_among_sources": sum(1 for x in rows if x["attributed_among_sources"]),
    }
    (R / "accurate_provenance.json").write_text(json.dumps(out, indent=1))
    (R / "accurate_provenance_rows.jsonl").write_text(
        "\n".join(json.dumps(x) for x in rows) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
