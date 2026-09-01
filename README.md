# Citation Under Pressure

**Status: Phase 0 (design). No API spend yet. Nothing here is frozen.**

This project asks two questions about legal citation fabrication that nobody has answered with a real measurement instrument, and answers them with the deterministic citation oracle we already built and calibrated.

**Question 1 — the cause.** Everyone knows LLMs fabricate legal citations; the sanctions cases pile up monthly. But the existing literature only *detects* fabrication after the fact. Nobody has run a controlled study of what *conditions* make a legal drafting model fabricate. Does arguing the losing side of a case do it? Does demanding "cite at least eight authorities"? Does restricting the model to pre-1970 precedent, where its knowledge is thinner? A March 2026 study (arXiv:2603.07287) ran exactly this factorial for *scholarly* citations and found that temporal and combined constraints crater citation existence below 50% while the output stays perfectly format-compliant — the model keeps producing confident, well-formatted citations that do not exist. No one has run the legal version, even though law is where fabricated citations get people sanctioned.

**Question 2 — the cure's side effect, which is the headline.** The obvious fix is to put a citation verifier inside the drafting loop: the model drafts, a checker flags every citation that doesn't exist or misquotes its source, the model revises. Code-generation research proved this "execution-grounded feedback" paradigm works for programs, where the test suite is the verifier. Nobody has done it in law, because nobody else has a deterministic legal verifier fast enough to sit inside a loop. But the deep question is not whether verification reduces fabrication — of course it does, it's a hard constraint. The question is what the model does *instead*. When a model under pressure to cite eight authorities can no longer invent them, does it produce honest arguments with fewer citations, or does it Goodhart — swap in citations that are real but irrelevant, or real but subtly misused, which survive the existence check while being just as dangerous to a filing? If substitution happens, that is a general finding about verifier-in-the-loop generation, not just a legal one: hard verifiers on the checkable property can displace fabrication into the unverifiable gap next door.

## Why we are the ones positioned to do this

Three assets exist in `../us_courts_gated_evolution` (referenced by path; nothing large is copied here):

The **citation oracle** (`data/courtlistener/checker.db`, 4.6GB, ~18M citation rows): deterministic existence checking calibrated at 96.3% on human citations, in one local lookup. For comparison, the best published detection agent (GPT-5 in LePhantomCite, arXiv:2606.21155) needs 15.3 web-search steps per excerpt and still catches only 18.2% of bad pincites — a failure its authors attribute to lacking exactly the authoritative corpus we have locally.

The **quote checker** (same repo, `src/checker`): verbatim quote-fidelity verification validated by seeded faults — genuine quotes 50/50 accurate, fabricated 25/25 caught, subtle corruptions 40/40 caught as near-miss. This is what lets the verifier loop check *misquotation*, not just existence.

The **500 leakage-clean case packets** (`data/packets`): argument tasks built from question presented plus lower-court opinion, with outcome text scrubbed and every packet leakage-scanned. These give the drafting prompts a realistic advocacy setting without contamination worries, because we are measuring citation behavior, not outcome accuracy.

One more instrument matters for Question 2: the **order-debiased jury** protocol (each pair judged in both display orders, only order-consistent verdicts count), developed and validated in the parked gated-evolution project. Existence and quote accuracy are read off the oracle deterministically, but *relevance* of a real citation is a judgment call, and that jury protocol is how we make LLM judgment usable.

## What we already know that shapes the design

From the gated-evolution campaign's own measurements: a 30B open model (Qwen3-30B) fabricates roughly 12–22% of its citations out of the box under ordinary advocacy prompts, while frontier models (Sonnet, DeepSeek Pro) sit at 98–99% citation existence in the same setting. So fabrication-at-rest is a small-model disease. That sharpens Question 1 into its most interesting form: **can deployment pressure reintroduce fabrication at frontier scale?** The scholarly-citation study says yes for academia (even strong models collapsed under temporal constraints). If the same holds in law, the safety story changes from "use a bigger model" to "no model is safe under the wrong prompt" — and if it doesn't hold, that is an equally publishable boundary on the phenomenon. Either way the cell has a finding in it. This no-null-outcome property is a deliberate design choice.

## The experiment in one worked example

Take packet for a 1996 criminal-procedure case. The model is told: argue the petitioner's side; you must cite at least eight authorities; use only authority decided before 1970. It produces a brief section citing, say, *Mapp v. Ohio, 367 U.S. 643* (real, on point), *Terry v. Ohio, 392 U.S. 1* (real, arguably relevant), and *Harlow v. Colgate, 358 U.S. 212* (does not exist — invented under quota pressure). The oracle flags the third in milliseconds. In the verifier-loop arm, that flag goes back to the model as structured feedback and it revises; we then ask whether the replacement is honest (a real, relevant case), a Goodhart substitution (real case, wrong proposition), or an honest retreat (fewer citations, hedged argument). Every draft in every condition is scored the same three ways: existence (oracle), quote fidelity (checker), and relevance-of-real-citations (jury).

## Phases and cost

**Phase 0 (now, free):** close reading of the four positioning papers (LePhantomCite 2606.21155; deployment-constraints factorial 2603.07287; LegalCiteBench 2605.10186; RLEF 2410.02089), then the frozen design doc and pre-registration. See `docs/HYPOTHESES.md` for the draft hypotheses and decision rules.

**Phase 1 (pilot, ~$10–15, needs explicit go):** one model, a slice of the factorial, ~30–50 drafts. Purpose: validate prompt wording, confirm the oracle's coverage on *generated* citations (it was calibrated on curated ones), and measure per-draft cost.

**Phase 2 (full run, ~$60–120, needs explicit go):** full factorial across 3–4 models spanning the capability ladder (one ~30B open model where fabrication lives, one mid-tier, one or two frontier), plus the verifier-in-the-loop arm with the substitution measurement.

Hard budget cap for the whole project: $200. Target venue: EMNLP/ACL main if the Goodhart result is strong, NLLP/Findings as the solid floor.

## Repository layout

    README.md            — this file
    docs/HYPOTHESES.md   — draft pre-registration: hypotheses, endpoints, decision rules
    docs/DESIGN.md       — full experimental design (written after the Phase 0 reading pass)
    papers/              — notes on the four positioning papers
    src/                 — experiment code (none yet; reuses the runtime harness and checker from us_courts_gated_evolution)
    results/             — run outputs (none yet)

## Provenance and rules of the road

This project inherits the working rules that earned their place in the previous two projects: no run launches without Hardy's explicit go after a cost-and-time pitch; a forking-paths ledger is kept from the first analysis onward; numbers are copied, never retyped; and any claim intended for the paper must survive on a second model before it becomes a headline sentence.
