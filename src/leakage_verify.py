#!/usr/bin/env python3
"""Verification pass for self-opinion leakage candidates.

The token screen (leakage.py) flags quotes whose corpus true-source is
the argued case itself. But the argued case's opinion CONTAINS the
record: statute text, the parties' own policies, lower-court language,
all of which also sit in the PACKET the model was shown. Quoting those
and mis-citing them to a precedent is record-misattribution, not
memorization. A genuine leak must be ABSENT from the packet materials
while present in the argued case's own (excluded, later-decided)
opinion. This pass applies that filter to every candidate.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path(__file__).resolve().parents[1]  # vendored checker, runtime, sim, packets
sys.path.insert(0, str(HERE / "src"))
sys.path.insert(0, str(GE / "src"))

from checker.quote_checker import normalize  # noqa: E402
import quotecheck2 as q2  # noqa: E402

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
    manifest = json.loads((GE / "data/manifests/final_sets.json").read_text())
    packets = {}
    for e in manifest["dev"] + manifest["stream"]:
        packets[e["id"]] = e["packet"]

    own_tokens, packet_norm = {}, {}

    def load(matter):
        if matter in own_tokens:
            return
        p = json.loads((GE / "data/packets" / packets[matter]).read_text())
        parties = p.get("parties") or {}
        own_tokens[matter] = toks(parties.get("petitioner", "")) | toks(
            parties.get("respondent", ""))
        blob = " ".join([
            p.get("question") or "", p.get("facts") or "",
            (p.get("lower_court_opinion") or {}).get("raw_text") or "",
        ])
        packet_norm[matter] = normalize(blob)

    verified, record_misattr, indeterminate = [], [], []
    for line in open(HERE / "results/provenance_report.md"):
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        cls, model, matter, cond, cited, sources, quote = m.groups()
        if cls not in ("misattributed", "generic_phrase_match") or \
                sources == "—" or matter not in packets:
            continue
        load(matter)
        if not (own_tokens[matter] & toks(sources)):
            continue
        frag = normalize(quote)
        entry = {
            "model": model, "matter": matter, "condition": cond,
            "cited": cited[:70], "quote": quote[:110],
            "distinctive": len(frag.split()) >= 6,
        }
        if len(frag) < 20:
            indeterminate.append(entry)
        elif frag[:120] in packet_norm[matter]:
            record_misattr.append(entry)
        else:
            verified.append(entry)

    out = {
        "verified_leaks": verified,
        "record_misattribution": record_misattr,
        "indeterminate_short": indeterminate,
        "note": ("verified_leaks = quote found in the argued case's own "
                 "opinion (provenance) AND absent from every packet field "
                 "the model saw. distinctive=False entries are short "
                 "phrases; treat with caution."),
    }
    (HERE / "results/leakage_verified.json").write_text(
        json.dumps(out, indent=1))
    print(f"verified leaks: {len(verified)} "
          f"(distinctive: {sum(e['distinctive'] for e in verified)})")
    print(f"record misattribution (in packet): {len(record_misattr)}")
    print(f"indeterminate (too short): {len(indeterminate)}")
    for e in verified:
        if e["distinctive"]:
            print(f"  LEAK {e['model']} {e['matter']}_{e['condition']} "
                  f"cited {e['cited'][:40]} | “{e['quote'][:70]}”")


if __name__ == "__main__":
    main()
