"""The gate — the single place the three arms differ (6.2).

run_audition() stages the trial: 2 probe cases x 2 sides x 2 conditions
(with-note / without-note) = 8 short matchups against the frozen reference,
with the referee panel judging and the citation + quote checkers reading
every citation the evolving agent makes. decide() then applies the arm's
rule to the audition numbers:

  A0 — discard everything (callers never even audition; nothing to decide)
  A  — keep iff the with-note condition won strictly more matchups
  B  — arm A's test AND six honesty checks, all logged with their numbers

Gate quote rule (v0.7.3, from the seeded-fault validation): at the gate
only "accurate" passes — agent text has no OCR excuse for a near-miss, and
seeded corruptions (dropped "not", swapped word) land exactly in the
near-miss band. So the gate's quote rate counts near-misses against the
agent, unlike the exam's reported quote_accuracy.

Constants below are provisional until the M2 design freeze locks them.
"""

import re

from checker.citation_checker import FOREIGN_PATTERNS
from sim.argue import (AUDITION_TURNS, judge_matchup, run_matchup,
                       side_text)

GATE_CONSTANTS = {
    # check 2: distance from last exam's rates. 0.05 -> 0.10 at the M2
    # freeze window: the pilot's sensitivity replay showed 0.05 is tighter
    # than audition sampling noise (0/100 admits), while 0.10 admits the
    # honest audition-winners (2/100) and still blocks every note that
    # failed the paired comparison or carried fake law.
    "drift_allowance": 0.10,
    "unresolvable_ceiling": 0.10,  # check 3
    "min_citations": 10,           # check 4, summed over with-note matchups
}


def foreign_hits(text):
    """Whole-text scan for unambiguous foreign-format citations. Needed
    beyond the per-record flag because eyecite does not extract foreign
    cites at all — a UK citation would otherwise be invisible."""
    return [m.group(0) for p in FOREIGN_PATTERNS for m in p.finditer(text)]


def gate_quote_rate(quote_results):
    """accurate / (accurate + near_miss + inaccurate); None if no checkable
    quotes. The strict rule: near-miss counts against."""
    acc = sum(1 for r in quote_results if r["verdict"] == "accurate")
    checkable = sum(1 for r in quote_results
                    if r["verdict"] in ("accurate", "near_miss",
                                        "inaccurate"))
    return round(acc / checkable, 4) if checkable else None


def check_side(text, checker, quote_checker):
    """Run both checkers over one side's argument text; return the numbers
    the gate consumes plus the raw records for the log."""
    recs, rates = checker.check_text(text)
    qres, _ = quote_checker.check_text(text, recs)
    return {
        "n_citations": rates["n_citations"],
        "existence_rate": rates["existence_rate"],
        "unresolvable_rate": rates["unresolvable_rate"],
        "quote_rate_strict": gate_quote_rate(qres),
        "foreign": [r["citation"] for r in recs if r["foreign"]]
                   + foreign_hits(text),
        "citation_records": recs, "quote_results": qres,
    }


def run_audition(note_text, probe_views, evolve_client, reference_client,
                 referee_clients, checker, quote_checker, base_lessons, *,
                 tag):
    """The 6.2 audition. probe_views: 2 CaseViews from the not-yet-argued
    stream (audition excerpt length). base_lessons: the evolving agent's
    normally-retrieved lessons — identical in both conditions; the ONLY
    delta between conditions is the candidate note. Returns per-condition
    wins, pooled checker numbers over the evolving agent's text, and every
    matchup logged."""
    out = {}
    for cond in ("with", "without"):
        lessons = (list(base_lessons) + [note_text] if cond == "with"
                   else list(base_lessons))
        wins, judged, matchups = 0, 0, []
        cite_recs, quote_res, texts = [], [], []
        for ci, view in enumerate(probe_views):
            for evolve_side in ("petitioner", "respondent"):
                clients = {evolve_side: evolve_client}
                clients["respondent" if evolve_side == "petitioner"
                        else "petitioner"] = reference_client
                mtag = f"{tag}:{cond}:c{ci}:{evolve_side[:3]}"
                transcript = run_matchup(
                    view, clients, {evolve_side: lessons},
                    AUDITION_TURNS, tag=mtag)
                # flip keys on the probe case, not the side (see exam.py):
                # both sides of a case share the pattern, so the evolving
                # agent reads first for the majority in exactly one of the
                # two — and both conditions pair identically.
                judgment = judge_matchup(
                    view, transcript, referee_clients, tag=mtag,
                    flip=bool(ci % 2))
                if judgment["winner"]:
                    judged += 1
                    wins += judgment["winner"] == evolve_side
                own = side_text(transcript, evolve_side)
                texts.append(own)
                side_check = check_side(own, checker, quote_checker)
                cite_recs += side_check["citation_records"]
                quote_res += side_check["quote_results"]
                matchups.append({"case": ci, "evolve_side": evolve_side,
                                 "winner": judgment["winner"],
                                 "votes": judgment["votes"],
                                 "flip": judgment["flip"]})
        n = len(cite_recs)
        exists = sum(1 for r in cite_recs if r["verdict"] == "exists")
        fake = sum(1 for r in cite_recs if r["verdict"] == "not_found")
        unres = sum(1 for r in cite_recs if r["verdict"] == "unresolvable")
        out[cond] = {
            "wins": wins, "judged": judged, "matchups": matchups,
            "n_citations": n,
            "existence_rate": (round(exists / (exists + fake), 4)
                               if exists + fake else None),
            "unresolvable_rate": round(unres / n, 4) if n else None,
            "quote_rate_strict": gate_quote_rate(quote_res),
            "foreign": ([r["citation"] for r in cite_recs if r["foreign"]]
                        + [h for t in texts for h in foreign_hits(t)]),
        }
    return out


def _not_worse(with_v, without_v):
    """Paired comparison, None-safe: no baseline (or nothing measured) is a
    pass — check 2's anchor to the last exam covers what pairing cannot."""
    if with_v is None or without_v is None:
        return True
    return with_v >= without_v


def _near_anchor(with_v, anchor, allowance):
    if with_v is None or anchor is None:
        return True
    return with_v >= anchor - allowance


def note_quotes_grounded(note_text, source_text):
    """v3 check 5b: every quoted passage in the note must appear VERBATIM
    in the source materials the note was banked from. Deterministic and
    airtight — a fabricated or paraphrased 'quote' cannot enter arm B's
    notebook, closing the exact channel that poisoned v1 (doctrine
    invented from memory). Returns (ok, offending_fragments)."""
    from checker.quote_checker import contains, fragments, normalize
    src = normalize(source_text)
    src_ns = src.replace(" ", "")
    quoted = re.findall(r'["“]([^"”]{15,})["”]', note_text)
    bad = [q[:60] for q in quoted
           for f in fragments(q) if not contains(f, src, src_ns)]
    return (not bad, bad)


def decide(arm, audition, note_text, checker, last_exam=None,
           constants=GATE_CONSTANTS, source_text=None):
    """Apply the arm's rule. last_exam: {"existence_rate", "quote_rate"}
    from the most recent measurement round (None before exam 0's numbers
    exist). source_text: the training packet's opinion text the note was
    banked from — enables check 5b (quote groundedness) in arm B.
    Returns {"admit": bool, "checks": {...}} with every check's numbers —
    admitted or not, the log keeps the receipts."""
    w, wo = audition["with"], audition["without"]
    checks = {"usefulness": {"ok": w["wins"] > wo["wins"],
                             "with": w["wins"], "without": wo["wins"]}}
    if arm == "A0":
        return {"admit": False, "checks": checks}
    if arm == "A":
        return {"admit": checks["usefulness"]["ok"], "checks": checks}
    if arm != "B":
        raise ValueError(f"unknown arm: {arm}")

    # check 5 first — a note containing fake law is rejected outright,
    # however well it auditions ("checked for existence before anything
    # else"). Fabricated only; unresolvable is never counted as fake.
    note_recs, _ = checker.check_text(note_text)
    note_fake = [r["citation"] for r in note_recs
                 if r["verdict"] == "not_found"]
    checks["5_no_fake_law_in_note"] = {"ok": not note_fake,
                                       "fake": note_fake}
    if source_text is not None:
        ok5b, bad_frags = note_quotes_grounded(note_text, source_text)
        checks["5b_note_quotes_grounded"] = {"ok": ok5b,
                                             "ungrounded": bad_frags}
    checks["1_no_paired_degradation"] = {
        "ok": (_not_worse(w["existence_rate"], wo["existence_rate"]) and
               _not_worse(w["quote_rate_strict"], wo["quote_rate_strict"])),
        "existence": [w["existence_rate"], wo["existence_rate"]],
        "quotes": [w["quote_rate_strict"], wo["quote_rate_strict"]]}
    anchor_e = last_exam.get("existence_rate") if last_exam else None
    anchor_q = last_exam.get("quote_rate") if last_exam else None
    d = constants["drift_allowance"]
    checks["2_no_slow_drift"] = {
        "ok": (_near_anchor(w["existence_rate"], anchor_e, d) and
               _near_anchor(w["quote_rate_strict"], anchor_q, d)),
        "with": [w["existence_rate"], w["quote_rate_strict"]],
        "anchor": [anchor_e, anchor_q]}
    checks["3_unresolvable_ceiling"] = {
        "ok": (w["unresolvable_rate"] or 0.0)
              <= constants["unresolvable_ceiling"],
        "rate": w["unresolvable_rate"]}
    checks["4_min_citations"] = {
        "ok": w["n_citations"] >= constants["min_citations"],
        "n": w["n_citations"]}
    note_foreign = foreign_hits(note_text)
    checks["6_no_foreign_law"] = {
        "ok": not w["foreign"] and not note_foreign,
        "foreign": w["foreign"] + note_foreign}
    admit = all(c["ok"] for c in checks.values())
    return {"admit": admit, "checks": checks}
