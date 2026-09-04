"""One-time import: curate the old project's opinion texts INTO this project.

Hardy's requirement: the project's data lives in the project — no runtime
dependency on the sprawling legal_classification folder (5.2 GB, mostly
things we don't need). This script walks the three useful sources there and
imports only the texts, citation-keyed, into checker.db:

  citation_texts(volume, reporter_norm, page, text, src)

~48K texts, ~2.5 GB of files, into one indexed SQLite table. After it runs,
OpinionTextStore reads this table (plus the API tier) and never touches the
old folder again. Also copies the 360 MB US Reports mega-corpus into
data/scotus_corpus/. Idempotent; re-running refreshes rows.
"""

import json
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/courtlistener/checker.db"
OLD = Path("/Users/hardy30894/Documents/NYU_Research/legal_classification/Legal_Citation")
CACHE = OLD / "LegalCitationEnhancement/results/usdb_courtlistener_bundle/_cache"
DATAPOINTS = OLD / "LegalCitationEnhancement/results/usdb_courtlistener_bundle/datapoints"
MEGA_SRC = OLD / "Web-Of-Law/original_usdb.txt"
MEGA_DST = ROOT / "data/scotus_corpus/original_usdb.txt"


def rows_from_cache():
    """The citation-stem-named cache dirs (620_F3d_392; US cites as 355_246)."""
    for sub in CACHE.iterdir():
        if not sub.is_dir():
            continue
        us_style = "us_" in sub.name
        for entry in sub.iterdir():
            txt = entry / "opinion.txt"
            if not txt.exists():
                continue
            parts = entry.name.split("_")
            if us_style and len(parts) == 2:
                yield parts[0], "US", parts[1], txt, "legacy_us"
            elif not us_style and len(parts) == 3:
                yield parts[0], parts[1].upper(), parts[2], txt, "legacy_fed"


def rows_from_datapoints():
    """The 8,419 US Reports opinions, keyed by each labels.json us_cite_id."""
    for dp in DATAPOINTS.iterdir():
        lab, doc = dp / "labels.json", dp / "usdb_document.txt"
        if not (lab.exists() and doc.exists()):
            continue
        try:
            cite = json.loads(lab.read_text()).get("us_cite_id") or ""
        except json.JSONDecodeError:
            continue
        m = re.match(r"(\d+)\s+U\.?S\.?\s+(\d+)", cite)
        if m:
            yield m.group(1), "US", m.group(2), doc, "legacy_usdb"


def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS citation_texts (volume TEXT, "
        "reporter_norm TEXT, page TEXT, text TEXT, src TEXT, "
        "PRIMARY KEY (volume, reporter_norm, page))")
    t0, n = time.time(), 0
    for source in (rows_from_cache, rows_from_datapoints):
        for vol, rep, page, path, src in source():
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            if len(text) < 200:
                continue
            # INSERT OR IGNORE: first writer wins, so the dedicated cache
            # texts take precedence over datapoint duplicates
            conn.execute(
                "INSERT OR IGNORE INTO citation_texts VALUES (?,?,?,?,?)",
                (vol, rep, page, text, src))
            n += 1
            if n % 5000 == 0:
                conn.commit()
                print(f"  {n:,} imported ({time.time()-t0:.0f}s)", flush=True)
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM citation_texts").fetchone()[0]
    by_src = dict(conn.execute(
        "SELECT src, COUNT(*) FROM citation_texts GROUP BY src").fetchall())
    conn.close()
    print(f"citation_texts: {total:,} rows {by_src} in {time.time()-t0:.0f}s")

    MEGA_DST.parent.mkdir(parents=True, exist_ok=True)
    if MEGA_SRC.exists() and not MEGA_DST.exists():
        shutil.copy2(MEGA_SRC, MEGA_DST)
        print(f"mega-corpus copied: {MEGA_DST} "
              f"({MEGA_DST.stat().st_size/1e6:.0f} MB)")


if __name__ == "__main__":
    main()
