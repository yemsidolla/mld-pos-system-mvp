# ADR-0005: Label Template Strategy

Status: Accepted
Date: 2026-06-16

## Context

Melodu POS needs barcode/QR labels, product labels, shelf labels, and promotion labels. Store staff need browser-accessible print workflows without adding a separate print server or hardware-specific driver layer in the current phase.

## Decision

Melodu POS will use database-backed `LabelTemplate` records and browser-rendered print pages for labels.

Label printing should use stock batch/product/store data, respect template toggles and sizes, and create audit evidence for print actions where appropriate.

## Consequences

| Consequence | Status |
| --- | --- |
| Staff can adjust label templates through dashboard workflows. | Current |
| Browser print remains the supported output path. | Current |
| Stock batch barcode/QR assets can be reused across print flows. | Current |
| Physical printer output still requires device-specific verification. | Needs Verification |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Hard-code one label format | Outdated; too rigid for product/promotion/shelf needs. |
| Use ESC/POS or printer SDK now | Future / Proposed; adds device complexity not required yet. |
| Generate only PDFs | Future / Proposed; browser print is simpler for current workflows. |

## Review Trigger

Review this ADR if printer hardware certification requires a native print bridge, ESC/POS service, or server-generated PDF workflow.
