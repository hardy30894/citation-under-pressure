#!/bin/sh
# Builds the JURIX paper the way IOS Press asks (pdflatex + bibtex).
# A user-level TeX Live lives in ~/texlive-portable if the system has none.
set -e
cd "$(dirname "$0")"
export PATH="$HOME/texlive-portable/bin/universal-darwin:$PATH"
/opt/anaconda3/bin/python3 ../../src/emit_macros.py
pdflatex -interaction=nonstopmode paper.tex >/dev/null
bibtex paper >/dev/null
pdflatex -interaction=nonstopmode paper.tex >/dev/null
pdflatex -interaction=nonstopmode paper.tex >/dev/null
grep -E "^! |Overfull|Undefined|multiply|Warning: (Citation|Reference)" paper.log || echo "clean build"
