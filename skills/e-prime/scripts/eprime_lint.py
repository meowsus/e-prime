#!/usr/bin/env python3
"""eprime_lint — a deterministic detector for every form of the verb "to be".

E-Prime (Bourland's E' = E - e) omits every inflected form of "to be". Language
models obey that ban poorly on first pass (studies report ~48-52% compliance),
so this script supplies the ground truth the model itself cannot.

Categories
----------
to_be        core form: be, am, is, are, was, were, been, being
contraction  I'm, you're, it's, isn't, wasn't, ain't, 'twas, thou art, ...
being_noun   "being" in noun/gerund use ("human being", "well-being"):
             still a violation under strict E-Prime; tolerated by soft
             E-Priming (E-Choice). Reported with a note either way.
possible     an ambiguous X's token — "is", "has", or possessive. The
             script shows context; a human or model resolves it.
quoted       a hit inside double-quoted material. The standard carve-out
             preserves quotes verbatim, so quoted hits never fail a run
             unless --strict (purist mode) promotes them.

Masked regions — never reported at all
--------------------------------------
fenced code blocks, inline code, URLs, e-mail addresses, and YAML
frontmatter (a leading --- block). Banned forms written inside backticks
therefore stay invisible to the linter, which lets E-Prime teaching
materials quote `is` freely.

Hyphen rule
-----------
The tokenizer splits on hyphens, so "well-being" flags its "being". To keep
acronym prefixes like "IS-Architecture" quiet, any token immediately followed
by a hyphen gets skipped: only post-hyphen segments count.

Exit codes: 0 clean, 1 counted violations found, 2 usage error.
Counted by default: to_be, contraction, being_noun.
Promoted by --strict: possible, quoted.

Usage
-----
    python3 eprime_lint.py FILE [FILE ...] [--strict] [--json] [--quiet]
    python3 eprime_lint.py -            (reads stdin)
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------

CORE = {"be", "am", "is", "are", "was", "were", "been", "being"}

NEG_CONTRACTIONS = {
    "isn't", "aren't", "wasn't", "weren't", "ain't", "amn't", "an't",
}

# Archaic / dialect forms, matched after stripping leading apostrophes.
ARCHAIC = {"twas", "twere", "twast", "twasn't", "tweren't", "tis", "beest"}

# Forms only counted directly after "thou" (avoids flagging the noun "art").
THOU_ONLY = {"art", "wert", "wast"}

# Stems where X's unambiguously expands to "X is" (unless a participle
# follows, which suggests "has").
S_STEMS = {
    "he", "she", "it", "that", "there", "here", "who", "what", "where",
    "when", "how", "why", "which", "ye", "thou",
}

# "let's" == "let us" — never a to-be form.
LET_US_STEMS = {"let"}

# Past participles that suggest a preceding "'s" or pronoun contraction
# reads as "has" rather than "is".
PARTICIPLE_HINTS = {
    "gone", "done", "finished", "started", "begun", "arrived", "left",
    "seen", "taken", "written", "made", "built", "sent", "kept", "put",
    "run", "come", "become", "eaten", "lost", "won", "sold", "bought",
    "had", "got", "been", "told", "said", "found", "held", "shown", "given",
}

# Words that turn a following "being" into a noun compound.
BEING_NOUN_PREV = {"human", "well", "supreme", "mortal", "sentient",
                   "otherworldly", "time", "living"}

TOKEN_RE = re.compile(r"[A-Za-z]+(?:['\u2019][A-Za-z]+)*")
FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+|\S+@\S+\.\S+")
QUOTED_RE = re.compile(r'"[^"\n]{1,600}"|\u201c[^\u201d\n]{1,600}\u201d')

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def normalize(tok: str) -> str:
    """Lowercase, straighten curly apostrophes, drop leading apostrophes."""
    t = tok.lower().replace("\u2019", "'")
    return t.lstrip("'")


def line_col(text: str, index: int) -> tuple[int, int]:
    line_start = text.rfind("\n", 0, index) + 1
    line = text.count("\n", 0, index) + 1
    return line, index - line_start + 1


def context_window(text: str, start: int, end: int, radius: int = 70) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    snippet = text[lo:hi].replace("\n", " ")
    prefix = "\u2026 " if lo > 0 else ""
    suffix = " \u2026" if hi < len(text) else ""
    return (prefix + snippet + suffix).strip()


def classify_function(form: str, prev: str | None, nxt: str | None) -> str:
    """A coarse hint about which copula job this token performs.

    Full classification (identity vs. predication vs. locative vs.
    ownership) needs a reader's judgment; the script handles only the
    mechanically detectable cases and defaults to "copula".
    """
    if form == "there's":
        return "existential"
    if prev == "there" and form in {"is", "are", "was", "were"}:
        return "existential"
    if form == "be" and prev == "to":
        return "infinitive"
    if form == "be" and prev in {"will", "shall", "may", "might", "must",
                                 "cannot", "can't", "let", "so"}:
        return "subjunctive/imperative"
    if nxt:
        if nxt.endswith("ing") and nxt != "being":
            return "progressive"
        if nxt.endswith("ed") or nxt in PARTICIPLE_HINTS:
            return "passive"
        if nxt == "to":
            return "scheduled (is to)"
    return "copula (identity/predication/locative)"


# --------------------------------------------------------------------------
# Masking
# --------------------------------------------------------------------------


def masked_and_quoted_spans(text: str) -> tuple[list, list]:
    """Return (masked spans, quoted spans) as sorted (start, end) pairs."""
    masked: list[tuple[int, int]] = []
    quoted: list[tuple[int, int]] = []

    # YAML frontmatter: a leading --- ... --- block.
    if text.startswith("---\n"):
        close = re.search(r"\n---[ \t]*\n", text)
        if close:
            masked.append((0, close.end()))

    # Fenced code blocks (``` or ~~~), scanned line by line.
    fence_char: str | None = None
    line_start = 0
    for line in text.splitlines(keepends=True):
        m = FENCE_RE.match(line)
        if fence_char is None and m:
            fence_char = m.group(1)[0]
            masked.append((line_start, line_start + len(line)))
        elif fence_char is not None:
            masked.append((line_start, line_start + len(line)))
            if m and m.group(1)[0] == fence_char:
                fence_char = None
        line_start += len(line)

    # Inline code, URLs, e-mail addresses.
    for pattern in (INLINE_CODE_RE, URL_RE):
        for m in pattern.finditer(text):
            masked.append((m.start(), m.end()))

    # Double-quoted spans (straight and curly). Quoted hits get reported
    # but tagged "quoted" instead of masked outright.
    for m in QUOTED_RE.finditer(text):
        quoted.append((m.start(), m.end()))

    masked.sort()
    quoted.sort()
    return masked, quoted


def spans_contain(spans: list, start: int, end: int) -> bool:
    lo, hi = 0, len(spans) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s, e = spans[mid]
        if start < s:
            hi = mid - 1
        elif start >= e:
            lo = mid + 1
        else:
            return s <= start and end <= e
    return False


# --------------------------------------------------------------------------
# Core scan
# --------------------------------------------------------------------------


def scan_text(text: str) -> list[dict]:
    masked, quoted = masked_and_quoted_spans(text)

    # Candidate tokens: whole words. Tokens immediately followed by a
    # hyphen belong to hyphenated prefixes ("IS-Architecture") and get
    # skipped; post-hyphen segments ("being" in "well-being") still flag.
    clean: list[tuple[int, int, str]] = []
    for m in TOKEN_RE.finditer(text):
        s, e = m.start(), m.end()
        if e < len(text) and text[e] == "-":
            continue
        if spans_contain(masked, s, e):
            continue
        clean.append((s, e, m.group()))

    hits: list[dict] = []
    for idx, (s, e, raw) in enumerate(clean):
        tok = normalize(raw)
        prev = normalize(clean[idx - 1][2]) if idx > 0 else None
        nxt = normalize(clean[idx + 1][2]) if idx + 1 < len(clean) else None

        category: str | None = None
        note: str | None = None

        if tok in CORE:
            category = "to_be"
            if tok == "being":
                if prev in BEING_NOUN_PREV:
                    category = "being_noun"
                    note = ("noun/gerund use — banned in strict E-Prime, "
                            "tolerated by soft E-Priming")
                elif s > 0 and text[s - 1] == "-":
                    note = "post-hyphen compound (e.g. well-being)"
        elif tok in NEG_CONTRACTIONS:
            category = "contraction"
        elif tok in ARCHAIC:
            category = "contraction"
            note = "archaic/dialect form"
        elif tok in THOU_ONLY and prev == "thou":
            category = "contraction"
            note = "archaic form after 'thou'"
        elif "'" in tok:
            stem, _, suffix = tok.rpartition("'")
            if suffix in ("m", "re"):
                category = "contraction"
            elif suffix == "s":
                if stem in LET_US_STEMS:
                    continue  # let's == let us
                if stem in S_STEMS:
                    if nxt and (nxt in PARTICIPLE_HINTS or nxt.endswith("ed")):
                        category = "possible"
                        note = "likely 'has' + participle; verify by hand"
                    else:
                        category = "contraction"
                else:
                    category = "possible"
                    note = "'s reads as is / has / possessive — judge by context"

        if category is None:
            continue

        hint = classify_function(tok, prev, nxt)
        quoted_hit = spans_contain(quoted, s, e)
        line, col = line_col(text, s)
        hits.append({
            "line": line,
            "col": col,
            "token": raw,
            "category": category,
            "hint": hint,
            "note": note,
            "quoted": quoted_hit,
            "context": context_window(text, s, e),
        })

    return hits


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

COUNTED_DEFAULT = {"to_be", "contraction", "being_noun"}
COUNTED_STRICT = COUNTED_DEFAULT | {"possible", "quoted"}


def counted_failures(hits: list[dict], strict: bool) -> int:
    """Hits that fail the run: counted categories, minus quoted material
    unless --strict (purist mode) promotes it."""
    counted = COUNTED_STRICT if strict else COUNTED_DEFAULT
    n = 0
    for h in hits:
        if h["category"] not in counted:
            continue
        if h["quoted"] and not strict:
            continue
        n += 1
    return n


def human_report(path: str, hits: list[dict], strict: bool,
                 total_words: int, quiet: bool) -> int:
    fail = counted_failures(hits, strict)
    if quiet:
        print(f"{path}: {fail} counted violation(s), "
              f"{len(hits)} hit(s) total")
        return fail
    print(path)
    if not hits:
        print("  clean \u2713  no form of 'to be' found")
        print()
        return 0
    for h in hits:
        quoted = " [quoted]" if h["quoted"] else ""
        note = f"  ({h['note']})" if h["note"] else ""
        print(f"  L{h['line']:>4} C{h['col']:>3}  {h['category']:<12} "
              f"{h['token']:<12} ({h['hint']}){quoted}{note}")
        print(f"        {h['context']}")
    by_cat: dict[str, int] = {}
    for h in hits:
        by_cat[h["category"]] = by_cat.get(h["category"], 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(by_cat.items()))
    print(f"  summary: {summary} | {total_words} words scanned")
    print(f"  counted violations: {fail}"
          + ("  (--strict: quoted/possible promoted)" if strict else ""))
    print()
    return fail


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Detect every form of the verb 'to be' (E-Prime linter).")
    parser.add_argument("paths", nargs="*",
                        help="files to scan ('-' reads standard input)")
    parser.add_argument("--strict", action="store_true",
                        help="purist mode: count 'possible' and quoted hits too")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of human-readable output")
    parser.add_argument("--quiet", action="store_true",
                        help="human output without per-hit context lines")
    args = parser.parse_args(argv)

    if args.paths:
        texts: list[tuple[str, str]] = []
        for p in args.paths:
            if p == "-":
                texts.append(("<stdin>", sys.stdin.read()))
                continue
            try:
                with open(p, encoding="utf-8") as fh:
                    texts.append((p, fh.read()))
            except OSError as exc:
                print(f"error: cannot read {p}: {exc}", file=sys.stderr)
                return 2
    else:
        texts = [("<stdin>", sys.stdin.read())]

    all_files = []
    total_fail = 0
    for path, text in texts:
        hits = scan_text(text)
        words = len(re.findall(r"[A-Za-z]+", text))
        fail = counted_failures(hits, args.strict)
        total_fail += fail
        if args.json:
            all_files.append({"path": path, "words": words, "hits": hits,
                              "counted_violations": fail})
        else:
            human_report(path, hits, args.strict, words, args.quiet)

    if args.json:
        print(json.dumps({
            "files": all_files,
            "total_counted_violations": total_fail,
        }, indent=2))
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
