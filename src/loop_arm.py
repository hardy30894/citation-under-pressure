#!/usr/bin/env python3
"""Experiment 2: verifier-in-the-loop drafting with a scrambled-feedback
control (RLEF protocol shape; DESIGN.md).

Episodes: 24 matters x combo condition x {true, scrambled} feedback x one
model per invocation. Round 0 reuses the full factorial's cached combo
draft when present. Up to 3 revision rounds; early stop on all-checks-pass;
cap-exhaustion recorded separately from failure.

True feedback: one structured line per failed deterministic check
(nonexistent citation / non-verbatim quote). Scrambled control: same
number of lines, same templates, but pointing at randomly chosen VERIFIED
items: informative-looking, content-free. A model that improves under
true but not scrambled feedback is using feedback content; substitution
that appears only under true feedback is steering to the verifier.

Ledger note: loop arm runs on the combo cell only (budget); recorded at
freeze in LEDGER.md.
"""

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from pilot import (  # noqa: E402  (also loads local .env)
    MODELS, MAX_TOKENS_BY_MODEL, GE, DB, task_message, pick_matters,
)
from runtime.llm_client import LLMClient, LLMCache, Meter, BudgetStop, \
    load_env_key  # noqa: E402
from runtime.state import RunState  # noqa: E402
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa
from checker.quote_checker import OpinionTextStore  # noqa: E402
from sim.prompts import case_view  # noqa: E402
from rescore_pilots import eyecite_pass  # noqa: E402
import quotecheck2 as q2  # noqa: E402

N_MATTERS = 24
MAX_ROUNDS = 3
LOOP_BUDGET = {"qwen30b": 2.0, "deepseek": 3.0, "gpt54mini": 8.0,
               "sonnet": 15.0, "llama4mav": 3.0, "glm47flash": 3.0, "mistralsmall": 3.0}

FB_CITE = (
    "The citation {c} does not correspond to any real case: it does not "
    "resolve in the court reporter database. Remove it or replace it with "
    "real authority."
)
FB_QUOTE = (
    "The quoted passage beginning “{q}…” does not appear "
    "verbatim in the opinion of {c}. Quote the opinion's actual language "
    "or remove the quotation marks."
)
FB_HEAD = (
    "A citation verification system checked your draft against the "
    "official reporters. The following problems must be fixed. Revise the "
    "full argument section, correcting ONLY these problems while "
    "preserving your argument:\n"
)


def score(text, checker, qchk_store):
    recs, rates = checker.check_text(text)
    qres = q2.check_draft(text, recs, eyecite_pass(text), qchk_store)
    return recs, rates, qres


def feedback_lines(recs, qres, arm, rng):
    true_lines = []
    for r in recs:
        if r["verdict"] == "not_found":
            true_lines.append(FB_CITE.format(c=r["citation"]))
    for r in qres:
        if r["verdict"] in ("inaccurate", "near_miss") and r["citation"]:
            true_lines.append(
                FB_QUOTE.format(q=r["quote"][:60], c=r["citation"])
            )
    if arm == "true" or not true_lines:
        return true_lines
    # scrambled: same count, templates aimed at VERIFIED items
    ok_cites = [r["citation"] for r in recs if r["verdict"] == "exists"]
    ok_quotes = [
        (r["quote"][:60], r["citation"])
        for r in qres if r["verdict"] == "accurate" and r["citation"]
    ]
    lines = []
    for _ in true_lines:
        if ok_quotes and rng.random() < 0.5:
            qt, c = rng.choice(ok_quotes)
            lines.append(FB_QUOTE.format(q=qt, c=c))
        elif ok_cites:
            lines.append(FB_CITE.format(c=rng.choice(ok_cites)))
    return lines


def summarize(recs, rates, qres):
    qs = [r["verdict"] for r in qres]
    return {
        "n_citations": rates["n_citations"],
        "existence_rate": rates["existence_rate"],
        "n_quotes": len(qs),
        "q_accurate": qs.count("accurate"),
        "q_near": qs.count("near_miss"),
        "q_inacc": qs.count("inaccurate"),
        "q_unver": qs.count("unverifiable"),
        "strict": q2.strict_rate(qres),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=MODELS, required=True)
    ap.add_argument("--n-matters", type=int, default=N_MATTERS)
    ap.add_argument("--slice", default=None,
                    help="a:b matter-index range for parallel workers")
    args = ap.parse_args()

    run_dir = HERE / "results" / f"loop_{args.model}"
    run_dir.mkdir(parents=True, exist_ok=True)
    meter = Meter(run_dir / "tokens.log")
    cache = LLMCache(run_dir / "cache.sqlite")
    client = LLMClient(
        name=f"loop-{args.model}",
        base_url="https://openrouter.ai/api/v1",
        key_names=("OPENROUTER_TOKEN", "OPENROUTER_KEY"),
        rpm=120, tpm=1_500_000, meter=meter, cache=cache,
        budget_ceiling=LOOP_BUDGET[args.model], **MODELS[args.model],
    )
    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    store = OpinionTextStore(
        DB, cl_token=load_env_key("COURTLISTENER_TOKEN"), fetch_budget=60
    )
    state = RunState(run_dir / "run", control_dir=run_dir)
    state.install_signal_handlers()

    full_drafts = HERE / "results" / f"full_{args.model}" / "drafts"
    episodes = []
    try:
        lo, hi = 0, args.n_matters
        if args.slice:
            lo, hi = (int(x) for x in args.slice.split(":"))
        for mi, entry in enumerate(pick_matters(48)[:args.n_matters]):
            if not (lo <= mi < hi):
                continue
            packet = json.loads(
                (GE / "data/packets" / entry["packet"]).read_text()
            )
            view = case_view(packet)
            side = "petitioner" if mi % 2 == 0 else "respondent"
            for arm in ("true", "scrambled"):
                if state.should_stop():
                    print("pause requested")
                    return
                ep_id = f"{entry['id']}:{arm}"
                if state.is_done(f"ep:{ep_id}"):
                    continue
                rng = random.Random(f"loop:{ep_id}:20260831")
                messages = task_message(view, side, "combo")
                d0 = full_drafts / f"{entry['id']}_combo.txt"
                draft = d0.read_text() if d0.exists() else client.chat(
                    messages, temperature=0.0,
                    max_tokens=MAX_TOKENS_BY_MODEL[args.model],
                    tag=f"r0:{ep_id}",
                )
                rounds = []
                converged = False
                for rnd in range(MAX_ROUNDS + 1):
                    recs, rates, qres = score(draft, checker, store)
                    rounds.append(summarize(recs, rates, qres))
                    lines = feedback_lines(recs, qres, arm, rng)
                    true_left = feedback_lines(recs, qres, "true", rng)
                    if not true_left:
                        converged = True
                        break
                    if rnd == MAX_ROUNDS or not lines:
                        break
                    messages = messages + [
                        {"role": "assistant", "content": draft},
                        {"role": "user",
                         "content": FB_HEAD + "\n".join(
                             f"- {ln}" for ln in lines)},
                    ]
                    draft = client.chat(
                        messages, temperature=0.0,
                        max_tokens=MAX_TOKENS_BY_MODEL[args.model],
                        tag=f"r{rnd + 1}:{ep_id}",
                    )
                    (run_dir / "drafts").mkdir(exist_ok=True)
                    (run_dir / "drafts" / f"{entry['id']}_{arm}_r{rnd + 1}.txt"
                     ).write_text(draft)
                ep = {
                    "episode": ep_id, "arm": arm, "matter": entry["id"],
                    "side": side, "rounds": rounds, "converged": converged,
                    "cap_exhausted": not converged and len(rounds) > MAX_ROUNDS,
                }
                episodes.append(ep)
                state.record(f"ep:{ep_id}", "episode_done", ep)
                print(
                    f"{ep_id:24s} rounds={len(rounds)} conv={converged} "
                    f"strict {rounds[0]['strict']}->{rounds[-1]['strict']} "
                    f"exist {rounds[0]['existence_rate']}->"
                    f"{rounds[-1]['existence_rate']} "
                    f"cost=${meter.total_cost():.3f}"
                )
    except BudgetStop as e:
        print(f"BUDGET STOP: {e}")

    (run_dir / "report.json").write_text(json.dumps(
        {"model": args.model, "episodes": episodes,
         "cost": round(meter.total_cost(), 4)}, indent=2))
    print(f"done: {len(episodes)} episodes, ${meter.total_cost():.3f}")


if __name__ == "__main__":
    main()
