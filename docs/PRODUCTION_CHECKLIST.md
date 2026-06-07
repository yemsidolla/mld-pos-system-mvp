# Production Checklist

## Environment

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY` is strong and unique.
- `POSTGRES_PASSWORD` is strong and unique.
- `DJANGO_ALLOWED_HOSTS` contains the real domain.
- `DJANGO_CSRF_TRUSTED_ORIGINS` contains the HTTPS origin.
- `DJANGO_SESSION_COOKIE_SECURE=True` when HTTPS is enabled.
- `DJANGO_CSRF_COOKIE_SECURE=True` when HTTPS is enabled.
- `TIME_ZONE=Asia/Phnom_Penh`

## Before First Launch

- Run `docker compose -f docker-compose.prod.yml up -d --build`.
- Run migrations.
- Run `collectstatic`.
- Create or confirm the first superuser.
- Run `setup_roles --admin-username admin`.
- Confirm `/health/` returns database `ok`.
- Confirm `/admin/` loads behind the domain.
- Confirm `data/postgres`, `data/media`, `data/static`, and `data/logs` persist on the VPS disk.

## Operations

- Run database backups daily.
- Run media backups weekly.
- Test restore commands on a non-production copy before relying on them.
- Monitor `/dashboard/system-health/`.
- Keep cashier users out of Django Admin by assigning only the `Cashier` group.
