#!/usr/bin/env python3
"""Quote provenance search: where does each inaccurate quote REALLY come from?

For every quote the hardened instrument scored inaccurate, search the 361MB
US Reports mega-corpus for the quoted language and name the case(s) that
actually contain it. Deterministic classification of the inaccurate bucket:

  found_in_attributed   -- language IS in the attributed case (the store's
                           opinion text was partial; checker false alarm)
  misattributed         -- language found verbatim in a DIFFERENT case:
                           right words, wrong authority, proven
  not_in_scotus_corpus  -- language appears nowhere in US Reports
                           (fabricated, paraphrase, or non-SCOTUS source)

Zero API cost; pure local compute.
"""

import json
import re
import sys
from bisect import bisect_right
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path("/Users/hardy30894/Documents/NYU_Research/us_courts_gated_evolution")
sys.path.insert(0, str(GE / "src"))
sys.path.insert(0, str(HERE / "src"))

from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore, normalize, fragments  # noqa
import quotecheck2 as q2  # noqa
from rescore_pilots import eyecite_pass  # noqa

# full-run drafts (the paper's corpus); pilot dirs retired
PILOTS = {
    m: Path(__file__).resolve().parents[1] / "results" / f"full_{m}" / "drafts"
    for m in ("qwen30b", "deepseek", "gpt54mini", "sonnet")
}

CORPUS = GE / "data/scotus_corpus/original_usdb.txt"
DB = GE / "data/courtlistener/checker.db"
SEP = "docsep777pes"


def load_corpus():
    raw = CORPUS.read_text(errors="ignore")
    # documents are separated by "\n--- [ Case Name ]" (bracket sometimes
    # absent); split on the separator itself, caption from the bracket
    docs, captions = [], []
    for chunk in raw.split("\n--- "):
        if len(chunk) < 200:
            continue
        m = re.match(r"^\[?\s*([^\]\n]{3,120})\]", chunk)
        cap = m.group(1).strip() if m else chunk[:80].strip()
        captions.append(cap[:90])
        docs.append(chunk)
    del raw
    norm_docs = [normalize(d) for d in docs]
    del docs
    big = (" " + SEP + " ").join(norm_docs)
    bounds = []
    pos = 0
    for nd in norm_docs:
        bounds.append(pos)
        pos += len(nd) + len(SEP) + 2
    return big, bounds, captions


def find_case(big, bounds, captions, frag_norm):
    """Return (hits, distinctive): matched captions, and whether the probe
    that matched is long enough (>= 6 words) to identify a source rather
    than a stock legal phrase."""
    hits = []
    start = 0
    probe = frag_norm
    if probe not in big:
        words = frag_norm.split()
        if len(words) >= 10:
            mid = len(words) // 2
            probe = " ".join(words[max(0, mid - 5): mid + 5])
        if probe not in big:
            return [], False
    while len(hits) < 3:
        i = big.find(probe, start)
        if i < 0:
            break
        hits.append(captions[bisect_right(bounds, i) - 1])
        start = i + 1
    return hits, len(probe.split()) >= 6


def cap_tokens(s):
    return {
        t.lower()
        for t in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", s or "")
        if t.lower() not in q2.NAME_STOP
    }


def main():
    print("loading corpus (few minutes)...", flush=True)
    big, bounds, captions = load_corpus()
    print(f"{len(captions)} documents indexed", flush=True)

    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = OpinionTextStore(DB, cl_token=None, fetch_budget=0)

    out_lines = ["# Provenance of inaccurate quotes\n"]
    tally = {}
    for model, drafts_dir in PILOTS.items():
        for p in sorted(drafts_dir.glob("*.txt")):
            text = p.read_text()
            recs, _ = checker.check_text(text)
            res = q2.check_draft(text, recs, eyecite_pass(text), store)
            full_quotes = {q["quote"][:120]: q for q in (
                {"quote": e["quote"], "start": e["start"]}
                for e in q2.extract_quotes(text))}
            for r in res:
                if r["verdict"] != "inaccurate":
                    continue
                fq = full_quotes.get(r["quote"], {"quote": r["quote"]})
                frags = fragments(fq["quote"]) or [normalize(fq["quote"])]
                frag = max(frags, key=len)
                hits, distinctive = find_case(big, bounds, captions, frag)
                # attributed case name from the oracle
                att_name = ""
                rec = next(
                    (x for x in recs if x["citation"] == r["citation"]), None
                )
                if rec and rec.get("cluster_id"):
                    hit = index.lookup(
                        rec["volume"], rec["reporter"], rec["page"]
                    )
                    att_name = (hit or {}).get("case_name") or ""
                if not hits:
                    cls = "not_in_scotus_corpus"
                elif any(cap_tokens(h) & cap_tokens(att_name) for h in hits):
                    cls = "found_in_attributed"
                elif distinctive:
                    cls = "misattributed"
                else:
                    cls = "generic_phrase_match"
                key = (model, cls)
                tally[key] = tally.get(key, 0) + 1
                out_lines.append(
                    f"- **{cls}** | {model} {p.stem} | cited "
                    f"{r['citation']} ({att_name[:60]}) | true source: "
                    f"{hits or '—'} | “{fq['quote'][:100]}”"
                )
    out = HERE / "results/provenance_report.md"
    out.write_text("\n".join(out_lines))
    print(json.dumps({f"{m}:{c}": n for (m, c), n in tally.items()},
                     indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
