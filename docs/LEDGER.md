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
  facts (TF-IDF over the 25,250 opinions of substantial length in the local Caselaw Access
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
- 2026-09-03 (grounded-arm lens, 7 items applied): the retrieval corpus
  is the 25,250 cached U.S. Reports opinions with a name and date and
  at least 2,000 characters (62,534 was the raw row count); exclusion is
  by party name in the caption, which for the ten matters with the
  United States as a party removes every opinion captioned United
  States v. (stated in the code and paper); the prompt permitted other
  authority; "at least half not verbatim" corrected to "no cell exceeded
  0.525"; quotation accuracy rose in every combined cell and six of
  seven baseline cells (Llama-4 baseline fell 0.402 to 0.381);
  "removes" softened to "nearly removes" (74 not found remain in 5,605,
  against 341 in 5,856 closed-book).
- 2026-09-03 (second task, federal courts of appeals; after the
  pre-registered analysis): src/appellate_packets.py builds 24 matters
  from published F.3d opinions in the local Caselaw Access Project
  cache (1995 to 2019, at most two per circuit, at most a quarter with
  the United States as a party): the packet is the opinion's statement
  of the case and facts, cut at the first analysis marker and scrubbed
  of outcome sentences, with a second scrub pass after a "we further
  instruct" leak was found in the first build; party roles and circuit
  from the CAP head matter. Drafts argue for the named appellant under
  baseline and combined on all seven models (results/app_*, 336 drafts).
  Findings (src/appellate_stats.py): baseline existence 0.565 (Qwen),
  0.716 (Mistral), 0.900 (DeepSeek), 0.910 (GPT), 0.936 (Llama, Grok),
  0.993 (Sonnet), lower than on the Supreme Court matters for six of
  seven models; the models cite the U.S. Reports for 49 to 76 percent
  of authorities even in a circuit appeal; at 24 matters only Sonnet's
  quotation rise survives Holm (OR 2.02, p 0.016); pooled over both
  tasks with a task effect, Qwen's existence fall and the quotation
  falls of Qwen, Llama, and DeepSeek survive, as does Sonnet's rise
  (OR 1.59, p 0.009). No refusals. Sanity check: the index holds
  262,886 F.3d and 506,638 F.2d citations and Sonnet's appellate drafts
  had 2 not-found in 368, so the lower existence of the other models is
  fabrication, not coverage.
- 2026-09-03 (appellate lens, 11 items applied): the cross-appeal
  F3d-169-1322 (Charles v. Burton) was argued for the cross-appellant
  because the caption regex matched "Cross-Appellants"; stated in the
  paper, and appellate_packets.py now skips cross-appeals. Not-found
  citations in the appellate drafts by reporter: 264 of 872 federal
  reporter citations (30 percent) and 103 of 1,780 U.S. Reports
  citations (6 percent) do not resolve; state reporters are 17 percent
  of failures, so the appellate shortfall is fabrication, not index
  coverage. Sonnet's pooled-task quotation rise (OR 1.59, Holm 0.009)
  is now reported beside the falls.
- 2026-09-03 (appellate task extended to the full factorial): 48
  matters (four per circuit, twelve circuits, cross-appeals excluded,
  22 of the first 24 kept), five conditions, seven models, 1,680 drafts.
  The OpenRouter account ran out of credits 38 drafts short; Hardy
  added $10 and the lanes resumed. Findings (appellate_stats.py, now
  the same GEE as gee.py with Holm within model): baseline existence
  0.645 Qwen, 0.725 Mistral, 0.907 DeepSeek, 0.924 GPT, 0.950 Llama,
  0.959 Grok, 0.993 Sonnet; 23 percent of federal-reporter citations
  and 4 percent of U.S. Reports citations do not resolve; within the
  task three contrasts survive: Llama-4's temporal existence fall (OR
  0.32), and Sonnet 5's quotation rises under combined (OR 1.61) and
  under the STAKES clause alone (0.316 to 0.433, OR 1.68, Holm 0.019),
  which the memorization alternative cannot explain because the stakes
  clause does not change which cases may be cited. Pooled over both
  tasks: six of the eight Supreme Court survivors survive (Qwen quota
  and temporal existence do not), plus Llama existence falls, DeepSeek
  and Mistral temporal quotation falls, and Sonnet's rises under
  combined and stakes. Page fit: a heading that could not fit with its
  first two lines had been leaving five lines empty at the foot of
  page 8; cutting five lines before Section 6 recovered ten. Appellate
  arm total $17.22; project $119.91.
- 2026-09-03 (appellate lens, second pass, 7 items applied): reporter
  mix now filtered to the 48 manifest matters (28 orphan drafts from the
  first build excluded; federal not-found 22 percent); the U.S. Reports
  share is reported at baseline only (37 to 58 percent), since the
  temporal clause inflates the pooled figure; the memorization check is
  now shown for the appellate task (Sonnet 5's median cited decision
  year 1991 at baseline and under stakes, 1946 under temporal), so the
  stakes-only rise is not a shift toward older cases; the twelve
  circuits are named (First through Eleventh and Federal; no D.C.
  Circuit); the Conclusion states the appellate result as a fall in
  baseline existence for six of seven models rather than "fabrication
  reaches every model but Sonnet".
- 2026-09-03 (final whole-paper review, 30 items applied): the
  Experiment 2 trace now names its fourth outcome (flagged quotations
  left in place), and the Discussion no longer says the words "usually"
  survive as paraphrase, since deletion exceeds dequoting for six of
  seven models; the abstract mentions the appellate task; the Inference
  paragraph counts three robustness fits; "grounded arm" is used
  consistently; the top of the range is defined at first use; the
  Sonnet paragraph is headed as a contrast that survived only outside
  the pre-registered run; the pincite remainder is named and pins
  outside the cited case are counted (26 in 6,644); the 99 stock-phrase
  matches close Sonnet's provenance partition; the temporal-violation
  sentence uses temporal-only counts; several colon reveals and a
  comma splice removed. Body ends three quarters down page 10.
- 2026-09-03 (second reviewer's list, review_papers/CUP_v5_self_review.txt
  from a parallel session, applied where still relevant): Zhao et al.'s
  conditions restated correctly in the introduction (year window,
  survey-style breadth, non-disclosure; the sanctions warning is ours);
  Table 2 gained a "left" column so flagged rows sum to n; the
  replication sentence reports standard deviations and ranges (0.088
  existence, 0.111 strict); the temporal-condition OCR confound is
  tested within baseline (src/era_check.py: strict accuracy 0.309 for
  quotations from pre-1970 opinions against 0.296 for later ones, so
  the fall under the temporal clause is not an artifact of scanned
  text); the misattribution count is stated as a ceiling (in 151 of 626
  the true source is also cited in the same draft, so attribution
  errors are possible); the appellate shortfall carries the coverage
  check (263,000 F.3d and 507,000 F.2d citations indexed, Sonnet 5 at
  0.993); the deletion finding is scoped to closed-book revision with
  a grounded loop left for future work; the Discussion names the
  lenient standard as the one a deployer should enforce. The release
  link works only once the repository is public, which is Hardy's step.
- 2026-09-03 (tenth pass, 17 items applied): Llama-4's loop existence
  rise is reported with its citation-count drop (270 to 244) beside
  Qwen's flat count; the precision-curve claim in the Discussion is
  scoped to Sonnet 5, the only monotone line; "most of the rest" fixed
  to "most of those"; the Sonnet three-run existence sentence names its
  direction and its baseline; stock-phrase matches (99) stated as
  excluded from the misattribution count; "one fixed template" scoped
  to the primary run and "single clause" to each pressure clause; the
  human existence shortfall restated as partly held state reporters;
  the second-template survivor count phrased without contradiction; the
  lenient-standard recommendation given its reason; "cannot distinguish";
  jury scores named as agreement with expert labels; "separate task" in
  the abstract; duplicate one-per-vendor phrasing removed; paired-test
  denominators named; the appellate coverage sentence says "overall".
  Previously hand-typed numbers (index sizes, provenance corpus, Sonnet
  median years, three-run not-found counts, jury scores) are now macros
  from results files (results/jury_calibration.json records the jury
  figures with their source).
- 2026-09-03 (external-style review, review_papers/CUP_v5_review.txt,
  relevant items applied): the sanctions tracker is described as a
  docket in the thousands; the loop rates are defined as means over
  drafts with at least one scored quotation, with drafts left with none
  dropping out; the human near-miss gap is characterised (bracketed
  alterations and ellipses); Sonnet 5's out-of-corpus quotations in the
  grounded arm are described as citing authority outside the U.S.
  Reports, which the decomposition does not cover; the Controls
  paragraph drops the per-level final accuracies (Figure 2 carries
  them) and keeps the half-precision point; Figure 2 is drawn at 1.15in
  height so the Section 6 heading no longer opens a page-foot gap. Body
  ends on page 10, references on page 11.
- 2026-09-03 (external-style review, second pass, the three open
  majors): (1) existence in the loop is traced per citation
  (src/loop_citations.py, results/loop_citations.json): of 113
  non-resolving round-0 citations across the seven models 86 were
  removed and 27 kept, with 33 new resolving citations, so the paper
  and Conclusion now say existence rises "chiefly by removal". (2) The
  precision curve is recomputed under the lenient verdict (same file):
  Sonnet 5 0.983 / 0.879 / 0.769 / 0.727 / 0.573 at precision 1 to 0
  against 0.796 with no feedback, so a verifier right half the time or
  less sits below revision alone; one sentence added to Controls. (3)
  The true-feedback loop was rerun from the grounded combined drafts of
  Sonnet 5 and DeepSeek with the retrieved excerpts kept in the prompt
  (loop_arm.py --grounded; results/gloop_*; rescore_loops.py and
  loop_transitions.py take --prefix gloop; cost $3.73): Sonnet 5 92
  flagged, 1 corrected, 17 dequoted, 56 deleted, 18 left, strict 0.496
  to 0.837; DeepSeek 3 of 89 corrected. The "future work" clause is
  replaced by the result. Also: Sonnet 5's pooled existence rise now
  carries Fisher's exact p = 0.38 on its twelve events beside the
  logistic p; the seeded validation is described as balanced (twenty
  drafts, one planted item of each of five kinds); the abstract gives
  the single-run count (three models) beside the pooled six of seven;
  Related Work, Inference, Controls, and Limitations trimmed to keep
  the body on ten pages.
- 2026-09-03 (external-style review, third pass, instrument items):
  gee.py --lenient refits every contrast with near misses counted as
  correct (results/stats_gee_lenient.json): 10 survivors, the combined
  quotation fall for Qwen, DeepSeek, Mistral (Llama-4 corrected p 0.055),
  and a Grok 4.3 stakes rise (OR 1.81, corrected p 0.002) absent on
  strict; reported in Section 4. src/validate_pins.py seeds the
  existence and pinpoint checks (20 opinions, 100 of 100). src/
  index_recall.py resolves the 1,766 citations in the 48 appellate
  deciding opinions (real by construction): 3 of 759 federal-reporter
  and 1 of 227 U.S. Reports citations not found, replacing the indirect
  coverage argument in the second-task paragraph. loop_citations.py now
  also counts final drafts with no scored quotation (47 of 168 true-arm
  episodes; 17 of Grok 4.3's 24, so its 1.000 rests on seven drafts) and
  splits round-0 flags into inaccurate and near miss (246 of 708 near
  misses; 36 of Sonnet 5's 89). Wording: Dahl et al. no longer cited for
  sanctioned filings; Ortega et al. cited for classification, not
  prediction; the temporal clause named as a proxy for binding-authority
  and jurisdiction limits; the matcher's handling of ellipses and
  bracketed alterations stated; the human excerpts described as
  OCR-converted and the figure as a floor; the mixed arms' recall
  confound stated; the 131 out-of-scope quotations stated to have had
  opinion text; the provenance corpus described as a dump predating the
  retrieval cache; pinpoint coverage stated (9,129 pins, 73 percent
  span-checked, 1,162 with a quotation); the intro's pinpoint claim
  scoped to U.S. Reports authority. The Ethics and Release section is
  folded into the Conclusion's last sentence to keep ten pages.
- 2026-09-03 (alteration-aware standard): src/alteration_aware.py
  rescores the full run with bracketed segments read as omissions and
  alteration parentheticals dropped (records_alt.jsonl,
  alteration_aware.json, stats_gee_alt.json): cells move at most 5.2
  points (mean 2.0) and the same 8 contrasts survive Holm. src/
  human_alt.py: human strict 0.407 to 0.495 under it; of 343 strict
  failures 130 altered, 94 unaltered near misses, 119 unaltered
  inaccurate. One sentence added to the human-reference paragraph; the
  "chiefly bracketed alterations" clause is replaced by the counts.
- 2026-09-03 (provenance search rerun over the CAP cache):
  provenance.py --corpus cap indexes all 62,049 cached U.S. Reports
  opinions with captions from the checker index
  (results/provenance_report_cap.md, provenance_cap.log; emit_macros and
  era_check read it when present). Against the 8,392-opinion dump:
  misattributed 626 to 620, found nowhere 2,573 to 2,546, generic 574 to
  569, checker false alarms 76 to 114 (Sonnet 5: 9 to 23 of 746, 1.2 to
  3.1 percent), the cleaner captions reclassifying some misattributions
  as the checker's own error. With real case names as sources the
  same-draft check rises from 151 to 294 of 620 (Sonnet 5: 83 of 123).
  Paper, README, and Discussion false-alarm rate follow the macros.
