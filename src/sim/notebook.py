"""The notebook — the evolving agent's only mutable state.

A notebook is an append-only JSONL of lesson events (crash-safe, torn-line
tolerant, same discipline as runtime.state). Arms A and B differ ONLY in
which lessons their gates allow in; this module is arm-agnostic — it
stores, retires, and retrieves. A lesson enters via add() after its gate
decision, leaves via retire() (canary rollback), and is retrieved for a new
case by cosine similarity over embeddings.

Retrieval embedder: a deterministic hashed bag-of-words (unigrams +
bigrams, md5-hashed into 512 dims, L2-normalized). Offline, dependency-free
and reproducible byte-for-byte — replay of a run retrieves identical
lessons. Pluggable behind the Embedder interface; if M2 swaps in a neural
embedder, the embedder name recorded with every run manifest pins which one
produced each result. Embeddings are recomputed from text on load, never
persisted, so the store stays embedder-independent.
"""

import hashlib
import json
import math
import os
import re


class HashingEmbedder:
    """Deterministic hashed bag-of-words. Same text -> same vector, on any
    machine, forever."""

    name = "hashing-bow-v1"
    dim = 512

    def embed(self, text):
        toks = re.findall(r"[a-z0-9]+", text.lower())
        vec = [0.0] * self.dim
        for term in toks + [f"{a} {b}" for a, b in zip(toks, toks[1:])]:
            h = int.from_bytes(
                hashlib.md5(term.encode()).digest()[:8], "big")
            vec[h % self.dim] += 1.0 if (h >> 62) & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm:
            vec = [x / norm for x in vec]
        return vec


# Relevance floor for retrieval, set at the M2 pilot's p90 of top-5
# similarity: unfiltered retrieval matched the case's legal area at chance
# (16.2%) while wins rose 4 points where relevance was accidentally high.
# Below the floor a lesson is noise; empty beats irrelevant.
RETRIEVE_MIN_SIM = 0.55


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


class Notebook:
    """Crash-safe lesson store for one run."""

    def __init__(self, path, embedder=None):
        self.path = str(path)
        self.embedder = embedder or HashingEmbedder()
        self.lessons = {}       # id -> lesson dict (live only)
        self.n_added = 0        # monotone counter, includes retired
        self._load()
        self._fh = open(self.path, "a", encoding="utf-8")

    def _load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue  # torn final line from a crash — ignore
                if ev["op"] == "add":
                    self.lessons[ev["id"]] = ev
                    self.n_added = max(self.n_added, ev["seq"])
                elif ev["op"] == "retire":
                    self.lessons.pop(ev["id"], None)
        for les in self.lessons.values():
            les["_vec"] = self.embedder.embed(les["text"])

    def _write(self, ev):
        self._fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def add(self, text, *, case_id, meta=None):
        """Record an accepted lesson. Returns its id. Call only after the
        arm's gate has said yes — the notebook holds no gate logic."""
        self.n_added += 1
        lid = f"L{self.n_added:04d}"
        ev = {"op": "add", "id": lid, "seq": self.n_added,
              "case_id": case_id, "text": text, "meta": meta or {}}
        self._write(ev)
        ev["_vec"] = self.embedder.embed(text)
        self.lessons[lid] = ev
        return lid

    def retire(self, lesson_id, reason=""):
        """Remove a lesson (canary rollback). Append-only: the add stays in
        the log; a retire event supersedes it."""
        if lesson_id in self.lessons:
            self._write({"op": "retire", "id": lesson_id, "reason": reason})
            del self.lessons[lesson_id]

    def retrieve(self, query_text, k=5, min_sim=None,
                 allow_case_ids=None):
        """Top-k live lessons by cosine similarity to the query, ties broken
        by recency (higher seq first). Returns lesson dicts, best first.

        min_sim: relevance floor. The M2 pilot measured that unfiltered
        top-5 retrieval matched the case's legal area at chance (16.2%)
        while wins rose 4 points exactly where relevance was accidentally
        high — so below the floor a lesson is noise, and an empty result
        beats an irrelevant one."""
        if not self.lessons:
            return []
        pool = self.lessons.values()
        if allow_case_ids is not None:
            # domain-keyed retrieval (the imx finding, Hardy's design
            # decision 2026-07-27): legal knowledge is domain-bound —
            # matched lessons +8.3pp, mismatched lessons inert. Only
            # lessons whose SOURCE case is in the allowed set (same
            # issue area, computed harness-side from pre-decision
            # metadata) may be injected; none beats mismatched.
            pool = [l for l in pool if l["case_id"] in allow_case_ids]
            if not pool:
                return []
        q = self.embedder.embed(query_text)
        scored = sorted(
            ((cosine(q, l["_vec"]), l) for l in pool),
            key=lambda t: (-t[0], -t[1]["seq"]))
        out = []
        for sim, l in scored[:k]:
            if min_sim is not None and sim < min_sim:
                break
            out.append({**{k2: v for k2, v in l.items() if k2 != "_vec"},
                        "retrieval_sim": round(sim, 4)})
        return out

    def size(self):
        return len(self.lessons)

    def close(self):
        self._fh.close()
