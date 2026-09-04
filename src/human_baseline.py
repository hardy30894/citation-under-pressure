"""Human-lawyer strict quote-accuracy baseline on LePhantomCite clean excerpts.

Scores the 482 clean (no injected hallucination) brief-derived excerpts from
ai-law-society-lab/Legal_Phantom_Citation with our validated quote instrument
(quotecheck2 on top of the CourtListener-backed citation checker). The Dahl
et al. 300 LLM-generated entries (non-.pdf filenames) are excluded, as are the
518 excerpts with injected errors, so what remains is real pre-ChatGPT federal
appellate brief text written by human lawyers. The aggregate answers: when a
human lawyer quotes a case, how often does the quote survive our strict check?

Outputs results/human_baseline.json. No LLM calls; CourtListener fetches are
capped by fetch_budget=120 inside OpinionTextStore.
"""

import json
import os
import sys
import time
import traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))

from rescore_pilots import eyecite_pass  # noqa: E402  (also loads local .env)
from checker.citation_checker import CitationChecker, SqliteIndex  # noqa: E402
from checker.quote_checker import OpinionTextStore  # noqa: E402
from runtime.llm_client import load_env_key  # noqa: E402
import quotecheck2 as q2  # noqa: E402

DATA_DIR = os.path.join(BASE, "data", "lephantomcite")
OUT_PATH = os.path.join(BASE, "results", "human_baseline.json")
from pilot import DB  # noqa: E402

QUOTE_VERDICTS = ("accurate", "near_miss", "inaccurate", "unverifiable", "unpaired")


def load_clean_excerpts():
    """Clean brief-derived excerpts from both splits.

    Brief-derived entries carry a *.pdf source filename; the 300 Dahl et al.
    entries use bare numeric ids and are dropped. Clean means the
    list_hallucinations dict is empty, meaning no injected error of any type.
    """
    rows = []
    for split in ("eval", "aux_train"):
        with open(os.path.join(DATA_DIR, f"{split}.jsonl")) as f:
            for line in f:
                r = json.loads(line)
                if not r["filename"].endswith(".pdf"):
                    continue  # Dahl et al. subset
                if r["list_hallucinations"]:
                    continue  # injected error present
                rows.append({"split": split, "filename": r["filename"], "text": r["text"]})
    return rows


def aggregate(per_excerpt, subset_name, keep):
    """Sum quote verdicts and existence counts over excerpts where keep(e)."""
    agg = {v: 0 for v in QUOTE_VERDICTS}
    exists = not_found = unresolvable = 0
    n = 0
    for e in per_excerpt:
        if e.get("error") or not keep(e):
            continue
        n += 1
        for v in QUOTE_VERDICTS:
            agg[v] += e["quote_verdicts"].get(v, 0)
        exists += e["exists"]
        not_found += e["not_found"]
        unresolvable += e["unresolvable"]
    scored = agg["accurate"] + agg["near_miss"] + agg["inaccurate"]
    resolvable = exists + not_found
    return {
        "subset": subset_name,
        "n_excerpts": n,
        "quote_verdicts": agg,
        "n_quotes_total": sum(agg.values()),
        "n_quotes_scored": scored,
        "strict_quote_rate": round(agg["accurate"] / scored, 4) if scored else None,
        "citations": {
            "exists": exists,
            "not_found": not_found,
            "unresolvable": unresolvable,
        },
        "existence_rate": round(exists / resolvable, 4) if resolvable else None,
    }


def main():
    rows = load_clean_excerpts()
    print(f"clean brief-derived excerpts: {len(rows)}", flush=True)

    index = SqliteIndex(DB)
    checker = CitationChecker(index)
    from local_text import ChainTextStore
    store = ChainTextStore(OpinionTextStore(DB, cl_token=None,
                                            fetch_budget=0))

    per_excerpt = []
    errors = []
    t0 = time.time()
    for i, row in enumerate(rows):
        entry = {"split": row["split"], "filename": row["filename"]}
        try:
            recs, rates = checker.check_text(row["text"])
            res = q2.check_draft(row["text"], recs, eyecite_pass(row["text"]), store)
            counts = {v: 0 for v in QUOTE_VERDICTS}
            for r in res:
                counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
            entry.update(
                quote_verdicts=counts,
                exists=sum(1 for r in recs if r["verdict"] == "exists"),
                not_found=sum(1 for r in recs if r["verdict"] == "not_found"),
                unresolvable=sum(1 for r in recs if r["verdict"] == "unresolvable"),
                n_citations=len(recs),
                quotes=[
                    {"quote": r["quote"][:120], "citation": r["citation"],
                     "verdict": r["verdict"], "coverage": r.get("coverage")}
                    for r in res
                ],
            )
        except Exception as exc:  # keep going; report crashes in the aggregate
            entry["error"] = f"{type(exc).__name__}: {exc}"
            errors.append(entry["error"])
            traceback.print_exc()
        per_excerpt.append(entry)
        if (i + 1) % 25 == 0:
            print(f"[{i + 1}/{len(rows)}] {time.time() - t0:.0f}s "
                  f"fetch_budget_left={store.fetch_budget}", flush=True)

    ok = [e for e in per_excerpt if not e.get("error")]
    overall = aggregate(per_excerpt, "all_clean", lambda e: True)
    # Oracle-resolved-only: every citation in the excerpt resolved to an
    # existing case in our index/CourtListener, with coverage gaps removed.
    resolved = aggregate(
        per_excerpt,
        "all_citations_exist",
        lambda e: e["n_citations"] > 0 and e["not_found"] == 0 and e["unresolvable"] == 0,
    )
    # Softer variant: at least one citation resolved.
    any_resolved = aggregate(per_excerpt, "any_citation_exists", lambda e: e["exists"] > 0)

    out = {
        "dataset": "ai-law-society-lab/Legal_Phantom_Citation",
        "selection": "brief-derived (.pdf filename), empty list_hallucinations; "
                     "Dahl et al. 300 non-pdf entries excluded",
        "n_clean_excerpts": len(rows),
        "n_scored": len(ok),
        "n_crashed": len(errors),
        "crash_examples": errors[:3],
        "fetch_budget_remaining": store.fetch_budget,
        "aggregates": {
            "overall": overall,
            "oracle_resolved_only": resolved,
            "any_citation_resolved": any_resolved,
        },
        "per_excerpt": per_excerpt,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in
                      ("n_clean_excerpts", "n_scored", "n_crashed")}, indent=2))
    print(json.dumps(out["aggregates"]["overall"], indent=2))
    print(json.dumps(out["aggregates"]["oracle_resolved_only"], indent=2))
    print(f"wrote {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
