# NutriPlan Deployment Readiness Audit

Date: 2026-07-06  
Scope: deployment readiness, UI/UX, security, architecture, functionality, edge cases, and resume/portfolio presentation.

## Verdict

NutriPlan is not ready for public deployment yet. It is close to being a strong resume demo, but a few issues would hurt both reliability and first impression if an interviewer or recruiter runs the repo.

Recommended target: fix all P0 items and the high-value P1 items before deploying. After that, deploy it as a controlled demo MVP, not as a production SaaS handling real client health data.

## Verification Results

Commands run locally:

| Check | Result | Notes |
|---|---:|---|
| `frontend: cmd /c npm run -s build` | PASS | Built successfully. Warning: JS bundle is 1,143 KB minified, 348 KB gzip. |
| `frontend: cmd /c npm test -- --run` | PASS | 2 files, 11 tests passed. |
| `frontend: cmd /c npm run -s lint` | PASS WITH WARNINGS | 23 warnings, mostly `any` and missing hook dependencies. |
| `backend: .\\.verify_venv_20260621\\Scripts\\python.exe -m ruff check app tests` | PASS | Ruff found no issues. |
| `backend: .\\.verify_venv_20260621\\Scripts\\python.exe -m pytest -q` | FAIL/TIMEOUT | Timed out after 120s. |
| `backend: pytest tests/test_articles.py::test_unpublish_article -vv` | FAIL/TIMEOUT | Single test timed out after 60s. The path creates a published article and triggers embedding sync. |

Important local constraint: system `python.exe` is the Windows Store launcher stub, so backend verification only worked through the checked-in `.verify_venv_20260621` virtualenv.

## P0 - Fix Before Deployment

### 1. Backend tests hang because placeholder AI keys are treated as real keys

Evidence:
- `backend/.env` contains set values for `GEMINI_API_KEY` and `OPENAI_API_KEY`, but they look like placeholders.
- Article create/publish/unpublish calls `_sync_article_index()` in `backend/app/services/article_service.py`, which calls the embedding stack for published articles.
- `tests/test_articles.py::test_unpublish_article` timed out by itself.

Why it matters:
- CI and local verification become unreliable.
- A recruiter running tests may think the app is broken.
- In production, article publishing can block on an external embedding call.

Recommendation:
- Treat placeholder API values like empty config.
- In tests, force `GEMINI_API_KEY=""` and mock `article_embedding_service.index_article`.
- Move article embedding sync to a background task or explicit "index article" job.
- Add a timeout around embedding calls.

### 2. The repo has a tracked virtualenv and test output

Evidence:
- `git ls-files backend/.verify_venv_20260621` reports 7,198 tracked files.
- `git ls-files` reports 7,428 tracked files total, so almost the whole repo is a virtualenv.
- `backend/pytest_out.txt` is tracked.
- `.gitignore` ignores `.venv/`, `venv/`, and `env/`, but not `.verify_venv_*`.

Why it matters:
- This is the single biggest resume-polish problem.
- It makes the repo look uncurated and AI-generated.
- It bloats clone size and can confuse dependency/security review.

Recommendation:
- Remove `backend/.verify_venv_20260621/` and `backend/pytest_out.txt` from git history or at least from the current tree.
- Add `.verify_venv_*/`, `pytest_out*.txt`, `*.log`, and local test DB files to `.gitignore`.
- Document normal setup using `python -m venv .venv` instead.

### 3. CI/CD files are currently untracked

Evidence:
- `git status --short` shows `?? .github/`.
- `docs/tasks.md` and `README.md` claim CI/CD exists.

Why it matters:
- GitHub will not run CI until `.github/workflows/ci.yml` is committed.
- The portfolio story says "automated CI/CD", but the repository does not actually contain it in the tracked state.

Recommendation:
- Commit `.github/workflows/ci.yml` after fixing backend test reliability.
- Add a README badge only after CI actually passes on GitHub.

### 4. Several UI styles do not apply because Tailwind-like classes are used without Tailwind

Evidence:
- Components use classes like `text-3xl`, `font-bold`, `mb-4`, `space-y-6`, `grid`, `flex`, `text-red-600`, `bg-red-50`.
- `frontend/src/index.css` defines only a small subset of utility classes.
- Tailwind is not installed, by project convention.

Why it matters:
- Key dashboard/client/progress screens will render flatter and less spaced than intended.
- This directly affects UI/UX first impression.

Recommendation:
- Either replace utility classes with scoped CSS modules/classes, or define the missing utility classes deliberately.
- Prefer component CSS for main screens so the vanilla-CSS architecture is credible.

### 5. Plan editor CSS references undefined design tokens

Evidence:
- `frontend/src/pages/plans/PlanEditorPage.css` uses `--primary-color`, `--secondary-color`, `--surface-color`, `--background-color`, and `--text-light`.
- `frontend/src/components/plans/FoodSearchModal.css` uses the same undefined tokens.
- The actual design tokens are named like `--color-primary-600`, `--surface-card`, and `--text-secondary`.

Why it matters:
- The most important product screen can render with missing colors/backgrounds.
- This makes the flagship AI meal plan editor look unfinished.

Recommendation:
- Replace old token names with the current tokens.
- Add a small visual regression check for the plan editor once seeded data exists.

### 6. Production Docker contexts are not controlled

Evidence:
- `backend/.dockerignore` is missing.
- `frontend/.dockerignore` is missing.
- Backend folder contains local venvs, caches, test DBs, and `pytest_out.txt`.

Why it matters:
- Docker images can include unnecessary files.
- Build times and image sizes will be worse.
- Sensitive local files are easier to accidentally include later.

Recommendation:
- Add `.dockerignore` files for backend and frontend.
- Exclude `.env`, venvs, caches, tests if not needed in runtime, `node_modules`, `dist`, logs, and local DB files.

## P1 - High-Value Fixes Before Resume Demo

### 7. Config validation is incomplete for real production

Evidence:
- `backend/app/config.py` defaults `DEBUG=True`.
- Production validation only enforces `JWT_SECRET`.
- It does not enforce `ENCRYPTION_KEY`, non-local `CORS_ORIGINS`, valid `FRONTEND_URL`, or required WhatsApp settings when WhatsApp is enabled.

Risk:
- Easy to deploy with docs disabled only if `DEBUG=false`, but other insecure or broken settings can slip through.

Recommendation:
- Add production validators for `ENCRYPTION_KEY`, `CORS_ORIGINS`, `FRONTEND_URL`, and placeholder AI keys.
- Add `ENVIRONMENT=development|test|production` instead of relying only on `DEBUG`.

### 8. Refresh tokens are stored in `localStorage`

Evidence:
- `frontend/src/contexts/AuthContext.tsx` stores both access and refresh tokens in `localStorage`.
- `frontend/src/api/client.ts` reads tokens from `localStorage`.

Risk:
- XSS can steal long-lived refresh tokens.

Recommendation:
- For a public deployment with real data, move refresh tokens to secure, httpOnly, SameSite cookies.
- For a resume MVP, document the tradeoff and keep sanitization tight.

### 9. WhatsApp credential fallback can break tenant isolation expectations

Evidence:
- `backend/app/services/whatsapp_service.py` tries per-dietitian credentials first, then falls back to global environment credentials.

Risk:
- In a multi-tenant SaaS, missing tenant credentials could send via the wrong global WhatsApp number.

Recommendation:
- For tenant-scoped sends, fail closed when a dietitian has no WhatsApp credentials.
- Keep global fallback only for single-tenant/dev mode and make that explicit.

### 10. Phone number normalization is too weak

Evidence:
- Client create checks exact `Client.whatsapp_number == data.whatsapp_number`.
- Webhook lookup normalizes inbound `from` only by prepending `+`.

Risk:
- `9876543210`, `+919876543210`, `91 98765 43210`, and Meta's numeric sender format may not match.
- Real client messages can be stored as inbound but never handled.

Recommendation:
- Normalize all phone numbers to E.164 at input boundaries.
- Store a canonical phone field and use it for uniqueness and webhook lookup.

### 11. Article embedding is synchronous in request paths

Evidence:
- `create_article`, `publish_article`, and `unpublish_article` await `_sync_article_index()`.

Risk:
- Article publish/unpublish can be slow or fail due to AI/network dependencies.
- It is the direct cause of the backend test timeout in this environment.

Recommendation:
- Use `BackgroundTasks` for indexing or persist `indexing_status`.
- Do not block article CRUD on embeddings.

### 12. Meal plan editing recreates all day/item rows

Evidence:
- `plan_service.update_plan()` deletes existing days and recreates all days/items when `days` is provided.
- `PlanEditorPage` adds/deletes items by sending the whole day structure.

Risk:
- Item IDs change after edits.
- Meal logs linked to old `meal_plan_item_id` can become orphaned or lose practical traceability.

Recommendation:
- Add item-level endpoints: add item, update item, delete item, reorder item.
- Keep full replacement only for AI regeneration.

### 13. Frontend bundle is large for an MVP

Evidence:
- Vite build warning: `dist/assets/index-*.js` is 1,143 KB minified.

Risk:
- Public landing page users download dashboard/editor/chart/editor libraries unnecessarily.

Recommendation:
- Route-level lazy-load dashboard pages, article editor, TipTap, and Recharts.
- Keep public landing/article pages in a light initial chunk.

### 14. Frontend error handling still uses blocking browser dialogs

Evidence:
- `alert`, `confirm`, and `prompt` appear in plan, client, article, protocol, and progress flows.

Risk:
- The app feels less polished and less SaaS-like.

Recommendation:
- Use the existing toast/modal system consistently.
- Replace `prompt` for protocol save with a small modal form.

## P2 - Polish And Architecture Improvements

### 15. README and docs contain mojibake in this environment

Evidence:
- README/task output shows characters like `ðŸ¥—`, `â€”`, and `â†’`.

Risk:
- If the file itself is encoded incorrectly, GitHub README presentation will look broken.

Recommendation:
- Re-save Markdown files as UTF-8.
- Check GitHub rendering before sharing the repo.

### 16. Leftover starter assets/files reduce repo credibility

Evidence:
- `frontend/src/App.css` contains Vite starter styles and is not imported by `main.tsx`.
- `frontend/src/assets/react.svg` and `frontend/src/assets/vite.svg` remain.

Recommendation:
- Delete unused starter files.
- Keep only product-specific assets.

### 17. Frontend test coverage is too thin

Evidence:
- Only 2 frontend test files and 11 tests passed.

Risk:
- The highest-risk UI flows are not protected: auth redirect, token refresh, plan editor, AI generation modal, article editor, public intake form.

Recommendation:
- Add tests for `AuthContext`, API refresh behavior, public intake submission, and plan editor add/delete behavior.

### 18. Backend tests are comprehensive but too integration-heavy

Evidence:
- 142 backend tests collected.
- Many tests register dietitians repeatedly, which means repeated bcrypt hashing.
- Full suite did not complete in 120s/180s in this environment.

Recommendation:
- Lower bcrypt cost in tests or monkeypatch password hashing.
- Mock external AI/WhatsApp services globally.
- Split slow integration tests from fast unit tests.

### 19. In-memory rate limiting is acceptable for a demo but not production-grade

Evidence:
- Custom `RateLimitMiddleware` is in process memory.
- Backend production Docker starts Uvicorn with `--workers 2`.

Risk:
- Limits are per worker and reset on deploy.

Recommendation:
- For public deployment, back rate limiting with Redis.
- For resume demo, mention it as a pragmatic MVP limiter.

### 20. Frontend uses React 19/Vite 8, while README says React 19 but AGENTS says React 18

Risk:
- Not a blocker, but it creates a story mismatch.

Recommendation:
- Update docs to match the actual stack, or downgrade to the intended stack.

## Security Assessment

Strengths:
- Tenant-scoped backend services are mostly consistent.
- Auth uses bcrypt and refresh-token rotation.
- Production FastAPI docs are disabled when `DEBUG=false`.
- CORS is not wildcarded by default.
- WhatsApp webhook signature verification exists.
- Public article rendering uses a custom sanitizer before `dangerouslySetInnerHTML`.
- Plan approval blocks critical/high validation failures.

Concerns:
- Refresh tokens in `localStorage`.
- Production config validation is too weak.
- Placeholder AI keys are accepted as configured.
- WhatsApp per-tenant credential fallback should fail closed.
- Phone numbers are not canonicalized.
- In-memory rate limiter with multiple workers.
- No `.dockerignore`.

## UI/UX Assessment

Strengths:
- Clear product surfaces: dashboard, clients, plan editor, protocols, articles, settings, public pages.
- The design system has a restrained health-tech palette.
- Public landing page has a real intake form and WhatsApp CTA.
- Toast infrastructure exists.

Concerns:
- Several major screens rely on undefined Tailwind-style utility classes.
- Plan editor and food modal use stale CSS variable names.
- Browser dialogs make key flows feel prototype-like.
- Sidebar uses emoji/string icons, and some characters render as mojibake in this shell.
- The plan editor has no real inline edit UI for portions/macros, only add/delete.
- Route-level code splitting is missing.

## Architecture Assessment

Strengths:
- Monolith is the correct choice for this project.
- Backend layering is understandable: routers -> services -> models/schemas.
- Multi-tenant query discipline is visible across core services.
- AI evolution story is strong for AI engineer roles: direct call -> LangChain/RAG -> LangGraph.
- PostgreSQL + pgvector is appropriate for article RAG.

Concerns:
- LangGraph/RAG/Redis may be more complexity than the MVP needs unless demoed clearly.
- Article embedding should not be synchronous.
- Meal plan item editing needs more granular API boundaries.
- CI must be committed and green to support the "production-grade" claim.

## Suggested Fix Order

1. Remove tracked virtualenv/test artifacts and add ignore rules.
2. Fix test config: empty placeholder AI keys, mock embeddings/WhatsApp, make backend suite pass quickly.
3. Commit `.github/workflows/ci.yml` and make CI green.
4. Fix missing frontend utility styles and undefined CSS variables.
5. Add `.dockerignore` files and verify Docker production builds.
6. Harden production config validation.
7. Normalize phone numbers end to end.
8. Move article embedding to background processing.
9. Replace browser dialogs with app modals/toasts.
10. Deploy backend/frontend and update README with real URLs and demo credentials.

## Resume Positioning

This can be a strong sole resume project after the P0 fixes. The best story is:

"I built a multi-tenant AI practice OS for Indian dietitians. It combines FastAPI, React, PostgreSQL/pgvector, WhatsApp webhooks, and an AI meal-plan workflow that evolved from direct structured LLM calls to RAG and LangGraph. I kept the MVP monolithic, enforced tenant isolation, added safety validation before plan approval, and wired CI/CD plus Docker deployment."

Avoid claiming:
- "Production-grade security" until refresh-token storage, config validation, Docker context, and test reliability are fixed.
- "Fully deployed" until there is a live URL.
- "CI/CD complete" until `.github/workflows` is committed and passing.

