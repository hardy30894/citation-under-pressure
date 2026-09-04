"""Local-first opinion text: checker.db tiers, then CAP static volumes.

Answers the "why are we paying CourtListener's rate cap" question: SCDB has
no opinion text, but CAP's static volume archives are free, unauthenticated,
and unrated (static.case.law/{slug}/{vol}.zip) and cover nearly every
reporter through mid-2018, which is almost every authority these drafts
cite. CourtListener drops to last resort.

CapStore.get(volume, reporter, page) downloads the volume zip once into
this project's data/cap_cache, then serves the case whose first_page
matches, caching extracted text in a local sqlite so the zip is parsed
once. The HTML variant (with star-pagination page-labels) is stored too,
feeding the pincite verifier.

ChainTextStore mimics OpinionTextStore.get()'s signature so it drops into
quotecheck2.verdict_for unchanged.
"""

import json
import re
import sqlite3
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
GE = Path(__file__).resolve().parents[1]  # vendored checker, runtime, sim, packets

CAP_DIR = HERE / "data" / "cap_cache"
CACHE_DB = HERE / "data" / "cap_text_cache.sqlite"
SLUG_MAP_PATH = GE / "data/manifests/cap_reporters.json"


def _norm_rep(reporter):
    return (reporter or "").replace(" ", "").replace(".", "").upper()


def _build_slug_map():
    entries = json.loads(SLUG_MAP_PATH.read_text())
    m = {}
    for e in entries:
        if isinstance(e, dict) and e.get("slug") and e.get("short_name"):
            m.setdefault(_norm_rep(e["short_name"]), e["slug"])
    return m


class CapStore:
    def __init__(self):
        CAP_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
        self.slugs = _build_slug_map()
        self.con = sqlite3.connect(CACHE_DB)
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS cap_texts ("
            "slug TEXT, volume TEXT, page TEXT, text TEXT, html TEXT, "
            "PRIMARY KEY (slug, volume, page))"
        )
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS cap_missing ("
            "slug TEXT, volume TEXT, PRIMARY KEY (slug, volume))"
        )

    def _volume_zip(self, slug, volume):
        path = CAP_DIR / f"{slug}_{volume}.zip"
        if path.exists():
            return path
        if self.con.execute(
            "SELECT 1 FROM cap_missing WHERE slug=? AND volume=?",
            (slug, volume),
        ).fetchone():
            return None
        url = f"https://static.case.law/{slug}/{volume}.zip"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "research-cap-fetch/1.0"}
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                path.write_bytes(r.read())
            return path
        except Exception:
            self.con.execute(
                "INSERT OR IGNORE INTO cap_missing VALUES (?,?)",
                (slug, volume),
            )
            self.con.commit()
            return None

    def _import_volume(self, slug, volume, zpath):
        with zipfile.ZipFile(zpath) as z:
            names = [n for n in z.namelist() if n.startswith("json/")]
            for n in names:
                try:
                    d = json.loads(z.read(n))
                except Exception:
                    continue
                page = str(d.get("first_page", ""))
                body = d.get("casebody", {})
                text = "\n".join(
                    op.get("text", "") for op in body.get("opinions", [])
                )
                hname = n.replace("json/", "html/").replace(".json", ".html")
                html = ""
                if hname in z.namelist():
                    html = z.read(hname).decode("utf-8", "ignore")
                self.con.execute(
                    "INSERT OR REPLACE INTO cap_texts VALUES (?,?,?,?,?)",
                    (slug, volume, page, text, html),
                )
        self.con.commit()

    def get(self, volume, reporter, page, want_html=False):
        slug = self.slugs.get(_norm_rep(reporter))
        if not slug or not volume or not page:
            return None
        row = self.con.execute(
            "SELECT text, html FROM cap_texts WHERE slug=? AND volume=? "
            "AND page=?",
            (slug, str(volume), str(page)),
        ).fetchone()
        if row is None:
            zpath = self._volume_zip(slug, str(volume))
            if zpath is None:
                return None
            self._import_volume(slug, str(volume), zpath)
            row = self.con.execute(
                "SELECT text, html FROM cap_texts WHERE slug=? AND volume=?"
                " AND page=?",
                (slug, str(volume), str(page)),
            ).fetchone()
        if row is None:
            return None
        return (row[1] or None) if want_html else (row[0] or None)


LII_DIR = (
    GE.parent / "legal_classification/Legal_Citation/"
    "LegalCitationEnhancement/results/us_scotus_retrieval/opinion_full_text"
)


def lii_text(volume, reporter, page):
    """Last local tier: the old project's LII web-scrape cache, keyed
    {vol}_{page}.txt. Noisy (site boilerplate) but covers post-2018 SCOTUS
    volumes that CAP lacks. U.S. Reports only."""
    if _norm_rep(reporter) != "US":
        return None
    p = LII_DIR / f"{volume}_{page}.txt"
    if not p.exists():
        return None
    raw = p.read_text(errors="ignore")
    # strip the leading LII site chrome: opinion bodies follow the last
    # occurrence of the syllabus/opinion marker words; fall back to raw
    m = re.search(r"delivered the opinion|Per Curiam|PER CURIAM", raw)
    return raw[m.start():] if m else raw


class ChainTextStore:
    """OpinionTextStore-compatible: checker.db tiers (incl. the legacy
    legal_classification cache the store already consults), then CAP
    static volumes, then the LII scrape cache; the wrapped store's remote
    CL tier only fires if it was built with budget."""

    def __init__(self, opinion_store, cap_store=None):
        self.local = opinion_store
        self.cap = cap_store or CapStore()

    @property
    def fetch_budget(self):
        return getattr(self.local, "fetch_budget", 0)

    def get(self, cluster_id, volume=None, reporter=None, page=None,
            prefer_full=False):
        text = self.local.get(
            cluster_id, volume=volume, reporter=reporter, page=page,
            prefer_full=prefer_full,
        )
        if text:
            return text
        text = self.cap.get(volume, reporter, page)
        if text:
            return text
        return lii_text(volume, reporter, page)


PAGE_LABEL_RE = re.compile(r'page-label[^>]*>\s*\*?(\d+)')


def html_pages(html, first_page=None):
    """Split CAP HTML into {page_number: text} using page-label markers;
    the star-pagination substrate for pincite verification. Text before
    the first label belongs to the case's first page (labels mark page
    BREAKS), so pass first_page to keep it."""
    if not html:
        return {}
    parts = PAGE_LABEL_RE.split(html)
    pages = {}
    if first_page is not None and parts[0].strip():
        pages[int(first_page)] = re.sub(r"<[^>]+>", " ", parts[0])
    # parts: [pre, num, seg, num, seg, ...]
    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        seg = re.sub(r"<[^>]+>", " ", parts[i + 1])
        pages[num] = seg
    return pages
