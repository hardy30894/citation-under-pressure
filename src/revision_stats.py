#!/usr/bin/env python3
"""Analyses demanded by the hostile review, all from existing artifacts.

1. Holm correction over all GEE contrasts per model; raw event counts.
2. Memorization alternative for the Sonnet temporal/combo result: citation
   decision-year distribution and canonical-case share by condition, and
   strict quotation accuracy on canonical vs other cases.
3. Human baseline comparability: unverifiable and near-miss shares for
   humans and per model x condition; U.S.-Reports-only existence for
   humans; lenient rate (near-miss counted correct) for everyone.
4. Loop held-out channels: per-round quotation and citation counts, so
   deletion can be separated from repair.
5. Pressured-draft count (excludes baseline).
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
R = HERE / "results"
import sys
sys.path.insert(0, str(HERE / "src"))
from pilot import cite_details, DB  # noqa: E402
from checker.citation_checker import SqliteIndex  # noqa: E402

out = {}

# ---- 1. Holm + raw counts -------------------------------------------------
gee = json.loads((R / "stats_gee.json").read_text())
by_model = defaultdict(list)
for k, v in gee.items():
    kind, model, cond = k.split(":")
    by_model[model].append((k, v["p"]))
holm = {}
for model, tests in by_model.items():
    tests.sort(key=lambda t: t[1])
    m = len(tests)
    for i, (k, p) in enumerate(tests):
        holm[k] = {"p": p, "holm_p": min(1.0, p * (m - i)), "n_tests": m}
sig_after = {k: v for k, v in holm.items() if v["holm_p"] < 0.05}
out["holm"] = holm
out["significant_after_holm"] = sorted(sig_after)

records = [json.loads(l) for l in open(R / "records.jsonl")]
counts = Counter()
for r in records:
    counts[(r["model"], r["condition"], r["kind"], r["verdict"])] += 1
raw = {}
for (m, c, k, v), n in counts.items():
    raw.setdefault(f"{m}:{c}:{k}", {})[v] = n
out["raw_counts"] = raw

# unverifiable share per cell and lenient quote rate
cells = {}
for key, d in raw.items():
    m, c, k = key.split(":")
    if k == "citation":
        tot = sum(d.values())
        cells.setdefault(f"{m}:{c}", {})["cite_unverifiable_share"] = round(
            d.get("unresolvable", 0) / tot, 4) if tot else None
    else:
        acc, near, inac = d.get("accurate", 0), d.get("near_miss", 0), d.get("inaccurate", 0)
        unv = d.get("unverifiable", 0)
        scored = acc + near + inac
        cells.setdefault(f"{m}:{c}", {}).update({
            "strict": round(acc / scored, 4) if scored else None,
            "lenient": round((acc + near) / scored, 4) if scored else None,
            "near_miss_share": round(near / scored, 4) if scored else None,
            "quote_unverifiable": unv, "quotes_scored": scored,
        })
out["cells"] = cells

# ---- 2. Memorization alternative (Sonnet, also all models) ----------------
index = SqliteIndex(DB)
year_stats = {}
cite_counter = Counter()
per_draft_cites = {}
for full in sorted(R.glob("full_*")):
    model = full.name.replace("full_", "")
    if len(list((full / "drafts").glob("*.txt"))) < 240:
        continue
    for p in sorted((full / "drafts").glob("*.txt")):
        matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
        dets = cite_details(p.read_text())
        keys = []
        for d in dets:
            if d["volume"] and d["reporter"] and d["page"]:
                keys.append((d["volume"], d["reporter"], d["page"]))
        per_draft_cites[(model, cond, matter)] = keys
        cite_counter.update(keys)
canonical = {k for k, _ in cite_counter.most_common(50)}
for (model, cond, matter), keys in per_draft_cites.items():
    s = year_stats.setdefault(f"{model}:{cond}", {"n": 0, "canonical": 0, "years": []})
    for k in keys:
        s["n"] += 1
        s["canonical"] += k in canonical
        hit = index.lookup(*k)
        if hit and hit.get("date_filed"):
            s["years"].append(int(hit["date_filed"][:4]))
mem = {}
for key, s in year_stats.items():
    ys = sorted(s["years"])
    mem[key] = {
        "n_cites": s["n"],
        "canonical_share": round(s["canonical"] / s["n"], 3) if s["n"] else None,
        "median_year": ys[len(ys) // 2] if ys else None,
    }
out["memorization"] = mem
out["canonical_top50"] = [f"{v} {r} {p}" for (v, r, p) in sorted(canonical)]

# ---- 3. Human baseline cuts ------------------------------------------------
hb = json.loads((R / "human_baseline.json").read_text())
out["human_overall"] = hb["aggregates"]["overall"]
out["human_resolved_only"] = hb["aggregates"].get("oracle_resolved_only")
hq = hb["aggregates"]["overall"]["quote_verdicts"]
acc, near, inac = hq.get("accurate", 0), hq.get("near_miss", 0), hq.get("inaccurate", 0)
out["human_lenient"] = round((acc + near) / (acc + near + inac), 4)
out["human_near_miss_share"] = round(near / (acc + near + inac), 4)

# ---- 4. Loop held-out counts -----------------------------------------------
loops = json.loads((R / "rescore_loops.json").read_text())


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


loop_counts = {}
for model, rows in loops.items():
    for arm in ("true", "scrambled", "none", "half"):
        sub = [r for r in rows if r["arm"] == arm]
        if not sub:
            continue
        loop_counts[f"{model}:{arm}"] = {
            "cites_r0": sum(r["r0"]["n_cites"] for r in sub),
            "cites_final": sum(r["final"]["n_cites"] for r in sub),
            "quotes_scored_r0": sum(r["r0"]["n_quotes_scored"] for r in sub),
            "quotes_scored_final": sum(r["final"]["n_quotes_scored"] for r in sub),
            "accurate_r0": sum(r["r0"]["acc"] for r in sub),
            "accurate_final": sum(r["final"]["acc"] for r in sub),
            "exist_r0": round(_mean([r["r0"]["exist"] for r in sub]), 3),
            "exist_final": round(_mean([r["final"]["exist"] for r in sub]), 3),
        }
out["loop_counts"] = loop_counts

# ---- 4b. Loop inference: paired by matter, true vs scrambled and true vs
# none, on the final strict rate and on the change in scored quotations.
from scipy.stats import wilcoxon  # noqa: E402
import random  # noqa: E402
loop_tests = {}
for model, rows in loops.items():
    by = {}
    for r in rows:
        by.setdefault(r["matter"], {})[r["arm"]] = r
    for other in ("scrambled", "none", "half"):
        pairs = [(v["true"], v[other]) for v in by.values()
                 if "true" in v and other in v
                 and v["true"]["final"]["strict"] is not None
                 and v[other]["final"]["strict"] is not None]
        if len(pairs) < 6:
            continue
        d = [a["final"]["strict"] - b["final"]["strict"] for a, b in pairs]
        rng = random.Random(0)
        boots = sorted(
            sum(rng.choice(d) for _ in d) / len(d) for _ in range(2000))
        try:
            p = float(wilcoxon(d).pvalue) if any(d) else 1.0
        except ValueError:
            p = 1.0
        loop_tests[f"{model}:true_vs_{other}"] = {
            "n_pairs": len(pairs), "mean_diff": round(sum(d) / len(d), 3),
            "ci_low": round(boots[50], 3), "ci_high": round(boots[1949], 3),
            "wilcoxon_p": round(p, 4),
        }
out["loop_tests"] = loop_tests

# ---- 5. counts ---------------------------------------------------------------
n_models = len([p for p in R.glob("full_*") if len(list((p / "drafts").glob("*.txt"))) >= 240])
out["n_pressured_drafts"] = 48 * 4 * n_models
out["n_all_drafts"] = 48 * 5 * n_models
cit = [r for r in records if r["kind"] == "citation"]
out["n_citation_records"] = len(cit)
out["unverifiable_share_pct"] = round(
    100 * sum(r["verdict"] == "unresolvable" for r in cit) / len(cit), 2)
full = json.loads((R / "rescore_full.json").read_text())
s = full["sonnet"]
out["sonnet_temporal_checked"] = s["temporal"]["tchecked"] + s["combo"]["tchecked"]
out["sonnet_temporal_viol"] = s["temporal"]["viol"] + s["combo"]["viol"]
gl = R / "full_glm47flash" / "drafts"
have = Counter(p.stem.rsplit("_", 1)[1] for p in gl.glob("*.txt"))
out["glm_missing"] = {c: 48 - have.get(c, 0)
                      for c in ("baseline", "quota", "temporal", "stakes", "combo")}

(R / "revision_stats.json").write_text(json.dumps(out, indent=1))
print("significant after Holm:", out["significant_after_holm"])
print("memorization (sonnet):", {k: v for k, v in mem.items() if k.startswith("sonnet")})
print("human lenient:", out["human_lenient"], "near-miss share:", out["human_near_miss_share"])
for k, v in loop_counts.items():
    if k.startswith("sonnet") or k.startswith("qwen"):
        print(k, v)
print("pressured drafts:", out["n_pressured_drafts"])
