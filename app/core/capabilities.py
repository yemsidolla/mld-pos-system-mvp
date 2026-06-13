"""Canonical capability registry (Authz Phase 1).

A capability is a permission "verb" the dashboard enforces. Roles grant
capabilities (stored as data on ``accounts.Role``); the ``can_*`` functions in
``core.permissions`` resolve to a capability via ``has_capability``.

Add a capability here, grant it to roles, then gate it with a ``can_*`` helper.
The keys are stable identifiers — do not rename one without a data migration.
"""

# (group label, [(key, human label), ...]) — drives the registry and the
# Phase 2 role-matrix editor UI.
CAPABILITY_GROUPS = [
    (
        "POS & sales",
        [
            ("pos.access", "Use the POS screen and create sales"),
            ("pos.override_below_cost", "Approve a below-cost sale"),
            ("sales.view_history", "View sales history"),
            ("sales.cancel", "Cancel a completed sale"),
            ("sales.reprint", "Reprint a receipt"),
        ],
    ),
    (
        "Catalog & inventory",
        [
            ("catalog.manage", "Manage products, categories, brands, suppliers"),
            ("promotions.manage", "Manage promotions"),
            ("inventory.manage", "Receive and manage stock, print labels"),
        ],
    ),
    (
        "Reports",
        [
            ("reports.view", "View and export reports"),
        ],
    ),
    (
        "System",
        [
            ("system.manage_users", "Manage users and role assignments"),
            ("system.manage_settings", "Manage store settings"),
            ("system.view_audit", "View audit logs"),
            ("system.view_logs", "View system health and live logs"),
            ("system.reset_data", "Reset or clear business data"),
        ],
    ),
]

ALL_CAPABILITIES = [key for _group, items in CAPABILITY_GROUPS for key, _label in items]
CAPABILITY_LABELS = {key: label for _group, items in CAPABILITY_GROUPS for key, label in items}

# Built-in roles seeded to reproduce the pre-Phase-1 hardcoded matrix exactly.
# OWNER is the all-powerful tier (is_owner=True) and implicitly holds every
# capability — present and future — so it is never listed explicitly.
BUILTIN_ROLES = [
    # slug, name, rank, is_owner, capabilities
    ("OWNER", "Owner", 10, True, []),
    (
        "MANAGER",
        "Manager",
        20,
        False,
        [
            "pos.access",
            "pos.override_below_cost",
            "sales.view_history",
            "sales.cancel",
            "sales.reprint",
            "catalog.manage",
            "promotions.manage",
            "inventory.manage",
            "reports.view",
            "system.manage_users",
            "system.manage_settings",
            "system.view_audit",
            "system.view_logs",
        ],
    ),
    ("INVENTORY", "Inventory staff", 30, False, ["inventory.manage"]),
    ("CASHIER", "Cashier", 40, False, ["pos.access"]),
    ("VIEWER", "Viewer / Auditor", 50, False, ["sales.view_history", "reports.view"]),
]
