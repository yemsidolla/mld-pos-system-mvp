# ADR-0009: Offline-First Mobile Client and Sync API

Status: **Proposed** (design for review — not accepted, nothing built)
Date: 2026-08-15
Supersedes on acceptance: parts of ADR-0001 (the "Django templates + vanilla JS
only" boundary), for the mobile client path only.

## Context

Sidolla wants the POS usable on tablets and phones. In discussion three
constraints were fixed, and they shape everything below:

1. **For ourselves first.** One shop (Melodu), not multiple tenants yet.
   Multi-tenancy (ADR-0008) is **not** a prerequisite and is out of scope here.
2. **Offline-first.** A sale must complete with no network, then sync.
3. **The device is usually co-located with the server.** Most of the time the
   tablet or phone is on the same local network as the backend. This is the key
   architectural lever: if the backend is reached by a **local network address /
   local DNS name** rather than a public internet route, then **losing the
   internet is not the same as losing the backend** — a WAN outage still leaves
   the device talking to the local server in real time. So the common "offline"
   situation is really *"no internet, local server still reachable,"* where
   near-real-time sync simply continues. The genuine "cannot reach the backend at
   all" case (the local network itself is down, or the device has left the
   premises) becomes the rarer edge. Offline-first is the safety net for that
   edge, not the everyday path — which materially de-risks the whole design.

React Native is acceptable to Sidolla as the client technology.

### What exists today

- Server-rendered **Django monolith**, no JSON API. Django can't feed a React
  Native client — that needs an API.
- **Business logic already lives in service functions**: `receive_stock`,
  `validate_sellable_batch`, `lookup_original_barcode`, `lookup_custom_code`,
  sale confirmation, `adjust_stock`. An API wraps these; it does not reinvent
  them. This is the single biggest reason this is feasible rather than a rewrite.
- **Batch-level inventory** (ADR-0003): a sale deducts from a specific
  `StockBatch.quantity_available`, must not go negative, and writes an
  `InventoryMovement`. The server is the source of truth for stock. Offline
  sales challenge this directly — see the oversell policy below.

### Why offline-first pushes toward native over a PWA

For a hard offline-first requirement, a native app is the stronger choice:
on-device **SQLite** and reliable background sync. iOS deliberately limits PWAs
on exactly these axes (evicts IndexedDB under storage pressure, throttles
background sync). A PWA would fight the one requirement that matters most here.
This reverses the PWA-first lean that would be correct for mere "make it mobile."

## Decision (proposed)

1. **Add a DRF (Django REST Framework) API layer** to the existing monolith,
   wrapping the current service functions. The monolith stays; the web app stays
   for back-office (reports, admin, user management). The API is additive.
2. **Build a React Native client** for the sale path (scan → cart → checkout)
   plus the catalog/stock reads it needs, with an **on-device SQLite store** and
   a **sync engine**.
3. **The offline scope is deliberately narrow**: the sale path and the read data
   it depends on. Reports, admin, stock-in, user management, promotions editing
   stay **online-only** (web or API-when-connected). Keeping offline scope tight
   is what makes this tractable.

### The offline sale model — the crux

**A completed offline sale is a fact, not a request.** The customer has walked
out with the goods. The system cannot later "reject" it. This single truth
drives the whole design:

- The client generates a **sale UUID** at checkout. Sales are **idempotent** on
  that UUID — retries and re-syncs never double-post.
- The client holds a **cached snapshot** of sellable batches (quantity, price)
  and validates the sale **locally** against that snapshot at checkout, so the
  common case (stock is there) works offline with confidence.
- On sync, the server **re-validates** each sale with `validate_sellable_batch`
  against *live* stock and records it. Three outcomes:
  - **Stock present** (the overwhelming majority, given LAN + seconds-sync +
    one small shop): deduct the batch, write the `InventoryMovement`, done.
  - **Batch short** (a rare race — another device sold the same units in the
    sync window): the sale is still **recorded as real**; the shortfall becomes
    an **oversell exception** flagged for a human to reconcile (the physical
    count was wrong, or two tills raced). Inventory reconciles to reality; the
    sale is never discarded.
  - **Product/batch gone** (deleted server-side while offline): recorded as an
    exception for manual resolution.

This is the honest answer to "must complete sales offline" on batch inventory:
not "overselling is impossible" (it isn't, in any offline system) but **"rare,
detected on sync, and reconciled — never a lost sale."** It is viable *here*
specifically because the shop is small and the backend is usually reachable on
the local network (constraint 3), so sync is near-continuous and the window for
two devices to race the same batch is tiny. It would not be viable for a
multi-shop cloud POS.

### Sync protocol (sketch)

- **Pull** (device ← server): catalog, sellable batches, store settings, price
  changes — as a **delta since last sync** using an `updated_at` watermark.
  (Note: the image backfill deliberately did not bump `updated_at`, so watermarks
  stay meaningful.)
- **Push** (device → server): queued sales, each with its client UUID; server
  upserts idempotently and returns per-sale results (accepted / exception).
- **Cadence**: on connectivity, on app foreground, and on a short timer. When
  the local server is reachable (the usual case, see constraint 3) this is
  effectively continuous — the full-offline queue is exercised only during a
  genuine local-network outage.
- **Backend address**: the client targets the backend by a **local DNS name**
  (e.g. `pos.melodu.local`) resolved on the local network, not a hardcoded IP and
  not a public internet route. This is what makes "internet down, backend still
  reachable" work, and it lets the server move without reconfiguring devices.
- **Auth**: token-based (DRF token or JWT). The device caches a token to operate
  offline under a known cashier identity. Token lifetime and offline-revocation
  are an open question (below).

## Consequences

| Consequence | Type |
| --- | --- |
| Business logic reused via services, not rewritten. | Benefit |
| Live Django web POS keeps running, untouched, throughout. | Benefit |
| Genuine offline sale capability on a small LAN shop. | Benefit (the goal) |
| A new API surface to build, secure, and maintain. | Cost |
| A second codebase (React Native / TS) with its own DB and sync engine. | Cost |
| Three things now run: web app, API, native app. | Cost |
| Oversell is possible but bounded, detected, and reconciled — not eliminated. | Accepted risk |
| App distribution (even internal / self-hosted) and update process. | Cost |
| Offline auth means a cached token on the device — a security surface. | Risk |

## Alternatives considered

| Alternative | Decision |
| --- | --- |
| **PWA + IndexedDB + service worker** | Cheaper, reuses the web app, no API — but iOS PWA storage/background-sync limits undermine the hard offline-first requirement. Rejected *for offline-first*; would be the right call for "offline-resilient only." |
| **Keep web-only, responsive** | The app already works in mobile browsers. Rejected because it cannot meet "complete sales offline." |
| **Native + full server-authoritative (no offline)** | Simplest data model, but fails the core requirement. Rejected. |
| **Sync framework (WatermelonDB / PowerSync / ElectricSQL)** | Worth evaluating in the PoC — could remove hand-rolled sync risk. Open. |

## Staged plan (proposed)

1. **This ADR** — agree the direction and the oversell policy. ← we are here
2. **Thin vertical slice PoC**: RN app scans a product from its *local* catalog
   with wifi off, completes one sale offline, then syncs to a new DRF endpoint
   that re-validates stock and records the sale idempotently. Proves the
   architecture end-to-end before building breadth. Nothing touches the live till.
3. **Design review of the PoC**, then build out the sale path, then the reads.
4. Multi-tenancy and the "world" goal remain a separate, later program (ADR-0008).

## Open questions for Sidolla

1. **Oversell policy** — confirm the "sale is a fact; shortfall becomes an
   exception to reconcile" model. This is the single most important decision here.
2. **Offline auth lifetime** — how long may a device operate offline on a cached
   token, and how do we revoke a lost device?
3. **Which devices** — counter tablet only, or staff phones too? (Affects how
   many devices race for the same stock.)
4. **Build vs. buy sync** — hand-rolled, or evaluate a sync framework in the PoC?
5. **Printing** — receipt printing from the native app: browser can't reach USB
   printers well; native can. Is that a driver for native beyond offline?
