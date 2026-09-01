#!/usr/bin/env python3
"""Seeded-fault validation of the hardened quote instrument (quotecheck2).

Same discipline that validated the original checker: WE plant the quotes,
so the truth of every one is known exactly.

Per sampled U.S. Reports opinion: one genuine sentence planted verbatim
with its correct citation (must score accurate); one planted with a WRONG
case's citation named in the signal phrase (attribution must follow the
named case and score inaccurate there); one word-swap corruption (must not
score accurate); one wholly fabricated sentence (must not score accurate).
Also plants a split-quote artifact and a markdown header in quotes; the
extractor must reject both.
"""

import random
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path("/Users/hardy30894/Documents/NYU_Research/us_courts_gated_evolution")
sys.path.insert(0, str(GE / "src"))
sys.path.insert(0, str(HERE / "src"))

from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa
from eyecite import get_citations  # noqa
from eyecite.models import FullCaseCitation  # noqa
import quotecheck2 as q2  # noqa

DB = GE / "data/courtlistener/checker.db"
random.seed(20260831)


def eyecite_pass(text):
    out = []
    for cite in get_citations(text):
        if not isinstance(cite, FullCaseCitation):
            continue
        g = cite.groups or {}
        out.append({
            "citation": cite.corrected_citation(), "start": cite.span()[0],
            "volume": g.get("volume"), "reporter": g.get("reporter"),
            "page": g.get("page"),
            "plaintiff": getattr(cite.metadata, "plaintiff", None),
            "defendant": getattr(cite.metadata, "defendant", None),
        })
    return out


def sample_sentence(text):
    sents = [
        s.strip() for s in re.split(r"(?<=[.;])\s+", text)
        if 70 <= len(s.strip()) <= 220 and '"' not in s and "“" not in s
        and not s.strip().startswith(("(", "["))
    ]
    return random.choice(sents[len(sents) // 4: -len(sents) // 4 or None]) \
        if len(sents) >= 8 else None


def corrupt(sentence):
    words = sentence.split()
    words[2] = "purple"  # early swap: no shared 40-char prefix with genuine
    return " ".join(words)


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT ct.volume, ct.page, c.case_name FROM citation_texts ct "
        "JOIN citations ci ON ci.volume=ct.volume AND ci.page=ct.page AND "
        "REPLACE(REPLACE(ci.reporter,' ',''),'.','')=ct.reporter_norm "
        "JOIN clusters c ON c.id=ci.cluster_id "
        "WHERE ct.reporter_norm='US' AND LENGTH(ct.text)>8000 LIMIT 400"
    ).fetchall()
    random.shuffle(rows)

    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = OpinionTextStore(DB, cl_token=None, fetch_budget=0)

    tally = {}
    n_cases = 0
    for k in range(0, len(rows) - 1):
        vol, page, name = rows[k]
        wvol, wpage, wname = rows[(k + 37) % len(rows)]
        hit = index.lookup(vol, "U.S.", page)
        text = store.get(
            (hit or {}).get("cluster_id"),
            volume=vol, reporter="U.S.", page=page,
        )
        if not text:
            continue
        sent = sample_sentence(text)
        sent2 = sample_sentence(text)
        if not sent or not sent2 or sent == sent2:
            continue
        n_cases += 1
        if n_cases > 20:
            break
        short = (name or "Doe v. Roe").split(" v. ")[0].split(",")[0]
        wshort = (wname or "Poe v. Coe").split(" v. ")[0].split(",")[0]
        draft = (
            f"## I. Argument\n\n"
            f"As the Court held in {name}, {vol} U.S. {page} (1950), "
            f"“{sent}” That principle controls here.\n\n"
            f"The rule in {wname}, {wvol} U.S. {wpage} (1951), was that "
            f"“{sent2}” as {wshort} makes clear.\n\n"
            f"Petitioner relies on {short}'s statement that "
            f"“{corrupt(sent)}” but misreads it. Respondent answers with "
            f"“the wholly invented proposition that federal courts must "
            f"defer to astrological guidance in matters of procedure,” "
            f"citing {name}, {vol} U.S. {page} (1950).\n\n"
            f"“—and further,” the brief adds, “## II. More argument here "
            f"follows in this section”"
        )
        recs, _ = checker.check_text(draft)
        res = q2.check_draft(draft, recs, eyecite_pass(draft), store)
        # expectations, matched by quote prefix
        exp = [
            (sent[:40], "accurate", "genuine+right cite"),
            (sent2[:40], "inaccurate", "genuine text, WRONG named cite"),
            (corrupt(sent)[:40], "not_accurate", "word-swap corruption"),
            ("the wholly invented proposition", "not_accurate", "fabricated"),
        ]
        for prefix, want, label in exp:
            r = next(
                (x for x in res if x["quote"].startswith(prefix[:40])), None
            )
            got = (f"{r['verdict']}@{r['citation']}" if r else "NOT_EXTRACTED")
            got = got.split("@")[0] if r else got
            if want == "accurate":
                ok = got == "accurate"
            elif want == "inaccurate":
                ok = got in ("inaccurate", "near_miss")
            else:
                ok = got != "accurate" and got != "NOT_EXTRACTED"
            key = (label, "pass" if ok else f"FAIL({got})")
            tally[key] = tally.get(key, 0) + 1
        # artifacts must NOT be extracted
        artifacts = [r for r in res if r["quote"].startswith(("—and", "## "))]
        key = ("artifact rejection",
               "pass" if not artifacts else "FAIL(extracted)")
        tally[key] = tally.get(key, 0) + 1

    print(f"{n_cases - 1 if n_cases > 20 else n_cases} seeded cases")
    for (label, outcome), n in sorted(tally.items()):
        print(f"  {label:32s} {outcome:20s} {n}")


if __name__ == "__main__":
    main()
