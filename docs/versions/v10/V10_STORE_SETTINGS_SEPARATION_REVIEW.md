# V10-006 Store Settings Separation Review

Status: Complete
Last updated: 2026-06-16

## Purpose

Review the current singleton settings model and plan how it would split safely for future stores.

## Current Settings

| Setting Area | Current Field/Model | Store-specific Later? | Status |
| --- | --- | --- | --- |
| Store name/address/phone | `StoreSetting` | Yes | Current |
| Logo | `StoreSetting.logo` | Yes | Current |
| Receipt header/footer/paper/font/logo toggle | `StoreSetting` | Yes | Current |
| Currency symbol and KHR rate | `StoreSetting` | Needs Verification | Current |
| KHQR image | `StoreSetting.khqr_image` | Yes | Current |
| Cost-visible roles | `StoreSetting.cost_visible_roles` | Needs Verification | Current |
| POS quick keys | `StoreSetting.quick_key_products` | Yes | Current |
| Auth runtime toggles | `AuthSetting` | No, likely global | Current |

## Recommended Separation

| Future Data | Recommendation | Status |
| --- | --- | --- |
| Store identity/contact | Move to future `Store`. | Future / Proposed |
| Receipt and payment display settings | Keep in a per-store settings model linked to `Store`. | Future / Proposed |
| Quick keys | Make store-specific, because best sellers differ by location. | Future / Proposed |
| Cost-visible roles | Keep global until store-specific role policy is explicitly approved. | Needs Verification |
| Auth settings | Keep singleton/global. | Future / Proposed |
| Logo/KHQR media | Store-specific media with MinIO-backed storage in production. | Future / Proposed |

## Migration Proposal

| Step | Status |
| --- | --- |
| Create default `Store` row. | Future / Proposed |
| Copy `StoreSetting` identity fields into default store or linked per-store settings. | Future / Proposed |
| Keep `StoreSetting.load()` compatibility during migration or replace callers in one coordinated pass. | Future / Proposed |
| Verify receipts, labels, POS payment dialog, and quick keys after migration. | Future / Proposed |
| Add rollback notes before release. | Future / Proposed |

## Risk Notes

| Risk | Mitigation |
| --- | --- |
| Receipt/KHQR settings could break checkout. | Keep migration small and browser-test POS receipt/payment. |
| `StoreSetting.load()` is used as singleton helper. | Replace carefully and test all callers. |
| Cost visibility might become confusing if scoped per store too early. | Keep global until real business rule is approved. |
| Media paths could change during storage migration. | Preserve existing media files and URL behavior. |

## Verification

Planning-only. No settings model or view behavior changed.

