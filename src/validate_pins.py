#!/usr/bin/env python3
"""Seeded-fault validation of the existence checker and the pincite
verifier, the companion of validate_q2.py (which covers quotations).

WE plant the citations and pins, so the truth of every one is known.

Per sampled U.S. Reports opinion with page-labelled CAP HTML:
(a) a genuine sentence from page p, cited with the correct citation and
    pincite p (must adjudicate as on the cited page);
(b) the same sentence cited with a pincite three or more pages away
    inside the case's span (must adjudicate as on a different page of the
    cited case, neither at nor adjacent to the pin);
(c) a real citation from the index, another sampled opinion (must exist);
(d) a fabricated citation, the sampled volume with a page the index does
    not hold (must be not_found);
(e) a vendor citation, 20xx WL nnnnnnn (the checker labels vendor
    citations unresolvable by design, never not_found; must be so).

Items (a) and (b) go through pincites.tally_texts, the pipeline that
produced the paper's pincite figures; (c) to (e) through the citation
checker. Writes results/validate_pins.json."""

import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from pilot import DB  # noqa: E402  (adds the checker package to the path)
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import normalize, fragments  # noqa: E402
from local_text import CapStore, html_pages  # noqa: E402
from pincites import tally_texts  # noqa: E402

random.seed(20260831)
N_CASES = 20
MIN_PAGES = 6


def clean_sentences(page_text):
    """Sentences of 12 to 40 words with no quotation marks, brackets,
    ellipses, or footnote digits, so the planted quote is a plain span."""
    text = re.sub(r"\s+", " ", page_text)
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text):
        s = s.strip()
        w = s.split()
        if not 12 <= len(w) <= 40:
            continue
        if re.search(r"[\"“”\[\]…]|\.\s*\.\s*\.|\d", s):
            continue
        if not re.match(r"^[A-Z][a-z]", s):
            continue
        out.append(s)
    return out


def pick_plant(pages):
    """A (page, sentence, far_pin) triple: the sentence occurs on one page
    only, and far_pin is a page in the span at least three away whose
    neighbours do not contain the sentence either."""
    span = sorted(pages)
    norm = {p: normalize(t) for p, t in pages.items()}
    cands = [p for p in span[1:] if len(pages[p].split()) > 150]
    random.shuffle(cands)
    for p in cands:
        sents = clean_sentences(pages[p])
        random.shuffle(sents)
        for s in sents:
            frags = fragments(s)
            if not frags:
                continue
            frag = normalize(max(frags, key=len))
            hits = [q for q in span if frag in norm[q]]
            if hits != [p]:
                continue
            fars = [q for q in span if abs(q - p) >= 3
                    and not any(frag in norm.get(r, "") for r in (q - 1, q, q + 1))]
            if not fars:
                continue
            return p, s, min(fars, key=lambda q: abs(q - p))
    return None


def main():
    cap = CapStore()
    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    rows = cap.con.execute(
        "SELECT volume, page, html FROM cap_texts WHERE slug='us' "
        "AND html IS NOT NULL AND length(text) > 8000 LIMIT 600"
    ).fetchall()
    random.shuffle(rows)

    tally = {}
    cases = []
    n_cases = 0

    def hit(label, ok, got):
        key = (label, "pass" if ok else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1

    for k, (vol, page, html) in enumerate(rows):
        if n_cases >= N_CASES:
            break
        info = index.lookup(vol, "U.S.", page)
        if not info or not info.get("case_name"):
            continue
        pages = html_pages(html, first_page=page)
        if len(pages) < MIN_PAGES:
            continue
        plant = pick_plant(pages)
        if not plant:
            continue
        p, sent, far = plant
        name = info["case_name"]
        year = (info.get("date_filed") or "1950")[:4]
        # (c) another real opinion from the sample
        ovol, opage, _ = rows[(k + 37) % len(rows)]
        oinfo = index.lookup(ovol, "U.S.", opage)
        if not oinfo:
            continue
        # (d) a page the index does not hold in this volume
        fake_page = None
        for cand in (9001, 9017, 9101, 9203):
            if not index.lookup(vol, "U.S.", cand):
                fake_page = cand
                break
        if fake_page is None:
            continue
        n_cases += 1

        draft_a = (f"As the Court held in {name}, {vol} U.S. {page}, {p} ({year}), "
                   f"“{sent}” That principle controls here.")
        draft_b = (f"As the Court held in {name}, {vol} U.S. {page}, {far} ({year}), "
                   f"“{sent}” That principle controls here.")
        ta = tally_texts([draft_a], cap, checker)
        tb = tally_texts([draft_b], cap, checker)
        hit("pin: quote on cited page", ta["quote_at_pin"] == 1 and ta["pin_in_span"] == 1,
            {k_: v for k_, v in ta.items() if v})
        hit("pin: quote on a different page", tb["quote_not_at_pin"] == 1 and tb["pin_in_span"] == 1,
            {k_: v for k_, v in tb.items() if v})

        draft_c = (f"See {oinfo['case_name']}, {ovol} U.S. {opage} ({(oinfo.get('date_filed') or '1950')[:4]}); "
                   f"Doe v. Roe, {vol} U.S. {fake_page} ({year}); "
                   f"Poe v. Coe, 2019 WL 1234567 (S.D.N.Y. 2019).")
        recs, _ = checker.check_text(draft_c)
        by = {r["citation"]: r["verdict"] for r in recs}
        got_c = by.get(f"{ovol} U.S. {opage}", "NOT_EXTRACTED")
        got_d = by.get(f"{vol} U.S. {fake_page}", "NOT_EXTRACTED")
        got_e = next((v for c, v in by.items() if "WL" in c), "NOT_EXTRACTED")
        hit("existence: real citation", got_c == "exists", got_c)
        hit("existence: fabricated citation", got_d == "not_found", got_d)
        hit("existence: vendor citation", got_e == "unresolvable", got_e)
        cases.append({"citation": f"{vol} U.S. {page}", "pin": p, "far_pin": far,
                      "real": f"{ovol} U.S. {opage}", "fake": f"{vol} U.S. {fake_page}"})

    print(f"{n_cases} seeded cases")
    for (label, outcome), n in sorted(tally.items()):
        print(f"  {label:36s} {outcome:20s} {n}")
    (HERE / "results" / "validate_pins.json").write_text(json.dumps(
        {"seeded_cases": n_cases,
         "tally": {f"{l} | {o}": n for (l, o), n in sorted(tally.items())},
         "cases": cases}, indent=1))


if __name__ == "__main__":
    main()
