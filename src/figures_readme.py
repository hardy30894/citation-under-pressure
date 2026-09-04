#!/usr/bin/env python3
"""Two figures for the README that the paper has no room for.

fig3_repair.png: for each model, what happened to the quotations the
checker flagged at round 0 under true feedback (bare flag) and under the
passage arm (the flag carries the closest passage of the cited opinion):
repaired (in place or replaced by an accurate quotation on the same
citation), dequoted, deleted, left. Reads results/loop_transitions.json.

fig4_selection.png: Sonnet 5 across the five conditions, the strict
quotation rate beside the quotations and accurate quotations per draft,
the selection effect in one picture. Reads results/records.jsonl.
"""

import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "docs" / "figures"
LABEL = {"qwen30b": "Qwen3-30B", "mistralsmall": "Mistral Small", "deepseek": "DeepSeek V4 Flash",
         "grok43": "Grok 4.3", "sonnet": "Sonnet 5", "llama4mav": "Llama-4 Maverick", "gpt54mini": "GPT-5.4-mini"}
ORDER = ["qwen30b", "mistralsmall", "deepseek", "grok43", "sonnet", "llama4mav", "gpt54mini"]
CONDS = ["baseline", "quota", "temporal", "stakes", "combo"]
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "pdf.fonttype": 42})


def fig3():
    t = json.loads((HERE / "results/loop_transitions.json").read_text())
    fates = [("repaired", ("kept:accurate", "edited:accurate", "replaced"), "#2a7"),
             ("dequoted", ("dequoted",), "#fc6"),
             ("deleted", ("deleted",), "#c33"),
             ("left flagged", ("kept:flagged", "edited:flagged"), "#999")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, arm, title in ((axes[0], "true", "bare flag (true feedback)"), (axes[1], "passage", "flag carrying the closest passage")):
        bottoms = [0.0] * len(ORDER)
        for name, keys, color in fates:
            vals = []
            for m in ORDER:
                c = t.get(m, {})
                total = sum(v for k, v in c.items() if k.startswith(f"{arm}:flagged:"))
                n = sum(c.get(f"{arm}:flagged:{k}", 0) for k in keys)
                vals.append(100 * n / total if total else 0)
            ax.bar(range(len(ORDER)), vals, bottom=bottoms, color=color, label=name, width=0.7)
            bottoms = [b + v for b, v in zip(bottoms, vals)]
        ax.set_xticks(range(len(ORDER)))
        ax.set_xticklabels([LABEL[m] for m in ORDER], rotation=30, ha="right")
        ax.set_title(title)
        ax.set_ylim(0, 100)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("share of quotations flagged at round 0 (%)")
    axes[1].legend(frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.suptitle("What each model did with the quotations the checker flagged", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_repair.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def fig4():
    cell = {}
    for l in open(HERE / "results/records.jsonl"):
        r = json.loads(l)
        if r["model"] != "sonnet" or r["kind"] != "quote":
            continue
        d = cell.setdefault(r["condition"], Counter())
        d["all"] += 1
        if r["verdict"] in ("accurate", "near_miss", "inaccurate"):
            d["scored"] += 1
            d["acc"] += r["verdict"] == "accurate"
    xs = range(len(CONDS))
    rate = [cell[c]["acc"] / cell[c]["scored"] for c in CONDS]
    per_draft = [cell[c]["all"] / 48 for c in CONDS]
    acc_draft = [cell[c]["acc"] / 48 for c in CONDS]
    fig, ax1 = plt.subplots(figsize=(7, 3.4))
    ax1.bar([x - 0.2 for x in xs], per_draft, width=0.4, color="#bbd", label="quotations per draft")
    ax1.bar([x + 0.2 for x in xs], acc_draft, width=0.4, color="#2a7", label="accurate quotations per draft")
    ax1.set_ylabel("per draft")
    ax1.set_xticks(list(xs)); ax1.set_xticklabels(["baseline", "quota", "temporal", "stakes", "combined"])
    ax2 = ax1.twinx()
    ax2.plot(list(xs), rate, marker="o", color="#c33", linewidth=2, label="strict rate over attributed quotations")
    ax2.set_ylim(0, 1.0); ax2.set_ylabel("strict quotation accuracy")
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
    ax1.set_title("Sonnet 5: the rate rises while it quotes less")
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_selection.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig3()
    fig4()
    print("written", OUT / "fig3_repair.png", OUT / "fig4_selection.png")
