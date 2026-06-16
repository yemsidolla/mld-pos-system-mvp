# MinIO Media Storage Guide

Melodu can store uploaded and generated media in MinIO using Django's
S3-compatible storage backend. Static files still use WhiteNoise; MinIO is only
for media such as product photos, store logos, KHQR images, barcode images, and
QR images.

## When To Enable

Enable MinIO when production image/media transfer through local filesystem media
is becoming unreliable or too large for the web container workflow.

```env
USE_S3_MEDIA=True
```

Leave it disabled for simple local development:

```env
USE_S3_MEDIA=False
```

## Required Environment

```env
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

For Docker-internal local testing, `S3_ENDPOINT_URL=http://minio:9000` works for
Django, but phones and external browsers cannot load that internal hostname.
Production should use an HTTPS endpoint that the browser can reach.

## Docker Services

`docker-compose.yml` and `docker-compose.prod.yml` include:

- `minio`: object storage server.
- `minio-init`: creates the configured bucket if it does not exist.
- `web`: Django, configured to use MinIO when `USE_S3_MEDIA=True`.

Production binds MinIO only to localhost:

```text
127.0.0.1:${MINIO_API_HOST_PORT:-9000}:9000
127.0.0.1:${MINIO_CONSOLE_HOST_PORT:-9001}:9001
```

Expose MinIO through host Nginx and HTTPS. Do not expose the raw MinIO ports
directly to the public internet.

## Host Nginx Example

Use a dedicated media subdomain:

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

Then set:

```env
S3_ENDPOINT_URL=https://melodu-media.khlovepet.com
S3_CUSTOM_DOMAIN=
```

This keeps generated media URLs reachable from desktop and phone browsers.

## Existing Media Migration

After enabling MinIO, new uploads go to MinIO. Existing files under
`data/media` stay on disk until migrated. A simple migration path is:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

Then copy existing files through Django storage in a controlled maintenance
script or one-off shell session. Keep a backup of `data/media` before migration.

## Backup

MinIO data is stored in `data/minio` by default. Back it up together with the
database:

```bash
MINIO_SOURCE=data/minio scripts/backup_minio.sh
```

Restore only into an intentionally replaceable environment:

```bash
CONFIRM_RESTORE=yes scripts/restore_minio.sh backups/melodu_pos_minio_YYYYMMDD_HHMMSS.tar.gz
```

## Operational Notes

- Keep `S3_QUERYSTRING_AUTH=True` so media URLs are temporary signed URLs.
- Use HTTPS for production media endpoints.
- Rotate MinIO credentials if they are ever exposed.
- Keep PostgreSQL backups and MinIO backups together; product records reference
  object keys stored in MinIO.
