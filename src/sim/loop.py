"""The training loop — section 6.1's three phases, orchestrated.

One call to train_case() is one case start to finish: self-play argument
(phase 1), reflection into at most one candidate lesson (phase 2), the
arm's gate (phase 3). run_stream() walks a case sequence, pauses training
for an exam at case 0 and after every `exam_every` cases, honors safe
pause between atomic steps, and appends one event per completed case.

Resume strategy, stated once: the LLM cache is the checkpoint. A completed
case whose event is on disk is skipped outright; a case interrupted midway
re-runs from its start, and every already-made LLM call replays
byte-identically from the cache at zero cost. So a resumed run converges
to the exact run the crash interrupted.

Audition probes come from further down the training queue — cases the
agent hasn't argued yet — fresh every decision (adaptive-overfitting
guard). End-of-stream edge (6.2): when fewer than 2 unargued cases remain,
the shortfall draws from the most recently argued cases and the gate log
marks the decision as a tail case.
"""

from sim.argue import TRAINING_TURNS, run_matchup
from sim.exam import run_exam
from sim.gate import decide, run_audition
from sim.notebook import Notebook
from sim.prompts import (AUDITION_EXCERPT_CHARS, EXAM_EXCERPT_CHARS,
                         case_view, parse_lesson, reflect_messages)

# Freeze-candidate retrieval (exam-1b validated): top-3, NO topical floor.
# Craft lessons are universal — the floor was right for doctrine (now
# banned) and wrong for craft (it suppressed retrieval to 2/30 dev cases).
RETRIEVE_K = 3
RETRIEVE_FLOOR = None   # Notebook.retrieve still supports min_sim
RETRIEVAL_MODE = "domain-keyed top-3"   # recorded in run manifests
N_PROBES = 2       # audition cases per gate decision (v0.7 cost lock)


def probe_packets(stream, idx):
    """The 6.2 probe draw: the next N_PROBES cases after idx; at the tail,
    backfill from the most recently argued. Returns (packets, is_tail)."""
    ahead = stream[idx + 1: idx + 1 + N_PROBES]
    if len(ahead) == N_PROBES:
        return ahead, False
    short = N_PROBES - len(ahead)
    return list(ahead) + list(reversed(stream[max(0, idx - short): idx])), True


def same_area_ids(area_of, case_id):
    """Source-case ids sharing the current case's issue area — the
    domain-keyed retrieval allow-list. None disables the filter."""
    if area_of is None:
        return None
    a = area_of.get(case_id)
    return {cid for cid, ar in area_of.items() if ar == a}


def train_case(idx, stream, *, arm, notebook, state, evolve, reference,
               referees, checker, quote_checker, last_exam, area_of=None):
    """One case through phases 1-3. Skipped instantly if already done."""
    pkt = stream[idx]
    step = f"case{idx:04d}"
    if state.is_done(step):
        return
    view = case_view(pkt, EXAM_EXCERPT_CHARS)
    lessons = [l["text"] for l in notebook.retrieve(
        view.question + " " + view.facts, k=RETRIEVE_K,
        min_sim=RETRIEVE_FLOOR,
        allow_case_ids=same_area_ids(area_of, pkt["scdb_caseId"]))]

    # Phase 1 — self-play: one brain, both roles, lessons on both sides.
    tag = f"{arm}:{step}"
    transcript = run_matchup(
        view, {"petitioner": evolve, "respondent": evolve},
        {"petitioner": lessons, "respondent": lessons},
        TRAINING_TURNS, tag=tag)

    # Phase 2 — at most one candidate lesson. Nothing saved yet.
    raw = evolve.chat(reflect_messages(view, transcript),
                      max_tokens=200, tag=f"{tag}:reflect")
    note = parse_lesson(raw)

    # Phase 3 — the gate: the single place the arms differ.
    event = {"case_id": pkt["scdb_caseId"], "note": note, "admitted": False}
    if note and arm in ("A", "B"):
        probes, is_tail = probe_packets(stream, idx)
        probe_views = [case_view(p, AUDITION_EXCERPT_CHARS) for p in probes]
        audition = run_audition(
            note, probe_views, evolve, reference, referees,
            checker, quote_checker, lessons, tag=f"{tag}:aud")
        decision = decide(
            arm, audition, note, checker, last_exam,
            source_text=pkt["lower_court_opinion"]["raw_text"])
        if decision["admit"]:
            notebook.add(note, case_id=pkt["scdb_caseId"],
                         meta={"case_idx": idx})
        # the full audition dict is kept, matchups included — 7.1 stores
        # every individual referee vote, and the M1 smoke's 12/12-side
        # referee was caught only because votes were on disk.
        event.update(
            admitted=decision["admit"], tail_probe=is_tail,
            checks=decision["checks"], audition=audition,
            probe_cases=[p["scdb_caseId"] for p in probes])
    elif note and arm == "A0":
        event["checks"] = {"arm": "A0 discards every note"}
    event["notebook_size"] = notebook.size()
    state.record(step, "case_done", event)


def run_stream(stream, dev_packets, *, arm, run_dir, evolve, reference,
               referees, checker, quote_checker, state, exam_every=50,
               area_of=None):
    """A whole run: exam at case 0, train, exam after every block. Returns
    the list of exam reports. Safe pause honored between atomic steps."""
    notebook = Notebook(f"{run_dir}/notebook.jsonl")
    exams = []
    last_exam = None

    def recorded_exam(round_idx):
        """A completed exam's report, read back from the event log. On
        resume, a finished exam must be SKIPPED, not recomputed: the live
        notebook has moved past the state that exam measured, so a
        recompute would rebuild different prompts (cache misses, real
        spend) against the wrong notebook. The log is the truth."""
        import json as _json
        from pathlib import Path as _P
        path = _P(run_dir) / "events.jsonl"
        if not path.exists():
            return None
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                ev = _json.loads(line)
            except ValueError:
                continue
            if ev.get("step") == f"exam{round_idx}" \
                    and ev.get("type") == "exam_done":
                return ev["data"]
        return None

    def hold_exam(round_idx):
        nonlocal last_exam
        report = None
        if state.is_done(f"exam{round_idx}"):
            report = recorded_exam(round_idx)
        if report is None:
            report = run_exam(
                round_idx, dev_packets, notebook=notebook, evolve=evolve,
                reference=reference, referees=referees, checker=checker,
                quote_checker=quote_checker, state=state, area_of=area_of)
        exams.append(report)
        # The gate's drift anchor is the BEST honesty any exam has shown
        # (adversarial review caught the ratchet in anchoring to the LAST
        # exam: each mildly-degrading admission lowers the next anchor,
        # licensing the next degradation — honesty could walk down while
        # every decision passes). Max-over-exams pins the anchor to the
        # cleanest measured self; exam 0's empty-notebook baseline is
        # always included. Strict quote rate per v0.7.3.
        cand = {"existence_rate": report["existence_rate"],
                "quote_rate": report["quote_rate_strict"]}
        if last_exam is None:
            last_exam = cand
        else:
            last_exam = {
                k: (max(v, cand[k]) if v is not None and cand[k] is not None
                    else (v if v is not None else cand[k]))
                for k, v in last_exam.items()}

    hold_exam(0)
    for idx in range(len(stream)):
        if state.should_stop():
            state.set_status("paused", f"at case {idx}")
            return exams
        train_case(idx, stream, arm=arm, notebook=notebook, state=state,
                   evolve=evolve, reference=reference, referees=referees,
                   checker=checker, quote_checker=quote_checker,
                   last_exam=last_exam, area_of=area_of)
        if (idx + 1) % exam_every == 0:
            hold_exam((idx + 1) // exam_every)
    state.set_status("done")
    notebook.close()
    return exams
