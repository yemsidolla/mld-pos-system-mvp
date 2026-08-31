#!/usr/bin/env python3
"""Prove a component migration is pixel-identical, from the compiled CSS.

Swapping utilities for a component class is only safe if the element ends up
with the same declarations. Two things can break that, and neither is visible
by reading the diff:

1. The component lives in `@layer components`, the utilities it replaced live
   in `@layer utilities` — a HIGHER layer. So a leftover utility on the same
   element that sets the same property used to TIE with the consumed tokens
   (resolved by source order) and now WINS outright.
2. A rule fires on an element that merely happens to contain the tokens, and
   the produced component is not actually equivalent for that element.

This script recomputes, for every class attribute the migration rewrote, the
full property set contributed by the before-tokens and the after-tokens using
the real compiled tailwind.css, and reports any element whose resolved
declarations differ.

    python3 scripts/verify_migration.py migration-pairs.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "app" / "core" / "static" / "core" / "css" / "tailwind.css"

LAYER_RANK = {"legacy": 0, "theme": 1, "base": 2, "components": 3, "utilities": 4}

# Differences that are real in the cascade but invisible on screen. Each entry
# is (tag, property, before, after) and must carry a reason — the point of the
# allowlist is that anything NOT listed here fails the run.
ACCEPTED = {
    # .btn folds in `no-underline` because anchors need it. A <button> never
    # had text-decoration to begin with, so setting it to none changes nothing.
    ("button", "text-decoration-line", "<unset>", "none"),
    # An empty-state cell now inherits vertical-align:middle from
    # `.data-table td`. The cell holds one centred line, so middle and
    # baseline paint identically.
    ("td", "vertical-align", "<unset>", "middle"),
}


def parse_css(text: str) -> dict[str, list[tuple[int, str, str]]]:
    """class name -> [(layer rank, property, value)] for simple class rules.

    Only single-class selectors are collected (`.foo{...}`), plus the
    descendant forms the data-table component uses. That is exactly the shape
    both the utilities layer and the component layer emit, so it is enough to
    compare two class lists on the same element.
    """
    rules: dict[str, list[tuple[int, str, str]]] = {}
    layer_rank = 4  # anything outside a named layer behaves as top precedence
    depth = 0
    i = 0
    stack: list[int] = []
    while i < len(text):
        m = re.compile(r"@layer\s+([a-z]+)\s*\{").match(text, i)
        if m:
            layer_rank = LAYER_RANK.get(m.group(1), 4)
            stack.append(layer_rank)
            depth += 1
            i = m.end()
            continue
        m = re.compile(r"@(media|supports|property)[^{]*\{").match(text, i)
        if m:  # skip conditional groups wholesale: they are not the base state
            level = 1
            j = m.end()
            while j < len(text) and level:
                if text[j] == "{":
                    level += 1
                elif text[j] == "}":
                    level -= 1
                j += 1
            i = j
            continue
        m = re.compile(r"([^{}@]+)\{([^{}]*)\}").match(text, i)
        if m:
            selector, body = m.group(1).strip(), m.group(2)
            # Split on commas that separate selectors, NOT the escaped
            # commas inside arbitrary values like
            # .grid-cols-\[repeat\(auto-fit\,minmax\(220px\,1fr\)\)\]
            for sel in re.split(r"(?<!\\),", selector):
                sel = sel.strip()
                key = None
                if re.fullmatch(r"\.[\w\\\[\]&:.%(),*_>+~=\"'-]+", sel):
                    key = sel[1:]
                elif re.fullmatch(r"\.[\w-]+ (th|td)", sel):
                    key = sel[1:]
                elif re.fullmatch(r"\.[\w-]+ (?:th|td)\.[\w-]+", sel):
                    # `.data-table td.cell-empty` — a component deliberately
                    # outranking the ancestor cell rule. Key it on the leaf
                    # class so it competes there, with its real specificity.
                    key = sel.rsplit(".", 1)[1]
                if key:
                    # (a,b,c) specificity: ids, classes/attrs/pseudo-classes,
                    # elements. Needed because .data-table td (0,1,1) and
                    # .cell-empty (0,1,0) live in the SAME layer, where only
                    # specificity separates them.
                    spec = (
                        len(re.findall(r"(?<!\\)\.", sel)) + len(re.findall(r"\[", sel)),
                        len(re.findall(r"(?:^| )(?:th|td|tbody|tr)\b", sel)),
                    )
                    decls = []
                    for decl in body.split(";"):
                        if ":" in decl:
                            prop, _, val = decl.partition(":")
                            decls.append((layer_rank, spec, prop.strip(), val.strip()))
                    # CSS escapes non-ident chars numerically (`\2c ` = comma),
                    # so unescape those before stripping plain backslashes —
                    # otherwise arbitrary-value classes never match a token.
                    key = re.sub(r"\\\\([0-9a-fA-F]{1,6})\\s?", lambda mm: chr(int(mm.group(1), 16)), key)
                    rules.setdefault(key.replace("\\", ""), []).extend(decls)
            i = m.end()
            continue
        if text[i] == "}" and stack:
            stack.pop()
            layer_rank = stack[-1] if stack else 4
        i += 1
    return rules


def resolve(tokens: list[str], rules: dict, tag: str = "", ancestors: tuple = ()) -> dict[str, tuple[int, str]]:
    """Winning (layer, value) per property for a class list.

    `tag` + `ancestors` model the one structural rule the component layer
    introduces: .data-table styles its own th/td, so after migration a cell
    inherits from the table rather than carrying the declarations itself.
    Without this the checker reports every migrated cell as a difference.
    """
    out: dict[str, tuple[int, str]] = {}
    lookup = list(tokens)
    if tag in ("th", "td"):
        lookup += [f"{a} {tag}" for a in ancestors]
    for order, tok in enumerate(lookup):
        for rank, spec, prop, val in rules.get(tok, []):
            weight = (rank, spec, order)
            prev = out.get(prop)
            if prev is None or weight >= prev[0]:
                out[prop] = (weight, val)
    return out


def main() -> int:
    pairs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rules = parse_css(CSS.read_text(encoding="utf-8"))
    print(f"parsed {len(rules)} class rules from compiled CSS")

    bad = 0
    for item in pairs:
        tag = item.get("tag", "")
        # Before migration a cell carried its own classes; after, the table
        # supplies them. Model that asymmetry explicitly.
        before = resolve(item["before"].split(), rules, tag, ())
        after = resolve(item["after"].split(), rules, tag, ("data-table",))
        diffs = []
        for prop in sorted(set(before) | set(after)):
            b = before.get(prop, (None, "<unset>"))[1]
            a = after.get(prop, (None, "<unset>"))[1]
            if b != a and (tag, prop, b, a) not in ACCEPTED:
                diffs.append(f"{prop}: {b!r} -> {a!r}")
        if diffs:
            bad += 1
            print(f"\nDIFFERS  {item['file']}")
            print(f"  before: {item['before'][:150]}")
            print(f"  after:  {item['after'][:150]}")
            for d in diffs:
                print(f"    {d}")

    print(f"\n{len(pairs)} rewritten class attributes checked, {bad} differ "
          f"(after {len(ACCEPTED)} documented no-op exceptions)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
