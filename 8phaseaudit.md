# NutriPlan Phase 1-8 Audit (Re-Verification)

Date: 2026-06-15
Audited against: `AGENTS.md`, `docs/technical_spec.md`, `docs/prd.md`, `docs/product_analysis.md`, `docs/implementation_plan.md`

## Re-Verification Run

- Backend tests: `python -m pytest -q` -> **96 passed**
- Frontend build: `npm run build` -> **success**
- Food seed count: `backend/seed/food_items.json` -> **205 items**

## Overall Verdict

The previously reported issues are now largely resolved.

- **Fixed:** 17/17

Phase 1-8 implementation quality has improved substantially and is now **complete** for MVP scope.

---

## Critical Issues Status

1. **Deploy workflow was broken**
   - **Status:** `FIXED`
   - **Evidence:** `.github/workflows/ci.yml`
   - `deploy` now exists in the same workflow and correctly uses:
     `needs: [lint-backend, lint-frontend, test-backend, build-frontend]`.

2. **Food database was far below MVP size**
   - **Status:** `FIXED`
   - **Evidence:** `backend/seed/food_items.json`
   - Current dataset count is **205** items (meets 200+ expectation).

3. **Outbound WhatsApp logging import path was broken**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/services/whatsapp_service.py`
   - Import now uses `from app.models.whatsapp_message import WhatsAppMessage`.

4. **Plan could be marked `delivered` even on failed/skipped sends**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/services/plan_service.py`
   - `approve_plan()` keeps status as `approved` on send skip/failure and only sets `delivered` after successful sends.

5. **WhatsApp send service was not tenant-aware**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/services/whatsapp_service.py`
   - `_resolve_credentials()` now resolves per-dietitian credentials first, with env fallback.

---

## High Issues Status

6. **Public URL contract differed from spec**
   - **Status:** `FIXED`
   - **Evidence:** `docs/technical_spec.md` §4.9, `frontend/src/App.tsx`, `backend/app/routers/public.py`, `backend/app/routers/p_pages.py`
   - Spec updated to document the implemented split: frontend SPA routes at `/p/*`, public JSON at `/api/v1/public/*`, and optional `POST /p/:slug/intake` alias.
   - Legacy `/d/*` redirects remain in the frontend.

7. **Landing page requirements were incomplete (intake + CTA)**
   - **Status:** `FIXED`
   - **Evidence:** `frontend/src/pages/public/DietitianLandingPage.tsx`, `backend/app/services/intake_service.py`, `backend/app/routers/public.py`
   - Intake form flow is implemented end-to-end and WhatsApp CTA links are present.

8. **Article editor was plain textarea**
   - **Status:** `FIXED`
   - **Evidence:** `frontend/src/pages/articles/ArticleEditorPage.tsx`
   - Rich editor component is now used (`RichTextEditor`).

9. **Profile setup/update API was incomplete**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/routers/v1/auth.py`
   - Added `PUT /auth/me` and `PUT /auth/me/whatsapp`.

10. **Spec-listed plan/food endpoints were missing**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/routers/v1/plans.py`, `backend/app/routers/v1/foods.py`
   - Includes plan validations and regenerate routes.
   - Includes food create/get/update routes.

---

## Medium Issues Status

11. **AI generation lacked strict schema validation + malformed JSON retry**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/ai/plan_generator.py`, `backend/app/ai/plan_schema.py`
   - Strict Pydantic schema validation added with retry flow.

12. **Grocery list was not quantity aggregated**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/whatsapp/message_formatter.py`
   - Output now aggregates totals (`portion_grams`) and handles count/portion aggregation.

13. **Structured logging missed request completion and duration**
   - **Status:** `FIXED`
   - **Evidence:** `backend/app/main.py`
   - Middleware now logs method/path + status + `duration_ms`.

14. **CI missed lint stage**
   - **Status:** `FIXED`
   - **Evidence:** `.github/workflows/ci.yml`
   - Added `lint-backend` and `lint-frontend` jobs.

15. **`docker-compose.yml` missed frontend service**
   - **Status:** `FIXED`
   - **Evidence:** `docker-compose.yml`
   - `frontend` service now included with dev command and port exposure.

16. **Task registry status was internally inconsistent**
   - **Status:** `FIXED`
   - **Evidence:** `docs/tasks.md`
   - Top summary and completed task list now align around completed audit-fix sprint.

17. **README still marked deployment pending**
   - **Status:** `FIXED`
   - **Evidence:** `README.md`
   - Deployment section now includes live URLs and CI/CD notes.

---

## Final Note

All items from the original audit list are resolved. Public routing contract is documented in `docs/technical_spec.md` §4.9 (SPA pages + versioned JSON APIs). Verified by tests/build.
