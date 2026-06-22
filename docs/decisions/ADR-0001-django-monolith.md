# ADR-0001: Django Monolith

Status: Accepted
Date: 2026-06-16

## Context

Melodu POS needs reliable retail workflows, clear deployment, simple operations, and fast development. The current system already uses a Django monolith with PostgreSQL, Django templates, Gunicorn, Docker Compose, and host Nginx.

## Decision

Melodu POS will continue as a Django monolith for the current product cycle.

Daily business interfaces will be built with Django views/templates and shared static assets. Django Admin remains available for raw back-office inspection and emergency maintenance, but the dashboard is the preferred daily interface.

## Consequences

| Consequence | Status |
| --- | --- |
| Simpler deployment and debugging for the VPS environment. | Current |
| Business rules can stay close to Django ORM transactions. | Current |
| No SPA/Next.js/Node.js service is introduced by default. | Current |
| Large frontend interaction changes must still fit Django templates and vanilla JS unless a new ADR changes direction. | Current |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Separate SPA frontend | Future / Proposed only; not justified for the current store workflow. |
| Microservices | Outdated for current scale; would add operational overhead. |
| Native mobile app | Future / Proposed only; browser dashboard remains current path. |

## Review Trigger

Review this ADR if the product needs offline POS, multi-store scale, real-time background processing, or a separate public customer application.
