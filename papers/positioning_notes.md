# Close-reading notes on the four positioning papers

Full-text reads completed 2026-08-31 (all via arXiv HTML). These notes record what each paper actually did, the quotes that position us, and the pitfalls their methods reveal. One exactness caveat is flagged inline and must be resolved before any manuscript quotes it.

## 1. LePhantomCite, arXiv:2606.21155 (Liu, Stammbach, Henderson; Princeton)

The legal hallucination *detection* benchmark: 1,300 excerpt entries (1,000 built from 245 real pre-ChatGPT federal appellate briefs with injected errors, 300 re-verified entries from Dahl et al.), 4,499 citation instances, 1,107 hallucinated. Taxonomy grounded in 1,000+ real sanctioned filings.

Their five error categories, which we adopt as our outcome coding:
1. **Non-existent citation**, corresponds to no real case.
2. **Case name mismatch**, name and reporter cite each real, but refer to different cases. (So existence must be checked on the *pairing*, not the components.)
3. **Incorrect pincite**, right case, cited page does not support the language.
4. **Verbatim misquote**, quoted language does not appear in the cited case (injected as 1–2 word synonym swaps).
5. **Content misrepresentation**, real case, does not support the proposition. (The one category no deterministic check reaches, where Goodharting will hide.)

**VERSION CORRECTION (2026-09-01, read directly from the v2/COLM camera-ready PDF with pdftotext).** The v1 HTML numbers previously recorded here (GPT-5 pincite recall 18.2, misquote 82.6, misrepresentation 84.0) do NOT match v2, which is the citable version. The paper's numbers changed between arXiv versions. Correct per-category agentic recall, Appendix **Table A6** (there is no "Table 8"; the model is "Qwen3.6-27B" not 3.5):

| Type | Gemini 2.5 Flash | GPT-5 | GPT-OSS 120B | Qwen3-8B | Qwen3.6-27B | Claude Code (Opus 4.8) |
|---|---|---|---|---|---|---|
| Non-existent citation | 100.0 | 100.0 | 83.9 | 58.1 | 100.0 | 93.5 |
| Case name mismatch | 100.0 | 100.0 | 84.2 | 49.1 | 96.5 | 83.8 |
| Incorrect pincite | 18.9 | **52.8** | 26.4 | 18.9 | 50.9 | 3.6 |
| Verbatim misquote | 78.6 | **95.2** | 42.9 | 31.0 | 64.3 | 71.7 |
| Content misrepresentation | 60.3 | **83.2** | 51.1 | 45.8 | 48.9 | 66.4 |

The load-bearing quotes survive v2 verbatim and were re-verified against the PDF text: "no models can reliably detect wrong pincites. Page number information for many cases is..."; "broader public access to legal databases, or verification systems built on top of commercial platforms"; the 65.9% CourtListener false-positive figure; "naturally occurring examples." Aggregate agentic recall (Table 2, v2): Gemini 66.9, GPT-5 84.4, GPT-OSS 55.1, Qwen3-8B 41.1, Qwen3.6-27B 65.0, Claude Code 62.8. Lesson recorded: always verify against the latest PDF version; v1 HTML and v2 PDF of the same arXiv id disagreed on headline numbers.

The quotes that hand us our niche:
- "No models can reliably detect wrong pincites. Page number information for many cases is only accessible through Westlaw and LexisNexis."
- "Improving automated verification performance will thus require either broader public access to legal databases, or verification systems built on top of commercial platforms."
- "We therefore encourage future work to complement our dataset with naturally occurring examples" (their injections are semi-synthetic; our factorial *elicits* natural fabrications).

Operational pitfalls they hit: Gemini flagged 65.9% of CourtListener-absent citations as hallucinated (coverage gaps masquerade as fabrication); 19.9% of retrieved opinions lacked usable text or pagination; 36.7% of false negatives came from the 30-step cap; duplicate lookups in 39.7% of episodes.

## 2. Deployment-constraints factorial, arXiv:2603.07287 (Zhao, Tang, Qian)

The skeleton we transplant. 144 claims × 5 conditions × 4 models = 2,880 runs, 17,443 citations, temperature 0, no retrieval. Conditions: baseline (exactly 5 citations), temporal (recent-year window), survey (8 citations, categorized synthesis), non-disclosure (persona constraint), combo. Full prompt templates live in their GitHub replication package (Zerichen/Citation-Hallucination), fetch during design.

Key numbers: temporal constraint moves Claude's existence rate from 0.381 to 0.119 (bootstrap Δ −0.261); combo to 0.106; GPT-4o collapses to 0.005 under combo. But the survey condition (MORE citations demanded) *raised* Claude's existence (+0.094) — pressure effects are not monotone. Temporal *violations* stay near zero throughout: models obey the year window and fill it with fabrications ("compliance without substance") — report violation rate and existence rate as separate endpoints.

Their verification pipeline is the weak point we replace: fuzzy metadata scoring with 0.85/0.60 thresholds, κ=0.63 on audit, and an Unresolved bucket covering 36–61% of citations of which nearly half were actually fabricated. Our oracle is deterministic — but we inherit the obligation to characterize our own coverage boundary or "fabricated" attracts the same false-positive critique.

Their qualitative failure typology, transplantable as our fabrication coding scheme: venue laundering → reporter laundering; author bricolage → party-name bricolage; title drift → case-name drift; identifier fabrication → invented volume/page.

Named limitations we answer: "we do not check whether a verified citation supports the claim; citation–claim alignment is an important next step" (that is our Goodhart arm); one fixed phrasing per claim (we add a paraphrase subsample). They ran no formal statistical models — bootstrap CIs only; we should fit mixed-effects logistic regression on top.

## 3. LegalCiteBench, arXiv:2605.10186 (Chen, Yin, Zhou)

Closed-book citation reliability over 1,000 recent CAP cases, five subtasks, 21 models. Retrieval-style citation recall is catastrophic closed-book (best 6.80/100). The design element to steal: **Misleading Answer Rate**, the fraction of failing responses that still assert a concrete citation rather than abstain; 89–99.8% across models, >94% on retrieval-heavy tasks for everything except gpt-5-mini. Ungrounded models essentially never abstain. Consequence for us: log abstention as a distinct outcome in every cell, or condition effects on fabrication confound with refusal shifts.

Evaluates quote accuracy nowhere; their error-detection corruptions are metadata-level only. Their future-work item 1 — "developing retrieval-augmented approaches that ground citation generation in verified legal databases" — is our loop arm, with a deterministic rather than LLM verifier. Their named weakness (GPT-4o-mini as judge) is our selling point: four of five error categories judged deterministically.

## 4. RLEF, arXiv:2410.02089 (Gehring et al., Meta)

Protocol shape for the verifier loop: feedback as a natural-language message appended to the dialog, one template per failure type, specific mismatch enumerated ("Expected X but got Y"), closing with an invitation to retry; up to 3 turns default, best at 5 in ablation; terminate early on all-pass; last draft is final, no reranking.

Two imported warnings that define our loop arm's controls: (a) *untrained* base models often gain little from execution feedback at fixed budget — so a null in our loop arm is a real possibility, not a strawman; (b) their random-feedback ablation (trained models recover under true feedback, are severely impaired under scrambled feedback) gives us the clean control: a **scrambled-feedback arm** separates "feedback content is used" from "more attempts help," and doubles as the sharpest Goodhart detector — a model that swaps to real-but-irrelevant citations under true feedback but not scrambled feedback is demonstrably steering to the verifier.

## Release artifacts located (2026-08-31)

LePhantomCite is fully released: dataset at huggingface.co/datasets/ai-law-society-lab/Legal_Phantom_Citation, code at github.com/princeton-polaris-lab/legal-hallucination-agent. This makes the jury-calibration step concrete: their content-misrepresentation category carries expert-validated labels (95% inter-rater agreement on their audit sample), and our order-debiased relevance jury can be calibrated against those labels before it scores anything of ours, converting the design's one non-deterministic instrument into a validated one, at zero API cost beyond the jury calls themselves.

The 2603.07287 replication repo (github.com/Zerichen/Citation-Hallucination, Apache 2.0) confirms the template conventions to adapt: "Write ONE concise academic paragraph... with exactly {n} citations, under 300 words" (baseline); "every cited paper MUST be within the time window ({start}–{end})" (temporal); the survey condition organizes into 3–4 categories. Note their fifth condition is called "privacy" in code (non-disclosure in the paper). Their human-audit files are in the repo too (pipeline-to-human agreement 68%, κ=0.52 — even weaker than the paper's stated κ=0.63, which strengthens our deterministic-upgrade pitch; use the repo number with care since it may cover a different batch).

## The five slots the literature names as missing that we fill

1. Pincite ground truth at scale (LePhantomCite's stated cause of the pincite failure (52.8% best-model recall in v2): no public pagination access, we have US Reports star pagination locally).
2. Deterministic verbatim-quote verification (evaluated as ground truth by no one, in any of the four).
3. Naturally occurring elicited hallucinations (LePhantomCite explicitly requests them).
4. Grounded generation loop over a verified legal database (LegalCiteBench's future-work item 1).
5. Citation–claim alignment under verification pressure (2603.07287's named next step; our relevance jury).
