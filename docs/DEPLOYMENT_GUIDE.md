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
