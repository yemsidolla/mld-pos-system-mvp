# Codex Rules

1. Implement one phase at a time only after approval.
2. Inspect existing files before changing code.
3. Keep changes small and reviewable.
4. Do not implement future phases early.
5. Prefer simple Django solutions over complex architecture.
6. Keep business logic in service functions, not directly inside views.
7. Use database transactions for stock-in, sale, cancellation, and adjustment.
8. Validate all barcode and QR scan input.
9. Do not log passwords, tokens, secret keys, or sensitive credentials.
10. Audit logs must be read-only in normal admin.
11. Cashier must not access audit logs or backend logs.
12. Use timezone Asia/Phnom_Penh.
13. Use Decimal for money.
14. Never use float for price or amount.
15. Use migrations properly.
16. Keep README and docs/TASKS.md updated after each phase.
17. Do not claim a task is done if it was not tested.
