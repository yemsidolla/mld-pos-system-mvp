# Deployment Guide

## Local Development Setup

1. Copy `.env.example` to `.env`.
2. Set `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, and `DJANGO_ALLOWED_HOSTS`.
3. Build, migrate, then start. Use the local override when you want the app
   reachable from your browser or phone at port 8000:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml build
docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

4. Collect static files:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py collectstatic --noinput
```

5. Create or reset the development admin user:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py setup_roles --admin-username admin --password Admin123
```

6. Open Django Admin:

```text
http://localhost:8000/admin/
```

## VPS Production Setup

1. Install Docker and Docker Compose on the VPS.
2. Copy the project folder to the VPS.
3. Copy `.env.example` to `.env`.
4. Set production values in `.env`.
5. Point the domain DNS record to the VPS IP.
6. Build the new image, migrate the database, then start serving new code.
   Additive nullable migrations (such as `Product.image_thumb`) are backward
   compatible with the previously running containers, so migrating first is
   safe. Serving new code before migrate is not: the new code selects columns
   the old database does not have yet, and every Product query fails until
   migrate finishes — taking the till down for any cashier scanning in that
   window. Do not reorder these steps.

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate
docker compose -f docker-compose.prod.yml up -d
```

7. Collect static files:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

8. Restart Django so the running process reads the latest static manifest:

```bash
docker compose -f docker-compose.prod.yml restart web
```

9. Create the first superuser:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

10. Create roles and assign the admin account:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py setup_roles --admin-username admin
```

For additional users, see `docs/guides/USER_MANAGEMENT_GUIDE.md`. The short version:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME admin --django-admin
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME cashier
```

11. Confirm health:

```bash
curl -fsS http://your-domain.example/health/
```

12. Enable HTTPS before using camera scanning on phones or tablets. Browser camera access works on `localhost` during development, but production device camera access requires HTTPS.

## VPS With External Nginx

Use this mode when Nginx is installed on the VPS host and Docker should run only PostgreSQL and Django.

1. Set `.env` for the real HTTPS domain:

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=melodu-pos.khlovepet.com,localhost,127.0.0.1,web
DJANGO_CSRF_TRUSTED_ORIGINS=https://melodu-pos.khlovepet.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
WEB_HOST_PORT=8001
```

2. Build, migrate, then start. Same migrate-before-serve rule as VPS Production
   Setup step 6 — additive migrations are safe with old code; new code against an
   unmigrated database is not.

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate
docker compose -f docker-compose.prod.yml up -d
```

3. Collect static files and restart so Gunicorn reads the latest static manifest:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml restart web
```

4. Point host Nginx to the Django port. In this mode, Nginx is only a reverse proxy. Django/Gunicorn serves collected static files through WhiteNoise.

```nginx
server {
    listen 443 ssl http2;
    server_name melodu-pos.khlovepet.com;

    ssl_certificate     /etc/letsencrypt/live/khlovepet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/khlovepet.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

5. Reload host Nginx:

```bash
nginx -t
systemctl reload nginx
```

There is intentionally no Docker `nginx` service. Host Nginx proxies to Gunicorn/Django, and WhiteNoise serves collected static files from Django.

## Garage Media Storage

Use Garage when uploaded/generated media should live outside the Django web
container filesystem. Static files still use WhiteNoise.

Production today runs with local filesystem media (`USE_S3_MEDIA=False`, files
under `data/media`). Cutover to Garage is:

```
local filesystem media (USE_S3_MEDIA=False)  →  Garage (USE_S3_MEDIA=True)
```

### Cutover order

1. Back up the database and local media:

```bash
scripts/backup_db.sh
scripts/backup_media.sh
```

2. Start or restart production compose, then bootstrap layout/bucket/key once:

> If this cutover also brings in new application code, apply any pending
> migrations **before** serving it — see the migrate-before-serve sequence
> earlier in this guide. Serving new code against an unmigrated database takes
> the till down.

```bash
docker compose -f docker-compose.prod.yml up -d --build
COMPOSE_FILE=docker-compose.prod.yml scripts/bootstrap_garage.sh
```

3. Upload local media into the Garage bucket (keys = paths relative to
   `data/media`):

```bash
GARAGE_ENDPOINT_URL=http://127.0.0.1:3900 \
S3_ACCESS_KEY_ID=... \
S3_SECRET_ACCESS_KEY=... \
S3_STORAGE_BUCKET_NAME=melodu-media \
MEDIA_ROOT=data/media \
scripts/migrate_media_to_garage.sh
```

4. Verify the script reports matching counts and bytes. **Do not proceed on
   failure.** An empty source exits non-zero.

5. Set production media storage values in `.env`:

```env
USE_S3_MEDIA=True
GARAGE_RPC_SECRET=replace-with-64-hex-from-openssl-rand-hex-32
S3_STORAGE_BUCKET_NAME=melodu-media
S3_ACCESS_KEY_ID=melodu_garage
S3_SECRET_ACCESS_KEY=replace-with-strong-password
S3_ENDPOINT_URL=https://melodu-media.khlovepet.com
S3_REGION_NAME=us-east-1
S3_QUERYSTRING_AUTH=True
S3_QUERYSTRING_EXPIRE=3600
```

6. Proxy the Garage S3 API through host Nginx so browser and phone media URLs are
   reachable over HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name melodu-media.khlovepet.com;

    ssl_certificate     /etc/letsencrypt/live/khlovepet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/khlovepet.com/privkey.pem;

    client_max_body_size 100m;

    location / {
        proxy_pass http://127.0.0.1:3900;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

7. Reload Nginx, restart Django, and verify images render (catalog list, product
   form, receipt, label with logo, KHQR on the POS page):

```bash
nginx -t
systemctl reload nginx
docker compose -f docker-compose.prod.yml restart web
```

8. Leave `data/media` in place — do not delete it.

### Rollback

Set `USE_S3_MEDIA=False` and restart web. Local files under `data/media` are
untouched, so rollback is near-instant.

See `docs/guides/GARAGE_STORAGE_GUIDE.md` for backup, restore, cutover detail,
and bootstrap notes.

## Backup

Database backup:

```bash
scripts/backup_db.sh
```

Media backup:

```bash
scripts/backup_media.sh
```

Garage backup when `USE_S3_MEDIA=True` (Garage must be stopped for consistency):

```bash
GARAGE_BACKUP_STOP=yes scripts/backup_garage.sh
```

## Restore

Database restore:

```bash
CONFIRM_RESTORE=yes scripts/restore_db.sh backups/melodu_pos_db_YYYYMMDD_HHMMSS.sql
```

Media restore:

```bash
CONFIRM_RESTORE=yes scripts/restore_media.sh backups/melodu_pos_media_YYYYMMDD_HHMMSS.tar.gz
```

Garage restore (stop Garage first; existing `data/garage` is moved aside):

```bash
docker compose -f docker-compose.prod.yml stop garage
CONFIRM_RESTORE=yes scripts/restore_garage.sh backups/melodu_pos_garage_YYYYMMDD_HHMMSS.tar.gz
docker compose -f docker-compose.prod.yml start garage
```

Expired stock maintenance:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py expire_batches --username admin --dry-run
docker compose -f docker-compose.prod.yml exec web python manage.py expire_batches --username admin
```

## Product image backfill

After deploying the `Product.image_thumb` migration, existing catalogue photos
can be rewritten with:

```bash
docker compose -f docker-compose.prod.yml exec web \
  python manage.py backfill_product_images
docker compose -f docker-compose.prod.yml exec web \
  python manage.py backfill_product_images --apply --confirm
```

Default mode is dry-run. Writing requires `--apply --confirm` and is
irreversible for every image that succeeds. Barcode, QR, KHQR, and logo files
are never touched.

**Quiesce product create/edit while the backfill runs.** A concurrent
non-image product edit can still write back a stale image filename: the form
reads image A, blocks on the backfill row lock, then saves all fields including
stale A after backfill committed B and deleted A. Cashiers on POS are
unaffected; only catalogue product forms need to be idle for the run.

## Production Checklist

- Use a strong `DJANGO_SECRET_KEY`.
- Use a strong `POSTGRES_PASSWORD`.
- Set `DJANGO_DEBUG=False`.
- Set `DJANGO_ALLOWED_HOSTS` to the real domain.
- Set `DJANGO_SECURE_SSL_REDIRECT=True` after HTTPS is working.
- Set `DJANGO_SECURE_HSTS_SECONDS=31536000` only after confirming the domain is HTTPS-only.
- Set HSTS subdomain and preload flags only after confirming all covered names are HTTPS-only.
- Set secure cookie options to `True` when HTTPS is enabled.
- Use HTTPS for camera-based barcode/QR scanning.
- Confirm `data/postgres`, `data/media`, `data/static`, and `data/logs` are backed up.
- If Garage is enabled, confirm `data/garage` is backed up.
- Rehearse restore monthly on a non-production copy.
