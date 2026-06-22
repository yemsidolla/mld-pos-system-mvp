# V3 QA Checklist — Cost Control, Pricing Rules, and Promotion Foundation

## Functional Checks

- [x] Reference cost CRUD — Implemented
- [x] Sale stores cost snapshots on SaleItem — Implemented
- [x] Cashier blocked below cost — Implemented
- [x] Authorized override requires reason — Implemented
- [x] Promotion applies best single discount — Implemented
- [x] `allow_below_cost` promotion flag respected — Implemented

## Permission Checks

- [x] Promotion management gated — Implemented (evolved to capabilities in V4+)

## Data Safety Checks

- [x] Decimal money fields — Implemented
- [x] Transactional sale confirm — Implemented

## UI/UX Checks

- [x] POS responsive layout improvements — Implemented
- [ ] Phone POS usability — Needs Verification

## Known Missing QA

Production promotion edge cases across date boundaries — Needs Verification.

## Regression Risks

Cost basis logic must remain consistent in V8/V9 reporting.
