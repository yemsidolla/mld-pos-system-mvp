# Dev Auth Bypass

A **local-development-only** switch that authenticates every request as a dev
user, so you can browse the dashboard without logging in (useful for UX passes
and automated browsing).

## It cannot run in production or SIT

`settings.py` refuses to start if `DEV_AUTH_BYPASS=True` while:

- `DJANGO_DEBUG` is false (production and SIT run `DEBUG=False`), **or**
- any `*.khlovepet.com` / `*.khapper.com` host is in `DJANGO_ALLOWED_HOSTS`.

A misconfiguration crashes the boot rather than silently opening the door. The
middleware also self-disables (`MiddlewareNotUsed`) unless both flags are set.
Guard behaviour is covered by `core.tests.DevAuthBypassGuardTests`.

## Turn it on (local only)

In a local `.env` (never a prod/SIT one):

```ini
DJANGO_DEBUG=True
DEV_AUTH_BYPASS=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,web
# optional — defaults to the first active superuser:
DEV_AUTH_BYPASS_USER=devadmin
```

Then rebuild/restart the local stack. Every request is now the dev user.

## Turn it off

Remove `DEV_AUTH_BYPASS` (or set it false). Login returns to normal.
