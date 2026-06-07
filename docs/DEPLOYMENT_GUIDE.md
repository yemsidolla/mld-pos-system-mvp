# Deployment Guide

## Local Development Setup

1. Copy `.env.example` to `.env`.
2. Set `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, and `DJANGO_ALLOWED_HOSTS`.
3. Start services:

```bash
docker compose up -d --build
```

4. Run migrations:

```bash
docker compose exec web python manage.py migrate
```

5. Collect static files:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

6. Create the first superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

7. Open Django Admin:

```text
http://localhost:8000/admin/
```

8. Create default roles and assign the development admin:

```bash
docker compose exec web python manage.py setup_roles --admin-username admin
```

## VPS Production Setup

1. Install Docker and Docker Compose on the VPS.
2. Copy the project folder to the VPS.
3. Copy `.env.example` to `.env`.
4. Set production values in `.env`.
5. Point the domain DNS record to the VPS IP.
6. Start production services:

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

9. Create the first superuser:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

10. Create roles and assign the admin account:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py setup_roles --admin-username admin
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
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
WEB_HOST_PORT=8001
```

2. Start PostgreSQL and Django with the external-Nginx override:

```bash
docker compose -f docker-compose.yml -f docker-compose.external-nginx.yml up -d --build postgres web
```

3. Run migrations and collect static files:

```bash
docker compose -f docker-compose.yml -f docker-compose.external-nginx.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.external-nginx.yml exec web python manage.py collectstatic --noinput
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

Do not run the Docker `nginx` service in this mode. If it was already started, stop it:

```bash
docker compose stop nginx
docker compose rm -f nginx
```

## Backup

Database backup:

```bash
scripts/backup_db.sh
```

Media backup:

```bash
scripts/backup_media.sh
```

## Restore

Database restore:

```bash
scripts/restore_db.sh backups/melodu_pos_db_YYYYMMDD_HHMMSS.sql
```

Media restore:

```bash
tar -xzf backups/melodu_pos_media_YYYYMMDD_HHMMSS.tar.gz
```

## Production Checklist

- Use a strong `DJANGO_SECRET_KEY`.
- Use a strong `POSTGRES_PASSWORD`.
- Set `DJANGO_DEBUG=False`.
- Set `DJANGO_ALLOWED_HOSTS` to the real domain.
- Set secure cookie options to `True` when HTTPS is enabled.
- Use HTTPS for camera-based barcode/QR scanning.
- Confirm `data/postgres`, `data/media`, `data/static`, and `data/logs` are backed up.
