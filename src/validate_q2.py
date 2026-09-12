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
extractor must reject both. Three further plants cover the attribution
faults the real-draft audit exposed: a genuine sentence introduced by a
signal phrase naming its case while a different case's citation follows
within the pairing window (must score accurate against the named case);
a statutory quotation introduced by a U.S.C. section with no case name
(must be left unpaired); two quotations in one sentence, whose
between-span must not be extracted as a quotation; a quotation whose own
sentence names no case but follows, in the same paragraph, a sentence
citing its case (attributed to that case); a quotation in a paragraph
with no citation (must be left unpaired); a quotation whose sentence
carries "Id." after a citation (must score against that citation); and a
parenthetical quotation inside a string cite, which belongs to the
citation before it and not the one after. Two further plants cover
attribution across citation strings: a genuine sentence followed by the
case's full parallel citation, where the quotation must be attributed to
the case and not to the last reporter in the string, and a genuine
sentence from one case followed by a nearer citation introduced by
"cert. denied", which is procedural history and must not take it.
"""

import random
import re
from difflib import SequenceMatcher
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path(__file__).resolve().parents[1]  # vendored checker, runtime, sim, packets
sys.path.insert(0, str(HERE / "src"))

from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa
from eyecite import get_citations  # noqa
from eyecite.models import FullCaseCitation  # noqa
import quotecheck2 as q2  # noqa

from pilot import DB  # noqa: E402
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
        if 70 <= len(s.strip()) <= 220 and not any(ch in s for ch in '"“”\n')
        and not s.strip().startswith(("(", "["))
    ]
    return random.choice(sents[len(sents) // 4: -len(sents) // 4 or None]) \
        if len(sents) >= 8 else None


CITE_IN_SENT = re.compile(
    r",\s*\d+ U\. ?S\. \d+"
    r"(?:[, ]+(?:\d+(?:[-\u2013]\d+|&#8212;\d+)?|S\.Ct\.|L\.Ed\.2d|L\.Ed\.|Pet\.|How\.|Wall\.|Cranch|Dall\.))*"
    r"(?: \(\d{4}\))?")  # a reporter citation inside a sentence, with its parallel cites; the case name stays


def sample_cited_sentence(text):
    """A sentence that carries a U.S. Reports citation inside it, returned
    with the citation removed (the quoter's "(citation omitted)") and with
    three words of text removed instead (a misquotation)."""
    guarded = re.sub(r"\bU\. ?S\.", "U@S@", text)  # abbreviations are not sentence ends
    guarded = re.sub(r"\b(v|Id|Co|Inc|Cir|No|Mr|Mrs|Dr|St|Ct|Ed|L|S)\.", r"\1@", guarded)
    for s in re.split(r"(?<=[.;])\s+", guarded):
        s = s.strip().replace("@", ".")
        m = CITE_IN_SENT.search(s)
        if not (80 <= len(s) <= 300) or any(ch in s for ch in '"“”&*\n') or s[0].isdigit() or not m:
            continue
        head, tail = s[:m.start()], s[m.end():]
        if len(head) < 20 or len(tail) < 20:
            continue
        omitted = (head + " " + tail).replace("  ", " ").strip()
        hw, tw = head.split(), tail.split()
        # drop three words of prose away from the citation's position, so
        # the gap they leave in the opinion holds no citation and cannot pass
        if len(hw) >= 8 and all(w.isalpha() and len(w) >= 3 for w in hw[:2]):
            k = 2
            gapped = " ".join(hw[:k] + hw[k + 3:] + tw)
        elif len(tw) >= 8:
            k = len(tw) - 5
            gapped = " ".join(hw + tw[:k] + tw[k + 3:])
        else:
            continue
        return omitted, gapped
    return None, None


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
    # a real parallel citation pair, so the two tokens share an opinion
    par = con.execute(
        "SELECT c2.volume, c2.reporter, c2.page FROM citations c1 "
        "JOIN citations c2 ON c1.cluster_id = c2.cluster_id "
        "WHERE REPLACE(REPLACE(c1.reporter,' ',''),'.','') = 'US' "
        "  AND REPLACE(REPLACE(c2.reporter,' ',''),'.','') = 'SCt' LIMIT 1").fetchone()
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
        omitted, gapped = sample_cited_sentence(text)
        if not omitted or not par:
            continue
        n_cases += 1
        if n_cases > 20:
            break
        short = (name or "Doe v. Roe").split(" v. ")[0].split(",")[0]
        if not q2.name_tokens(short):  # "United States" names no case
            short = (name or "Doe v. Roe").split(" v. ")[-1].split(",")[0]
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
            f"follows in this section”\n\n"
            f"In *{short}*, the Court held that “{sent}” See also {wname}, "
            f"{wvol} U.S. {wpage} (1951).\n\n"
            f"The statute, 28 U.S.C. § 1407(a), provides that “civil actions "
            f"involving one or more common questions of fact are pending in "
            f"different districts” and nothing more. {wname}, {wvol} U.S. {wpage}.\n\n"
            f"The court called it “a plain command” and then “an anomaly” in "
            f"the same breath, {wname}, {wvol} U.S. {wpage} (1951).\n\n"
            f"{name}, {vol} U.S. {page} (1950), is instructive. As the Court "
            f"there recognized, “{sent2}”\n\n"
            f"As courts have long recognized, “{corrupt(sent2)}”\n\n"
            f"{name}, {vol} U.S. {page} (1950). Id. at 5. The Court added that "
            f"“{sent}”\n\n"
            f"See {name}, {vol} U.S. {page}, 9 (1950) (holding that “{sent}”); "
            f"{wname}, {wvol} U.S. {wpage}, 4 (1951) (same).\n\n"
            f"The Court explained that “{omitted}” {name}, {vol} U.S. {page}, "
            f"5 (1950) (citation omitted).\n\n"
            f"The Court explained that “{gapped}” {name}, {vol} U.S. {page} (1950).\n\n"
            f"As the Court put it, “{sent2}” {name}, {vol} U.S. {page}, 7, "
            f"{par[0]} {par[1]} {par[2]} (1950).\n\n"
            f"The panel below agreed. {wname}, {wvol} U.S. {wpage} (1951), "
            f"cert. denied, {vol} U.S. {page} (1950). It held that “{sent}”"
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
        # the signal-phrase plant is the second occurrence of `sent`
        sig = [x for x in res if x["quote"].startswith(sent[:40])]
        got = sig[1]["verdict"] if len(sig) > 1 else "NOT_EXTRACTED"
        key = ("signal phrase vs following cite", "pass" if got == "accurate" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        stat = next((x for x in res if x["quote"].startswith("civil actions involving")), None)
        got = stat["verdict"] if stat else "NOT_EXTRACTED"
        key = ("statutory quote unpaired", "pass" if got == "unpaired" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        # a quotation whose sentence names no case follows the case cited
        # in the sentence before, in the same paragraph: attributed to it
        para = [x for x in res if x["quote"].startswith(sent2[:40])]
        got = para[1]["verdict"] if len(para) > 1 else "NOT_EXTRACTED"
        key = ("paragraph attribution", "pass" if got == "accurate" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        # a quotation in a paragraph with no citation is left unpaired
        orphan = [x for x in res if x["quote"].startswith(corrupt(sent2)[:40])]
        got = orphan[0]["verdict"] if orphan else "NOT_EXTRACTED"
        key = ("no citation in paragraph: unpaired", "pass" if got == "unpaired" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        # "Id." in the sentence points at the preceding citation
        idq = [x for x in res if x["quote"].startswith(sent[:40])]
        got = idq[2]["verdict"] if len(idq) > 2 else "NOT_EXTRACTED"
        key = ("Id. to preceding citation", "pass" if got == "accurate" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        # a parenthetical quotation in a string cite belongs to the citation
        # it follows, not the one after it
        pq = [x for x in res if x["quote"].startswith(sent[:40])]
        got = pq[3]["verdict"] if len(pq) > 3 else "NOT_EXTRACTED"
        key = ("string-cite parenthetical", "pass" if got == "accurate" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        # check_draft keeps 120 characters of each quotation, so the two plants
        # are located by their position in the draft
        quotes = q2.extract_quotes(draft)
        assert len(quotes) == len(res)

        def at(planted):
            pos = draft.find("\u201c" + planted) + 1
            return next((r for q, r in zip(quotes, res) if q["start"] == pos), None)
        par_hits = [x for x in res if x["quote"].startswith(sent2[:40])]
        got = par_hits[2]["citation"] if len(par_hits) > 2 else "NOT_EXTRACTED"
        key = ("parallel cite attribution",
               "pass" if got == f"{vol} U.S. {page}" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        proc = [x for x in res if x["quote"].startswith(sent[:40])]
        got = proc[4]["citation"] if len(proc) > 4 else "NOT_EXTRACTED"
        key = ("cert. denied not a source",
               "pass" if got == f"{wvol} U.S. {wpage}" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        om = at(omitted)
        got = om["verdict"] if om else "NOT_EXTRACTED"
        key = ("omitted internal citation", "pass" if got == "accurate" else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        gp = at(gapped)
        got = gp["verdict"] if gp else "NOT_EXTRACTED"
        key = ("omitted words, no ellipsis", "pass" if got in ("inaccurate", "near_miss") else f"FAIL({got})")
        tally[key] = tally.get(key, 0) + 1
        between = [x for x in res if "and then" in x["quote"]]
        key = ("between-span rejection", "pass" if not between else "FAIL(extracted)")
        tally[key] = tally.get(key, 0) + 1
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
