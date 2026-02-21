# API Coverage (App-by-App)

## accounts
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`

## rbac (superuser/admin)
- `GET/POST /api/rbac/roles/`
- `GET/PATCH/DELETE /api/rbac/roles/{id}/`
- `GET/POST /api/rbac/user-roles/`
- `GET/PATCH/DELETE /api/rbac/user-roles/{id}/`

## cases
- CRUD: `/api/cases/cases/`
- `POST /api/cases/cases/submit_complaint/`
- `POST /api/cases/cases/submit_scene_report/`
- `POST /api/cases/cases/{id}/approve_scene/`
- `POST /api/cases/cases/{id}/intern_review/`
- `POST /api/cases/cases/{id}/officer_review/`
- `POST /api/cases/cases/{id}/assign_detective/`
- `POST /api/cases/cases/{id}/send_to_court/`
- CRUD: `/api/cases/complaint-submissions/`
- CRUD: `/api/cases/case-complainants/`
- CRUD: `/api/cases/case-witnesses/`

## evidence
- CRUD: `/api/evidence/witness/`
- CRUD: `/api/evidence/biological/`
- CRUD: `/api/evidence/vehicle/`
- CRUD: `/api/evidence/identification/`
- CRUD: `/api/evidence/other/`

## investigation
- CRUD: `/api/investigation/boards/`
- CRUD: `/api/investigation/board-nodes/`
- CRUD: `/api/investigation/board-edges/`
- CRUD: `/api/investigation/suspects/`
- `POST /api/investigation/suspects/{id}/arrest/`
- CRUD: `/api/investigation/interrogations/`
- `POST /api/investigation/interrogations/{id}/captain_decision/`
- `POST /api/investigation/interrogations/{id}/chief_review/`
- CRUD: `/api/investigation/notifications/`
- `POST /api/investigation/notifications/{id}/mark_read/`
- `GET /api/investigation/high-alert/`

## judiciary
- CRUD: `/api/judiciary/court-sessions/`

## rewards
- CRUD: `/api/rewards/tips/`
- `POST /api/rewards/tips/{id}/officer_review/`
- `POST /api/rewards/tips/{id}/detective_review/`
- Read: `/api/rewards/reward-claims/`
- `POST /api/rewards/reward-claims/verify/`

## payments
- CRUD: `/api/payments/bail/`
- `POST /api/payments/bail/{id}/callback/`
- `GET /api/payments/return/`

## dashboard
- `GET /api/dashboard/stats/`
- `GET /api/dashboard/modules/`
