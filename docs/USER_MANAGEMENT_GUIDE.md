# User Management Guide

Melodu uses Django users with two application roles:

- `Admin`: can access the Melodu dashboard management pages.
- `Cashier`: can access POS workflows only.

Django Admin access is separate from Melodu dashboard access. A user must have `is_staff=True` to log in to `/admin/`. Cashiers are always blocked from Django Admin, even if they are accidentally marked as staff.

## Create A Dashboard Admin

Create the user in Django Admin or with `createsuperuser`, then assign the role:

```bash
docker compose -f docker-compose.yml -f docker-compose.external-nginx.yml exec web python manage.py set_user_role USERNAME admin
```

This user can log in to `/dashboard/`, but not `/admin/`.

## Create A Django Admin User

Use this only for owners or trusted managers who need raw Django Admin access:

```bash
docker compose -f docker-compose.yml -f docker-compose.external-nginx.yml exec web python manage.py set_user_role USERNAME admin --django-admin
```

## Create A Cashier

```bash
docker compose -f docker-compose.yml -f docker-compose.external-nginx.yml exec web python manage.py set_user_role USERNAME cashier
```

The cashier can log in to `/dashboard/` and use POS. The cashier cannot access `/admin/`.

## Django Admin Checklist

When creating users manually at `/admin/auth/user/`:

- Set a usable password.
- Keep `Active` checked.
- Add exactly one Melodu group: `Admin` or `Cashier`.
- Check `Staff status` only for trusted Admin users who need `/admin/`.
- Do not check `Staff status` for Cashier users.

