# V4 QA Checklist — User Management, Classification, Printing, and Admin Maintenance

## Functional Checks

- [x] Five roles resolve correctly with legacy group fallback — Implemented
- [x] User create/edit/disable with audit — Implemented
- [x] Product classification fields and filters — Implemented
- [x] Receipt uses store settings (80mm) — Implemented
- [x] Label template CRUD and print — Implemented
- [x] Promotion labels print with promo pricing — Implemented
- [x] Reset command dry-run and scoped delete — Implemented

## Permission Checks

- [x] Only Owner assigns Owner role — Implemented
- [x] Last Owner cannot be removed — Implemented
- [x] Cashier still blocked from Admin — Implemented

## Data Safety Checks

- [x] Reset never deletes users/audit/templates — Implemented
- [x] Reset requires env + phrase guards — Implemented

## Printing Checks

- [x] Browser print receipt and labels — Implemented
- [ ] Physical thermal printer output — Needs Verification

## Audit Checks

- [x] USER_*, SETTING_CHANGE, BARCODE_PRINT, DATA_RESET audited — Implemented

## Regression Risks

Role/capability changes in V6 must preserve V4 user-management protections.
