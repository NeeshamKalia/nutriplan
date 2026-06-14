# NutriPlan — Product Requirements Document (PRD)

**Version:** 1.0  
**Last Updated:** 2026-06-13  
**Status:** Draft — Awaiting Review  

---

## 1. Product Vision

### One-Line Pitch

**NutriPlan is an AI-powered practice OS for Indian nutritionists — where AI drafts personalized meal plans in the dietitian's style, clients interact entirely via WhatsApp, and a branded landing page with blog drives organic growth.**

### Problem Statement

Thousands of Indian nutritionists manage their practice using a fragmented stack:

| Current Tool | What It's Used For | Pain |
|---|---|---|
| **Canva** | Creating meal plan PDFs | Manual, time-consuming (30-60 min per plan), no reusability |
| **WhatsApp** | All client communication | Unstructured, data gets buried, no tracking, boundary issues |
| **Excel/Google Sheets** | Client tracking, food databases | No automation, no insights, manual updates |
| **Phone/memory** | Client health profiles | Not scalable, details forgotten, no history |

**Result:** A nutritionist with 15+ clients spends more time on admin than on actual nutrition counseling. Scaling beyond 20 clients becomes unsustainable without staff.

### Solution

NutriPlan replaces this fragmented workflow with three integrated surfaces:

1. **Dietitian Dashboard (Web)** — Manage clients, generate AI-drafted meal plans, review & approve, write articles, track adherence
2. **Client WhatsApp Bot** — Clients receive plans, track meals, request substitutions, get grocery lists, read articles — all without downloading an app
3. **Branded Landing Page** — Public page with blog/articles for SEO, new client intake form, credentials, testimonials

### Target Market

**Primary:** Independent and part-time nutritionists/dietitians in India (estimated 50,000+ practicing, growing post-COVID health awareness)

**Characteristics:**
- Solo practitioners or small clinics (1-3 dietitians)
- Currently using WhatsApp + Canva + Excel
- Price-sensitive (willing to pay ₹499-1499/month for a tool that saves hours)
- Clients are primarily urban Indian, communicating in English/Hindi
- Focus on weight management, PCOS, thyroid, diabetes management, general wellness

---

## 2. User Personas

### Persona 1: Dr. Neha (The Dietitian) — Primary Customer

- **Age:** 28-40
- **Profile:** Certified nutritionist (BSc/MSc Nutrition or equivalent), 2-10 years experience
- **Practice:** Part-time (employed elsewhere) or full-time independent
- **Clients:** 5-30 active clients
- **Tech comfort:** Uses smartphone daily, comfortable with web apps, not a developer
- **Current workflow:** Canva + WhatsApp + Excel + memory
- **Pain:** Spends 30-60 min creating each meal plan, forgets client details, can't track adherence, no professional online presence
- **Willingness to pay:** ₹499-999/month if it saves 5+ hours/week
- **Success metric:** "I can manage 2x the clients in the same time"

### Persona 2: Priya (The Client) — End User (Does NOT Pay)

- **Age:** 22-45
- **Profile:** Urban Indian, health-conscious or managing a condition (PCOS, thyroid, diabetes, weight loss)
- **Tech comfort:** Uses WhatsApp daily, rarely downloads new apps
- **Current experience:** Gets a Canva PDF on WhatsApp, forgets about it by Wednesday
- **Pain:** Plans feel generic, no accountability, can't easily ask for substitutions
- **What she wants:** Daily reminders, easy tracking, quick answers when she can't find an ingredient
- **Does NOT want:** Another app to download, another login to remember

---

## 3. User Stories

### 3.1 Dietitian Stories — Dashboard

#### Authentication & Onboarding
| ID | Story | Priority |
|---|---|---|
| D-AUTH-01 | As a dietitian, I can sign up with email and password so I can create my practice | P0 |
| D-AUTH-02 | As a dietitian, I can log in to my dashboard securely | P0 |
| D-AUTH-03 | As a dietitian, I can set up my practice profile (name, specializations, photo, bio) | P0 |
| D-AUTH-04 | As a dietitian, I can connect my WhatsApp Business number to send client messages | P0 |

#### Client Management
| ID | Story | Priority |
|---|---|---|
| D-CLIENT-01 | As a dietitian, I can add a new client with their WhatsApp number | P0 |
| D-CLIENT-02 | As a dietitian, I can fill in a client's health profile (conditions, allergies, goals, preferences, budget, lifestyle) | P0 |
| D-CLIENT-03 | As a dietitian, I can view a list of all my clients with status indicators | P0 |
| D-CLIENT-04 | As a dietitian, I can view a single client's full profile, plan history, and adherence | P0 |
| D-CLIENT-05 | As a dietitian, I can edit a client's profile when their conditions or goals change | P1 |
| D-CLIENT-06 | As a dietitian, I can archive/deactivate a client who has completed their program | P2 |

#### AI Meal Plan Generation
| ID | Story | Priority |
|---|---|---|
| D-PLAN-01 | As a dietitian, I can click "Generate Plan" for a client and get an AI-drafted 7-day meal plan based on their profile | P0 |
| D-PLAN-02 | As a dietitian, the generated plan shows structured meals (breakfast, mid-morning, lunch, evening snack, dinner) with food items, portions, and macros for each day | P0 |
| D-PLAN-03 | As a dietitian, I can edit any item in the generated plan (swap food, adjust portion, change timing) before approving | P0 |
| D-PLAN-04 | As a dietitian, I can approve a plan which triggers delivery to the client via WhatsApp | P0 |
| D-PLAN-05 | As a dietitian, I can reject a plan and regenerate with additional instructions ("make it more South Indian", "reduce dairy") | P1 |
| D-PLAN-06 | As a dietitian, I can save a plan framework as a protocol template for reuse with similar clients | P1 |
| D-PLAN-07 | As a dietitian, I can generate a plan based on a saved protocol template | P1 |
| D-PLAN-08 | As a dietitian, I see an AI safety check before approval (allergen warnings, calorie validation, nutritional balance) | P1 |
| D-PLAN-09 | As a dietitian, I can view a plan's cost estimate based on approximate Indian grocery prices | P2 |

#### Adherence & Tracking
| ID | Story | Priority |
|---|---|---|
| D-TRACK-01 | As a dietitian, I can see which meals each client completed, skipped, or deviated from | P1 |
| D-TRACK-02 | As a dietitian, I can see an adherence overview across all clients (who needs attention) | P1 |
| D-TRACK-03 | As a dietitian, I can see a weekly summary of a client's adherence | P1 |
| D-TRACK-04 | As a dietitian, I receive alerts when a client's adherence drops below a threshold | P2 |

#### Content & Articles
| ID | Story | Priority |
|---|---|---|
| D-CONTENT-01 | As a dietitian, I can write a health article/tip in a rich text editor | P1 |
| D-CONTENT-02 | As a dietitian, I can publish an article to my branded landing page | P1 |
| D-CONTENT-03 | As a dietitian, I can broadcast an article summary to all active clients via WhatsApp | P2 |
| D-CONTENT-04 | As a dietitian, AI can help me draft an article from a topic/title | P2 |
| D-CONTENT-05 | As a dietitian, my published articles are indexed by the AI so clients can ask about them via WhatsApp | P2 |

#### Landing Page
| ID | Story | Priority |
|---|---|---|
| D-LANDING-01 | As a dietitian, I have a public landing page at a unique URL (e.g., nutriplan.app/dr-neha) | P1 |
| D-LANDING-02 | As a dietitian, my landing page shows my profile, specializations, and published articles | P1 |
| D-LANDING-03 | As a dietitian, new leads can fill an intake form on my landing page that creates a client record | P2 |
| D-LANDING-04 | As a dietitian, I can add testimonials to my landing page | P3 |

### 3.2 Client Stories — WhatsApp

| ID | Story | Priority |
|---|---|---|
| C-WA-01 | As a client, I receive my approved meal plan on WhatsApp in a clear, formatted message | P0 |
| C-WA-02 | As a client, I can see today's meals by sending "TODAY" | P0 |
| C-WA-03 | As a client, I can mark a meal as done by replying "DONE" or "✅" | P1 |
| C-WA-04 | As a client, I can request a substitution ("I don't have paneer") and get an AI-suggested alternative within my plan's constraints | P1 |
| C-WA-05 | As a client, I can get my weekly grocery list by sending "GROCERY" | P1 |
| C-WA-06 | As a client, I can log a deviation ("had pizza for dinner") which is noted without judgment | P1 |
| C-WA-07 | As a client, I can ask a nutrition question and get an AI answer grounded in my dietitian's knowledge base | P2 |
| C-WA-08 | As a client, I receive daily morning reminders with today's plan | P2 |
| C-WA-09 | As a client, I receive a weekly adherence summary ("You followed 5/7 days! 🎉") | P2 |
| C-WA-10 | As a client, I can send "HELP" to see all available commands | P0 |
| C-WA-11 | As a client, I receive new article notifications from my dietitian | P2 |
| C-WA-12 | As a client, I can request a consultation booking by sending "BOOK" | P3 |

### 3.3 System Stories

| ID | Story | Priority |
|---|---|---|
| S-AI-01 | The system validates every AI-generated plan against the client's allergen list before showing it to the dietitian | P1 |
| S-AI-02 | The system validates calorie totals per day against the client's target range | P1 |
| S-AI-03 | The system uses Indian food items and names (dal, roti, sabzi, not "lentil soup, flatbread, vegetable curry") | P0 |
| S-AI-04 | The system tracks token usage and cost per AI generation for monitoring | P1 |
| S-WA-01 | The system handles WhatsApp webhook verification (GET challenge) | P0 |
| S-WA-02 | The system processes incoming WhatsApp messages and routes to appropriate handler | P0 |
| S-WA-03 | The system sends WhatsApp messages using approved templates for plan delivery | P0 |
| S-WA-04 | The system sends session messages for conversational AI (substitutions, questions) | P1 |
| S-SEC-01 | The system isolates data between dietitians (multi-tenant) | P0 |
| S-SEC-02 | The system never exposes one dietitian's client data to another | P0 |
| S-SEC-03 | The system stores sensitive health data encrypted at rest | P1 |

---

## 4. Feature Requirements by Surface

### 4.1 Dietitian Dashboard (Web App)

**P0 — Must Have:**
- Dietitian authentication (signup, login, logout)
- Practice profile setup
- Client CRUD (create, read, update)
- Client health profile form (structured: conditions, allergies, food preferences, cuisine type, budget, goals, lifestyle/activity, meal timing preferences)
- AI meal plan generation from client profile
- Plan review/edit interface (structured table: 7 days × 5 meals × items/portions/macros)
- Plan approve → trigger WhatsApp delivery
- Plan history per client

**P1 — Should Have:**
- Adherence dashboard (per client + overview)
- Protocol templates (save/load plan frameworks)
- Content editor (rich text, publish to landing page)
- AI safety validation on generated plans
- Plan regeneration with custom instructions

**P2 — Nice to Have:**
- AI article drafting assistance
- WhatsApp broadcast for articles
- Client intake from landing page
- Cost estimation per plan
- Adherence alerts

### 4.2 Client WhatsApp Bot

**P0 — Must Have:**
- Receive approved plan (formatted message)
- `TODAY` command — show today's meals
- `HELP` command — show available commands
- Webhook handler for incoming messages

**P1 — Should Have:**
- `DONE` / `✅` — mark meal as completed
- `SWAP [item]` — AI substitution within constraints
- `GROCERY` — weekly grocery list
- Deviation logging (free text)

**P2 — Nice to Have:**
- Daily morning reminders
- Weekly adherence summary
- Nutrition Q&A (RAG from dietitian's articles)
- Article broadcast reception
- `BOOK` — consultation booking

### 4.3 Branded Landing Page

**P1 — Should Have:**
- Unique URL per dietitian
- Profile display (name, photo, specializations, bio)
- Published articles / blog list
- Article detail page

**P2 — Nice to Have:**
- Client intake form (creates a new client record)
- Testimonials section
- Consultation booking CTA
- SEO meta tags per page

---

## 5. Non-Functional Requirements

| Category | Requirement | Priority |
|---|---|---|
| **Performance** | AI plan generation completes in < 30 seconds | P0 |
| **Performance** | WhatsApp message response time < 5 seconds for commands, < 15 seconds for AI responses | P1 |
| **Performance** | Dashboard pages load in < 2 seconds | P1 |
| **Scalability** | Support 50 dietitians with 30 clients each (1,500 clients) in MVP | P1 |
| **Security** | JWT-based auth with refresh tokens for dashboard | P0 |
| **Security** | WhatsApp webhook signature verification | P0 |
| **Security** | Multi-tenant data isolation (dietitian can only see their clients) | P0 |
| **Security** | Health data encrypted at rest | P1 |
| **Reliability** | Webhook endpoint must return 200 within 5s (WhatsApp requirement) | P0 |
| **Reliability** | Failed WhatsApp deliveries are retried and logged | P1 |
| **Deployment** | Dockerized (docker-compose for local, single container for deploy) | P0 |
| **Deployment** | CI/CD pipeline (GitHub Actions: lint → test → build → deploy) | P0 |
| **Deployment** | Live URL accessible on internet | P0 |
| **Testing** | Unit tests for core business logic (plan validation, macro calculation, allergen check) | P0 |
| **Testing** | Integration tests for API endpoints | P1 |
| **Testing** | WhatsApp webhook handler tests (mock incoming messages) | P1 |
| **Monitoring** | Request logging with structured logs | P1 |
| **Monitoring** | AI token usage and cost tracking per generation | P1 |
| **Monitoring** | LLM observability (LangSmith or Langfuse traces) | P2 |

---

## 6. Scope Boundaries

### In Scope (MVP)
- Single dietitian type (individual practitioner)
- English language (Hindi food names in the food database, but UI and bot in English)
- 7-day meal plans with 5 meals per day
- WhatsApp as the only client channel
- Indian food database (curated, 200-500 items)
- OpenAI / Gemini API for generation (configurable)
- Web dashboard on desktop (responsive but not mobile-optimized in MVP)

### Out of Scope (MVP)
- Mobile app for dietitians
- Multi-language bot (Hindi/Tamil/etc.)
- Payment processing / subscription billing
- Video consultations
- Wearable device integration
- Comprehensive IFCT food database (full 6,000+ items)
- Multi-dietitian team accounts
- Client-to-client community features
- Automated social media posting
- White-label / custom domain for landing page

---

## 7. Success Metrics

### Product Metrics (for your wife to validate)
- Time to create a meal plan: **< 5 minutes** (vs. 30-60 min on Canva)
- Client WhatsApp engagement: **> 3 interactions/week** per client
- Dietitian can manage **15+ clients** without feeling overwhelmed

### Technical Metrics (for your resume)
- AI plan generation: **< 30 seconds**
- WhatsApp command response: **< 5 seconds**
- Test coverage: **> 70%** on core business logic
- Zero allergen violations in generated plans (evaluation pipeline)
- Clean Git history with meaningful commits

### Portfolio Metrics
- Live deployed URL
- Demo video (3 min)
- Blog post explaining architecture
- README with architecture diagram
- Exemplary commit history with feature branches

---

## 8. Compliance & Safety Notes

- Generated meal plans are **educational drafts**, not medical prescriptions
- Dietitian must review and approve every plan before client delivery
- Bot responses include a disclaimer when answering health questions
- No diagnosis or treatment recommendations from AI
- Client health data is stored per-dietitian in isolated tenants
- WhatsApp messages comply with Meta's Business messaging policies
- Published articles carry the dietitian's name, not "AI-generated"

---

## 9. Revenue Model (Conceptual — Not Implemented in MVP)

| Tier | Price | Clients | Features |
|---|---|---|---|
| Free Trial | ₹0 / 14 days | 3 clients | All features |
| Starter | ₹499/month | 15 clients | Dashboard + WhatsApp + landing page |
| Pro | ₹999/month | 50 clients | + protocols + AI article drafting + priority support |
| Clinic | ₹1999/month | Unlimited + 3 dietitians | + team features + analytics |

> [!NOTE]
> Revenue model is conceptual. MVP has no paywall — all features are available for portfolio demonstration.
