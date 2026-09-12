<h1 align="center">Citation Under Pressure</h1>

<h3 align="center"><em>Deployment Constraints, Legal Citation Integrity,<br>and the Limits of Deterministic Verification</em></h3>

```mermaid
flowchart LR
    A["a model is asked to<br/>draft a legal brief"] --> B["under real-world pressure:<br/>a citation quota, an<br/>old-authority rule, a<br/>sanctions warning"]
    B --> C["it cites cases.<br/>do they exist? are the<br/>quotes verbatim? is the<br/>page right?"]
    C --> D["we check every citation<br/>deterministically,<br/>never with an AI judge"]
    D --> E["then put the checker inside<br/>the drafting loop and ask:<br/>does the model fix what<br/>pressure broke, or just<br/>satisfy the checker?"]
```

## In one paragraph

The short answer, in three parts. Under deployment constraints the
failure mode moves with capability: the smallest model fabricates
citations, the middle of the range misquotes and loses correct quotations per
draft, and the strongest model's quotation rate holds, most plausibly
because it quotes less, while its residual errors are paraphrase in
quotation marks, real language from the wrong case, and wrong pages. Verification is not repair: fed the checker's
findings, a capable model reaches a perfect measured score by deleting
what was flagged (Sonnet 5 repaired 3 of 35 flagged quotations and
deleted 30), and an imprecise verifier makes it delete correct
quotations too (43 of 69 under all-false flags, 21 under 50 percent
precision, which is what revision with no verifier at all removes, 4
under a precise one); counted over every episode, correct quotations
per draft rose for one model of seven. Both experiments make one point: a
model can raise an observable correctness rate by changing what it
exposes to the check, so a rate has to be read beside the count of
correct items it is computed over.

> **The point in one sentence.** Optimizing an observable correctness
> metric can change what the model chooses to expose to that metric
> instead of improving the underlying capability. Under pressure the
> strongest model quotes less; under feedback it deletes what was
> flagged; in both cases the measured rate rises and the count of
> correct quotations does not.
>
> In the paper's notation, for a draft $d$ with scored quotations $S_d$
> and $K_d$ accurate ones among them, the observed rate is
>
> $$R_d = \frac{K_d}{|S_d|},$$
>
> and a model can raise $R_d$ by shrinking $|S_d|$ as well as by raising
> $K_d$. Under pressure the strongest model quoted less ($|S_d|$ down,
> $K_d$ flat); under feedback every model deleted what was flagged
> ($|S_d|$ down, $K_d$ flat or lower). A rising $R_d$ therefore does
> not imply more correct output, and an evaluation that scores only what
> a system chooses to emit should report $K_d$ beside $R_d$.

Courts keep sanctioning lawyers for filing briefs with citations that a
language model invented, and nearly all research on the problem works
after the fact: given a brief that already contains errors, how many
can a detector find? That is the right question for a court clerk and
the wrong one for anyone deciding whether and how to deploy a drafting
model, because it treats fabrication as a fixed property of text when
it is a behavior with causes. This paper asks the production-side
questions instead: what conditions make a model fail at legal citation
in the first place, and what does the model do when a checker that
needs no AI judgment tells it where it failed? Answering them took an
instrument the field has said lives only behind commercial legal
databases; we built it from public data, and it produces every primary
number in the paper. The paper is the JURIX 2026 submission in
[`docs/jurix/paper.tex`](docs/jurix/paper.tex); this README is its
companion and carries the same numbers.

## Results at a glance

| claim | the one number | where |
|---|---|---|
| No one failure mode covers the seven | the 30B model's reporter-coordinate existence falls from 0.924 to 0.773 under combined pressure, and it is the only model whose existence moves in the primary fit; strict quotation accuracy falls significantly for three of seven models, only two of them under both prompt templates; accurate quotations per draft fall significantly for six of the seven across the two templates, two of them at the top of the range; Sonnet 5, which escapes all three, sees its rate rise from 0.527 to 0.649 while its quotations per draft fall from 9.6 to 6.1 | Finding 1, Figures 1 and 4 |
| Verification is not repair | under precise flags Sonnet 5 repaired 3 of 35 flagged quotations and deleted 30, reaching a measured 1.000 over what it kept; correct quotations per draft rose for one model of seven; at 50 percent verifier precision it removed 21 of its 69 correct quotations, as many as revision with no feedback (21), and 43 under all-false flags | Finding 2, Figures 2 and 3 |
| What survives at the top is misattribution | 68 percent of Sonnet 5's inaccurate quotations are paraphrases of the correct case in quotation marks, and 317 quotations across the models are real opinion passages bound to the wrong case | Finding 3 |

```mermaid
flowchart LR
    P["deployment pressure<br/>quotas, date limits,<br/>sanctions warnings"]
    V["deterministic verifier<br/>inside the drafting loop"]
    subgraph L["capability ladder"]
        direction TB
        F["frontier: rate holds because it quotes less;<br/>residue is paraphrase, wrong case, wrong page"]
        M["mid-tier: citations stay real,<br/>quotation accuracy falls"]
        S["small: citations fabricated,<br/>quotations collapse, almost never a refusal"]
    end
    P --> L
    V -->|"deletes flagged quotes (30 of 35);<br/>with the passage in the flag, repairs 13"| F
    V -->|"deletes or dequotes most flags"| M
    V -.->|"leaves most flags standing"| S
```

## Finding 1. No one failure mode covers the seven

Seven models, one per vendor, drafted argument sections for 48 Supreme
Court matters under five conditions: a baseline, a citation quota, a
restriction to pre-1970 authority, a Rule 11 sanctions warning, and all
three combined. Every citation in the 1,680 drafts was adjudicated
deterministically. Table 1 gives the baseline and combined cells; the
Method section below explains the labels and the standard.

**Table 1.** Baseline versus the combined-pressure condition. Strict
quotation accuracy is the alteration-aware verbatim standard, over
attributed quotations only, on which human lawyers score 0.610 (lenient
rate in parentheses; humans 0.788), with the scored quotations in
brackets; existence cells carry citations not found over adjudicable
citations. An asterisk marks a contrast that is significant after Holm
correction within model.

| model | quotes: baseline | quotes: combo | citations exist: baseline | citations exist: combo | temporal violations (temporal condition) |
|---|---|---|---|---|---|
| Qwen3-30B | 0.179 (0.607) [229] | 0.061 (0.322) [326] * | 0.924 [28/370] | 0.773 [90/397] * | 20% (60 of 307) |
| Mistral Small | 0.255 (0.620) [184] | 0.164 (0.455) [244] | 0.901 [37/373] | 0.868 [69/521] | 35% (141 of 401) |
| DeepSeek V4 Flash | 0.383 (0.733) [251] | 0.149 (0.491) [281] * | 0.972 [10/354] | 0.959 [20/488] | 11% (40 of 356) |
| Grok 4.3 | 0.480 (0.757) [152] | 0.302 (0.647) [119] | 0.981 [5/257] | 0.994 [3/479] | 0 of 240 |
| Sonnet 5 | 0.527 (0.802) [258] | 0.649 (0.820) [194] | 0.991 [3/318] | 0.998 [1/450] | 0 of 353 |
| GPT-5.4-mini | 0.583 (0.819) [127] | 0.466 (0.693) [88] | 0.981 [8/417] | 0.962 [27/713] | 13% (68 of 519) |
| Llama-4 Maverick | 0.588 (0.784) [51] | 0.230 (0.557) [61] * | 0.958 [9/213] | 0.939 [31/506] | 10% (22 of 213) |

![Figure 1: strict quotation accuracy and reporter-coordinate existence by condition, one line per model, human floor dotted](docs/figures/fig1_pressure.png)

### Existence falls at the bottom

Going from the baseline column to the combo column is what pressure
does. **Only the 30B model's reporter-coordinate existence moves**: from 0.924 to
0.773 under combined pressure (odds ratio 0.30, corrected p < 0.001),
with the quota, temporal, and combined contrasts all significant after
correction. Each of its surviving existence contrasts rests on at least
28 citations not found per arm. A record is one occurrence of a full
citation and short forms are not counted, and refitting on distinct
authorities per draft (`src/gee.py --distinct`) leaves the same eight
contrasts surviving. Mistral Small's existence goes from 0.901 to 0.868
without reaching significance, and every other model stays at 0.939 or
above in both columns.

### Quotation accuracy falls in the middle

**Strict quotation accuracy falls for every model but Sonnet 5**, and
the fall survives correction for Llama-4 and Qwen3-30B under the
temporal and combined conditions and for DeepSeek under the combined
condition. Llama-4 shows the
largest drop, from 0.588 at baseline to 0.230 under combined pressure.
Once three generations are pooled the combined fall survives for six of
seven models. **The date clause both degrades quoting and moves the model onto harder
authority.** Comparing eras inside the baseline cell cannot separate the
two, because there the old cases are the ones the model chose. Adjusting
for the cited opinion's decision year does (`src/era_strata.py`), with
one caveat that matters: the clause *sets* that year, so it is a
mediator rather than a confounder, and the fit decomposes the effect
rather than removing a bias. Odds ratios are also not collapsible, so
part of the movement is mechanical. Pooled over models with a model
effect on the 3,644 dated scored quotations, the temporal clause's odds
ratio moves from 0.62 to 0.768 (p 0.035) once decision year enters, and
the combined condition's from 0.557 to 0.682 (0.530 to 0.879, p 0.003),
removing 45 and 35 percent of the log-odds effect respectively. The
assumption-light alternative disagrees: bucketing into pre- and
post-1970 still leaves the arms twelve years apart in median, and inside
the bucket neither pooled contrast survives Holm correction (combined
0.099). Descriptively, only 24
percent of the temporal arm's scored quotations cite an authority the
model also cites at baseline, and those score 0.409 against the
baseline's 0.397 while the rest score 0.252 (combined: 19 percent,
0.457, 0.194); that split conditions on a choice the treatment causes,
so it describes the mechanism rather than testing it.

### The rate is conditional on quoting, so the count is tested too

Scored quotations per cell run from 42 to 326 and the unpaired share
from 15 to 50 percent, so every rate in Table 1 is conditional on
quoting. The count of accurate quotations per draft is therefore
tested as an outcome of its own (`src/count_outcome.py`, post hoc:
Wilcoxon paired by matter, n = 48, Holm within model). **It falls from
baseline to combined for all seven models, and the fall survives
correction for eight contrasts in five models**, all under the temporal
or combined clause: Qwen3-30B, DeepSeek (2.00 to 0.88 per draft), Llama-4 (0.62 to
0.29), and two models whose rate contrasts never survived, GPT-5.4-mini
(1.54 to 0.85, corrected p 0.033) and Grok 4.3 (1.52 to 0.75, corrected
p 0.011). A lawyer reading the draft gets fewer correct quotations under
pressure even where the rate does not move.

The same test on the second prompt template (`src/count_outcome.py
--records records_para.jsonl --out count_outcome_para.json`) replicates
the direction and not the per-model attribution. The contrast keeps its
sign in 20 of the 26 tests that have one on both templates (two of the
28 are exactly zero on one); six of the eight first-template survivors
fall again; the second template has eight Holm survivors of its own, in four
models, one of which, Mistral Small, shows nothing on the first; and
across the two templates six of the seven models lose correct quotations
under some clause. Llama-4, whose fall is the largest on the first
template, does not reproduce it on the second. So the finding to carry
away is that pressure costs a draft correct quotations, not that any
particular model is the one it happens to.

### The strongest model's rate holds, most plausibly because it quotes less

Sonnet 5's combo rate is numerically higher than its baseline rate
(0.527 to 0.649, uncorrected p 0.025, corrected 0.201), a contrast that
reaches no fit. It wrote 9.6 quotations per draft at baseline and 6.1
under combined pressure; its accurate quotations per draft held (2.83
to 2.62, p 0.579) while its inaccurate ones fell (2.54 to 1.42), so the
quotations it stopped writing were disproportionately the ones that
would have failed. **Selection, fewer and safer quotations, is the
leading reading**; which quotations were dropped, by length or case age,
is not tested. The temporal rule also shifts its citations toward
older, better-memorized cases (median decision year 1943 against
1986). On the appellate task its rate rises under the sanctions warning
alone (0.475 to 0.624, corrected p 0.057), and that rise survives only
the pooled-task fit (odds ratio 1.59, corrected p 0.009).

![Figure 4: Sonnet 5's quotations per draft, accurate quotations per draft, and strict rate by condition](docs/figures/fig4_selection.png)

### Compliance and refusals

Compliance with the pre-1970 rule is perfect for Sonnet 5 and Grok 4.3
and worst for Mistral Small, whose other figures are second-lowest.
Across the 1,344 pressured drafts there are no refusals. Nothing in the
seven-model run declines the task, under the sanctions clause or any
other, so no draft leaves a rate on that ground and all 1,344 are
scored. Two drafts stop under 100 words, DeepSeek on 2010-065 and
GPT-5.4-mini on 2000-087, both under the sanctions clause; reading them
shows arguments cut off mid-sentence rather than refusals, and they are
scored as they stand. This matters more than the count suggests, because
a refusal is the limiting case of the denominator argument this paper
makes: a system that declines to answer scores no errors. That route is
simply not what these models took. An eighth model, GLM-4.7-flash,
produced no output on 33 of 240 drafts, 28 of them under combined
pressure; it is counted as a stall, excluded from the paper, and is not
a refusal either.

> **Takeaway.** Reliability at a neutral prompt does not predict
> reliability under drafting constraints, and the failure changes kind
> with capability: nonexistent citations at 30B, misquotation in the
> middle, and at the top a rate that holds, most plausibly because the
> model quotes less, with paraphrase, misattribution, and wrong pages
> left behind.

## Finding 2. Verification is not repair

Combined-condition drafts entered a revision loop: each round the
checker returned one line per failure, the model revised, and the loop
ended on a clean draft or after three revisions. A scrambled-feedback
control gave the same number of identically formatted lines aimed at
items that were correct, mixed controls set the verifier's precision to
about 0.25, 0.5, or 0.75, and a no-feedback control gave the same
rounds with no checker content. The loop ran on 24 matters per model,
and was rerun in full after the attribution rule was corrected (see the
audit below), so every flag here came from the corrected checker.

**Table 2.** Up to three rounds of checker feedback on combined-pressure
drafts, 24 matters per model. "Scored" and "accurate" are quotation
counts summed over the 24 episodes at round 0 and at the final draft;
the strict rate is the mean over drafts with a quotation left to score.
Clean episodes are split into those that ended on a passing draft with
quotations and those that ended on a draft emptied of them.

| model | scored r0 to final | accurate r0 to final | strict, true feedback | strict, scrambled | clean drafts (with quotations, by deletion) |
|---|---|---|---|---|---|
| Qwen3-30B | 151 to 160 | 12 to 12 | 0.089 to 0.092 | 0.089 to 0.121 | 0 of 24 |
| Mistral Small | 106 to 89 | 14 to 18 | 0.238 to 0.354 | 0.238 to 0.116 | 10 of 24 (3, 7) |
| DeepSeek V4 Flash | 165 to 34 | 31 to 29 | 0.301 to 0.958 | 0.301 to 0.228 | 23 of 24 (11, 12) |
| Grok 4.3 | 50 to 10 | 13 to 10 | 0.234 to 1.000 | 0.234 to 0.275 | 24 of 24 (5, 19) |
| Sonnet 5 | 104 to 68 | 69 to 68 | 0.743 to 1.000 | 0.743 to 0.591 | 24 of 24 (23, 1) |
| Llama-4 Maverick | 44 to 9 | 11 to 9 | 0.273 to 1.000 | 0.273 to 0.111 | 24 of 24 (6, 18) |
| GPT-5.4-mini | 53 to 29 | 31 to 27 | 0.538 to 0.857 | 0.538 to 0.536 | 20 of 24 (11, 9) |

### Deletion, not correction

**Read the strict column alone and this looks like repair rising with
capability. Read the counts and it is deletion**: Sonnet 5 ended with 68
of the 69 accurate quotations it started with and 36 fewer scored ones,
and 68 of the 168 true-feedback episodes ended with nothing left to
score, 19 of Grok 4.3's 24, so its final 1.000 rests on five drafts.
Told a quotation was not verbatim, every model but Qwen3-30B, which
left most flags standing, and Mistral Small, which left nearly half (44
of 92), removed the quotation or its quotation marks far more often
than it corrected the words. **Dequoting is not deletion**: the words
stay and the citation stays in 100 of the 103 dequoted quotations, so
for a passage that is really a paraphrase, dropping the marks is the
lawyer's correct fix. Counting dequoting as repair, deletion still
exceeds it for six of seven models under bare flags and four of seven
under the passage arm; Grok 4.3 is the exception, dequoting 23 of its
37 flags and deleting 14. Counted over all 24 episodes of the arm,
the intent-to-treat measure, accurate quotations per draft rose only
for Mistral Small (0.58 to 0.75) and were flat or lower for the other
six (Sonnet 5 2.88 to 2.83, Grok 4.3 0.54 to 0.42): the loop raised the
rate over surviving quotations, not the number of correct ones in a
draft. Grok
4.3 is the purest case: every one of its 24 episodes ended clean, and of
its 37 flagged quotations it corrected none, dequoted 23, and deleted
14.

A per-quotation trace (`results/loop_transitions.json`) shows the
mechanism directly. Of Sonnet 5's 35 flagged quotations, 1 was
corrected in place and 2 replaced by a new accurate quotation from the
same case, 2 lost their quotation marks, 30 were deleted, and none was
left. Only 4 of its 69 accurate quotations went, against 21 under
revision with no feedback, so precise flags made it more careful with
correct material. **The practical reading: use the checker as a gate on
output, since bare feedback invites deletion, and measure a
probabilistic detector's false-positive rate before wiring it into a
loop.**

![Figure 3: what each model did with the quotations the checker flagged, bare flag against passage in the flag](docs/figures/fig3_repair.png)

### A false flag deletes correct work

The scrambled column of Table 2 shows that false flags lower accuracy
for five of seven models, most for Sonnet 5 and Llama-4; under
all-false feedback Sonnet 5 removed 43 of its 69 correct quotations.
Mixed arms in which each feedback line is true with probability
$\pi = 0.25$, $0.5$, or $0.75$ give the dose-response: Sonnet 5 removed
4, 9, 21, 28, and 43 of its 69 correct quotations as the verifier
precision $\pi$ fell from 1 to 0
(21 with no feedback at all), and its final accuracy fell 1.000, 1.000,
0.956, 0.830, 0.591 with it. **These labels are nominal**: they are the share of feedback lines
drawn from the checker, whose own flags are right 65 to 78 percent of
the time depending on which of the two hand readings you take, so
realised precision is roughly two-thirds to four-fifths of the label. The arms
also replace true lines rather than adding false ones, so recall falls
with precision, and because the loop stops on a clean draft they differ
in rounds executed too (2.47 under true feedback against 3.21 under
false). **Holding rounds fixed keeps the series and moves the crossing**
(`src/rounds_control.py`): pooled over models, removals per
episode-round run 0.048, 0.090, 0.145, 0.150, and 0.200 against 0.109
with no feedback, and after exactly one round, where every arm has had
one opportunity, 10, 15, 25, 31, and 32 percent of the 181 accurate
quotations are gone against 23 percent. On both bases revision with no feedback sits between
precision 0.75 and 0.5, interpolating to **0.56 to 0.66 nominal, or 0.37
to 0.52 realised** once you allow that a "true" line is right only as
often as the checker is (65 to 78 percent). Below that a verifier
destroys more correct work than leaving the model alone. The realised
interval is widened by the readers' disagreement, not narrowed: 0.37
comes from the pessimistic reading and 0.52 from the optimistic one.
Because the audited rule is worse than the rule now shipped, the
realised crossings are lower bounds, and because the
arms lower recall along with precision the number bounds a loop of this
shape rather than precision on its own. On the accurate side the checker was audited at 0 of 40
verdicts wrong, an upper bound near 9 percent on the 69 correct
quotations these counts run over; under
the lenient verdict (near misses counted as correct) only all-false
feedback leaves Sonnet 5 below revision alone (0.873 against 0.880).
**Verifier precision is therefore a deployment requirement.**

![Figure 2: final strict accuracy and share of correct quotations removed against verifier precision, one line per model](docs/figures/fig2_repair.png)

The no-feedback control separates feedback content from revision
itself. Revision alone lifts Sonnet 5 only to 0.796 and GPT-5.4-mini to
0.714; true feedback adds a further 0.20 for Sonnet 5 (matter-paired
over matters scored in both arms, interval 0.11 to 0.31, p 0.003) and
0.39 for DeepSeek (0.20 to 0.58, p 0.012), while GPT-5.4-mini's,
Qwen3-30B's, and Mistral Small's differences (0.04, 0.02, 0.05) are
within noise and Llama-4 and Grok 4.3 left too few paired matters to
test.

### Evidence in the flag helps, and removal still wins

Because a closed-book model cannot consult the opinion it is told it
misquoted, the true-feedback loop was rerun from the grounded
combined-condition drafts of Sonnet 5 and DeepSeek with the verbatim
excerpts of the ten retrieved authorities kept in the prompt
(`src/loop_arm.py --grounded`, `results/gloop_transitions.json`).
Repair, in place or by a replacement quotation on the same citation,
stayed at 3 of Sonnet 5's 20 flags and 1 of DeepSeek's 47, against 3 of
35 and 2 of 134 closed-book, with removal still the majority response.

A passage arm then put the evidence in the flag itself: each quotation
line carried the closest passage of the cited opinion, found by the same
window search the retrieval arm uses (`--arms passage`). Repair rose in
six of seven models (Grok 4.3 still repaired none): to 13 of 35 for
Sonnet 5 (3 in place, 10 replaced by the supplied passage) against 22
deleted or dequoted, to 27 of 92 for Mistral Small against 4 under bare
flags, to 25 of 139 for Qwen3-30B against none, and to 12 of 134 for
DeepSeek, which still removed 122. Almost all of it came by replacement,
and removal exceeded repair in every model. Final strict rates under the
passage arm were 1.000 for Sonnet 5 and 1.000 for DeepSeek over more
surviving quotations (83 scored against 68 for Sonnet 5). **A loop
should hand the model the passage; even then it removes more than it
repairs.**

### Existence rises the same way

The existence rise under true feedback is also removal
(`results/loop_citations.json`). Of the 113 citations that did not
resolve at round 0 across the seven models, 82 were gone from the final
draft and 31 remained, while 37 new resolving citations appeared, 17 of
them Mistral Small's.

> **Takeaway.** A verifier in the loop makes the draft pass the
> verifier. Told a quotation is wrong, a capable model deletes it far
> more often than it fixes it; told a correct quotation is wrong, it
> deletes that too. Supplying the source passage raises repair in six of
> seven models and still leaves removal in the majority. Verification is
> not repair, and the checker belongs at the gate, in front of a person.

## Finding 3. What survives at the top of the range

Three residual failure modes remain for the strongest models, each
measured deterministically.

| failure mode | measurement | headline number |
|---|---|---|
| paraphrase wearing quotation marks | inaccurate quotes (verdict `inaccurate`, not the wider set of strict failures) decomposed against the cited case's own text | 68% of Sonnet 5's 248 inaccurate quotes (169) are paraphrases of the correct case; 56 match nothing in it and 23 cite authority outside the U.S. Reports |
| right words, wrong case | search of the 62,049 cached U.S. Reports opinions for each quote's true source (`src/provenance.py --corpus cap`) | 317 quotes across the seven models (72 of Sonnet 5's) are real opinion passages bound to the wrong authority; 134 have the true source cited in the same draft; the same search finds 6 of Sonnet 5's 248 inaccurate verdicts (2.4%) to be the checker's own error, and a hand reading of 160 inaccurate verdicts, made under the rule before the two corrections of 2026-09-05, finds 35 on the checker's side (22 percent, interval 16 to 29) |
| right case, wrong opinion | which part of the record holds the quotation, from the Caselaw Access Project's structural markers (`src/opinion_part.py`) | of the 1,578 accurate quotations it can place, 73% of those scored accurate, 39 sit outside the Court's own opinion (20 concurrence, 11 dissent, 8 syllabus) and 33 of those, 2.1% of the placed, carry nothing in the draft saying so; the archives hold majority, concurrences, dissents, and head matter in one record, so quoting a dissent as the Court passes the verbatim check |
| right case, wrong page | quote located against the official reporter's page boundaries, any page a cited range names counting as cited | quote sits on a cited page 85% of the time (Sonnet 5), 52 to 67% for the rest (n = 42 to 262 per model), 90% for human briefs (n = 41); 9% of the rest sit on an adjacent page |

These are the errors an existence check cannot see, and the page-level
measurement covers, on public data, the error class on which published
detection agents have the lowest recall: the highest-recall published
detector misses nearly half of wrong pincites (52.8% recall), and
open-weight detectors reach 19 to 51%. A second agent in the same
benchmark reaches 76.1% precision against that one's 40.8%, and leads on
F1, so which detector is "best" depends on the axis, and the two would
behave very differently inside a revision loop.

> **Takeaway.** At the top of the range the citations exist and the
> words are real; what fails is the binding of words to case and page.
> An existence benchmark scores these drafts as clean.

## Finding 4. Relevance defeated every jury

Whether a real quotation actually supports its proposition cannot be
looked up, only judged, so we tried to calibrate LLM panels against
expert-labeled misrepresentations with a pre-declared bar of 0.75.

| panel | accuracy | failure mode |
|---|---|---|
| three-family budget panel, binary verdict | 0.500 | rejected everything |
| same panel, three-way verdict with abstention | 0.700 | accepted everything |
| GPT-5.4 + Sonnet 5 + Gemini 2.5 Pro, 15K-character excerpts | 0.594 | accepted everything |

No verdict from a failed panel was interpreted; relevance is a stated
limitation of the paper.

> **Takeaway.** Everything this paper measures has a deterministic
> answer. The one question that does not, whether a real and correctly
> quoted case supports the proposition, is left open; no judge that
> failed calibration answers it.

## Method

Everything below is the machinery behind the findings: what the models
were given, how every citation was adjudicated, how the statistics were
run, and how the human reference was scored.

### Reading a legal citation

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

### Matters and conditions

The matters are 48 Supreme Court cases from 1990 to 2020, each a
leakage-screened packet holding the question presented, the facts, and
a lower-court opinion excerpt, with the Supreme Court's own decision
excluded. They were drawn this way: from the SCDB rows with a term
between 1990 and 2020, an argued decision type, a clean outcome, a
docket, and Oyez question-and-facts material, a decade-stratified sample
of 600 was taken under seed 20260723, shuffled under seed 20260724, and
split into dev, stream, and spares; these 48 are the first 48 of dev in
manifest order. The stratification applies to the 600, not to the head
of the shuffle, which is why the realised decades are uneven at 14, 8,
20, and 6. The selection code is `scripts/select_experiment_cases.py`
and `src/pipeline/select_pilot_cases.py` in the companion repository,
and the manifest is `data/manifests/final_sets.json` here. Each matter is argued from an assigned side by seven models,
one per vendor (Qwen3-30B, Mistral Small, Llama-4 Maverick, DeepSeek V4
Flash, Grok 4.3, GPT-5.4-mini, Claude Sonnet 5) at temperature 0, under
five conditions.

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

The two hypotheses were pre-registered before the full run
([`docs/HYPOTHESES.md`](docs/HYPOTHESES.md), frozen 2026-08-31), with
one amendment recorded at freeze: the pilot had already refuted the
strong form of H1 (frontier models re-fabricating under pressure), so
the full run tests the dose-response below the frontier and the
frontier's level against a human baseline. H2 asks whether a model
given a deterministic checker's findings corrects its drafts, fails to,
or satisfies the checker in a way the checker cannot detect; the
identification comes from the scrambled-feedback control, since
improvement under true feedback but not scrambled feedback shows the
model uses feedback content. Post-freeze decisions are dated in
[`docs/LEDGER.md`](docs/LEDGER.md). Architecture detail and diagrams
are in [`docs/DESIGN.md`](docs/DESIGN.md).

### Adjudication

For a draft $d$ let $C_d$ be its citation records, $A_d \subseteq C_d$
the *adjudicable* ones (labelled exists or not found), $Q_d$ its
quotations, and $S_d \subseteq Q_d$ the *scored* ones, those the draft
attributes to a case whose text the checker holds. The outcomes are

$$E_d = \frac{|\{c \in A_d : \text{exists}\}|}{|A_d|}, \qquad
R_d = \frac{|\{q \in S_d : \text{accurate}\}|}{|S_d|}, \qquad
K_d = |\{q \in S_d : \text{accurate}\}|,$$

reporter-coordinate existence, strict quotation accuracy, and the count of
accurate quotations in the draft; the lenient rate $R^{\ell}_d$ counts
near misses as accurate. A quotation the draft does not attribute is
outside $S_d$ and so outside $R_d$.

Every citation gets one of three labels, never two: exists, not found,
or unverifiable, so oracle coverage gaps are never counted as
fabrication. The outcome is called **reporter-coordinate existence**
rather than plain existence, and the name is doing real work. It means
the volume, reporter, and page resolve to an indexed opinion. It does
not mean the citation is the one a lawyer would recognise: a draft that
writes *Smith v. Jones*, 347 U.S. 483 when 347 U.S. 483 is an unrelated
real case scores as existing under this definition, and a lawyer would
call it fabricated. That gap is measured rather than assumed. The case
name is compared separately
(`src/name_mismatch.py`), and 205 of 11,769 resolving citations (1.7
percent) carry a name the index does not match, a ceiling that includes
abbreviated names, so the cells near 1.00 do not rest on wrong pages
landing on real opinions. Pinpoint pages are located against the
official reporter's page boundaries.

The strict quotation standard splits a quotation $q$ into fragments
$f_1, \dots, f_n$ at ellipses and bracketed alterations, so that a
lawful substitution is read as an omission and the words around it must
match, drops alteration parentheticals, and compares the fragments with
the normalized text $T$ of the opinion the quotation is attributed to
(case and punctuation insensitive):

the quotation is *accurate* when every $f_j$ is a substring of $T$,
and otherwise a *near miss* when

$$\min_j \mathrm{cov}(f_j, T) \ge 0.85,$$

where $\mathrm{cov}(f_j, T)$ is the share of the fragment's words of
five or more letters that occur in $T$; anything else is inaccurate, so
the alterations lawyers make legitimately pass and a changed word does
not. The lenient rate, which admits near misses, is
reported beside it as a diagnostic. The literal matcher the strict
standard replaced, which read a bracketed alteration as its contents,
is kept as the comparison (`src/alteration_aware.py`): human lawyers
score 0.507 under it, model cells move by at most 9 points (mean 3),
and the same eight contrasts survive.

Quotations are found by balanced quotation marks, which block quotations
lack, so a long indented passage would fall outside the scored set. That
is not a route out of it here: across the 1,680 drafts of the seven reported
models there are 12 markdown block-quoted lines in 9 drafts and no
indented display paragraphs, none of them Sonnet 5's
(`results/block_quotes.json`), so
block form cannot account for the strongest model quoting less.

The attribution rule decides which cited case a quotation is tested
against. It attributes a quotation to the citation whose parenthetical
holds it, else the case named in its own sentence, else the citation
that follows it in that sentence, else the citation an Id. points to,
else the last citation in the paragraph. A quotation introduced by a
statute, rule, the record, or a lower court, or with no citation in its
paragraph, is left unpaired, which is 37 percent of the 10,846
quotations in the full run, so every quotation rate is a rate over
attributed quotations.

### Inference

The primary analysis is a citation-level logistic generalized
estimating equation per model,

$$\mathrm{logit}\, P(y_{imk} = 1) = \beta_0 + \beta_k,$$

for the existence or accuracy indicator $y_{imk}$ of item $i$ in matter
$m$ under condition $k$, with exchangeable working correlation within
matter, so that the 48 matters are the independent units and the
effective sample is 48, no matter how many thousands of citations they
hold; the reported odds ratio for condition $k$ is $e^{\beta_k}$. Each model has eight contrasts
(four conditions, two outcomes); Holm correction is applied within
model, each model being the family the paper draws conclusions about,
and an effect is called significant only when it survives correction.
The robustness fits described below follow the same model, pooling
generations, templates, or tasks with a fixed effect for each, and the
revision experiment adds matter-paired comparisons of final strict
accuracy between arms over the matters scored in both.

The sandwich standard errors that fit gives are consistent as the number
of clusters grows, and 48 clusters is not many. Worse, some of the cells
that matter here are thin: the existence outcome for the strongest
models turns on a handful of citations not found per arm, and a test
leaning on asymptotics there can be anticonservative. This is why
DESIGN.md fixed a companion at freeze, before any of the data existed: a
matter-level cluster bootstrap of 2,000 resamples over per-draft rates.
It is implemented in `src/cluster_bootstrap.py`. Matters are resampled
with replacement, 48 at a time, which keeps the clustering the GEE
assumes and asks nothing about the shape of anything; each draw weights
every resampled matter equally and, as DESIGN.md's "paired throughout"
rule requires, takes the mean over resampled matters of the
within-matter difference between the condition draft's rate and the
baseline draft's. A matter whose draft has nothing adjudicable in either
cell leaves the contrast rather than shifting one arm's mean against the
other's, which matters for Llama-4, where the two cells otherwise rest
on largely different sets of cases. Reported are the percentile interval
and the share of draws keeping the observed sign.

Seven of the eight surviving contrasts have an interval excluding zero,
and the lowest sign share among them is 0.999. The eighth, Qwen3-30B's
quotation fall under the temporal clause, does not: its interval is
-0.155 to 0.004 and it keeps its sign in 0.966 of draws. That is the
honest answer and it is worth saying plainly. The GEE gives that
contrast a corrected p of 0.030, and the equal-weight-per-draft
bootstrap puts it just on the line at -0.073. Weighting by citation
instead, which is nearer what the GEE estimates, does clear zero over
the same draws: -0.089, interval -0.156 to -0.028 (`pooled_risk_diff`
and `pooled_ci_low` / `pooled_ci_high` in the JSON). So the contrast is real
under the model and under one bootstrap weighting and marginal under the
other, which makes it the weakest of the eight and the one a reader
should expect to go first. Note also that the bootstrap
interval carries no multiplicity correction, so it excludes zero for
six further contrasts that Holm rejects; those are not claimed
anywhere.

### The human reference

The same instrument scored 482 clean pre-ChatGPT human appellate briefs
to anchor every comparison. Human lawyers reach 0.610 strict and 0.788
lenient quotation accuracy under this standard (410 scored quotations)
and 0.957 reporter-coordinate existence (0.976 on U.S. Reports and published
federal reporters). Crediting the 57 failures that are near misses
carrying no alteration, the signature of a corrupted character, lifts
the floor to 0.749; the rest are unaudited, which is why the figure
anchors the severity of the standard and is not a comparison. Of the 160 human strict failures that remain under
the strict standard (`src/human_alt.py`, `results/human_alt.json`), 40
still carry a bracket or an ellipsis, 57 are near misses without any
alteration (a corrupted character), and 63 are inaccurate without one.

## How the instrument was checked

The checker is the paper's foundation, so it was tested three ways:
planted faults with known answers, a hand reading of its verdicts on
real drafts, and a full rerun of the experiment that depended on it
once the reading found a flaw. **Every number in this README and the
paper is from the corrected rule and the rerun loop.**

### Seeded validation

The quotation checker was validated before the campaign on seeded
faults, with planted genuine quotes, wrong attributions, single-word
corruptions, fabrications, and formatting artifacts, at 100 of 100. After
the audits described next, `src/validate_q2.py` plants sixteen kinds
of item per draft, eight of them attribution traps and two of them
omissions without an ellipsis (an omitted internal citation, which must
pass, and three omitted words, which must not), and scores 320 of 320.
The existence and pinpoint checks carry a seeded validation of their
own (`src/validate_pins.py`, `results/validate_pins.json`): on twenty
seeded U.S. Reports opinions with planted real, fabricated, and vendor
citations and a sentence pinned to its own page and to a page three or
more away, 100 of 100.

### The audit on real drafts

The attribution step was audited on real drafts and corrected on
2026-09-04. Under the original rule a case named after a quotation could
take it from the case named before it, a quotation of a statute was
bound to the nearest case citation, and a parenthetical quotation inside
a string cite went to the next case in the string. A hand reading of 40
inaccurate verdicts drawn at random found about 20 on the checker's
side under that rule.

Under the corrected rule a reading of 160 (the same 40 plus a disjoint
120, `results/attribution_audit_sample.md` and
`results/attribution_audit_sample2.md`) found **35 on the checker's
side, 22 percent with a 95 percent interval of 16 to 29**, 111 the model's, 4
failing only on a bracketed alteration, and 10 open
(`results/attribution_sample_reading.json`). The checker-side share
varies by condition, 8 of 28 at baseline, 11 of 30 under the quota, 6
of 33 under the temporal clause, 6 of 27 under the stakes clause, and 4
of 42 under combined pressure, and by model from 14 percent (Llama-4,
1 of 7) to 27 percent (Qwen3-30B, 12 of 45). These readings are a single unblinded pass with no second rater, over
samples released with their classifications, and were made under the
rule before the two corrections of 2026-09-05 described below, which can
only remove checker-side verdicts. **Carried into the fit**
(`src/audit_sensitivity.py`: every inaccurate verdict reclassified as
unpaired with its condition's checker-side probability, 200 draws, the
eight-test Holm family refit each time), **all eight pre-registered
survivors survive in every draw and Qwen3-30B's temporal quotation
fall in 82 percent of them, 44 percent when each condition's share is
set to the upper end of its interval**, because the error is smallest
where the falls are. Forty accurate
verdicts read the same way all held
(`results/attribution_audit_accurate_sample.md`). The rerun loop's
flags are the corrected rule's own verdicts, so their precision on
quotation flags is 78 percent (71 to 84) by this reading, and the
precision axis of Figure 2 is nominal.

A separate reading of 40 inaccurate verdicts from the grounded arm,
where the cited passages were in the prompt
(`results/attribution_audit_grounded_sample.md`), found 14 on the
checker's side (35 percent, 22 to 50): 6 statutory, constitutional, or
policy text in quotation marks, 4 a lower court's or the record's
words, 4 bound to the wrong case. The share is higher there because
the model's own failures are rarer. That reading exposed two further
faults, both **fixed on 2026-09-05, with every result regenerated**: the
name rule matched a party token as a substring, so `under`, from a
defendant eyecite parsed as "Under Mooney", matched inside
"understanding" and took a quotation from the case its own sentence
named, and the strict standard failed a quotation that omits an
internal citation without leaving an ellipsis, which the Bluebook
permits under a "(citation omitted)" parenthetical. Tokens now match at
word boundaries, and a fragment passes when it splits at a word
boundary into two halves the opinion contains in order, at most 300
characters apart, with a citation-shaped gap between them. Neither
change can make a correct quotation fail; both remove checker-side
errors, and strict rates moved by at most 0.03. Every number in this
README and the paper is from the instrument as released.

### The loop was rerun

The revision loop had been run before the correction, with flags from
the original rule. It was rerun in full with the corrected checker, and
the original runs are kept as `results/loop_v1_*` and
`results/gloop_v1_*`, where `src/realized_precision.py` replays their
feedback under the corrected rule and finds the arm labelled true had
realized precision 0.71 pooled over models and 0.38 for Sonnet 5. Every
loop number above is from the rerun.

### Other checks

Resolving the 1,766 citations that the 48 appellate deciding opinions
themselves contain, real by construction (`src/index_recall.py`,
`results/index_recall.json`), the index misses 3 of 759 to F.2d, F.3d,
and F. Supp. (0.4 percent) and 1 of 227 to the U.S. Reports, so the 22
percent not-found rate the models produce on those reporters is not
coverage. Federal Appendix spellings, F. App'x with a curly apostrophe
and Fed. Appx., had failed the index lookup for briefs and drafts alike
until an alias was added to the vendored checker; the index holds that
reporter. A citation counts as existing when its volume and page
resolve; of the 11,769 resolving citations whose draft names the
parties, 205 (1.7 percent; 1.1 at baseline, 2.8 under the temporal
clause; 0.3 percent for Sonnet 5, 3.5 for Mistral Small) carry a name
the index does not match, and counting every one of them as not found
(`results/records_nm.jsonl`, `results/stats_gee_nm.json`) keeps the
three surviving existence contrasts, adds Mistral Small's temporal fall
(odds ratio 0.59, corrected p 0.046), and removes Sonnet 5's
uncorrected combined-condition rise (odds ratio 1.07). The temporal fall is no artifact of scanned text, since within
the baseline condition alone strict accuracy for quotations from
opinions decided before 1970 is 0.449 against 0.388 for later ones
(`src/era_check.py`).

## Robustness

Each check below asks whether the single-run table would change under a
different reasonable choice: another generation, another phrasing,
another quotation standard, retrieval in the prompt, or another court.
**The same eight within-model contrasts survive every refit**, and the
paper relies only on those.

### Three generations

Three independent generations of the baseline and combined drafts on
all 48 matters and all seven models (672 drafts per run): cell-level
standard deviations are at most 0.050 for existence and 0.065 for
strict accuracy, the combined-versus-baseline quotation contrast kept
its sign in every run for every model, and pooling the three runs with
a run effect the combined fall in quotation accuracy survives Holm
correction for six of seven models (odds ratios 0.21 to 0.53), Sonnet 5
excepted.

### Two templates

A second prompt template for every condition on all 48 matters and all
seven models: twelve contrasts survive under it alone, five of them
among the eight single-run survivors (Qwen3-30B's existence falls under
temporal and combined and its quotation fall under combined, DeepSeek's
combined and Mistral Small's temporal quotation falls, **the five
effects that hold under both templates**); Qwen3-30B's quota existence
fall and Llama-4's two quotation falls did not replicate, and seven
contrasts, all falls, survive under the second template only
(GPT-5.4-mini's temporal existence; quotation for DeepSeek and Qwen3-30B
under temporal, GPT-5.4-mini, Grok 4.3, and Mistral Small under
combined, Mistral Small under stakes). Pooling both templates with a
template effect, all eight single-run survivors survive and the
combined fall survives for six of seven models (odds ratios 0.26 to
0.45), Sonnet 5 again excepted. Every contrast under every fit is in
one table, `results/contrast_matrix.md` (`src/contrast_matrix.py`),
with one family rule throughout: Holm within model over that fit's own
tests. Cell rates differ between templates by
at most 15 points of strict accuracy and 19 of existence, more than many
single-run condition effects, so single cells are template-specific and
the within-model contrasts that survive across runs and templates are
what the paper relies on.

### The lenient, literal, and distinct-authority refits

Refitting every contrast on the lenient outcome (near misses counted as
correct; `src/gee.py --lenient`, `results/stats_gee_lenient.json`),
eight contrasts survive Holm within model, the combined-condition fall
among them for Qwen3-30B and DeepSeek (Llama-4's combined fall reaches
corrected p = 0.076). Under the literal matcher
(`results/records_alt.jsonl`, `results/alteration_aware.json`,
`results/stats_gee_alt.json`) model cells move by at most 9 points
(mean 3) and the same eight contrasts survive Holm correction.
Refitting on distinct authorities per draft
(`results/stats_gee_distinct.json`) leaves the same eight as well.

### The grounded arm

A grounded arm reran the baseline and combined conditions with ten
retrieved, verified U.S. Reports authorities in the prompt (TF-IDF over
25,250 cached opinions, decided before argument, with the best-matching
passage). Models drew 51 to 83 percent of their citations from the list,
citations not found fell from 341 in 5,856 to 74 in 5,605, and the 30B
model's combined-condition existence went from 0.773 to 0.995. Quotation
accuracy rose in every cell, yet no cell exceeded 0.753 even with the
source passage in the prompt, and 60 percent of Sonnet 5's 63 remaining
inaccurate quotations are paraphrase of the cited case inside quotation
marks. Retrieval nearly removes the existence failure and leaves the
residual class in place.

### The second task

A second task, 48 published federal appellate decisions (four from each
of the First through Eleventh and Federal Circuits, packets built from
the deciding court's own statement of the case with the analysis
withheld and outcome sentences scrubbed), run under all five conditions
on all seven models, shows that fabrication at a neutral prompt is more
common outside the Supreme Court. Baseline reporter-coordinate existence is 0.65
for the 30B model, 0.73 for Mistral Small, 0.91 to 0.96 for the four
models in between, and 0.99 for Sonnet 5 alone. Twenty-two percent of
citations to the federal reporters do not resolve against four percent
of citations to the U.S. Reports (the index misses 0.4 percent of the
federal-reporter citations in the deciding opinions themselves, so the
gap is not coverage), and at baseline the models cite the U.S. Reports
for 37 to 58 percent of their authorities in a circuit appeal.

Within the task, one pressure contrast survives correction, Llama-4's
existence fall under the date restriction (0.950 to 0.857, odds ratio
0.32, corrected p 0.018); Sonnet 5's quotation rate rises under the
sanctions warning alone (0.475 to 0.624, odds ratio 1.81, corrected p
0.057), without any shift toward older cases, and that rise survives
only the pooled-task fit (odds ratio 1.59, corrected p 0.009). Pooled
over both tasks, seven of the eight Supreme Court survivors survive
(Qwen3-30B's quota existence fall drops out), joined by Llama-4's
existence falls under the temporal and combined clauses, DeepSeek's
temporal quotation fall, Mistral Small's temporal and combined
quotation falls, and Sonnet 5's rate rise under the sanctions warning.

## Where this sits in prior work

| prior work | what it does | what it could not do, which we measure |
|---|---|---|
| LePhantomCite (COLM 2026) | detects injected citation errors in briefs | naturally occurring errors, elicited under realistic pressure; page-level pincite truth |
| Deployment-constraints study (arXiv:2603.07287) | pressure factorial for scholarly citations | the legal version, against a full-text index that leaves 0.2% unresolved where their bibliographic pipeline leaves 36 to 61%, plus formal statistics |
| LegalCiteBench (arXiv:2605.10186) | closed-book citation recall | quote fidelity anywhere; generation grounded in a verified database (our loop) |
| RLEF (arXiv:2410.02089) | execution feedback for code | the same protocol where the verifier is a legal citation oracle, plus the false-positive control |
| LLM-judge critiques (arXiv:2606.19544 among others) | show agreement overstates judge validity | a pre-declared calibration bar, and three documented failures against expert labels |

## Repository guide

This is the companion repository for the paper (JURIX 2026 submission
in [`docs/jurix/paper.tex`](docs/jurix/paper.tex); an earlier markdown
draft is in [`docs/PAPER_DRAFT.md`](docs/PAPER_DRAFT.md)). Everything
here is the real campaign: the pre-registered design, the instruments,
all 1,680 drafts and the revision episodes, the statistics, and a
ledger of every analysis decision, including the findings the project
withdrew itself after its own verification passes.

    docs/jurix/paper.tex        the paper; every number is a macro generated
                                from the results files by src/emit_macros.py
    docs/PAPER_DRAFT.md         earlier markdown draft
    docs/DESIGN.md              frozen design with architecture diagrams
    docs/HYPOTHESES.md          pre-registration (frozen 2026-08-31)
    docs/LEDGER.md              dated log of every post-freeze decision,
                                including two self-retracted findings and
                                the three jury calibration failures
    docs/figures/               the paper's two figures and the two README
                                figures (src/figures.py, src/figures_readme.py)
    papers/                     close-reading notes on the positioning papers
    data/packets/               the 48 Supreme Court packets
    src/                        instruments and experiment drivers
      checker/                    the citation checker and index builder
      runtime/, sim/              the request runtime and the packet prompts
      legacy/                     the attribution rule the audit replaced
    results/                    all drafts, verdicts, and tables
      rescore_full.json           definitive Experiment 1 tables
      stats_gee.json              primary citation-level inference
      stats_gee_distinct.json     the primary fit on distinct authorities per draft
      rescore_loops.json          definitive Experiment 2 tables
      loop_transitions.json       per-quotation trace of the revision loop
      loop_citations.json         existence trace and lenient rates by arm
      gloop_<model>/              grounded true-feedback loop (Sonnet 5, DeepSeek)
      loop_v1_<model>/            the loop as first run, under the original rule
      realized_precision.json     that run's feedback replayed under the corrected rule
      alteration_aware.json       the literal matcher against the strict standard
      provenance_report_cap.md    per-quote true-source classification
      attribution_audit.json      audit of every inaccurate verdict on real drafts
      attribution_sample_reading.json  the hand readings: 160 closed-book, 40 grounded, 40 accurate
      audit_sensitivity.json      the eight-test family refit with checker-side verdicts reclassified
      count_outcome.json          accurate quotations per draft, tested by matter
      count_outcome_para.json     the same test on the second prompt template
      cluster_bootstrap.json      the primary contrasts under a matter-level cluster bootstrap
      contrast_matrix.md          every pre-registered contrast under every fit
      stats_gee_nm.json           existence refit with name mismatches counted as not found
      validate_q2.log             seeded validation of the quotation checker, 320 of 320
      pincites.json               page-level pincite verification
      human_baseline.json         the human yardstick
      revision_stats.json         Holm correction, raw counts, loop counts
      records.jsonl               24,886 citation-level records

## Reproducing

The repository stands alone. The checker (`src/checker/`, with
`build_index.py` for the citation index), the request runtime
(`src/runtime/`), the packet prompts (`src/sim/`), the 48 Supreme Court
packets (`data/packets/`), and the appellate packets (`results/appellate/`)
are all here. Two things are not committed because of size and rebuild
from public sources: the 18-million-row citation index `checker.db`,
built by `src/checker/build_index.py` from the CourtListener bulk
citation and cluster exports (set `CUP_CHECKER_DB` to its path), and the
Caselaw Access Project text cache `data/cap_text_cache.sqlite`, which
`src/local_text.py` fills from static.case.law on first use. The original
attribution rule the audit replaced is kept as
`src/legacy/quotecheck2_original.py`, and the loop runs made under it as
`results/loop_v1_*` and `results/gloop_v1_*`; `src/realized_precision.py`
replays their feedback under the corrected rule.

Scoring is deterministic and free of API calls:
`src/rescore_full.py` rebuilds the Experiment 1 tables from the
committed drafts, `src/rescore_loops.py` the Experiment 2 tables, and
the GEE in `results/stats_gee.json` runs from `records.jsonl`.
Generating new drafts requires an OpenRouter key in `.env`; every
driver is resumable, budget-capped in code, and parallelizes with
`--slice`. Large text caches are not committed; they rebuild from free
public sources (static.case.law).
