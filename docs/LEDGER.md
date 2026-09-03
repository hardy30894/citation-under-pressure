# Forking-paths ledger

Opened at design freeze, 2026-08-31. Every analysis decision made after
freeze gets a dated entry: what was decided, why, and whether it was made
before or after seeing the relevant data. Nothing is deleted.

- 2026-08-31 (freeze): design frozen as DESIGN.md + HYPOTHESES.md stand
  today. Pilot-informed amendments folded in before freeze: three-label
  adjudication with unverifiable bucket; abstention logged per cell;
  quote instrument = quotecheck2 (validated 100/100 seeded); pincite =
  range check now, CAP star-pagination build for U.S. Reports during the
  run; misattribution/leakage provenance classification with the six-word
  distinctiveness threshold; leak-rate-by-era as designed endpoint.
- 2026-08-31 (freeze): H1 strong form (frontier existence collapse) was
  refuted at pilot scale before freeze; recorded in HYPOTHESES.md header.
  The full run does not get to resurrect it.
- 2026-09-01 (jury v1 -> v2): the relevance panel FAILED its pre-declared
  calibration bar (0.500, constant "not supported", misrep recall 30/30,
  clean specificity 0/30). Diagnosis: binary framing forced a false
  verdict whenever the partial opinion window missed the supporting
  passage. Instrument changed AFTER seeing calibration data (that is what
  calibration is for; measurement verdicts from v1 were never interpreted
  and are archived in results/jury_v1_failed/): three-way verdict
  (supports / contradicts / cannot_tell) with cannot_tell = abstention,
  window widened 3K->6K. v2 must clear the same 0.75 bar on decisive
  verdicts, with decisiveness rate reported alongside.
- 2026-09-01 (jury CLOSED): v2 failed inverted (0.700; misrep recall
  2/11, specificity 19/19, accepts everything). Pre-declared escalation
  run on Hardy's go: FRONTIER panel (GPT-5.4 + Sonnet 5 + Gemini 2.5
  Pro, 15K windows) scored 0.594, misrep recall 4/17, specificity
  15/15. DECISION (pre-registered contingency): the relevance/Goodhart
  channel is reported as bounded-but-unmeasurable by LLM jury; the
  paper's Goodhart claims scope to the deterministic channels
  (existence, verbatim quotes, pincite pages, corpus-proven
  misattribution). The three failed calibrations are methods-section
  content, not discarded data. No further jury spend.
- 2026-09-01 (human baseline upgraded): the original baseline run was
  quota-starved (CourtListener cap; 147 of 1,674 quotations scored,
  strict 0.381). Re-scored on the local-first text chain: 578 scored,
  strict 0.407, stable at 0.400 on the all-citations-resolve subset;
  existence unchanged at 0.931. This is an instrument-coverage
  improvement applied uniformly, decided independently of any model
  comparison; every document now cites 0.407. Consequence honestly
  noted: Sonnet's baseline (0.333) sits below the human level rather
  than inside a band containing it, reaching parity only under combo.
- 2026-09-01 (sixth model): GLM-4.7-flash cannot complete the factorial.
  It returns empty completions on most combo drafts at 12K and again at
  30K reasoning budget (101 skip events; 23 of 30 blocked drafts are
  combo): under maximum pressure it reasons until the budget dies and
  never emits a word. Decision, made before any GLM row was interpreted:
  GLM is reported as a documented pressure-paralysis case, excluded from
  the main tables (its partial data would be missing-not-at-random in
  exactly the combo cells the analysis compares), and Mistral Small
  replaces it as the sixth complete ladder model. Both facts go in the
  paper: six complete models, and one further family whose failure mode
  under stacked constraints is silence.
- 2026-09-01 (abstention count corrected): the draft claimed no model
  ever abstained; the event logs show three refusals across the four
  original models (two DeepSeek, one GPT-5.4-mini). All documents now
  say three refusals in 1,440 drafts. Caught during the six-model
  integration's number check.
- 2026-09-02 (venue): submitting to JURIX 2026 (deadline Sept 13, long
  paper, 10 IOS pages, single-blind). Decision by Hardy: one paper out
  quickly outweighs the A* ceiling for this paper. Fallback recorded:
  JURIX notifies Oct 8; a rejection can still enter ARR Oct 12. Number
  audit script (src/audit_numbers.py) passes 22/22 at this point.
- 2026-09-02 (post-review analyses, results/revision_stats.json): (a) Holm
  correction within model over all GEE contrasts: surviving = Qwen
  existence (quota, temporal, combo), Qwen quotes (temporal, combo),
  DeepSeek combo quotes, Llama temporal and combo quotes. Sonnet's positive
  combo effects (p=.029/.034 uncorrected) do NOT survive; the "sanctions
  warning induces care" claim is withdrawn as a finding and reported only
  as an uncorrected exploratory contrast with its alternative explanation.
  (b) Loop held-out counts: under true feedback Sonnet's scored quotations
  fell 157 -> 73 while accurate quotations went 68 -> 70; the rise in strict
  rate to 0.974 is denominator collapse. The model satisfies the verifier
  mainly by removing quotations, not by correcting them. Qwen changed
  nothing (182 -> 181 scored, 16 -> 16 accurate). Existence repair is
  genuine (citations replaced, counts flat). H2's headline changes from
  "near-perfect repair" to "verifier satisfaction by deletion": the
  Goodhart question the introduction asks is answered, and the answer is
  yes. (c) Pressured drafts are 1,152, not 1,440.
- 2026-09-02 (JURIX revision applied): paper.tex rewritten around the
  Holm-corrected results; Table 1 carries lenient rates and not-found
  counts, Table 2 carries scored and accurate quotation counts so the
  deletion effect is visible in the table itself. Figure 1's existence
  panel now starts at 0.7; Figure 2 splits true and false feedback into
  two panels. Provenance, pincite, and not-in-corpus decompositions were
  re-run over all six models (463 misattributed quotations in total). The
  paraphrase arm covers the four models that existed when it was designed
  (Qwen, DeepSeek, GPT-5.4-mini, Sonnet); the paper says so rather than
  implying six.
- 2026-09-02 (bibliography audit): every entry in references.bib and
  ailaw.bib checked against arXiv, Crossref, the ACL Anthology, IOS Press,
  and dblp by independent verifiers. Five field errors fixed: gehring
  (now the ICML 2025 PMLR version with its six-author list), shao (year
  2025, not 2026), gu (two missing authors, year 2024), spaeth (Michael J.
  Nelson missing from the SCDB author line), tan (ICLR 2025 note added).
  Two entries added and verified: Mata v. Avianca, 678 F. Supp. 3d 443
  (S.D.N.Y. 2023), docket 1:22-cv-01461, opinion of June 22, 2023; and
  Charlotin's hallucination cases database (2,008 cases as of Sept 2).
  Gray et al. pages are 199-208 (188-198 is a different ICAIL paper);
  Khatri et al. has seven authors per IOS Press (dblp's five is a gap).
- 2026-09-02 (no-feedback loop control): a third loop arm ("none": the
  same number of revision rounds with a content-free "revise as you see
  fit" instruction) launched on all six models, 24 matters each, so that
  repair and deletion can be separated from what revision alone does.
  One DeepSeek lane died on an empty completion; loop_arm.py now drops the
  episode instead of the lane, and the five missing episodes were rerun.
- 2026-09-02 (second review round, applied): a reviewer pass on the
  revised paper found the false-feedback paragraph repeating the
  denominator error (inaccurate counts fell under false feedback, so the
  models deleted correct quotations rather than rewriting them), four
  text-versus-table mismatches, and no inference in Experiment 2. Added:
  src/gee.py (the GEE fit was previously an unsaved inline script; it now
  reproduces stats_gee.json exactly and adds 95 percent intervals);
  src/loop_transitions.py, a per-quotation trace from round 0 to the
  final draft (corrected, dequoted, deleted, added) for all three arms;
  matter-paired Wilcoxon and bootstrap comparisons of final strict
  accuracy, true feedback against each control. Findings: Sonnet 5
  corrected 4 of 89 flagged quotations and deleted or dequoted 85; under
  false feedback it removed 56 of 68 correct ones. Revision without
  feedback lifts Sonnet 5 to 0.595 and GPT-5.4-mini to 0.543; true
  feedback adds 0.36 for Sonnet 5 (p = 0.0003) and nothing
  distinguishable for GPT-5.4-mini (0.12, interval includes zero). The
  Sonnet combined contrast is now labeled a pre-registered null result,
  not exploratory. Liu et al. open-weight pincite recall corrected to 19
  to 51 percent (Qwen3.6-27B reaches 50.9). GLM missing drafts are 33
  (28 combined), not 30. Loop rescoring drifted by a few quotations
  (Qwen 182 to 186 scored at round 0) because the local text cache grew
  between runs; all macros regenerated together. Body fits exactly ten
  pages; the phrasing-robustness paragraph moved into Limitations and
  the language-model-judges paragraph into Section 6 to make room.
- 2026-09-02 (IOS Press format pass): checked paper.tex against the JURIX
  call and the IOS book-article instructions. Title and headings now
  follow IOS capitalization (prepositions lower case). Every table,
  figure, and section carries a label and is cross-referenced with
  \ref; every illustration is referenced in the text; no "above" or
  "below" references remain. Figures are drawn at the type-area width
  (12.4 cm) so lettering prints at 6.5 to 8 points, above the 6-point
  minimum; tables use the class's 8-point footnotesize, the minimum for
  tables. DOIs print in the reference list (IOS asks for them when known;
  the bst constant that suppresses them is documented as adjustable and
  was switched on); arXiv DataCite DOIs added to preprint entries. The
  paper builds cleanly with pdflatex and bibtex, the toolchain IOS names,
  with all fonts embedded, via docs/jurix/build.sh; a user-level TeX Live
  was installed in ~/texlive-portable for this. Body ends at the foot of
  page 10 under pdflatex. Still needed from Hardy: ORCID in the author
  line, and the EasyChair category (long paper).
- 2026-09-02 (award pass, three additions, all after the pre-registered
  analysis): (1) a half-true feedback arm (each checker line kept or
  replaced by a scrambled one with equal probability, so the verifier's
  precision is about one half), 24 matters on all six models; with true,
  false, and no feedback this gives a precision dose-response. Sonnet 5's
  correct quotations removed: 17 under true, 38 under half, 56 under
  false, 18 under none; its final strict rate under half-true feedback
  (0.664) sits close to revision without feedback (0.595) and 0.31 below
  true feedback (paired p = 0.001). Table 3 now shows all four arms.
  (2) A replication of the baseline and combined drafts for the first
  twelve matters on all six models with a fresh cache (144 drafts): one
  draft identical to the first run; existence rates agreed within 0.031
  and every existence contrast kept its sign; strict quotation rates on
  twelve matters differed by a median of 0.067 and up to 0.328
  (GPT-5.4-mini combined, where the contrast changed sign). Reported in
  Limitations as the run-to-run noise bound. (3) The pincite verifier
  run on the human brief excerpts: quotations sit on the cited page 89
  percent of the time (45 quotations), against 77 percent for Sonnet 5.
  Also: round-0 clean drafts counted (12 of 144 combined drafts would
  pass a gate unrevised). Spend for the three additions about $5; project
  total about $57.
- 2026-09-02 (third lens pass, 30 items applied): two pipeline fixes
  behind the prose. The per-quotation trace could claim one final
  quotation for two round-0 quotations; each final quotation is now
  matched once, and the trace reconciles exactly with the loop scorer
  (Sonnet 5 final accurate 70 = 51 kept + 4 corrected + 15 added).
  The provenance search had used the bare opinion store while every
  other scorer used the local-first chain, so its inaccurate population
  (617 for Sonnet 5) differed from the decomposition's (746); it now
  uses the chain and both report 746. Misattributions across the six
  models are 563 (was 463), Sonnet 5 false alarms 9 of 746 (1.2 percent).
  The replication sentence now says which existence contrasts kept sign
  (Qwen's, the only significant one; DeepSeek's and GPT's, both within
  0.05 of zero, flipped). "Strongest model" replaced by a defined term,
  the top of the range (Sonnet 5 and GPT-5.4-mini, highest baseline
  existence). Rule 11's scope now cites FRCP Rule 1.
- 2026-09-03 (seventh model): Grok 4.3 (xAI, x-ai/grok-4.3 through
  OpenRouter) added as a second top-of-range model so that the frontier
  claim does not rest on Sonnet 5 alone. Chosen over Gemini 2.5 Pro on
  price (xAI output tokens at $2.50 per million against $10); the full
  factorial cost $2.08 and the four loop arms $0.79. Results: existence
  0.981 to 0.994 in every condition, strict quotation accuracy 0.326 at
  baseline to 0.246 combined with no contrast surviving correction, 2
  temporal violations in 719 checked citations, no refusals or empty
  completions. In the loop it is the purest deletion case: 46 flagged
  quotations, 0 corrected, 27 dequoted, 19 deleted, 24 of 24 drafts clean,
  final strict accuracy 1.000. Counts throughout the paper are now seven
  models, 1,680 drafts, 1,344 pressured, 56 contrasts; misattributions
  626; the top of the range is Sonnet 5, GPT-5.4-mini, and Grok 4.3
  (highest baseline existence). The replication and paraphrase arms
  cover the six original models and say so. Project spend about $60.
- 2026-09-03 (award pass, second round; all after the pre-registered
  analysis, all reported as robustness beside the primary fit):
  (1) Precision arms at 0.25 and 0.75 on all seven models; Figure 2 is
  now the precision curve (final accuracy and share of correct
  quotations removed against verifier precision, with no feedback as
  the leftmost point) and Table 3 was removed as redundant with it.
  Sonnet 5's correct quotations removed: 17, 24, 38, 53, 56 of 68 at
  precisions 1, 0.75, 0.5, 0.25, 0. (2) Two further generations of the
  baseline and combined drafts on all 48 matters and all seven models
  ($14.60): no identical drafts except 22 of 96 for Mistral Small;
  cell SD at most 0.05 (existence) and 0.06 (strict); the combined
  quotation contrast kept its sign in every run for all seven models;
  pooling three runs with a run effect (src/gee_pooled_runs.py), the
  combined fall survives Holm for six of seven models (OR 0.33 to
  0.50), Sonnet 5 excepted; Sonnet's existence contrast reaches
  corrected p = 0.005 on 7 not found in 975 against 5 in 1,324, still
  reported as a null with the memorization alternative untested.
  (3) The second template on all 48 matters and all seven models
  ($19.61): 12 contrasts survive under template B, 5 of the 8
  template-A survivors; pooling both templates with a template effect
  (src/gee.py --pooled, src/phrasing_stats.py), all 8 survive and the
  combined fall survives for 6 of 7 models (OR 0.32 to 0.46); cell
  rates differ between templates by at most 11 points (strict) and 20
  (existence, Qwen temporal), replacing the 40-point figure from the
  twelve-matter check. (4) The deletion-is-rational objection is stated
  and answered in the Discussion. Project spend $93.90 of the $200 cap.
- 2026-09-03 (grounded arm): a retrieval condition, run after the
  pre-registered analysis and reported as its own paragraph. For each
  matter the ten U.S. Reports opinions most similar to the question and
  facts (TF-IDF over the 62,534 opinions in the local Caselaw Access
  Project cache; decided before argument, and before 1970 for the
  combined condition; the argued case excluded by citation and by name)
  were placed in the prompt with citation, year, and best-matching
  250-word passage (src/retrieve.py, results/retrieval/), and baseline
  and combined were rerun on all 48 matters and seven models
  (results/rag_*, $8.79). Findings (src/grounded_stats.py): models drew
  51 to 83 percent of citations from the list; citations not found fell
  to 74 in 5,605; Qwen combined existence 0.773 to 0.995 (OR 54);
  combined existence no lower than baseline for any model; strict
  quotation accuracy rose for every model (Qwen combined 0.072 to
  0.368, Sonnet baseline 0.333 to 0.525) yet stayed at or below 0.53
  everywhere, and Sonnet's remaining 221 inaccurate quotations are 62
  percent paraphrase of the cited case (55 closed-book). Retrieval
  removes the existence failure and leaves the residual class in place;
  the Discussion's earlier prediction to that effect is now a
  measurement. Project spend $102.69.
