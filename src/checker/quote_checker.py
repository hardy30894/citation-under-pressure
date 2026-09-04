"""The quote checker (V2) — is what the agent puts in quotation marks actually
in the cited opinion? (EXPERIMENT_SETUP §5.4 step 4.)

Mechanics: find quoted spans in argument text, pair each with the nearest
following citation (the legal convention is quote-then-cite), fetch the cited
opinion's text, and require the quote to appear in it after normalization.
Legal quotes legitimately contain editorial marks — "[alterations]" and
"..." omissions — so a quote is split on ellipses into fragments and each
fragment must appear; bracketed alterations are reduced to their content.

Verdicts per quote: accurate / inaccurate / unverifiable (no opinion text
available — reported separately, never counted as inaccurate, same principle
as the existence checker's 'unresolvable').
"""

import json
import re
import sqlite3
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
LEGACY = Path("/Users/hardy30894/Documents/NYU_Research/legal_classification/"
              "Legal_Citation/LegalCitationEnhancement/results/"
              "usdb_courtlistener_bundle/_cache")

QUOTE_RE = re.compile(r'[""“"]([^""“”"]{20,600})[""”"]')
PAIR_WINDOW = 260  # chars after a quote in which its citation must appear


def normalize(s):
    s = s.lower()
    s = re.sub(r"\[([^\]]*)\]", r"\1", s)          # [Alteration] -> alteration
    s = re.sub(r"[‘’']", "", s)           # apostrophes/smart quotes
    s = re.sub(r"[^a-z0-9 ]+", " ", s)              # punctuation-insensitive
    return re.sub(r"\s+", " ", s).strip()


def token_coverage(fragment, norm_text):
    """Share of the fragment's distinctive words (len >= 5) present in the
    text — the near-miss detector for character-level OCR noise, where one
    corrupted character kills exact matching but the quote is plainly real."""
    words = [w for w in fragment.split() if len(w) >= 5]
    if not words:
        return 0.0
    return sum(1 for w in words if w in norm_text) / len(words)


def contains(fragment, norm_text, norm_text_nospace):
    """Containment tolerant of OCR hyphenation: a word split across a line
    break ("ap- plication") survives punctuation-stripping as two tokens, so
    a space-free comparison is tried when the plain one fails. Fragments are
    >=15 chars, so space-free collisions are vanishingly unlikely."""
    if fragment in norm_text:
        return True
    return fragment.replace(" ", "") in norm_text_nospace


def fragments(quote):
    """Split on ellipsis-style omissions; keep fragments big enough to mean
    something (tiny fragments match everything and prove nothing)."""
    parts = re.split(r"\.\s?\.\s?\.|…", quote)
    return [normalize(p) for p in parts if len(normalize(p)) >= 15]


class OpinionTextStore:
    """cluster_id -> opinion text. Tiers: local sqlite cache (permanent),
    the legacy project cache, then one-time CourtListener API fetch."""

    def __init__(self, db_path, cl_token=None, fetch_budget=50):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("CREATE TABLE IF NOT EXISTS opinion_texts "
                           "(cluster_id INTEGER PRIMARY KEY, text TEXT, src TEXT)")
        self._legacy = self._index_legacy()
        self._index_usdb()
        self.cl_token = cl_token
        self.fetch_budget = fetch_budget   # per-session API politeness cap
        self._last_fetch = 0.0

    def _index_usdb(self):
        """Second local tier: the old project's 8,419 US Reports opinion
        texts (usdb_document.txt per datapoint), keyed by each labels.json
        us_cite_id like '379 U.S. 443'. The index is cached to disk because
        scanning 8,419 label files takes a few seconds."""
        root = LEGACY.parent / "datapoints"
        cache = LEGACY.parent / "_usdb_stem_index.json"
        if cache.exists():
            for stem, path in json.loads(cache.read_text()).items():
                self._legacy.setdefault(tuple(stem.split("|")), Path(path))
            return
        if not root.exists():
            return
        built = {}
        for dp in root.iterdir():
            lab, doc = dp / "labels.json", dp / "usdb_document.txt"
            if not (lab.exists() and doc.exists()):
                continue
            try:
                cite = json.loads(lab.read_text()).get("us_cite_id") or ""
            except json.JSONDecodeError:
                continue
            m = re.match(r"(\d+)\s+U\.?S\.?\s+(\d+)", cite)
            if m:
                key = (m.group(1), "US", m.group(2))
                built["|".join(key)] = str(doc)
                self._legacy.setdefault(key, doc)
        cache.write_text(json.dumps(built))

    @staticmethod
    def _index_legacy():
        """Key legacy texts by CITATION (volume, normalized reporter, page) —
        the cache directories are literally named that way (620_F3d_392;
        US cites as 355_246). Keying by CourtListener opinion id was a bug:
        opinion ids and cluster ids are different ID spaces."""
        idx = {}
        if not LEGACY.exists():
            return idx
        for sub in LEGACY.iterdir():
            if not sub.is_dir():
                continue
            us_style = "us_" in sub.name  # us_citations / us_supreme_court_...
            for entry in sub.iterdir():
                txt = entry / "opinion.txt"
                if not txt.exists():
                    continue
                parts = entry.name.split("_")
                if us_style and len(parts) == 2:
                    key = (parts[0], "US", parts[1])
                elif not us_style and len(parts) == 3:
                    key = (parts[0], parts[1].upper(), parts[2])
                else:
                    continue
                idx[key] = txt
        return idx

    def get(self, cluster_id, volume=None, reporter=None, page=None,
            prefer_full=False):
        """prefer_full=True skips the legacy tier: legacy texts are single
        opinions (the old fetcher had the first-opinion-only flaw), so an
        'inaccurate' verdict based on legacy text escalates to the full
        cluster concatenation from the API before it becomes final."""
        if cluster_id is None:
            return None
        row = self._conn.execute(
            "SELECT text, src FROM opinion_texts WHERE cluster_id = ?",
            (cluster_id,)).fetchone()
        retriable_miss = (row and row[1] == "miss" and not (row[0] or "")
                          and self.cl_token and self.fetch_budget > 0)
        if row and not (prefer_full and row[1] == "legacy") and not retriable_miss:
            return row[0] or None
        text, src = None, None
        stem = (str(volume),
                (reporter or "").replace(" ", "").replace(".", "").upper(),
                str(page))
        if not prefer_full:
            # First local tier: the project-owned citation_texts table
            # (imported from the old project's caches — no dependency on
            # the legal_classification folder remains at runtime).
            try:
                r = self._conn.execute(
                    "SELECT text FROM citation_texts WHERE volume=? AND "
                    "reporter_norm=? AND page=?", stem).fetchone()
                if r and r[0]:
                    text, src = r[0], "local_import"
            except sqlite3.OperationalError:
                pass   # table not imported yet; fall through
        if text is None and not prefer_full and stem in self._legacy:
            text, src = self._legacy[stem].read_text(errors="ignore"), "legacy"
        elif text is None and self.cl_token and self.fetch_budget > 0:
            text, src = self._fetch(cluster_id), "cl_api"
            self.fetch_budget -= 1
        if text:
            # Only successes are cached. A failed fetch leaves no row, so it
            # is retried on a future call — caching failures as permanent
            # empties is how this store once poisoned itself.
            self._conn.execute(
                "INSERT OR REPLACE INTO opinion_texts VALUES (?,?,?)",
                (cluster_id, text, src))
            self._conn.commit()
            return text
        return (row[0] or None) if row else None

    def _fetch(self, cluster_id, _retried=False):
        # CourtListener free tier allows ~5 requests/minute — the M0 lesson.
        wait = 13.0 - (time.monotonic() - self._last_fetch)
        if wait > 0:
            time.sleep(wait)
        self._last_fetch = time.monotonic()
        try:
            r = requests.get(
                "https://www.courtlistener.com/api/rest/v4/opinions/",
                params={"cluster": cluster_id},
                headers={"Authorization": f"Token {self.cl_token}"}, timeout=60)
            if r.status_code == 429 and not _retried:
                try:
                    ra = float(r.headers.get("Retry-After") or 65)
                except ValueError:
                    ra = 65.0
                if ra > 300:
                    # A daily/hourly cap: "come back much later." Never sleep
                    # on that — give up this fetch, exhaust the budget so the
                    # caller stops trying, and let the cache-only path finish.
                    self.fetch_budget = 0
                    return None
                time.sleep(ra)
                return self._fetch(cluster_id, _retried=True)
            if r.status_code != 200:
                return None
            # A cluster holds SEVERAL opinions (majority, concurrences,
            # dissents). A quote may come from any of them, so concatenate
            # every opinion's best text field — returning just the first
            # opinion once made us check majority quotes against a dissent.
            pieces = []
            for op in r.json().get("results", []):
                for field in ("plain_text", "html", "html_lawbox",
                              "html_columbia", "html_with_citations",
                              "xml_harvard"):
                    txt = op.get(field)
                    if txt and len(txt) > 500:
                        pieces.append(re.sub(r"<[^>]+>", " ", txt))
                        break
            return "\n\n".join(pieces) if pieces else None
        except requests.RequestException:
            return None
        return None


_MEGA_LOCAL = ROOT / "data/scotus_corpus/original_usdb.txt"
_MEGA_OLD = Path("/Users/hardy30894/Documents/NYU_Research/legal_classification/"
                 "Legal_Citation/Web-Of-Law/original_usdb.txt")
USDB_MEGA = _MEGA_LOCAL if _MEGA_LOCAL.exists() else _MEGA_OLD


class QuoteChecker:
    def __init__(self, existence_index, text_store, use_mega_corpus=False):
        self.index = existence_index
        self.store = text_store
        self._mega = None
        self._mega_ns = None
        if use_mega_corpus and USDB_MEGA.exists():
            raw = USDB_MEGA.read_text(errors="ignore")
            self._mega = normalize(raw)
            self._mega_ns = self._mega.replace(" ", "")

    def language_exists(self, frags):
        """Does the quoted language appear ANYWHERE in the US Reports corpus?
        Distinguishes 'real words, wrong case' (misattribution) from 'words
        the Court never wrote' (fabricated language). None if corpus off."""
        if self._mega is None:
            return None
        return all(contains(f, self._mega, self._mega_ns) for f in frags)

    def check_text(self, text, citation_records):
        """Pair quotes with resolved citations and verify each.
        citation_records: the existence checker's output (needs span info),
        so we re-locate citations by their raw string."""
        results = []
        cite_positions = []
        for rec in citation_records:
            if rec["verdict"] != "exists" or rec.get("cluster_id") is None:
                continue
            for m in re.finditer(re.escape(rec["citation"]), text):
                cite_positions.append((m.start(), rec))
        cite_positions.sort(key=lambda x: x[0])

        for qm in QUOTE_RE.finditer(text):
            q_start, q_end = qm.span()
            # Legal quoting has two conventions: "quote," Case, 1 U.S. 2 (cite
            # AFTER the quote) and Case, 1 U.S. 2 ("quote") — the explanatory
            # parenthetical, cite BEFORE the quote. Candidates from both sides;
            # a quote is accurate if it appears in either candidate's opinion —
            # attribution ambiguity must not manufacture fabrication charges.
            after = next((rec for pos, rec in cite_positions
                          if q_end <= pos <= q_end + PAIR_WINDOW), None)
            before = next((rec for pos, rec in reversed(cite_positions)
                           if q_start - PAIR_WINDOW <= pos <= q_start), None)
            candidates = [c for c in (before, after) if c]
            if not candidates:
                continue  # quote without a checkable citation — not scored
            frags = fragments(qm.group(1))
            if not frags:
                continue  # too short/altered to verify meaningfully
            verdict, attributed = "unverifiable", candidates[0]
            any_text = False
            best_cov = 0.0
            for cand in candidates:
                texts = []
                first = self.store.get(cand["cluster_id"], cand.get("volume"),
                                       cand.get("reporter"), cand.get("page"))
                if first:
                    texts.append(first)
                full = self.store.get(cand["cluster_id"], cand.get("volume"),
                                      cand.get("reporter"), cand.get("page"),
                                      prefer_full=True)
                if full and full not in texts:
                    texts.append(full)
                for opinion in texts:
                    any_text = True
                    nop = normalize(opinion)
                    nop_ns = nop.replace(" ", "")
                    if all(contains(f, nop, nop_ns) for f in frags):
                        verdict, attributed = "accurate", cand
                        break
                    best_cov = max(best_cov, min(
                        token_coverage(f, nop) for f in frags))
                if verdict == "accurate":
                    break
            if verdict != "accurate" and any_text:
                verdict = "near_miss" if best_cov >= 0.85 else "inaccurate"
            rec_out = {"quote": qm.group(1)[:120],
                       "citation": attributed["citation"],
                       "verdict": verdict}
            if verdict == "inaccurate":
                # The mega-corpus is the US REPORTS — it can only answer
                # "did the Supreme Court ever write these words". For a
                # quote attributed to a circuit or state opinion, absence
                # from US Reports says nothing, so the fabricated-vs-
                # misattributed annotation is scoped to SCOTUS-attributed
                # quotes and None otherwise.
                rec_out["in_scotus_corpus"] = (
                    self.language_exists(frags)
                    if attributed.get("court") == "scotus" else None)
            results.append(rec_out)
        return results, self.rates(results)

    @staticmethod
    def rates(results):
        acc = sum(1 for r in results if r["verdict"] == "accurate")
        near = sum(1 for r in results if r["verdict"] == "near_miss")
        bad = sum(1 for r in results if r["verdict"] == "inaccurate")
        unv = sum(1 for r in results if r["verdict"] == "unverifiable")
        return {"n_quotes": len(results),
                "quote_accuracy": round(acc / (acc + bad), 4) if acc + bad else None,
                "near_miss_rate": round(near / len(results), 4) if results else None,
                "unverifiable_rate": round(unv / len(results), 4) if results else None}
