#!/usr/bin/env python3
"""Audit of the attribution step on real drafts.

A quotation is attributed to the case named in the same sentence, else the
nearest citation within 260 characters after it, else the nearest
preceding one. A draft may instead be quoting the packet it was given
(the question presented, the facts, the lower-court opinion) or a statute
or rule; such a quotation gets attributed to a nearby case and, where that
case has opinion text, scored inaccurate. This script rescores the full
Supreme Court run with the paper's pipeline and sorts every inaccurate
quotation into packet material (its longest fragment is verbatim in the
packet), statutory (the nearest citation-like token before it, within 260
characters or in the same sentence, is a statute or rule with no case
citation between it and the quotation), both, or neither. It also counts
packet material over all scored quotations, whatever the verdict.

Writes results/attribution_audit.json and a 40-item random sample of
inaccurate quotations with draft context to
results/attribution_audit_sample.md for a human spot-check."""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from pilot import GE, DB, pick_matters, case_view  # noqa: E402
from rescore_pilots import eyecite_pass  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore, normalize, fragments  # noqa: E402
from local_text import ChainTextStore  # noqa: E402
import quotecheck2 as q2  # noqa: E402
from records_dump import MODELS  # noqa: E402

WINDOW = 260
STATUTE = re.compile(
    r"U\.?\s?S\.?\s?C\.?|C\.?\s?F\.?\s?R\.?|§|\bSection\s+\d|\bRule\s+\d|Fed\.\s?R\.|\bStat\.")


def packet_text(entry):
    packet = json.loads((GE / "data/packets" / entry["packet"]).read_text())
    view = case_view(packet)
    raw = packet.get("lower_court_opinion", {}).get("raw_text", "") or view.opinion_excerpt
    return normalize(" ".join([view.question, view.facts, raw]))


def in_packet(quote, pnorm, pnospace):
    frags = fragments(quote) or [normalize(quote)]
    frag = max(frags, key=len)
    if len(frag) < 15:
        return False
    return frag in pnorm or frag.replace(" ", "") in pnospace


def statutory(text, qstart, cite_starts):
    """True when the nearest statute or rule token before the quotation
    (within the window, or anywhere in the same sentence) is closer than
    any case citation in between."""
    lo = max(0, qstart - WINDOW)
    sent = text.rfind(". ", 0, qstart)
    lo = min(lo, sent + 2 if sent >= 0 else lo)
    before = text[lo:qstart]
    last = None
    for m in STATUTE.finditer(before):
        last = lo + m.start()
    if last is None:
        return False
    return not any(last < c < qstart for c in cite_starts)


def main():
    checker = CitationChecker(SqliteIndex(DB))
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None, fetch_budget=0))
    packets = {}
    for entry in pick_matters(48):
        p = packet_text(entry)
        packets[entry["id"]] = (p, p.replace(" ", ""))
    out = {}
    sample_pool = []
    for model in MODELS:
        c = Counter()
        for path in sorted((HERE / "results" / f"full_{model}" / "drafts").glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", path.stem).groups()
            if matter not in packets:
                continue
            text = path.read_text()
            recs, _ = checker.check_text(text)
            ep = eyecite_pass(text)
            res = q2.check_draft(text, recs, ep, store)
            quotes = q2.extract_quotes(text)
            assert len(quotes) == len(res)
            cite_starts = [e["start"] for e in ep]
            pnorm, pnospace = packets[matter]
            for q, r in zip(quotes, res):
                if r["verdict"] not in ("accurate", "near_miss", "inaccurate"):
                    continue
                c["scored_total"] += 1
                pk = in_packet(q["quote"], pnorm, pnospace)
                if pk:
                    c["packet_material_any_verdict"] += 1
                    c[f"packet_material_{r['verdict']}"] += 1
                if r["verdict"] != "inaccurate":
                    continue
                st = statutory(text, q["start"], cite_starts)
                c["inaccurate_total"] += 1
                # extraction artifact: a span opening with whitespace is the
                # tail of a quotation whose closing mark was paired wrongly
                if q["quote"][:1].isspace():
                    c["artifact_leading_space"] += 1
                c[f"attribution_{r['attribution']}"] += 1
                if pk and st:
                    cls = "both"
                elif pk:
                    cls = "packet_material"
                elif st:
                    cls = "statutory"
                else:
                    cls = "neither"
                c[cls] += 1
                sample_pool.append({
                    "model": model, "draft": path.stem, "citation": r["citation"],
                    "class": cls, "attribution": r["attribution"], "quote": q["quote"][:200],
                    "context": text[max(0, q["start"] - 200): q["start"]].replace("\n", " "),
                })
        out[model] = {k: c.get(k, 0) for k in (
            "inaccurate_total", "packet_material", "statutory", "both", "neither",
            "scored_total", "packet_material_any_verdict",
            "packet_material_accurate", "packet_material_near_miss", "packet_material_inaccurate",
            "artifact_leading_space", "attribution_named", "attribution_proximity")}
        print(f"{model:12s} inacc {out[model]['inaccurate_total']:4d}  packet {out[model]['packet_material']:3d}  "
              f"statute {out[model]['statutory']:3d}  both {out[model]['both']:2d}  neither {out[model]['neither']:4d}  | "
              f"scored {out[model]['scored_total']:5d} packet-any {out[model]['packet_material_any_verdict']:3d}", flush=True)
    pooled = Counter()
    for v in out.values():
        pooled.update(v)
    pooled = dict(pooled)
    n = pooled["inaccurate_total"]
    pooled["share_packet_or_statutory"] = round((pooled["packet_material"] + pooled["statutory"] + pooled["both"]) / n, 4) if n else None
    out["_pooled"] = pooled
    (HERE / "results" / "attribution_audit.json").write_text(json.dumps(out, indent=1))
    print("pooled", pooled)
    rng = random.Random(20260831)
    sample = rng.sample(sample_pool, min(40, len(sample_pool)))
    lines = ["# Attribution audit: 40 random inaccurate quotations\n",
             "Seed 20260831 over every inaccurate verdict in the full run. Class is the",
             "script's deterministic call; read the context and judge for yourself.\n"]
    for i, s in enumerate(sample, 1):
        lines.append(f"## {i}. {s['model']} {s['draft']} | cited {s['citation']} ({s['attribution']}) | class: {s['class']}\n")
        lines.append(f"context before: ...{s['context']}\n")
        lines.append(f"quote: “{s['quote']}”\n")
    (HERE / "results" / "attribution_audit_sample.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
