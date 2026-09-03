#!/usr/bin/env python3
"""Two checks the final review asked for.

Era check. Pre-1970 opinions in the public archives are scanned text,
so a strict verbatim standard could penalize quotations from old cases
for OCR reasons and make the temporal condition's quotation fall an
artifact. Within the baseline condition, where nothing pushes a model
toward old cases, this reports strict quotation accuracy for quotations
attributed to opinions decided before 1970 and from 1970 on, per model
and pooled.

Attribution check. A misattributed quotation (verbatim in a different
opinion than the one cited) could be an attribution error of the
checker when the true source is also cited in the same draft. This
reports, for each model, how many misattributed quotations have a true
source whose name matches a case cited anywhere in the same draft.
Writes results/era_attribution_check.json."""

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
from checker.quote_checker import OpinionTextStore  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB, cite_details  # noqa: E402
import quotecheck2 as q2  # noqa: E402

MODELS = ("qwen30b", "mistralsmall", "deepseek", "grok43", "sonnet", "llama4mav", "gpt54mini")


def era_check(checker, store, index):
    out = {}
    pooled = Counter()
    for m in MODELS:
        c = Counter()
        for p in sorted((R / f"full_{m}" / "drafts").glob("*_baseline.txt")):
            text = p.read_text()
            recs, _ = checker.check_text(text)
            qres = q2.check_draft(text, recs, eyecite_pass(text), store)
            years = {}
            for d in cite_details(text):
                if d["volume"] and d["reporter"] and d["page"]:
                    h = index.lookup(d["volume"], d["reporter"], d["page"])
                    y = re.match(r"\d{4}", (h or {}).get("date_filed") or "")
                    if y:
                        years[d["citation"]] = int(y.group(0))
            for r in qres:
                if r["verdict"] not in ("accurate", "near_miss", "inaccurate"):
                    continue
                y = years.get(r["citation"])
                if y is None:
                    continue
                era = "pre1970" if y < 1970 else "post1970"
                c[era + "_scored"] += 1
                if r["verdict"] == "accurate":
                    c[era + "_acc"] += 1
        pooled.update(c)
        out[m] = {k: c[k] for k in sorted(c)}
        for era in ("pre1970", "post1970"):
            n = c[era + "_scored"]
            out[m][era + "_strict"] = round(c[era + "_acc"] / n, 3) if n else None
    out["pooled"] = {k: pooled[k] for k in sorted(pooled)}
    for era in ("pre1970", "post1970"):
        n = pooled[era + "_scored"]
        out["pooled"][era + "_strict"] = round(pooled[era + "_acc"] / n, 3) if n else None
    return out


def name_tokens(s):
    return {t.lower() for t in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", s or "")
            if t.lower() not in q2.NAME_STOP}


def attribution_check(index):
    """For each misattributed quotation in provenance_report.md, is a
    true-source case cited elsewhere in the same draft?"""
    out = {}
    pat = re.compile(r"- \*\*misattributed\*\* \| (\w+) (\S+) \| cited (.+?) \((.*?)\) \| true source: \[(.*?)\] \|")
    per = defaultdict(lambda: Counter())
    cache = {}
    # the CAP-cache report (provenance.py --corpus cap) when present,
    # else the original dump's report
    report = R / "provenance_report_cap.md"
    if not report.exists():
        report = R / "provenance_report.md"
    for line in open(report):
        m = pat.match(line)
        if not m:
            continue
        model, stem, cited, att_name, sources = m.groups()
        key = (model, stem)
        if key not in cache:
            text = (R / f"full_{model}" / "drafts" / f"{stem}.txt").read_text()
            names = set()
            for d in cite_details(text):
                if d["volume"] and d["reporter"] and d["page"]:
                    h = index.lookup(d["volume"], d["reporter"], d["page"])
                    if h and h.get("case_name"):
                        names |= name_tokens(h["case_name"])
            cache[key] = names
        src_tokens = set()
        for s in re.findall(r"'([^']+)'", sources):
            src_tokens |= name_tokens(s)
        per[model]["misattributed"] += 1
        if src_tokens & cache[key]:
            per[model]["true_source_cited_in_draft"] += 1
    for m, c in per.items():
        out[m] = dict(c)
        out[m]["share"] = round(c["true_source_cited_in_draft"] / c["misattributed"], 3)
    tot = sum(c["misattributed"] for c in per.values())
    hit = sum(c["true_source_cited_in_draft"] for c in per.values())
    out["pooled"] = {"misattributed": tot, "true_source_cited_in_draft": hit,
                     "share": round(hit / tot, 3) if tot else None}
    return out


def main():
    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    out = {"era": era_check(checker, store, index), "attribution": attribution_check(index)}
    (R / "era_attribution_check.json").write_text(json.dumps(out, indent=1))
    print("era pooled:", out["era"]["pooled"])
    for m in MODELS:
        print(m, out["era"][m].get("pre1970_strict"), out["era"][m].get("post1970_strict"))
    print("attribution:", out["attribution"]["pooled"], {m: v.get("share") for m, v in out["attribution"].items()})


if __name__ == "__main__":
    main()
