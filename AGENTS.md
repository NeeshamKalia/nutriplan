# AGENTS.md — Read This First

> **If you are an AI agent working on this project, read this file completely before doing anything.**

## What Is NutriPlan?

NutriPlan is a **B2B SaaS for Indian nutritionists**. It has three surfaces:

1. **Dietitian Dashboard** (React web app) — Manage clients, generate AI meal plans, review/approve, write articles, track adherence and progress
2. **Client WhatsApp Bot** (WhatsApp Business Cloud API) — Clients receive plans, track meals, request substitutions, get grocery lists — all via WhatsApp, no app download
3. **Branded Landing Page** (public) — Dietitian's profile, blog/articles, client intake form, SEO

The AI drafts personalized Indian meal plans based on each client's health profile. The dietitian reviews and approves before delivery. AI assists the expert, it does NOT replace them.

## Document Map

| File | Purpose | When to Read |
|------|---------|-------------|
| **`docs/tasks.md`** | 🔴 **Operational task registry — your primary file** | ALWAYS read first. Check PROJECT STATUS. Execute the next task. Update status when done |
| `docs/prd.md` | Product requirements, user stories, feature priorities | When you need to understand WHAT to build and WHY |
| `docs/technical_spec.md` | Architecture, database schema (SQL), API contracts, WhatsApp flow | When you need HOW — schema, endpoint signatures, data structures |
| `docs/implementation_plan.md` | Phased strategy, evolution story, dependency graph | When you need to understand phase ordering or the big picture |
| `docs/product_analysis.md` | Market research, competitor analysis, USP reasoning | Only if you need product context (rarely needed for coding) |

## Agent Workflow

```
1. Open docs/tasks.md
2. Read PROJECT STATUS at the top
3. Find the next TODO task
4. Check its prerequisites (deps must be ✅)
5. Execute the task following the steps
6. Run the verification commands
7. Update the task status to ✅ DONE
8. Update PROJECT STATUS (last completed, next task)
9. Git commit with the specified message
```

## Key Rules

### Architecture
- **Monolith** — one FastAPI server, one React app, one PostgreSQL database
- **No microservices**, no message queues, no Kubernetes
- **No Redis** until Phase 10 — use FastAPI BackgroundTasks for async
- **No LangChain** until Phase 9 — use direct OpenAI API calls with structured JSON output
- **No LangGraph** until Phase 10 — start with simple prompt → JSON → rule-based validation

### AI Evolution (Critical for Interview Story)
```
Phase 4 (MVP):   Direct Gemini API calls → structured JSON → rule-based validation
Phase 9:         LangChain → composability → LangSmith tracing
Phase 10:        LangGraph → multi-step stateful workflow → retry on validation failure
```
This evolution is intentional. Do NOT skip ahead. Interviewers prefer hearing "I started simple and added complexity when justified."

### Security — Multi-Tenant Isolation
**Every database query on tenant-scoped tables MUST include `dietitian_id` filter.** A dietitian must never see another dietitian's clients.
```python
# CORRECT
clients = db.query(Client).filter(Client.dietitian_id == current_dietitian.id)

# WRONG — never do this
clients = db.query(Client).all()
```

### Client Authentication
Clients have NO login. They are identified by their WhatsApp phone number. When a WhatsApp message arrives, look up the sender's number in the `clients` table to find their `dietitian_id`.

### WhatsApp Webhooks
The POST webhook handler MUST return 200 within 5 seconds (Meta requirement). Process messages in `BackgroundTasks`, never block the response.

### Food & Cultural Context
- Use Indian food names: dal, roti, sabzi, paneer — NOT "lentil soup, flatbread, cottage cheese"
- The food database has Hindi names alongside English
- Plans must respect: vegetarian/non-veg, regional cuisine preferences, monthly budget in INR
- Generated plans are educational drafts — always require dietitian approval before client delivery

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + Vite + TypeScript |
| Database | PostgreSQL 16 + pgvector |
| AI (MVP) | Google Gemini API (free tier, direct calls, structured JSON output) |
| Messaging | WhatsApp Business Cloud API |
| Deployment | Docker + Railway/Render |
| CI/CD | GitHub Actions |
| CSS | Vanilla CSS with design tokens (NO Tailwind unless asked) |

## Project Structure

```
nutriplan/
├── AGENTS.md              ← You are here
├── README.md
├── docker-compose.yml
├── docs/
│   ├── tasks.md           ← Your primary operational file
│   ├── prd.md
│   ├── technical_spec.md
│   ├── implementation_plan.md
│   └── product_analysis.md
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── core/
│   │   │   └── logger.py      # Structured JSON logging (request_id, user_id, correlation_id)
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   │   ├── v1/            # Versioned API routes (/api/v1/*)
│   │   │   ├── webhook.py     # WhatsApp (not versioned)
│   │   │   └── public.py      # Landing page (not versioned)
│   │   ├── services/
│   │   ├── ai/
│   │   ├── whatsapp/
│   │   └── utils/
│   ├── tests/
│   └── seed/
└── frontend/
    ├── src/
    │   ├── api/
    │   ├── components/
    │   ├── contexts/
    │   ├── hooks/
    │   └── pages/
    └── public/
```

## Conventions

### Git
- Feature branches: `feat/task-101-scaffolding`
- Commit messages: use the message from the task, or follow conventional commits
- Clean, meaningful commits — interviewers WILL look at commit history

### Python (Backend)
- Async everywhere (async def, await)
- Pydantic v2 for schemas
- SQLAlchemy 2.0 style (select(), not query())
- Type hints on all function signatures
- Docstrings on services and AI functions

### TypeScript (Frontend)
- Strict mode
- Functional components with hooks
- Named exports
- CSS modules or scoped CSS (not inline styles)

### Testing
- pytest for backend
- Test files mirror source: `app/services/auth_service.py` → `tests/test_auth.py`
- Fixtures in `conftest.py`
- Mock external APIs (OpenAI, WhatsApp)

## Owner Context

This is a personal project by Neesham Kalia (backend engineer, 3+ years Node.js/TypeScript). His wife is a nutritionist who currently manages clients via Canva + WhatsApp + Excel. She is the first user and tester.

The project serves two purposes:
1. **Portfolio** — demonstrate full-stack + AI skills for Mohali/Chandigarh job applications
2. **Real product** — actually useful for his wife's practice

The 13-week career roadmap is at: `C:\Users\Neesham.Kalia\Documents\career_roadmap.md`
