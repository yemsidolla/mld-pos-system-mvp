# Garage Media Storage Guide

Melodu can store uploaded and generated media in Garage using Django's
S3-compatible storage backend. Static files still use WhiteNoise; Garage is only
for media such as product photos, store logos, KHQR images, barcode images, and
QR images.

Pinned image: `dxflrs/garage:v2.3.0` (stable release verified on Docker Hub and
<https://garagehq.deuxfleurs.fr/_releases.html>).

## When To Enable

Enable Garage when production image/media transfer through local filesystem media
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
# Generate with: openssl rand -hex 32
GARAGE_RPC_SECRET=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
GARAGE_ADMIN_TOKEN=
GARAGE_S3_HOST_PORT=3900
S3_STORAGE_BUCKET_NAME=melodu-media
S3_ACCESS_KEY_ID=melodu_garage
S3_SECRET_ACCESS_KEY=replace-with-strong-password
S3_ENDPOINT_URL=https://melodu-media.khlovepet.com
S3_REGION_NAME=us-east-1
S3_QUERYSTRING_AUTH=True
S3_QUERYSTRING_EXPIRE=3600
```

Keep every `S3_*` variable name as-is — they are backend-neutral. Only the
endpoint and Garage-specific secrets change when switching backends.

For Docker-internal local testing, `S3_ENDPOINT_URL=http://garage:3900` works for
Django, but phones and external browsers cannot load that internal hostname.
Production should use an HTTPS endpoint that the browser can reach.

## Docker Services

`docker-compose.yml` and `docker-compose.prod.yml` include:

- `garage`: single-node S3-compatible object storage (`replication_factor = 1`).
- `web`: Django, configured to use Garage when `USE_S3_MEDIA=True`.

Config file: `docker/garage/garage.toml`.

- S3 API listens on `:3900` (reachable by the `web` service on the compose network).
- Admin API (`:3903`) and RPC (`:3901`) bind to `127.0.0.1` inside the container.
- Production publishes only the S3 API to host loopback:
  `127.0.0.1:${GARAGE_S3_HOST_PORT:-3900}:3900`.

Expose Garage S3 through host Nginx and HTTPS. Do not expose the raw S3 port
directly to the public internet. Do not publish admin or RPC ports.

## First-Run Bootstrap

Garage does not auto-create the layout, bucket, or key. After the first
`docker compose ... up -d`, run:

```bash
COMPOSE_FILE=docker-compose.yml:docker-compose.local.yml scripts/bootstrap_garage.sh
# production:
# COMPOSE_FILE=docker-compose.prod.yml scripts/bootstrap_garage.sh
```

The script is re-runnable. It performs:

1. `garage layout assign` (zone `dc1`, capacity `10G` by default)
2. `garage layout apply`
3. `garage bucket create` for `S3_STORAGE_BUCKET_NAME`
4. `garage key import` using `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY`
5. `garage bucket allow --read --write --owner`

Manual equivalent (via `docker compose exec garage /garage ...`):

```bash
docker compose exec garage /garage status
docker compose exec garage /garage layout assign -z dc1 -c 10G <node_id>
docker compose exec garage /garage layout apply --version 1
docker compose exec garage /garage bucket create melodu-media
docker compose exec garage /garage key import -n melodu-media-key --yes \
  "$S3_ACCESS_KEY_ID" "$S3_SECRET_ACCESS_KEY"
docker compose exec garage /garage bucket allow --read --write --owner \
  melodu-media --key melodu-media-key
```

Pass `GARAGE_RPC_SECRET` into `docker compose exec` (or rely on the service env)
so the CLI can talk to the node.

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
        proxy_pass http://127.0.0.1:3900;
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

## Migrating From MinIO

Object keys and the bucket name must stay identical so existing
`Product.image.name` values in PostgreSQL keep resolving.

1. Keep the MinIO volume (`data/minio`) — do not delete it; rollback depends on it.
2. Start Garage, run `scripts/bootstrap_garage.sh`.
3. Ensure the MinIO API is temporarily reachable, then copy objects:

```bash
MINIO_ENDPOINT_URL=http://127.0.0.1:9000 \
MINIO_ACCESS_KEY_ID=... \
MINIO_SECRET_ACCESS_KEY=... \
GARAGE_ENDPOINT_URL=http://127.0.0.1:3900 \
S3_ACCESS_KEY_ID=... \
S3_SECRET_ACCESS_KEY=... \
S3_STORAGE_BUCKET_NAME=melodu-media \
scripts/migrate_minio_to_garage.sh
```

The migrate script syncs keys unchanged, is safe to re-run, and verifies
object count + total bytes at the end.

Existing files under `data/media` (filesystem mode) are a separate concern —
migrate those deliberately only when switching from filesystem to S3.

## Backup

Garage data lives under `data/garage` (`meta/` + `data/`) by default. Back it up
together with the database:

```bash
GARAGE_SOURCE=data/garage scripts/backup_garage.sh
```

Restore only into an intentionally replaceable environment (stop Garage first):

```bash
CONFIRM_RESTORE=yes scripts/restore_garage.sh backups/melodu_pos_garage_YYYYMMDD_HHMMSS.tar.gz
```

## Operational Notes

- Keep `S3_QUERYSTRING_AUTH=True` so media URLs are temporary signed URLs.
- Use HTTPS for production media endpoints.
- Rotate Garage S3 credentials and `GARAGE_RPC_SECRET` if they are ever exposed.
- Keep PostgreSQL backups and Garage backups together; product records reference
  object keys stored in Garage.
- Single-node only (`replication_factor = 1`). Multi-node Garage is out of scope.
