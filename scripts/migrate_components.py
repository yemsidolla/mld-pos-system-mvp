#!/usr/bin/env python3
"""Phase 3: swap repeated utility strings for the V8 component classes.

Deterministic and reversible on purpose. The transform is a table of EXACT
class-token sets, never a regex over markup: every rule states the tokens it
consumes and the tokens it leaves behind, and a rule only fires when the
element's class list contains the whole set. Anything unrecognised is left
alone and reported, so the script can never half-convert an element.

The invariant: for each rule, `component-classes + leftovers` must render
identically to the original string, because the component was defined by
@apply-ing exactly the tokens it consumes (DESIGN_SYSTEM §2.0/§4).

    python3 scripts/migrate_components.py --batch shared --dry-run
    python3 scripts/migrate_components.py --batch shared

Batches are ordered by blast radius so each is separately revertable.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "app" / "templates"

# Templates whose classes must NOT be touched by this script.
#   styleguide.html  — its utilities-only sections deliberately prove the
#                      theme mapping; its V8 section is already components.
#   receipt.html     — standalone print page with its own <style>; it does not
#                      load the shared stylesheet at all.
#   pos_sale.html    — the till. Out of scope until its own task (V8 plan).
SKIP = {"styleguide.html", "receipt.html", "pos_sale.html"}

BATCHES = {
    "shared": ["dashboard"],
    "admin": ["accounts", "core", "audit", "system_logs"],
    "catalog": ["catalog", "labels", "batch_upload"],
    "sales": ["inventory", "reports", "pos"],
}

# --- the transform table -------------------------------------------------
# (consumed tokens, produced tokens). Order matters: longest/most specific
# first, since a fired rule removes its tokens from the pool.
BTN = "inline-flex min-h-[38px] cursor-pointer items-center justify-center gap-1.5 whitespace-nowrap rounded-md border"
TAIL = "px-[13px] py-[9px] font-sans text-sm font-[750]"

RULES: list[tuple[str, str]] = [
    # Buttons. `no-underline hover:no-underline` only appears on anchors; both
    # are folded into .btn, so they are consumed wherever present.
    (f"{BTN} border-primary bg-primary {TAIL} text-white no-underline hover:bg-primary-hover hover:no-underline", "btn btn-primary"),
    (f"{BTN} border-primary bg-primary {TAIL} text-white hover:bg-primary-hover hover:no-underline", "btn btn-primary"),
    (f"{BTN} border-success bg-success {TAIL} text-white no-underline hover:brightness-95 hover:no-underline", "btn btn-success"),
    (f"{BTN} border-success bg-success {TAIL} text-white hover:brightness-95 hover:no-underline", "btn btn-success"),
    (f"{BTN} border-danger bg-danger {TAIL} text-white no-underline hover:brightness-95 hover:no-underline", "btn btn-danger"),
    (f"{BTN} border-danger bg-danger {TAIL} text-white hover:brightness-95 hover:no-underline", "btn btn-danger"),
    (f"{BTN} border-border-strong bg-surface {TAIL} text-text no-underline hover:bg-surface-subtle hover:no-underline", "btn"),
    (f"{BTN} border-border-strong bg-surface {TAIL} text-text hover:bg-surface-subtle hover:no-underline", "btn"),
    # File-upload <label> styled as a button: same skeleton but tinted, so
    # `.btn` plus the tint utility (utilities beat components) is identical.
    (f"{BTN} border-border-strong bg-surface-subtle {TAIL} text-text hover:bg-surface-subtle hover:no-underline", "btn bg-surface-subtle"),
    # Compact buttons (column filters, dense toolbars).
    ("inline-flex min-h-8 flex-1 cursor-pointer items-center justify-center rounded-md border border-primary bg-primary px-2.5 py-1.5 text-xs font-[750] text-white hover:bg-primary-hover hover:no-underline", "btn btn-sm btn-primary flex-1"),
    ("inline-flex min-h-8 flex-1 cursor-pointer items-center justify-center rounded-md border border-border-strong bg-surface px-2.5 py-1.5 text-xs font-[750] text-text no-underline hover:bg-surface-subtle hover:no-underline", "btn btn-sm flex-1"),
    # Panels and their header trio.
    ("rounded border border-border bg-surface p-[18px] shadow-panel", "panel"),
    ("mb-3.5 flex items-start justify-between gap-3.5", "panel-header"),
    ("m-0 mb-1 text-base font-semibold text-text", "panel-title"),
    # Tables. th/td styling now comes from the .data-table ancestor, so the
    # per-cell strings are consumed entirely.
    ("overflow-x-auto [-webkit-overflow-scrolling:touch]", "table-wrap"),
    ("w-full min-w-[720px] border-collapse", "data-table"),
    ("border-b border-border px-[9px] py-2 text-left text-[11px] font-semibold uppercase tracking-[0.07em] text-text-soft", ""),
    # Centre-aligned header variant: identical apart from the alignment,
    # which stays an inline utility (utilities beat the component).
    ("border-b border-border px-[9px] py-2 text-center text-[11px] font-semibold uppercase tracking-[0.07em] text-text-soft", "text-center"),
    ("border-b border-border px-[9px] py-2.5 align-middle", ""),
    ("border-b border-border px-[9px] py-6 text-center text-text-soft", "cell-empty"),
    ("font-mono text-[0.95em] tracking-[-0.01em]", "cell-num"),
    # Forms.
    ("grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-3.5 [&_ul]:mt-1 [&_ul]:mb-0 [&_ul]:flex [&_ul]:list-none [&_ul]:flex-wrap [&_ul]:gap-x-4 [&_ul]:gap-y-1.5 [&_ul]:p-0 [&_ul_li_label]:inline-flex [&_ul_li_label]:items-center [&_ul_li_label]:gap-[7px] [&_ul_li_label]:text-[13px] [&_ul_li_label]:font-medium [&_ul_li_label]:text-text", "field-grid"),
    ("mb-2 mt-3.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-text-soft", "section-label"),
    # Toolbars.
    ("flex flex-wrap items-center gap-2 [&_input]:min-w-0 [&_input]:flex-[1_1_220px] [&_select]:flex-[1_1_220px]", "toolbar toolbar-input"),
    ("flex flex-wrap items-center gap-2", "toolbar"),
    # Alerts.
    ("rounded-r-md border border-alert-danger-border border-l-[3px] border-l-danger bg-alert-danger-bg px-3 py-2.5 text-danger", "alert alert-danger"),
    ("rounded-r-md border border-alert-warning-border border-l-[3px] border-l-warning bg-alert-warning-bg px-3 py-2.5 text-warning", "alert alert-warning"),
    # Stat cards.
    ("mb-4 grid grid-cols-[repeat(auto-fit,minmax(170px,1fr))] gap-3", "stat-grid mb-4"),
    ("rounded-md border border-border bg-surface p-4", "stat-card"),
    ("mt-1.5 block text-[28px]", "stat-value"),
    ("mt-1.5 block text-lg", "stat-value stat-value-sm"),
    ("block text-text-soft", "stat-label"),
    # Panel help text / subtitle — 89 sites, the largest single miss in the
    # first pass. MUST come after panel-title, whose consumed set also
    # contains `m-0`; apply_rules removes tokens as rules fire.
    ("m-0 text-text-soft", "panel-sub"),
    # Status pills.
    ("inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold tracking-[0.02em] bg-pill-neutral text-pill-neutral-fg", "pill pill-neutral"),
    ("inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold tracking-[0.02em] bg-pill-success text-pill-success-fg", "pill pill-success"),
    ("inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold tracking-[0.02em] bg-pill-warning text-pill-warning-fg", "pill pill-warning"),
    ("inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold tracking-[0.02em] bg-pill-danger text-pill-danger-fg", "pill pill-danger"),
    ("inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold tracking-[0.02em] bg-pill-info text-pill-info-fg", "pill pill-info"),
    # Dashboard KPI tiles.
    ("grid gap-1 rounded border border-border bg-surface px-4 py-3.5", "kpi-tile"),
    ("font-mono text-[26px] font-semibold leading-[1.1] text-text", "kpi-value"),
    # Neutral alert.
    ("rounded-r-md border border-border border-l-[3px] border-l-border bg-surface px-3 py-2.5", "alert alert-neutral"),
    # Modal close button (standalone, not a .btn variant).
    ("inline-flex size-9 min-h-0 cursor-pointer items-center justify-center border border-border-strong bg-surface p-0 text-[22px] font-[750] text-text hover:bg-surface-subtle", "btn-icon"),
    # Quiet link.
    ("text-[12.5px] font-semibold text-text-soft no-underline hover:text-accent hover:no-underline", "link-subtle"),
]

# `grid gap-3.5` is form-stack, but only on a <form> — the same tokens are
# generic layout elsewhere, so it is handled separately with that guard.
FORM_STACK = ("grid gap-3.5", "form-stack")


def apply_rules(class_value: str, on_form: bool) -> tuple[str, list[str]]:
    """Return (new class string, names of rules that fired)."""
    tokens = class_value.split()
    fired: list[str] = []
    for consumed, produced in RULES:
        need = consumed.split()
        if all(t in tokens for t in need):
            for t in need:
                tokens.remove(t)
            tokens = produced.split() + tokens
            fired.append(produced or "(cell)")
    if on_form:
        need = FORM_STACK[0].split()
        if all(t in tokens for t in need):
            for t in need:
                tokens.remove(t)
            tokens = FORM_STACK[1].split() + tokens
            fired.append(FORM_STACK[1])
    # Stable, readable order: components first (already prepended), then the
    # leftover utilities in their original relative order.
    return " ".join(tokens), fired


PAIRS: list[dict] = []


def migrate(path: Path, dry_run: bool, rel_to: Path | None = None) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8")
    changes = 0
    fired_all: list[str] = []

    # Walk class="..." occurrences and look backwards for the owning tag, so
    # the regex never has to model whole attribute lists (which is where
    # markup-rewriting regexes usually go wrong).
    out: list[str] = []
    pos = 0
    for m in re.finditer(r'class="([^"]*)"', text):
        before = m.group(1)
        # A value containing Django tags is conditional markup: swapping
        # tokens inside it can silently change which branch emits which
        # classes, so leave it for a human.
        if "{%" in before or "{{" in before:
            continue
        tag_start = text.rfind("<", 0, m.start())
        tag_match = re.match(r"<([a-zA-Z][\w-]*)", text[tag_start:]) if tag_start != -1 else None
        on_form = bool(tag_match and tag_match.group(1).lower() == "form")
        after, fired = apply_rules(before, on_form)
        if after == before:
            continue
        out.append(text[pos : m.start()])
        out.append(f'class="{after}"')
        pos = m.end()
        changes += 1
        fired_all.extend(fired)
        PAIRS.append({
            "file": str(path.relative_to(rel_to or TEMPLATES)),
            "tag": tag_match.group(1).lower() if tag_match else "",
            "before": before,
            "after": after,
        })
    out.append(text[pos:])
    new_text = "".join(out)

    if changes and not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return changes, fired_all


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, choices=sorted(BATCHES) + ["all"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--from-rev",
        help="read templates from this git revision instead of the working "
             "tree and only emit before/after pairs. Makes the migration's "
             "equivalence proof reproducible after the migration has landed.",
    )
    args = ap.parse_args()

    dirs = sorted({d for b in (BATCHES if args.batch == "all" else [args.batch]) for d in BATCHES[b]})
    total_files = total_changes = 0

    if args.from_rev:
        # Replay the transform over the pre-migration templates, in a temp
        # tree, purely to regenerate the pairs. Nothing in the repo is touched.
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", args.from_rev, "app/templates"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        with tempfile.TemporaryDirectory() as tmp:
            for rel in listing:
                if not rel.endswith(".html"):
                    continue
                name = Path(rel).name
                batch_dir = Path(rel).parts[2] if len(Path(rel).parts) > 2 else ""
                if name in SKIP or batch_dir not in dirs:
                    continue
                blob = subprocess.run(["git", "show", f"{args.from_rev}:{rel}"],
                                      cwd=ROOT, capture_output=True, text=True, check=True).stdout
                dest = Path(tmp) / Path(rel).relative_to("app/templates")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(blob, encoding="utf-8")
            for path in sorted(Path(tmp).rglob("*.html")):
                changed, _ = migrate(path, dry_run=True, rel_to=Path(tmp))
                if changed:
                    total_files += 1
                    total_changes += changed
        print(f"\nreplayed {total_changes} rewrites across {total_files} templates "
              f"from {args.from_rev}")
        out = ROOT / "migration-pairs.json"
        out.write_text(json.dumps(PAIRS, indent=1), encoding="utf-8")
        print(f"wrote {len(PAIRS)} before/after pairs to {out.name}")
        return 0

    for d in dirs:
        for path in sorted((TEMPLATES / d).rglob("*.html")):
            if path.name in SKIP:
                print(f"  skip  {path.relative_to(TEMPLATES)} (excluded)")
                continue
            changed, fired = migrate(path, args.dry_run)
            if changed:
                total_files += 1
                total_changes += changed
                print(f"  {changed:3d}  {path.relative_to(TEMPLATES)}")
    verb = "would change" if args.dry_run else "changed"
    print(f"\n{verb} {total_changes} class attributes across {total_files} templates")
    # Emit before/after pairs so scripts/verify_migration.py can prove, from
    # the compiled CSS, that every rewrite resolves to the same declarations.
    out = ROOT / "migration-pairs.json"
    out.write_text(json.dumps(PAIRS, indent=1), encoding="utf-8")
    print(f"wrote {len(PAIRS)} before/after pairs to {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
