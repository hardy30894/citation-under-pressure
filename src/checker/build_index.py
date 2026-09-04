"""Build the checker's SQLite index from CourtListener bulk data.

Streams the bz2 CSVs directly (never decompresses to disk) and keeps only the
columns the checker needs, so ~2.6 GB of downloads become a few GB of indexed
SQLite instead of ~20 GB of raw CSV. Idempotent: safe to re-run; each table is
rebuilt only if its source file is present and the table is missing or --force.

Tables:
  citations(volume TEXT, reporter TEXT, page TEXT, cluster_id INTEGER)
      + index on (volume, reporter, page)       <- the existence oracle
  clusters(id INTEGER PRIMARY KEY, case_name TEXT, date_filed TEXT,
           court_id TEXT)                        <- name/year/court/anachronism
  courts(id TEXT PRIMARY KEY, full_name TEXT, jurisdiction TEXT)
"""

import bz2
import csv
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/courtlistener"
DB = DATA / "checker.db"
SNAPSHOT = "2026-06-30"

csv.field_size_limit(sys.maxsize)


def stream(name):
    path = DATA / f"{name}-{SNAPSHOT}.csv.bz2"
    if not path.exists():
        return None
    fh = bz2.open(path, "rt", newline="")
    return csv.DictReader(fh)


def build_citations(conn):
    rows = stream("citations")
    if rows is None:
        print("citations file missing; skipped")
        return
    conn.execute("DROP TABLE IF EXISTS citations")
    conn.execute("CREATE TABLE citations (volume TEXT, reporter TEXT, "
                 "page TEXT, cluster_id INTEGER)")
    batch, n, t0 = [], 0, time.time()
    for r in rows:
        batch.append((r["volume"], r["reporter"], r["page"],
                      int(r["cluster_id"])))
        if len(batch) >= 50_000:
            conn.executemany("INSERT INTO citations VALUES (?,?,?,?)", batch)
            n += len(batch)
            batch.clear()
    if batch:
        conn.executemany("INSERT INTO citations VALUES (?,?,?,?)", batch)
        n += len(batch)
    conn.execute("CREATE INDEX idx_cite ON citations (volume, reporter, page)")
    conn.commit()
    print(f"citations: {n:,} rows in {time.time()-t0:.0f}s")


def build_clusters(conn):
    """Resync-robust parser: the clusters CSV contains multi-line quoted
    fields and at least one quote-desync landmine, so instead of trusting
    one continuous csv parse, we split records on the unmistakable
    record-start pattern ("<digits>","<timestamp>...) and parse each record
    individually. Records that still fail to parse are counted and logged,
    never silently absorbed. Columns kept: id(0), date_filed(4),
    case_name(8), scdb_id(10), docket_id(33)."""
    import io
    import re
    path = DATA / f"opinion-clusters-{SNAPSHOT}.csv.bz2"
    if not path.exists():
        print("opinion-clusters file missing; skipped")
        return
    record_start = re.compile(r'^"\d{1,10}","\d{4}-\d{2}-\d{2} ')
    conn.execute("DROP TABLE IF EXISTS clusters")
    conn.execute("CREATE TABLE clusters (id INTEGER PRIMARY KEY, "
                 "case_name TEXT, date_filed TEXT, scdb_id TEXT, "
                 "docket_id INTEGER)")

    def parse_record(buf, batch, stats):
        text = "".join(buf)
        try:
            row = next(csv.reader(io.StringIO(text)))
        except (csv.Error, StopIteration):
            stats["failed"] += 1
            return
        if len(row) < 34 or not row[0].strip().isdigit():
            stats["failed"] += 1
            return
        batch.append((int(row[0]), row[8], row[4], row[10],
                      int(row[33]) if row[33].strip().isdigit() else None))
        stats["ok"] += 1

    batch, buf = [], []
    stats = {"ok": 0, "failed": 0}
    t0 = time.time()
    with bz2.open(path, "rt", newline="") as fh:
        fh.readline()  # header
        for line in fh:
            if record_start.match(line) and buf:
                parse_record(buf, batch, stats)
                buf = []
            buf.append(line)
            if len(batch) >= 20_000:
                conn.executemany(
                    "INSERT OR REPLACE INTO clusters VALUES (?,?,?,?,?)", batch)
                batch.clear()
        if buf:
            parse_record(buf, batch, stats)
    if batch:
        conn.executemany(
            "INSERT OR REPLACE INTO clusters VALUES (?,?,?,?,?)", batch)
    conn.commit()
    print(f"clusters: {stats['ok']:,} rows ok, {stats['failed']:,} failed "
          f"({100*stats['failed']/max(1,sum(stats.values())):.3f}%) "
          f"in {time.time()-t0:.0f}s")


def build_courts(conn):
    rows = stream("courts")
    if rows is None:
        print("courts file missing; skipped")
        return
    conn.execute("DROP TABLE IF EXISTS courts")
    conn.execute("CREATE TABLE courts (id TEXT PRIMARY KEY, full_name TEXT, "
                 "jurisdiction TEXT)")
    for r in rows:
        conn.execute("INSERT OR REPLACE INTO courts VALUES (?,?,?)",
                     (r["id"], r.get("full_name", ""),
                      r.get("jurisdiction", "")))
    conn.commit()
    print("courts: done")


if __name__ == "__main__":
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")  # bulk build; checker reads only
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "citations"):
        build_citations(conn)
    if which in ("all", "clusters"):
        build_clusters(conn)
    if which in ("all", "courts"):
        build_courts(conn)
    conn.close()
    print(f"index at {DB}")
