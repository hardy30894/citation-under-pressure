#!/usr/bin/env python3
"""The paper's two figures, rendered from result artifacts only.

Figure 1: strict quotation accuracy by condition, one line per model,
with the human baseline as a reference band. Reads rescore_full.json,
so it grows automatically when models are added and re-scored.

Figure 2: verifier precision against what revision does, from
rescore_loops.json and loop_transitions.json.

Both figures are drawn at the IOS Press type-area width (12.4 cm) so
that the fonts print at their nominal size; IOS requires lettering of at
least 6 points. Outputs PDF and PNG into docs/figures/.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

CONDS = ["baseline", "quota", "temporal", "stakes", "combo"]
LABEL = {
    "qwen30b": "Qwen3-30B", "deepseek": "DeepSeek V4 Flash",
    "gpt54mini": "GPT-5.4-mini", "sonnet": "Sonnet 5",
    "llama4mav": "Llama-4 Maverick", "glm47flash": "GLM-4.7-flash",
    "mistralsmall": "Mistral Small", "grok43": "Grok 4.3",
}
WIDTH_IN = 12.4 / 2.54  # IOS Press type-area width
plt.rcParams.update({
    "font.size": 7, "axes.titlesize": 8, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "legend.fontsize": 6.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42,
})


def fig1():
    data = json.loads((HERE / "results/rescore_full.json").read_text())
    human = json.loads((HERE / "results/human_baseline.json").read_text())
    h = human["aggregates"]["overall"]["strict_quote_rate"]

    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, 1.3))
    for ax, key, title in (
        (axes[0], "strict_rate", "strict quotation accuracy"),
        (axes[1], "existence_rate", "citation existence"),
    ):
        for model, conds in data.items():
            ys = [conds.get(c, {}).get(key) for c in CONDS]
            ax.plot(range(len(CONDS)), ys, marker="o", markersize=3,
                    linewidth=1.4, label=LABEL.get(model, model))
        ax.set_xticks(range(len(CONDS)))
        ax.set_xticklabels(["base", "quota", "temporal", "stakes", "combined"])
        if key == "existence_rate":
            ax.set_ylim(0.7, 1.02)
            ax.set_yticks([0.7, 0.8, 0.9, 1.0])
        else:
            ax.set_ylim(0, 1.02)
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.grid(axis="y", linewidth=0.3, alpha=0.5)
        ax.set_title(title)
        if key == "strict_rate":
            ax.axhline(h, color="gray", linewidth=0.8, linestyle=":",
                       label=f"human lawyers, floor ({h:.2f})")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="lower center",
               ncol=4, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig1_pressure.{ext}", dpi=200,
                    bbox_inches="tight")
    plt.close(fig)


def fig2():
    """Verifier precision against what revision does: final strict
    accuracy and the share of accurate round-0 quotations removed, at
    precision 0 (all flags false), 0.25, 0.5, 0.75, 1 (all true), with no
    feedback as the leftmost point."""
    data = json.loads((HERE / "results/rescore_loops.json").read_text())
    trans = json.loads((HERE / "results/loop_transitions.json").read_text())
    arms = [("none", "none"), ("scrambled", "0"), ("quarter", "0.25"),
            ("half", "0.5"), ("threequarter", "0.75"), ("true", "1")]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, 1.3))
    for mi, (model, rows) in enumerate(data.items()):
        strict, removed = [], []
        for arm, _ in arms:
            sub = [r for r in rows if r["arm"] == arm]
            m1 = [r["final"]["strict"] for r in sub
                  if r["final"]["strict"] is not None]
            strict.append(sum(m1) / len(m1) if m1 else float("nan"))
            c = trans[model]
            acc0 = sum(c.get(f"{arm}:accurate:{k}", 0) for k in (
                "kept:accurate", "edited:accurate", "kept:flagged",
                "edited:flagged", "dequoted", "deleted"))
            gone = sum(c.get(f"{arm}:accurate:{k}", 0) for k in (
                "kept:flagged", "edited:flagged", "dequoted", "deleted"))
            removed.append(gone / acc0 if acc0 else float("nan"))
        xs = range(len(arms))
        axes[0].plot(xs, strict, marker="o", markersize=3, linewidth=1.4,
                     color=f"C{mi}", label=LABEL.get(model, model))
        axes[1].plot(xs, removed, marker="o", markersize=3, linewidth=1.4,
                     color=f"C{mi}")
    for ax, title in ((axes[0], "final strict quotation accuracy"),
                      (axes[1], "share of correct quotations removed")):
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels([lab for _, lab in arms])
        ax.set_xlabel("verifier precision (share of true flags)")
        ax.set_ylim(0, 1.02)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.grid(axis="y", linewidth=0.3, alpha=0.5)
        ax.set_title(title)
        ax.axvline(0.5, color="gray", linewidth=0.6, linestyle=":")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="lower center",
               ncol=4, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.15, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig2_repair.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    print(f"figures written to {OUT}")
