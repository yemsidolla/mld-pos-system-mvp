# V8 Tasks: Inventory, Label, and Promotion Professionalization

Status: Complete
Last updated: 2026-06-16

Task statuses start as `Proposed`. When a task is completed, change its status to `Complete` and mark the matching checkbox in `docs/versions/VERSION_COMPLETION_TRACKER.md`. Do not delete completed tasks.

## V8-001

**Task ID:** V8-001  
**Version:** V8  
**Epic:** Inventory Professionalization  
**Module:** Inventory  
**Title:** Inventory workflow audit  
**Business reason:** Inventory workflows must remain accurate and easy to operate.  
**Technical scope:** Audit stock-in, stock overview, batch detail, adjustments, expiry, damaged stock, and stock movement flow.  
**Files likely affected:** `app/inventory/views.py`, `app/inventory/forms.py`, `app/inventory/services.py`, `app/templates/inventory/*.html`, inventory tests, docs.  
**Permission impact:** Inventory capability review only.  
**Data impact:** Audit only unless follow-up implementation is approved.  
**UI impact:** Findings may propose UI improvements.  
**Docs impact:** Update V8 task notes and development log.  
**Acceptance criteria:** Inventory workflow gaps are documented with clear follow-up actions.  
**Test cases:** None for audit-only; implementation follow-ups require targeted tests.  
**Manual UI check:** Stock-in, stock overview, batch detail, adjustment flow.  
**Risk:** Audit may discover high-risk stock issues requiring separate approval.  
**Definition of done:** Audit results accepted, follow-ups tracked, tracker updated.  
**Status:** Complete

## V8-002

**Task ID:** V8-002  
**Version:** V8  
**Epic:** Batch Visibility  
**Module:** Inventory  
**Title:** Stock batch list/detail improvement plan  
**Business reason:** Managers need to understand exact batch condition quickly.  
**Technical scope:** Improve or plan batch list/detail display for expiry, available quantity, supplier, costs, codes, labels, and movement links.  
**Files likely affected:** `app/templates/inventory/inventory_summary.html`, `app/templates/inventory/stock_batch_detail.html`, `app/inventory/views.py`, inventory tests.  
**Permission impact:** Cost fields must obey cost visibility rules.  
**Data impact:** None unless new fields are separately approved.  
**UI impact:** Batch tables/detail cards may change.  
**Docs impact:** Inventory docs if workflow changes.  
**Acceptance criteria:** Batch status, expiry, quantity, supplier, and print/movement actions are clearer.  
**Test cases:** Render and permission tests, especially cost visibility.  
**Manual UI check:** Batch list/detail on desktop/mobile.  
**Risk:** Cost leakage to unauthorized users.  
**Definition of done:** Batch visibility improved or plan accepted, tests pass, tracker updated.  
**Status:** Complete

## V8-003

**Task ID:** V8-003  
**Version:** V8  
**Epic:** Stock Operations  
**Module:** Inventory/reports  
**Title:** Expiry and low-stock operational flow  
**Business reason:** Staff must act before stock expires or runs out.  
**Technical scope:** Review expiry labels, low-stock report links, stock overview warnings, and operational next actions.  
**Files likely affected:** `app/templates/inventory/*.html`, `app/templates/reports/low_stock.html`, `app/templates/reports/expiry.html`, `app/reports/views.py`, tests.  
**Permission impact:** Reports/inventory access unchanged.  
**Data impact:** None unless thresholds/rules are explicitly approved.  
**UI impact:** Warning/critical/expired displays and action links.  
**Docs impact:** Update guides only if process changes.  
**Acceptance criteria:** Staff can see which products/batches need action and why.  
**Test cases:** Report/view tests for low stock and expiry states.  
**Manual UI check:** Low stock, expiry report, stock overview.  
**Risk:** Misleading labels can cause wrong purchasing or disposal action.  
**Definition of done:** Flow reviewed/improved, tests pass, tracker updated.  
**Status:** Complete

## V8-004

**Task ID:** V8-004  
**Version:** V8  
**Epic:** Cost Visibility  
**Module:** Catalog/inventory  
**Title:** Supplier/product cost visibility review  
**Business reason:** Cost information is sensitive and must still help managers make decisions.  
**Technical scope:** Review supplier reference costs, actual/landed cost display, stock-in cost wording, and role visibility.  
**Files likely affected:** `app/templates/catalog/supplier_product_cost_*.html`, `app/templates/inventory/*.html`, `app/core/permissions.py`, tests, docs.  
**Permission impact:** Cost visibility must remain controlled.  
**Data impact:** None unless cost fields/logic change is approved.  
**UI impact:** Cost labels/help text may change.  
**Docs impact:** Cost terminology docs if wording changes.  
**Acceptance criteria:** Cost fields are understandable and visible only to allowed roles.  
**Test cases:** Cost visibility tests and affected view tests.  
**Manual UI check:** Owner/Manager/Cashier cost visibility comparison.  
**Risk:** Sensitive cost data can leak through UI or reports.  
**Definition of done:** Cost behavior verified, tests pass, tracker updated.  
**Status:** Complete

## V8-005

**Task ID:** V8-005  
**Version:** V8  
**Epic:** Codes  
**Module:** Inventory/labels/scanner  
**Title:** Barcode/QR workflow polish  
**Business reason:** Code generation and lookup must be reliable for selling and labeling.  
**Technical scope:** Review batch custom code display, barcode/QR image generation, scanner lookup flows, print shortcuts, and uploaded image decode guidance.  
**Files likely affected:** `app/inventory/services.py`, `app/templates/inventory/barcode_print.html`, `app/templates/dashboard/scanner_modal.html`, `app/core/static/core/js/scanner.js`, tests.  
**Permission impact:** Existing scan/label permissions unchanged.  
**Data impact:** Code generation behavior must not change unless explicitly approved.  
**UI impact:** Barcode/QR display and scanner guidance polish.  
**Docs impact:** Scanner/label docs if workflow changes.  
**Acceptance criteria:** Staff can find, scan, and print codes with fewer mistakes.  
**Test cases:** Scan resolver/code tests and barcode print render tests.  
**Manual UI check:** Camera/manual/upload decode and barcode/QR print.  
**Risk:** Changing code parsing can break POS/stock-in lookup.  
**Definition of done:** Code workflows verified, tests pass, tracker updated.  
**Status:** Complete

## V8-006

**Task ID:** V8-006  
**Version:** V8  
**Epic:** Labels  
**Module:** Label templates  
**Title:** Label template management polish  
**Business reason:** Managers need confidence before printing shelf/product/promotion labels.  
**Technical scope:** Review label template list/form, default template behavior, field toggles, preview clarity, and template naming.  
**Files likely affected:** `app/templates/labels/template_list.html`, `app/templates/labels/template_form.html`, `app/labels/forms.py`, `app/labels/views.py`, labels tests.  
**Permission impact:** Template management remains Owner/Manager-gated.  
**Data impact:** Existing templates must not be deleted or overwritten unexpectedly.  
**UI impact:** Template form/list polish.  
**Docs impact:** `docs/guides/LABEL_TEMPLATE_GUIDE.md` if behavior changes.  
**Acceptance criteria:** Template management is clear and existing templates remain safe.  
**Test cases:** Label template CRUD/render tests.  
**Manual UI check:** Create/edit template and preview printed output if changed.  
**Risk:** Incorrect defaults can alter printed labels.  
**Definition of done:** Template workflow verified, tests pass, tracker updated.  
**Status:** Complete

## V8-007

**Task ID:** V8-007  
**Version:** V8  
**Epic:** Labels  
**Module:** Product/shelf/promotion label workflows  
**Title:** Product/shelf/promotion label workflow  
**Business reason:** Staff need to choose the right label type without trial and error.  
**Technical scope:** Review product label print, shelf label conventions, promotion label print, quantity selection, preview, and print actions.  
**Files likely affected:** `app/templates/labels/label_print.html`, `app/templates/labels/promotion_label_print.html`, `app/labels/views.py`, labels tests, label docs.  
**Permission impact:** Label print permissions unchanged.  
**Data impact:** None unless template data changes are separately approved.  
**UI impact:** Print workflow and preview polish.  
**Docs impact:** Label/promotion label guides if workflow changes.  
**Acceptance criteria:** Staff understand which label type is being printed and what data appears.  
**Test cases:** Label print route/render tests.  
**Manual UI check:** Browser print preview and physical printer if output changes.  
**Risk:** Print CSS/layout changes may waste labels.  
**Definition of done:** Label workflows verified, tests pass, tracker updated.  
**Status:** Complete

## V8-008

**Task ID:** V8-008  
**Version:** V8  
**Epic:** Promotions  
**Module:** Promotions  
**Title:** Promotion setup and lifecycle polish  
**Business reason:** Promotions should be easy to configure and safe to audit.  
**Technical scope:** Review promotion list/form fields, active dates, scope, pricing type, status display, and audit behavior.  
**Files likely affected:** `app/templates/pos/promotion_list.html`, `app/templates/pos/promotion_form.html`, `app/pos/forms.py`, `app/pos/views.py`, POS tests.  
**Permission impact:** Promotion management capabilities unchanged.  
**Data impact:** No promotion calculation changes unless approved.  
**UI impact:** Promotion management polish.  
**Docs impact:** Promotion docs if behavior changes.  
**Acceptance criteria:** Promotion setup fields and lifecycle states are clear.  
**Test cases:** Promotion form/view tests; pricing tests if behavior touched.  
**Manual UI check:** Create/edit/list active and inactive promotions.  
**Risk:** UI changes can imply pricing behavior that does not exist.  
**Definition of done:** Promotion management verified, tests pass, tracker updated.  
**Status:** Complete

## V8-009

**Task ID:** V8-009  
**Version:** V8  
**Epic:** POS Promotion Safety  
**Module:** POS/promotions  
**Title:** POS promotion visibility and below-cost review  
**Business reason:** Cashiers and managers need clear pricing warnings without unsafe overrides.  
**Technical scope:** Review POS promotion display, applied discount explanation, below-cost warning, override path, and audit data.  
**Files likely affected:** `app/templates/pos/pos_sale.html`, `app/pos/pricing.py`, `app/pos/services.py`, `app/core/permissions.py`, POS tests.  
**Permission impact:** Below-cost override capability must remain controlled.  
**Data impact:** Sale price/cost snapshots must remain correct.  
**UI impact:** POS promotion/warning display.  
**Docs impact:** Business rules and development log if behavior changes.  
**Acceptance criteria:** Promotion and below-cost state is visible and safe.  
**Test cases:** POS pricing, below-cost, permission, and sale tests.  
**Manual UI check:** Promotion sale and below-cost warning scenarios.  
**Risk:** Pricing regressions are high risk.  
**Definition of done:** Pricing behavior verified, tests pass, tracker updated.  
**Status:** Complete

## V8-010

**Task ID:** V8-010  
**Version:** V8  
**Epic:** Traceability  
**Module:** Inventory/audit  
**Title:** Inventory audit and movement traceability review  
**Business reason:** Owner/manager must be able to explain stock changes.  
**Technical scope:** Review movement records, audit links, stock-in/cancel/adjust/damage/expiry paths, and dashboard visibility.  
**Files likely affected:** `app/inventory/services.py`, `app/inventory/views.py`, `app/audit/views.py`, inventory/audit templates, tests.  
**Permission impact:** Audit visibility remains capability-gated.  
**Data impact:** No movement model changes unless approved.  
**UI impact:** Movement/audit display improvements may be proposed.  
**Docs impact:** Business rules/audit docs if behavior changes.  
**Acceptance criteria:** Stock changes can be traced from batch/product/user/action.  
**Test cases:** Movement and audit tests for stock workflows.  
**Manual UI check:** Stock movement report, batch detail, audit log.  
**Risk:** Missing or confusing audit/movement data hides stock errors.  
**Definition of done:** Traceability verified, tests pass, tracker updated.  
**Status:** Complete

## V8-011

**Task ID:** V8-011  
**Version:** V8  
**Epic:** Release  
**Module:** QA/release  
**Title:** V8 QA and release preparation  
**Business reason:** Inventory, label, and promotion changes carry operational risk.  
**Technical scope:** Run V8 QA checklist, finalize release notes, update tracker/development log.  
**Files likely affected:** `docs/versions/v8/*`, `docs/versions/VERSION_COMPLETION_TRACKER.md`, `docs/DEVELOPMENT_LOG.md`.  
**Permission impact:** Verify only.  
**Data impact:** Verify only.  
**UI impact:** Verify only.  
**Docs impact:** Finalize V8 docs.  
**Acceptance criteria:** Approved tasks complete/deferred with evidence and test results.  
**Test cases:** Full suite recommended if stock/pricing logic changed.  
**Manual UI check:** Inventory, labels, promotions, POS pricing, physical print if relevant.  
**Risk:** Releasing incomplete stock/pricing work can harm operations.  
**Definition of done:** V8 release note finalized and tracker marked complete.  
**Status:** Complete
