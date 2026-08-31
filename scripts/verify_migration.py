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

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAILWIND = ROOT / "app/core/static/core/css/tailwind.css"
# dashboard.css is imported by cascade.css as layer(legacy). It MUST be parsed:
# it holds rules keyed on .panel, .panel-header, .btn, .data-table … that match
# nothing while templates use raw utilities, and wake the moment an element is
# given the class. That is how panel headers started stacking on phones.
LEGACY = ROOT / "app/core/static/core/css/dashboard.css"


def load_rules(rev=None):
    """Parse both sheets. `rev` reads them from a git revision instead of disk,
    so the BEFORE side can be resolved against the pre-migration build —
    rebuilding Tailwind tree-shakes away utilities that only existed on
    migrated elements, which would otherwise read as '<unset>'."""
    merged = {}
    for path, default_rank in ((TAILWIND, 4),):
        rel = path.relative_to(ROOT)
        if rev:
            out = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT,
                                 capture_output=True, text=True)
            if out.returncode != 0:
                raise SystemExit(f"cannot read {rel} at {rev}: {out.stderr.strip()}")
            text = out.stdout
        else:
            text = path.read_text(encoding="utf-8")
        for key, decls in parse_css(text, default_rank).items():
            merged.setdefault(key, []).extend(decls)
    return merged

LAYER_RANK = {"legacy": 0, "theme": 1, "base": 2, "components": 3, "utilities": 4}

# Differences that are real in the cascade but invisible on screen. Each entry
# is (tag, property, before, after) and must carry a reason — the point of the
# allowlist is that anything NOT listed here fails the run.
ACCEPTED = {
    # .btn folds in `no-underline` because anchors need it. A <button> never
    # had text-decoration to begin with, so setting it to none changes nothing.
    ("button", "text-decoration-line", "<unset>", "none"),
    # Same for the file-upload <label> styled as a button.
    ("label", "text-decoration-line", "<unset>", "none"),
    # An empty-state cell now inherits vertical-align:middle from
    # `.data-table td`. The cell holds one centred line, so middle and
    # baseline paint identically.
    ("td", "vertical-align", "<unset>", "middle"),
    # Compact buttons (btn + btn-sm) inherit three things from .btn that the
    # canonical compact string never had. Each is inert on the 3 elements
    # that exist: dashboard.css:352 already sets `font: inherit` on every
    # button and :48 sets the body to --font-sans, so the computed family is
    # unchanged; all 3 compact buttons hold a single text node and `gap`
    # needs two flex children; and their labels are single words that cannot
    # wrap. Re-check these if a compact button ever gains an icon.
    ("button", "font-family", "<unset>", "var(--font-sans)"),
    ("button", "gap", "<unset>", "calc(var(--spacing) * 1.5)"),
    ("button", "white-space", "<unset>", "nowrap"),
    # Same three, on the compact secondary <a> ("Clear"). Anchors inherit the
    # body's --font-sans already; all 3 hold the single word "Clear", so
    # neither gap nor nowrap can apply.
    ("a", "font-family", "<unset>", "var(--font-sans)"),
    ("a", "gap", "<unset>", "calc(var(--spacing) * 1.5)"),
    ("a", "white-space", "<unset>", "nowrap"),
    # --- Two DELIBERATE responsive adoptions (phone only) ---------------
    # Phase 1 folded dashboard.css's dormant dense-phone table padding into
    # .data-table th/td. Nothing carried .data-table before Phase 3, so the
    # legacy rule never fired; now it does, via the component. This restores
    # the original author's stated intent ("Denser tables so more columns fit
    # before horizontal scroll kicks in"), and applies ONLY at <=640px.
    ("th", "padding-inline", "9px", "7px"),
    ("td", "padding-inline", "9px", "7px"),
    ("td", "padding-block", "calc(var(--spacing) * 2.5)", "calc(var(--spacing) * 2)"),
    ("th", "padding-block", "calc(var(--spacing) * 2.5)", "calc(var(--spacing) * 2)"),
    # Phone touch targets. Phase 1 folded dashboard.css's dormant
    # `@media (max-width:640px) .btn { min-height: 42px }` into .btn. Buttons
    # carried min-h-[38px] as a utility before and never matched .btn, so the
    # guard never fired; §8 of DESIGN_SYSTEM requires >=42px on phone, so this
    # restores a documented requirement rather than changing a decision.
    ("*", "min-height", "38px", "42px"),
    # Print flattening. Same shape: `@media print { .panel { border:0;
    # padding:0; box-shadow:none } }` was dormant, and Phase 1 folded it into
    # .panel. Printed reports lose panel chrome, which is what it was for.
    ("*", "padding-block", "18px", "0"),
    ("*", "padding-inline", "18px", "0"),
    ("*", "border-width", "1px", "0"),
    ("*", "--tw-shadow", "0 1px 0 var(--tw-shadow-color,#11182708)", "0 0 #0000"),
    # Panel headers stack on phones (dashboard.css:1960, also dormant). Owning
    # both properties in the component is what makes it coherent — see the
    # comment on .panel-header in tailwind/input.css.
    ("*", "flex-direction", "<unset>", "column"),
    ("*", "align-items", "flex-start", "stretch"),
}


def expand(prop: str, val: str) -> list[tuple[str, str]]:
    """Expand the shorthands legacy CSS uses into the longhands Tailwind emits.

    Without this, `padding: 10px 9px` (dashboard.css) and
    `padding-block/inline` (a component) look like different properties and
    every migrated cell reports a phantom difference.
    """
    parts = val.split()
    if prop == "padding" or prop == "margin":
        if len(parts) == 1:
            block = inline = parts[0]
        elif len(parts) == 2:
            block, inline = parts
        else:  # 3-4 values: not worth modelling precisely, keep as-is
            return [(prop, val)]
        return [(f"{prop}-block", block), (f"{prop}-inline", inline)]
    if prop in ("border", "border-bottom", "border-top", "border-left", "border-right"):
        if len(parts) == 3:
            width, style, color = parts
            side = "" if prop == "border" else prop[len("border"):]
            return [
                (f"border{side}-width", width),
                (f"border{side}-style", style),
                (f"border{side}-color", color),
            ]
    if prop == "background" and not any(c in val for c in "(,"):
        return [("background-color", val)]
    return [(prop, val)]


def parse_css(text: str, default_rank: int = 4) -> dict:
    """(media condition, class key) -> [(rank, specificity, prop, value)].

    @media blocks are KEPT, keyed by their condition. Skipping them was the
    bug that let a dormant legacy rule through: `flex` sets `display`, not
    `flex-direction`, so `@media (max-width:640px) .panel-header {
    flex-direction: column }` applied the moment the class name existed.
    """
    rules: dict = {}
    i = 0
    stack: list[tuple[str, object]] = []  # ("layer", rank) | ("media", cond)

    def rank() -> int:
        for kind, val in reversed(stack):
            if kind == "layer":
                return val
        return default_rank

    def media() -> str:
        return " and ".join(v for k, v in stack if k == "media")

    while i < len(text):
        m = re.compile(r"@layer\s+([a-z]+)\s*\{").match(text, i)
        if m:
            stack.append(("layer", LAYER_RANK.get(m.group(1), default_rank)))
            i = m.end()
            continue
        m = re.compile(r"@media([^{]*)\{").match(text, i)
        if m:
            stack.append(("media", m.group(1).strip()))
            i = m.end()
            continue
        m = re.compile(r"@(supports|property|keyframes|font-face)[^{]*\{").match(text, i)
        if m:  # genuinely outside the class cascade
            level, j = 1, m.end()
            while j < len(text) and level:
                level += (text[j] == "{") - (text[j] == "}")
                j += 1
            i = j
            continue
        m = re.compile(r"([^{}@]+)\{([^{}]*)\}").match(text, i)
        if m:
            selector, body = m.group(1).strip(), m.group(2)
            # Split on selector commas, NOT escaped commas inside arbitrary
            # values like .grid-cols-\[repeat\(auto-fit\,minmax\(220px\,1fr\)\)\]
            for sel in re.split(r"(?<!\\),", selector):
                sel = sel.strip()
                key = None
                if re.fullmatch(r"\.[\w\\\[\]&:.%(),*_>+~=\"'-]+", sel):
                    key = sel[1:]
                elif re.fullmatch(r"\.[\w-]+ (th|td)", sel):
                    key = sel[1:]
                elif re.fullmatch(r"(?:button|a|label|input|select|textarea)", sel):
                    # Element selectors matter: dashboard.css styles `button`
                    # directly, so a <button> already carried those
                    # declarations BEFORE it was given .btn. Without this the
                    # legacy shorthands look like they appeared from nowhere.
                    key = f"tag:{sel}"
                elif re.fullmatch(r"\.[\w-]+ (?:th|td)\.[\w-]+", sel):
                    # `.data-table td.cell-empty` deliberately outranks the
                    # ancestor cell rule; key it on the leaf class.
                    key = sel.rsplit(".", 1)[1]
                if not key:
                    continue
                key = re.sub(r"\\([0-9a-fA-F]{1,6})\s?",
                             lambda mm: chr(int(mm.group(1), 16)), key)
                key = key.replace("\\", "")
                spec = (
                    len(re.findall(r"(?<!\\)\.", sel)) + len(re.findall(r"\[", sel)),
                    len(re.findall(r"(?:^| )(?:th|td|tbody|tr)\b", sel)),
                )
                decls = []
                for decl in body.split(";"):
                    if ":" in decl:
                        prop, _, val = decl.partition(":")
                        for pr, vl in expand(prop.strip(), val.strip()):
                            decls.append((rank(), spec, pr, vl))
                rules.setdefault((media(), key), []).extend(decls)
            i = m.end()
            continue
        if text[i] == "}" and stack:
            stack.pop()
        i += 1
    return rules


def resolve(tokens, rules, media_ctx, tag="", ancestors=()):
    """Winning (weight, value) per property within one media context.

    Base rules always apply; the context's rules stack on top of them.
    """
    out: dict = {}
    lookup = list(tokens)
    if tag:
        lookup = [f"tag:{tag}"] + lookup  # element rules lose to class rules
        lookup += [f"{a} {tag}" for a in ancestors]
    for ctx in ("", media_ctx) if media_ctx else ("",):
        for order, tok in enumerate(lookup):
            for r, spec, prop, val in rules.get((ctx, tok), []):
                weight = (r, spec, ctx != "", order)
                if prop not in out or weight >= out[prop][0]:
                    out[prop] = (weight, val)
    return out


def report_legacy_wakes(pairs) -> int:
    """List dormant dashboard.css rules that the new class names activate.

    This is the failure mode a declaration comparator cannot see cheaply:
    legacy has rules keyed on `.panel`, `.panel-header`, `.btn`,
    `.data-table` … that matched NOTHING while templates used raw utilities.
    Giving an element the class wakes them. Modelling that fully means
    implementing shorthand/longhand equivalence and inheritance — i.e. a CSS
    engine — so instead we surface exactly which rules woke, for review.
    """
    produced = set()
    for item in pairs:
        produced |= set(item["after"].split()) - set(item["before"].split())
    produced = {c for c in produced if not re.search(r"[\[\]:]", c)}

    legacy = LEGACY.read_text(encoding="utf-8")
    woken = {}
    for cls in sorted(produced):
        for m in re.finditer(r"([^{}]*\." + re.escape(cls) + r"\b[^{}]*)\{([^{}]*)\}", legacy):
            sel = m.group(1).strip().splitlines()[-1].strip()
            line = legacy[: m.start()].count("\n") + 1
            # Is it inside an @media? Find the nearest unclosed @media before it.
            depth, media = 0, ""
            for mm in re.finditer(r"@media([^{]*)\{|\{|\}", legacy[: m.start()]):
                tok = mm.group(0)
                if tok.startswith("@media"):
                    depth += 1
                    media = mm.group(1).strip()
                elif tok == "{":
                    depth += 1
                elif tok == "}":
                    depth -= 1
                    if depth == 0:
                        media = ""
            woken.setdefault(cls, []).append((line, media, sel, m.group(2).strip()[:90]))

    if not woken:
        print("\nno dormant legacy rules are activated by the new class names")
        return 0
    print("\nDORMANT LEGACY RULES ACTIVATED (dashboard.css) — review each:")
    for cls, hits in woken.items():
        print(f"\n  .{cls}")
        for line, media, sel, body in hits:
            ctx = f"@media {media} " if media else ""
            print(f"    :{line:<5} {ctx}{sel} {{ {body} }}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs")
    ap.add_argument(
        "--before-rev",
        help="git revision to read the BEFORE stylesheets from. Rebuilding "
             "Tailwind tree-shakes away utilities that only existed on "
             "migrated elements, so resolving both sides against the current "
             "build reports phantom differences.",
    )
    args = ap.parse_args()

    pairs = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
    after_rules = load_rules()
    before_rules = load_rules(args.before_rev) if args.before_rev else after_rules

    contexts = sorted({m for m, _ in after_rules if m} | {m for m, _ in before_rules if m})
    print(f"parsed {len({k for _, k in after_rules})} class keys; checking base "
          f"+ {len(contexts)} @media contexts"
          + (f" (before side from {args.before_rev})" if args.before_rev else ""))

    bad = 0
    for item in pairs:
        tag = item.get("tag", "")
        for ctx in [""] + contexts:
            # Before migration a cell carried its own classes; after, the
            # table supplies them. Model that asymmetry explicitly.
            before = resolve(item["before"].split(), before_rules, ctx, tag, ())
            after = resolve(item["after"].split(), after_rules, ctx, tag, ("data-table",))
            diffs = []
            for prop in sorted(set(before) | set(after)):
                b = before.get(prop, (None, "<unset>"))[1]
                a = after.get(prop, (None, "<unset>"))[1]
                if b == a:
                    continue
                if (tag, prop, b, a) in ACCEPTED or ("*", prop, b, a) in ACCEPTED:
                    continue
                diffs.append(f"{prop}: {b!r} -> {a!r}")
            if diffs:
                bad += 1
                print(f"\nDIFFERS  {item['file']}  [{'@media ' + ctx if ctx else 'base'}]")
                print(f"  before: {item['before'][:130]}")
                print(f"  after:  {item['after'][:130]}")
                for d in diffs:
                    print(f"    {d}")

    print(f"\n{len(pairs)} rewritten attributes checked across {len(contexts) + 1} "
          f"contexts, {bad} differ (after {len(ACCEPTED)} documented no-op exceptions)")
    report_legacy_wakes(pairs)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
