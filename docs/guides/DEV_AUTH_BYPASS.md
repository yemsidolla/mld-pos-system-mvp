# Dev Auth Bypass

A **local-development-only** switch that authenticates every request as a dev
user, so you can browse the dashboard without logging in (useful for UX passes
and automated browsing).

## It cannot run in production or SIT

The gate is an **allowlist**: it activates only when `DJANGO_DEBUG=True` **and**
every entry in `DJANGO_ALLOWED_HOSTS` is a loopback host (`localhost`,
`127.0.0.1`, `::1`, `0.0.0.0`, `web`, `testserver`). Anything else refuses to
start:

- a real domain (production/SIT hosts), **or**
- a public IP, **or**
- a wildcard `*` (which would make Django accept every Host header), **or**
- `DEBUG=False`.

Case and a trailing dot are normalised, so `KHLOVEPET.COM` and
`melodu-pos.khlovepet.com.` are rejected too. The single gate function
`dev_auth_bypass_active` in `core/dev_auth.py` is called by both `settings.py`
and the tests, so it cannot be weakened without failing
`core.tests.DevAuthBypassGuardTests`. The middleware also self-disables
(`MiddlewareNotUsed`) unless the gate agrees.

A denylist of production domains was the original design and was unsafe —
`ALLOWED_HOSTS=['*']` passed it. Do not reintroduce one.

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
