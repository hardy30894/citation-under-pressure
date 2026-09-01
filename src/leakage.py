#!/usr/bin/env python3
"""Self-opinion leakage analysis: how often does a draft 'quote' language
whose true source (per corpus provenance) is the argued case's OWN
opinion, laundered as precedent? Per model, condition, and decade."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path("/Users/hardy30894/Documents/NYU_Research/us_courts_gated_evolution")
sys.path.insert(0, str(HERE / "src"))

import quotecheck2 as q2  # noqa: E402  (for NAME_STOP)

LINE_RE = re.compile(
    r"- \*\*(\w+)\*\* \| (\w+) (\S+)_([a-z]+) \| cited (.*?) \| "
    r"true source: (\[.*?\]|—) \| “(.*)”"
)


def toks(s):
    return {
        t.lower() for t in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", s or "")
        if t.lower() not in q2.NAME_STOP
    }


def main():
    # matter -> own-party tokens from the packets
    own = {}
    manifest = json.loads((GE / "data/manifests/final_sets.json").read_text())
    for e in manifest["dev"] + manifest["stream"]:
        try:
            p = json.loads((GE / "data/packets" / e["packet"]).read_text())
        except Exception:
            continue
        parties = p.get("parties") or {}
        own[e["id"]] = toks(parties.get("petitioner", "")) | toks(
            parties.get("respondent", ""))

    counts = Counter()
    examples = []
    for line in open(HERE / "results/provenance_report.md"):
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        cls, model, matter, cond, cited, sources, quote = m.groups()
        if cls not in ("misattributed", "generic_phrase_match"):
            continue
        own_toks = own.get(matter, set())
        if not own_toks or sources == "—":
            continue
        src_toks = toks(sources)
        if own_toks & src_toks:
            counts[(model, cond)] += 1
            counts[(model, "TOTAL")] += 1
            decade = matter[:3] + "0s"
            counts[(model, decade)] += 1
            if len(examples) < 25:
                examples.append(
                    f"{model} {matter}_{cond} cited {cited[:50]} | "
                    f"src {sources[:70]} | “{quote[:80]}”"
                )

    out = {
        "counts": {f"{k[0]}:{k[1]}": v for k, v in sorted(counts.items())},
        "examples": examples,
        "note": ("Leak = provenance true-source caption shares a "
                 "distinctive party token with the argued case's own "
                 "parties. Token overlap is a screen, not proof: verify "
                 "flagged examples by reading before quoting a rate."),
    }
    (HERE / "results/leakage.json").write_text(json.dumps(out, indent=1))
    for k, v in sorted(counts.items()):
        if k[1] == "TOTAL":
            print(f"{k[0]:10s} self-opinion leak candidates: {v}")
    print(f"-> results/leakage.json ({len(examples)} examples saved)")


if __name__ == "__main__":
    main()
