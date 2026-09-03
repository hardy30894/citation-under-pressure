#!/usr/bin/env python3
"""Retrieval for the grounded condition.

For each of the 48 matters, find the ten U.S. Reports opinions most
similar to the matter's question and facts among the opinions decided
before the matter was argued, and save each with its citation, case
name, year, and the 250-word passage that best matches the query. The
corpus is the U.S. Reports text already cached from the Caselaw Access
Project (data/cap_text_cache.sqlite, slug "us"), so every retrieved
citation exists by construction. Case names and decision dates come from
the CourtListener-derived index. The argued case itself is excluded by
citation lookup and by name.

Similarity is TF-IDF cosine (sublinear term frequency) over the first
2,500 words of each opinion; the best passage is the 250-word window
with the most query-term overlap. Writes results/retrieval/<matter>.json."""

import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from pilot import GE, DB, pick_matters, case_view  # noqa: E402
from checker.citation_checker import SqliteIndex  # noqa: E402
from local_text import CACHE_DB  # noqa: E402

OUT = HERE / "results" / "retrieval"
TOP = 10
HEAD_WORDS = 2500
WINDOW = 250
STOP = set("the of and to in a that is for it as on be by with was this or are "
           "from at an which not have has had his their its he she they we our "
           "were been but were also any all such may would could shall does did "
           "than then there these those where whether under over into upon".split())


def tokens(s):
    return re.findall(r"[a-z][a-z']+", s.lower())


def best_window(text, query_terms):
    words = text.split()
    if len(words) <= WINDOW:
        return " ".join(words)
    best, best_score = 0, -1
    step = 50
    for i in range(0, len(words) - WINDOW + 1, step):
        chunk = words[i:i + WINDOW]
        score = sum(1 for w in chunk if w.lower().strip(".,;:()") in query_terms)
        if score > best_score:
            best, best_score = i, score
    return " ".join(words[best:best + WINDOW])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CACHE_DB)
    rows = con.execute(
        "SELECT volume, page, text FROM cap_texts WHERE slug='us' AND length(text) > 2000"
    ).fetchall()
    print(f"{len(rows)} U.S. Reports opinions", flush=True)
    index = SqliteIndex(DB)
    meta = []
    docs = []
    for vol, page, text in rows:
        hit = index.lookup(vol, "U.S.", page)
        if not hit or not hit.get("date_filed"):
            continue
        meta.append({"volume": vol, "page": page, "name": hit["case_name"] or "",
                     "date": hit["date_filed"][:10]})
        docs.append(" ".join(text.split()[:HEAD_WORDS]))
    print(f"{len(docs)} with name and date", flush=True)
    vec = TfidfVectorizer(sublinear_tf=True, min_df=3, max_df=0.5,
                          stop_words="english", dtype=np.float32)
    X = vec.fit_transform(docs)
    dates = np.array([m["date"] for m in meta])
    full_text = {(r[0], r[1]): r[2] for r in rows}
    for entry in pick_matters(48):
        packet = json.loads((GE / "data/packets" / entry["packet"]).read_text())
        view = case_view(packet)
        query = f"{view.question} {view.facts}"
        q = vec.transform([query])
        sims = (X @ q.T).toarray().ravel()
        argued = str(view.argued_date)[:10]
        parties = {view.petitioner.lower(), view.respondent.lower()}
        qterms = {t for t in tokens(query) if t not in STOP and len(t) > 3}
        order = np.argsort(-sims)

        def pick(cutoff):
            # cutoff: latest allowed decision date; the temporal conditions
            # use 1970-01-01 so that a retrieval tool honouring the
            # instruction supplies authorities the drafter may cite
            picked = []
            for i in order:
                m = meta[i]
                if m["date"] >= min(argued, cutoff):
                    continue
                name_l = m["name"].lower()
                if any(p and p in name_l for p in parties):
                    continue
                picked.append({
                    "citation": f"{m['volume']} U.S. {m['page']}",
                    "name": m["name"], "year": m["date"][:4],
                    "score": round(float(sims[i]), 4),
                    "excerpt": best_window(full_text[(m["volume"], m["page"])], qterms),
                })
                if len(picked) == TOP:
                    break
            return picked

        out = {"all": pick("9999"), "pre1970": pick("1970-01-01")}
        (OUT / f"{entry['id']}.json").write_text(json.dumps(out, indent=1))
        print(entry["id"], [p["citation"] for p in out["all"][:3]],
              [p["citation"] for p in out["pre1970"][:3]], flush=True)


if __name__ == "__main__":
    main()
