# NutriPlan — Task Registry

> [!IMPORTANT]
> **This is the operational task file.** Every agent session must READ this first, EXECUTE a task, then UPDATE the status before ending. This file is the single source of truth for project progress.

---

## 📍 PROJECT STATUS

**⚠️ AGENTS: Update this section after every task completion.**

```
Current Phase:        2 — Client Management
Last Completed Task:  TASK-303
Next Task:            TASK-401
In Progress:          (none)
Blockers:             (none)
Deployed URL:         (not yet)
Repository:           c:\Users\Neesham.Kalia\Documents\nutriplan
```

### What's Done
_(Agents: add completed items here as you finish them)_

- ✅ **TASK-101** — Repository scaffolded, backend + frontend + docker-compose created (2026-06-14)
- ✅ **TASK-102** — 15 SQLAlchemy models + initial Alembic migration created (2026-06-14)
- ✅ **TASK-103** — Authentication system: register, login, refresh, logout, /me — 12 tests passing (2026-06-14)
- ✅ **TASK-201** — Client CRUD API with multi-tenant isolation — 9 tests passing (2026-06-14)

### What's Next
1. **TASK-401** — Simple AI Plan Generator
2. **TASK-402** — Frontend - AI Generation Trigger

---

## 📖 AGENT INSTRUCTIONS

### Before Starting Any Work
1. **Read this file** — check PROJECT STATUS above
2. **Read the next task below** — each task is self-contained
3. **Check prerequisites** — don't start a task if its deps aren't ✅
4. **If a task is 🔄 IN PROGRESS**, check the agent notes — it may be partially done

### While Working
5. **Follow the steps in order** — each task has numbered steps
6. **Create files at the exact paths listed** — the project structure matters
7. **Run verification commands** — every task has a "Verify" section

### After Completing a Task
8. **Update the task status** to ✅ DONE with the date
9. **Add notes** about anything the next agent should know
10. **Update PROJECT STATUS** at the top (last completed, next task)
11. **Commit with the specified message** (or a variant)

### Reference Documents
- **PRD** (what to build): `docs/prd.md` → [View PRD](./prd.md)
- **Technical Spec** (how to build): `docs/technical_spec.md` → [View Spec](./technical_spec.md)
- **Implementation Plan** (phases & strategy): `docs/implementation_plan.md` → [View Plan](./implementation_plan.md)

### Project Location
- **Repository root:** To be created at `C:\Users\Neesham.Kalia\Documents\nutriplan`
- **Backend:** `nutriplan/backend/`
- **Frontend:** `nutriplan/frontend/`

---

## PHASE 1: FOUNDATION

---

### TASK-101: Repository & Project Scaffolding

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 1 | **Priority:** P0 | **Est:** 1h  
**Deps:** None  
**Commit:** `feat: initialize nutriplan monorepo`

#### Goal
Create the NutriPlan monorepo with a FastAPI backend and a React+Vite+TypeScript frontend, connected via docker-compose with PostgreSQL.

#### Steps

**Step 1 — Create the project directory and git repo:**
```bash
mkdir C:\Users\Neesham.Kalia\Documents\nutriplan
cd C:\Users\Neesham.Kalia\Documents\nutriplan
git init
```

**Step 2 — Create `.gitignore`:**
```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
*.egg
.venv/
venv/
env/

# Node
node_modules/
dist/

# Environment
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp

# Docker
docker-compose.override.yml

# OS
.DS_Store
Thumbs.db

# Test
.coverage
htmlcov/
.pytest_cache/
```

**Step 3 — Create backend structure:**

Create `backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.0
pydantic[email]==2.9.0
pydantic-settings==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
python-multipart==0.0.12
google-genai==1.0.0
openai==1.50.0
pytest==8.3.0
pytest-asyncio==0.24.0
```

Create `backend/app/__init__.py`: (empty file)

Create `backend/app/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nutriplan:nutriplan@localhost:5432/nutriplan"
    
    # Auth
    JWT_SECRET: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    JWT_REFRESH_EXPIRATION_DAYS: int = 30
    
    # Gemini (primary — free tier)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_CHEAP_MODEL: str = "gemini-2.0-flash-lite"
    
    # OpenAI (fallback — paid, optional for MVP)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_CHEAP_MODEL: str = "gpt-4o-mini"
    
    # WhatsApp
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    
    # App
    APP_NAME: str = "NutriPlan"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"           # DEBUG in dev, INFO in prod
    
    class Config:
        env_file = ".env"

settings = Settings()
```

Create `backend/app/main.py`:
```python
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.logger import setup_logging, get_logger, request_id_ctx, correlation_id_ctx

# Initialize structured logging
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered practice OS for nutritionists",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    cid = request.headers.get("X-Correlation-ID", rid)
    request_id_ctx.set(rid)
    correlation_id_ctx.set(cid)
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
```

Create `backend/app/database.py`:
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

Create `backend/tests/__init__.py`: (empty)

Create `backend/app/core/__init__.py`: (empty)

Create `backend/app/core/logger.py`:
```python
import logging
import json
import sys
from contextvars import ContextVar

# Context variables — set per-request via middleware
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
            "correlation_id": correlation_id_ctx.get(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers = [handler]

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

**Step 4 — Create frontend:**
```bash
cd C:\Users\Neesham.Kalia\Documents\nutriplan
npx -y create-vite@latest frontend --template react-ts
```
_(Do NOT run `npm install` yet — docker-compose will handle deps)_

**Step 5 — Create `docker-compose.yml`:**
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: nutriplan
      POSTGRES_PASSWORD: nutriplan
      POSTGRES_DB: nutriplan
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://nutriplan:nutriplan@postgres:5432/nutriplan
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  pgdata:
```

Create `backend/Dockerfile.dev`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Step 6 — Create `backend/.env`:**
```env
DATABASE_URL=postgresql+asyncpg://nutriplan:nutriplan@localhost:5432/nutriplan
JWT_SECRET=dev-secret-change-in-production
GEMINI_API_KEY=your-gemini-key-here
OPENAI_API_KEY=sk-your-key-here
```

**Step 7 — Create README.md:**
```markdown
# 🥗 NutriPlan

AI-powered practice OS for Indian nutritionists. Dietitians manage clients via a web dashboard, AI drafts personalized meal plans, and clients interact entirely through WhatsApp.

## Tech Stack
- **Backend:** FastAPI (Python 3.11)
- **Frontend:** React + Vite + TypeScript
- **Database:** PostgreSQL 16 + pgvector
- **AI:** Google Gemini 2.0 Flash (free tier) + OpenAI fallback
- **Messaging:** WhatsApp Business Cloud API

## Quick Start
\```bash
docker-compose up -d
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
\```

## Project Structure
\```
nutriplan/
├── backend/         # FastAPI API server
├── frontend/        # React dashboard
├── docs/            # PRD, specs, plans
└── docker-compose.yml
\```
```

**Step 8 — Create docs folder and copy spec files:**
```bash
mkdir docs
```
_(Copy prd.md, technical_spec.md, implementation_plan.md, tasks.md into docs/)_

**Step 9 — Commit:**
```bash
git add .
git commit -m "feat: initialize nutriplan monorepo with FastAPI + React + Docker"
```

#### Verify
```bash
# From project root
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000
# Visit http://localhost:8000/health → should return {"status": "ok", "app": "NutriPlan"}
# Visit http://localhost:8000/docs → should show FastAPI Swagger UI

# OR via Docker:
docker-compose up -d postgres
docker-compose up backend
# Same verification
```

#### Agent Notes
_(Fill in after completing this task)_
```
Completed by:
Date:
Notes:
```

---

### TASK-102: Database Schema & Models

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 1 | **Priority:** P0 | **Est:** 2h  
**Deps:** TASK-101 ✅  
**Commit:** `feat: add database models and initial migration`

#### Goal
Create all SQLAlchemy models and run the first Alembic migration.

#### Steps

**Step 1 — Initialize Alembic:**
```bash
cd backend
alembic init alembic
```

Update `alembic.ini` — set `sqlalchemy.url`:
```ini
sqlalchemy.url = postgresql+asyncpg://nutriplan:nutriplan@localhost:5432/nutriplan
```

Update `alembic/env.py` — configure for async and import models:
```python
# Add at top:
from app.database import Base
from app.models import *  # Import all models so Alembic detects them

# Set target_metadata:
target_metadata = Base.metadata

# Change run_migrations_online to use async engine
```
_(See FastAPI + Alembic async migration patterns if needed)_

**Step 2 — Create model files:**

Create `backend/app/models/__init__.py`:
```python
from app.models.dietitian import Dietitian
from app.models.refresh_token import RefreshToken
from app.models.client import Client
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanItem, MealPlanValidation
from app.models.meal_log import MealLog
from app.models.progress_log import ProgressLog
from app.models.whatsapp_message import WhatsAppMessage
from app.models.protocol import Protocol
from app.models.article import Article, ArticleEmbedding
from app.models.food_item import FoodItem
from app.models.audit_log import AuditLog
```

Create these model files following the SQL schema in the technical spec (Section 3.2). Each model maps to the corresponding table. Key things to include:

`backend/app/models/dietitian.py`:
- All columns from `dietitians` table in spec
- Relationships: `clients`, `protocols`, `articles`, `food_items`, `refresh_tokens`

`backend/app/models/refresh_token.py`:
- All columns from `refresh_tokens` table in spec (token_hash, expires_at, revoked_at, replaced_by, user_agent, ip_address)
- Relationship: `dietitian`
- Self-referential FK: `replaced_by` → `refresh_tokens.id`

`backend/app/models/client.py`:
- All columns from `clients` table including health profile fields
- ARRAY types for: `medical_conditions`, `allergies`, `food_preferences`
- Include `archived_at` TIMESTAMPTZ column (set when status → 'archived')
- Relationships: `dietitian`, `meal_plans`, `meal_logs`, `progress_logs`

`backend/app/models/meal_plan.py`:
- Three classes: `MealPlan`, `MealPlanDay`, `MealPlanItem`, `MealPlanValidation`
- All columns from spec
- Relationships between plan → days → items

`backend/app/models/meal_log.py`:
- Columns: client_id, meal_plan_item_id, log_date, meal_type, status, deviation_note, logged_via

`backend/app/models/progress_log.py`:
- Columns: client_id, log_date, weight_kg, waist_cm, hip_cm, chest_cm, notes, logged_via
- Unique constraint on (client_id, log_date)

`backend/app/models/whatsapp_message.py`:
- All columns from spec including: direction, wa_message_id, message_type, message_body, intent, ai_response

`backend/app/models/protocol.py`:
- Columns from spec including JSONB for macro_split, ARRAY for preferred/avoided foods

`backend/app/models/article.py`:
- Two classes: `Article`, `ArticleEmbedding`
- ArticleEmbedding has `vector(1536)` column for pgvector

`backend/app/models/food_item.py`:
- All nutritional columns, boolean flags, ARRAY for common_allergens

`backend/app/models/audit_log.py`:
- Columns: dietitian_id (nullable, ON DELETE SET NULL), action, entity_type, entity_id, metadata (JSONB), ip_address, user_agent
- No relationship back to dietitian (keep it lightweight, dietitian might be deleted)

**Step 3 — Generate and run migration:**
```bash
# Make sure postgres is running
docker-compose up -d postgres

# Generate migration
alembic revision --autogenerate -m "initial schema"

# Run migration
alembic upgrade head
```

**Step 4 — Verify tables exist:**
```bash
docker-compose exec postgres psql -U nutriplan -d nutriplan -c "\dt"
# Should list all 14+ tables (including refresh_tokens and audit_logs)
```

#### Verify
```bash
# All tables exist
docker-compose exec postgres psql -U nutriplan -d nutriplan -c "\dt"

# pgvector extension exists
docker-compose exec postgres psql -U nutriplan -d nutriplan -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"

# Migration is clean
alembic current  # Should show the latest revision
```

#### Schema Reference
Full SQL schema: [Technical Spec — Section 3.2](./technical_spec.md#32-table-definitions)

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

### TASK-103: Authentication System

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 1 | **Priority:** P0 | **Est:** 1.5h  
**Deps:** TASK-102 ✅  
**Commit:** `feat: add dietitian authentication with JWT`

#### Goal
Dietitian can register, login, and access protected routes.

#### Steps

**Step 1 — Create `backend/app/utils/security.py`:**
```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
```

**Step 2 — Create `backend/app/schemas/auth.py`:**
```python
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str  # min 8 chars
    full_name: str
    phone: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class DietitianResponse(BaseModel):
    id: str
    email: str
    full_name: str
    slug: str
    phone: str | None
    specializations: list[str] | None
    has_whatsapp_setup: bool
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    dietitian: DietitianResponse
```

**Step 3 — Create `backend/app/dependencies.py`:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.database import get_db
from app.utils.security import decode_token
from app.models.dietitian import Dietitian
from sqlalchemy import select

security = HTTPBearer()

async def get_current_dietitian(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dietitian:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        dietitian_id = payload.get("sub")
        if not dietitian_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = await db.execute(select(Dietitian).where(Dietitian.id == dietitian_id))
    dietitian = result.scalar_one_or_none()
    if not dietitian:
        raise HTTPException(status_code=401, detail="Dietitian not found")
    return dietitian
```

**Step 4 — Create `backend/app/services/auth_service.py`:**
- `register(db, data)` → check email unique, hash password, generate slug from name, create dietitian, store refresh token in `refresh_tokens` table (as SHA-256 hash), return tokens
- `login(db, data)` → find by email, verify password, store refresh token in `refresh_tokens` table, create `audit_log` entry (action='login'), return tokens
- `refresh(db, token)` → hash the incoming refresh token, look up in `refresh_tokens`, verify not revoked/expired, revoke old token, issue new pair, link via `replaced_by`. If revoked token is reused → revoke entire token family (security: potential theft detected)
- `logout(db, token)` → hash the refresh token, set `revoked_at` on the matching row
- `generate_slug(name)` → "Dr. Neha Sharma" → "dr-neha-sharma", handle conflicts by appending numbers

**Step 5 — Create `backend/app/routers/v1/auth.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, DietitianResponse
from app.services import auth_service
from app.dependencies import get_current_dietitian

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(db, data)

@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, data)

@router.get("/me", response_model=DietitianResponse)
async def get_me(dietitian = Depends(get_current_dietitian)):
    return dietitian
```

**Step 6 — Register router in `main.py`:**
```python
from fastapi import APIRouter
from app.routers.v1 import auth

# Create versioned API router with /api/v1 prefix
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)

app.include_router(api_v1)
```

> **Note:** Create `backend/app/routers/__init__.py` and `backend/app/routers/v1/__init__.py` (both empty). All versioned routers go inside `routers/v1/`. Non-versioned routes (webhook, public) go directly in `routers/`.

**Step 7 — Create tests `backend/tests/test_auth.py`:**
- Test register → returns tokens
- Test login → returns tokens
- Test login with wrong password → 401
- Test duplicate email → 409
- Test `/me` with valid token → returns dietitian
- Test `/me` with no token → 401

#### Verify
```bash
# Start backend
cd backend && uvicorn app.main:app --reload

# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123","full_name":"Dr. Test"}'
# Should return: {access_token, refresh_token, dietitian: {id, slug: "dr-test", ...}}

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123"}'
# Should return tokens

# Me (use the access_token from above)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
# Should return dietitian profile

# Tests
cd backend && pytest tests/test_auth.py -v
```

#### Agent Notes
```
Completed by: Antigravity Agent
Date: 2026-06-14
Notes:
- Implemented secure refresh token rotation with SHA-256 hashing (never store raw tokens)
- Token family tracking for theft detection (revoked token reuse → revoke all tokens)
- 12 pytest tests passing using SQLite + aiosqlite (no Postgres needed for tests)
- Fixed bcrypt 5.x incompatibility with passlib → pinned bcrypt>=4.0,<5.0
- Fixed timezone-naive comparison for SQLite compatibility
- Fixed UUID string→object conversion in get_current_dietitian dependency
- Pydantic V2 ConfigDict used (no deprecated class Config)
```

---

## PHASE 2: CLIENT MANAGEMENT

---

### TASK-201: Client CRUD API

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 2 | **Priority:** P0 | **Est:** 1.5h  
**Deps:** TASK-103 ✅  
**Commit:** `feat: add client CRUD with health profiles`

#### Goal
Dietitian can add, view, edit, and archive clients with full health profiles. Multi-tenant isolation enforced.

#### Steps

**Step 1 — Create `backend/app/schemas/client.py`:**
- `ClientCreate` — all fields from the clients table (see spec Section 4.2)
- `ClientUpdate` — all fields optional
- `ClientResponse` — includes id, created_at, status
- `ClientListResponse` — paginated list with total count

**Step 2 — Create `backend/app/services/client_service.py`:**
- `create_client(db, dietitian_id, data)` → validate unique WhatsApp number per dietitian, create
- `list_clients(db, dietitian_id, search, status, limit, offset)` → filtered list
- `get_client(db, dietitian_id, client_id)` → single client, 404 if not found or wrong dietitian
- `update_client(db, dietitian_id, client_id, data)` → partial update
- `archive_client(db, dietitian_id, client_id)` → set status='archived' AND archived_at=now()

**⚠️ CRITICAL — Multi-tenant isolation:**
Every query MUST filter by `dietitian_id`. A dietitian must never see another dietitian's clients.

**Step 3 — Create `backend/app/routers/v1/clients.py`:**
```
GET    /api/v1/clients               → list (query params: search, status, limit, offset)
POST   /api/v1/clients               → create
GET    /api/v1/clients/{client_id}   → get detail
PUT    /api/v1/clients/{client_id}   → update
DELETE /api/v1/clients/{client_id}   → archive (soft delete)
```
All routes use `Depends(get_current_dietitian)`.

**Step 4 — Register router in main.py**

**Step 5 — Tests `backend/tests/test_clients.py`:**
- Create client → 201 with all fields
- List clients → returns only this dietitian's clients
- Get client → returns full profile
- Update client → partial update works
- Delete client → status becomes 'archived'
- **Multi-tenant test:** Create client as dietitian A, try to access as dietitian B → 404

#### Verify
```bash
# Register a dietitian, get token, then:

# Create client
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Priya Kapoor",
    "whatsapp_number": "+919876543210",
    "age": 28, "gender": "female",
    "height_cm": 162, "weight_kg": 72, "target_weight_kg": 60,
    "activity_level": "light",
    "medical_conditions": ["PCOS"],
    "allergies": ["peanuts"],
    "dietary_type": "veg",
    "cuisine_preference": "north_indian",
    "primary_goal": "weight_loss",
    "monthly_food_budget_inr": 8000
  }'

# List clients
curl http://localhost:8000/api/v1/clients \
  -H "Authorization: Bearer <token>"

# Tests
pytest tests/test_clients.py -v
```

#### Agent Notes
```
Completed by: Antigravity Agent
Date: 2026-06-14
Notes:
- All 5 REST endpoints: POST, GET list, GET detail, PUT, DELETE (archive)
- Multi-tenant isolation enforced — every query filters by dietitian_id
- Unique WhatsApp number per dietitian (UniqueConstraint + service-level check)
- Soft delete via status='archived' + archived_at timestamp
- Audit log entries for client_created and client_archived
- 9 tests passing including multi-tenant isolation test
- ARRAY/JSONB columns use TypeDecorator for SQLite compatibility in tests
```

---

### TASK-202: Frontend — Shell, Design System, Auth Pages

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 2 | **Priority:** P0 | **Est:** 2h  
**Deps:** TASK-103 ✅  
**Commit:** `feat: add dashboard shell with auth UI`

#### Goal
Create the design system, layout shell, and auth pages. After this, a dietitian can register and log in via the web UI.

#### Steps

**Step 1 — Install frontend deps:**
```bash
cd frontend
npm install react-router-dom axios recharts
npm install -D @types/react-router-dom
```
_(recharts is for the progress charts in Phase 7 — install now to avoid context switch later)_

**Step 2 — Create `frontend/src/index.css`:**
Design system with:
- CSS custom properties (tokens) for colors, spacing, typography, shadows
- Color palette: health/wellness theme — muted greens, clean whites, warm accents
- Google Font: `Inter` (add to `index.html`)
- Dark mode variables (optional, but impressive)
- Base element styles, utility classes

**Step 3 — Create layout components:**
- `src/components/layout/Sidebar.tsx` — nav links: Dashboard, Clients, Protocols, Articles, Settings
- `src/components/layout/TopBar.tsx` — dietitian name, avatar placeholder, logout
- `src/components/layout/MainLayout.tsx` — wraps sidebar + topbar + `<Outlet />`

**Step 4 — Create UI components:**
- `src/components/ui/Button.tsx` — variants: primary, secondary, ghost, danger; sizes: sm, md, lg
- `src/components/ui/Input.tsx` — text, email, password, textarea; with label and error
- `src/components/ui/Card.tsx` — container with shadow
- `src/components/ui/Badge.tsx` — status colors (green=active, yellow=paused, red=attention)
- `src/components/ui/Modal.tsx` — overlay dialog
- `src/components/ui/LoadingSpinner.tsx`

**Step 5 — Create API client:**
- `src/api/client.ts` — axios instance with baseURL, token injection, 401 redirect

**Step 6 — Create auth context:**
- `src/contexts/AuthContext.tsx` — login, register, logout, currentUser, isAuthenticated

**Step 7 — Create auth pages:**
- `src/pages/LoginPage.tsx` — email + password form, error display, link to register
- `src/pages/RegisterPage.tsx` — name + email + password, link to login

**Step 8 — Create placeholder pages:**
- `src/pages/DashboardPage.tsx` — "Dashboard coming soon"
- `src/pages/ClientsPage.tsx` — "Clients coming soon"

**Step 9 — Set up routing in `App.tsx`:**
```tsx
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />
  <Route element={<ProtectedRoute />}>
    <Route element={<MainLayout />}>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/clients" element={<ClientsPage />} />
    </Route>
  </Route>
</Routes>
```

#### Verify
```bash
cd frontend && npm run dev
# Visit http://localhost:5173/register → register form renders
# Fill in form → submit → redirects to dashboard
# Visit http://localhost:5173/login → login works
# Sidebar navigation works
# Logout clears token and redirects to login
```

#### Design Notes
- **DO NOT** make it look like a Bootstrap template. Premium health-tech aesthetic.
- Use subtle gradients, proper spacing, rounded corners
- Sidebar should feel like a modern SaaS app (think Linear, Notion, Vercel dashboard)

#### Agent Notes
```
Completed by: Antigravity Agent
Date: 2026-06-14
Notes:
- Installed react-router-dom, axios, recharts
- Built Sage Green / Warm Amber CSS theme using design tokens
- UI Components: Button, Input, Card, Badge, LoadingSpinner
- Layout: MainLayout, Sidebar, TopBar (responsive)
- Created fully functional Login and Register pages
- Configured AuthContext with token injection and 401 interceptor
- Set up React Router with Protected and Public routes
- Frontend builds cleanly via Vite
```

---

### TASK-203: Frontend — Clients List & Detail Pages

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 2 | **Priority:** P0 | **Est:** 2h  
**Deps:** TASK-201 ✅, TASK-202 ✅  
**Commit:** `feat: add client management UI`

#### Goal
Client list page with search/filter, add client form, and client detail page with tabs.

#### Steps

**Step 1 — `src/pages/ClientsPage.tsx`:**
- Fetch and display clients as cards or table
- Search bar (filters by name)
- Status filter dropdown (all, active, paused, archived)
- "Add Client" button → opens modal with form
- Each client card shows: name, primary goal, conditions (badges), status, last plan date

**Step 2 — Add Client form (modal or separate page):**
- Organized in sections: **Personal** (name, phone, age, gender) → **Body** (height, weight, target weight, activity) → **Health** (conditions, allergies, dietary type) → **Preferences** (cuisine, food preferences, budget) → **Goals** (primary goal, calorie target, meals per day, notes)
- Multi-select inputs for conditions, allergies, preferences (checkboxes or tag input)

**Step 3 — `src/pages/ClientDetailPage.tsx`:**
- Route: `/clients/:id`
- Header: client name, status badge, key stats (weight, goal, adherence)
- Tabs: **Profile** | **Plans** | **Progress** | **Adherence**
- Profile tab: view/edit all health profile fields
- Plans tab: list of plans (placeholder — populated in Phase 3)
- Progress tab: placeholder for Phase 7
- Adherence tab: placeholder for Phase 6
- "Generate Plan" button (placeholder — connected in Phase 4)

#### Verify
- Clients page loads and displays clients
- Add client form creates a new client
- Client detail page shows full profile
- Edit client works
- Search filters correctly

#### Agent Notes
```
Completed by: Antigravity Agent
Date: 2026-06-14
Notes:
- Built ClientsPage with search, status filtering, and client summary cards
- Built ClientDetailPage with comprehensive tabbed interface (Profile, Plans, Progress, Adherence)
- Built ClientFormPage (covers TASK-204) with comprehensive health/body/goals inputs
- Updated routing and verified Vite build
- API integration for creating and fetching clients is active
```

---

## PHASE 3: MEAL PLAN CRUD

---

### TASK-301: Meal Plan Manual CRUD API

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 3 | **Priority:** P0 | **Est:** 1.5h  
**Deps:** TASK-201 ✅  
**Commit:** `feat: add meal plan CRUD`

#### Goal
Dietitian can create, view, edit, and approve meal plans manually (without AI). This builds the data layer that AI generation will populate in Phase 4.

#### Steps

**Step 1 — Create schemas:** `backend/app/schemas/meal_plan.py`
- `MealPlanItemCreate` — food_name, portion_description, portion_grams, calories, protein_g, carbs_g, fat_g, meal_type
- `MealPlanDayCreate` — day_number, day_label, items list
- `MealPlanCreate` — title, week_start_date, days list
- `MealPlanItemResponse`, `MealPlanDayResponse`, `MealPlanResponse` — full detail with IDs
- `MealPlanListResponse` — summary (id, title, status, date, avg_calories)

**Step 2 — Create service:** `backend/app/services/plan_service.py`
- `create_plan(db, dietitian_id, client_id, data)` → create plan + days + items, calculate totals
- `list_plans(db, dietitian_id, client_id)` → ordered by date desc
- `get_plan(db, dietitian_id, plan_id)` → full plan with days/items
- `update_plan(db, dietitian_id, plan_id, data)` → update items, recalculate totals
- `approve_plan(db, dietitian_id, plan_id)` → set status='approved', approved_at=now

**Step 3 — Create router:** `backend/app/routers/plans.py`
```
POST   /api/v1/clients/{client_id}/plans          → create
GET    /api/v1/clients/{client_id}/plans           → list
GET    /api/v1/plans/{plan_id}                     → detail
PUT    /api/v1/plans/{plan_id}                     → update
POST   /api/v1/plans/{plan_id}/approve             → approve
```

**Step 4 — Auto-calculate nutritional totals:**
When plan is created or updated, calculate:
- Per-day totals (sum of item macros)
- Plan averages (avg of daily totals)

**Step 5 — Register router, write tests**

#### Verify
```bash
# Create a plan manually
curl -X POST http://localhost:8000/api/v1/clients/{id}/plans \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Plan","week_start_date":"2026-06-16","days":[...]}'

# Get plan → shows all days and items with calculated totals
# Approve plan → status changes

pytest tests/test_plans.py -v
```

#### Agent Notes
```
Completed by: Antigravity Agent
Date: 2026-06-14
Notes:
- Created schemas for MealPlan, MealPlanDay, MealPlanItem
- Created plan_service.py with macro auto-calculation and full tree insertion
- Set up plans.py router with client-scoped lists and plan-scoped updates
- All endpoints tested and pass multi-tenant isolation tests
```

---

### TASK-302: Indian Food Database

**Status:** ✅ DONE (2026-06-14)  
**Phase:** 3 | **Priority:** P0 | **Est:** 2h  
**Deps:** TASK-102 ✅  
**Commit:** `feat: add Indian food database with 200+ items`

#### Goal
Curated Indian food database with nutritional data. Used by AI for plan generation and by the plan editor for food search.

#### Steps

**Step 1 — Create `backend/seed/food_items.json`:**
200+ items covering: roti/paratha, rice varieties, all major dals (moong, masoor, toor, chana, urad), 30+ vegetables (lauki, tori, bhindi, palak, methi, gobhi, etc.), 20+ fruits, dairy (paneer, curd, milk, chaach, ghee), eggs/chicken/fish, snacks (makhana, roasted chana, murmura), beverages, condiments.

Each item format:
```json
{
  "name": "Moong dal (cooked)",
  "name_hindi": "मूंग दाल",
  "category": "lentil",
  "subcategory": "dal",
  "calories_per_100g": 106,
  "protein_per_100g": 7.0,
  "carbs_per_100g": 18.0,
  "fat_per_100g": 0.4,
  "fiber_per_100g": 1.5,
  "default_serving_description": "1 medium bowl (150g)",
  "default_serving_grams": 150,
  "is_vegetarian": true,
  "is_vegan": true,
  "is_gluten_free": true,
  "common_allergens": [],
  "approx_cost_per_kg_inr": 120
}
```

**Step 2 — Create seed script:** `backend/app/seed/load_foods.py`
```bash
python -m app.seed.load_foods
# Inserts all items, skips duplicates
```

**Step 3 — Create food search API:**
- `GET /api/v1/foods?q=paneer` → name search
- `GET /api/v1/foods?category=lentil` → category filter
- `GET /api/v1/foods?is_vegetarian=true` → boolean filter

**Step 4 — Verify seed:**
```bash
python -m app.seed.load_foods
curl "http://localhost:8000/api/v1/foods?q=dal"  # Should return multiple dals
curl "http://localhost:8000/api/v1/foods?category=vegetable"  # Should return 30+ items
```

#### Agent Notes
```
Completed by: Antigravity Agent
Date: 2026-06-14
Notes:
- Created backend/seed/food_items.json with diverse list of Indian foods
- Created load_foods.py script for DB seeding
- Built FoodItem schemas and added GET /api/v1/foods search endpoint
- Wrote and passed pytest for the food router filters and search
```

---

### TASK-303: Frontend — Plan Editor

**Status:** ⬜ TODO  
**Phase:** 3 | **Priority:** P0 | **Est:** 2.5h  
**Deps:** TASK-301 ✅, TASK-302 ✅, TASK-203 ✅  
**Commit:** `feat: add meal plan editor UI`

#### Goal
The plan review/edit interface — the most important screen. Shows 7 days × 5 meals with inline editing.

#### Steps
See implementation plan TASK-303 for detailed acceptance criteria. Key points:
- 7-day tabbed view
- Each meal slot shows food items with macros
- Inline edit: click to change food, portion, macros
- Food search modal (searches the food database API)
- Daily/weekly nutritional totals
- "Approve & Send" button (WhatsApp delivery connected in Phase 5)
- "Generate with AI" button (connected in Phase 4)

#### Agent Notes
```
Completed by: Antigravity Agent
Date: 2026-06-14
Notes:
- Created PlanEditorPage.tsx with 7-day tabbed navigation and 5 daily meal slots
- Implemented stunning aesthetics: glassmorphism day tabs, dynamic hover effects, premium micro-animations
- Built FoodSearchModal.tsx with debounced real-time search hitting the backend /foods endpoint
- Integrated handleCreatePlan in ClientDetailPage to auto-initialize 7 empty days
- Ensured state updates properly display added food macros instantly
```

---

## PHASE 4: AI PLAN GENERATION

---

### TASK-401: Simple AI Plan Generator

**Status:** ⬜ TODO  
**Phase:** 4 | **Priority:** P0 | **Est:** 2.5h  
**Deps:** TASK-301 ✅, TASK-302 ✅  
**Commit:** `feat: add AI meal plan generation (simple prompt + structured output)`

#### Goal
AI generates structured 7-day meal plans using **direct OpenAI API calls** (no LangChain). The output is validated JSON that maps to the meal plan schema.

#### Steps

**Step 1 — Create `backend/app/ai/__init__.py`** (empty)

**Step 2 — Create `backend/app/ai/prompts/plan_generation.py`:**

System prompt template:
```python
SYSTEM_PROMPT = """You are a clinical nutrition AI assistant.
You generate structured Indian meal plans for clients based on their health profile.

RULES:
1. Use Indian food items with local names (roti, dal, sabzi — NOT "flatbread, lentil soup")
2. NEVER include any food the client is allergic to — ZERO TOLERANCE
3. Stay within the calorie target ±10%
4. Respect dietary type strictly (vegetarian = no meat/fish/eggs unless eggetarian)
5. Vary meals across 7 days — no identical meals on consecutive days
6. Include 5 meals per day: breakfast, mid_morning, lunch, evening_snack, dinner
7. Consider the client's monthly food budget when selecting ingredients
8. Include preparation notes for items that need them
9. Use common Indian portion descriptions (1 roti, 1 katori dal, 1 bowl rice)
10. Output MUST be valid JSON matching the exact schema provided

OUTPUT FORMAT:
{json_schema}"""

def build_client_context(client, food_items) -> str:
    """Build a detailed prompt section from client profile."""
    # Format: conditions, allergies, preferences, goals, budget, etc.
    ...
```

**Step 3 — Create `backend/app/ai/plan_generator.py`:**
```python
import json
import time
from openai import AsyncOpenAI
from app.config import settings
from app.ai.prompts.plan_generation import SYSTEM_PROMPT, build_client_context

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_meal_plan(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None
) -> tuple[dict, dict]:
    """
    Generate a 7-day meal plan using simple prompt → OpenAI → structured JSON.
    Returns: (plan_data: dict, metadata: dict)
    """
    context = build_client_context(client_profile, food_items)
    
    user_prompt = f"Generate a 7-day meal plan for this client:\n\n{context}"
    if custom_instructions:
        user_prompt += f"\n\nAdditional instructions from dietitian: {custom_instructions}"
    
    start = time.time()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=4000
    )
    duration_ms = int((time.time() - start) * 1000)
    
    plan_data = json.loads(response.choices[0].message.content)
    
    metadata = {
        "model": settings.OPENAI_MODEL,
        "tokens_used": response.usage.total_tokens,
        "cost_usd": calculate_cost(response.usage),
        "duration_ms": duration_ms
    }
    
    return plan_data, metadata
```

**Step 4 — Create `backend/app/ai/plan_validator.py`:**
```python
def check_allergens(plan_data: dict, allergies: list[str]) -> dict:
    """Check every food item against client's allergen list."""
    ...

def check_calorie_range(plan_data: dict, target: int, tolerance: float = 0.1) -> dict:
    """Check if average daily calories are within target ±tolerance."""
    ...

def check_dietary_type(plan_data: dict, dietary_type: str) -> dict:
    """Check no meat for veg, no dairy for vegan, etc."""
    ...

def run_all_validations(plan_data: dict, client: Client) -> list[dict]:
    """Run all checks, return list of {type, passed, severity, message}."""
    ...
```

**Step 5 — Add generate endpoint to `backend/app/routers/plans.py`:**
```python
@router.post("/api/v1/clients/{client_id}/plans/generate")
async def generate_plan(
    client_id: str,
    request: GeneratePlanRequest,  # custom_instructions, week_start_date
    dietitian = Depends(get_current_dietitian),
    db = Depends(get_db)
):
    # 1. Fetch client + validate belongs to dietitian
    # 2. Fetch food items
    # 3. Call generate_meal_plan()
    # 4. Run validations
    # 5. Save plan + days + items + validations to DB
    # 6. Return full plan response
```

**Step 6 — Tests:**
- `test_plan_validator.py` — allergen detection, calorie range, dietary type
- Mock OpenAI response for plan generation tests

#### Verify
```bash
# Generate a plan (requires valid OPENAI_API_KEY in .env)
curl -X POST http://localhost:8000/api/v1/clients/{id}/plans/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"week_start_date": "2026-06-16"}'
# Should return a structured 7-day plan with macros

# With custom instructions
curl -X POST ... -d '{"custom_instructions": "Focus on anti-inflammatory foods"}'

pytest tests/test_plan_validator.py -v
```

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

### TASK-402: Connect AI to Plan Editor UI

**Status:** ⬜ TODO  
**Phase:** 4 | **Priority:** P0 | **Est:** 1h  
**Deps:** TASK-401 ✅, TASK-303 ✅  
**Commit:** `feat: wire AI plan generation to editor UI`

#### Goal
"Generate Plan" button on client detail page calls the AI, shows loading state, and opens the result in the plan editor.

#### Steps
- Add "Generate Plan" button on ClientDetailPage
- Loading state with animation (skeleton or spinner with text)
- Optional: custom instructions textarea before generating
- On success → navigate to PlanEditorPage with generated plan
- Validation results shown in sidebar panel (pass/fail badges, warnings)
- "Regenerate" button with instruction input

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

## PHASE 5: WHATSAPP INTEGRATION

---

### TASK-501: WhatsApp Webhook & Send Service

**Status:** ⬜ TODO  
**Phase:** 5 | **Priority:** P0 | **Est:** 2h  
**Deps:** TASK-102 ✅  
**Commit:** `feat: add WhatsApp webhook and send service`

#### Goal
Receive messages from WhatsApp, send messages to clients. All via Meta Cloud API.

#### Steps
See implementation plan TASK-501 for full details:
- `backend/app/routers/webhook.py` — GET (verification) + POST (receive)
- `backend/app/services/whatsapp_service.py` — send_text, send_template
- `backend/app/whatsapp/message_formatter.py` — format plans, grocery lists
- Signature verification, background processing, message logging

#### Reference
[Technical Spec — Section 5](./technical_spec.md#5-whatsapp-integration-architecture)

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

### TASK-502: Intent Classification & Command Handlers

**Status:** ⬜ TODO  
**Phase:** 5 | **Priority:** P0 | **Est:** 2h  
**Deps:** TASK-501 ✅, TASK-301 ✅  
**Commit:** `feat: add WhatsApp intent classification and commands`

#### Goal
Classify incoming messages → route to handlers → respond.

#### Handlers to build:
- `today` → send today's meals from active plan
- `help` → send command list
- `grocery` → send aggregated ingredient list
- Unknown → friendly fallback

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

### TASK-503: Plan Delivery via WhatsApp

**Status:** ⬜ TODO  
**Phase:** 5 | **Priority:** P0 | **Est:** 1h  
**Deps:** TASK-501 ✅, TASK-301 ✅  
**Commit:** `feat: deliver approved plans via WhatsApp`

#### Goal
When dietitian approves a plan → format and send to client on WhatsApp.

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

## PHASE 6: MEAL TRACKING

---

### TASK-601: DONE, Deviation & SWAP Handlers

**Status:** ⬜ TODO  
**Phase:** 6 | **Priority:** P1 | **Est:** 2h  
**Deps:** TASK-502 ✅, TASK-401 ✅  
**Commit:** `feat: add meal tracking and AI substitution via WhatsApp`

#### Handlers:
- `done/✅` → log meal as completed
- Free text deviation → log with note
- `swap [item]` → AI suggests alternatives (direct OpenAI call)

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

### TASK-602: Adherence Dashboard

**Status:** ⬜ TODO  
**Phase:** 6 | **Priority:** P1 | **Est:** 1.5h  
**Deps:** TASK-601 ✅, TASK-203 ✅  
**Commit:** `feat: add adherence dashboard`

#### Goal
- `GET /api/v1/clients/:id/adherence` — stats
- `GET /api/v1/dashboard` — overview for dietitian
- Dashboard page with stats cards, attention list
- Client detail — adherence tab

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

## PHASE 7: PROGRESS TRACKING + DEPLOY

---

### TASK-701: Progress Tracking API + UI

**Status:** ⬜ TODO  
**Phase:** 7 | **Priority:** P0 | **Est:** 2h  
**Deps:** TASK-201 ✅, TASK-203 ✅  
**Commit:** `feat: add progress tracking with weight charts`

#### Goal
- CRUD API for progress logs (weight, waist, notes)
- Client detail — Progress tab with line chart (Recharts)
- Delta indicators: "↓ 2.3 kg from start"
- WhatsApp: `weight 70.5` → logs weight

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

### TASK-702: Docker + CI/CD + Deploy

**Status:** ⬜ TODO  
**Phase:** 7 | **Priority:** P0 | **Est:** 2h  
**Deps:** All Phase 1-7 tasks  
**Commit:** `feat: add production Docker, CI/CD, and deployment`

#### Goal
Ship it. Live URL.

#### Steps
- Production Dockerfile (multi-stage)
- `.github/workflows/ci.yml` — lint + test + build
- Deploy backend to Railway/Render
- Deploy frontend to Vercel
- Configure WhatsApp webhook URL
- End-to-end test on production
- Update README with live URL

#### Agent Notes
```
Completed by:
Date:
Notes:
```

---

## PHASES 8-10: POST-MVP (Expand When Reached)

> [!NOTE]
> These phases are intentionally kept at summary level. When Phase 7 is complete, expand the relevant tasks with full detail like Phases 1-7 above. Don't over-plan what you haven't started.

### Phase 8: Content & Landing Page
- TASK-801: Articles CRUD API + editor UI + landing page
- TASK-802: WhatsApp article broadcast

### Phase 9: LangChain + RAG
- TASK-901: Migrate AI to LangChain, add LangSmith tracing
- TASK-902: RAG pipeline (article embeddings → WhatsApp Q&A)

### Phase 10: LangGraph + Polish
- TASK-1001: LangGraph multi-step plan workflow
- TASK-1002: Protocol templates
- TASK-1003: Redis caching + LLM-as-judge evaluation + daily reminders

---

## QUICK REFERENCE

### Running Locally
```bash
docker-compose up -d                      # Start postgres
cd backend && uvicorn app.main:app --reload  # Start backend
cd frontend && npm run dev                # Start frontend
```

### Running Tests
```bash
cd backend && pytest -v                   # All tests
cd backend && pytest tests/test_auth.py   # Specific test
```

### Database
```bash
docker-compose exec postgres psql -U nutriplan -d nutriplan  # Connect
alembic upgrade head                      # Run migrations
alembic revision --autogenerate -m "msg"  # Create migration
```

### Key URLs
```
Backend API:     http://localhost:8000
API Docs:        http://localhost:8000/docs
Frontend:        http://localhost:5173
PostgreSQL:      localhost:5432
```
