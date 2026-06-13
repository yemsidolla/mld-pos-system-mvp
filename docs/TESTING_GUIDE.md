# Testing Guide

Run tests from the Django app directory:

```bash
cd app
python manage.py test
```

Run tests in Docker after the web image is built:

```bash
docker compose run --rm web python manage.py test
```

Run the batch upload tests specifically:

```bash
docker compose run --rm -v "$PWD/app:/app" web python manage.py test batch_upload
```

Run Django system checks:

```bash
cd app
python manage.py check
```

Current critical coverage includes barcode parsing, stock deduction, sale cancellation, inventory movement, audit logging, permissions, secret-safe logging, CSV/XLSX batch upload parsing, preview staging, row edit/delete, update-or-create commits, and stock-in upload through the existing receiving service.

Dashboard UX checks:

```bash
docker compose run --rm web python manage.py test core
docker compose run --rm web python manage.py collectstatic --noinput
```

After major UI changes, verify these pages in a browser at desktop and mobile sizes:

- `/dashboard/`
- `/dashboard/pos/`
- `/dashboard/inventory/`
- `/dashboard/batch-upload/`

Also open the scanner modal from POS and confirm camera, upload image, and manual fallback controls are visible. Production camera testing requires HTTPS. On a phone, test a real EAN-13 barcode, a generated Code128 Melodu label, and a QR label; for upload decode, use a close, sharp, bright image where the full code is straight and fills most of the image.
