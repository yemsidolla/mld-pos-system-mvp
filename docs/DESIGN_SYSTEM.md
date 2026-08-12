# Melodu Design System

**Status:** authoritative. This document is the single source of truth for how
the Melodu dashboard looks and behaves. The live counterpart is the styleguide
page at `/dashboard/styleguide/` (owner/manager only) — it renders every token
and component below from the real CSS, so if the styleguide and a screen
disagree, the screen is wrong.

---

## 0. How to use this document

### For everyone (human and AI)

1. **Before building or changing any screen, read the relevant section here.**
   Reuse an existing token, component, and page archetype. Do not invent a new
   one when one already fits.
2. **The styleguide page is the proof.** New or changed components must appear
   there. "Make it match the styleguide" is a valid, complete instruction.
3. **Everything ships against the Definition of Done (§9).** A screen is not
   finished until it passes that checklist.

### Change policy (important)

> **This document changes only through a dedicated task** whose explicit purpose
> is to optimize or change the design system — never as a side effect of feature
> work. If feature work needs a rule that doesn't exist yet, stop, raise a
> design-system task, change the doc + styleguide + tokens together, then resume.

This keeps the contract stable: a developer or AI reading this file can trust it
matches the code, because the only way it drifts is a deliberate, reviewed task.
When you do change it, update three things in the same commit: this doc, the
styleguide page, and the CSS — and add a line to §11.

### The layered model

```
Screens & flows   ← what users touch   (POS, inventory, reports)
Patterns          ← page archetypes    (list, form, detail, workflow)
Components         ← reusable pieces    (buttons, pills, cards, tables)
Tokens             ← raw design values  (color, spacing, type, radius)
Principles         ← the why            (speed, clarity, safety, role-fit)
```

Lower layers are defined once; upper layers inherit them. You change a screen by
composing patterns, not by writing new tokens.

---

## 1. Principles

These settle disagreements. When a UI decision is unclear, the higher-numbered
principle yields to the lower.

1. **Speed at the counter beats everything.** The POS sale is performed hundreds
   of times a day. Save clicks, keep focus on the scan field, never make a
   cashier wait for a full page reload mid-sale.
2. **Clarity over density.** Staff are not power users. Prefer obvious labels,
   generous spacing, and one clear action over a dense control panel.
3. **Prevent the costly mistake.** Below-cost sales, wrong batch, wrong change,
   data resets — these get confirmation, a written reason where money or stock
   is at risk, and an audit trail.
4. **Show only what the role needs.** A cashier never sees cost, profit, or
   admin tools. Visibility follows `core.permissions`, never guesswork.
5. **One system, two surfaces.** A light working surface for daytime data entry;
   a dark "ink" console surface for identity, the cart, and focus moments. They
   are deliberately different and must not blur into each other.

---

## 2. Tokens — the contract

All values live in `:root` in `app/core/static/core/css/dashboard.css`.
**Use the variable, never the raw value.** Raw hex in a template or new CSS rule
is a defect (see the Debt register, §10, for existing violations being retired).

### 2.0 Tailwind mapping (Phase 1)

Tailwind CSS **v4.3.3** (standalone CLI, no Node) is available alongside
`dashboard.css`. Both stylesheets load on every dashboard page. Preflight is
**off** so Tailwind does not reset global element styles.

- **Input:** `tailwind/input.css` (CSS-first `@theme`, no `tailwind.config.js`;
  kept outside `static/` so WhiteNoise does not resolve CLI `@import`s)
- **Output:** `app/core/static/core/css/tailwind.css` (built at image build time
  and by `scripts/build_tailwind.sh`)
- **Local workflow:** `docs/guides/TAILWIND_WORKFLOW.md`

`:root` custom properties in `dashboard.css` remain the authoritative token
names. The Tailwind `@theme` block mirrors the same values into Tailwind
namespaces so utilities exist. **Do not use Tailwind's default palette.**

| DESIGN_SYSTEM token | Tailwind theme variable | Example utilities |
|---|---|---|
| `--bg` | `--color-bg` | `bg-bg` |
| `--surface` | `--color-surface` | `bg-surface` |
| `--surface-subtle` | `--color-surface-subtle` | `bg-surface-subtle`, `hover:bg-surface-subtle` |
| `--text` | `--color-text` | `text-text` |
| `--text-soft` | `--color-text-soft` | `text-text-soft` |
| `--border` | `--color-border` | `border-border` |
| `--border-strong` | `--color-border-strong` | `border-border-strong` |
| `--primary` | `--color-primary` | `bg-primary`, `border-primary` |
| `--primary-hover` | `--color-primary-hover` | `hover:bg-primary-hover` |
| `--success` | `--color-success` | `bg-success`, `text-success` |
| `--danger` | `--color-danger` | `bg-danger`, `text-danger` |
| `--warning` | `--color-warning` | `bg-warning`, `text-warning` |
| `--focus` | `--color-focus` | `bg-focus`, `outline-focus` |
| `--ink` | `--color-ink` | `bg-ink` |
| `--ink-soft` | `--color-ink-soft` | `bg-ink-soft` |
| `--ink-border` | `--color-ink-border` | `border-ink-border` |
| `--ink-text` | `--color-ink-text` | `text-ink-text` |
| `--ink-text-dim` | `--color-ink-text-dim` | `text-ink-text-dim` |
| `--accent` | `--color-accent` | `bg-accent`, `text-accent`, `accent-accent` |
| `--accent-bright` | `--color-accent-bright` | `bg-accent-bright` |
| `--radius` | `--radius-DEFAULT` | `rounded` |
| `--shadow` | `--shadow-DEFAULT` | `shadow` |
| `--font-sans` | `--font-sans` | `font-sans` (includes Noto Sans Khmer) |
| `--font-mono` | `--font-mono` | `font-mono` |

Phase 1 converts only `/dashboard/styleguide/` to utilities. All other templates
still use `dashboard.css` component classes.

### 2.1 Light working surface

| Token | Value | Use |
|---|---|---|
| `--bg` | `#f6f8fa` | page background |
| `--surface` | `#ffffff` | panels, cards |
| `--surface-subtle` | `#f8fafb` | hover rows, insets, secondary buttons |
| `--text` | `#1a2330` | primary text |
| `--text-soft` | `#5f6b76` | labels, hints, captions |
| `--border` | `#d8dee4` | default 1px borders |
| `--border-strong` | `#aeb8c2` | input/button borders |

### 2.2 Ink console surface (sidebar, POS cart, payment, auth)

| Token | Value | Use |
|---|---|---|
| `--ink` | `#0b1220` | console background |
| `--ink-soft` | `#13314a` | raised elements on ink |
| `--ink-border` | `#1e3a5f` | borders on ink |
| `--ink-text` | `#c9d7e6` | text on ink |
| `--ink-text-dim` | `#5c7f9f` | muted text on ink |
| `--accent` | `#0e7490` | primary accent (teal) on ink |
| `--accent-bright` | `#7dd3fc` | active/hover accent on ink |

### 2.3 Semantic (actions & feedback)

| Token | Value | Use |
|---|---|---|
| `--primary` / `--primary-hover` | `#2563eb` / `#1d4ed8` | primary action buttons, links |
| `--success` | `#127454` | success, confirm, sell-OK |
| `--danger` | `#b42318` | destructive, below-cost, errors |
| `--warning` | `#b7791f` | low stock, caution |
| `--focus` | `#0ea5e9` | focus accents |

### 2.4 Status ramp (pills & badges)

Status uses a fixed pastel-background / dark-text pairing. **Do not** use the
semantic action colors for status pills — they are a separate scale.

| Meaning | Background | Text | Class |
|---|---|---|---|
| neutral / sold out | `#f1efe8` | `#444441` | `.pill` / `.pill-neutral` |
| success / active / paid | `#e1f5ee` | `#085041` | `.pill-success` |
| warning / low stock | `#faeeda` | `#633806` | `.pill-warning` |
| danger / expired / below-cost | `#fcebeb` | `#791f1f` | `.pill-danger` |
| info / promo / status | `#e6f1fb` | `#0c447c` | `.pill-info` |

### 2.5 Typography

- **Sans:** `--font-sans` = Inter → Noto Sans Khmer → system. All UI text.
  Khmer is self-hosted (`@font-face`, `app/core/static/core/fonts/noto-sans-khmer.woff2`),
  so it renders identically on every till.
- **Mono:** `--font-mono`. **Every machine value** — codes, barcodes, batch
  numbers, prices, quantities, timestamps, IDs, IP addresses. Never for prose.
  Apply with the `.mono` class.
- **Scale (current):** body 14px / line-height 1.45. Panel `h2` 16px. Topbar
  `h1` 19px. KPI value 26px mono. Pills 11.5px. Use these; don't introduce
  arbitrary sizes.
- **Weights:** 600 for emphasis/labels in V7+ components. (Legacy buttons use
  750 — see Debt §10.)

### 2.6 Spacing, radius, motion

- **Spacing:** multiples of 4 (4, 6, 8, 10, 12, 14, 16, 20, 24). Component-internal
  gaps in px; vertical page rhythm in the same scale.
- **Radius:** `--radius` (10px) for panels, cards, pills-rectangles, quick keys.
  999px for pills/badges/avatars. (Legacy buttons/inputs use 6px — Debt §10.)
- **Shadow:** `--shadow` only. No other drop shadows. No gradients, blur, or glow
  on the light surface. (The ink/auth surface may use the defined glow accents.)
- **Motion:** 0.15–0.16s ease for layout transitions (sidebar, frame loading).
  Toasts auto-fade after 4s (success only). No decorative animation.

---

## 3. Iconography

Inline SVG via the `{% icon %}` tag — `app/core/templatetags/melodu_icons.py`.
**No icon webfont, no external dependency.** 24×24 stroke icons, Tabler outline
style, `stroke-width 1.8`, `currentColor`.

```django
{% load melodu_icons %}
{% icon "cart" %}              {# 18px default #}
{% icon "alert" 15 %}         {# custom size #}
{% icon "home" 17 "nav-ic" %} {# size + extra class #}
```

- Add an icon by adding one entry to the `ICONS` dict; never hand-draw paths in a
  template, never pull a second icon set.
- Icons inherit color and are `aria-hidden` (decorative). Icon-only buttons need
  an `aria-label`.
- Current set (32, alphabetical): activity, alert, barcode, camera, cart, cash,
  category, chart, check, clock, dollar, hold, home, logout, logs, package,
  percent, plus, printer, receipt, scan, search, settings, shield, sidebar, tag,
  trend-up, truck, upload, user, users, x. (The live styleguide is the source of
  truth for this list.)

---

## 4. Components

Each component: what it is, the markup, variants, and rules. All are rendered
live on the styleguide page.

### 4.1 Buttons — `.btn`
Base `.btn` (or any `<button>`). Variants: `.btn-primary` (blue, the main
action), `.btn-success` (green, complete/confirm), `.btn-danger` (destructive),
`.btn-secondary` (subtle). `.full-width` to stretch. Icon + label allowed.
**One primary action per view.** Destructive actions pair with
`data-confirm-message`.

```django
<button class="btn btn-primary">{% icon "plus" 16 %} {% trans "New product" %}</button>
<button class="btn btn-danger" data-confirm-message="{% trans 'Delete?' %}">{% trans "Delete" %}</button>
```

### 4.2 Status pill — `.pill`
Inline status label. Variants in §2.4. Use for any enum/state in a table or
header. Prefer over plain text for status columns.

```django
<span class="pill pill-success">{% trans "Active" %}</span>
<span class="pill pill-danger">{% trans "Expired" %}</span>
```

### 4.3 Role badge — `.role-badge`
A pill keyed to staff role. Classes `.role-owner`, `.role-manager`,
`.role-inventory`, `.role-cashier`, `.role-viewer` (each its own color). Render
with `role-{{ role|lower }}`. Used in the user list and profile dropdown only.

### 4.4 Panel — `.panel`
The base container: white surface, 1px border, `--radius`. Optional
`.panel-header` with `<h2>` + `<p>` subtitle. The unit every page is built from.

```django
<section class="panel">
  <header class="panel-header"><div><h2>{% trans "Title" %}</h2><p>{% trans "Subtitle" %}</p></div></header>
  …
</section>
```

### 4.5 KPI card — `.kpi-card`
A headline metric: `.kpi-label` (icon + caption), `.kpi-value` (mono number),
`.kpi-hint` (context). Accent variants `.kpi-warning` / `.kpi-danger` recolor
the whole card. Lay out in `.kpi-grid` (auto-fit, min 160px). Home dashboard
only.

### 4.6 Action card — `.action-card`
A large tappable shortcut: leading `.action-ic`, `<strong>` title, `<span>`
description. Lay out in `.action-grid`. Used for quick actions and report menus.

### 4.7 Data table — `.data-table`
Standard table: uppercase 11px headers, row hover, centered `.empty-cell` for
empty state. Wrap in `.table-scroll` when it can overflow. Code/amount columns
get `.mono`. Status columns get a pill.

### 4.8 Forms — `.form-stack` / `.form-grid`
`.form-stack` = vertical fields; `.form-grid` = responsive two-column (collapses
to one on mobile). `.input-row` groups an input with an adjacent button (scan,
quick-add). `.quantity-stepper` for −/+ number controls. Errors render via
`.errorlist`. Filter forms reuse `dashboard/_list_filter.html`.

### 4.9 Quick key — `.quick-key`
POS tap button: `<strong>` name, `<span class="mono">` price. `.quick-key-promo`
variant (amber) for promotions, with `.promo-tag`. Grid: `.quick-key-grid`.

### 4.10 Alert / toast — `.alert`
Inline message: `.alert-success` / `.alert-warning` / `.alert-danger`, left
accent bar. Stack in `.message-stack`. Success alerts auto-fade after 4s;
warnings and errors persist.

### 4.11 Pagination — `dashboard/_pagination.html`
Shared include. Centered, mono "Page X of Y". Always use this; never hand-roll.

### 4.12 Empty state — `.empty-state` / `.empty-cell`
Friendly centered message with an icon when a list or region has no data. Every
list and table must define one.

### 4.13 Modal / overlay
Patterns: scanner modal, quick-create modal, quick-find (`Ctrl/Cmd+K`), payment
dialog. All toggle a `hidden` attribute, close on `Esc` and backdrop click, and
are bound via event delegation (survive partial navigation).

### 4.14 Column filter — `.col-filter`
A funnel control embedded in a `.data-table` header that opens a popover to
filter that column. Built on `<details>` (like the profile menu) so it needs no
custom open/close JS. The host `<th>` carries `.has-filter`. The funnel shows
`.is-active` (teal) when that column has a selection.

The popover (`.col-filter-pop`) **adapts to the column type**:
- **enum** (status, category): `.col-filter-search` to narrow long lists +
  `.col-filter-options` checkbox list. Multi-select = OR within the column.
- **text** (name, code): a single "contains…" input.
- **date** (sale date): a from/to range.

It ends in `.col-filter-actions` with **Apply** (submits the enclosing GET filter
form → server-side, correct across all pages) and **Clear**. Multiple column
filters combine as AND.

```django
<th class="has-filter">{% trans "Status" %}
  <details class="col-filter {% if status_selected %}is-active{% endif %}">
    <summary aria-label="{% trans 'Filter status' %}">{% icon "search" 14 %}</summary>
    <div class="col-filter-pop">
      <p class="col-filter-title">{% trans "Filter: Status" %}</p>
      <div class="col-filter-options">
        {% for value, label in status_choices %}
          <label><input type="checkbox" name="status" value="{{ value }}"
            {% if value in status_selected %}checked{% endif %}> {{ label }}</label>
        {% endfor %}
      </div>
      <div class="col-filter-actions">
        <button class="btn btn-primary" type="submit">{% trans "Apply" %}</button>
        <button class="btn" type="reset">{% trans "Clear" %}</button>
      </div>
    </div>
  </details>
</th>
```

Implementation notes: the table must **not** sit in an `overflow:auto` wrapper
when funnels are present, or the popover clips — render filtered tables without
`.table-scroll`, or solve clipping in the feature task. Outside-click-to-close
is not native to `<details>`; add a small delegated handler if needed (same gap
as the profile menu — acceptable).

### 4.16 Permission matrix — `.matrix-grid`
A role × capability grid for the authorization editor. A `.data-table.matrix-grid`
where rows are capabilities (grouped by area under a `.matrix-group` row) and
columns are roles; each body cell is a centered checkbox. The Owner column is
rendered all-checked and disabled — an Owner always holds every capability and
can never be locked out. The whole grid is one GET/POST form; checkboxes are
named `cap__{role_slug}__{capability_key}` so the view rebuilds each role's
capability list from what's checked. Capability labels come from
`core.capabilities`. Every save is audited.

```django
<table class="data-table matrix-grid">
  <thead><tr><th>{% trans "Capability" %}</th>
    {% for role in roles %}<th class="matrix-role">{{ role.name }}</th>{% endfor %}</tr></thead>
  <tbody>
    {% for group, items in capability_groups %}
      <tr class="matrix-group"><td colspan="…">{{ group }}</td></tr>
      {% for key, label in items %}
        <tr><td>{{ label }}</td>
          {% for role in roles %}<td class="matrix-cell">
            <input type="checkbox" name="cap__{{ role.slug }}__{{ key }}"
              {% if role.is_owner %}checked disabled{% elif key in role.capabilities %}checked{% endif %}>
          </td>{% endfor %}
        </tr>
      {% endfor %}
    {% endfor %}
  </tbody>
</table>
```

### 4.15 Active-filter bar — `.filter-bar`
A summary line above the table that states the current filter rule in plain
words, rendered **server-side from the applied filters** so it always matches the
data. Each `.filter-chip` is removable (an `x` link that drops that value);
`.filter-bar-clear` resets all. Only rendered when at least one filter is active.

```django
{% if active_filters %}
<div class="filter-bar">
  <span class="filter-bar-label">{% icon "search" 13 %} {% trans "Showing" %}</span>
  {% for f in active_filters %}
    {% if not forloop.first %}<span class="filter-bar-join">{% trans "and" %}</span>{% endif %}
    <span class="filter-chip">{{ f.label }}: {{ f.values|join:", " }}
      <a href="{{ f.remove_url }}" aria-label="{% trans 'Remove' %}">{% icon "x" 13 %}</a></span>
  {% endfor %}
  <a class="filter-bar-clear" href="{{ request.path }}">{% trans "Clear all" %}</a>
</div>
{% endif %}
```

---

## 5. Page archetypes

Every screen is one of these. Build new pages by copying the archetype, not from
scratch. (Archetype base templates are a planned consolidation — see §10.)

### 5.1 List page
`.panel` (title + primary "New …" action in the header) → optional
**active-filter bar** (§4.15) → `.data-table` whose filterable headers carry a
**column filter** (§4.14) → `_pagination.html`. Filtering is server-side via a
single GET form wrapping the table; multiple column filters combine as AND.
Examples: products, sales history, users, audit logs. Rules: every column that
is a code/amount is `.mono`; every status is a pill; define the empty state.

The legacy separate filter card (`dashboard/_list_filter.html`) is **superseded**
by this pattern and is being retired page by page (see Debt §10).

### 5.2 Form page
`.panel` → `.form-grid`/`.form-stack` grouped into logical sections →
`.form-actions` with one `.btn-primary` save. Examples: product form, settings,
user form. Rules: group related fields; one primary action; inline field errors;
destructive options confirm.

### 5.3 Detail page
`.panel-header` with title + status pill → fact grid (`.form-grid` of read-only
pairs) → related lists in nested panels. Examples: sale detail, stock batch
detail. Rules: status as a pill in the header; money/codes in mono; respect cost
visibility.

### 5.4 Workflow page (POS)
The full-viewport locked register: two panes inside `.pos-layout`, page does not
scroll on desktop (only inner regions do), light scan/quick-key pane left, ink
cart pane right with totals + charge pinned at the bottom. This archetype is
unique to POS — do not reuse its locking elsewhere.

### 5.5 Auth / status page
Centered ink console card on the grid backdrop. Login, access-denied, no-role,
404/500. Terminal-line header, brand mark, one primary action. Friendly, never a
raw stack trace.

---

## 6. Interaction & motion

- **Partial navigation (`nav.js`):** sidebar/mobile-nav clicks swap only the
  `.app-frame`; the sidebar never reloads. Opt a link out with `data-full-nav`
  (receipts, print, downloads, Django admin). After a swap, `meloduPageInit()`
  re-runs page-load effects.
- **No-reload POS (`pos.js`):** scan/add/update/remove/clear post via fetch and
  swap `#main-content`. The checkout form opts out with `data-full-submit`.
- **Event delegation everywhere.** All JS binds on `document`, not on elements,
  so bindings survive DOM swaps. New interactive markup must follow this — never
  bind in a one-shot `querySelectorAll` loop at load.
- **Focus discipline:** the POS scan field auto-focuses on load and after every
  cart change. Modals focus their first input and restore focus on close.
- **Keyboard:** `F9` = complete sale, `Esc` = clear scan / close modal,
  `Ctrl/Cmd+K` = quick-find. Document any new shortcut here.
- **Loading:** swapped regions get `.frame-loading` (60% opacity). No spinners.

---

## 7. Content & language

- **Bilingual (EN + KH).** Every user-facing string is wrapped in `{% trans %}`
  / `{% blocktrans %}`. Khmer is a first-class language, not an afterthought.
- **Voice:** plain, calm, imperative for actions ("Receive stock", "Complete
  sale"). Sentence case for labels and buttons — never Title Case or ALL CAPS in
  content (uppercase is a CSS treatment for table headers/eyebrows only).
- **Empty states** explain what to do next, not just "no data".
- **Errors** say what happened and how to recover; never expose internals.
- **Numbers:** money and quantities always mono; show ≈KHR alongside USD where a
  total is displayed, using the store exchange rate.

---

## 8. Accessibility & device matrix

**Target widths (must all work):**

| Class | Width | Behaviour |
|---|---|---|
| Wide | ≥1500px | full-bleed POS, larger quick keys, taller cart |
| PC | 900–1500px | sidebar + content, cart 330–480px |
| Tablet | 640–900px | sidebar hides → mobile bottom nav; POS stacks |
| Phone | <640px | single column, ≥42px touch targets, stepper enlarged |

- **Touch targets** ≥42px on phone; quantity steppers enlarged there.
- **Contrast:** all status text uses the dark stop of its own ramp (§2.4) — never
  black on a colored fill.
- **Focus rings** visible on every input (accent ring). Never remove outlines
  without a replacement.
- **Scanner = keyboard.** USB barcode scanners type + Enter; the scan field must
  stay focused and submit on Enter without a mouse.
- **`sr-only`** labels on icon-only controls; skip-link first in the DOM.

---

## 9. Definition of Done (UI)

A screen is finished only when **all** are true:

- [ ] Uses tokens only — no raw hex / arbitrary px in the change
- [ ] Built from an existing component + page archetype (§4, §5)
- [ ] New/changed components are rendered on the styleguide page
- [ ] Works at all four widths (§8)
- [ ] Keyboard + scanner flow works; focus handled
- [ ] Empty, loading, and error states exist
- [ ] All strings `{% trans %}`'d (EN + KH)
- [ ] Cost/role visibility respected (§ principle 4)
- [ ] Destructive/below-cost actions confirm + audit
- [ ] JS uses event delegation (survives partial nav)
- [ ] Print views (receipt/label) left untouched unless the task is about them
- [ ] Tests pass; `collectstatic` clean; **web restarted** so new assets serve

---

## 10. Debt register

Known divergences from this contract, each to be retired by a **dedicated
design-system task** (never silently inside feature work). Listed so the doc
stays honest about reality:

1. **Buttons/inputs use `radius 6px` and `font-weight 750`** while V7+ components
   use `--radius` (10px) and weight 600. Unify on a `--radius-sm` token + weight
   600.
2. **Raw hex in components:** pills (§2.4), role badges (§4.3), and KPI accent
   colors use literal hex instead of tokens. Promote the status ramp and role
   colors to named tokens.
3. **CSS is append-only.** `dashboard.css` (~1760 lines) is organized as stacked
   `/* V7 */ /* V8.1 */ …` sections with later overrides. Split into
   `tokens.css` / `components.css` / `pages/*.css` (or clearly delimited,
   deduplicated sections).
4. **No archetype base templates yet.** §5 archetypes are conventions, not
   enforced bases. Extract `base_list.html` / `base_form.html` / `base_detail.html`.
5. **`:has()` reliance.** The POS viewport lock uses `body:has(.pos-layout)`
   (Chrome 105+/Safari 15.4+). If older till browsers appear, switch to a body
   class set by the view.
6. **Legacy filter card.** `dashboard/_list_filter.html` (separate filter card)
   is superseded by the column-filter + active-filter-bar pattern (§4.14–4.15).
   Migrate each list page (products → sales → users → audit → inventory) to the
   new pattern, then remove the include. Tracked as a feature rollout, page by
   page.

---

## 11. Change log

Append one line per design-system task (the only thing that may edit this file).

- 2026-06-13 — Initial system extracted from V6–V8.3 code; styleguide page added.
- 2026-06-13 — Added column-filter (§4.14) and active-filter-bar (§4.15)
  components; updated list-page archetype (§5.1) to the column-header filter
  pattern; legacy `_list_filter.html` marked superseded (Debt §10.6). Components
  and CSS defined and demoed on the styleguide; list-page wiring is a separate
  feature task.
- 2026-06-13 — Added permission-matrix component (§4.16) for the authorization
  editor; CSS + styleguide demo. Consumed by the Authz Phase 2 role-matrix page.
- 2026-08-06 — Tailwind Phase 1: standalone CLI v4.3.3 (CSS-first `@theme`, no
  Node in runtime), Melodu 24-token theme mapped in §2.0, styleguide converted
  to utilities; `dashboard.css` unchanged and still loaded for all other pages.
- 2026-08-11 — Form-field affordance: text inputs, selects and textareas fill
  with `--surface-subtle` by default (was `--surface`) so a field's extent is
  visible against a white card, and lift to `--surface` on focus. CSS-only;
  styleguide Forms section reflects it automatically via the global input rule.
- 2026-08-12 — Native `<select>` restyled with `appearance: none` and a custom
  chevron so dropdowns match the styled inputs (dark chevron on the light
  surface, light chevron on the ink POS cart selects). Added an `emphasis`
  option to the report metric-card component (`_metric_card.html`) — accent
  border, tint and value colour — for the single most important number on a
  page (e.g. daily revenue). CSS + component + this log together.
