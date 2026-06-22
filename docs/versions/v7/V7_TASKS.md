# V7 Tasks: UX/UI Cleanup & Staff Workflow Polish

Status: Complete
Last updated: 2026-06-16

Task statuses start as `Proposed`. When a task is completed, change its status to `Complete` and mark the matching checkbox in `docs/versions/VERSION_COMPLETION_TRACKER.md`. Do not delete completed tasks.

## V7-001

**Task ID:** V7-001  
**Version:** V7  
**Epic:** UX/UI Cleanup  
**Module:** Dashboard navigation  
**Title:** Navigation and naming cleanup audit  
**Business reason:** Staff should know where to go without training or guessing.  
**Technical scope:** Audit sidebar, mobile nav, topbar titles, route labels, and dashboard group names against current workflows.  
**Files likely affected:** `app/core/context_processors.py`, `app/templates/dashboard/base.html`, relevant dashboard templates, docs only if naming changes.  
**Permission impact:** Review only; no permission model change.  
**Data impact:** None.  
**UI impact:** Navigation labels/grouping may change if approved.  
**Docs impact:** Update task tracker/development log; update guides only if labels change.  
**Acceptance criteria:** Navigation is grouped clearly, duplicate/confusing labels are resolved, and role-specific nav stays correct.  
**Test cases:** Role navigation render tests for Owner, Manager, Inventory, Cashier, Viewer.  
**Manual UI check:** Desktop sidebar and mobile bottom nav.  
**Risk:** Renaming can confuse existing users or break tests expecting labels.  
**Definition of done:** Audit notes are resolved or deferred, tests pass, tracker updated.  
**Status:** Complete

## V7-002

**Task ID:** V7-002  
**Version:** V7  
**Epic:** UX/UI Cleanup  
**Module:** Dashboard home  
**Title:** Dashboard home polish  
**Business reason:** The first screen should guide each role to useful daily work.  
**Technical scope:** Review role-specific cards, metrics, quick actions, empty states, and page hierarchy.  
**Files likely affected:** `app/core/views.py`, `app/templates/dashboard/home.html`, `app/core/static/core/css/dashboard.css`, view tests.  
**Permission impact:** Role visibility review only.  
**Data impact:** None.  
**UI impact:** Home page layout/content polish.  
**Docs impact:** Development log; docs only if workflow entry points change.  
**Acceptance criteria:** Each role sees relevant actions only; empty/no-data states are clear.  
**Test cases:** Home render tests for major roles.  
**Manual UI check:** Owner/Manager/Cashier home on desktop and phone width.  
**Risk:** Helpful shortcuts can accidentally expose unavailable workflows.  
**Definition of done:** Role home pages verified, tests pass, tracker updated.  
**Status:** Complete

## V7-003

**Task ID:** V7-003  
**Version:** V7  
**Epic:** Cashier Workflow  
**Module:** POS  
**Title:** POS cashier workflow polish  
**Business reason:** POS speed and clarity matter most at the counter.  
**Technical scope:** Polish scan field prominence, cart readability, payment controls, error messages, scanner affordance, and receipt handoff.  
**Files likely affected:** `app/templates/pos/pos_sale.html`, `app/core/static/core/js/pos.js`, `app/core/static/core/js/scanner.js`, `app/core/static/core/css/dashboard.css`, POS tests.  
**Permission impact:** Cashier access must remain POS-focused.  
**Data impact:** None; no sale logic changes.  
**UI impact:** POS layout and copy polish.  
**Docs impact:** Development log; receipt/POS guide only if workflow behavior changes.  
**Acceptance criteria:** Existing POS flow still works, errors are clearer, and scan/manual fallback remains obvious.  
**Test cases:** POS view tests and sale service regression tests if any behavior path is touched.  
**Manual UI check:** Cashier sale flow, scan modal, payment panel, mobile width.  
**Risk:** UI polish can interrupt scan focus or cart calculation display.  
**Definition of done:** POS smoke flow works, tests pass, tracker updated.  
**Status:** Complete

## V7-004

**Task ID:** V7-004  
**Version:** V7  
**Epic:** Catalog UX  
**Module:** Catalog/products  
**Title:** Catalog/product list polish  
**Business reason:** Product management should be clear as catalog size grows.  
**Technical scope:** Review product list columns, photo display, filters, search, product form sections, quick-add controls, and empty states.  
**Files likely affected:** `app/templates/catalog/product_list.html`, `app/templates/catalog/product_form.html`, `app/templates/catalog/master_data_list.html`, `app/templates/catalog/master_data_form.html`, `app/catalog/views.py`, catalog tests.  
**Permission impact:** Catalog capability remains unchanged.  
**Data impact:** None.  
**UI impact:** Product/catalog table and form polish.  
**Docs impact:** Update product classification guide only if workflow text changes.  
**Acceptance criteria:** Product list is scannable, photos/classification are visible where useful, and form sections are easy to complete.  
**Test cases:** Product list/form render tests and permission tests.  
**Manual UI check:** Product list, create/edit form, quick-add animal type/category/brand where applicable.  
**Risk:** Table changes can hide important product identifiers.  
**Definition of done:** Product workflows render cleanly, tests pass, tracker updated.  
**Status:** Complete

## V7-005

**Task ID:** V7-005  
**Version:** V7  
**Epic:** Inventory UX  
**Module:** Inventory/stock-in  
**Title:** Inventory and stock receiving workflow polish  
**Business reason:** Inventory staff need fewer mistakes when receiving and reviewing stock.  
**Technical scope:** Polish stock overview, batch detail, stock-in form, cost wording, expiry/quantity messaging, and post-stock-in shortcuts.  
**Files likely affected:** `app/templates/inventory/inventory_summary.html`, `app/templates/inventory/stock_batch_detail.html`, `app/templates/inventory/stock_in.html`, `app/inventory/views.py`, inventory tests.  
**Permission impact:** Inventory capability remains unchanged.  
**Data impact:** None; no stock service changes.  
**UI impact:** Inventory layout, messages, buttons, and field help.  
**Docs impact:** Development log; inventory guide only if wording or workflow materially changes.  
**Acceptance criteria:** Receiving stock is understandable and stock/batch states are easier to scan.  
**Test cases:** Inventory and stock-in render tests; existing service tests if form behavior changes.  
**Manual UI check:** Receive stock, stock overview, batch detail on desktop/mobile.  
**Risk:** Cost/quantity wording can alter staff interpretation.  
**Definition of done:** UI clarified without service changes, tests pass, tracker updated.  
**Status:** Complete

## V7-006

**Task ID:** V7-006  
**Version:** V7  
**Epic:** Label/Promotion UX  
**Module:** Promotions and labels  
**Title:** Promotion and label page polish  
**Business reason:** Staff need clearer label/print and promotion setup flows.  
**Technical scope:** Review promotion list/form, label template list/form, barcode print, product label print, and promotion label print pages.  
**Files likely affected:** `app/templates/pos/promotion_list.html`, `app/templates/pos/promotion_form.html`, `app/templates/inventory/barcode_print.html`, `app/templates/labels/*.html`, labels/POS tests.  
**Permission impact:** Existing promotion/label capabilities remain unchanged.  
**Data impact:** None.  
**UI impact:** Label and promotion workflow polish.  
**Docs impact:** Update label/promotion guides only if workflow text changes.  
**Acceptance criteria:** Staff understand which print page to use and promotion actions are clear.  
**Test cases:** Render tests for promotion and label pages.  
**Manual UI check:** Print preview pages and promotion create/edit.  
**Risk:** Print layout changes may affect physical labels.  
**Definition of done:** Pages remain printable/readable, tests pass, tracker updated.  
**Status:** Complete

## V7-007

**Task ID:** V7-007  
**Version:** V7  
**Epic:** Reports UX  
**Module:** Reports  
**Title:** Reports page readability polish  
**Business reason:** Owner/manager should read reports quickly without interpreting technical tables.  
**Technical scope:** Review reports index, daily sales, stock summary, low stock, expiry, stock movement, and staff sales pages for headings, filters, totals, empty states, and table density.  
**Files likely affected:** `app/templates/reports/*.html`, `app/reports/views.py`, reports tests.  
**Permission impact:** Reports capability remains unchanged.  
**Data impact:** None; no report calculation changes.  
**UI impact:** Report display polish only.  
**Docs impact:** Development log; report guide only if labels/definitions change.  
**Acceptance criteria:** Reports are easier to scan and existing totals remain unchanged.  
**Test cases:** Existing report tests plus render checks for empty/filter states.  
**Manual UI check:** All report pages desktop/mobile.  
**Risk:** Display changes may be mistaken for calculation changes.  
**Definition of done:** Report visuals improved without calculation changes, tests pass, tracker updated.  
**Status:** Complete

## V7-008

**Task ID:** V7-008  
**Version:** V7  
**Epic:** System UX  
**Module:** Audit/log/system pages  
**Title:** Audit/log/system pages polish  
**Business reason:** Troubleshooting and audit review should be understandable without Django Admin.  
**Technical scope:** Review audit log list, live logs, system health, users/roles/settings pages for readability and clear warning states.  
**Files likely affected:** `app/templates/audit/audit_log_list.html`, `app/templates/system_logs/*.html`, `app/templates/accounts/*.html`, `app/templates/core/*.html`, related tests.  
**Permission impact:** Audit/system/settings capabilities remain unchanged.  
**Data impact:** None.  
**UI impact:** Admin/support page polish.  
**Docs impact:** Development log; system guides only if operator instructions change.  
**Acceptance criteria:** Admin/support pages are readable and sensitive areas remain capability-gated.  
**Test cases:** Permission and render tests for audit/log/system/settings pages.  
**Manual UI check:** Owner/Manager access and denied-role checks.  
**Risk:** Exposing too much detail in logs or system pages.  
**Definition of done:** Visibility and readability verified, tests pass, tracker updated.  
**Status:** Complete

## V7-009

**Task ID:** V7-009  
**Version:** V7  
**Epic:** UX States  
**Module:** Dashboard error/empty states  
**Title:** Empty/error/access-denied states polish  
**Business reason:** Staff need clear next steps when a page has no data or access is denied.  
**Technical scope:** Review dashboard error template, empty table states, form validation messages, 403/404/500 pages, and no-role behavior.  
**Files likely affected:** `app/templates/dashboard/error.html`, affected templates, `app/core/views.py`, tests.  
**Permission impact:** No permission rule changes; messaging only.  
**Data impact:** None.  
**UI impact:** Empty/error/access-denied copy and layout.  
**Docs impact:** Development log.  
**Acceptance criteria:** Empty and error states explain what happened and safe next action.  
**Test cases:** Error handler/no-role/access denied tests where available.  
**Manual UI check:** Trigger no-role/403 and representative empty list pages.  
**Risk:** Error copy can reveal too much technical information.  
**Definition of done:** States are helpful without leaking secrets, tests pass, tracker updated.  
**Status:** Complete

## V7-010

**Task ID:** V7-010  
**Version:** V7  
**Epic:** Mobile UX  
**Module:** Dashboard responsive behavior  
**Title:** Mobile/tablet usability pass  
**Business reason:** Staff may use phones or tablets for scanning, stock work, and review.  
**Technical scope:** Review responsive layout, mobile nav, table overflow, scanner modal, forms, POS, inventory, product list, and reports.  
**Files likely affected:** `app/core/static/core/css/dashboard.css`, `app/core/static/core/js/nav.js`, `app/core/static/core/js/scanner.js`, affected templates, view tests.  
**Permission impact:** None.  
**Data impact:** None.  
**UI impact:** Responsive layout polish.  
**Docs impact:** Development log; testing notes.  
**Acceptance criteria:** Core workflows are usable at phone/tablet widths.  
**Test cases:** Render tests where relevant; no app logic tests unless JS/form behavior changes.  
**Manual UI check:** Phone/tablet viewport checks for dashboard, POS, products, stock-in, inventory, batch upload.  
**Risk:** Mobile fixes can degrade desktop layout.  
**Definition of done:** Mobile and desktop checks recorded, tracker updated.  
**Status:** Complete

## V7-011

**Task ID:** V7-011  
**Version:** V7  
**Epic:** Language/Wording  
**Module:** Dashboard i18n/copy  
**Title:** English/Khmer wording consistency review  
**Business reason:** Staff-facing words should be consistent and understandable in both languages.  
**Technical scope:** Review page titles, buttons, status labels, field help, errors, and translation coverage for V7-touched screens.  
**Files likely affected:** Templates, locale files, `app/locale/` if present, documentation if terminology is standardized.  
**Permission impact:** None.  
**Data impact:** None.  
**UI impact:** Copy/translation polish.  
**Docs impact:** Development log; glossary note if needed.  
**Acceptance criteria:** Common labels are consistent and no obvious untranslated staff-facing text remains on touched screens.  
**Test cases:** Template render tests if translation-sensitive behavior exists.  
**Manual UI check:** Toggle English/Khmer on key pages.  
**Risk:** Wording changes can alter business meaning.  
**Definition of done:** Wording reviewed by Sidolla or assigned reviewer, tracker updated.  
**Status:** Complete

## V7-012

**Task ID:** V7-012  
**Version:** V7  
**Epic:** Release  
**Module:** QA/release  
**Title:** V7 QA and release preparation  
**Business reason:** V7 should ship only after staff workflow polish is verified.  
**Technical scope:** Run the V7 QA checklist, finalize release notes, update tracker and development log.  
**Files likely affected:** `docs/versions/v7/V7_QA_CHECKLIST.md`, `docs/versions/v7/V7_RELEASE_NOTE.md`, `docs/versions/VERSION_COMPLETION_TRACKER.md`, `docs/DEVELOPMENT_LOG.md`.  
**Permission impact:** Verify only.  
**Data impact:** None.  
**UI impact:** Verify only.  
**Docs impact:** Finalize V7 docs.  
**Acceptance criteria:** All approved tasks complete/deferred with evidence; tests and manual checks recorded.  
**Test cases:** Full or targeted suite based on implemented scope.  
**Manual UI check:** Final desktop/mobile pass.  
**Risk:** Releasing without clear acceptance leaves ambiguous incomplete work.  
**Definition of done:** V7 release note finalized and tracker marked complete.  
**Status:** Complete
