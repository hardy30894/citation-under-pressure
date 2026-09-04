"""The argument engine — matchups, self-play, and the referee panel.

A matchup is one case argued through a fixed turn structure by an advocate
per side. Training self-play (6.1 phase 1) is the special case where both
sides are the same evolving agent; exams and auditions assign the evolving
agent to one side and the frozen reference advocate to the other.

Determinism and resume come for free from LLMClient's request-keyed cache:
re-running a matchup replays identical completions for identical prompts,
so a crashed run resumed mid-matchup finishes byte-identically without any
extra checkpoint machinery here.

Referee reads are blind (7.1): party names are replaced with neutral labels
before any referee sees a word — a deterministic string pass, no LLM — so
no referee can reward the side history says won a famous case. Citations
inside the arguments stay intact; they ARE the argument. Generic party
names ("United States", "State of Texas") are left alone: they identify
nothing and masking them would mangle citations to unrelated cases.
"""

import json
import re
from dataclasses import replace

from sim.prompts import advocate_messages, referee_messages

# 6.1: opening, rebuttal, closing for each side — six substantive turns.
TRAINING_TURNS = (
    ("petitioner", "opening"), ("respondent", "opening"),
    ("petitioner", "rebuttal"), ("respondent", "rebuttal"),
    ("petitioner", "closing"), ("respondent", "closing"),
)
# 6.2: auditions use a shortened format — opening and response only.
AUDITION_TURNS = (("petitioner", "opening"), ("respondent", "rebuttal"))


def run_matchup(view, side_clients, side_lessons, turns, *, tag,
                temperature=0.7, max_tokens=1100):
    """Argue one case through `turns`. Returns the transcript as
    (side, text) pairs. side_clients / side_lessons: dicts keyed by side."""
    transcript = []
    for i, (side, kind) in enumerate(turns):
        msgs = advocate_messages(view, side, kind, transcript,
                                 side_lessons.get(side, ()))
        text = side_clients[side].chat(
            msgs, temperature=temperature, max_tokens=max_tokens,
            tag=f"{tag}:t{i}:{side}:{kind}")
        transcript.append((side, text))
    return transcript


def side_text(transcript, side):
    """All argument text one side produced — what the honesty checks read."""
    return "\n\n".join(t for s, t in transcript if s == side)


# ------------------------------------------------------------- masking

# Party names too generic to identify a case; masking them would do nothing
# for blindness and would corrupt citations to unrelated cases.
GENERIC_PARTIES = {
    "united states", "united states of america", "state", "government",
    "commissioner of internal revenue", "commissioner", "attorney general",
    "secretary", "people", "federal trade commission",
    "securities and exchange commission", "national labor relations board",
}
# Trailing entity suffixes stripped before deciding what is distinctive.
SUFFIX = re.compile(
    r",?\s*(et al\.?|inc\.?|co\.?|corp\.?|company|corporation|llc|l\.l\.c\.|"
    r"ltd\.?|l\.p\.)\s*$", re.I)
TOKEN_STOP = {"united", "states", "state", "county", "city", "board",
              "department", "district", "school", "america", "american",
              "national", "federal", "court", "justice", "director"}


def _mask_terms(name):
    """The strings that identify this party: the full cleaned name plus its
    distinctive tokens, longest first so full phrases win."""
    clean = name
    while True:
        shorter = SUFFIX.sub("", clean).strip()
        if shorter == clean:
            break
        clean = shorter
    if clean.lower() in GENERIC_PARTIES:
        return []
    toks = [t for t in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", clean)
            if t.lower() not in TOKEN_STOP]
    return sorted({clean, *toks}, key=len, reverse=True)


def mask_for_referee(view, transcript):
    """Deterministically replace party names with neutral labels in
    everything a referee will read. Returns (masked_view, masked_transcript).
    """
    subs = []
    for name, label in ((view.petitioner, "Petitioner"),
                        (view.respondent, "Respondent")):
        for term in _mask_terms(name):
            subs.append((re.compile(re.escape(term), re.I), label))

    def mask(text):
        for pat, label in subs:
            text = pat.sub(label, text)
        return text

    masked_view = replace(
        view, petitioner="Petitioner", respondent="Respondent",
        question=mask(view.question), facts=mask(view.facts))
    return masked_view, [(s, mask(t)) for s, t in transcript]


# ------------------------------------------------------------- referees

VERDICT_RE = re.compile(r'"stronger"\s*:\s*"(petitioner|respondent)"')


def parse_verdict(raw):
    """LAST match wins: a deliberating referee may quote both options from
    the rubric before its final verdict; the final JSON is the answer."""
    matches = VERDICT_RE.findall(raw)
    return matches[-1] if matches else None


def judge_matchup(view, transcript, referee_clients, *, tag, flip=False,
                  max_tokens=1500):
    """The 7.1 panel: masked, grouped per-side presentation, temperature 0,
    one vote per referee, majority of valid votes decides. Reading order is
    counterbalanced twice over: within the panel, referee i reads the
    blocks in alternating order (i even / i odd), and `flip` inverts the
    whole panel's assignment — callers alternate it per matchup so that
    across a panel and across matchups neither side systematically enjoys
    the first (or last) word. Returns {"votes": {client_name: vote},
    "winner": side-or-None}; winner is None on a tie or when no referee
    produced a parseable verdict — callers record it and exclude it from
    win denominators, never guess."""
    masked_view, masked_transcript = mask_for_referee(view, transcript)
    votes = {}
    for i, rc in enumerate(referee_clients):
        first = ("petitioner" if (i + int(flip)) % 2 == 0
                 else "respondent")
        msgs = referee_messages(masked_view, masked_transcript, first=first)
        # generous cap: reasoning-model referees (gpt-5.4-nano) spend
        # thinking tokens from the completion budget before the verdict
        # JSON; 30 tokens would starve them into empty completions.
        raw = rc.chat(msgs, temperature=0.0, max_tokens=max_tokens,
                      tag=f"{tag}:ref:{rc.name}")
        votes[rc.name] = parse_verdict(raw)
    valid = [v for v in votes.values() if v]
    pet = sum(1 for v in valid if v == "petitioner")
    res = len(valid) - pet
    winner = ("petitioner" if pet > res
              else "respondent" if res > pet else None)
    # flip is stored with the votes so position-bias audits read straight
    # from events.jsonl instead of reconstructing panel order from config.
    return {"votes": votes, "winner": winner, "flip": flip}


def matchup_record(case_id, evolve_side, transcript, judgment):
    """One loggable row: who argued what, who won, every vote kept."""
    return {"case_id": case_id, "evolve_side": evolve_side,
            "winner": judgment["winner"], "votes": judgment["votes"],
            "evolve_won": (judgment["winner"] == evolve_side
                           if judgment["winner"] else None),
            "transcript": [{"side": s, "text": t} for s, t in transcript]}
