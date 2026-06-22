# User Management Guide

> **V4 update:** Melodu now has five dashboard roles managed from
> `/dashboard/users/` (Owner and Manager only). See
> `docs/reference/PERMISSION_MATRIX.md` for the full access matrix. The legacy
> `Admin`/`Cashier` Django groups still work (map and keep): superusers are
> always Owner, `Admin` maps to Manager, and `Cashier` maps to Cashier.

## V4 Roles

- **Owner** — full access, including Owner-only maintenance (data reset).
- **Manager** — all management except Owner-only maintenance.
- **Inventory staff** — stock-in, inventory, expiry, label printing.
- **Cashier** — POS sales and receipts only.
- **Viewer / Auditor** — read-only reports, sales history, audit.

## Manage Users In The Dashboard

Sign in as Owner or Manager and open **Users** in the sidebar
(`/dashboard/users/`) to create accounts, assign a role, reset a password, or
disable an account. Protections: only an Owner can assign the Owner role or edit
an Owner/superuser; you cannot change your own role or disable your own account;
at least one active Owner must always remain. Every change is written to the
audit log.

## Roles From The Command Line

`set_user_role` accepts `owner`, `manager`, `inventory`, `cashier`, `viewer`
(plus the legacy `admin` alias for Manager). It sets the `StaffProfile` role and
keeps the legacy group in sync.

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME inventory
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME manager --django-admin
```

`--django-admin` (Django Admin / `is_staff`) is allowed for Owner and Manager
roles only.

---

## Legacy Reference (still valid)

Django Admin access is separate from Melodu dashboard access. A user must have `is_staff=True` to log in to `/admin/`. Cashiers are always blocked from Django Admin, even if they are accidentally marked as staff.

Use `docker-compose.prod.yml` on the VPS. For local development, replace the compose flags below with `-f docker-compose.yml -f docker-compose.local.yml`.

## Create A Dashboard Admin

Create the user in Django Admin or with `createsuperuser`, then assign the role:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME admin
```

This user can log in to `/dashboard/`, but not `/admin/`.

## Create A Django Admin User

Use this only for owners or trusted managers who need raw Django Admin access:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME admin --django-admin
```

## Create A Cashier

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME cashier
```

The cashier can log in to `/dashboard/` and use POS. The cashier cannot access `/admin/`.

## Django Admin Checklist

When creating users manually at `/admin/auth/user/`:

- Set a usable password.
- Keep `Active` checked.
- Add exactly one Melodu group: `Admin` or `Cashier`.
- Check `Staff status` only for trusted Admin users who need `/admin/`.
- Do not check `Staff status` for Cashier users.
