#!/usr/bin/env python3
"""Earlier-source screen for the 9 verified leak candidates: list EVERY
corpus case containing the quoted language. If an earlier case carries
it (the argued opinion was quoting precedent), the candidate is doctrine
misattribution, not memorization leakage. Corpus coverage caveat applies
and is printed with the result."""

import json
import sys
from bisect import bisect_right
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from provenance import load_corpus  # noqa: E402
from checker.quote_checker import normalize  # noqa: E402


def all_hits(big, bounds, captions, frag, cap=10):
    hits, start = [], 0
    while len(hits) < cap:
        i = big.find(frag, start)
        if i < 0:
            break
        hits.append(captions[bisect_right(bounds, i) - 1])
        start = i + 1
    return hits


def main():
    data = json.loads(
        (HERE / "results/leakage_verified.json").read_text())
    print("loading corpus...", flush=True)
    big, bounds, captions = load_corpus()
    out = []
    for e in data["verified_leaks"]:
        frag = normalize(e["quote"])
        words = frag.split()
        if len(words) > 12:
            mid = len(words) // 2
            frag = " ".join(words[mid - 6: mid + 6])
        hits = all_hits(big, bounds, captions, frag)
        e2 = dict(e)
        e2["all_corpus_hits"] = hits
        e2["sole_source_is_argued_case"] = len(set(hits)) == 1
        out.append(e2)
        print(f"{e['model']} {e['matter']}_{e['condition']} | "
              f"hits={len(hits)} unique={len(set(hits))} | "
              f"“{e['quote'][:60]}”")
        for h in dict.fromkeys(hits):
            print(f"    <- {h[:80]}")
    (HERE / "results/leak_screen.json").write_text(
        json.dumps(out, indent=1))
    sole = sum(1 for e in out if e["sole_source_is_argued_case"])
    print(f"\nsole-source (argued case only, within corpus coverage): "
          f"{sole}/{len(out)}")


if __name__ == "__main__":
    main()
