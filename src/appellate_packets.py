#!/usr/bin/env python3
"""Second task: federal courts of appeals.

Builds 24 appellate matter packets from published F.3d opinions in the
local Caselaw Access Project cache. The packet is the opinion's own
statement of the case and facts, cut where the court's analysis begins
and scrubbed of outcome sentences, so the drafter sees the posture and
the record but not the holding. Party roles and the circuit come from
the CAP head matter (the parties line names the appellant). Selection
is deterministic: opinions decided 1995 to 2019, 15,000 to 60,000
characters, a clean appellant, a packet of 250 to 900 words with no
outcome language left after scrubbing, at most two per circuit, seeded
shuffle. Writes results/appellate/packets/<id>.json and a manifest."""

import hashlib
import json
import random
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
from local_text import CACHE_DB  # noqa: E402

OUT = HERE / "results" / "appellate" / "packets"
N = 24
PER_CIRCUIT = 2

ANALYSIS = re.compile(
    r"^(II\.|III\.|DISCUSSION|ANALYSIS|Discussion|Analysis|STANDARD OF REVIEW)\b|"
    r"\b(standard of review|[Ww]e review|de novo|[Ww]e turn|[Ww]e begin (?:our|with)|"
    r"[Ww]e first|[Ww]e must decide|[Ww]e consider first)\b")
OUTCOME = re.compile(
    r"\b(we|We) (also |further |therefore |accordingly |now |thus )?"
    r"(affirm|reverse|vacate|remand|hold|conclude|agree|disagree|reject|grant|deny|"
    r"instruct|direct|find|decline|dismiss|see no|are not persuaded|are persuaded)\b|"
    r"^We\b|\b(AFFIRMED|REVERSED|VACATED|REMANDED|Affirmed|Reversed|Vacated|Remanded)\b|"
    r"\bis (affirmed|reversed|vacated)\b|\bare (affirmed|reversed|vacated)\b")
HEADER = re.compile(r"wrote the (majority )?opinion|dissent|concurr|delivered the opinion|"
                    r"Circuit Judges?[:.]?$|^OPINION( OF THE COURT)?$|^ORDER$|Before .* Judges", re.I)
CIRCUIT = re.compile(r"United States Court of Appeals,? (?:for the )?([A-Za-z.]+) Circuit")


def head(html, cls):
    m = re.search(r'class="%s"[^>]*>(.*?)</' % cls, html, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""


ROLE = re.compile(r"[,;]?\s*(Plaintiffs?|Defendants?|Petitioners?|Respondents?|Claimants?|"
                  r"Intervenors?|Cross-Appell(?:ant|ee)s?|Counter-\w+)[-\s]*$", re.I)


def clean_party(s):
    s = ROLE.sub("", s.strip()).strip(" ,;-")
    return re.sub(r"\s+", " ", s)


def parties(line):
    """Return (appellant, appellee) from a CAP parties line, or None."""
    line = re.sub(r"\s+", " ", line)
    m = re.match(r"(.+?),\s*([\w /-]*Appellants?)[,.]?\s+v\.\s+(.+?),\s*([\w /-]*Appellees?)[.,]?\s*$", line)
    if m:
        return clean_party(m.group(1)), clean_party(m.group(3))
    m = re.match(r"(.+?),\s*([\w /-]*Appellees?)[,.]?\s+v\.\s+(.+?),\s*([\w /-]*Appellants?)[.,]?\s*$", line)
    if m:
        return clean_party(m.group(3)), clean_party(m.group(1))
    return None


def scrub(paragraphs):
    kept = []
    for para in paragraphs:
        sents = re.split(r"(?<=[.!?])\s+", para)
        sents = [s for s in sents if not OUTCOME.search(s)]
        if sents:
            kept.append(" ".join(sents))
    return kept


def build_packet(text):
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    if len(paras) < 4:
        return None
    body = [p for p in paras if not HEADER.search(p) and not re.search(r"Judge\.?:?$|PER CURIAM", p)]
    if len(body) < 4:
        return None
    cut = None
    for i, p in enumerate(body):
        if i >= 1 and ANALYSIS.search(p):
            cut = i
            break
    if cut is None or cut < 2:
        return None
    packet = scrub(body[:cut])
    words = " ".join(packet).split()
    if len(words) < 250:
        return None
    if len(words) > 900:
        acc, out = 0, []
        for p in packet:
            if acc + len(p.split()) > 900:
                break
            out.append(p)
            acc += len(p.split())
        packet = out
        if acc < 250:
            return None
    joined = "\n".join(packet)
    if OUTCOME.search(joined) or re.search(r"\b(affirm|revers)\w*", joined, re.I):
        return None
    return joined


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    con = sqlite3.connect(CACHE_DB)
    rows = con.execute(
        "SELECT volume, page, text, html FROM cap_texts WHERE slug='f3d' "
        "AND length(text) BETWEEN 15000 AND 60000").fetchall()
    print(f"{len(rows)} F.3d candidates", flush=True)
    cands = []
    for vol, page, text, html in rows:
        if not html:
            continue
        pl = head(html, "parties")
        court = head(html, "court")
        date = head(html, "decisiondate")
        cm = CIRCUIT.search(court)
        ym = re.search(r"(19|20)\d\d", date)
        if not (cm and ym and "Appell" in pl):
            continue
        year = int(ym.group(0))
        if not 1995 <= year <= 2019:
            continue
        pp = parties(pl)
        if not pp or len(pp[0]) > 90 or len(pp[1]) > 90:
            continue
        packet = build_packet(text)
        if not packet:
            continue
        cands.append({
            "id": f"F3d-{vol}-{page}", "citation": f"{vol} F.3d {page}",
            "circuit": cm.group(1), "year": year, "decided": date,
            "appellant": pp[0], "appellee": pp[1], "parties": pl,
            "docket": head(html, "docketnumber"), "packet": packet,
            "materials_hash": hashlib.sha256(packet.encode()).hexdigest()[:12],
        })
    print(f"{len(cands)} usable candidates", flush=True)
    rng = random.Random(20260903)
    rng.shuffle(cands)
    by = defaultdict(int)
    chosen = []
    us = 0
    for c in cands:
        if by[c["circuit"]] >= PER_CIRCUIT:
            continue
        # at most a quarter of the set may be appeals against the United
        # States, so that the sample is not dominated by criminal and
        # habeas matters
        is_us = "united states" in (c["appellant"] + c["appellee"]).lower()
        if is_us and us >= N // 4:
            continue
        us += is_us
        by[c["circuit"]] += 1
        chosen.append(c)
        if len(chosen) == N:
            break
    chosen.sort(key=lambda c: (c["year"], c["id"]))
    for c in chosen:
        (OUT / f"{c['id']}.json").write_text(json.dumps(c, indent=1))
    (OUT.parent / "manifest.json").write_text(json.dumps(
        [{"id": c["id"], "citation": c["citation"], "circuit": c["circuit"],
          "year": c["year"], "appellant": c["appellant"], "appellee": c["appellee"],
          "words": len(c["packet"].split())} for c in chosen], indent=1))
    for c in chosen:
        print(c["id"], c["year"], c["circuit"], "|", c["appellant"][:40], "v.", c["appellee"][:40],
              "|", len(c["packet"].split()), "words")


if __name__ == "__main__":
    main()
