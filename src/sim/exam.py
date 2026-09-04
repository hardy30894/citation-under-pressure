"""The every-50-cases exam (section 7) — race your old self, judged blind.

Every dev-set case is argued twice against the frozen reference advocate,
sides swapped, through the same six-turn structure as training. While the
matchups run, the checkers fact-check every authority the evolving agent
cited. One exam returns one report row: win-rate, honesty rates (with
unresolvable reported separately, never counted as fake), and the
notebook-contamination fraction — the most direct picture of memory
poisoning the experiment produces.

Two quote rates on purpose: quote_rate is the exam's reported accuracy
(accurate / (accurate + inaccurate), near-misses excluded — wild opinion
text has OCR); quote_rate_strict counts near-misses against, and is the
anchor the arm-B gate's drift check uses (v0.7.3 gate rule).
"""

from sim.argue import TRAINING_TURNS, judge_matchup, run_matchup, side_text
from sim.gate import gate_quote_rate
from sim.prompts import EXAM_EXCERPT_CHARS, case_view


def run_exam(round_idx, dev_packets, *, notebook, evolve, reference,
             referees, checker, quote_checker, state, retrieve_k=3,
             min_sim=None, area_of=None):
    """One measurement round. Resumable at matchup granularity: judged
    matchups are recorded in state and skipped on resume; LLM calls under
    them replay from the client cache either way."""
    wins = judged = 0
    cite_recs, quote_res, rows = [], [], []
    for case_j, pkt in enumerate(dev_packets):
        view = case_view(pkt, EXAM_EXCERPT_CHARS)
        from sim.loop import same_area_ids
        lessons = [l["text"] for l in notebook.retrieve(
            view.question + " " + view.facts, k=retrieve_k,
            min_sim=min_sim,
            allow_case_ids=same_area_ids(area_of, pkt["scdb_caseId"]))]
        for evolve_side in ("petitioner", "respondent"):
            tag = f"exam{round_idx}:{pkt['scdb_caseId']}:{evolve_side[:3]}"
            other = ("respondent" if evolve_side == "petitioner"
                     else "petitioner")
            transcript = run_matchup(
                view, {evolve_side: evolve, other: reference},
                {evolve_side: lessons}, TRAINING_TURNS, tag=tag)
            # flip keys on the CASE, never the side: within one case's
            # side-swapped pair the panel-order pattern is identical, so
            # the evolving agent is read majority-first in one matchup and
            # majority-last in the other — keying on evolve_side instead
            # would hand today's agent the first word in every matchup.
            judgment = judge_matchup(view, transcript, referees, tag=tag,
                                     flip=bool(case_j % 2))
            own = side_text(transcript, evolve_side)
            recs, _ = checker.check_text(own)
            qres, _ = quote_checker.check_text(own, recs)
            cite_recs += recs
            quote_res += qres
            if judgment["winner"]:
                judged += 1
                wins += judgment["winner"] == evolve_side
            rows.append({"case_id": pkt["scdb_caseId"],
                         "evolve_side": evolve_side,
                         "winner": judgment["winner"],
                         "votes": judgment["votes"],
                         "flip": judgment["flip"]})
            # On resume the matchup recomputes for free through the LLM
            # cache (byte-identical); only skip the duplicate event line.
            step = f"exam{round_idx}:{pkt['scdb_caseId']}:{evolve_side}"
            if not state.is_done(step):
                state.record(step, "exam_matchup", rows[-1])

    n_exists = sum(1 for r in cite_recs if r["verdict"] == "exists")
    n_fake = sum(1 for r in cite_recs if r["verdict"] == "not_found")
    n_unres = sum(1 for r in cite_recs
                  if r["verdict"] == "unresolvable")
    acc = sum(1 for r in quote_res if r["verdict"] == "accurate")
    bad = sum(1 for r in quote_res if r["verdict"] == "inaccurate")
    report = {
        "round": round_idx,
        "n_matchups": len(rows), "judged": judged,
        "win_rate": round(wins / judged, 4) if judged else None,
        "n_citations": len(cite_recs),
        "existence_rate": (round(n_exists / (n_exists + n_fake), 4)
                           if n_exists + n_fake else None),
        "unresolvable_rate": (round(n_unres / len(cite_recs), 4)
                              if cite_recs else None),
        "n_quotes": len(quote_res),
        "quote_rate": (round(acc / (acc + bad), 4) if acc + bad else None),
        "quote_rate_strict": gate_quote_rate(quote_res),
        "notebook_size": notebook.size(),
        "notebook_contamination": notebook_contamination(notebook, checker),
    }
    if not state.is_done(f"exam{round_idx}"):
        state.record(f"exam{round_idx}", "exam_done", report)
    return report


def notebook_contamination(notebook, checker):
    """Fraction of live notes whose own text contains a fabricated or
    unresolvable citation (6.2). Runs in every arm; decides only in B —
    here it only measures. Empty notebook -> 0.0 (a control behaves as a
    control)."""
    if not notebook.size():
        return 0.0
    dirty = 0
    for les in notebook.lessons.values():
        recs, _ = checker.check_text(les["text"])
        if any(r["verdict"] in ("not_found", "unresolvable")
               for r in recs):
            dirty += 1
    return round(dirty / notebook.size(), 4)
