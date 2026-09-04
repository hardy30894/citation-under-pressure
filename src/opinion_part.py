#!/usr/bin/env python3
"""Which opinion does an accurate quotation actually come from?

The text the checker compares a quotation against is one record per
case, and that record holds the Court's opinion, any concurrences, any
dissents, and the head matter (syllabus, counsel, headnotes) together.
A draft that quotes a dissent and cites the case therefore passes the
verbatim check, though attributing a dissent's words to the Court is
the kind of misrepresentation the check exists to catch. Quoting a
dissent is proper when the draft says so, so the question is both where
the words came from and whether the draft signalled it.

The Caselaw Access Project's HTML marks the parts structurally, as
<section class="head-matter"> and <article class="opinion"
data-type="majority|concurrence|dissent">, so this measures rather than
guesses. For every quotation the full run scores accurate against a
U.S. Reports authority the archive holds, it finds which part contains
the quotation's longest fragment, and, when that part is not the
majority, whether the draft's own sentence flags it (dissenting,
concurring, in dissent, and the like). Writes results/opinion_part.json.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
R = HERE / "results"

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore, normalize, contains  # noqa: E402
from local_text import ChainTextStore, CapStore, _norm_rep  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from records_dump import MODELS  # noqa: E402

PART_RE = re.compile(
    r'<section class="head-matter">|<article class="opinion" data-type="([a-z]+)"', re.I)
SIGNAL = re.compile(r"dissent|concurr|separate opinion|plurality", re.I)


def parts(html):
    """[(part name, normalized text)] for one CAP case record."""
    marks = [(m.start(), (m.group(1) or "head-matter").lower())
             for m in PART_RE.finditer(html)]
    if not marks:
        return []
    out = []
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(html)
        seg = re.sub(r"<[^>]+>", " ", html[pos:end])
        out.append((name, normalize(seg)))
    return out


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    cap = CapStore()
    cache = {}
    counts = Counter()
    per = defaultdict(Counter)
    sample = []
    for model in MODELS:
        for p in sorted((R / f"full_{model}" / "drafts").glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            text = p.read_text()
            recs, _ = checker.check_text(text)
            qres = q2.check_draft(text, recs, eyecite_pass(text), store)
            by_cite = {r["citation"]: r for r in recs}
            quotes = q2.extract_quotes(text)
            assert len(quotes) == len(qres)
            for q, r in zip(quotes, qres):
                if r["verdict"] != "accurate":
                    continue
                counts["accurate"] += 1
                rec = by_cite.get(r["citation"], {})
                vol, rep, pg = rec.get("volume"), rec.get("reporter"), rec.get("page")
                if not (vol and rep and pg) or _norm_rep(rep) != "US":
                    counts["not_us_reports"] += 1
                    continue
                key = (vol, pg)
                if key not in cache:
                    html = cap.get(vol, rep, pg, want_html=True)
                    cache[key] = parts(html) if html else None
                ps = cache[key]
                if not ps:
                    counts["no_archive"] += 1
                    continue
                counts["checked"] += 1
                frags = q2.fragments(r["quote"])
                if not frags:
                    continue
                longest = max(frags, key=len)
                where = [name for name, body in ps
                         if contains(longest, body, body.replace(" ", ""))]
                if not where:
                    counts["not_located"] += 1
                    continue
                # the majority wins when the words appear in more than one
                # part, since the syllabus quotes the opinion it summarises
                part = "majority" if "majority" in where else where[0]
                counts[part] += 1
                per[f"{model}:{cond}"][part] += 1
                if part != "majority":
                    ctx = text[max(0, q["start"] - 260): q["start"] + 160]
                    flagged = bool(SIGNAL.search(ctx))
                    counts[f"{part}:{'flagged' if flagged else 'unflagged'}"] += 1
                    counts["separate"] += 1
                    counts["separate_flagged"] += flagged
                    if len(sample) < 60:
                        sample.append({"model": model, "draft": p.stem,
                                       "citation": r["citation"], "part": part,
                                       "signalled": flagged, "quote": r["quote"][:150]})
        print(model, dict(counts), flush=True)
    out = {"pooled": dict(counts), "cells": {k: dict(v) for k, v in per.items()}, "sample": sample}
    loc = counts["majority"] + counts["separate"]
    out["located"] = loc
    out["separate_share"] = round(counts["separate"] / loc, 4) if loc else None
    out["separate_unflagged"] = counts["separate"] - counts["separate_flagged"]
    out["unflagged_share_of_located"] = round(out["separate_unflagged"] / loc, 4) if loc else None
    (R / "opinion_part.json").write_text(json.dumps(out, indent=1))
    print("located", loc, "separate", counts["separate"],
          "of which unsignalled", out["separate_unflagged"],
          "share of located", out["unflagged_share_of_located"])


if __name__ == "__main__":
    main()
