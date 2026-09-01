"""Hardened quote extraction + attribution for model-generated drafts.

Fixes the two artifact classes the Sonnet-probe audit exposed:

1. Overcapture: the legacy QUOTE_RE, calibrated on plain judicial prose,
   swallows spans of the model's own markdown prose when smart quotes go
   unbalanced. Here a quote is only a balanced smart-quote or same-line
   straight-quote pair, and any span containing paragraph breaks, headers,
   or bold markup is rejected as not-a-quote.

2. Mispairing: legacy pairing attributes a quote to the nearest citation,
   but models quote case X while citing case Y in the same passage.
   Here attribution is signal-phrase first: if a case NAME from the
   draft's own citations appears near the quote, the quote belongs to
   that case; proximity is only the fallback. This is also the seed of
   the name-mismatch detector the design owes the five-way taxonomy.

Verdict bands are unchanged from the calibrated checker (accurate /
near_miss at token coverage >= 0.85 / inaccurate / unverifiable), reusing
its normalize/fragments/contains/token_coverage primitives verbatim.
"""

import re
import sys
from pathlib import Path

GE = Path("/Users/hardy30894/Documents/NYU_Research/us_courts_gated_evolution")
sys.path.insert(0, str(GE / "src"))

from checker.quote_checker import (  # noqa: E402
    normalize,
    fragments,
    contains,
    token_coverage,
)

SMART_RE = re.compile(r"“([^“”]{20,600})”")
STRAIGHT_RE = re.compile(r'"([^"\n]{20,600})"')
NOT_A_QUOTE = re.compile(r"\n\s*\n|(^|\n)\s*#|\*\*|__")
# a span opening with a dash/closing punctuation is the tail of a quote the
# model split across a citation ("... text—" cite "—more text"): not a quote
SPLIT_ARTIFACT = re.compile(r"^\s*[—–)\].,;:]")

NAME_STOP = {
    "united", "states", "state", "people", "commonwealth", "city",
    "county", "board", "school", "court", "company", "corp",
}
CTX_BEFORE = 350
CTX_AFTER = 120
PAIR_WINDOW = 260


def extract_quotes(text):
    seen = set()
    out = []
    for rx in (SMART_RE, STRAIGHT_RE):
        for m in rx.finditer(text):
            q = m.group(1)
            if NOT_A_QUOTE.search(q) or SPLIT_ARTIFACT.match(q):
                continue
            key = (m.start(1), q[:40])
            if key in seen:
                continue
            seen.add(key)
            out.append({"quote": q, "start": m.start(1)})
    out.sort(key=lambda d: d["start"])
    return out


def name_tokens(*names):
    toks = set()
    for n in names:
        if not n:
            continue
        for t in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", n):
            if t.lower() not in NAME_STOP:
                toks.add(t.lower())
    return toks


def attribute(q, text, cites):
    """Return (cite, how) for one extracted quote.

    Named attribution is distance-based: the case name nearest the quote
    wins, measuring backwards through the signal phrase and forwards only
    to the end of the quote's own line — a name in the NEXT sentence must
    not steal the quote (the bug the seeded validation caught)."""
    qend = q["start"] + len(q["quote"])
    before = text[max(0, q["start"] - CTX_BEFORE): q["start"]].lower()
    after = text[qend: qend + CTX_AFTER].split("\n")[0].lower()
    best = None
    for c in cites:
        for t in c["tokens"]:
            i = before.rfind(t)
            if i >= 0:
                d = len(before) - (i + len(t))
                if best is None or d < best[0]:
                    best = (d, c)
            j = after.find(t)
            if j >= 0 and (best is None or j < best[0]):
                best = (j, c)
    if best:
        return best[1], "named"
    after = [c for c in cites if 0 <= c["start"] - qend <= PAIR_WINDOW]
    if after:
        return min(after, key=lambda c: c["start"]), "proximity"
    before = [
        c for c in cites if 0 <= q["start"] - c["start"] <= PAIR_WINDOW + 40
    ]
    if before:
        return max(before, key=lambda c: c["start"]), "proximity"
    return None, None


def verdict_for(q, cite, store):
    if cite is None:
        return "unpaired", None
    opinion = (
        store.get(
            cite.get("cluster_id"),
            volume=cite.get("volume"),
            reporter=cite.get("reporter"),
            page=cite.get("page"),
        )
        if cite.get("cluster_id")
        else None
    )
    if not opinion:
        return "unverifiable", None
    frags = fragments(q["quote"])
    if not frags:
        return "no_fragment", None
    text_norm = normalize(opinion)
    nospace = text_norm.replace(" ", "")
    if all(contains(f, text_norm, nospace) for f in frags):
        return "accurate", 1.0
    cov = min(token_coverage(f, text_norm) for f in frags)
    return ("near_miss" if cov >= 0.85 else "inaccurate"), round(cov, 3)


def check_draft(text, citation_records, eyecite_pass, store):
    """Score every quote in one draft.

    citation_records: from CitationChecker.check_text (verdicts, cluster ids)
    eyecite_pass: list of dicts with citation/start/plaintiff/defendant
                  (spans + party names, which the legacy records drop)
    """
    by_cite = {}
    for r in citation_records:
        by_cite.setdefault(r["citation"], r)
    cites = []
    for e in eyecite_pass:
        rec = by_cite.get(e["citation"], {})
        cites.append(
            {
                "citation": e["citation"],
                "start": e["start"],
                "tokens": name_tokens(e.get("plaintiff"), e.get("defendant")),
                "cluster_id": rec.get("cluster_id"),
                "volume": rec.get("volume") or e.get("volume"),
                "reporter": rec.get("reporter") or e.get("reporter"),
                "page": rec.get("page") or e.get("page"),
            }
        )
    results = []
    for q in extract_quotes(text):
        cite, how = attribute(q, text, cites)
        verdict, cov = verdict_for(q, cite, store)
        results.append(
            {
                "quote": q["quote"][:120],
                "citation": cite["citation"] if cite else None,
                "attribution": how,
                "verdict": verdict,
                "coverage": cov,
            }
        )
    return results


def strict_rate(results):
    acc = sum(1 for r in results if r["verdict"] == "accurate")
    bad = sum(
        1 for r in results if r["verdict"] in ("near_miss", "inaccurate")
    )
    return round(acc / (acc + bad), 3) if acc + bad else None
