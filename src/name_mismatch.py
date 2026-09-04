#!/usr/bin/env python3
"""Name mismatches among resolving citations.

The checker's `exists` label means the volume and page resolve to a real
opinion in the index; the case name is checked separately. For every
resolving citation whose draft names the parties (eyecite's plaintiff
and defendant metadata) and whose index row carries a case name, the
checker sets name_match to whether the two share at least one
non-stopword token; otherwise name_match is None. That flag is unusable
on model drafts as they stand: the drafts italicize case names with
markdown asterisks, eyecite's name extraction stops at the asterisk and
keeps only the party after "v." (usually "United States", all
stopwords), and the flag comes out False for correct citations such as
Mistretta v. United States, 488 U.S. 361. This script therefore redoes
the comparison from the draft text: the "A v. B" span immediately before
the citation, markdown stripped, against the index case name, sharing at
least one non-stopword token; a claimed name with no non-stopword token
is unchecked. It counts, over the full Supreme Court run, per model and
condition: citations that resolve, those with a name check, and
mismatches (the checker's raw flag is kept beside it for the record). A
mismatch is a real volume and page carrying a different case name, the
kind of error a wrong page number produces. Writes
results/name_mismatch.json."""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

from pilot import DB  # noqa: E402  (puts the checker package on the path)
from checker.citation_checker import CitationChecker, SqliteIndex, _name_tokens  # noqa: E402
from records_dump import MODELS  # noqa: E402
from eyecite import get_citations  # noqa: E402
from eyecite.models import FullCaseCitation  # noqa: E402

SEP = re.compile(r"[;:()\n]|\d+\s+[A-Z][A-Za-z. ]*\d+")  # separators and earlier citations


def claimed_name(text, start):
    """The 'A v. B' span ending where the citation begins, markdown
    stripped: the last ' v. ' in the 160 characters before the citation,
    the plaintiff being the words after the last separator or earlier
    citation, the defendant the words up to the citation. None when the
    draft gives no case name there."""
    before = re.sub(r"[*_]", "", text[max(0, start - 160):start])
    k = max(before.rfind(" v. "), before.rfind(" v "))
    if k < 0:
        return None
    left = before[:k]
    seps = [m.end() for m in SEP.finditer(left)]
    plaintiff = left[seps[-1]:] if seps else left
    defendant = before[k + 3:].strip().rstrip(",").strip()
    if SEP.search(defendant):
        return None
    cut = max(plaintiff.rfind(ch) for ch in ("\u201d", '"', "]", ". ", "? ", "! "))
    if cut >= 0:
        plaintiff = plaintiff[cut + 1:]
    plaintiff = " ".join(plaintiff.split()[-6:]).strip(" ,.")
    if not plaintiff or not defendant:
        return None
    return f"{plaintiff} v. {defendant}"


def main():
    index = SqliteIndex(DB)
    out = defaultdict(lambda: Counter())
    examples = []
    for model in MODELS:
        for p in sorted((HERE / "results" / f"full_{model}" / "drafts").glob("*.txt")):
            matter, cond = re.match(r"(.+)_([a-z]+)$", p.stem).groups()
            text = p.read_text()
            c = out[f"{model}:{cond}"]
            for cite in get_citations(text):
                if not isinstance(cite, FullCaseCitation):
                    continue
                g = cite.groups or {}
                if not (g.get("volume") and g.get("reporter") and g.get("page")):
                    continue
                hit = index.lookup(g["volume"], g["reporter"], g["page"])
                if hit is None:
                    continue
                c["exists"] += 1
                # the checker's own flag, for the record
                raw = " ".join(filter(None, [getattr(cite.metadata, "plaintiff", None),
                                             getattr(cite.metadata, "defendant", None)]))
                if raw and hit.get("case_name") and not (_name_tokens(raw) & _name_tokens(hit["case_name"])):
                    c["checker_flag_false"] += 1
                claimed = claimed_name(text, cite.span()[0])
                ctoks = _name_tokens(claimed) if claimed else set()
                itoks = _name_tokens(hit.get("case_name"))
                if not ctoks or not itoks:
                    c["name_unchecked"] += 1
                    continue
                c["name_checked"] += 1
                if not (ctoks & itoks):
                    c["mismatch"] += 1
                    if len(examples) < 40:
                        examples.append({"model": model, "draft": p.stem, "citation": str(cite.corrected_citation()),
                                         "claimed": claimed, "index": hit.get("case_name")})
        print(model, "done", flush=True)
    res = {k: dict(v) for k, v in out.items()}
    pooled = Counter()
    for v in out.values():
        pooled.update(v)
    res["_pooled"] = dict(pooled)
    per_model = defaultdict(Counter)
    for k, v in out.items():
        per_model[k.split(":")[0]].update(v)
    res["_per_model"] = {m: dict(v) for m, v in per_model.items()}
    res["_examples"] = examples
    (HERE / "results" / "name_mismatch.json").write_text(json.dumps(res, indent=1))
    for k in sorted(out):
        v = out[k]
        print(f"{k:24s} exists {v['exists']:5d} checked {v['name_checked']:5d} "
              f"unchecked {v['name_unchecked']:4d} mismatch {v['mismatch']:4d}")
    print("pooled", dict(pooled))


if __name__ == "__main__":
    main()
