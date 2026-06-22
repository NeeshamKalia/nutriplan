# NutriPlan Fix Reverification — 20 June 2026

This note independently verifies Claude's claimed Tier 1/2 fixes against the current uncommitted working tree.

## Verdict

**The fix batch is partially implemented, but it is not verified or release-ready.** Clean backend dependency installation succeeds and several code changes are directionally correct. However, frontend tests/build, backend lint, and the LangGraph test are red. Migration and production Docker behavior remain incomplete.

## Claim-by-claim result

| # | Claim | Result | Evidence / remaining issue |
|---|---|---|---|
| 1 | Git remote cleaned | **Verified locally** | Origin is the canonical credential-free GitHub URL and contains no embedded PAT pattern. Token revocation on GitHub cannot be verified locally and remains a manual action. |
| 2 | OpenAI version fixed | **Verified** | A fresh temporary environment installed all requirements successfully; `pip check` reported no broken requirements. |
| 3 | Rate limiter test fixture | **Verified for the original cascade** | Autouse fixture clears `_windows`; four representative registration/client tests passed. Full suite did not complete within five minutes, so all 130 tests are not verified. |
| 4 | Health fields migration | **Partial / unsafe for existing data** | Revision `002` exists and offline SQL generation succeeds. It converts old arrays to plaintext JSON, but the model immediately tries Fernet decryption when an encryption key is configured. Existing migrated rows will raise `Decryption failed`; the migration does not actually encrypt legacy data. No real PostgreSQL upgrade/downgrade test was run. |
| 5 | Safety gate on approval | **Partial** | Server query blocks stored critical/high failures. No regression test was added. Manual plan edits do not recompute validations, so stale passed validations can allow newly unsafe edits, while stale failed validations can block a corrected plan. |
| 6 | LangGraph abort path | **Code added, verification failed** | Route now returns `abort`, but the existing test still expects `format_output` and fails. Abort messages use nonexistent `check_name` instead of validation `type`, producing `unknown`. No end-to-end abort test exists. |
| 7 | Truthful delivery feedback | **Mostly implemented** | Plan editor branches on returned `delivered` versus `approved` status and renders through the toast system. The page renders locally. There is still no delivery retry endpoint/action, so an approved-but-failed plan remains stuck. No frontend test covers either toast branch. |
| 8 | Frontend Docker API build arg | **Incomplete** | Dockerfile declares `ARG VITE_API_URL`, but CI invokes `docker build` without `--build-arg`. The resulting image still falls back to `http://localhost:8000`. The image also cannot build while `npm run build` is red. |
| 9 | README fixed | **Verified for named items** | README now states React 19, removes Zustand, and uses the correct repository URL. Broader deployment/CI claims remain stronger than current evidence. |
| 10 | `.env.example` created | **Verified** | `backend/.env.example` exists and covers application settings. |
| 11 | Report cleanup / ignore rules | **Verified with caveat** | Three report files are absent and untracked. `*.xml` is overly broad and may hide legitimate future XML files. |
| 12 | CI runs frontend tests | **Step exists but CI remains red** | Workflow includes the test step. Current tests fail in this verification environment, production build fails, and backend Ruff reports errors. |

## Executed checks

| Check | Result |
|---|---|
| Fresh `pip install -r requirements.txt` | **Pass** |
| `pip check` | **Pass** |
| Representative rate-limit regression tests | **Pass — 4/4** |
| Existing plan approval/delivery tests | **Pass — 2/2** |
| LangGraph max-safety-retry test | **Fail — expected old route** |
| Backend full suite | **Unverified — timed out after 5 minutes at 17 tests** |
| Ruff (`app`, `tests`, `alembic`) | **Fail — 11 errors** |
| Frontend tests | **Fail** |
| Frontend production build | **Fail — Jest-DOM types, ThemeContext type import, Vite config typing** |
| Frontend lint | **Pass with 23 warnings** |
| Alembic history/heads | **Pass — `002` is head** |
| Alembic offline upgrade SQL | **Pass** |
| Real PostgreSQL migration | **Not run** |
| Docker builds | **Not run; frontend build already fails** |

## Required next fixes

1. Fix frontend TypeScript/Vitest configuration and make tests/build green.
2. Update/add LangGraph tests for the abort node and correct `check_name` to `type`.
3. Add approval-gate tests and recompute deterministic validations after every manual plan edit and immediately before approval.
4. Redesign migration `002` to encrypt existing values safely, or explicitly support one-time plaintext legacy reads followed by re-encryption; test on PostgreSQL in both directions.
5. Pass `VITE_API_URL` to the production Docker build or use a same-origin runtime proxy; fail builds when it is absent.
6. Fix Ruff errors so the existing CI backend lint step can pass.
7. Add an idempotent WhatsApp delivery retry workflow and persist/display the delivery error.
8. Commit the intended files before relying on GitHub CI; `.github/` and several implementation files are currently untracked.

## Readiness

The previous audit verdict remains: **do not publicly host or use real client health data yet**. The project is suitable only for a controlled synthetic-data demonstration after the exposed token is revoked.
