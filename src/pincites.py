#!/usr/bin/env python3
"""Page-level pincite verification over CAP star pagination (U.S. Reports).

For every full-run draft citation carrying a pinpoint page: is the pin
inside the case's true span, and if a quote is attributed to that cite,
does the quoted language actually sit on the cited page (+/- one page)?
This is the measurement LePhantomCite says needs Westlaw/Lexis access."""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import normalize, fragments  # noqa: E402
from local_text import CapStore, html_pages, _norm_rep  # noqa: E402
from pilot import DB, cite_details  # noqa: E402
import quotecheck2 as q2  # noqa: E402

MODELS = tuple(
    p.name.replace("full_", "")
    for p in sorted((Path(__file__).resolve().parents[1] / "results").glob("full_*"))
    if len(list((p / "drafts").glob("*.txt"))) >= 240
)


def tally_texts(texts, cap, checker):
    """Pincite tally over an iterable of draft or brief texts."""
    tally = {"no_pin": 0, "non_us": 0, "pin_in_span": 0,
             "pin_out_of_span": 0, "no_cap_data": 0,
             "quote_at_pin": 0, "quote_near_pin": 0,
             "quote_not_at_pin": 0}
    for text in texts:
        details = cite_details(text)
        recs, _ = checker.check_text(text)
        qres = q2.check_draft(
            text, recs, eyecite_pass(text),
            type("S", (), {"get": lambda *a, **k: None})())
        quotes_by_cite = {}
        for r in qres:
            if r["citation"]:
                quotes_by_cite.setdefault(r["citation"], []).append(
                    r["quote"])
        for d in details:
            if d["pin_page"] is None:
                tally["no_pin"] += 1
                continue
            if _norm_rep(d["reporter"]) != "US":
                tally["non_us"] += 1
                continue
            html = cap.get(d["volume"], d["reporter"], d["page"],
                           want_html=True)
            if not html:
                tally["no_cap_data"] += 1
                continue
            pages = html_pages(html, first_page=d["page"])
            span = sorted(pages)
            if not span:
                tally["no_cap_data"] += 1
                continue
            pin = d["pin_page"]
            if not (span[0] <= pin <= span[-1]):
                tally["pin_out_of_span"] += 1
                continue
            tally["pin_in_span"] += 1
            qs = quotes_by_cite.get(d["citation"], [])
            for qtext in qs:
                frags = fragments(qtext)
                if not frags:
                    continue
                frag = normalize(max(frags, key=len))
                at_pin = frag in normalize(pages.get(pin, ""))
                near = any(
                    frag in normalize(pages.get(pp, ""))
                    for pp in (pin - 1, pin + 1)
                )
                anywhere = any(
                    frag in normalize(t) for t in pages.values()
                )
                if at_pin:
                    tally["quote_at_pin"] += 1
                elif near:
                    tally["quote_near_pin"] += 1
                elif anywhere:
                    tally["quote_not_at_pin"] += 1
    return tally


def main():
    cap = CapStore()
    checker = CitationChecker(SqliteIndex(DB))
    out_path = HERE / "results/pincites.json"
    out = json.loads(out_path.read_text()) if out_path.exists() else {}
    only = sys.argv[1:] or (list(MODELS) + ["human"])
    for model in only:
        if model == "human":
            # the human reference: the same clean LePhantomCite brief
            # excerpts that anchor the quotation baseline
            from human_baseline import load_clean_excerpts
            texts = [r["text"] for r in load_clean_excerpts()]
        else:
            drafts = HERE / "results" / f"full_{model}" / "drafts"
            texts = [p.read_text() for p in sorted(drafts.glob("*.txt"))]
        out[model] = tally_texts(texts, cap, checker)
        print(model, out[model], flush=True)
        out_path.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
