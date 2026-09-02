#!/usr/bin/env python3
"""The paper's two figures, rendered from result artifacts only.

Figure 1: strict quotation accuracy by condition, one line per model,
with the human baseline as a reference band. Reads rescore_full.json,
so it grows automatically when models are added and re-scored.

Figure 2: the repair experiment. Round-0 to final strict accuracy under
true feedback (solid) and scrambled feedback (dashed), per model.
Reads rescore_loops.json.

Outputs PDF and PNG into docs/figures/.
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
    "mistralsmall": "Mistral Small",
}
plt.rcParams.update({
    "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
})


def fig1():
    data = json.loads((HERE / "results/rescore_full.json").read_text())
    human = json.loads((HERE / "results/human_baseline.json").read_text())
    h = human["aggregates"]["overall"]["strict_quote_rate"]

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
    for ax, key, title in (
        (axes[0], "strict_rate", "strict quotation accuracy"),
        (axes[1], "existence_rate", "citation existence"),
    ):
        for model, conds in data.items():
            ys = [conds.get(c, {}).get(key) for c in CONDS]
            ax.plot(range(len(CONDS)), ys, marker="o", markersize=3,
                    linewidth=1.4, label=LABEL.get(model, model))
        ax.set_xticks(range(len(CONDS)))
        ax.set_xticklabels(CONDS, rotation=20)
        ax.set_ylim(0.7 if key == "existence_rate" else 0, 1.02)
        ax.set_title(title)
        if key == "strict_rate":
            ax.axhline(h, color="gray", linewidth=0.8, linestyle=":")
            ax.text(2.6, h - 0.07, f"human lawyers ({h:.2f})",
                    fontsize=7.5, color="gray")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=7, frameon=False, loc="lower center",
               ncol=3, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig1_pressure.{ext}", dpi=200,
                    bbox_inches="tight")
    plt.close(fig)


def fig2():
    data = json.loads((HERE / "results/rescore_loops.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True)
    xs = [0, 1]
    for ax, arm, title in ((axes[0], "true", "true feedback"),
                           (axes[1], "scrambled", "false feedback")):
        for mi, (model, rows) in enumerate(data.items()):
            sub = [r for r in rows if r["arm"] == arm]
            m0 = [r["r0"]["strict"] for r in sub
                  if r["r0"]["strict"] is not None]
            m1 = [r["final"]["strict"] for r in sub
                  if r["final"]["strict"] is not None]
            y = [sum(m0) / len(m0), sum(m1) / len(m1)]
            ax.plot(xs, y, "-", marker="o", markersize=3, color=f"C{mi}",
                    linewidth=1.4, label=LABEL.get(model, model))
        ax.set_xticks(xs)
        ax.set_xticklabels(["round 0", "after revision"])
        ax.set_ylim(0, 1.02)
        ax.set_title(title)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=7, frameon=False, loc="lower center",
               ncol=3, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig2_repair.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    print(f"figures written to {OUT}")
