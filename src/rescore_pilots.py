#!/usr/bin/env python3
"""Re-score both pilots' cached drafts with the hardened quote instrument.

Zero API cost for LLMs; opinion texts come from the local store with a small
CourtListener trickle for newly attributed cases. Prints old-vs-new strict
rates per model x condition and writes the surviving inaccurate residue for
manual read.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path("/Users/hardy30894/Documents/NYU_Research/us_courts_gated_evolution")
sys.path.insert(0, str(GE / "src"))
sys.path.insert(0, str(HERE / "src"))

import os
env = HERE / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from runtime.llm_client import load_env_key  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa: E402
from checker.quote_checker import OpinionTextStore  # noqa: E402
from eyecite import get_citations  # noqa: E402
from eyecite.models import FullCaseCitation  # noqa: E402
import quotecheck2 as q2  # noqa: E402

DB = GE / "data/courtlistener/checker.db"

PILOTS = {
    "qwen30b": HERE / "results/pilot/drafts",
    "sonnet": HERE / "results/pilot_sonnet/drafts",
}


def eyecite_pass(text):
    out = []
    for cite in get_citations(text):
        if not isinstance(cite, FullCaseCitation):
            continue
        g = cite.groups or {}
        out.append(
            {
                "citation": cite.corrected_citation(),
                "start": cite.span()[0],
                "volume": g.get("volume"),
                "reporter": g.get("reporter"),
                "page": g.get("page"),
                "plaintiff": getattr(cite.metadata, "plaintiff", None),
                "defendant": getattr(cite.metadata, "defendant", None),
            }
        )
    return out


def main():
    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = OpinionTextStore(
        DB, cl_token=load_env_key("COURTLISTENER_TOKEN"), fetch_budget=60
    )

    residue_lines = ["# Surviving inaccurate quotes (hardened instrument)\n"]
    summary = {}
    for model, drafts_dir in PILOTS.items():
        agg = {}
        for p in sorted(drafts_dir.glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            text = p.read_text()
            recs, _ = checker.check_text(text)
            res = q2.check_draft(text, recs, eyecite_pass(text), store)
            a = agg.setdefault(
                cond, {"n": 0, "acc": 0, "near": 0, "inacc": 0,
                       "unver": 0, "unpaired": 0, "named": 0}
            )
            for r in res:
                a["n"] += 1
                a["named"] += r["attribution"] == "named"
                if r["verdict"] == "accurate":
                    a["acc"] += 1
                elif r["verdict"] == "near_miss":
                    a["near"] += 1
                elif r["verdict"] == "inaccurate":
                    a["inacc"] += 1
                    residue_lines.append(
                        f"- {model} {p.stem} | {r['citation']} "
                        f"({r['attribution']}, cov={r['coverage']}): "
                        f"“{r['quote']}”"
                    )
                elif r["verdict"] == "unverifiable":
                    a["unver"] += 1
                elif r["verdict"] == "unpaired":
                    a["unpaired"] += 1
        for cond, a in agg.items():
            scored = a["acc"] + a["near"] + a["inacc"]
            a["strict"] = round(a["acc"] / scored, 3) if scored else None
        summary[model] = agg

    out = HERE / "results/rescore_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    (HERE / "results/rescore_residue.md").write_text(
        "\n".join(residue_lines)
    )
    for model, agg in summary.items():
        print(f"\n{model}")
        for cond in ("baseline", "quota", "temporal", "stakes", "combo"):
            if cond not in agg:
                continue
            a = agg[cond]
            print(
                f"  {cond:9s} quotes={a['n']:3d} strict={a['strict']} "
                f"acc={a['acc']} near={a['near']} inacc={a['inacc']} "
                f"unver={a['unver']} unpaired={a['unpaired']} "
                f"named={a['named']}"
            )


if __name__ == "__main__":
    main()
