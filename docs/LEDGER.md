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
- 2026-09-04 (passage arm and the replaced outcome): loop_arm.py gains
  a passage arm in which each quotation line carries the closest passage
  of the cited opinion (closest_passage, the retrieval arm's window
  search); run on Sonnet 5 and DeepSeek, 24 matters, $3.17. The trace
  gains a "replaced" outcome (a flagged quotation deleted while a new
  accurate quotation appeared on the same citation, each new quotation
  claimed once), and Table 2's corrected column is now in place plus
  replaced. Closed-book true feedback: Sonnet 5 4 in place + 8 replaced
  of 89, DeepSeek 2 of 183; grounded loop: 17 of 92 and 6 of 89; passage
  arm: 36 of 89 (9 + 27) and 22 of 183, final strict 0.944 and 0.877
  over 110 and more surviving quotations, 52 and 159 flags still deleted
  or dequoted. Abstract, Section 5, Discussion, and Conclusion updated;
  "For courts" folded into "What evaluations should include"; Figure 2
  at 1.08in; the Section 5 thesis sentence dropped as redundant with the
  Discussion.
- 2026-09-04 (INSTRUMENT CORRECTION, the largest change since the
  freeze). A cold review of the 18:17 build asked for the attribution
  step to be audited on real drafts. The audit (src/attribution_audit.py,
  40-item hand reading) found about half of the inaccurate verdicts on
  the checker's side, from three faults in quotecheck2: (1) a case name
  in the text after a quotation could take it from the case named in the
  signal phrase before it, because generic name words (judicial, circuit,
  district, ...) matched ordinary prose and the nearer match won ("In
  *United States v. Nixon*, 418 U.S. 683, the Court held that ..." bound
  to a state case cited in the next sentence); (2) quotations introduced
  by a statute or rule were bound to the nearest case citation; (3) the
  text between two quotations in one sentence was extracted as a
  quotation. Fixes: the signal-phrase name wins unless a citation follows
  the quotation directly and is not introduced by see/cf./accord/
  compare; a generic-word stop list; a statute-introduced quotation with
  no case name is left unpaired; spans opening or closing with
  whitespace are rejected; name tokens also come from the "A v. B" the
  draft writes before the citation (eyecite's party metadata stops at a
  markdown asterisk). validate_q2.py gains three plants for these faults:
  160 of 160. Effect: Sonnet 5 baseline strict 0.333 to 0.439, combined
  0.427 to 0.587; Qwen3-30B moves less than a point; human reference
  0.407 to 0.427. Every derived result is regenerated by
  src/rebuild_all.sh (records for full/para/app/rag/rep2/rep3, rescores,
  loops, grounded loop, passage arm, provenance over the CAP cache,
  decomposition, pincites, human reference and its alteration and
  reporter splits, every GEE fit, robustness campaigns, era check,
  macros, figures). The previous numbers stand in git history (commit
  07f651c) and are not carried into the paper. Also from that review:
  name mismatch defined and counted (src/name_mismatch.py; exists is a
  volume/reporter/page hit, the name compared separately; 205 of 11,769
  resolving citations, 1.7 percent, a ceiling; Sonnet 5 6 of 1,787);
  human existence by reporter (src/human_existence.py; 21 of the 61 not
  found are Federal Appendix, a reporter the index lacks; 0.974 on U.S.
  and published federal reporters); figures redrawn at readable height
  with full axes; Table 1 with adjudicable n per cell and the temporal
  denominator named; Table 2 with an added column and pooled final
  rates; abstract's precision comparison made against no feedback; Zhao
  sentence corrected; the human line labelled a floor; bibliography
  et al. period fixed in vancouver.bst; grounded Qwen OR given its p.
- 2026-09-04 (instrument correction, rounds two to six, final). The
  first correction left about 40 percent of a fresh 40-item sample on
  the checker's side, so the attribution rule was rebuilt around the
  quotation's own sentence: a quotation belongs, in order, to the
  citation whose parenthetical holds it, the case named in its own
  sentence, a citation later in that sentence (not one introduced by
  see/cf.), the citation an Id. points to, or the last citation in the
  paragraph; a quotation introduced by a statute, rule, the
  Constitution, legislative history, a lower court, a party's
  contention, or the record, or with no citation in its paragraph, is
  left unpaired (37 percent of the 10,846 quotations in the full run).
  Sentence boundaries are found with an abbreviation list (v., U.S.,
  Id., Co., Cir., initials) so that citations do not end sentences.
  validate_q2.py now plants twelve kinds per draft, 240 of 240. Hand
  readings of the seeded 40-item sample after each round: ~20, 16, 14,
  14, 8 of 40 checker-side; results/attribution_sample_reading.json
  records the final reading (8 checker, 30 model, 2 open). Final
  headline numbers (single run): Sonnet 5 strict 0.488 baseline, 0.613
  combined (uncorrected p 0.03, Holm 0.25); pressure falls survive for
  Qwen (existence x3, combined quote), DeepSeek (combined), Llama-4
  (temporal, combined), Mistral (temporal); pooled runs: combined fall
  for six of seven (OR 0.23 to 0.57), Sonnet excepted; appellate: Llama
  temporal existence fall and Sonnet's stakes rise (OR 1.88, Holm
  0.019), the rise surviving the pooled-task fit. Loop: Sonnet 40 flags,
  3 corrected in place + 5 replaced, 4 dequoted, 26 deleted, 2 left; 21
  of 64 accurate removed (19 with none, 37 at precision 0.5, 54 all
  false); passage arm 21 of 40 repaired against 16 removed; DeepSeek 14
  of 138 against 122. Human 0.493 strict (416 scored), 0.594 under the
  alteration-aware standard. Provenance: 330 misattributed, Sonnet 258
  inaccurate of which 5 the checker's (1.9 percent), 140 of 330 with the
  true source in the same draft. The "Relevance" paragraph is folded into
  Limitations and the Conclusion shortened for the page fit.
- 2026-09-04 (last items): unpaired quotations classified by cause
  (results/unpaired_causes.json: of 10,846 quotations, 24 percent are
  introduced by non-case material, 10 percent stand in a paragraph that
  cites nothing, 3 percent have a citation too far back; per-model share
  31 to 42 percent); one sentence in Section 3. Limitations names the
  post hoc correction of the attribution rule. README gains the name
  mismatch and era-check sentences. Page 2 keeps a tolerated underfull
  (badness 5,681) from a paragraph the class will not split under its
  widow rule.
- 2026-09-04 (reader's review, six items): the Conclusion and abstract
  lead with the failure mode moving with capability (existence at 30B,
  verbatim quotation in the middle, paraphrase, misattribution, and
  wrong pages at the top) and scope every effect to the model and the
  constraint; strict accuracy is defined over attributed quotations in
  Terms and the Table 1 caption; "quotes above the human floor" replaced
  by the two rates; Holm within model justified as the family the paper
  draws conclusions about, with the effective sample named as 48
  matters; numeric detail cut from the abstract, the Section 4 prose, and
  the precision-curve sentence. Ten pages, no underfull page but the
  reference page.
- 2026-09-04 (reader's second note): the hand reading of inaccurate
  verdicts extended from 40 to 160 (a disjoint 120-item sample, seed
  20260904, results/attribution_audit_sample2.md, read under the final
  rule only): 35 checker-side (22 percent, Wilson 95 percent interval
  16 to 29), 111 model-side, 4 strict-standard failures on a bracketed
  alteration, 10 open; the second sample alone runs 27 of 120. Section 6
  and the Discussion carry the interval. The Discussion's gate sentence
  now favors the gate over a loop resolving bare flags, since the
  passage arm shows a loop with evidence in the flag does better.
- 2026-09-04 (the 22:09 review, six majors; the last changes to the
  instrument and the design). (1) The loop's feedback had been produced
  by the original attribution rule at run time. src/realized_precision.py
  replays every feedback line and re-adjudicates it under the corrected
  rule: pooled over models the arm labelled precision 1 had realized
  precision 0.71 (Sonnet 5 0.38, Qwen 0.80), the 0.75, 0.5, 0.25, and 0
  arms 0.54, 0.38, 0.18, and 0.01. The loop is therefore rerun with the
  corrected checker for all seven arms and all seven models, and the
  grounded loop for Sonnet 5 and DeepSeek; the original runs are kept as
  results/loop_v1_* and gloop_v1_*. (2) The strict standard now reads a
  bracketed alteration as an omission and drops alteration parentheticals
  (quotecheck2.fragments); the literal matcher is kept in
  alteration_aware.py as the comparison. Human strict 0.594 (literal
  0.493); Sonnet 5 0.523 baseline, 0.644 combined; the same eight
  contrasts survive. (3) Federal Appendix spellings (F. App'x with a
  curly apostrophe, Fed. Appx.) had failed the index lookup; aliases
  added in the vendored checker; human existence 0.957 (was 0.931) and 1
  Federal Appendix citation not found (was 24). (4) Records carry the
  citation string; gee.py --distinct refits on distinct authorities per
  draft, same eight survivors; the surviving existence contrasts rest on
  28 to 90 not-found events per arm. (5) Denominators: scored quotations
  per cell (42 to 325) in Table 1 and macros for quotations and accurate
  quotations per draft; Sonnet 5's rate rise is selection (9.6 to 6.1
  quotations per draft, 2.83 to 2.60 accurate per draft), stated as such
  in Section 4, the abstract, and the Conclusion; the appellate stakes
  rise no longer survives correction (Holm 0.084) and is reported as a
  rate rise surviving only the pooled-task fit. (6) The checker, runtime,
  prompts, and packets are vendored into the repository; README says
  what is not committed and how it rebuilds. Audit: checker-side share by
  condition from the 160 readings (baseline 8 of 28, quota 11 of 30,
  temporal 6 of 33, stakes 6 of 27, combined 4 of 42), and 40 accurate
  verdicts read, 0 checker-side. Minor items: Zhao breadth sentence;
  cache sizes reconciled (25,250 is the retrieval subset of the 62,049
  cached opinions); paraphrase and found-nowhere counts reconciled;
  pinpoint scope stated (24 percent non-U.S. Reports, 3 percent after
  volume 572 or without page marks, 12 percent adjacent); template spread
  named against effect sizes in Limitations; "50 percent precision" in
  the abstract; the audit sentence no longer uses "precision".
- 2026-09-04 (loop rerun with the corrected checker, $15.66): all seven
  arms for all seven models and the grounded true arm for Sonnet 5 and
  DeepSeek, 24 matters each, flags now from the corrected quotecheck2
  over the same local-first text chain the rescoring uses (loop_arm.py
  uses ChainTextStore). Sonnet 5 under true feedback: 36 flags, 1
  corrected in place, 2 replaced, 2 dequoted, 31 deleted, 0 left; only 3
  of 68 accurate quotations removed (21 under no feedback), final 1.000,
  24 of 24 clean. Precision curve (accurate removed of 68): 3, 8, 20, 27,
  43 at precision 1, .75, .5, .25, 0 against 21 with none; finals 1.000,
  1.000, 0.956, 0.830, 0.575 against 0.787. Passage arm: repair rose in
  six of seven models (Sonnet 12 of 36, Mistral 26 of 96, Qwen 24 of
  138, DeepSeek 12 of 136, GPT 6 of 22, Llama 3 of 33, Grok 0 of 37),
  removal still exceeding it everywhere. Paired true vs none: Sonnet
  +0.21 (0.12 to 0.32, p 0.002), DeepSeek +0.38; GPT, Qwen, Mistral within
  noise; Llama and Grok too few pairs. Grounded loop: 4 of 23 and 1 of
  51. 68 of 168 true-arm episodes ended with nothing to score (Grok 19).
  The original runs are archived as loop_v1_* and gloop_v1_*; Section 5
  states their realized true-arm precision (0.71 pooled, 0.38 Sonnet 5)
  from src/realized_precision.py. Section 5, Figure 2, the abstract,
  Discussion, and Conclusion rewritten to the new trace: "the one setting
  in which repair exceeded removal" is withdrawn; "a loop should hand the
  model the passage; even then it removes more than it repairs" stands.
  The "Compliance and refusals" paragraph is folded into the Table 1
  caption and the intro's refusal count for the page fit.
- 2026-09-04 (reader's note): the Discussion now joins the two
  experiments in one sentence, a model can raise an observable
  correctness rate by changing what it exposes to the check, quoting less
  under pressure and deleting under feedback, so a rate should be read
  beside the count of correct items; Discussion, Limitations, and
  Conclusion trimmed to keep ten pages.
- 2026-09-04 (README): opening rewritten to the three-part answer
  (failure mode moves with capability; verification is not repair; a
  rate moves by what the model exposes to the check), the results
  diagram relabelled, Finding 1 retitled, and four figures embedded: the
  paper's two (docs/figures/fig1_pressure.png, fig2_repair.png) and two
  README-only ones from src/figures_readme.py, the fate of flagged
  quotations under a bare flag against the passage in the flag
  (fig3_repair.png) and Sonnet 5's quotations per draft against its rate
  (fig4_selection.png).
- 2026-09-04 (README restructured for hierarchy): results at a glance,
  the three findings each in subsections that state the claim and carry
  the figure that supports it, then Method, How the instrument was
  checked, Robustness, prior work, repository guide; every number kept.
- 2026-09-05 (review of the 01:31 build, six majors and seven minors,
  applied without a rebuild): (1) the audit's error is now carried into
  the contrasts: src/audit_sensitivity.py reclassifies every inaccurate
  verdict as unpaired with its condition's checker-side probability, 200
  draws, eight-test Holm family refit each draw; all eight pre-registered
  survivors survive in every draw at the observed shares and in at least
  99 percent of draws at each condition's Wilson upper bound
  (results/audit_sensitivity.json). The reading is reported by condition
  including baseline (8 of 28) and by model (14 to 27 percent), and a
  further 40-item reading of the grounded arm (seed 20260906,
  results/attribution_audit_grounded_sample.md) found 14 of 40 on the
  checker's side (35 percent, 22 to 50): 6 statutory or policy text, 4
  lower-court words, 4 wrong bindings. The rerun loop's flags are the
  corrected rule's verdicts, so their audited precision on quotation
  flags (78 percent, 71 to 84) is stated and Figure 2's precision axis
  is called nominal. (2) Accurate quotations per draft is tested as an
  outcome for every model (src/count_outcome.py, post hoc, Wilcoxon paired
  by matter, Holm within model): seven contrasts in four models survive,
  DeepSeek, Llama-4, GPT-5.4-mini, and Grok 4.3, the last two with no
  surviving rate contrast; Sonnet 5's count is flat (p 0.53) while its
  inaccurate count falls 2.58 to 1.44, which is the evidence for
  selection, now stated as the leading explanation, not a fact. The
  existence arithmetic is reconciled: 13,241 of 14,040 records resolve,
  774 not found; 11,769 is the name-checked subset. (3) One family rule
  is stated (Holm within model over each fit's own tests), every other
  fit is labelled exploratory, the five effects that hold under both
  templates are named, the seven template-B-only survivors are named,
  Llama-4's "largest drop" is qualified as not replicating, and the
  abstract marks the four as pre-registered, three under both templates,
  and the six of seven as exploratory. results/contrast_matrix.{csv,md}
  (src/contrast_matrix.py) gives all 56 contrasts under eleven fits.
  (4) Table 2 splits Clean into with-quotations / emptied, gives the
  pooled round-0 rate beside the pooled final, and every paired test
  carries its n; the intent-to-treat count (accurate quotations per draft
  over all 24 episodes) rises for Mistral Small alone; "Mistral Small left
  most flags standing" corrected to 45 of 96. (5) The human line in
  Figure 1 is labelled a severity floor, not a comparison, and the Llama-4
  sentence no longer sets its rate beside it; the pinpoint scope
  (quotation-bearing pinpoints on U.S. Reports authority, quotations
  found in the cited case, ranges read at the first page, straddling
  quotations placed by the longest fragment) is stated in the abstract,
  introduction, and Section 3; the strict standard's remaining gap, an
  internal citation omitted without an ellipsis, is stated. (6) The
  precision result is stated against the no-feedback arm (20 at 0.5 is
  what revision alone removes, 21); "where the checker belongs" and the
  strict-standard advice are labelled recommendations from arms with no
  person in them. Minors: temporal clause direction (toward memorized
  authority, the gentler direction) and Rule 11 governing neither forum;
  the 3 percent unpaired remainder; tables reordered so Llama-4 (0.588)
  follows GPT-5.4-mini (0.583); the two partitions of Sonnet 5's 250 are
  stated as two partitions by different questions; "window search" is
  now "best-matching passage"; name mismatches reported by model and
  condition with a sensitivity fit counting them as not found
  (src/name_mismatch.py writes results/records_nm.jsonl; stats_gee_nm.json
  keeps the three Qwen survivors, adds Mistral temporal at Holm 0.041,
  removes Sonnet 5's uncorrected combined rise, OR 1.07); the grounded
  odds ratio carries its interval and p; the Liu et al. precision is
  derived from their reported recall and F1 (84.4 and 55.0, precision
  near 41 percent). Two instrument faults found by the grounded reading
  are staged, not applied: a party token matched inside a longer word
  ("under" in "understanding") and the omitted-internal-citation gap;
  docs/pending_instrument_fixes.patch carries both with two new seeded
  plants, and applying it requires the full rebuild. Page fit: abstract
  and several paragraphs tightened, tables set in scriptsize, figures at
  1.1 in; body ends on page 10, references begin on page 11.
- 2026-09-05 (notation): Section 3 now defines the outcomes in symbols,
  E_d (existence over adjudicable citations A_d), R_d (strict accuracy
  over the scored set S_d), K_d (accurate quotations in the draft), R^l_d
  (lenient), and the verdict rule (fragments f_j of a quotation against
  the normalized opinion text T; accurate when every f_j is a substring,
  near miss when min_j cov(f_j, T) >= 0.85); Section 5 names the
  feedback precision pi; the GEE indicator y_imk is named. The Discussion
  states the paper's core point in that notation: R_d = K_d / |S_d| rises
  when |S_d| shrinks as well as when K_d grows, and both experiments are
  the first case (quoting less under pressure, deleting under feedback),
  so an evaluation that scores only what a system emits should report
  K_d beside R_d. The strict-rate formula S_d that an earlier draft
  carried is superseded by this block. Page fit kept by small trims in
  Sections 5 to 9; body ends on page 10.
- 2026-09-05 (two instrument corrections applied, full rebuild): (a) the
  name rule matched party tokens as substrings, so "under", from a
  defendant eyecite parsed as "Under Mooney", matched inside
  "understanding" and bound a quotation whose sentence names Affronti v.
  United States to Mooney v. Holohan; tokens now match at word boundaries
  (quotecheck2.word_find/word_rfind), and that quotation scores accurate
  against Affronti. (b) A quotation that drops an internal citation
  without an ellipsis, under a "(citation omitted)" or "(cleaned up)"
  parenthetical or Bluebook 5.2, failed the strict standard because the
  fragment spanned the citation; quotecheck2.omitted_citation now passes
  a fragment that splits at a word boundary into two halves of at least
  15 characters that the opinion contains in order, at most 300
  characters apart, when the gap holds a digit or id., ibid., or supra.
  Two seeded plants cover it (an omitted internal citation must pass;
  three omitted words of prose must not); validate_q2 is 280 of 280 on
  fourteen plants. Every result regenerated (src/rebuild_all.sh, 21 min).
  What moved: strict rates by at most 0.03 (human 0.594 to 0.610); the
  pre-registered survivor set is still eight, but Mistral Small's
  temporal quotation fall (p 0.009, Holm above 0.05) left it and
  Qwen3-30B's temporal quotation fall entered, so the abstract's "four
  models" is "three" (now macro-driven), the effects holding under both
  templates are Qwen3-30B's four and DeepSeek's combined fall, and the
  template-B-only list gains Mistral temporal; lenient refit 7; count
  outcome 8 contrasts in 5 models (Qwen temporal added); audit
  sensitivity now 7 of 8 in every draw and Qwen3-30B's temporal
  quotation fall in 82 percent (44 at the upper bound), stated; pooled
  tasks 7 of 8 kept with five further falls; Sonnet 5 combined rise
  uncorrected p 0.025, Holm 0.201, and its stakes rise uncorrected p
  0.048; loop trace Sonnet 5: 35 flags, 3 repaired, 30 deleted, 4 of 69
  accurate removed, precision curve 4/9/21/28/43 (at 0.5 exactly the 21
  of no feedback); Mistral left 44 of 92; passage 13/35. The hand
  readings (160 closed-book, 40 grounded, 40 accurate) were made under
  the rule before these corrections; the sample files they refer to are
  kept as read (restored from git after the rebuild), and the paper says
  the readings predate the corrections, which can only remove
  checker-side verdicts. docs/pending_instrument_fixes.patch removed.
- 2026-09-05 (review of the 02:26 build, six majors and seven minors):
  (1) Precision axis. The mixed arms' labels are the share of true lines
  supplied, and Section 5 now says the checker's own flags are right 78
  percent of the time, so realised precision is about 0.8 of the label
  and the crossing sits nearer 0.4; the arms replace rather than add
  lines, so recall falls with precision, restored to the text after a
  page-fit cut had removed it; the accurate side of the checker is
  reported too (0 of 40 wrong, upper bound near 9 percent). (2) The date
  clause is confounded with what gets quoted, and the old era check
  compared eras inside the baseline cell, where the old cases are the
  model's own choices. src/era_strata.py dates every scored quotation by
  the cited opinion's decision year and refits inside strata: within
  pre-1970 opinions strict accuracy is 0.449 baseline (187), 0.292
  temporal (936), 0.232 combined (1,140), the combined fall surviving
  pooled with a model effect (OR 0.54, 0.31 to 0.92, p 0.025), the
  temporal marginal (OR 0.59, p 0.062), three per-model falls at p<0.05;
  within later opinions neither moves (OR 0.96, 1.03). A second
  stratification: under the temporal clause only 24 percent of scored
  quotations cite authority the model also uses at baseline and those
  score 0.409 against the baseline 0.397, while new authority scores
  0.252 (combined 19 percent, 0.457, 0.194). The clause damages
  integrity chiefly by composition, which the paper now says. (3) The
  Discussion had called Liu et al.'s GPT-5 agent "the best" and used its
  40.8 percent precision to argue the precision requirement; verified
  against the v2 PDF, Table 2 also carries a Claude Code agent at 76.1
  percent precision and 68.8 F1, which the text calls highest precision
  and highest F1, and the 52.8 percent pincite recall is the GPT-5 row.
  Both rows are now reported, "best" is qualified by axis in both
  places, and the argument is restated. (4) The hand readings are
  declared a single unblinded pass with no second rater, over released
  samples. (5) Both rules the reviewer named are fixed: the
  omitted-internal-citation tolerance shipped this morning, and
  src/pilot.py now parses a pincite range or list so any page it names
  counts as cited (45 quotations moved from adjacent to at-page; Sonnet
  5 83 to 85 percent, human 88 to 90, pooled adjacent 12 to 9), with the
  n behind every page-level figure now given (42 to 262 per model).
  (6) Dequoting is separated from deletion: the citation survives in 100
  of 103 dequoted quotations, so for a paraphrase it is the right
  repair; counting it as repair, deletion still exceeds repair for six
  of seven models under bare flags and four of seven under the passage
  arm, Grok 4.3 the exception. Minors: Llama-4's loop basis disclosed;
  the combined condition's clause confound stated where it is called
  pressure; "inaccurate" given one meaning (failing = near miss plus
  inaccurate in Section 4); the two episodes that ended empty without
  passing noted; the fourfold repair rise attributed to Sonnet 5; the
  ortega citation moved to the claim it supports; the 482 human excerpts
  explained; coverage gap defined and statutes excluded from the
  existence denominator; the paired share's movement with treatment
  given; figures enlarged to 1.25 in with a distinct marker per model so
  the lines separate in greyscale. Page fit took about 3,000 characters
  out of the intro, related work, method, and discussion; the release
  link is Hardy's to fix.
- 2026-09-05 (abstract rewritten): the previous abstract was a results
  list with no through-line and never stated the paper's claim. Rewritten
  with a spine, problem, design, the two experiments, and closing on the
  point the Discussion makes: a rate computed over what a model chooses
  to expose to a check can rise while the correct output behind it does
  not, so an evaluation should report the count beside the rate. The
  stratified date-clause result is now in the abstract; the loop control
  detail and per-fit qualifiers came out. countModelsWithFall now emits
  a word, so the abstract no longer mixes "three models" with "5 models".
- 2026-09-05 (review of the 11:45 build, six majors on construct
  validity): each was tested rather than argued.
  (1) TRUE and now measured. The stored record holds the Court's
  opinion, concurrences, dissents, and head matter together, so a
  quotation from a dissent scores accurate against the case; Jackson's
  Korematsu dissent is inside that record. A first detector built on
  textual headings put a quarter of accurate quotations in a separate
  opinion, but it was wrong: the syllabus announces "filed a dissenting
  opinion" before the majority begins, so the majority fell after the
  boundary and Mistretta's "intelligible principle" was misclassified.
  src/opinion_part.py instead uses the Caselaw Access Project's
  structural markers (<article class="opinion" data-type=...>): of 1,578
  accurate quotations it can place, 39 sit outside the Court's opinion
  (20 concurrence, 11 dissent, 8 syllabus) and 33 of those, 2.1 percent
  of the total, carry no signal in the draft. Reported in Section 6 as
  its own residual class. The first, wrong figure was never written into
  the paper.
  (2) FALSE for this corpus, and now answered with a measurement:
  across 1,887 drafts there are 12 markdown block-quoted lines in 9
  drafts and no indented display paragraphs, none of them Sonnet 5's, so
  block form is not a route out of the scored set and cannot explain the
  selection reading (results/block_quotes.json).
  (3) TRUE and it sharpens the result. The loop stops on a clean draft,
  so rounds executed rise as precision falls (2.47 true, 2.72, 2.91,
  3.02, 3.21 false, 3.11 none). src/rounds_control.py re-analyses with
  rounds held fixed: removals per episode-round run 0.048, 0.090, 0.145,
  0.150, 0.200 against 0.109 with no feedback, and after exactly one
  round 10, 15, 25, 31, 32 percent of the 181 accurate quotations are
  gone against 23 percent. On both bases no feedback sits between
  precision 0.75 and 0.5, so the old claim that a half-precision
  verifier merely matches revision alone was too kind: it is worse, and
  a verifier needs about three in four to beat doing nothing. Abstract,
  Section 5, Discussion, and Conclusion restated.
  (4) TRUE in part. The reclassification draws cover the primary fit
  only. The count outcome is insulated by construction, since
  reclassifying an inaccurate verdict as unpaired leaves the accurate
  count untouched, and the paper now says so; the year-adjusted fit is
  not, and is labelled exploratory. The 78 percent flag precision is
  stated as a lower bound.
  (5) TRUE, partly addressed: the text store's coverage is characterised
  where the scored set is defined; the year distribution of scored
  against dropped quotations is in results/records_era.jsonl but not in
  the paper.
  (6) TRUE and it changed the result. Applying the paper's own Holm rule
  inside the stratified fit, neither pooled bucket contrast survives
  (combined Holm 0.099, temporal 0.185) and only two per-model falls do.
  The bucket does not hold age fixed either: within pre-1970 the arms
  are twelve years apart in median (1952 baseline against 1940). The
  analysis is now a continuous year adjustment on all 3,644 dated
  quotations: combined OR 0.557 to 0.682 (0.530 to 0.879, p 0.003),
  temporal 0.62 to 0.768 (p 0.035), so about 35 percent of the effect on
  the log-odds scale is composition and the rest is not. The composition
  split conditions on a post-treatment choice and is now presented as
  descriptive. The abstract no longer says the clause damages integrity
  "chiefly" by composition.
  Minors: the human floor with OCR-corrupted near misses credited is
  0.749, now reported, and the Discussion no longer recommends the
  standard on the ground that the human reference passes it; good-law
  status named in Limitations; the abstract's "without overtaking
  removal" was wrong and is replaced (the passage arm's repair overtakes
  deletion in three of seven). Fitting roughly 2,000 characters of new
  material inside ten pages cost the grounded arm its own paragraph (now
  folded into the second-task paragraph) and the grounded-arm audit
  reading its sentence; both remain in the repository.
- 2026-09-05 (README resynced to the 11:45 round): the README had kept
  the retracted bucket stratification and the too-kind
  half-precision-equals-no-feedback claim after the paper dropped both.
  It now carries the continuous year adjustment, the rounds-controlled
  precision series with the corrected crossing, the separate-opinion
  residual class as its own row in the Finding 3 table, the block-quote
  measurement where the scored set is defined, and the corrected human
  floor of 0.749.
- 2026-09-05 (review of the 12:48 build): two of the six majors were
  errors in numbers the abstract carried, and both are corrected.
  (1) The verifier threshold did not follow from its own series. Linear
  interpolation of the no-feedback point gives nominal 0.664 on the
  per-round basis and 0.564 after one round, so the bracket is 0.56 to
  0.66 and "about three times in four" was above all of it; on the
  realised scale (a true line is right only as often as the checker,
  0.78) the crossing is 0.44 to 0.52, and since 78 percent is a lower
  bound these are upper bounds. src/rounds_control.py now computes the
  interpolation, and the abstract, Section 5, and Discussion state the
  interval on both scales. The Discussion's comparison with published
  detectors is restated against it; the ranking of the two agents is
  unchanged.
  (2) The abstract broke the paper's own both-templates rule: it said
  quotation accuracy fell for three models without saying that only two
  of those replicate, and the count outcome was never run on the second
  template at all. Both qualifiers are now in the abstract and in
  Section 4.
  (3) The opinion-type audit reported 39 of 1,578 without saying what
  1,578 was a share of; it is 73 percent of the accurate quotations, now
  stated.
  (4) The year adjustment conditions on a variable the treatment sets.
  Decision year is a mediator, not a confounder, so the fit decomposes
  the effect rather than removing a bias, and odds ratios are not
  collapsible, so part of the movement is mechanical; both are now
  stated, the bucketed null is named as the assumption-light alternative
  that disagrees, and the abstract now quotes the temporal clause's own
  45 percent rather than the combined 35.
  (5) Compliance with the date clause runs from 0 to 35 percent with no
  ordering against effect, so every contrast is intention-to-treat
  across models receiving different doses; said in Section 3.
  (6) The nulls are failures to reject on cells as small as 3 against 1,
  and capability is indexed by baseline existence, an ordering that
  differs on other axes; both said.
  Minors: the relevance-panel sentence cited Liu et al. for a 0.75 bar
  that paper does not contain (the bar was ours, their contribution is
  the expert labels), now attributed correctly; Zhao et al. call their
  own pipeline deterministic, so "fuzzy bibliographic matching" is
  replaced by the resolution-rate contrast, which is the one that
  survives; block quotations are recounted over the 1,680 drafts of the
  seven reported models rather than 1,887 including the excluded model;
  the unpaired shares read as percentages again; the duplicated
  "separates the two" sentence is gone; a round is defined; the pincite
  scope says a pincite with no quotation is outside it. Two source
  attributions in two rounds were wrong in the same way, both caught by
  checking the source rather than the memory of it.
- 2026-09-05 (page fit, honestly): fitting the last two review rounds
  inside ten pages had reached the point of an \enlargethispage of four
  baselineskips, which ran page 10 about four lines below the type area
  of its neighbours. That is a format deviation a production editor
  would catch, so it is gone: four more lines of prose were tightened
  and the release link moved from the Conclusion to the author footnote,
  where a reviewer meets it on page 1 rather than page 10. Every body
  page now ends on the same baseline (y=124.1) and there is no layout
  hack in the source.
- 2026-09-05 (review of the 18:52 build; twelve of fifteen prior
  comments confirmed fixed, presentation raised to 4). Four of the new
  items were real and three of those were self-inflicted by the
  compression of the previous rounds.
  (1) The paper contradicted itself on its own error bound: Section 5
  called 78 percent an upper bound and Section 8 a lower one. Lower is
  right, since both later corrections removed only checker-side
  verdicts, so the realised crossing of 0.44 to 0.52 is a lower bound
  too. Section 5 corrected.
  (2) The abstract said the date clause moves the model onto unfamiliar
  authority while Section 3 said it moves citations toward
  well-memorized opinions. The data say unfamiliar (24 percent of the
  temporal arm's quotations cite authority the model also uses at
  baseline). Section 3 now records that as an expectation the results
  overturn, which is what it is, and Section 4's memorisation aside is
  rewritten to match.
  (3) The 78 percent was measured on inaccurate verdicts only, while the
  flag set is inaccurate or near miss and no near-miss flag was audited.
  Said in Section 5 and Limitations.
  (4) The Discussion's removal claim was true of the flags a model acted
  on and misleading for Qwen3-30B, which acted on 23 of 139 and left 116
  standing. Scoped, with the counts given, and the Conclusion now says a
  model acting on the flags satisfies them by removal.
  Not addressed: the arithmetic alternative to the count outcome
  (citations rise in a fixed word budget while scored quotations fall),
  the abstract's residual mediation claim against the null bucketed
  check, and an interval on the crossing. These are recorded here rather
  than fixed.
  Page fit: ten pages hold with \enlargethispage{2\baselineskip} before
  the Conclusion, so page 10 runs two lines below its neighbours. That
  is a deliberate and documented deviation, taken after cutting four
  further lines of prose failed to close the gap; the earlier
  four-baselineskip version was rejected as too large.
- 2026-09-08 (provenance audit of the human reference, on Hardy's
  question): verified end to end and nothing is invented. The 482
  excerpts are every brief-derived row in Liu et al.'s released files
  whose injected-hallucination list is empty (1,000 brief-derived rows,
  518 perturbed, 482 clean); their README describes a 500/500 split, so
  the 18 an earlier reviewer asked about are the dataset's own
  discrepancy and not a filter of ours, which the paper now states as
  "482 of their 1,000". The rate rebuilds exactly from the per-excerpt
  records: 1,640 quotations extracted, 1,075 unpaired, 155 unverifiable,
  410 scored, 250 accurate, so 250/410 = 0.6098; existence 845 of 883
  adjudicable = 0.957; 482 excerpts scored, none crashed. The human
  briefs and the model drafts go through the same ChainTextStore with
  the CourtListener fetch budget at zero, so neither side gets text the
  other could not have. Corrected a stale docstring in
  src/human_baseline.py that claimed a fetch budget of 120 through
  OpinionTextStore; the code has used the chain store at budget zero
  since the vendoring. The substantive caveat stands and is already in
  the paper: only 410 of 1,640 quotations in those briefs reach the
  rate, and 103 of the 160 failures are unexplained after the 57 OCR
  near misses, which is why the figure is a severity floor and not a
  lawyer error rate.
- 2026-09-12 (full verification pass before submission). Two real
  defects found and fixed, plus seven source-attribution corrections.
  INSTRUMENT BUG, now fixed. The paper claimed the unverifiable label
  covered "a reporter the index does not carry", but the code only gave
  it to vendor database numbers and malformed cites. A reporter the
  index holds nothing from fell through to not_found, i.e. was counted
  as fabrication. N.L.R.B. was the case: 54 citations, all 54 labelled
  not found, in an agency reporter the index has zero rows for. The
  design note had flagged the agency-reporter blind spot before the
  freeze and it was never closed. SqliteIndex.covers() now answers
  whether the index holds anything in a reporter, cached, and the
  checker returns unresolvable with a coverage_gap flag when it does
  not. The fix is safe because eyecite emits a full case citation only
  for reporters in its own database, so an invented reporter (F.5th,
  S.W.4th) never reaches the checker and cannot hide behind the label.
  Effect after the full rebuild: not_found 774 to 720, unresolvable 25
  to 79, exists unchanged at 13,241; the largest cell shift is 0.019 and
  all eight pre-registered survivors are unchanged.
  STALE RESULT, now fixed. results/index_recall.json was dated 3
  September and was not in rebuild_all.sh, so it predated the Federal
  Appendix alias fix and showed Fed. Appx. failing 11 of 11 on citations
  that are real by construction. Re-run, it is 0 of 11. The two numbers
  the paper cites from it, 1 of 227 U.S. Reports and 3 of 759 federal
  reporters, were unchanged. index_recall.py is now in the pipeline.
  TWO TYPED RESULTS, now macro-driven: the seeded validation count and
  the band the five stable models sit in were literals in the text.
  SOURCE ATTRIBUTIONS, from a verification pass over every cited claim.
  Four were wrong: ortega2025scotusmem classifies SCDB issue areas and
  documents no memorisation confound, so the cite is dropped and the
  sentence states only the design fact; LegalCiteBench's task is
  supplying the authorities a proposition rests on, not a named case's
  citation, and the magnitude is under 7 of 100; RLEF has a
  random-feedback ablation, which is the analogue of our false arm, and
  no no-feedback control, so the sentence is rewritten and our
  no-feedback arm is claimed as ours; the Rule 11 sentence cited a bib
  entry for Rule 1, now Rule 11(b)-(c) with Rule 1 for scope. Two were
  overstated: Liu et al.'s misrepresentation labels are model-injected
  with a 40-item expert review, so "expert labels" becomes
  "content-misrepresentation labels", and the 0.75 bar was ours, set by
  reference to reported judge agreement, not Zheng's. One was loose:
  their taxonomy is grounded in real court filings, not only sanctioned
  ones. Garneau et al. is CJEU material, now said, and the second
  author's surname is Palmer Olsen, fixed in the bib.
  VERIFIED CLEAN: numbers.tex regenerates identically from results/, so
  no number in the paper is typed; all 35 Table 1 cells reconcile with
  records.jsonl; all seven Table 2 rows sum to their flagged totals; 70
  of 70 figure and table source cells match their macros; the Figure 1
  human line matches human_baseline.json; both figure PDFs postdate
  their data; no undefined macros, no unresolved references, no overfull
  boxes; ten body pages with references from page 11.
- 2026-09-12 (completion pass: missing data fetched, second rater added).
  PINCITE SCOPE WIDENED. The page-level check had been restricted to the
  U.S. Reports by choice, not by data: the Caselaw Access Project marks
  page breaks the same way in the federal reporters and 551 F.3d and 420
  F.2d volumes were already cached. pincites.py now accepts every
  reporter the archive publishes, which is 99 percent of the pinpoints
  the drafts contain. Coverage rises from 73 to 92 percent of the 9,129
  pinpoints checked against a page span, and the scored set from 1,001
  to 1,283 quotations; the appellate task now has a pincite check where
  it had none. Rates barely move (Sonnet 5 85 percent on a cited page,
  human 85, pooled adjacent 10), so the wider scope confirms rather than
  changes the finding. N.L.R.B. remains outside it: the archive
  publishes no agency reporter, and those citations are now correctly
  unverifiable rather than not found.
  SECOND RATER. The audit had one reader, which the last three reviews
  called its weakest point. A second, independent reading of the same
  160 inaccurate verdicts, blind to the first, puts 35 percent on the
  checker's side against the first reading's 22. The two agree on 9
  items, 54 percent of the sample, at Cohen's kappa -0.10, which is
  worse than chance: the classification is not reproducible and no point
  estimate of the checker's error is defensible. Rather than choose a
  reader, the contrasts are refit against the union, counting an item as
  the checker's whenever either reader did, 51 percent of the sample and
  45 to 59 percent by condition. Seven of the eight pre-registered
  survivors hold in every one of 200 draws at that rate; only Qwen3-30B's
  temporal quotation fall does not (6 percent). The paper now reports
  the disagreement and the pessimistic refit instead of a single share,
  which is a stronger claim than the one it replaces: the results stand
  even if the instrument is wrong about half the time. Written to
  results/audit_two_raters.json with the second reader's per-item labels.
  The second reader also named three mechanical defects worth recording:
  a quotation can be bound to a parallel citation (41 L. Ed. 2d 935, 96
  S. Ct. 1592) as though it were a separate case, to a cert denial with
  no opinion text, or backwards to the citation preceding it when the
  quotation sits before its own. These are not fixed and are candidates
  for the next rebuild.
- 2026-09-12 (mechanical defects closed). Of the three the second reader
  named, two were real and are fixed, and one was not a defect.
  PARALLEL CITATION STRINGS. A court cited once in three reporters
  ("418 U.S. 539, 558, 94 S.Ct. 2963, 2976, 41 L.Ed.2d 935") yields one
  eyecite citation per reporter, and a quotation could be attributed by
  proximity to the last of them as though a different court had spoken.
  quotecheck2.merge_parallel now folds a citation into the previous one
  when they resolve to the same opinion and sit within 60 characters
  plus the previous citation's length, keeping the first position and
  the union of the name tokens. Measured on a 220-draft sample before
  the fix, 19 of 1,152 scored quotations were bound to a parallel cite
  of a case already cited earlier, 14 of them carrying an inaccurate
  verdict.
  PROCEDURAL HISTORY. A citation introduced by "cert. denied", "aff'd",
  "rev'd" and the like is the subsequent history of the case being
  cited, not a source a draft quotes from, and one could take a
  quotation by proximity. Such citations are now flagged and passed over
  in attribution. The sampled instance, a quotation belonging to Veatch,
  674 F.2d 1217, that had been bound to the cert denial at 456 U.S. 946,
  now attributes correctly and scores accurate rather than inaccurate.
  NOT A DEFECT. The third case, a quotation bound to 96 S. Ct. 1592,
  was reported as a parallel citation treated as a separate case. The
  draft cites Rose only by its S.Ct. parallel, five times, and that
  resolves to the right opinion, so the attribution was correct and the
  verdict stands as the model's error. Reproducing each report before
  fixing it is what separated the two.
  Both rules carry seeded plants: a genuine sentence followed by a real
  parallel citation pair drawn from the index, which must attribute to
  the case, and a genuine sentence followed by a nearer cert-denial
  citation, which must not take it. validate_q2 is 320 of 320 on 16
  kinds. Everything rebuilt; the eight pre-registered survivors are
  unchanged for the third rebuild running.

- 2026-09-12 (review pass, two additions and a set of cuts, all after the
  pre-registered analysis): (1) the count outcome K_d, until now run on
  the first prompt template only, was run on the second as well
  (src/count_outcome.py grew --records/--out; results/count_outcome_para
  .json). It replicates in direction and not in per-model attribution:
  the contrast keeps its sign in 20 of the 26 tests
  that have one on both templates, two of the 28 being exactly zero on
  one template and so having no sign to keep; six of the eight
  first-template Holm survivors fall again, template B has eight Holm
  survivors of its own in four models, and six of the seven models lose
  correct quotations under some clause on at least one template. Llama-4's
  fall does not reappear and Mistral Small's appears only on template B.
  Reported as a replication of the direction, with the per-model
  limitation stated. (2) The matter-level cluster
  bootstrap DESIGN.md fixed at freeze, 2,000 resamples over per-draft
  rates, was implemented and put in the pipeline
  (src/cluster_bootstrap.py, seed 20260913). It is pre-registered, not
  exploratory, and it is reported because sandwich standard errors are
  asymptotic in the number of clusters and several cells here are thin.
  It is paired by matter, which DESIGN.md also requires ("paired
  throughout"): the statistic is the mean over resampled matters of the
  within-matter difference, so a matter missing from either cell leaves
  the contrast instead of shifting one arm's mean against the other's.
  That distinction bites for Llama-4, whose baseline and condition cells
  otherwise rest on largely different sets of matters. Seven of the eight
  primary survivors have a percentile interval excluding zero, the lowest
  sign share among them 0.999. The eighth, Qwen3-30B's temporal quotation
  fall, does not: -0.073, interval -0.155 to 0.004, sign kept in 0.966 of
  draws, against a corrected GEE p of 0.030. Weighting by citation rather
  than by draft over the same resamples puts it at -0.089, interval
  -0.156 to -0.028. Both weightings are in the released JSON; the paper
  reports the per-draft paired one, the statistic fixed at freeze, and
  names the exception. Two earlier passes of this script were discarded
  rather than reported: the first used 5,000 draws and a
  citation-weighted statistic, the second was unpaired. Neither is what
  DESIGN.md specified. Two defects in DESIGN.md itself were corrected in
  place with a dated marker naming what the text used to say, rather than
  silently rewritten: its Statistics section said "their 1,000-draw
  convention" while its Inference section said 2,000 resamples, and its
  claim that "the two agreed on every cell in this campaign" was written
  before the bootstrap existed and is false, since they disagree on
  exactly the contrast named above. The paper reports the disagreement. An
  orphan results/stats_h1_bootstrap.json, predating the coverage-gap
  correction and never wired into src/rebuild_all.sh, was not used.
  (3) Wording: "the failure mode moves with capability" became, after an
  intermediate version that wrongly implied a strict ordering, "no one
  failure mode covers the seven", followed by which outcome moves for how
  many models. Baseline existence does not order the models the way the
  intermediate wording implied: Grok 4.3 is above Sonnet 5 on it and
  Mistral Small below Qwen3-30B, so neither "the strongest" nor "the 30B
  model" is an endpoint of that ordering, and the old three-way split of
  the range also failed at both ends, since Qwen3-30B loses quotation
  accuracy and Grok 4.3 loses correct quotations per draft. The mediation
  result is now stated as consistent with both
  mechanisms rather than as a decomposition; the precision crossing is
  scoped to this loop; "citation integrity is one with deterministic
  ground truth" became "one whose ground truth is public and
  machine-checkable", since the checker's execution is deterministic and
  its agreement with hand reading is measured, not assumed. (4) To hold
  ten body pages, these were cut and survive in the repository: the
  descriptive split of temporal-arm quotations into authority the model
  also cites at baseline (it conditioned on a post-treatment choice, as
  the sentence itself said, and the pre-1970 stratification asks the same
  question without that defect); the literal-matcher sensitivity on the
  human reference; a duplicate statement of the 0.85-coverage caveat; a
  duplicate statement of Sonnet~5's median-year shift; and the
  jurisdiction-limit contrast in the design rationale for the date clause.
  (5) An adversarial internal-consistency audit of the edited manuscript
  found, and this round fixes, three defects that predate it: the
  provenance sentence in Section 6 attributed its four classes to the 319
  quotations found verbatim elsewhere when they partition Sonnet 5's 249
  inaccurate ones (a set including a class "found nowhere", which the
  wrong antecedent made incoherent); the pinpoint range "55 to 63 for the
  other six" named Llama-4 as the top when Grok 4.3 at 69 is; and "between
  a fifth and a half" described two hand readings of 22 and 35 percent,
  where the half was the union reported in the following sentence. It
  also found four defects this round had introduced: an abstract clause
  whose "of them" read as six of three; a Discussion paragraph left
  saying "the first is" after its second recommendation was cut; a
  mechanism claim in the abstract resting on evidence that had been cut,
  now restated as a shift toward older opinions, which the year-adjusted
  fit does support; and two cross-references to Limitations for results
  that live in Experiment 1. The Discussion's point estimate for checker
  error was also replaced by the range the two readings give.
  (6) A second pass of the same audit, on the corrected manuscript, found
  that fix had been applied in one place and not three. The realised
  precision of a true feedback line was still 0.78 throughout, which is
  one minus the first reader's 22 percent, and the realised crossing was
  derived from it. Since the paper declines to endorse either reading
  alone, src/rounds_control.py now takes the factor as an interval over
  both, 0.65 to 0.781, and the realised crossing widens from 0.44 to 0.52
  to 0.37 to 0.52; the abstract carries the wider range. The same pass
  found four further defects, now fixed: the conclusion's "citation
  existence falls only for the 30B model" was true of the primary fit and
  false of three exploratory ones, and now says so; "paired by matter"
  was the wrong name for the bootstrap's resampling unit and is now "on
  within-matter differences"; the Sonnet paragraph's appellate sentence
  had been orphaned by an earlier trim and its connecting clause is
  restored; and the design rationale's claim that Experiment 1 finds the
  date clause did not reach well-memorized landmarks was cut, since the
  evidence that separated damage to quoting from a change in what is
  quoted is no longer in the paper and the median-year shift is if
  anything consistent with landmarks. Four smaller ones were closed in
  the same pass: "all seven models" now says the fall is numerical, next
  to Sonnet 5's flat count; "numerically highest" now says highest of the
  seven; a 35-to-22 bracket is now 22 to 35; and the true-arm rate range
  now names all three models that reach 1.000 rather than Sonnet 5 alone.
  The README was carrying the reverse of the paper on whether the
  realised crossings bound above or below; the paper is right, they are
  lower bounds, and the README is corrected.
  (7) Four changes from a third reviewer pass, which rated the manuscript
  accept. (a) The sampling rule for the 48 Supreme Court matters is now
  in the paper. It was traced to the companion repository and verified
  against the released manifests: SCDB rows with a term from 1990 to
  2020, an argued decision type, a clean outcome, a docket, and Oyez
  question-and-facts material; a decade-stratified sample of 600 under
  seed 20260723; a shuffle under 20260724; dev, stream and spares; and
  these 48 are the first 48 of dev in manifest order, which this session
  checked element by element against that manifest. The stratification
  binds the 600 and not the head of the shuffle, which is why the
  realised decades are 14, 8, 20 and 6 rather than balanced. An earlier
  attempt at this sentence said "stratified by decade and issue area",
  which is true of the draw and false of these 48; it was written, caught
  against the realised counts, and removed before it reached a build.
  (b) The paper said "three refusals" as a typed number, the only one in
  it not driven by a macro. It could not be reproduced. All 1,344
  pressured drafts exist and were scored; a scan for refusal language
  over all of them returns nothing but ordinary legal use of "decline";
  the two anomalously short drafts, DeepSeek on 2010-065 and GPT-5.4-mini
  on 2000-087, both under the sanctions clause, read as arguments cut off
  mid-sentence, not refusals. The claim is replaced by what is true and
  macro-driven: no draft refuses, and the two that stop under 100 words
  are scored as they stand. (c) The realised precision of a true feedback
  line is now given as what the two readings imply rather than as a
  measured quantity, in the body and in the abstract, since the readers'
  kappa is negative and an interval between two unreliable readings is a
  sensitivity range and not a confidence interval. (d) "Citation
  integrity is one whose ground truth is public and machine-checkable"
  overstated what Section 6 goes on to show, and now says the opinions
  and coordinates are public and machine-checkable while binding a
  quotation to the authority a draft means is heuristic.
