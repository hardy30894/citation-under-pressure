#!/usr/bin/env python3
"""Human-reference citation existence by reporter group.

The human reference's existence rate (src/human_baseline.py) pools every
reporter, so a state-reporter citation the index holds only in part
lands in the not-found count. This script rescores the same clean brief
excerpts with the citation checker alone and tallies the verdicts by
reporter group (U.S. Reports; the F., F.2d, F.3d, F. Supp. family;
S. Ct. and L. Ed.; state reporters; other), then reports existence
overall and on U.S. Reports plus federal-reporter citations only.
Writes results/human_existence.json."""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

import human_baseline as hb  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa: E402
from appellate_stats import FEDERAL  # noqa: E402

SCT_LED = {"SCt", "LEd", "LEd2d"}
STATE = re.compile(
    r"^(NE|NE2d|NE3d|NW|NW2d|NW3d|P|P2d|P3d|So|So2d|So3d|A|A2d|A3d|SE|SE2d|SW|SW2d|SW3d|"
    r"NYS|NYS2d|NYS3d|CalRptr|CalRptr2d|CalRptr3d|Cal|Cal2d|Cal3d|Cal4th|Cal5th|CalApp\w*|"
    r"NY|NY2d|NY3d|AD|AD2d|AD3d|Misc|Misc2d|Misc3d|Ill|Ill2d|IllApp\w*|IllDec|Mass|MassApp\w*|"
    r"NJ|NJSuper|Pa|PaSuper|PaCmwlth|Ohio\w*|Tex|TexCrim\w*|Wash|Wash2d|WashApp|Or|OrApp|"
    r"Mich|MichApp|Minn|Wis|Wis2d|Conn|ConnApp|Md|MdApp|Va|VaApp|Ga|GaApp|Fla|Ariz|ArizApp|"
    r"Colo|ColoApp|Idaho|Kan|KanApp\w*|Ky|La|Me|Mont|Neb|Nev|NH|NM|NC|NCApp|ND|Okla|"
    r"OklaCrim|RI|SC|SD|Tenn|TennApp|Utah|Vt|WVa|Wyo|Haw|HawApp|Alaska|Ala|AlaApp|Ark|ArkApp|"
    r"Del|DelCh|Ind|IndApp|Iowa|Miss|Mo|MoApp|Ill\w*|Ohio\w*)$")


def group(reporter):
    rep = (reporter or "").replace(" ", "").replace(".", "")
    if rep == "US":
        return "us"
    if rep in FEDERAL or rep.startswith(("F", "FSupp", "FedAppx", "FedCl", "FRD", "BR")):
        return "federal"
    if rep in SCT_LED:
        return "sct_led"
    if STATE.match(rep):
        return "state"
    return "other"


def main():
    rows = hb.load_clean_excerpts()
    checker = CitationChecker(SqliteIndex(hb.DB))
    tally = defaultdict(Counter)
    reporters = defaultdict(Counter)
    nf_by_reporter = Counter()
    for row in rows:
        try:
            recs, _ = checker.check_text(row["text"])
        except Exception:
            continue
        for r in recs:
            g = group(r["reporter"])
            tally[g][r["verdict"]] += 1
            reporters[g][r["reporter"]] += 1
            if r["verdict"] == "not_found":
                nf_by_reporter[r["reporter"]] += 1

    def rate(groups):
        ex = sum(tally[g]["exists"] for g in groups)
        nf = sum(tally[g]["not_found"] for g in groups)
        return {"exists": ex, "not_found": nf,
                "unresolvable": sum(tally[g]["unresolvable"] for g in groups),
                "existence_rate": round(ex / (ex + nf), 4) if ex + nf else None}

    out = {"by_group": {g: dict(c) for g, c in tally.items()},
           "reporters_by_group": {g: dict(c.most_common(12)) for g, c in reporters.items()},
           "overall": rate(list(tally)),
           "us_and_federal": rate(["us", "federal"]),
           "us_only": rate(["us"]),
           "federal_only": rate(["federal"]),
           "state_only": rate(["state"]),
           "not_found_by_reporter": dict(nf_by_reporter.most_common()),
           "n_excerpts": len(rows)}
    (HERE / "results" / "human_existence.json").write_text(json.dumps(out, indent=1))
    for g, c in tally.items():
        ex, nf = c["exists"], c["not_found"]
        print(f"{g:9s} exists {ex:5d} not_found {nf:4d} unresolvable {c['unresolvable']:4d} "
              f"rate {ex / (ex + nf) if ex + nf else float('nan'):.3f}")
    print("overall", out["overall"])
    print("us+federal", out["us_and_federal"])
    print("not found by reporter", dict(nf_by_reporter.most_common(15)))


if __name__ == "__main__":
    main()
