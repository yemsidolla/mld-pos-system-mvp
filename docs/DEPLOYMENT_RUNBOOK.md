# Melodu POS Deployment Runbook

Date: 2026-06-09

## Deployment Shape

Docker services:

```text
postgres
web
```

There is intentionally no internal Docker Nginx service. Production HTTPS and reverse proxy are handled by Nginx installed on the host. Django/Gunicorn serves the app, and WhiteNoise serves collected static assets.

## Local Development And iPhone Testing

Use the local override:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py setup_roles --admin-username admin --password Admin123
```

Open:

```text
Mac: http://127.0.0.1:8000/dashboard/
iPhone: http://192.168.1.199:8000/dashboard/
```

Local credentials:

```text
Username: admin
Password: Admin123
```

Camera note:

- Manual POS/scanner entry can work over local LAN HTTP.
- iPhone camera scanning usually requires HTTPS, except localhost-style development contexts.

## Local Verification

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml config --services
docker compose -f docker-compose.yml -f docker-compose.local.yml ps
curl http://127.0.0.1:8000/health/
curl -I http://192.168.1.199:8000/health/
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py test
```

Expected services:

```text
postgres
web
```

## Production Environment

Required production environment values:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<strong unique value>
DJANGO_ALLOWED_HOSTS=<production-domain>,localhost,127.0.0.1,web
DJANGO_CSRF_TRUSTED_ORIGINS=https://<production-domain>
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
POSTGRES_DB=<database>
POSTGRES_USER=<database-user>
POSTGRES_PASSWORD=<strong unique value>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
TIME_ZONE=Asia/Phnom_Penh
WEB_HOST_PORT=8001
```

## Production Deploy

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml exec web python manage.py setup_roles --admin-username admin
```

Do not set the production admin password to the local development password.

After `collectstatic`, restart `web` so the running Django process reads the latest static manifest:

```bash
docker compose -f docker-compose.prod.yml restart web
```

## Host Nginx

Nginx should be installed on the host and proxy to Django/Gunicorn:

```nginx
server {
    server_name melodu-pos.khlovepet.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Reload host Nginx:

```bash
nginx -t
systemctl reload nginx
```

## Production Verification

```bash
docker compose -f docker-compose.prod.yml config --services
docker compose -f docker-compose.prod.yml ps
curl https://melodu-pos.khlovepet.com/health/
```

Check:

- `/dashboard/` loads.
- `/admin/` loads for trusted admin users.
- Static assets load.
- Pages reference the latest collected static asset hashes after `web` restart.
- Product images/media load.
- POS sale can be completed.
- Stock-in can create a batch.
- System health reports database `ok`.
- Camera scanner works over HTTPS or manual fallback works.

## Backup

Database backup:

```bash
scripts/backup_db.sh
```

Media backup:

```bash
scripts/backup_media.sh
```

Operational policy:

- Database backups: daily.
- Media backups: weekly or before large catalog/image changes.
- Restore rehearsal: non-production copy before relying on backups.

## Restore Rehearsal

Run restore only on a non-production copy unless an owner has approved production recovery. Restore scripts require `CONFIRM_RESTORE=yes`.

```bash
CONFIRM_RESTORE=yes scripts/restore_db.sh <backup-file>
CONFIRM_RESTORE=yes scripts/restore_media.sh <media-backup-file>
```

After restore:

- Run `/health/`.
- Log into `/dashboard/`.
- Check product catalog.
- Check inventory batches.
- Check recent sales.
- Check media files.
- Run the Django test suite if the environment is a test/staging copy.

## Expired Stock Maintenance

Run a dry run first:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py expire_batches --username admin --dry-run
```

Then run the maintenance command:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py expire_batches --username admin
```

The command uses the normal inventory service, so each affected batch gets an expired movement and audit log.

## Rollback Notes

- Keep the previous Docker image/tag or previous branch available before deploy.
- Keep a database backup from before deploy.
- Roll back app code first if schema did not change.
- If migrations are introduced in future V2 phases, define migration-specific rollback steps before deploying.
