# V6 Technical Requirements

Status: Implemented (documentation)
Last updated: 2026-06-17

Version theme: **Foundation Reset & Access Control**

## Technical Scope

V6 TRD is documentation-only. No application code changes.

## As-Built References

| Area | Source |
| --- | --- |
| Auth modes | `app/melodu_pos/settings.py`, `app/accounts/oidc.py` |
| Capabilities | `app/core/capabilities.py`, `app/core/permissions.py` |
| OIDC architecture | `docs/versions/v6/V6_AUTHENTIK_AUTH_ARCHITECTURE.md` |
| Deployment | `docs/guides/DEPLOYMENT_GUIDE.md`, `docker-compose.authentik.yml` |
| System map | `docs/product/00_CURRENT_SYSTEM_MAP.md` |

## Auth As-Built

| Setting | Behavior | Status |
| --- | --- | --- |
| `AUTH_MODE=local` | Django username/password | Implemented |
| `AUTH_MODE=oidc` | Authentik/OIDC primary | Implemented |
| `LOCAL_LOGIN_ENABLED` | Emergency local login when OIDC | Implemented |
| OIDC auto-create | Configurable user creation | Implemented |
| Group sync | Authentik groups → Melodu roles | Implemented |
| Local users | Required for audit, StaffProfile, attribution | Implemented |

## Deliverables

- Product foundation docs `docs/product/00`–`11`
- Version planning docs V6–V10
- ADRs under `docs/decisions/`
- README and CURRENT_STATUS links updated

## Out Of Scope

Code changes, migrations, template/CSS changes, permission logic changes.
