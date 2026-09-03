#!/usr/bin/env python3
"""Index coverage on citations known to be real.

The appellate task reports that citations to F.2d, F.3d, and F. Supp.
fail to resolve far more often than citations to the U.S. Reports. A
reviewer asks whether that gap is the index's coverage rather than the
models' fabrication. This script resolves every full case citation that
appears in the 48 deciding appellate opinions themselves (the F.3d
opinions behind results/appellate/manifest.json, read from the Caselaw
Access Project cache), which are real by construction, and reports the
not-found share per reporter group. Writes results/index_recall.json."""

import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
R = HERE / "results"

from pilot import DB  # noqa: E402  (puts the checker package on the path)
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa: E402
from local_text import CACHE_DB  # noqa: E402
from appellate_stats import FEDERAL  # noqa: E402


def group(rep):
    rep = (rep or "").replace(" ", "").replace(".", "")
    return "us" if rep == "US" else ("federal" if rep in FEDERAL else "other")


def main():
    checker = CitationChecker(SqliteIndex(DB))
    con = sqlite3.connect(CACHE_DB)
    manifest = json.loads((R / "appellate" / "manifest.json").read_text())
    counts = Counter()
    by_reporter = Counter()
    opinions = 0
    for m in manifest:
        vol, page = re.match(r"F3d-(\d+)-(\d+)", m["id"]).groups()
        row = con.execute("SELECT text FROM cap_texts WHERE slug='f3d' AND volume=? AND page=?",
                          (vol, page)).fetchone()
        if not row or not row[0]:
            continue
        opinions += 1
        recs, _ = checker.check_text(row[0])
        for r in recs:
            if r["verdict"] not in ("exists", "not_found"):
                continue
            g = group(r["reporter"])
            counts[g] += 1
            rep = (r["reporter"] or "").replace(" ", "")
            by_reporter[rep] += 1
            if r["verdict"] == "not_found":
                counts[g + "_nf"] += 1
                by_reporter[rep + "_nf"] += 1
    out = {"opinions": opinions, "groups": {}}
    for g in ("us", "federal", "other"):
        n, nf = counts[g], counts[g + "_nf"]
        out["groups"][g] = {"citations": n, "not_found": nf,
                            "not_found_share": round(nf / n, 4) if n else None}
    tot = sum(counts[g] for g in ("us", "federal", "other"))
    tnf = sum(counts[g + "_nf"] for g in ("us", "federal", "other"))
    out["all"] = {"citations": tot, "not_found": tnf,
                  "not_found_share": round(tnf / tot, 4) if tot else None}
    reps = sorted({k for k in by_reporter if not k.endswith("_nf")},
                  key=lambda k: -by_reporter[k])
    out["by_reporter"] = {k: {"citations": by_reporter[k], "not_found": by_reporter[k + "_nf"]}
                          for k in reps[:25]}
    (R / "index_recall.json").write_text(json.dumps(out, indent=1))
    print(f"{opinions} deciding opinions")
    for g, v in out["groups"].items():
        print(f"  {g:8s} {v['citations']:6d} citations  not found {v['not_found']:4d}  share {v['not_found_share']}")
    print(f"  all      {out['all']['citations']:6d} citations  not found {out['all']['not_found']:4d}  share {out['all']['not_found_share']}")
    print("  top reporters:", {k: (v["citations"], v["not_found"]) for k, v in list(out["by_reporter"].items())[:8]})


if __name__ == "__main__":
    main()
