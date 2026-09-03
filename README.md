<h1 align="center">Citation Under Pressure</h1>

<h3 align="center"><em>What Deployment Constraints Do to Legal Citation Integrity,<br>and What a Deterministic Checker Does Inside the Revision Loop</em></h3>

```mermaid
flowchart LR
    A["a model is asked to<br/>draft a legal brief"] --> B["under real-world pressure:<br/>a citation quota, an<br/>old-authority rule, a<br/>sanctions warning"]
    B --> C["it cites cases.<br/>do they exist? are the<br/>quotes verbatim? is the<br/>page right?"]
    C --> D["we check every citation<br/>deterministically,<br/>never with an AI judge"]
    D --> E["then put the checker inside<br/>the drafting loop and ask:<br/>does the model fix what<br/>pressure broke, or just<br/>satisfy the checker?"]
```

The short answer: pressure breaks citation integrity in the models that
are cheapest to deploy, it breaks them with almost no refusals, and when
the checker's findings are fed back, capable models satisfy it mainly
by deleting the flagged quotations rather than correcting them.

## Introduction

Courts keep sanctioning lawyers for filing briefs with citations that a
language model invented. Nearly all research on the problem works after
the fact: given a brief that already contains errors, how many can a
detector find? That is the right question for a court clerk reviewing a
filing, and the wrong one for anyone deciding whether and how to deploy
a drafting model, because it treats fabrication as a fixed property of
text rather than a behavior with causes.

This paper asks the production-side questions instead. What conditions
make a model fail at legal citation in the first place? Real users do
not prompt in the abstract; they demand a minimum number of citations,
restrict which authority is allowed, and warn about consequences. And
when a citation checker that needs no AI judgment sits inside the
drafting loop, does the model correct its work, fail to, or change the
draft so that the checker's tests pass without the quotations being
corrected?
Answering these questions took an instrument the field has said lives
only behind commercial legal databases; we built it from public data,
and it produces every primary number in the paper.

## Background: reading a legal citation

An American case citation such as *Brown v. Board of Education*, 347
U.S. 483, 495 (1954) names the parties, then the volume (347), the
reporter series (U.S., the official Supreme Court reports), and the
first page (483) where the opinion is printed. The optional second page
number (495) is the *pincite*: it points at the exact page that
supports the writer's claim. Quotations from opinions are expected to
be verbatim, and the official reporter's page boundaries, preserved in
public scans of the printed volumes, are what let a quotation be located
to its page. Rule 11 of the Federal Rules of Civil Procedure lets
district courts sanction attorneys for unwarranted filings; it is the
rule invoked in the real sanctions cases over invented AI citations,
and the one our stakes condition names (it does not govern Supreme
Court filings, which the paper says plainly). Those five terms are all
the law this repository requires.

## Abstract

Language models fabricate legal citations, and the failures that reach
courtrooms have so far been studied mainly after the fact, through
detection benchmarks and sanctions dockets. We study the production
side. Seven models spanning a capability ladder across seven vendors, from
30B open-weight to frontier, each drafted merits-brief argument
sections for 48 leakage-screened U.S. Supreme Court matters under five
deployment conditions: an unpressured baseline, a citation quota, a
restriction to pre-1970 authority, a Rule 11 sanctions warning, and all
three combined. Every citation in the resulting 1,680 drafts (1,344 of
them under some pressure) was adjudicated deterministically, with no
LLM judge anywhere in the primary measurements.

Pressure degrades citation integrity from the bottom of the ladder up.
The 30B model's citation existence falls from 0.924 to 0.773 under
combined pressure (odds ratio 0.30, corrected p < 0.001), strict
quotation accuracy falls significantly for three of the seven models
after Holm correction, and the models refused the task three times in
1,344 pressured drafts. At the top of the range (Sonnet 5, Grok 4.3,
GPT-5.4-mini) no contrast survives correction; Sonnet 5's apparent
improvement under the sanctions warning is reported as a pre-registered
null result.

A second experiment placed the checker inside the drafting loop. Under
true feedback the strongest model's strict accuracy rose from 0.471 to
0.974, and the counts show why: its scored quotations fell from 157 to
73 while its accurate quotations went from 68 to 70. The model
satisfied the checker by deleting or de-quoting the flagged passages,
and the same pattern holds for GPT-5.4-mini and DeepSeek. Nonexistent
citations, by contrast, were genuinely replaced. A scrambled-feedback
control shows that false flags lower accuracy for four of the six
models, most for the ones best at following feedback. What survives at
frontier scale is mostly real law in the wrong place: 55 percent of the
strongest model's inaccurate quotations are paraphrases of the correct
case inside quotation marks, and 626 quotations across the seven models
are verbatim passages of real opinions attributed to the wrong case.

## What the paper tests

**H1 (pressure).** Do realistic deployment constraints cause citation
failure, and does the effect depend on model capability? Pre-registered
before the full run, with one amendment recorded at freeze: the pilot
had already refuted the strong form (frontier models re-fabricating
under pressure), so the full run tests the dose-response below the
frontier and the frontier's level against a human baseline.

**H2 (the verifier loop).** When a deterministic citation checker sits
inside the drafting loop, does the model correct its drafts, fail to,
or satisfy the checker in a way the checker cannot detect?
The identification comes from a scrambled-feedback control: identical
protocol, identical number of official-looking warnings, but aimed at
items that are in fact correct. Improvement under true feedback but not
scrambled feedback proves the model uses feedback content.

The full pre-registration is [`docs/HYPOTHESES.md`](docs/HYPOTHESES.md)
(frozen 2026-08-31); post-freeze decisions are dated in
[`docs/LEDGER.md`](docs/LEDGER.md).

## Where this sits in prior work

| prior work | what it does | what it could not do, which we measure |
|---|---|---|
| LePhantomCite (COLM 2026) | detects injected citation errors in briefs | naturally occurring errors, elicited under realistic pressure; page-level pincite truth |
| Deployment-constraints study (arXiv:2603.07287) | pressure factorial for scholarly citations | the legal version, with deterministic rather than fuzzy verification, and formal statistics |
| LegalCiteBench (arXiv:2605.10186) | closed-book citation recall | quote fidelity anywhere; generation grounded in a verified database (our loop) |
| RLEF (arXiv:2410.02089) | execution feedback for code | the same protocol where the verifier is a legal citation oracle, plus the false-positive control |
| LLM-judge critiques (arXiv:2606.19544 among others) | show agreement overstates judge validity | a pre-declared calibration bar, and three documented failures against expert labels |

## Design

48 Supreme Court matters (1990 to 2020), each a leakage-screened packet
holding the question presented, the facts, and a lower-court opinion
excerpt, with the Supreme Court's own decision excluded. Each matter is
argued from an assigned side by seven models, one per vendor (Qwen3-30B,
Mistral Small, Llama-4 Maverick, DeepSeek V4 Flash, Grok 4.3,
GPT-5.4-mini, Claude Sonnet 5) at temperature 0, under five
conditions:

| condition | added instruction |
|---|---|
| baseline | none |
| quota | cite at least eight distinct case authorities |
| temporal | every authority must predate 1970 |
| stakes | this will be filed; miscited authority risks Rule 11 sanctions |
| combo | all three at once |

```mermaid
flowchart LR
    P["48 matters<br/>(leakage-screened packets)"] --> C["5 conditions"]
    C --> M["7 models"]
    M --> D["1,680 drafts"]
    D --> A["deterministic adjudication<br/>existence, verbatim quotes,<br/>page-level pincites"]
    A --> H1["Experiment 1: pressure effects<br/>(citation-level GEE, clustered by matter)"]
    D -->|combo drafts| L["verifier loop, 3 rounds max<br/>true vs scrambled feedback"]
    L --> H2["Experiment 2: what revision does"]
    A --> PV["provenance search:<br/>where does each bad quote<br/>really come from?"]
```

Every citation gets one of three labels, never two: exists, not found,
or unverifiable, so oracle coverage gaps are never counted as
fabrication. Inference is a citation-level logistic GEE clustered by
matter, with Holm correction over the eight contrasts within each
model. The quotation checker was validated before use on seeded
faults (planted genuine quotes, wrong attributions, single-word
corruptions, fabrications, formatting artifacts) at 100 of 100. The
same instrument scored 482 clean pre-ChatGPT human appellate briefs to
anchor every comparison: human lawyers reach 0.407 strict and 0.680
lenient quotation accuracy under this standard (578 scored quotations). Architecture detail and diagrams are in
[`docs/DESIGN.md`](docs/DESIGN.md).

## Results

The two experiments in one picture, then the numbers.

```mermaid
flowchart LR
    P["deployment pressure<br/>quotas, date limits,<br/>sanctions warnings"]
    V["deterministic verifier<br/>inside the drafting loop"]
    subgraph L["capability ladder"]
        direction TB
        F["frontier: unshaken by pressure"]
        M["mid-tier: citations stay real,<br/>quotation accuracy falls"]
        S["small: citations fabricated,<br/>quotations collapse, almost never a refusal"]
    end
    P --> L
    V -->|"replaces bad citations;<br/>deletes flagged quotes"| F
    V -->|"same, less completely"| M
    V -.->|"changes nothing"| S
```

### Finding 1. Pressure breaks citation integrity from the bottom up, with almost no refusals

**Table 1.** Baseline versus the combined-pressure condition. Strict
quotation accuracy is the verbatim standard, on which human lawyers
score 0.407 (lenient rate in parentheses; humans 0.680). An asterisk
marks a contrast that is significant after Holm correction within
model.

| model | quotes: baseline | quotes: combo | citations exist: baseline | citations exist: combo | temporal violations |
|---|---|---|---|---|---|
| Qwen3-30B | 0.175 (0.564) | 0.072 (0.320) * | 0.924 | 0.773 * | 20% |
| Mistral Small | 0.207 (0.608) | 0.136 (0.383) | 0.901 | 0.868 | 35% |
| DeepSeek V4 Flash | 0.281 (0.631) | 0.120 (0.436) * | 0.972 | 0.959 | 11% |
| Grok 4.3 | 0.326 (0.644) | 0.246 (0.578) | 0.981 | 0.994 | 2 of 719 |
| Sonnet 5 | 0.333 (0.622) | 0.427 (0.642) | 0.991 | 0.998 | 1 of 803 |
| Llama-4 Maverick | 0.402 (0.618) | 0.179 (0.453) * | 0.958 | 0.939 | 10% |
| GPT-5.4-mini | 0.460 (0.722) | 0.294 (0.571) | 0.981 | 0.962 | 13% |

How to read it: rows are ordered by baseline strict accuracy; going
from the baseline column to the combo column is what pressure does.
Only the 30B model's citation existence moves. Strict quotation
accuracy falls for every model but Sonnet 5, and the fall survives
correction for Qwen, DeepSeek, and Llama. Sonnet 5's numerically higher
combo rate had an uncorrected p of 0.029 and a corrected p of 0.233, so
the paper reports it as exploratory and offers a memorization
alternative (the temporal rule shifts its citations toward older,
better-memorized cases). Compliance with the pre-1970 rule is near perfect for Sonnet 5 and
Grok 4.3 and worst for Mistral, whose other figures are second-lowest.
Across the 1,344 pressured drafts there were three refusals; an eighth
model, GLM-4.7-flash, produced no output on 33 of 240 drafts, 28 of them
under combined pressure, and is reported as a stall rather than a refusal.

### Finding 2. Capable models satisfy the checker by deleting quotations, and false flags lower accuracy

**Table 2.** Up to three rounds of checker feedback on combined-pressure
drafts, 24 matters per model. "Scored" and "accurate" are quotation
counts summed over the 24 episodes at round 0 and at the final draft;
the strict rate is their ratio. The scrambled arm receives the same
number of official-looking warnings aimed at items that are correct.

| model | scored r0 to final | accurate r0 to final | strict, true feedback | strict, scrambled | clean drafts |
|---|---|---|---|---|---|
| Qwen3-30B | 186 to 188 | 16 to 16 | 0.099 to 0.107 | 0.099 to 0.093 | 0 of 24 |
| Mistral Small | 145 to 133 | 15 to 17 | 0.208 to 0.264 | 0.208 to 0.122 | 9 of 24 |
| DeepSeek V4 Flash | 211 to 47 | 28 to 19 | 0.181 to 0.645 | 0.181 to 0.153 | 21 of 24 |
| Grok 4.3 | 61 to 10 | 15 to 10 | 0.207 to 1.000 | 0.207 to 0.208 | 24 of 24 |
| Sonnet 5 | 157 to 73 | 68 to 70 | 0.471 to 0.974 | 0.471 to 0.266 | 23 of 24 |
| Llama-4 Maverick | 64 to 29 | 11 to 8 | 0.176 to 0.349 | 0.176 to 0.188 | 21 of 24 |
| GPT-5.4-mini | 65 to 39 | 28 to 29 | 0.360 to 0.719 | 0.360 to 0.241 | 22 of 24 |

Read the strict column alone and this looks like repair rising with
capability. Read the counts and it is deletion: Sonnet 5 ended with two
more accurate quotations than it started with and 84 fewer scored ones.
Told a quotation was not verbatim, the capable models removed the
quotation or its quotation marks far more often than they corrected the
words, and the 30B model changed nothing. Citation existence was
repaired for real (citation counts flat, existence up, so nonexistent
citations were replaced). The scrambled column shows that false flags
lower accuracy for five of seven models, most for Sonnet 5 and
GPT-5.4-mini, which follow feedback best. Grok 4.3 is the purest case:
it reached 1.000 with every draft clean by correcting none of its 46
flagged quotations and removing all of them. The practical reading: use
the checker as a gate on output rather than as feedback, and measure a
probabilistic detector's false-positive rate before wiring it into a
loop. A no-feedback control arm (same rounds, no checker content) shows
that revision alone lifts Sonnet 5 only to 0.595 and GPT-5.4-mini to
0.543; true feedback adds a further 0.36 for Sonnet 5 (matter-paired,
p = 0.0003) but nothing distinguishable for GPT-5.4-mini. A
per-quotation trace (`results/loop_transitions.json`) shows the
mechanism directly: of Sonnet 5's 89 flagged quotations, 4 were
corrected, 13 lost their quotation marks, and 72 were deleted; under
false feedback it removed 56 of its 68 correct quotations. A fourth
arm in which each feedback line is true or false with equal
probability (verifier precision about one half) gives the
dose-response: Sonnet 5 removed 17 correct quotations under a precise
verifier, 38 under the half-true one, 56 under an all-false one, and
18 with no feedback at all, and the half-true verifier left it within
seven points of no feedback (0.664 against 0.595). Verifier precision
is therefore a deployment requirement.

A replication of the baseline and combined drafts for twelve matters
(fresh cache, same prompts, the six original models) produced one identical
draft in 144. Existence rates agreed within 0.03 and the one
significant existence contrast kept its sign; strict quotation rates
on twelve matters moved by a median of 0.07 and up to 0.33, so the
quotation claims the paper relies on are the within-model contrasts
that survive Holm correction, never a single cell.

### Finding 3. What survives at frontier scale is misattribution, not invention

Three residual failure modes, each measured deterministically:

| failure mode | measurement | headline number |
|---|---|---|
| paraphrase wearing quotation marks | inaccurate quotes decomposed against the cited case's own text | 55% of Sonnet 5's inaccurate quotes are paraphrases of the correct case |
| right words, wrong case | corpus search for each quote's true source | 626 quotes across the seven models are real opinion passages bound to the wrong authority |
| right case, wrong page | quote located against the official reporter's page boundaries | quote sits on the cited page 77% of the time (Sonnet 5), 42 to 64% for the rest, 89% for human briefs |

These are the errors an existence check cannot see, and the page-level
measurement covers, on public data, the error class on which published
detection agents have the lowest recall: the best published detector
misses nearly half of wrong pincites (52.8% recall), and open-weight
detectors reach 19 to 51%.

### Finding 4. The one judgment call defeated every jury

Whether a real quotation actually supports its proposition cannot be
looked up, only judged, so we tried to calibrate LLM panels against
expert-labeled misrepresentations with a pre-declared bar of 0.75:

| panel | accuracy | failure mode |
|---|---|---|
| three-family budget panel, binary verdict | 0.500 | rejected everything |
| same panel, three-way verdict with abstention | 0.700 | accepted everything |
| GPT-5.4 + Sonnet 5 + Gemini 2.5 Pro, 15K-character excerpts | 0.594 | accepted everything |

No verdict from a failed panel was interpreted; relevance is a stated
limitation of the paper.

## Repository guide

This is the companion repository for the paper (JURIX 2026 submission
in [`docs/jurix/paper.tex`](docs/jurix/paper.tex); an earlier markdown
draft is in [`docs/PAPER_DRAFT.md`](docs/PAPER_DRAFT.md)). Everything
here is the real campaign: the pre-registered design, the instruments,
all 1,680 drafts and the revision episodes, the statistics, and a
ledger of every analysis decision, including the findings the project
withdrew itself after its own verification passes.

    docs/jurix/paper.tex     the paper; every number is a macro generated
                             from the results files by src/emit_macros.py
    docs/PAPER_DRAFT.md      earlier markdown draft
    docs/DESIGN.md           frozen design with architecture diagrams
    docs/HYPOTHESES.md       pre-registration (frozen 2026-08-31)
    docs/LEDGER.md           dated log of every post-freeze decision,
                             including two self-retracted findings and
                             the three jury calibration failures
    papers/                  close-reading notes on the positioning papers
    src/                     instruments and experiment drivers
    results/                 all drafts, verdicts, and tables
      rescore_full.json        definitive Experiment 1 tables
      stats_gee.json           primary citation-level inference
      rescore_loops.json       definitive Experiment 2 tables
      provenance_report.md     per-quote true-source classification
      pincites.json            page-level pincite verification
      human_baseline.json      the human yardstick
      revision_stats.json      Holm correction, raw counts, loop counts
      records.jsonl            23,002 citation-level records

## Reproducing

Scoring is deterministic and free of API calls:
`src/rescore_full.py` rebuilds the Experiment 1 tables from the
committed drafts, `src/rescore_loops.py` the Experiment 2 tables, and
the GEE in `results/stats_gee.json` runs from `records.jsonl`.
Generating new drafts requires an OpenRouter key in `.env`; every
driver is resumable, budget-capped in code, and parallelizes with
`--slice`. The citation database lives in the sibling
`us-courts-gated-evolution` repository. Large text caches are not
committed; they rebuild from free public sources (static.case.law).
