# Multi-stage: compile Melodu Tailwind CSS with the standalone CLI, then ship a
# Python-only runtime image (no Node).

# ---- Stage 1: Tailwind standalone CLI (pinned) ----------------------------
FROM debian:bookworm-slim AS tailwind

ARG TAILWIND_VERSION=4.3.3
# Docker BuildKit sets TARGETARCH (amd64|arm64).
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) TW_ARCH=linux-x64 ;; \
      arm64) TW_ARCH=linux-arm64 ;; \
      *) echo "Unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fsSL \
      "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/tailwindcss-${TW_ARCH}" \
      -o /usr/local/bin/tailwindcss; \
    curl -fsSL \
      "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/sha256sums.txt" \
      -o /tmp/sha256sums.txt; \
    EXPECTED="$(awk -v f="./tailwindcss-${TW_ARCH}" '$2 == f { print $1; exit }' /tmp/sha256sums.txt)"; \
    echo "${EXPECTED}  /usr/local/bin/tailwindcss" | sha256sum -c -; \
    chmod +x /usr/local/bin/tailwindcss; \
    tailwindcss --help >/dev/null

WORKDIR /build
COPY tailwind/input.css tailwind/input.css
COPY app/templates app/templates
RUN mkdir -p app/core/static/core/css \
    && tailwindcss \
         -i tailwind/input.css \
         -o app/core/static/core/css/tailwind.css \
         --minify

# ---- Stage 2: Django runtime (no Node) ------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gettext libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app /app
COPY --from=tailwind /build/app/core/static/core/css/tailwind.css \
     /app/core/static/core/css/tailwind.css

RUN python manage.py compilemessages

EXPOSE 8000

CMD ["gunicorn", "melodu_pos.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
