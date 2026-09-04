"""Prompt assembler — the allow-list boundary, enforced by structure.

EXPERIMENT_SETUP 5.1: agents see six packet fields and nothing else —
parties, question, facts, lower-court name, lower-court opinion text,
argument date. This module makes that a property of the code, not of
discipline: `case_view()` distills a packet into a frozen CaseView holding
ONLY those fields, and every prompt builder takes a CaseView. Bookkeeping
(SCDB ids, source URLs, hashes, match metadata) cannot reach a prompt
because nothing downstream of case_view() ever touches the packet dict.

Prompt-cache layout: providers cache a request's byte-identical prefix, so
messages are ordered stable-to-volatile — fixed system instruction (shared
by every call in the project), then case material (shared by every turn and
both sides of a matchup), then lessons, then the transcript so far, then
the current-turn ask. Only the tail changes between turns.
"""

import re
from dataclasses import dataclass

# The 5.1 allow-list. Anything not derivable from these never enters a prompt.
AGENT_VISIBLE_FIELDS = (
    "parties", "question", "facts", "lower_court_name",
    "lower_court_opinion.raw_text", "argued_date",
)

OMISSION_MARK = "\n[... middle of opinion omitted ...]\n"


@dataclass(frozen=True)
class CaseView:
    """The only case data prompts can be built from."""
    petitioner: str
    respondent: str
    question: str
    facts: str
    lower_court_name: str
    opinion_excerpt: str
    argued_date: str


def head_tail_excerpt(text, budget):
    """5.1 truncation: first 75% of the budget from the head (caption, facts,
    the majority's reasoning), last 25% from the tail (conclusion and any
    dissent — the future petitioner's roadmap, which head-only cutting would
    silently lose). Cost trim, not a safety measure; both duelists always
    see the identical excerpt."""
    text = text.strip()
    if len(text) <= budget:
        return text
    head = (budget * 3) // 4
    tail = budget - head
    return text[:head].rstrip() + OMISSION_MARK + text[-tail:].lstrip()


def case_view(packet, excerpt_chars=20_000):
    """Distill a packet dict into its agent-visible CaseView.

    excerpt_chars: 20,000 for training arguments and exams (v0.7 cost lock);
    auditions pass a smaller budget (AUDITION_EXCERPT_CHARS) — identical
    across the with-note and without-note conditions, so the paired
    comparison stays exact.
    """
    parties = packet["parties"]
    return CaseView(
        petitioner=parties["petitioner"],
        respondent=parties["respondent"],
        question=packet["question"].strip(),
        facts=packet["facts"].strip(),
        lower_court_name=packet["lower_court_name"],
        opinion_excerpt=head_tail_excerpt(
            packet["lower_court_opinion"]["raw_text"], excerpt_chars),
        argued_date=packet["argued_date"],
    )


EXAM_EXCERPT_CHARS = 20_000       # v0.7 cost lock
AUDITION_EXCERPT_CHARS = 8_000    # provisional; locked at the M2 freeze


# ---------------------------------------------------------------- advocate

# Identical in all three arms (so it cannot confound the comparison), and it
# requires citation-grounded argument — every legal proposition supported by
# cited authority — which guarantees every argument yields checkable
# material for the honesty checks (v0.6 item 2).
SYSTEM_ADVOCATE = """\
You are an experienced appellate advocate arguing before the Supreme Court \
of the United States. You will be told which party you represent.

Rules of argument:
1. Support every legal proposition with cited authority. Cite cases in \
full citation format (for example: Smith v. Jones, 490 U.S. 100 (1989)).
2. When you quote a source, quote it exactly and attribute it to its \
citation. Use quotation marks only for verbatim quotations.
3. Argue as of the argument date you are given. Rely only on authority \
that existed on that date.
4. Be concrete: engage the record facts, the question presented, and the \
lower court's reasoning. Address opposing counsel's strongest points \
directly.
5. Write in clear prose, no headings or bullet lists, at most 700 words \
per turn."""

TURN_ASK = {
    "opening": "Write your opening argument for the {role}.",
    "rebuttal": ("Write your rebuttal for the {role}. Answer opposing "
                 "counsel's strongest arguments directly."),
    "closing": ("Write your closing argument for the {role}. Consolidate "
                "your strongest points and address what remains of "
                "opposing counsel's case."),
}

ROLE = {"petitioner": "petitioner", "respondent": "respondent"}


def case_block(view):
    """The stable case-material block — byte-identical for every turn and
    both sides of a matchup, so providers cache it as a shared prefix."""
    return (
        f"CASE FOR ARGUMENT\n"
        f"Petitioner: {view.petitioner}\n"
        f"Respondent: {view.respondent}\n"
        f"Argument date: {view.argued_date}\n"
        f"Court below: {view.lower_court_name}\n\n"
        f"QUESTION PRESENTED\n{view.question}\n\n"
        f"BACKGROUND\n{view.facts}\n\n"
        f"OPINION UNDER REVIEW ({view.lower_court_name})\n"
        f"{view.opinion_excerpt}"
    )


def lessons_block(lessons):
    if not lessons:
        return ""
    body = "\n\n".join(f"Lesson {i}: {t}" for i, t in enumerate(lessons, 1))
    return ("\n\nNOTES FROM YOUR PAST CASES\n"
            "You have argued before. These are lessons you recorded; apply "
            "them where they help.\n" + body)


def transcript_block(transcript):
    if not transcript:
        return ""
    parts = []
    for side, text in transcript:
        parts.append(f"--- Argument by counsel for the {ROLE[side]} ---\n"
                     f"{text.strip()}")
    return "\n\nARGUMENT SO FAR\n" + "\n\n".join(parts)


def advocate_messages(view, side, turn, transcript=(), lessons=()):
    """Chat messages for one advocate turn.

    side: "petitioner" | "respondent"
    turn: "opening" | "rebuttal" | "closing"
    transcript: prior turns as (side, text) pairs, oldest first
    lessons: retrieved notebook lesson texts (empty for arm A0 and for the
             frozen reference advocate)
    """
    if side not in ROLE:
        raise ValueError(f"unknown side: {side}")
    role = ROLE[side]
    user = (
        case_block(view)
        + lessons_block(list(lessons))
        + transcript_block(list(transcript))
        + f"\n\nYOUR TASK\nYou are counsel for the {role}. "
        + TURN_ASK[turn].format(role=role)
    )
    return [{"role": "system", "content": SYSTEM_ADVOCATE},
            {"role": "user", "content": user}]


# -------------------------------------------------------------- reflection

# 6.1 phase 2: at most one candidate lesson per case. Rewritten at the M2
# freeze window: the pilot's blind panel graded 42/42 lessons produced by
# the earlier prompt as case-specific doctrine, 42/42 unlikely to help an
# unrelated case — the agent was summarizing the case it just argued, not
# extracting skill. This version demands TECHNIQUE over content and adds
# the both-sides study (the adversarial channel: same transcript, zero
# extra calls — study the winning side's craft, not just your own plan).
# v3 (the opened loop): notes are VERIFIED AUTHORITY MEMORY. The v1
# post-mortem showed doctrine-from-memory poisons (44% fabricated); the
# v2 post-mortem showed craft-from-self-play is inert (placebo-equal).
# The one authentic input stream is the source materials themselves —
# each training case delivers a real opinion full of real authority. A
# v3 note banks one usable authority FROM those materials, with an exact
# quote — which makes it mechanically verifiable at the gate: the quote
# must appear in the source text, the citation must resolve as real.
SYSTEM_REFLECT = """\
You are the same appellate advocate, closing your case file. From the \
OPINION UNDER REVIEW above, bank the single most useful authority for \
future cases — a precedent or rule the opinion relies on that you could \
deploy again.

Write your note in exactly this form:
ISSUE: the kind of dispute where this authority helps (one line).
AUTHORITY: the case in full citation format, exactly as the opinion \
cites it.
QUOTE: the key passage, copied EXACTLY, word for word, from the opinion \
text above — in quotation marks. Do not paraphrase inside the quotation \
marks; a single changed word makes the note worthless.
USE: one sentence on how to deploy it.

Bank only authority that appears in the materials above. If the opinion \
contains no authority worth banking, reply with exactly: NO LESSON"""


def reflect_messages(view, transcript):
    user = (case_block(view)
            + transcript_block(list(transcript))
            + "\n\nYOUR TASK\nWrite the one lesson, or NO LESSON.")
    return [{"role": "system", "content": SYSTEM_REFLECT},
            {"role": "user", "content": user}]


# Template-echo markers. Any ONE can occur in a legitimate lesson
# ("situations like X-ray searches", a party initial "because Z. moved") —
# so a lesson is rejected only when at least two markers co-occur, which is
# the signature of the parroted template, not of real content.
PLACEHOLDER_MARKS = [re.compile(p, re.I) for p in
                     (r"situations? like x\b", r"tactic y\b",
                      r"because z\b")]
PLACEHOLDER_HARD = re.compile(r"\[insert", re.I)


def parse_lesson(raw):
    """None if the agent declined or echoed template placeholders;
    otherwise the lesson text."""
    text = raw.strip()
    if not text or "NO LESSON" in text[:40].upper():
        return None
    if PLACEHOLDER_HARD.search(text):
        return None
    if sum(bool(p.search(text)) for p in PLACEHOLDER_MARKS) >= 2:
        return None
    return text


# ----------------------------------------------------------------- referee

# Referees judge a finished matchup: which side's counsel argued better.
# Three blindfolds (7.1): advocate identities never shown; party names
# masked by the caller; and the two sides' arguments are presented as
# GROUPED per-side blocks whose order the caller alternates — models
# slightly favor whatever they read first (and last), and the M1 smoke
# measured exactly that: with an interleaved transcript, where the
# respondent always speaks last, one referee voted respondent 12 out of
# 12 times. Grouping the turns per side is what makes order something we
# CAN counterbalance; an interleaved dialogue has only one honest order.
# Callers run referees at temperature 0.
SYSTEM_REFEREE = """\
You are judging a moot-court argument between two appellate advocates. \
Each side's turns (opening, rebuttal, closing) are shown together as one \
block; the order of the two blocks carries no meaning. Decide which \
side's counsel made the stronger legal argument — responsiveness to the \
question presented, use of authority, logical coherence, and how well \
each side answers the other's points. Judge advocacy quality only; \
do not decide which side ought to win the case on the merits, and do not \
reward confident assertion unsupported by authority.

Answer with exactly one JSON object on a single line: \
{"stronger": "petitioner"} or {"stronger": "respondent"}. No other text."""


def side_block(transcript, side):
    turns = [t for s, t in transcript if s == side]
    body = "\n\n".join(f"[Turn {i}]\n{t.strip()}"
                       for i, t in enumerate(turns, 1))
    return (f"=== ARGUMENT OF THE {ROLE[side].upper()} "
            f"({len(turns)} turns) ===\n{body}")


def referee_messages(view, transcript, first="petitioner"):
    """Chat messages for one referee read. `first` sets which side's block
    the referee reads first — callers alternate it (7.1)."""
    second = "respondent" if first == "petitioner" else "petitioner"
    user = (
        f"QUESTION PRESENTED\n{view.question}\n\n"
        f"BACKGROUND\n{view.facts}\n\n"
        + side_block(transcript, first) + "\n\n"
        + side_block(transcript, second)
        + "\n\nWhich side's counsel argued better? Answer with the JSON "
          "object only."
    )
    return [{"role": "system", "content": SYSTEM_REFEREE},
            {"role": "user", "content": user}]
