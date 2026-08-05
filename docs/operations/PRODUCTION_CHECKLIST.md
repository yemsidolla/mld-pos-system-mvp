# Production Checklist

## Environment

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY` is strong and unique.
- `POSTGRES_PASSWORD` is strong and unique.
- If Garage is enabled, `GARAGE_RPC_SECRET` and `S3_SECRET_ACCESS_KEY` are strong and unique.
- If Garage is enabled, `S3_ENDPOINT_URL` is an HTTPS URL reachable by desktop and phone browsers.
- `DJANGO_ALLOWED_HOSTS` contains the real domain.
- `DJANGO_CSRF_TRUSTED_ORIGINS` contains the HTTPS origin.
- `DJANGO_SECURE_SSL_REDIRECT=True` after HTTPS is verified.
- `DJANGO_SECURE_HSTS_SECONDS=31536000` only after the domain is HTTPS-only.
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True` only after covered subdomains are HTTPS-only.
- `DJANGO_SECURE_HSTS_PRELOAD=True` only when the domain is ready for browser preload requirements.
- `DJANGO_SESSION_COOKIE_SECURE=True` when HTTPS is enabled.
- `DJANGO_CSRF_COOKIE_SECURE=True` when HTTPS is enabled.
- `TIME_ZONE=Asia/Phnom_Penh`

## Before First Launch

- Build, migrate, then start (migrate before serve):
  `docker compose -f docker-compose.prod.yml build`
  then `docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate`
  then `docker compose -f docker-compose.prod.yml up -d`.
- Run `collectstatic`.
- Create or confirm the first superuser.
- Run `setup_roles --admin-username admin`.
- Confirm `/health/` returns database `ok`.
- Confirm `/admin/` loads behind the domain.
- Confirm `data/postgres`, `data/media`, `data/static`, and `data/logs` persist on the VPS disk.
- If Garage is enabled, confirm `data/garage` persists on the VPS disk.
- If Garage is enabled, run `scripts/bootstrap_garage.sh` once after first start.

## Operations

- Run database backups daily.
- Run media backups weekly.
- If Garage is enabled, run Garage backups weekly.
- Test restore commands monthly on a non-production copy before relying on them.
- Run expired-batch maintenance daily with `expire_batches --username <maintenance-user>`.
- Monitor `/dashboard/system-health/`.
- Keep cashier users out of Django Admin by assigning only the `Cashier` group.
