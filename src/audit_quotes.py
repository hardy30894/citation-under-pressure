#!/usr/bin/env python3
"""Audit Sonnet's 'inaccurate' quote verdicts against source opinions.

For every quote the checker scored inaccurate, print the model's quoted
language next to the closest matching passage in the cited opinion, so a
human read can classify: real misquote / paraphrase-in-quotes vs checker
noise (OCR, pairing, attribution). Zero API cost: opinion texts come from
the local store; no LLM calls.
"""

import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path(__file__).resolve().parents[1]  # vendored checker, runtime, sim, packets

from checker.citation_checker import CitationChecker, SqliteIndex
from checker.quote_checker import (
    QuoteChecker,
    OpinionTextStore,
    normalize,
    fragments,
    token_coverage,
)

from pilot import DB  # noqa: E402
DRAFTS = HERE / "results/pilot_sonnet/drafts"
OUT = HERE / "results/pilot_sonnet/quote_audit.md"


def best_window(frag_norm, text_norm, pad=40):
    """Locate the closest region of the opinion to the quoted fragment."""
    sm = difflib.SequenceMatcher(None, frag_norm, text_norm, autojunk=False)
    m = sm.find_longest_match(0, len(frag_norm), 0, len(text_norm))
    if m.size < 10:
        return None, 0.0
    start = max(0, m.b - m.a - pad)
    end = min(len(text_norm), start + len(frag_norm) + 2 * pad)
    window = text_norm[start:end]
    ratio = difflib.SequenceMatcher(None, frag_norm, window).ratio()
    return window, round(ratio, 3)


def main():
    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = OpinionTextStore(DB, cl_token=None, fetch_budget=0)
    qchk = QuoteChecker(index, store, use_mega_corpus=False)

    lines = ["# Quote audit: Sonnet probe (inaccurate verdicts)\n"]
    n_bad = 0
    for draft_path in sorted(DRAFTS.glob("*.txt")):
        text = draft_path.read_text()
        recs, _ = checker.check_text(text)
        qres, _ = qchk.check_text(text, recs)
        by_cite = {r["citation"]: r for r in recs}
        for q in qres:
            if q["verdict"] != "inaccurate":
                continue
            n_bad += 1
            cite = q.get("citation") or ""
            rec = by_cite.get(cite, {})
            cluster = rec.get("cluster_id")
            opinion = (
                store.get(
                    cluster,
                    volume=rec.get("volume"),
                    reporter=rec.get("reporter"),
                    page=rec.get("page"),
                )
                if cluster
                else None
            )
            # recover the full quote from the draft by prefix match
            prefix = q["quote"][:80]
            mstart = text.find(prefix)
            full_quote = q["quote"]
            if mstart >= 0:
                m = re.match(
                    r'[^"”"]{0,600}', text[mstart:]
                )
                if m:
                    full_quote = m.group()
            lines.append(f"\n## {draft_path.stem} | {cite}")
            lines.append(f"**Model quoted:** “{full_quote.strip()}”")
            if not opinion:
                lines.append("**Opinion text:** UNAVAILABLE locally "
                             "(pairing/attribution audit needed)")
                continue
            text_norm = normalize(opinion)
            frags = fragments(full_quote)
            if not frags:
                lines.append("**No scoreable fragment** (short quote)")
                continue
            for f in frags:
                win, ratio = best_window(f, text_norm)
                cov = token_coverage(f, text_norm)
                lines.append(
                    f"- fragment (cov={cov:.2f}, best-match ratio={ratio}):"
                    f"\n  - quoted: `{f[:160]}`"
                    f"\n  - opinion: `{(win or 'NO MATCH REGION')[:200]}`"
                )
    lines.append(f"\n\nTotal inaccurate quotes audited: {n_bad}\n")
    OUT.write_text("\n".join(lines))
    print(f"{n_bad} inaccurate quotes -> {OUT}")


if __name__ == "__main__":
    main()
