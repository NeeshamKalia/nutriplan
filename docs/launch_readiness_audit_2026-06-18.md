# NutriPlan Launch Readiness Audit

**Audit date:** 18 June 2026  
**Repository state:** Current working tree, including uncommitted changes  
**Purpose:** Portfolio review for AI engineer/full-stack roles and readiness to demonstrate to a nutritionist

## Executive verdict

**Not ready for public hosting or use with real client health data.**

The project is suitable for a controlled local portfolio walkthrough after the critical security issue below is handled, but it should not yet accept real nutritionist/client data or send real WhatsApp messages. The primary blockers are a leaked GitHub credential in local Git configuration, broken production builds/dependencies, schema/migration incompatibility, a failing test suite, and safety/delivery behavior that can mislead a dietitian.

| Area | Rating | Verdict |
|---|---:|---|
| Product concept | 8/10 | Strong, specific problem and credible first-user story |
| Architecture/storytelling | 7/10 | Good monolith and AI-evolution narrative; implementation has drift |
| Backend correctness | 4/10 | Useful coverage, but current suite is red and production paths are unverified |
| AI safety/reliability | 3/10 | Structured output exists, but unsafe plans are not blocked |
| Frontend UI | 6/10 | Coherent and responsive; production build currently fails |
| UX for a nutritionist | 5/10 | Main workflows are understandable; delivery/error feedback is unreliable |
| Security/privacy | 3/10 | Tenant-scoping effort is visible, but credential and health-data issues block launch |
| Deployment readiness | 2/10 | No live deployment, no deploy workflow, and current images/config cannot be trusted |
| Portfolio readiness | 6/10 | Strong scope, but interviewers will quickly find inconsistencies unless fixed |

## P0 — fix before any hosted demo

### 1. Revoke the exposed GitHub personal access token

The `origin` remote URL contains a GitHub personal access token. This audit does not reproduce it.

**Risk:** Anyone who obtains terminal logs, screenshots, Git config, or copied diagnostics may gain repository access.

**Required action:** Revoke the token in GitHub immediately, create a new narrowly scoped credential only if needed, and change the remote to a credential-free URL such as `https://github.com/NeeshamKalia/nutriplan.git`. Check shell history and any shared logs for the old token.

### 2. Make backend dependencies installable

`backend/requirements.txt:15` pins `openai==1.50.0`, while `backend/requirements.txt:18` pins `langchain-openai==0.2.14`, which requires OpenAI `>=1.58.1,<2`. A clean `pip install -r requirements.txt` fails dependency resolution.

**Required action:** Choose a compatible, tested lock set. Prefer a compiled lock/constraints file and run installation in CI from a clean environment.

### 3. Fix the production database migration for encrypted health fields

The model stores `medical_conditions` and `allergies` through encrypted text decorators (`backend/app/models/client.py:50-51`), but the only migration creates PostgreSQL arrays (`backend/alembic/versions/001_initial_schema.py:99-100`). A ciphertext string is not compatible with an array column. The original migration also appears to have been expanded repeatedly instead of adding immutable follow-up revisions.

**Risk:** Fresh or existing PostgreSQL deployments can fail when saving client health data; migration history cannot safely evolve a deployed database.

**Required action:** Stop editing revision `001`; create a new migration that converts these fields to `TEXT` safely, with a data migration/rollback plan. Test `alembic upgrade head` from an empty database and from a database at the prior revision.

### 4. Restore a green frontend production build

`npm run build` fails due to:

- missing Vitest/Jest-DOM type integration in test files;
- `ReactNode` not imported as a type in `ThemeContext.tsx:1`;
- Vite config typing rejecting the `test` key at `frontend/vite.config.ts:8` (use Vitest's config import/merge pattern).

The production frontend Dockerfile runs this command, so its image cannot build.

### 5. Restore a green backend suite and make it deterministic

Observed full-suite result: **69 failed, 61 passed**. The main cascade is the global in-memory registration rate limiter returning 429 across tests. Even `tests/test_auth.py` fails in isolation after its third registration request because limiter state is not reset between tests.

There is also an independent LangGraph integration-test failure: the test patches `app.ai.plan_generator._call_provider`, but `plan_generator_langgraph.py` imported the function directly, so the patch misses it and makes a real provider call.

**Required action:** Disable/reset rate limiting through an injected test dependency or fixture; patch the symbol where it is used; keep all external AI/WhatsApp calls mocked. CI must run the exact clean install, test, lint, type-check, migration, and image-build path.

### 6. Enforce safety failures as a hard approval gate

After the maximum safety retries, `route_after_safety` sends a plan with remaining critical/high failures to `format_output` (`backend/app/ai/plan_generator_langgraph.py:158-170`). The plan is saved with failed validations, and `approve_plan` checks only that status is `draft` (`backend/app/services/plan_service.py:322-340`). The UI also leaves **Approve & Send** enabled when validations fail.

The deterministic checks are too shallow for clinical safety:

- allergen detection searches only substrings in `food_name`;
- it ignores ingredients, preparation notes, and the food database's allergen metadata;
- dietary checks are English keyword lists;
- the generated schema allows duplicate/missing day numbers and arbitrary meal types/counts.

**Required action:** Reject generation when blocking checks remain, prevent approval server-side and client-side, add an explicit dietitian override only with reason/audit log, validate day/meal uniqueness, and perform ingredient/allergen checks against structured food IDs. Continue presenting plans as educational drafts requiring expert review.

### 7. Fix WhatsApp delivery state and truthful feedback

If WhatsApp delivery fails, the backend leaves the plan `approved`, but no delivery-retry route exists and the approval route cannot be called again. The UI always displays “Plan approved and sent successfully!” (`frontend/src/pages/plans/PlanEditorPage.tsx:64`) regardless of returned delivery status.

**Required action:** Separate approval from delivery, persist delivery attempts/errors, add an idempotent retry action, and show distinct states: approved, sending, delivered, failed. Never claim delivery unless Meta returned success for all required messages.

### 8. Make production runtime topology safe

The backend image starts two Uvicorn workers (`backend/Dockerfile:40`) while the scheduler starts inside application lifespan. The environment-variable “single scheduler” guard is process-local; one worker cannot set another worker's environment. With scheduling enabled, both workers can send reminders.

The same in-memory rate limiter is also per worker and trusts `X-Forwarded-For` directly, while Uvicorn trusts forwarded headers from all sources. This allows inconsistent limits and potential IP spoofing unless a trusted proxy strips/sets the header.

**Required action:** Run scheduled jobs in one dedicated process/worker or use a distributed lock; use Redis-backed limits; trust forwarded headers only from the actual reverse proxy.

### 9. Supply a real production frontend API URL

The frontend falls back to `http://localhost:8000` (`frontend/src/api/client.ts:3`). Vite variables are compiled at build time, but `frontend/Dockerfile` has no build argument/environment for `VITE_API_URL`. The Compose environment only affects the dev server.

**Required action:** Add an explicit production build argument or same-origin reverse proxy. Fail the production build when the API URL is missing instead of silently using localhost.

## P1 — fix before presenting to a nutritionist

### Privacy and consent

- The public form explicitly invites allergies and medical conditions but has no consent checkbox, privacy notice, retention statement, or link explaining who controls the data.
- There is no client data export/deletion workflow, account deletion, or documented retention policy.
- Access and refresh tokens are stored in `localStorage`; a future XSS issue could expose them. Prefer short-lived access tokens in memory and a secure, HttpOnly, SameSite refresh cookie.
- Add a clear disclaimer that AI output is a draft reviewed by a qualified professional and is not emergency/medical advice.

Do not enter real client health data until these controls and the migration issue are resolved.

### Public landing-page issues

- “Fill in your details and Dr. will reach out” is produced by taking the first token of `Dr. Neha Sharma`. Strip honorifics or say “the dietitian will reach out.”
- Add validation for Indian/international WhatsApp numbers instead of accepting any 10–20 character string.
- The duplicate non-versioned `/p/{slug}/intake` endpoint is not covered by the public API rate-limit prefix. Either remove it or rate-limit both routes.
- Add terms/privacy links and explicit consent before submission.

### UX and accessibility

- Login/register labels have very low contrast on the dark panel; increase contrast to WCAG AA.
- Client, article, and protocol list pages mostly log request errors but do not show a recoverable error state. A network failure can look like an empty list.
- Replace native `alert()`/`confirm()` usage with the existing modal/toast system, especially for delivery and destructive actions.
- Add visible focus states, keyboard/modal focus trapping, Escape handling, and a basic automated accessibility check.
- Destructive actions should explain consequences and, where practical, use archive/undo rather than immediate deletion.

### AI implementation reliability

- Gemini generation currently throws `unexpected keyword argument 'response_mime_type'` through the pinned LangChain/Google integration and falls back to OpenAI. Verify the binding API against the selected package versions.
- LangChain metadata records zero tokens and zero cost, weakening the claimed observability/cost story.
- The LLM judge samples only three days and fails open (`passed: true`) when unavailable. Treat it as advisory, not a safety control.
- Add a versioned prompt/evaluation dataset with representative Indian profiles: vegan, Jain, egg allergy, lactose intolerance, diabetes, renal constraints, low budget, pregnancy, elderly, and conflicting preferences.

### CI/deployment documentation

- `docs/tasks.md` marks “Docker + CI/CD + Deploy” complete while also saying no deployed URL and listing deployment as next work.
- Only `.github/workflows/ci.yml` exists; there is no deployment workflow.
- README claims React 18 and Zustand, but the package uses React 19 and no Zustand.
- README clone URL is still `yourusername`.
- There is no `.env.example`, production runbook, backup/restore procedure, rollback procedure, or smoke-test script.

## P2 — portfolio and maintainability improvements

- Add backend formatting/lint tooling to declared dev dependencies; `ruff` is referenced by CI but absent locally.
- Resolve 23 frontend lint warnings, especially effect dependencies and `any` error handling.
- Add frontend coverage for auth refresh, route guards, forms, plan editor, failed API states, and delivery status. Current frontend evidence is 2 test files / 11 tests.
- Add true browser E2E tests for register → create client → generate mocked plan → review → approve → delivery failure/retry.
- Add pagination to client/plan/article lists and test large data sets.
- Add database constraints for domain enums/statuses and AI plan day uniqueness.
- Remove generated reports (`report.xml`, `report2.xml`, `pytest_articles.txt`) from the repository/worktree and ignore them.
- Make health/readiness checks verify PostgreSQL/Redis connectivity rather than returning process-only health.
- Add dependency/security scanning and secret scanning to CI.

## UI/UX observations from browser QA

Tested at 1280×720 and 390×844 using a local mock API; no project files were modified for the mock.

### What works

- Navigation labels and core information architecture are easy to understand.
- Dashboard hierarchy is sensible: active clients, adherence, plan volume, approvals, attention list, activity.
- Client cards expose goal, diet, and conditions without excessive drilling.
- Protocol and article screens use consistent cards/actions.
- Auth, client, article, protocol, settings, and public landing screens showed no horizontal overflow at 390 px.
- Forms generally have accessible names and mobile controls are large enough to tap.
- Public page WhatsApp links are properly encoded and use a recognizable CTA.

### What needs work

- The design is clean but generic; the nutritionist workflow would benefit from clearer daily actions: plans awaiting review, delivery failures, unread client messages, and today’s follow-ups.
- The dashboard does not expose WhatsApp connection health or failed deliveries.
- The client list reveals medical-condition badges at a glance; consider a privacy mode for clinics/shared screens.
- The plan editor's most important safety state is visually secondary and does not control the primary action.
- Mobile navigation works structurally, but the hidden sidebar remains in the accessibility tree; confirm proper `aria-hidden`/inert behavior when closed.

## Automated verification evidence

| Check | Result |
|---|---|
| Backend clean dependency install | **Fail** — OpenAI/LangChain version conflict |
| Backend full pytest | **Fail** — 69 failed, 61 passed |
| Targeted validator/webhook/schema tests | **Pass** — 14 passed |
| LangGraph integration test | **Fail** — mock misses imported symbol; real provider call attempted |
| Frontend unit tests | **Pass** — 11 passed |
| Frontend production build | **Fail** — TypeScript/Vitest config errors |
| Frontend lint | **Pass with warnings** — 23 warnings |
| Docker image build | **Not run** — Docker unavailable; frontend/dependency blockers already guarantee failure risk |
| Real PostgreSQL/Alembic upgrade | **Not run** — PostgreSQL/Docker unavailable; static type mismatch found |
| Real Gemini/WhatsApp E2E | **Not run** — would cause external calls and requires valid credentials/sandbox numbers |

## Hosting readiness gates

Do not host publicly until all gates below pass:

- [ ] Exposed GitHub token revoked and secret scan clean
- [ ] Clean backend install succeeds from scratch
- [ ] `alembic upgrade head` succeeds on fresh PostgreSQL and migration test passes
- [ ] Health-field encryption round-trip tested on PostgreSQL
- [ ] Backend tests, frontend tests, lint, type-check, and both Docker builds are green in CI
- [ ] Critical/high AI validation failures block approval
- [ ] WhatsApp delivery has persisted failure state and retry
- [ ] Scheduler proven single-instance
- [ ] Production API/CORS/proxy/environment configuration documented and smoke-tested
- [ ] Privacy notice, consent, retention, deletion, and AI disclaimer added
- [ ] Backup/restore and rollback exercised
- [ ] Demo tenant uses synthetic data only

After those gates, deploy first as a **private demo** with synthetic clients and WhatsApp sandbox/test recipients. Only move to a nutritionist pilot after a threat/privacy review and a complete observed workflow test.

## Recommended nutritionist demo script

Use synthetic data and keep the session to 15–20 minutes:

1. Show the public practice page and intake experience.
2. Create/review a client profile with Indian dietary preferences and budget.
3. Generate a plan using a protocol and explain that AI creates a draft.
4. Deliberately show allergen/calorie validation and the approval gate.
5. Edit one meal/portion manually.
6. Approve, send to a sandbox WhatsApp number, and verify actual delivery status.
7. Log a meal/weight through WhatsApp and show dashboard/adherence updates.
8. Ask the nutritionist: What would you need before trusting this weekly? What information is missing? Which step is slower than Canva/WhatsApp/Excel today?

## Portfolio guidance

The strongest interview story is not “all ten phases are complete.” It is:

- a real problem observed in a nutrition practice;
- deliberate monolith and multi-tenant choices;
- direct LLM baseline, then measured reasons for adding orchestration/RAG;
- deterministic safety checks and human approval;
- concrete failures found through QA and how they were fixed.

Because the implementation was produced heavily with Claude/Gemini, be prepared to explain and modify every critical path without assistance: JWT rotation, tenant filters, Alembic migration strategy, webhook signature/idempotency, LangGraph state transitions, structured-output validation, Redis behavior, scheduler topology, CORS/proxy trust, and frontend token refresh. An interviewer will value a smaller system you fully understand more than a broad feature list with red builds or inaccurate claims.

## Final recommendation

**Today:** Safe only for local/private demonstration with synthetic data after revoking the exposed GitHub token.  
**Public portfolio URL:** Wait until P0 items and hosting gates are green.  
**Real nutritionist pilot:** Wait until P0 + privacy/consent + delivery retry + observed sandbox E2E are complete.
