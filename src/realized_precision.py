#!/usr/bin/env python3
"""The precision the loop's feedback actually had.

The revision loop ran before the attribution rule was corrected, so the
flags the models received were produced by the original quotecheck2
(src/legacy/quotecheck2_original.py). The request cache keeps replies,
not prompts, but the feedback is deterministic given the draft, the arm,
and the episode seed, so this script replays it: for every episode and
round it rescores the draft the model was shown with the original rule,
rebuilds the feedback lines exactly as loop_arm.py did (same templates,
same per-episode random stream for the false and mixed arms), and then
adjudicates each line under the corrected rule on the same draft. A
citation line is true when the citation still does not resolve. A
quotation line is true when the corrected rule scores that quotation
inaccurate or near miss (true but misattributed when it does so against a
different case than the flag named), false when it scores it accurate,
and unverifiable when the corrected rule leaves it unpaired. Realized
precision is true lines, misattributed or not, over all lines,
unverifiable lines counted as false, and is reported per model and arm,
for round-1 feedback and over all rounds. Writes
results/realized_precision.json."""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB, pick_matters  # noqa: E402
import quotecheck2 as q2new  # noqa: E402
from legacy import quotecheck2_original as q2old  # noqa: E402
import loop_arm  # noqa: E402

ARMS = ("true", "scrambled", "none", "half", "quarter", "threequarter", "passage")


def flags_old(text, checker, store, arm, rng):
    recs, _ = checker.check_text(text)
    qres = q2old.check_draft(text, recs, eyecite_pass(text), store)
    lines = loop_arm.feedback_lines(recs, qres, arm, rng, store)
    true_left = loop_arm.feedback_lines(recs, qres, "true", rng)
    return recs, qres, lines, bool(true_left)


def adjudicate(lines, text, recs_new, qres_new):
    """Classify each feedback line under the corrected rule."""
    nf = {r["citation"] for r in recs_new if r["verdict"] == "not_found"}
    out = Counter()
    for ln in lines:
        m = re.match(r"The citation (.+?) does not correspond", ln)
        if m:
            out["true" if m.group(1) in nf else "false"] += 1
            continue
        m = re.match(r"The quoted passage beginning “(.*?)…” does not appear verbatim in the opinion of (.+?)\. (?:Quote|The closest)", ln)
        if not m:
            continue
        prefix, cite = m.group(1), m.group(2)
        hit = [q for q in qres_new if q["quote"].startswith(prefix[:40])]
        if not hit or hit[0]["verdict"] not in ("accurate", "near_miss", "inaccurate"):
            out["unverifiable"] += 1  # the corrected rule leaves the quotation unpaired or unscored
        elif hit[0]["verdict"] == "accurate":
            out["false"] += 1  # a correct quotation was flagged
        elif hit[0]["citation"] == cite:
            out["true"] += 1
        else:
            out["true_misattributed"] += 1  # not verbatim, but the flag named the wrong case
    return out


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    out = {}
    for prefix in ("loop_v1", "gloop_v1"):
        for d in sorted((HERE / "results").glob(f"{prefix}_*")):
            if not (d / "run/events.jsonl").exists():
                continue
            model = d.name[len(prefix) + 1:]
            src = HERE / "results" / (f"full_{model}" if prefix == "loop_v1" else f"rag_{model}") / "drafts"
            eps = {}
            for l in open(d / "run/events.jsonl"):
                try:
                    e = json.loads(l)
                    if e["type"] == "episode_done":
                        eps[e["step"]] = e["data"]
                except Exception:
                    continue
            per = {}
            for ep in eps.values():
                matter, arm = ep["matter"], ep["arm"]
                rng = random.Random(f"loop:{matter}:{arm}:20260831")
                revs = sorted((d / "drafts").glob(f"{matter}_{arm}_r*.txt"),
                              key=lambda p: int(re.search(r"_r(\d+)", p.stem).group(1)))
                drafts = [src / f"{matter}_combo.txt"] + revs
                for rnd, p in enumerate(drafts):
                    text = p.read_text()
                    recs_o, qres_o, lines, left = flags_old(text, checker, store, arm, rng)
                    if not left or not lines or lines == ["__NONE__"]:
                        break  # converged, or a no-feedback round
                    if rnd == loop_arm.MAX_ROUNDS:
                        break
                    recs_n, _ = checker.check_text(text)
                    qres_n = q2new.check_draft(text, recs_n, eyecite_pass(text), store)
                    c = adjudicate(lines, text, recs_n, qres_n)
                    key = per.setdefault(arm, {"r1": Counter(), "all": Counter()})
                    key["all"].update(c)
                    if rnd == 0:
                        key["r1"].update(c)
            res = {}
            for arm, v in per.items():
                res[arm] = {}
                for k in ("r1", "all"):
                    n = sum(v[k].values()); t = v[k]["true"] + v[k]["true_misattributed"]
                    res[arm][k] = {"lines": n, "true": v[k]["true"], "true_misattributed": v[k]["true_misattributed"],
                                   "false": v[k]["false"], "unverifiable": v[k]["unverifiable"],
                                   "precision": round(t / n, 3) if n else None,
                                   "precision_right_case": round(v[k]["true"] / n, 3) if n else None}
            out[f"{prefix}:{model}"] = res
            print(prefix, model, {a: r["r1"]["precision"] for a, r in res.items()}, flush=True)
    (HERE / "results" / "realized_precision.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
