#!/usr/bin/env python3
"""Definitive re-score of the full factorial drafts on the local-first
text chain (checker.db tiers -> legacy cache -> CAP static volumes -> LII;
no CourtListener). Produces the paper's H1 quote tables, replacing the
inline scoring that ran quota-starved during the drafting night.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402 (loads .env)
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB, cite_details, temporal_violations  # noqa: E402
import quotecheck2 as q2  # noqa: E402

MODELS = ("qwen30b", "deepseek", "gpt54mini", "sonnet")


def main():
    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None,
                                            fetch_budget=0))
    out = {}
    for model in MODELS:
        drafts = HERE / "results" / f"full_{model}" / "drafts"
        agg = {}
        for p in sorted(drafts.glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            text = p.read_text()
            recs, rates = checker.check_text(text)
            qres = q2.check_draft(text, recs, eyecite_pass(text), store)
            a = agg.setdefault(cond, {
                "drafts": 0, "exists": 0, "not_found": 0, "unresolvable": 0,
                "acc": 0, "near": 0, "inacc": 0, "unver": 0, "unpaired": 0,
                "viol": 0, "tchecked": 0, "rows": [],
            })
            a["drafts"] += 1
            for r in recs:
                key = {"exists": "exists", "not_found": "not_found",
                       "unresolvable": "unresolvable"}[r["verdict"]]
                a[key] += 1
            for r in qres:
                v = r["verdict"]
                if v == "accurate":
                    a["acc"] += 1
                elif v == "near_miss":
                    a["near"] += 1
                elif v == "inaccurate":
                    a["inacc"] += 1
                elif v == "unverifiable":
                    a["unver"] += 1
                elif v == "unpaired":
                    a["unpaired"] += 1
            if cond in ("temporal", "combo"):
                tv = temporal_violations(cite_details(text), index)
                a["viol"] += tv["violated"]
                a["tchecked"] += tv["checked"]
            a["rows"].append({
                "matter": matter,
                "n_cites": rates["n_citations"],
                "exist": rates["existence_rate"],
                "strict": q2.strict_rate(qres),
            })
        for c, a in agg.items():
            scored = a["acc"] + a["near"] + a["inacc"]
            a["existence_rate"] = (
                round(a["exists"] / (a["exists"] + a["not_found"]), 4)
                if a["exists"] + a["not_found"] else None
            )
            a["strict_rate"] = (
                round(a["acc"] / scored, 4) if scored else None
            )
        out[model] = agg
        print(f"{model} done", flush=True)

    (HERE / "results" / "rescore_full.json").write_text(
        json.dumps(out, indent=1)
    )
    for model in MODELS:
        print(f"\n{model}")
        for c in ("baseline", "quota", "temporal", "stakes", "combo"):
            a = out[model].get(c)
            if not a:
                continue
            print(
                f"  {c:9s} exist={a['existence_rate']} "
                f"strict={a['strict_rate']} "
                f"(a{a['acc']}/n{a['near']}/i{a['inacc']}/u{a['unver']}) "
                f"viol={a['viol']}/{a['tchecked']}"
            )


if __name__ == "__main__":
    main()
