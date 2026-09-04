"""Seeded-fault validation of the quote checker (M1 criterion: "checker
validated against hand-labeled citations").

The wild-text calibration measured the checker on 19 judicial opinions —
adversarial input full of OCR noise and ambiguous attribution. This test
measures it on the distribution that actually matters: agent-style argument
text in the tight quote-then-cite format, where WE plant the quotes and
therefore know the exact truth of every one.

Per sampled opinion: two genuine sentences planted verbatim, plus three
corruptions —
  negation  : meaning-flipping insertion/removal of "not" (or shall<->may)
  word_swap : one content word replaced (subtle factual corruption)
  fabricated: a legal-sounding sentence the Court never wrote

Report: verdict distribution per planted class. A perfect instrument scores
genuine=accurate, all corruptions=inaccurate. Where corruptions land in the
near-miss band instead, that is a finding about how the GATE must treat
near-misses (conservatively), measured rather than assumed.
"""

import random
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checker.citation_checker import CitationChecker, SqliteIndex
from checker.quote_checker import QuoteChecker, OpinionTextStore

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/courtlistener/checker.db"

FABRICATED = [
    "The Constitution requires that every administrative determination be "
    "subject to plenary de novo review before an Article III tribunal.",
    "A statute that burdens interstate commerce is presumptively invalid "
    "unless ratified by a majority of the affected state legislatures.",
    "The Due Process Clause guarantees each litigant the right to select "
    "the judicial forum most favorable to its claims.",
    "Congressional silence must always be construed as an affirmative "
    "delegation of regulatory authority to the executive branch.",
    "No precedent of this Court may be overruled except upon a showing of "
    "manifest injustice established by clear and convincing evidence.",
]


def sentences_from(text):
    """Clean quotable sentences: mid-length, alphabetic, from the body."""
    body = text[len(text) // 6:]  # skip caption/headnote region
    for m in re.finditer(r"(?<=[.!?])\s+([A-Z][^.!?]{70,220}[.])", body):
        s = " ".join(m.group(1).split())
        if re.fullmatch(r"[A-Za-z0-9 ,;:'()\-\.]+", s) and s.count("(") < 2:
            yield s


def corrupt_negation(s):
    if " not " in s:
        return s.replace(" not ", " ", 1)
    for a, b in ((" is ", " is not "), (" was ", " was not "),
                 (" shall ", " may "), (" must ", " may "),
                 (" may ", " must ")):
        if a in s:
            return s.replace(a, b, 1)
    return None


def corrupt_word(s):
    words = [w for w in s.split() if len(w) >= 7 and w.isalpha()]
    if not words:
        return None
    target = words[len(words) // 2]
    swap = "jurisdiction" if target.lower() != "jurisdiction" else "immunity"
    return s.replace(target, swap, 1)


def main(n_opinions=25, seed=20260723):
    rng = random.Random(seed)
    conn = sqlite3.connect(DB)
    # sample US Reports opinions that resolve in the citation index and have
    # cluster metadata (case name + year) for realistic snippets
    rows = conn.execute("""
        SELECT t.volume, t.page, t.text, k.case_name, k.date_filed
        FROM citation_texts t
        JOIN citations c ON c.volume = t.volume AND c.page = t.page
             AND REPLACE(REPLACE(c.reporter,' ',''),'.','') = 'US'
        JOIN clusters k ON k.id = c.cluster_id
        WHERE t.reporter_norm = 'US' AND LENGTH(t.text) > 20000
              AND k.case_name != '' AND k.date_filed != ''
        GROUP BY t.volume, t.page LIMIT 400""").fetchall()
    rng.shuffle(rows)

    chk = CitationChecker(SqliteIndex(DB))
    store = OpinionTextStore(DB, cl_token=None, fetch_budget=0)
    qchk = QuoteChecker(chk.index, store, use_mega_corpus=True)

    tally = {}   # planted_class -> verdict -> count
    used = 0
    for vol, page, text, name, filed in rows:
        if used >= n_opinions:
            break
        sents = [s for s in sentences_from(text)]
        if len(sents) < 4:
            continue
        used += 1
        rng.shuffle(sents)
        year = str(filed)[:4]
        cite = f"{name}, {vol} U.S. {page} ({year})"

        planted = [("genuine", sents[0]), ("genuine", sents[1])]
        neg = corrupt_negation(sents[2])
        if neg and neg != sents[2]:
            planted.append(("negation", neg))
        swap = corrupt_word(sents[3])
        if swap and swap != sents[3]:
            planted.append(("word_swap", swap))
        planted.append(("fabricated", rng.choice(FABRICATED)))

        for cls, quote in planted:
            snippet = (f'As the Court explained, "{quote}" {cite}. That '
                       f'holding controls the question presented here.')
            recs, _ = chk.check_text(snippet)
            qres, _ = qchk.check_text(snippet, recs)
            verdict = qres[0]["verdict"] if qres else "NOT_SCORED"
            tally.setdefault(cls, {}).setdefault(verdict, 0)
            tally[cls][verdict] += 1

    print(f"opinions used: {used}")
    print(f"{'planted class':14s} {'accurate':>9s} {'near_miss':>10s} "
          f"{'inaccurate':>11s} {'other':>7s}")
    for cls in ("genuine", "negation", "word_swap", "fabricated"):
        v = tally.get(cls, {})
        other = sum(c for k, c in v.items()
                    if k not in ("accurate", "near_miss", "inaccurate"))
        print(f"{cls:14s} {v.get('accurate', 0):9d} "
              f"{v.get('near_miss', 0):10d} {v.get('inaccurate', 0):11d} "
              f"{other:7d}")


if __name__ == "__main__":
    main()
