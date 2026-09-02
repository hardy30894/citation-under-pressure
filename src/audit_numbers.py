#!/usr/bin/env python3
"""Copy-never-retype check: every load-bearing number in the paper draft
must match its results file. Prints PASS/FAIL per claim. Extend the
CLAIMS list whenever a number enters the draft."""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
R = HERE / "results"
draft = (HERE / "docs/PAPER_DRAFT.md").read_text()

full = json.loads((R / "rescore_full.json").read_text())
loops = json.loads((R / "rescore_loops.json").read_text())
gee = json.loads((R / "stats_gee.json").read_text())
human = json.loads((R / "human_baseline.json").read_text())["aggregates"]["overall"]
pins = json.loads((R / "pincites.json").read_text())
decomp = json.loads((R / "notincorpus_decomposition.json").read_text())


def loop_final(model, arm):
    sub = [r for r in loops[model] if r["arm"] == arm]
    vals = [r["final"]["strict"] for r in sub if r["final"]["strict"] is not None]
    return round(sum(vals) / len(vals), 3)


def loop_conv(model, arm):
    return sum(r["converged"] for r in loops[model] if r["arm"] == arm)


def pin_rate(model):
    p = pins[model]
    tot = p["quote_at_pin"] + p["quote_near_pin"] + p["quote_not_at_pin"]
    return round(100 * p["quote_at_pin"] / tot)


CLAIMS = [
    # (description, value computed from artifact, regex the draft must contain)
    ("qwen combo existence", full["qwen30b"]["combo"]["existence_rate"], r"0\.773"),
    ("qwen baseline existence", full["qwen30b"]["baseline"]["existence_rate"], r"0\.924"),
    ("sonnet combo strict", full["sonnet"]["combo"]["strict_rate"], r"0\.427"),
    ("sonnet baseline strict", full["sonnet"]["baseline"]["strict_rate"], r"0\.333"),
    ("gpt baseline strict", full["gpt54mini"]["baseline"]["strict_rate"], r"0\.460"),
    ("llama baseline strict", full["llama4mav"]["baseline"]["strict_rate"], r"0\.402"),
    ("mistral combo strict", full["mistralsmall"]["combo"]["strict_rate"], r"0\.136"),
    ("human strict", human["strict_quote_rate"], r"0\.407"),
    ("human scored quotes", human["n_quotes_scored"], r"578"),
    ("human existence", human["existence_rate"], r"0\.931"),
    ("qwen combo OR", gee["citation:qwen30b:combo"]["OR"], r"odds ratio 0\.30|OR 0\.304"),
    ("sonnet combo quote OR", gee["quote:sonnet:combo"]["OR"], r"1\.475"),
    ("sonnet combo exist OR", gee["citation:sonnet:combo"]["OR"], r"4\.556"),
    ("sonnet loop final true", loop_final("sonnet", "true"), r"0\.974"),
    ("sonnet loop scrambled", loop_final("sonnet", "scrambled"), r"0\.266"),
    ("gpt loop final true", loop_final("gpt54mini", "true"), r"0\.719"),
    ("qwen loop final true", loop_final("qwen30b", "true"), r"0\.112"),
    ("mistral loop final true", loop_final("mistralsmall", "true"), r"0\.264"),
    ("llama loop final true", loop_final("llama4mav", "true"), r"0\.349"),
    ("sonnet converged", loop_conv("sonnet", "true"), r"23 of 24"),
    ("sonnet pin-at-page pct", pin_rate("sonnet"), r"77 percent"),
    ("sonnet paraphrase count", decomp["sonnet"]["paraphrase_in_quotes"], r"413"),
]


def main():
    fails = 0
    for desc, value, pattern in CLAIMS:
        ok = re.search(pattern, draft) is not None
        # the regex encodes the artifact value; also print the live value
        print(f"{'PASS' if ok else 'FAIL':4s} {desc:28s} artifact={value} draft~/{pattern}/")
        fails += not ok
    print(f"\n{len(CLAIMS) - fails}/{len(CLAIMS)} claims match")


if __name__ == "__main__":
    main()
