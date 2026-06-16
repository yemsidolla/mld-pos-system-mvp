# Deployment Guide

## Local Development Setup

1. Copy `.env.example` to `.env`.
2. Set `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, and `DJANGO_ALLOWED_HOSTS`.
3. Start PostgreSQL and Django. Use the local override when you want the app reachable from your browser or phone at port 8000:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

4. Run migrations:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py migrate
```

5. Collect static files:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py collectstatic --noinput
```

6. Create or reset the development admin user:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py setup_roles --admin-username admin --password Admin123
```

7. Open Django Admin:

```text
http://localhost:8000/admin/
```

## VPS Production Setup

1. Install Docker and Docker Compose on the VPS.
2. Copy the project folder to the VPS.
3. Copy `.env.example` to `.env`.
4. Set production values in `.env`.
5. Point the domain DNS record to the VPS IP.
6. Start production services. Docker runs PostgreSQL and Django only; Nginx must run on the VPS host.

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

7. Run migrations:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

8. Collect static files:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

9. Restart Django so the running process reads the latest static manifest:

```bash
docker compose -f docker-compose.prod.yml restart web
```

10. Create the first superuser:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

11. Create roles and assign the admin account:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py setup_roles --admin-username admin
```

For additional users, see `docs/USER_MANAGEMENT_GUIDE.md`. The short version:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME admin --django-admin
docker compose -f docker-compose.prod.yml exec web python manage.py set_user_role USERNAME cashier
```

12. Confirm health:

```bash
curl -fsS http://your-domain.example/health/
```

13. Enable HTTPS before using camera scanning on phones or tablets. Browser camera access works on `localhost` during development, but production device camera access requires HTTPS.

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

2. Start PostgreSQL and Django:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

3. Run migrations and collect static files:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
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

## MinIO Media Storage

Use MinIO when uploaded/generated media should live outside the Django web
container filesystem. Static files still use WhiteNoise.

1. Set production media storage values:

```env
USE_S3_MEDIA=True
MINIO_ROOT_USER=melodu_minio
MINIO_ROOT_PASSWORD=replace-with-strong-password
S3_STORAGE_BUCKET_NAME=melodu-media
S3_ACCESS_KEY_ID=melodu_minio
S3_SECRET_ACCESS_KEY=replace-with-strong-password
S3_ENDPOINT_URL=https://melodu-media.khlovepet.com
S3_REGION_NAME=us-east-1
S3_QUERYSTRING_AUTH=True
S3_QUERYSTRING_EXPIRE=3600
```

2. Start or restart production compose. The `minio-init` service creates the
   bucket automatically.

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

3. Proxy the MinIO API through host Nginx so browser and phone media URLs are
   reachable over HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name melodu-media.khlovepet.com;

    ssl_certificate     /etc/letsencrypt/live/khlovepet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/khlovepet.com/privkey.pem;

    client_max_body_size 100m;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

4. Reload Nginx and restart Django:

```bash
nginx -t
systemctl reload nginx
docker compose -f docker-compose.prod.yml restart web
```

See `docs/MINIO_STORAGE_GUIDE.md` for backup, restore, and existing-media
migration notes.

## Backup

Database backup:

```bash
scripts/backup_db.sh
```

Media backup:

```bash
scripts/backup_media.sh
```

MinIO backup when `USE_S3_MEDIA=True`:

```bash
scripts/backup_minio.sh
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

Expired stock maintenance:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py expire_batches --username admin --dry-run
docker compose -f docker-compose.prod.yml exec web python manage.py expire_batches --username admin
```

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
- If MinIO is enabled, confirm `data/minio` is backed up.
- Rehearse restore monthly on a non-production copy.
