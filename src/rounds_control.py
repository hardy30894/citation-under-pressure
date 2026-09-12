#!/usr/bin/env python3
"""The precision series against the number of revision rounds each arm ran.

The loop stops on a clean draft, so an arm whose feedback is mostly true
converges early while an arm whose feedback is mostly false runs to the
cap: the model edits correct items while its real failures stand, and
the draft goes clean only when those are removed too. Correct quotations
removed therefore rise both as precision falls and as rounds executed
rise, and the raw series cannot separate them.

This reports, per model and arm, the mean rounds executed, the count of
accurate round-0 quotations removed, and the removal per episode-round,
which holds the number of revision opportunities fixed. It also gives
the removal restricted to the first round, where every arm has had
exactly one opportunity and the confound cannot operate. Writes
results/rounds_control.json.
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
from checker.quote_checker import OpinionTextStore, normalize  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
from pilot import DB  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from loop_transitions import scored_quotes, classify  # noqa: E402

ARMS = ("true", "threequarter", "half", "quarter", "scrambled", "none", "passage")
ALPHA = ("qwen30b", "mistralsmall", "deepseek", "grok43", "sonnet", "llama4mav", "gpt54mini")


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    loops = json.loads((R / "rescore_loops.json").read_text())
    out = {"cells": {}, "pooled": {}}
    for model in ALPHA:
        drafts = R / f"loop_{model}" / "drafts"
        full = R / f"full_{model}" / "drafts"
        for arm in ARMS:
            eps = [e for e in loops[model] if e["arm"] == arm]
            if not eps:
                continue
            c = Counter()
            for ep in eps:
                matter = ep["matter"]
                revs = sorted(drafts.glob(f"{matter}_{arm}_r*.txt"),
                              key=lambda p: int(re.search(r"_r(\d+)", p.stem).group(1)))
                r0 = (full / f"{matter}_combo.txt").read_text()
                q0s = scored_quotes(r0, checker, store)
                acc0 = [q for q in q0s if q["verdict"] == "accurate"]
                c["episodes"] += 1
                c["rounds"] += ep["rounds"]
                c["acc_r0"] += len(acc0)
                # removal after one round, where every arm has had one chance
                if revs:
                    first = revs[0].read_text()
                    q1 = scored_quotes(first, checker, store)
                    used = set()
                    fates = [classify(q, q1, normalize(first), used) for q in q0s]
                    for q, (fate, v1) in zip(q0s, fates):
                        if q["verdict"] == "accurate" and (
                                fate in ("dequoted", "deleted") or v1 == "flagged"):
                            c["removed_r1"] += 1
                # removal by the final draft, the paper's headline count
                final = revs[-1].read_text() if revs else r0
                qf = scored_quotes(final, checker, store)
                used = set()
                fates = [classify(q, qf, normalize(final), used) for q in q0s]
                for q, (fate, v1) in zip(q0s, fates):
                    if q["verdict"] == "accurate" and (
                            fate in ("dequoted", "deleted") or v1 == "flagged"):
                        c["removed_final"] += 1
            cell = {
                "episodes": c["episodes"], "mean_rounds": round(c["rounds"] / c["episodes"], 2),
                "acc_r0": c["acc_r0"], "removed_final": c["removed_final"],
                "removed_r1": c["removed_r1"],
                "removed_per_round": round(c["removed_final"] / c["rounds"], 3) if c["rounds"] else None,
                "removed_r1_share": round(c["removed_r1"] / c["acc_r0"], 3) if c["acc_r0"] else None,
            }
            out["cells"][f"{model}:{arm}"] = cell
        print(model, {a: out["cells"].get(f"{model}:{a}", {}).get("removed_per_round") for a in ARMS}, flush=True)
    for arm in ARMS:
        cs = [v for k, v in out["cells"].items() if k.endswith(":" + arm)]
        if not cs:
            continue
        rounds = sum(c["mean_rounds"] * c["episodes"] for c in cs)
        out["pooled"][arm] = {
            "mean_rounds": round(rounds / sum(c["episodes"] for c in cs), 2),
            "acc_r0": sum(c["acc_r0"] for c in cs),
            "removed_final": sum(c["removed_final"] for c in cs),
            "removed_r1": sum(c["removed_r1"] for c in cs),
            "removed_per_round": round(sum(c["removed_final"] for c in cs) / rounds, 3),
            "removed_r1_share": round(sum(c["removed_r1"] for c in cs) / sum(c["acc_r0"] for c in cs), 3),
        }
    # where revision with no feedback falls on the precision axis: the
    # nominal pi at which a verifier does as much damage as no verifier,
    # by linear interpolation between the bracketing arms, and the same
    # point on the realised scale, since a true line is right only as
    # often as the checker is
    NOMINAL = {"true": 1.0, "threequarter": 0.75, "half": 0.5, "quarter": 0.25, "scrambled": 0.0}
    out["crossing"] = {}
    for basis in ("removed_per_round", "removed_r1_share"):
        pts = sorted(((NOMINAL[a], out["pooled"][a][basis]) for a in NOMINAL if a in out["pooled"]),
                     key=lambda t: -t[0])
        target = out["pooled"]["none"][basis]
        cross = None
        for (p1, v1), (p2, v2) in zip(pts, pts[1:]):
            if (v1 - target) * (v2 - target) <= 0 and v1 != v2:
                cross = p1 + (target - v1) * (p2 - p1) / (v2 - v1)
                break
        out["crossing"][basis] = None if cross is None else round(cross, 3)
    cs = [v for v in out["crossing"].values() if v is not None]
    if cs:
        out["crossing"]["nominal_range"] = [round(min(cs), 2), round(max(cs), 2)]
        # Realised precision of a true line is one minus the share of the
        # checker's inaccurate verdicts that are its own error, and the two
        # independent readings of that sample disagree, so the realised
        # crossing is an interval over both readings rather than a point.
        two = json.loads((R / "audit_two_raters.json").read_text())
        shares = [two["rater1_share"], two["rater2_share"]]
        rp_low, rp_high = 1 - max(shares), 1 - min(shares)
        out["crossing"]["realised_range"] = [round(min(cs) * rp_low, 2), round(max(cs) * rp_high, 2)]
        out["crossing"]["realised_factor_range"] = [round(rp_low, 3), round(rp_high, 3)]
    (R / "rounds_control.json").write_text(json.dumps(out, indent=1))
    for arm in ARMS:
        if arm in out["pooled"]:
            print(arm, out["pooled"][arm])


if __name__ == "__main__":
    main()
