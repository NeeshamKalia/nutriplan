# NutriPlan — Technical Specification

**Version:** 1.0  
**Last Updated:** 2026-06-13  
**Status:** Draft — Awaiting Review  
**Companion:** [PRD](./prd.md) | [Implementation Plan](./implementation_plan.md)

---

## 1. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Backend API** | FastAPI (Python 3.11+) | AI ecosystem is Python-first; async support; auto-generated OpenAPI docs |
| **Frontend Dashboard** | React 18 + Vite + TypeScript | Modern SPA framework; user has 3+ years React/TS experience |
| **Database** | PostgreSQL 16 + pgvector | Relational data + vector embeddings in one DB; proven, free |
| **LLM Provider** | Google Gemini (primary) + OpenAI (fallback) | Gemini 2.0 Flash free tier (1,500 req/day); OpenAI GPT-4o as paid fallback; configurable |
| **Messaging** | WhatsApp Business Cloud API (Meta) | India's #1 messaging platform; webhook-based integration |
| **File Storage** | Local filesystem (MVP) → S3 (later) | PDF plans, article images |
| **Deployment** | Docker + docker-compose (local) → Railway/Render (production) | Simple deployment, free tiers available |
| **CI/CD** | GitHub Actions | Lint → test → build → deploy on push to main |
| **CSS** | Vanilla CSS with design tokens | Full control, no framework dependency |

### Added Later (Evolution Path)

| Layer | Technology | When | Why |
|---|---|---|---|
| **AI Framework** | LangChain | Phase 9 | Composability, prompt management, tracing via LangSmith |
| **AI Orchestration** | LangGraph | Phase 10 | Multi-step stateful workflow for plan generation + validation |
| **Cache** | Redis | Phase 10 | Caching food queries, rate limiting, session state |
| **Embeddings** | Gemini text-embedding-004 (free) or OpenAI text-embedding-3-small | Phase 9 | RAG for article-based Q&A |
| **Observability** | LangSmith or Langfuse | Phase 9 | LLM call tracing, cost tracking |

---

## 2. Architecture Overview

```
                    ┌──────────────────────────────┐
                    │        Internet / Users       │
                    └──────┬───────────┬───────────┘
                           │           │
                 ┌─────────▼──┐  ┌─────▼──────────┐
                 │  React SPA │  │  WhatsApp Cloud │
                 │ (Dashboard)│  │   API (Meta)    │
                 └─────────┬──┘  └─────┬───────────┘
                           │           │
                    ┌──────▼───────────▼──────┐
                    │      FastAPI Server      │
                    │                          │
                    │  /api/v1/*  (REST)       │
                    │  /webhook/whatsapp       │
                    │  /p/{slug}  (public)     │
                    ├──────────────────────────┤
                    │     Service Layer         │
                    │  ┌──────────────────────┐│
                    │  │  Plan Generation     ││
                    │  │  (LangGraph Agent)   ││
                    │  ├──────────────────────┤│
                    │  │  WhatsApp Service    ││
                    │  │  (Send/Receive)      ││
                    │  ├──────────────────────┤│
                    │  │  RAG Service         ││
                    │  │  (Q&A from articles) ││
                    │  ├──────────────────────┤│
                    │  │  Content Service     ││
                    │  │  (Articles/Blog)     ││
                    │  └──────────────────────┘│
                    └──────┬──────────┬────────┘
                           │          │
                    ┌──────▼───┐ ┌────▼────┐
                    │PostgreSQL│ │  Redis  │
                    │+pgvector │ │         │
                    └──────────┘ └─────────┘
```

### Key Design Decisions

1. **Monolith, not microservices** — One FastAPI server handles everything. Faster to build, simpler to deploy, easier to debug. Split later if needed.
2. **Async webhook processing** — WhatsApp webhooks return 200 immediately, then process in background (FastAPI BackgroundTasks). Meta requires < 5s response.
3. **Simple AI first, frameworks later** — Start with direct OpenAI API calls + structured JSON output. Migrate to LangChain (Phase 9) then LangGraph (Phase 10) as complexity demands. This evolution story is stronger for interviews.
4. **pgvector for everything** — No separate vector DB. Embeddings stored alongside relational data.
5. **No client auth** — Clients are identified by WhatsApp phone number. No passwords, no sessions, no web login.
6. **No Redis initially** — FastAPI BackgroundTasks for async processing. Redis added in Phase 10 when caching is justified by actual usage patterns.

---

## 3. Database Schema

### 3.1 Entity Relationship

```
dietitians ──< clients ──< meal_plans ──< meal_plan_days ──< meal_plan_items
    │              │            │
    │              │            └── meal_plan_validations
    │              │
    │              └──< meal_logs
    │              └──< whatsapp_messages
    │
    ├──< refresh_tokens
    ├──< audit_logs
    ├──< protocols ──< protocol_items
    ├──< articles ──< article_embeddings
    └──< food_items (shared, dietitian can add custom)
```

### 3.2 Table Definitions

```sql
-- ============================================
-- CORE TABLES
-- ============================================

CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Dietitian (the paying customer)
CREATE TABLE dietitians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,          -- for landing page URL: /p/{slug}
    phone VARCHAR(20),
    photo_url TEXT,
    bio TEXT,
    specializations TEXT[],                      -- e.g., ['PCOS', 'Thyroid', 'Weight Loss', 'Diabetes']
    qualifications TEXT,                          -- e.g., 'MSc Clinical Nutrition, IAPEN Certified'
    practice_name VARCHAR(255),
    whatsapp_phone_number_id VARCHAR(50),        -- Meta WABA phone number ID
    whatsapp_business_account_id VARCHAR(50),    -- Meta WABA ID
    whatsapp_access_token TEXT,                  -- Encrypted access token
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Refresh Tokens (for secure JWT rotation)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dietitian_id UUID NOT NULL REFERENCES dietitians(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,             -- SHA-256 hash of the refresh token (never store raw)
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,                       -- set on logout or rotation
    replaced_by UUID REFERENCES refresh_tokens(id), -- points to the new token after rotation
    user_agent TEXT,                              -- browser/device info for session management
    ip_address VARCHAR(45),                       -- IPv4 or IPv6
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_dietitian ON refresh_tokens(dietitian_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);

-- Client (managed by dietitian, interacts via WhatsApp)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dietitian_id UUID NOT NULL REFERENCES dietitians(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    whatsapp_number VARCHAR(20) NOT NULL,        -- E.164 format: +919876543210
    email VARCHAR(255),
    age INTEGER,
    gender VARCHAR(20),                          -- 'male', 'female', 'other'
    height_cm DECIMAL(5,1),
    weight_kg DECIMAL(5,1),
    target_weight_kg DECIMAL(5,1),
    activity_level VARCHAR(50),                  -- 'sedentary', 'light', 'moderate', 'active', 'very_active'
    
    -- Health profile
    medical_conditions TEXT[],                   -- e.g., ['hypothyroid', 'PCOS', 'pre-diabetic']
    allergies TEXT[],                             -- e.g., ['peanuts', 'shellfish', 'lactose']
    food_preferences TEXT[],                     -- e.g., ['vegetarian', 'no_onion', 'no_garlic']
    cuisine_preference VARCHAR(50),              -- 'north_indian', 'south_indian', 'mixed', 'continental'
    dietary_type VARCHAR(50),                    -- 'veg', 'non_veg', 'eggetarian', 'vegan'
    
    -- Goals & constraints
    primary_goal VARCHAR(100),                   -- 'weight_loss', 'weight_gain', 'maintenance', 'muscle_building', 'manage_condition'
    monthly_food_budget_inr INTEGER,             -- e.g., 8000
    daily_calorie_target INTEGER,                -- e.g., 1500 (can be null, let AI calculate)
    meals_per_day INTEGER DEFAULT 5,
    meal_timing_preferences JSONB,               -- e.g., {"breakfast": "7:30", "lunch": "13:00", ...}
    
    -- Additional notes
    notes TEXT,                                  -- free-text notes from dietitian
    lifestyle_notes TEXT,                        -- e.g., "works night shifts", "cooks for family of 4"
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',         -- 'active', 'paused', 'completed', 'archived'
    archived_at TIMESTAMPTZ,                     -- set when status → 'archived' (soft delete timestamp)
    onboarded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(dietitian_id, whatsapp_number)
);

CREATE INDEX idx_clients_dietitian ON clients(dietitian_id);
CREATE INDEX idx_clients_whatsapp ON clients(whatsapp_number);

-- ============================================
-- MEAL PLAN TABLES
-- ============================================

-- Meal Plan (a 7-day plan for a client)
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    dietitian_id UUID NOT NULL REFERENCES dietitians(id) ON DELETE CASCADE,
    
    title VARCHAR(255),                          -- e.g., "Week 3 - Thyroid Focus"
    week_start_date DATE,
    status VARCHAR(20) DEFAULT 'draft',          -- 'draft', 'approved', 'delivered', 'expired'
    
    -- Generation metadata
    generation_prompt TEXT,                      -- the full prompt sent to LLM
    generation_model VARCHAR(100),               -- e.g., 'gpt-4o'
    generation_tokens_used INTEGER,
    generation_cost_usd DECIMAL(10,6),
    generation_duration_ms INTEGER,
    custom_instructions TEXT,                    -- dietitian's extra instructions for regeneration
    
    -- Nutritional summary (calculated from items)
    avg_daily_calories INTEGER,
    avg_daily_protein_g DECIMAL(5,1),
    avg_daily_carbs_g DECIMAL(5,1),
    avg_daily_fat_g DECIMAL(5,1),
    avg_daily_fiber_g DECIMAL(5,1),
    
    -- Protocol reference
    protocol_id UUID REFERENCES protocols(id),   -- if generated from a template
    
    approved_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_meal_plans_client ON meal_plans(client_id);
CREATE INDEX idx_meal_plans_dietitian ON meal_plans(dietitian_id);

-- Meal Plan Day (one day within a 7-day plan)
CREATE TABLE meal_plan_days (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,                 -- 1-7 (Monday=1)
    day_label VARCHAR(20),                       -- 'Monday', 'Tuesday', etc.
    
    total_calories INTEGER,
    total_protein_g DECIMAL(5,1),
    total_carbs_g DECIMAL(5,1),
    total_fat_g DECIMAL(5,1),
    total_fiber_g DECIMAL(5,1),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_meal_plan_days_plan ON meal_plan_days(meal_plan_id);

-- Meal Plan Item (a single meal/food within a day)
CREATE TABLE meal_plan_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_plan_day_id UUID NOT NULL REFERENCES meal_plan_days(id) ON DELETE CASCADE,
    
    meal_type VARCHAR(30) NOT NULL,              -- 'breakfast', 'mid_morning', 'lunch', 'evening_snack', 'dinner', 'bedtime'
    sort_order INTEGER DEFAULT 0,
    
    food_name VARCHAR(255) NOT NULL,             -- e.g., "Moong dal cheela"
    food_name_hindi VARCHAR(255),                -- e.g., "मूंग दाल चीला"
    portion_description VARCHAR(255),            -- e.g., "2 medium pieces"
    portion_grams DECIMAL(6,1),                  -- e.g., 150.0
    
    calories INTEGER,
    protein_g DECIMAL(5,1),
    carbs_g DECIMAL(5,1),
    fat_g DECIMAL(5,1),
    fiber_g DECIMAL(5,1),
    
    -- Link to food database (optional)
    food_item_id UUID REFERENCES food_items(id),
    
    preparation_notes TEXT,                      -- e.g., "Use minimal oil, add green chutney on side"
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_meal_plan_items_day ON meal_plan_items(meal_plan_day_id);

-- Plan Validation Results (AI safety checks)
CREATE TABLE meal_plan_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    
    validation_type VARCHAR(50) NOT NULL,        -- 'allergen_check', 'calorie_range', 'nutritional_balance', 'preference_compliance'
    passed BOOLEAN NOT NULL,
    severity VARCHAR(20),                        -- 'error', 'warning', 'info'
    message TEXT,                                -- e.g., "Plan contains peanuts but client has peanut allergy"
    details JSONB,                               -- structured details
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MEAL TRACKING (from WhatsApp)
-- ============================================

CREATE TABLE meal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    meal_plan_item_id UUID REFERENCES meal_plan_items(id),
    
    log_date DATE NOT NULL,
    meal_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,                 -- 'completed', 'skipped', 'deviated'
    deviation_note TEXT,                         -- e.g., "Had pizza instead"
    
    logged_via VARCHAR(20) DEFAULT 'whatsapp',   -- 'whatsapp', 'manual'
    logged_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_meal_logs_client_date ON meal_logs(client_id, log_date);

-- ============================================
-- PROGRESS TRACKING
-- ============================================

CREATE TABLE progress_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    weight_kg DECIMAL(5,1),
    waist_cm DECIMAL(5,1),
    hip_cm DECIMAL(5,1),
    chest_cm DECIMAL(5,1),
    notes TEXT,                          -- "Feeling more energetic", "Slept badly"
    logged_via VARCHAR(20) DEFAULT 'dashboard',  -- 'dashboard', 'whatsapp'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, log_date)
);

CREATE INDEX idx_progress_logs_client ON progress_logs(client_id, log_date);

-- ============================================
-- WHATSAPP MESSAGES
-- ============================================

CREATE TABLE whatsapp_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id),
    dietitian_id UUID REFERENCES dietitians(id),
    
    direction VARCHAR(10) NOT NULL,              -- 'inbound', 'outbound'
    wa_message_id VARCHAR(255),                  -- Meta's message ID
    from_number VARCHAR(20),
    to_number VARCHAR(20),
    
    message_type VARCHAR(20),                    -- 'text', 'template', 'interactive', 'image', 'document'
    message_body TEXT,
    template_name VARCHAR(100),
    
    status VARCHAR(20),                          -- 'sent', 'delivered', 'read', 'failed'
    error_message TEXT,
    
    -- AI processing
    intent VARCHAR(50),                          -- 'command_today', 'command_done', 'command_swap', 'command_grocery', 'question', 'deviation', 'unknown'
    ai_response TEXT,
    ai_model VARCHAR(100),
    ai_tokens_used INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wa_messages_client ON whatsapp_messages(client_id);
CREATE INDEX idx_wa_messages_direction ON whatsapp_messages(direction, created_at);

-- ============================================
-- PROTOCOLS (dietitian's saved templates)
-- ============================================

CREATE TABLE protocols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dietitian_id UUID NOT NULL REFERENCES dietitians(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,                  -- e.g., "PCOS Weight Loss - Moderate Activity"
    description TEXT,
    target_conditions TEXT[],                    -- e.g., ['PCOS', 'insulin_resistance']
    target_goals TEXT[],                         -- e.g., ['weight_loss']
    
    calorie_range_min INTEGER,
    calorie_range_max INTEGER,
    macro_split JSONB,                           -- e.g., {"protein_pct": 30, "carbs_pct": 40, "fat_pct": 30}
    
    general_guidelines TEXT,                     -- free-text guidelines for AI
    preferred_foods TEXT[],                      -- e.g., ['methi seeds', 'cinnamon', 'flaxseeds']
    avoided_foods TEXT[],                        -- e.g., ['refined sugar', 'maida', 'white rice']
    
    sample_plan JSONB,                           -- optional: a full sample plan structure
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CONTENT & ARTICLES
-- ============================================

CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dietitian_id UUID NOT NULL REFERENCES dietitians(id) ON DELETE CASCADE,
    
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    summary TEXT,                                -- short summary for WhatsApp broadcast & SEO
    content TEXT NOT NULL,                       -- full article content (HTML or Markdown)
    cover_image_url TEXT,
    
    tags TEXT[],                                 -- e.g., ['thyroid', 'weight_loss', 'recipes']
    
    status VARCHAR(20) DEFAULT 'draft',          -- 'draft', 'published'
    published_at TIMESTAMPTZ,
    
    -- SEO
    meta_title VARCHAR(200),
    meta_description VARCHAR(300),
    
    -- WhatsApp broadcast
    broadcasted_at TIMESTAMPTZ,
    broadcast_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(dietitian_id, slug)
);

CREATE INDEX idx_articles_dietitian ON articles(dietitian_id);
CREATE INDEX idx_articles_status ON articles(status, published_at);

-- Article embeddings for RAG (chunked)
CREATE TABLE article_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(1536),                      -- OpenAI text-embedding-3-small dimension
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_article_embeddings_vector ON article_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- FOOD DATABASE
-- ============================================

CREATE TABLE food_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dietitian_id UUID REFERENCES dietitians(id), -- NULL = system-wide, non-null = dietitian's custom item
    
    name VARCHAR(255) NOT NULL,                  -- English name: "Moong dal cheela"
    name_hindi VARCHAR(255),                     -- Hindi: "मूंग दाल चीला"
    category VARCHAR(100),                       -- 'grain', 'lentil', 'vegetable', 'fruit', 'dairy', 'meat', 'snack', 'beverage', 'condiment'
    subcategory VARCHAR(100),                    -- 'dal', 'roti', 'rice', 'sabzi', etc.
    
    -- Per 100g values
    calories_per_100g INTEGER,
    protein_per_100g DECIMAL(5,1),
    carbs_per_100g DECIMAL(5,1),
    fat_per_100g DECIMAL(5,1),
    fiber_per_100g DECIMAL(5,1),
    
    -- Common serving
    default_serving_description VARCHAR(100),    -- e.g., "1 medium bowl (150g)"
    default_serving_grams DECIMAL(6,1),
    
    -- Metadata
    is_vegetarian BOOLEAN DEFAULT true,
    is_vegan BOOLEAN DEFAULT false,
    is_gluten_free BOOLEAN DEFAULT false,
    common_allergens TEXT[],                     -- e.g., ['gluten', 'dairy', 'nuts']
    
    -- Approximate cost
    approx_cost_per_kg_inr INTEGER,              -- rough price for budget estimation
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_food_items_category ON food_items(category);
CREATE INDEX idx_food_items_dietitian ON food_items(dietitian_id);

-- ============================================
-- AUDIT LOG (track important SaaS events)
-- ============================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dietitian_id UUID REFERENCES dietitians(id) ON DELETE SET NULL,
    
    action VARCHAR(100) NOT NULL,                -- e.g., 'login', 'client_created', 'plan_generated', 'plan_approved', 'plan_delivered'
    entity_type VARCHAR(50),                     -- e.g., 'client', 'meal_plan', 'article', 'dietitian'
    entity_id UUID,                              -- ID of the affected entity
    
    metadata JSONB,                              -- additional context (e.g., {"client_name": "Priya", "plan_title": "Week 3"})
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_dietitian ON audit_logs(dietitian_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
```

---

## 4. API Design

### Base URL: `/api/v1`

### 4.1 Authentication

```
POST   /api/v1/auth/register        # Dietitian signup
POST   /api/v1/auth/login            # Dietitian login → returns JWT
POST   /api/v1/auth/refresh          # Refresh JWT token
POST   /api/v1/auth/logout           # Invalidate refresh token
GET    /api/v1/auth/me               # Get current dietitian profile
PUT    /api/v1/auth/me               # Update dietitian profile
```

#### Register Request
```json
{
    "email": "neha@example.com",
    "password": "securePass123!",
    "full_name": "Dr. Neha Sharma",
    "phone": "+919876543210"
}
```

#### Login Response
```json
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600,
    "dietitian": {
        "id": "uuid",
        "email": "neha@example.com",
        "full_name": "Dr. Neha Sharma",
        "slug": "dr-neha-sharma",
        "has_whatsapp_setup": false
    }
}
```

### 4.2 Clients

```
GET    /api/v1/clients               # List all clients (with filters, pagination)
POST   /api/v1/clients               # Create new client
GET    /api/v1/clients/:id           # Get client details + profile
PUT    /api/v1/clients/:id           # Update client profile
DELETE /api/v1/clients/:id           # Archive client (soft delete)
GET    /api/v1/clients/:id/adherence # Get adherence stats for a client
```

#### Create Client Request
```json
{
    "full_name": "Priya Kapoor",
    "whatsapp_number": "+919876543210",
    "age": 28,
    "gender": "female",
    "height_cm": 162,
    "weight_kg": 72,
    "target_weight_kg": 60,
    "activity_level": "light",
    "medical_conditions": ["PCOS", "insulin_resistance"],
    "allergies": ["peanuts"],
    "food_preferences": ["vegetarian", "no_onion"],
    "cuisine_preference": "north_indian",
    "dietary_type": "veg",
    "primary_goal": "weight_loss",
    "monthly_food_budget_inr": 8000,
    "daily_calorie_target": 1400,
    "meals_per_day": 5,
    "notes": "Works from home, sedentary. Cooks for herself only."
}
```

### 4.3 Meal Plans

```
POST   /api/v1/clients/:id/plans/generate  # AI generate a new plan
GET    /api/v1/clients/:id/plans           # List plans for a client
GET    /api/v1/plans/:id                    # Get full plan with all days/items
PUT    /api/v1/plans/:id                    # Edit plan (update items)
POST   /api/v1/plans/:id/approve           # Approve → triggers WhatsApp delivery
POST   /api/v1/plans/:id/regenerate        # Regenerate with custom instructions
GET    /api/v1/plans/:id/validations       # Get validation results
```

#### Generate Plan Request
```json
{
    "custom_instructions": "Focus on anti-inflammatory foods. Include more flaxseeds and turmeric.",
    "protocol_id": "uuid-or-null",
    "week_start_date": "2026-06-16"
}
```

#### Plan Response (abbreviated)
```json
{
    "id": "uuid",
    "client_id": "uuid",
    "title": "Week 1 - PCOS Weight Loss",
    "status": "draft",
    "week_start_date": "2026-06-16",
    "avg_daily_calories": 1420,
    "avg_daily_protein_g": 62,
    "avg_daily_carbs_g": 165,
    "avg_daily_fat_g": 52,
    "days": [
        {
            "day_number": 1,
            "day_label": "Monday",
            "total_calories": 1380,
            "meals": [
                {
                    "meal_type": "breakfast",
                    "items": [
                        {
                            "food_name": "Moong dal cheela",
                            "food_name_hindi": "मूंग दाल चीला",
                            "portion_description": "2 medium pieces",
                            "portion_grams": 150,
                            "calories": 180,
                            "protein_g": 12,
                            "carbs_g": 22,
                            "fat_g": 4,
                            "preparation_notes": "Use minimal oil, add green chutney on side"
                        }
                    ]
                }
            ]
        }
    ],
    "validations": [
        {
            "type": "allergen_check",
            "passed": true,
            "message": "No allergens detected"
        },
        {
            "type": "calorie_range",
            "passed": true,
            "message": "Average 1420 cal/day (target: 1400 ±10%)"
        }
    ],
    "generation_metadata": {
        "model": "gpt-4o",
        "tokens_used": 4200,
        "cost_usd": 0.042,
        "duration_ms": 12500
    }
}
```

### 4.4 Protocols

```
GET    /api/v1/protocols             # List dietitian's protocols
POST   /api/v1/protocols             # Create protocol
GET    /api/v1/protocols/:id         # Get protocol details
PUT    /api/v1/protocols/:id         # Update protocol
DELETE /api/v1/protocols/:id         # Delete protocol
```

### 4.5 Articles / Content

```
GET    /api/v1/articles              # List articles (with filter: draft/published)
POST   /api/v1/articles              # Create article
GET    /api/v1/articles/:id          # Get article
PUT    /api/v1/articles/:id          # Update article
POST   /api/v1/articles/:id/publish  # Publish to landing page
POST   /api/v1/articles/:id/broadcast # Broadcast to clients via WhatsApp
DELETE /api/v1/articles/:id          # Delete article (soft)
```

### 4.6 Food Database

```
GET    /api/v1/foods                 # Search food items (with query, category filter)
POST   /api/v1/foods                 # Add custom food item (per dietitian)
GET    /api/v1/foods/:id             # Get food item details
PUT    /api/v1/foods/:id             # Update custom food item
```

### 4.7 Progress Tracking

```
GET    /api/v1/clients/:id/progress  # Get progress history (ordered by date)
POST   /api/v1/clients/:id/progress  # Log weight/measurements
PUT    /api/v1/progress/:id          # Update a progress entry
DELETE /api/v1/progress/:id          # Delete a progress entry
```

#### Log Progress Request
```json
{
    "log_date": "2026-06-15",
    "weight_kg": 70.5,
    "waist_cm": 82.0,
    "notes": "Feeling lighter after week 1"
}
```

#### Progress Response
```json
{
    "history": [
        { "log_date": "2026-06-15", "weight_kg": 70.5, "waist_cm": 82.0, "notes": "Feeling lighter" },
        { "log_date": "2026-06-08", "weight_kg": 72.0, "waist_cm": 84.0, "notes": "Starting" }
    ],
    "summary": {
        "starting_weight": 72.0,
        "current_weight": 70.5,
        "target_weight": 60.0,
        "total_change_kg": -1.5,
        "weeks_tracked": 2
    }
}
```

### 4.8 WhatsApp Webhook

```
GET    /webhook/whatsapp             # Verification challenge (Meta sends this on setup)
POST   /webhook/whatsapp             # Receive incoming messages & status updates
```

### 4.8 Public / Landing Page

```
GET    /p/:slug                      # Dietitian's landing page (SSR HTML)
GET    /p/:slug/articles             # Public article list
GET    /p/:slug/articles/:article_slug  # Public article detail
POST   /p/:slug/intake               # New client intake form submission
```

### 4.9 Dashboard Stats

```
GET    /api/v1/dashboard             # Overview stats for dietitian
```

#### Response
```json
{
    "total_clients": 12,
    "active_clients": 10,
    "plans_this_month": 8,
    "avg_adherence_pct": 72,
    "clients_needing_attention": [
        { "id": "uuid", "name": "Priya", "adherence_pct": 40, "last_interaction": "2026-06-10" }
    ],
    "recent_activity": [
        { "type": "plan_delivered", "client": "Priya", "timestamp": "2026-06-13T10:00:00Z" },
        { "type": "meal_logged", "client": "Riya", "timestamp": "2026-06-13T09:30:00Z" }
    ]
}
```

---

## 5. WhatsApp Integration Architecture

### 5.1 Setup Requirements

- Meta Developer Account
- WhatsApp Business Account (WABA)
- Phone number registered with WhatsApp Business
- Approved message templates (for plan delivery, reminders)
- Webhook URL (must be HTTPS with valid SSL)

### 5.2 Message Flow

```
CLIENT SENDS MESSAGE ON WHATSAPP
        │
        ▼
META CLOUD API ──POST──▶ /webhook/whatsapp
        │
        ▼
WEBHOOK HANDLER
  ├─ Verify signature (X-Hub-Signature-256)
  ├─ Return 200 immediately
  └─ BackgroundTask: process_message()
        │
        ▼
IDENTIFY CLIENT
  ├─ Lookup by from_number in clients table
  ├─ If not found → ignore (or send "not registered" reply)
  └─ Get dietitian_id for this client
        │
        ▼
CLASSIFY INTENT
  ├─ "TODAY" / "today"       → intent: command_today
  ├─ "DONE" / "✅"           → intent: command_done
  ├─ "GROCERY" / "grocery"   → intent: command_grocery
  ├─ "HELP" / "help"         → intent: command_help
  ├─ "SWAP ..." / "I don't have ..."  → intent: command_swap
  ├─ "BOOK" / "book"         → intent: command_book
  ├─ Looks like deviation    → intent: deviation
  └─ Everything else         → intent: question (→ RAG)
        │
        ▼
EXECUTE HANDLER
  ├─ command_today  → Fetch active plan → format today's meals → send
  ├─ command_done   → Create meal_log(status=completed) → send confirmation
  ├─ command_grocery → Fetch active plan → aggregate ingredients → send list
  ├─ command_help   → Send static help text
  ├─ command_swap   → Call AI substitution chain → send suggestion
  ├─ deviation      → Create meal_log(status=deviated, note=...) → acknowledge
  └─ question       → RAG pipeline (search articles + knowledge) → send answer
        │
        ▼
SEND REPLY VIA META CLOUD API
  POST https://graph.facebook.com/v21.0/{phone_number_id}/messages
```

### 5.3 Message Templates (Must Be Pre-Approved by Meta)

| Template Name | Use Case | Variables |
|---|---|---|
| `meal_plan_delivery` | When dietitian approves a plan | `{{client_name}}`, `{{dietitian_name}}`, `{{week_dates}}` |
| `daily_reminder` | Morning reminder with today's meals | `{{client_name}}`, `{{day_label}}`, `{{meals_summary}}` |
| `weekly_summary` | End of week adherence | `{{client_name}}`, `{{adherence_count}}`, `{{total_days}}` |
| `new_article` | Article broadcast | `{{dietitian_name}}`, `{{article_title}}`, `{{article_link}}` |

### 5.4 Rate Limiting & Costs

- Meta allows 1,000 free service conversations/month (business-initiated)
- User-initiated conversations (client messages first) have a 24-hour window for free-form replies
- Template messages outside the 24-hour window cost ~₹0.35-0.70 per message
- Rate limit: 80 messages/second (more than enough for MVP)

---

## 6. AI Pipeline Design

### 6.1 Evolution Path

```
Phase 4 (MVP):     prompt → Gemini API (google-genai) → structured JSON → rule-based validation
Phase 9:           prompt → LangChain ChatGoogleGenerativeAI → structured output → tracing via LangSmith
Phase 10:          LangGraph StateGraph → multi-node workflow → stateful validation + retry
```

### 6.2 Plan Generation — MVP (Simple Prompt + Structured JSON)

```python
# backend/app/ai/plan_generator.py (Phase 4 — no LangChain)

from google import genai
from app.config import settings
from app.schemas.meal_plan import GeneratedPlan

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def generate_meal_plan(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None
) -> GeneratedPlan:
    prompt = build_prompt(client_profile, food_items, custom_instructions)
    
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[prompt],
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "temperature": 0.7,
        }
    )
    
    plan_data = json.loads(response.text)
    plan = GeneratedPlan.model_validate(plan_data)  # Pydantic validation
    
    validations = run_validations(plan, client_profile)
    return plan, validations
```

> **Note:** Gemini's `response_mime_type="application/json"` is equivalent to OpenAI's `response_format={"type": "json_object"}`. Both enforce structured JSON output.
>
> **Fallback:** If Gemini fails or hits rate limits, the service should retry with OpenAI (`openai` package) using the same prompt. Keep both clients configured.

### 6.3 Plan Generation — Phase 10 (LangGraph)

After the simple version works, migrate to LangGraph for multi-step orchestration:

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ PARSE       │ Extract client profile
                    │ PROFILE     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ RETRIEVE    │ Fetch protocol, previous plans
                    │ CONTEXT     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ GENERATE    │ LLM call → structured JSON
                    │ PLAN        │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ VALIDATE    │ Allergens, calories, preferences
                    │ SAFETY      │
                    └──────┬──────┘
                     ┌─────┴─────┐
                 PASS ▼      FAIL ▼
            ┌────────────┐  ┌────────────┐
            │ FORMAT     │  │ RETRY (2x) │
            │ OUTPUT     │  └─────┬──────┘
            └─────┬──────┘        │
                  ▼               ▼
            ┌──────────────────────┐
            │        END           │
            └──────────────────────┘
```

### 6.2 Plan Generation Prompt Strategy

```
SYSTEM PROMPT:
You are a clinical nutrition AI assistant working for {dietitian_name}.
You generate structured Indian meal plans.

RULES:
1. Use Indian food items with local names (roti, dal, sabzi, not "flatbread")
2. Respect ALL allergies — zero tolerance
3. Stay within calorie target ±10%
4. Ensure macro distribution matches protocol (or default 30/40/30 P/C/F)
5. Vary meals across the 7 days (no exact repetition)
6. Consider budget constraints when selecting ingredients
7. Include preparation notes for complex items
8. Output MUST be valid JSON matching the provided schema

CLIENT PROFILE:
{structured_client_data}

PROTOCOL (if any):
{protocol_data}

CUSTOM INSTRUCTIONS:
{dietitian_instructions}

OUTPUT SCHEMA:
{json_schema}
```

### 6.3 Substitution Chain (for WhatsApp SWAP command)

```
Input: "I don't have paneer" + client profile + current plan context
  │
  ▼
1. Identify the food item being swapped (paneer)
2. Find the meal context (which meal, what macros it contributes)
3. Generate alternatives that:
   - Match similar macros (protein-rich vegetarian)
   - Don't violate allergies
   - Are culturally appropriate
   - Are within budget
4. Return: "Try tofu (same protein, lower fat) or cottage cheese.
   If neither works, 2 boiled eggs would also work. Want me to update your plan?"
```

### 6.4 RAG Pipeline (for WhatsApp Questions)

```
Client asks: "Is curd okay at night?"
  │
  ▼
1. Generate embedding for question
2. Search article_embeddings (cosine similarity, top 3)
3. If relevant chunks found (similarity > 0.7):
   - Answer grounded in dietitian's published content
   - Cite the article: "According to Dr. Neha's article on dairy timing..."
4. If no relevant chunks:
   - Answer from general nutrition knowledge
   - Add disclaimer: "This is general advice. Check with your nutritionist for personalized guidance."
```

---

## 7. Authentication & Authorization

### 7.1 Dietitian Auth (JWT)

- **Registration:** Email + password → bcrypt hash → store → issue JWT
- **Login:** Email + password → verify hash → issue access_token (1h) + refresh_token (30d)
- **Access token:** Short-lived (1 hour), in Authorization header
- **Refresh token:** Long-lived (30 days), stored in `refresh_tokens` table as SHA-256 hash, single-use rotation
- **Token rotation:** On `/auth/refresh`, the old refresh token is revoked (`revoked_at` set) and a new one is issued (`replaced_by` points to the new token). If a revoked token is reused, revoke the entire family (potential token theft).
- **Logout:** Revokes the refresh token (sets `revoked_at`)
- **All `/api/v1/*` routes:** Require valid JWT except `/auth/register` and `/auth/login`

### 7.2 Client Auth (WhatsApp)

- No traditional auth. Client is identified by their WhatsApp number.
- When a message arrives, lookup `clients` by `whatsapp_number` → get `dietitian_id`
- If number not found → ignore or send "You're not registered" message
- Multi-tenant isolation: Every query includes `dietitian_id` filter

### 7.3 Multi-Tenant Isolation

Every database query on tenant-scoped tables MUST include `dietitian_id` filter:

```python
# CORRECT — always filter by dietitian
clients = db.query(Client).filter(
    Client.dietitian_id == current_dietitian.id
).all()

# WRONG — never expose cross-tenant data
clients = db.query(Client).all()  # DO NOT DO THIS
```

---

## 8. Structured Logging

Structured JSON logging from Day 1. Every log line includes context for production debugging.

### 8.1 Setup

`backend/app/core/logger.py` — configure Python's `logging` module with JSON formatter.

```python
# backend/app/core/logger.py
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

### 8.2 Request ID Middleware

Add middleware in `main.py` that:
1. Generates a UUID `request_id` for every incoming request (or reads `X-Request-ID` header if present)
2. Sets `request_id_ctx` and `correlation_id_ctx` context vars
3. Sets `user_id_ctx` after authentication (via dependency)
4. Adds `X-Request-ID` to response headers

```python
# In main.py — add before router registration
from app.core.logger import setup_logging, request_id_ctx, correlation_id_ctx
import uuid

setup_logging(settings.LOG_LEVEL)

@app.middleware("http")
async def logging_middleware(request, call_next):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    cid = request.headers.get("X-Correlation-ID", rid)
    request_id_ctx.set(rid)
    correlation_id_ctx.set(cid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response
```

### 8.3 Usage Pattern

```python
# In any service file:
from app.core.logger import get_logger
logger = get_logger(__name__)

async def generate_meal_plan(client, ...):
    logger.info("Starting plan generation", extra={"client_id": str(client.id)})
    # ... work ...
    logger.info("Plan generated", extra={"tokens": tokens_used, "duration_ms": elapsed})
```

**Output (structured JSON):**
```json
{"timestamp": "2026-06-15 10:30:00", "level": "INFO", "logger": "app.services.plan_service", "message": "Plan generated", "request_id": "abc-123", "user_id": "diet-456", "correlation_id": "abc-123"}
```

### 8.4 What to Log

| Event | Level | Where |
|---|---|---|
| Request start/end + duration | INFO | Middleware |
| Auth success/failure | INFO/WARN | auth_service |
| Client CRUD operations | INFO | client_service |
| AI plan generation start/end + tokens + cost | INFO | plan_generator |
| AI validation results | INFO | plan_validator |
| WhatsApp webhook received | INFO | webhook router |
| WhatsApp message sent/failed | INFO/ERROR | whatsapp_service |
| Unhandled exceptions | ERROR | Exception handler |

> [!NOTE]
> Keep logging simple — Python stdlib `logging` + JSON formatter + `contextvars`. No need for Loguru or structlog at MVP scale.

---

## 9. Project Structure

```
nutriplan/
├── docker-compose.yml
├── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions: lint → test → build → deploy
├── docs/
│   ├── prd.md
│   ├── technical_spec.md
│   └── implementation_plan.md
├── backend/
│   ├── pyproject.toml               # Dependencies (Poetry or pip)
│   ├── alembic.ini                  # DB migrations config
│   ├── alembic/
│   │   └── versions/               # Migration files
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings (env vars, Pydantic BaseSettings)
│   │   ├── database.py              # DB connection, session
│   │   ├── dependencies.py          # FastAPI dependencies (get_db, get_current_user)
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── dietitian.py
│   │   │   ├── refresh_token.py
│   │   │   ├── client.py
│   │   │   ├── meal_plan.py
│   │   │   ├── meal_log.py
│   │   │   ├── progress_log.py
│   │   │   ├── protocol.py
│   │   │   ├── article.py
│   │   │   ├── food_item.py
│   │   │   ├── whatsapp_message.py
│   │   │   └── audit_log.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── client.py
│   │   │   ├── meal_plan.py
│   │   │   ├── protocol.py
│   │   │   ├── article.py
│   │   │   └── food_item.py
│   │   ├── core/                    # Cross-cutting concerns
│   │   │   ├── __init__.py
│   │   │   └── logger.py            # Structured JSON logging + context vars
│   │   ├── routers/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── v1/                  # Versioned API routes (/api/v1/*)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── clients.py
│   │   │   │   ├── plans.py
│   │   │   │   ├── protocols.py
│   │   │   │   ├── articles.py
│   │   │   │   ├── foods.py
│   │   │   │   └── dashboard.py
│   │   │   ├── webhook.py           # WhatsApp webhook handler (not versioned)
│   │   │   └── public.py            # Landing page routes (not versioned)
│   │   ├── services/                # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── client_service.py
│   │   │   ├── plan_service.py
│   │   │   ├── whatsapp_service.py  # Send/receive WhatsApp messages
│   │   │   ├── content_service.py
│   │   │   └── food_service.py
│   │   ├── ai/                      # AI/LLM layer
│   │   │   ├── __init__.py
│   │   │   ├── plan_generator.py    # LangGraph plan generation workflow
│   │   │   ├── plan_validator.py    # Safety validation checks
│   │   │   ├── substitution.py      # Food substitution chain
│   │   │   ├── rag.py               # RAG pipeline for Q&A
│   │   │   ├── article_drafter.py   # AI article drafting
│   │   │   ├── prompts/             # Prompt templates
│   │   │   │   ├── plan_generation.py
│   │   │   │   ├── substitution.py
│   │   │   │   └── qa.py
│   │   │   └── embeddings.py        # Embedding generation & search
│   │   ├── whatsapp/                # WhatsApp-specific logic
│   │   │   ├── __init__.py
│   │   │   ├── intent_classifier.py # Classify incoming messages
│   │   │   ├── message_formatter.py # Format plans, lists for WhatsApp
│   │   │   ├── handlers/            # One handler per intent
│   │   │   │   ├── today.py
│   │   │   │   ├── done.py
│   │   │   │   ├── swap.py
│   │   │   │   ├── grocery.py
│   │   │   │   ├── help.py
│   │   │   │   ├── deviation.py
│   │   │   │   └── question.py
│   │   │   └── templates.py         # WhatsApp template message builders
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py          # JWT, password hashing
│   │       └── formatting.py        # Meal plan formatters
│   ├── tests/
│   │   ├── conftest.py              # Fixtures, test DB setup
│   │   ├── test_auth.py
│   │   ├── test_clients.py
│   │   ├── test_plans.py
│   │   ├── test_webhook.py          # WhatsApp webhook tests (mocked)
│   │   ├── test_plan_validator.py
│   │   └── test_intent_classifier.py
│   └── seed/
│       └── food_items.json          # Initial Indian food database (200+ items)
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css                # Design system: tokens, global styles
│   │   ├── api/                     # API client (fetch wrapper)
│   │   ├── hooks/                   # React hooks
│   │   ├── contexts/                # Auth context, etc.
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── ClientsPage.tsx
│   │   │   ├── ClientDetailPage.tsx
│   │   │   ├── PlanEditorPage.tsx
│   │   │   ├── ProtocolsPage.tsx
│   │   │   ├── ArticlesPage.tsx
│   │   │   ├── ArticleEditorPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   └── components/
│   │       ├── layout/
│   │       ├── clients/
│   │       ├── plans/
│   │       ├── articles/
│   │       └── ui/                  # Buttons, inputs, cards, modals
│   └── public/
└── README.md
```

---

## 10. Deployment

### 9.1 Local Development

```bash
# Start everything
docker-compose up -d

# Services:
# - backend:  http://localhost:8000 (FastAPI + auto-reload)
# - frontend: http://localhost:5173 (Vite dev server)
# - postgres: localhost:5432
# - redis:    localhost:6379
```

### 9.2 Production (Railway / Render)

| Service | Provider | Tier |
|---|---|---|
| Backend (FastAPI) | Railway or Render | Free/Starter |
| Frontend (React) | Vercel or Netlify | Free |
| PostgreSQL | Railway or Supabase | Free tier (500MB) |
| Redis | Railway or Upstash | Free tier |

### 9.3 Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/nutriplan

# Redis
REDIS_URL=redis://localhost:6379

# App
LOG_LEVEL=INFO                        # DEBUG in dev, INFO in prod

# Auth
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Gemini (primary — free tier)
GEMINI_API_KEY=AIza...

# OpenAI (fallback — paid)
OPENAI_API_KEY=sk-...                # Optional for MVP, used as fallback

# WhatsApp (Meta Cloud API)
WHATSAPP_VERIFY_TOKEN=your-verify-token
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_BUSINESS_ACCOUNT_ID=9876543210
WHATSAPP_ACCESS_TOKEN=EAAx...

# LangSmith (optional — Phase 9+)
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=nutriplan
```
