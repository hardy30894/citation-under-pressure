#!/usr/bin/env python3
"""One matrix of the 56 pre-registered contrasts against every fit.

Rows are outcome x model x condition (citation existence and strict
quotation accuracy, seven models, four conditions against baseline);
columns are the fits the paper reports, each with its odds ratio, 95
percent interval, uncorrected p, and Holm p within model over that fit's
own tests: the primary fit (template A), the lenient outcome, distinct
authorities, the literal matcher, name mismatches counted as not found,
template B alone, both templates pooled, three generations pooled, both
tasks pooled, the appellate task alone, and the grounded arm (baseline
and combined only). Writes results/contrast_matrix.csv and a markdown
rendering, results/contrast_matrix.md, with survivors marked."""

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
R = HERE / "results"
MODELS = ["qwen30b", "mistralsmall", "deepseek", "grok43", "sonnet", "gpt54mini", "llama4mav"]
CONDS = ["quota", "temporal", "stakes", "combo"]


def load(path, key=None):
    if not path.exists():
        return {}
    d = json.loads(path.read_text())
    return d[key] if key else d


FITS = [
    ("primary", load(R / "stats_gee.json")),
    ("lenient", load(R / "stats_gee_lenient.json")),
    ("distinct", load(R / "stats_gee_distinct.json")),
    ("literal", load(R / "stats_gee_alt.json")),
    ("mismatch_not_found", load(R / "stats_gee_nm.json")),
    ("template_B", load(R / "stats_gee_para.json")),
    ("templates_pooled", load(R / "stats_gee_pooled.json")),
    ("generations_pooled", load(R / "stats_gee_runs.json")),
    ("tasks_pooled", load(R / "appellate_stats.json", "gee_pooled_tasks")),
    ("appellate", load(R / "appellate_stats.json", "gee")),
    ("grounded", load(R / "grounded_stats.json", "gee")),
]


def main():
    rows = []
    for kind in ("citation", "quote"):
        for m in MODELS:
            for c in CONDS:
                key = f"{kind}:{m}:{c}"
                row = {"outcome": kind, "model": m, "condition": c}
                for name, fit in FITS:
                    v = fit.get(key)
                    if v and v.get("OR") is not None:
                        row[f"{name}_OR"] = v["OR"]
                        row[f"{name}_ci"] = f"{v.get('ci_low')}-{v.get('ci_high')}"
                        row[f"{name}_p"] = v.get("p")
                        row[f"{name}_holm"] = v.get("holm_p")
                    else:
                        for s in ("OR", "ci", "p", "holm"):
                            row[f"{name}_{s}"] = ""
                rows.append(row)
    fields = list(rows[0].keys())
    with open(R / "contrast_matrix.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    # markdown: OR with a star when the Holm p within that fit is below 0.05
    lines = ["# Contrast matrix", "",
             "Odds ratio for each pre-registered contrast under each fit; `*` marks Holm p < 0.05 within model over that fit's tests; blank where the fit has no such cell.", "",
             "| outcome | model | condition | " + " | ".join(n for n, _ in FITS) + " |",
             "|---|---|---|" + "---|" * len(FITS)]
    for r in rows:
        cells = []
        for name, _ in FITS:
            o = r[f"{name}_OR"]
            if o == "":
                cells.append("")
            else:
                h = r[f"{name}_holm"]
                cells.append(f"{o}{'*' if h != '' and h is not None and h < 0.05 else ''}")
        lines.append(f"| {r['outcome']} | {r['model']} | {r['condition']} | " + " | ".join(cells) + " |")
    (R / "contrast_matrix.md").write_text("\n".join(lines) + "\n")
    surv = {name: sum(1 for r in rows if r[f"{name}_holm"] != "" and r[f"{name}_holm"] < 0.05) for name, _ in FITS}
    print("survivors per fit:", surv)


if __name__ == "__main__":
    main()
