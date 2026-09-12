"""Hardened quote extraction + attribution for model-generated drafts.

Fixes the two artifact classes the Sonnet-probe audit exposed:

1. Overcapture: the legacy QUOTE_RE, calibrated on plain judicial prose,
   swallows spans of the model's own markdown prose when smart quotes go
   unbalanced. Here a quote is only a balanced smart-quote or same-line
   straight-quote pair, and any span containing paragraph breaks, headers,
   or bold markup is rejected as not-a-quote.

2. Mispairing: legacy pairing attributes a quote to the nearest citation,
   but models quote case X while citing case Y in the same passage.
   Here attribution is signal-phrase first: if a case NAME from the
   draft's own citations appears near the quote, the quote belongs to
   that case; proximity is only the fallback. This is also the seed of
   the name-mismatch detector the design owes the five-way taxonomy.

Verdict bands are unchanged from the calibrated checker (accurate /
near_miss at token coverage >= 0.85 / inaccurate / unverifiable), reusing
its normalize/contains/token_coverage primitives; since 2026-09-05 the
strict standard reads a bracketed alteration as an omission (fragments
below), the literal matcher being kept in alteration_aware.py as the
comparison.
"""

import re
import sys
from pathlib import Path

GE = Path(__file__).resolve().parents[1]  # vendored checker, runtime, sim, packets

from checker.quote_checker import (  # noqa: E402
    normalize,
    fragments as literal_fragments,
    contains,
    token_coverage,
)

# An alteration parenthetical inside the marks is not part of the quotation
ALTERATION_PAREN = re.compile(
    r"\((?:emphasis (?:added|in original|omitted)|citations? omitted|"
    r"internal quotation marks (?:and citations? )?omitted|cleaned up|"
    r"footnote omitted|alterations? (?:in original|omitted))\)", re.I)


def fragments(quote):
    """The strict standard's fragments: split on ellipses and on bracketed
    segments, so that a lawful alteration ("[the defendant]" for "he",
    "[t]he") is read as an omission and the words around it must match;
    fragments under 15 normalized characters are dropped, as in the
    literal matcher this replaces (checker.quote_checker.fragments)."""
    quote = ALTERATION_PAREN.sub(" ", quote)
    parts = re.split(r"\.\s?\.\s?\.|…|\[[^\]]*\]", quote)
    return [normalize(p) for p in parts if len(normalize(p)) >= 15]

SMART_RE = re.compile(r"“([^“”]{20,600})”")
STRAIGHT_RE = re.compile(r'"([^"\n]{20,600})"')
NOT_A_QUOTE = re.compile(r"\n\s*\n|(^|\n)\s*#|\*\*|__")
# a span opening with a dash/closing punctuation is the tail of a quote the
# model split across a citation ("... text—" cite "—more text"): not a quote
# a span that opens or closes with whitespace is the text BETWEEN two
# quotations (a closing mark paired with the next opening mark), not a quote
SPLIT_ARTIFACT = re.compile(r"^\s*[—–)\].,;:]|^\s|\s$")

# words that occur in case names and in ordinary legal prose; a match on
# one of these says nothing about which case a quotation belongs to
NAME_STOP = {
    "united", "states", "state", "people", "commonwealth", "city",
    "county", "board", "school", "court", "company", "corp", "corporation",
    "judicial", "circuit", "district", "rules", "federal", "national",
    "american", "department", "secretary", "commissioner", "attorney",
    "general", "government", "association", "trust", "bank", "insurance",
    "railroad", "railway", "education", "public", "service", "services",
    "administration", "agency", "office", "director", "officer", "council",
    "commission", "committee", "union", "america", "labor", "health",
    "human", "election", "elections", "welfare", "housing", "authority",
    "transportation", "industries", "products", "power", "light", "water",
    "sons", "brothers", "trustees", "estate", "citizens", "society",
}
# among names at the same distance the citation nearest the quotation wins
STATUTE_BEFORE = 60  # a statute marker this close introduces the quotation
# a quotation introduced by a statute, rule, or Congress ("28 U.S.C. §
# 1407(a) provides that ...", "the Act defines ...", "Congress said ...")
# quotes non-case material; with no case name nearer in its signal phrase
# it is left unpaired instead of bound to whatever case citation is nearest
STATUTE_RE = re.compile(
    r"(u\.?s\.?c\.?|c\.?f\.?r\.?|§|fed\. ?r\.|\brule \d|\bstat\.|\bsection \d|\bact\b|"
    r"\bstatute\b|\bcode\b|\bcongress\b|\bthe phrase\b|\bthe term\b|\bprovision\b|"
    r"\bsubsection\b|\bregulation\b|s\. ?rep\.|h\. ?r\. ?rep\.|\bamendment\b|"
    r"\bconstitution\b|\bclause\b|\b(first|second|third|fourth|fifth|sixth|seventh|eighth|"
    r"ninth|tenth|eleventh|d\.c\.|federal) circuit\b|\bdistrict court\b|\bcourt of appeals\b|"
    r"\bthe panel\b|\bthe court below\b|\bthe district\b|\bthe board\b|\bthe agency\b|"
    r"\b(government|petitioners?|respondents?|appellants?|appellees?|plaintiffs?|defendants?|"
    r"the state) (contend|argue|assert|maintain|claim|urge|submit)s?\b|\bcong\. rec\.|"
    r"\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|"
    r"georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|"
    r"massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|"
    r"new jersey|new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|"
    r"pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|"
    r"washington|west virginia|wisconsin|wyoming|state) supreme court\b)", re.I)
CTX_BEFORE = 350
CTX_AFTER = 120
PAIR_WINDOW = 260


def extract_quotes(text):
    seen = set()
    out = []
    for rx in (SMART_RE, STRAIGHT_RE):
        for m in rx.finditer(text):
            q = m.group(1)
            if NOT_A_QUOTE.search(q) or SPLIT_ARTIFACT.match(q):
                continue
            key = (m.start(1), q[:40])
            if key in seen:
                continue
            seen.add(key)
            out.append({"quote": q, "start": m.start(1)})
    out.sort(key=lambda d: d["start"])
    return out


def name_tokens(*names):
    toks = set()
    for n in names:
        if not n:
            continue
        for t in re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", n):
            if t.lower() not in NAME_STOP:
                toks.add(t.lower())
    return toks


CLAIMED_RE = re.compile(r"([A-Z][\w.&'’,-]*(?: [A-Z&][\w.&'’,-]*){0,6}) v\. ([A-Z][\w.&'’,-]*(?: [A-Z&][\w.&'’,-]*){0,6})")


def claimed_name(text, start, window=120):
    """The last "A v. B" the draft writes within `window` characters before
    a citation, markdown emphasis stripped; (A, B) or ()."""
    seg = re.sub(r"[*_]", "", text[max(0, start - window):start])
    m = None
    for m in CLAIMED_RE.finditer(seg):
        pass
    return (m.group(1), m.group(2)) if m else ()


ABBREV = {"v", "u.s", "id", "co", "inc", "cir", "ct", "no", "rep", "app", "stat",
          "corp", "bd", "f", "l.ed", "s.ct", "j", "st", "ry", "r.r", "ass'n", "dep't",
          "mfg", "bros", "ltd", "jr", "sr", "mr", "mrs", "ms", "dr", "ins", "assn",
          "supp", "cal", "n.y", "mass", "pa", "tex", "ill", "va", "u.s.c", "c.f.r",
          "e.g", "i.e", "cf", "sec", "art", "amend", "ed", "vol", "ch", "pp", "p"}


def is_abbrev(word):
    w = word.lower().rstrip(".")
    return w in ABBREV or len(w) <= 1 or re.fullmatch(r"(?:[a-z]\.)+[a-z]?", w) is not None


def sentence_start(seg):
    """Position in `seg` (text ending at the quotation) where the
    quotation's own sentence begins: the last period followed by a space and
    a capital, ignoring the abbreviations of legal citation. 0 if none."""
    pos = 0
    for m in re.finditer(r"\.\s+(?=[A-Z\u201c\"*(\[])", seg):
        word = re.split(r"[\s(,;]", seg[:m.start()].rstrip())[-1]
        if is_abbrev(word):
            continue
        pos = m.end()
    return pos


def sentence_end(seg):
    """Length of the part of `seg` (text after the quotation) that belongs
    to the quotation's own sentence: up to the first real period boundary
    or line break."""
    for m in re.finditer(r"\.\s+(?=[A-Z\u201c\"*(\[])|\n", seg):
        if m.group(0) == "\n":
            return m.start()
        word = re.split(r"[\s(,;]", seg[:m.start()].rstrip())[-1]
        if is_abbrev(word):
            continue
        return m.start()
    return len(seg)


def word_find(hay, tok):
    """First position of tok as a whole word (a party name must not match
    inside a longer word: "under" in "understanding")."""
    m = re.search(r"(?<![a-z])" + re.escape(tok) + r"(?![a-z])", hay)
    return m.start() if m else -1


def word_rfind(hay, tok):
    last = -1
    for m in re.finditer(r"(?<![a-z])" + re.escape(tok) + r"(?![a-z])", hay):
        last = m.start()
    return last


def attribute(q, text, cites):
    """Return (cite, how) for one extracted quote.

    A quotation belongs to the case named in its own sentence before it (the
    signal phrase), else to the citation that follows it directly, else,
    when its sentence carries "Id.", to the nearest preceding citation. A
    quotation introduced by a statute, rule, or lower court is not a case
    quotation and is left unpaired; so is one whose sentence names nothing,
    since the checker then has nothing to test it against. Names in a later
    sentence never take a quotation (the seeded validation's original
    catch), and a citation introduced by "see" or "cf." after the quotation
    is further authority, not its source."""
    qend = q["start"] + len(q["quote"])
    raw_before = text[max(0, q["start"] - CTX_BEFORE): q["start"]]
    sent = sentence_start(raw_before)
    before = raw_before.lower()
    raw_after = text[qend: qend + PAIR_WINDOW]
    tail = sentence_end(raw_after)  # the quotation's own sentence, after it
    after = raw_after[:min(tail, CTX_AFTER)].lower()
    best_before = best_after = None
    cites = [c for c in cites if not c.get("procedural")]
    for c in cites:
        prox = abs(c["start"] - q["start"])  # tie-break: the nearer citation
        for t in c["tokens"]:
            i = word_rfind(before, t)
            if i >= sent and i >= 0:  # the name must sit in the quote's own sentence
                d = len(before) - (i + len(t))
                if best_before is None or (d, prox) < (best_before[0], best_before[2]):
                    best_before = (d, c, prox)
            j = word_find(after, t)
            if j >= 0 and (best_after is None or (j, prox) < (best_after[0], best_after[2])):
                best_after = (j, c, prox)
    # a quotation inside a parenthetical that opens right after a citation
    # ("Case, 1 U.S. 2, 3 (1990) (holding that “...”)") belongs to that
    # citation, whatever follows it in a string cite
    for c in sorted(cites, key=lambda c: -c["start"]):
        if 0 < q["start"] - c["start"] <= 160:
            gap = text[c["start"]: q["start"]]
            if gap.count("(") > gap.count(")") and re.search(r"\(\s*[\w\s,.;:'’-]{0,60}[\u201c\"]?$", gap):
                return c, "parenthetical"
            break
    intro = after.lstrip("\u201d\" .,;:)\n").lstrip()
    further = intro.startswith(("see", "cf.", "accord", "compare", "but see", "e.g."))
    # a name, or a citation, in the rest of the quotation's own sentence is
    # its citation
    after_c = [c for c in cites if 0 <= c["start"] - qend <= tail]
    direct_after = bool(best_after or after_c) and not further
    own = before[sent:]
    stat = None
    for m in STATUTE_RE.finditer(own):
        stat = len(own) - m.end()  # distance to the quote
    if stat is not None and (best_before is None or best_before[0] > stat) and not direct_after:
        return None, None
    if best_before and not direct_after:
        return best_before[1], "named"
    if best_after and not further:
        return best_after[1], "named"
    if after_c and not (further and best_before):
        return min(after_c, key=lambda c: c["start"]), "proximity"
    # "Id." in the quotation's sentence points at the last citation before it
    if re.search(r"\bid\.", own):
        prev = [c for c in cites if c["start"] < q["start"]]
        if prev:
            return max(prev, key=lambda c: c["start"]), "id"
    # else the nearest preceding citation in the same paragraph, as a reader
    # attributes "The Court explained that ..." to the case under discussion
    para = text.rfind("\n", 0, q["start"]) + 1
    before_c = [c for c in cites if para <= c["start"] < q["start"]
                and q["start"] - c["start"] <= PAIR_WINDOW + 40]
    if before_c:
        return max(before_c, key=lambda c: c["start"]), "proximity"
    return None, None


CITATION_GAP = re.compile(r"\d|\b(?:id|ibid|supra)\b")
GAP_MAX = 300


def omitted_citation(fragment, text_norm):
    """A quotation may drop an internal citation without an ellipsis, under
    a "(citation omitted)" or "(cleaned up)" parenthetical or under
    Bluebook 5.2, and the fragment then spans material the opinion has and
    the quotation does not. The fragment passes when it splits at a word
    boundary into two halves of at least 15 characters that the opinion
    contains in order, at most GAP_MAX characters apart, and the gap looks
    like a citation (a digit, or id., ibid., supra)."""
    words = fragment.split()
    for k in range(2, len(words) - 1):
        head, tail = " ".join(words[:k]), " ".join(words[k:])
        if len(head) < 15:
            continue
        if len(tail) < 15:
            break
        start = 0
        while True:
            i = text_norm.find(head, start)
            if i < 0:
                break
            j = text_norm.find(tail, i + len(head), i + len(head) + GAP_MAX + len(tail))
            if j >= 0 and CITATION_GAP.search(text_norm[i + len(head):j]):
                return True
            start = i + 1
    return False


def verdict_for(q, cite, store):
    if cite is None:
        return "unpaired", None
    opinion = (
        store.get(
            cite.get("cluster_id"),
            volume=cite.get("volume"),
            reporter=cite.get("reporter"),
            page=cite.get("page"),
        )
        if cite.get("cluster_id")
        else None
    )
    if not opinion:
        return "unverifiable", None
    frags = fragments(q["quote"])
    if not frags:
        return "no_fragment", None
    text_norm = normalize(opinion)
    nospace = text_norm.replace(" ", "")
    if all(contains(f, text_norm, nospace) or omitted_citation(f, text_norm) for f in frags):
        return "accurate", 1.0
    cov = min(token_coverage(f, text_norm) for f in frags)
    return ("near_miss" if cov >= 0.85 else "inaccurate"), round(cov, 3)


PARALLEL_GAP = 60  # a parallel cite string runs on from the official one
PROCEDURAL = re.compile(r"cert\.?\s*(?:denied|granted|dismissed)|reh'?g\s+denied|"
                        r"aff'?d|rev'?d|vacated|remanded", re.I)


def merge_parallel(cites, text):
    """Collapse a parallel citation string into the citation it repeats.

    A court is cited once in three reporters at a stretch ("418 U.S. 539,
    558, 94 S.Ct. 2963, 2976, 41 L.Ed.2d 935"), and eyecite emits one
    citation per reporter. They are the same case, so a quotation must
    not be attributed to the last of them as though a different court had
    spoken: the name the draft writes belongs to the first. Tokens that
    resolve to the same opinion and sit within PARALLEL_GAP characters of
    the previous one are folded into it, keeping its position and taking
    the union of the name tokens.

    A citation introduced by procedural history ("cert. denied, 456 U.S.
    946") is not a source a draft quotes from; it is marked so that
    attribution passes over it."""
    out = []
    for c in cites:
        prev = out[-1] if out else None
        if (prev is not None and c.get("cluster_id")
                and prev.get("cluster_id") == c["cluster_id"]
                and 0 <= c["start"] - prev["start"] <= PARALLEL_GAP + len(prev["citation"])):
            prev["tokens"] = prev["tokens"] | c["tokens"]
            prev["parallel"] = prev.get("parallel", 0) + 1
            continue
        c["procedural"] = bool(PROCEDURAL.search(text[max(0, c["start"] - 40): c["start"]]))
        out.append(c)
    return out


def check_draft(text, citation_records, eyecite_pass, store):
    """Score every quote in one draft.

    citation_records: from CitationChecker.check_text (verdicts, cluster ids)
    eyecite_pass: list of dicts with citation/start/plaintiff/defendant
                  (spans + party names, which the legacy records drop)
    """
    by_cite = {}
    for r in citation_records:
        by_cite.setdefault(r["citation"], r)
    cites = []
    for e in eyecite_pass:
        rec = by_cite.get(e["citation"], {})
        cites.append(
            {
                "citation": e["citation"],
                "start": e["start"],
                # eyecite's party metadata stops at a markdown asterisk and
                # keeps one word a side, so the case name the draft itself
                # writes before the citation ("*Board of Education v.
                # Doe*, 123 U.S. 4") supplies tokens too
                "tokens": name_tokens(e.get("plaintiff"), e.get("defendant"),
                                      *claimed_name(text, e["start"])),
                "cluster_id": rec.get("cluster_id"),
                "volume": rec.get("volume") or e.get("volume"),
                "reporter": rec.get("reporter") or e.get("reporter"),
                "page": rec.get("page") or e.get("page"),
            }
        )
    cites = merge_parallel(cites, text)
    results = []
    for q in extract_quotes(text):
        cite, how = attribute(q, text, cites)
        verdict, cov = verdict_for(q, cite, store)
        results.append(
            {
                "quote": q["quote"][:120],
                "citation": cite["citation"] if cite else None,
                "attribution": how,
                "verdict": verdict,
                "coverage": cov,
            }
        )
    return results


def strict_rate(results):
    acc = sum(1 for r in results if r["verdict"] == "accurate")
    bad = sum(
        1 for r in results if r["verdict"] in ("near_miss", "inaccurate")
    )
    return round(acc / (acc + bad), 3) if acc + bad else None
