# NutriPlan — Product Analysis & Core Idea

## The Market Right Now

### What Already Exists (India-focused)

| Product | Model | AI? | Price | Gap |
|---------|-------|-----|-------|-----|
| **Zoconut** | B2B (dietitian-first) | Template-based, no real AI | Waitlist/demo-based | No AI generation, no intelligence in plans |
| **Nutrena** | B2B | Basic, WhatsApp integration | INR pricing | Workflow tool, not an AI co-pilot |
| **Ntuitive** | B2B (clinical) | No | — | Clinical-only, IFCT data, no AI |
| **Clinicia** | B2B (practice mgmt) | No | — | EMR-focused, not nutrition-specific AI |
| **ReeCoach** | B2B2C | Some AI | — | AI is tracking-focused, not plan-generation |
| **Kore App** | B2B | No | — | Consultation platform, no AI |

### What Already Exists (Global)

| Product | AI? | Price | Gap |
|---------|-----|-------|-----|
| **Foodzilla** | ✅ AI meal plans in 60s | $37/mo | Generic AI, not protocol-aware, no Indian food DB |
| **Nutrium** | ❌ | $25/mo | Clinical precision but zero AI |
| **NutriAdmin** | ❌ | $21/mo | Admin/CRM focus, no AI |
| **Practice Better** | Basic | $25-79/mo | All-in-one but AI is an afterthought |

---

## The Gap Nobody Has Filled

> **No tool gives a dietitian an AI that learns THEIR method.**

Every existing AI tool does one of these:
1. **Generic AI** — generates a "1500 cal plan" like ChatGPT would (Foodzilla)
2. **No AI at all** — just templates and databases (Zoconut, Nutrium, NutriAdmin)
3. **Tracking AI** — tells you what you ate, not what you should eat (MyFitnessPal, Healthify)

### What's Missing:

A dietitian has a **method**. Your wife doesn't just calculate calories — she has:
- Preferred food combinations for hypothyroid clients
- Specific meal timing approaches
- Go-to substitutions for common restrictions
- Cultural food knowledge (North Indian vs South Indian diets)
- Phase-based approaches (detox week → building week → maintenance)

**No tool captures and amplifies this expertise.** The AI should draft plans that look like *she* wrote them, not like ChatGPT wrote them.

---

## The Verdict: B2B First, With Client Portal

### Why NOT B2C (marketplace where users find dietitians):

| Problem | Why it kills you |
|---------|-----------------|
| Chicken-and-egg | Need both dietitians AND users from day 1 |
| Competing with Practo/Healthify | They have crores in funding, you have weekends |
| User acquisition cost | You'd spend more on marketing than building |
| No moat | Anyone can list dietitians |
| Scope explosion | Payments, reviews, matching algorithm, dispute resolution |
| For resume | A marketplace is a CRUD app with extra steps — not impressive |

### Why B2B (dietitian manages their own clients):

| Advantage | Why it works |
|-----------|-------------|
| Single buyer | The dietitian decides and pays |
| They bring clients | You don't need to acquire end-users |
| Real workflow problem | Canva + WhatsApp + Excel is painful |
| AI is the moat | This is where your skills shine |
| Wife is User #0 | Instant feedback loop |
| Resume gold | Multi-tenant SaaS, RBAC, AI workflow, structured output |
| Buildable in 13 weeks | Focused scope |

### The Client Portal Is Still There

The dietitian is the customer. The client portal is a **feature** of the dietitian's product, not a separate product. Think of it like Shopify: the merchant is the customer, the buyer sees the merchant's store.

---

## The Core Idea

### One-Line Pitch

> **NutriPlan is an AI-powered practice OS for nutritionists — where AI drafts personalized Indian meal plans in the dietitian's style, and clients get a beautiful portal to follow their plans, track progress, and stay connected.**

### The USP (What Makes This Different)

**"AI that works FOR the dietitian, not INSTEAD of the dietitian."**

| What ChatGPT Does | What NutriPlan Does |
|--------------------|--------------------|
| Generic advice anyone can get | Plans grounded in the dietitian's own protocols & preferences |
| One-shot answers, no memory | Knows the client's full history, allergies, conditions, progress |
| Text blob output | Structured meal plan: meals × days × macros × portions × timings |
| No accountability | Client tracks adherence, dietitian sees dashboard |
| No professional workflow | Draft → Review → Approve → Deliver → Track → Iterate |
| Can't monetize for the dietitian | Dietitian charges clients, NutriPlan charges the dietitian |

### The Workflow

```
1. Dietitian signs up → creates practice profile
2. Adds a client → client fills intake form (health, goals, allergies, budget, cuisine, lifestyle)
3. Dietitian clicks "Generate Plan" → AI drafts a 7-day meal plan
   ↳ AI uses: client profile + dietitian's saved protocols + Indian food DB
   ↳ Output: structured table, not a text blob
4. Dietitian reviews, tweaks portions/substitutions, approves
5. Client gets notified → sees plan in their portal
6. Client follows plan → checks off meals → logs deviations
7. Client can ask AI: "I don't have paneer today" → AI suggests equivalent swap within plan constraints
8. Weekly check-in: dietitian sees adherence dashboard
9. Dietitian generates next week's plan → AI pre-fills based on what worked
10. Repeat
```

### Client Experience: WhatsApp-First (No Web Login)

Clients never need to download an app or visit a website. Everything happens on WhatsApp:

| Client Action | How It Works on WhatsApp |
|--------------|------------------------|
| **View meal plan** | Receives formatted daily plan message each morning |
| **Track meals** | Replies "DONE" or "✅" to mark meals complete |
| **Request swap** | "I don't have paneer" → AI suggests equivalent within plan constraints |
| **Get grocery list** | Replies "GROCERY" → receives aggregated weekly list with quantities |
| **Log deviations** | "Had pizza for dinner" → logged, no judgment, visible to dietitian |
| **Ask questions** | "Is curd okay at night?" → AI answers from dietitian's knowledge base |
| **Get content** | Receives dietitian's new articles/tips as WhatsApp broadcast |
| **Book consultation** | Replies "BOOK" → gets available slots or booking link |

**Tech:** WhatsApp Business Cloud API + webhooks + message templates

### Content & Blog Layer

Dietitians can publish health articles that serve three purposes:

1. **Client engagement** — Tips broadcast to clients via WhatsApp ("5 thyroid-friendly snacks under ₹50")
2. **SEO & discovery** — Published on dietitian's branded landing page → brings in organic leads from Google
3. **RAG knowledge base** — Articles feed the AI, so when clients ask questions, the bot references the dietitian's own published content

**Workflow:** Dietitian writes in dashboard (AI assists drafting from a topic) → publishes to landing page → optionally broadcasts to WhatsApp clients

### Branded Landing Page (Public)

Each dietitian gets a public page (nutriplan.in/dietitian-name) with:
- About / credentials / services
- Published articles & blog
- New client intake form
- Testimonials
- Consultation booking
- Contact via WhatsApp

This replaces a traditional client portal — clients interact via WhatsApp, new leads discover via the landing page.

### The Dietitian Dashboard Features (Web App)

- Client list with status indicators (on-track / falling off / needs attention)
- AI meal plan generator with client context
- Protocol library (save your preferred approaches as templates)
- Client intake form builder
- Adherence overview across all clients
- Revenue/appointment tracking (simple)
- WhatsApp notification integration (send plan summaries)

---

## MVP Scope (What to Build in 13 Weeks)

> [!IMPORTANT]
> The MVP must be demo-able and tell the full story, but it does NOT need to handle every edge case.

### Three Surfaces

| Surface | Tech | Who |
|---------|------|-----|
| **Dietitian Dashboard** | React web app | Nutritionist (paying user) |
| **Client WhatsApp Bot** | WhatsApp Business Cloud API + webhooks | End client |
| **Branded Landing Page** | SSR/static page per dietitian | Public / new leads |

### Must Have (Weeks 1-5)
- [ ] Auth (dietitian signup/login)
- [ ] Client management (add client, intake form with health/allergy/preference/budget data)
- [ ] AI meal plan generation (structured 7-day plan from client profile + Indian food context)
- [ ] Dietitian review & edit interface (modify portions, swap items, approve)
- [ ] WhatsApp integration — send approved plan to client, receive basic commands (DONE, SWAP, GROCERY, TODAY)
- [ ] Conversational AI on WhatsApp for substitution requests
- [ ] Basic Indian food database (curated, not comprehensive — dal, roti, sabzi, paneer, etc.)
- [ ] Docker + CI/CD + deployed

### Should Have (Weeks 6-9)
- [ ] Meal tracking via WhatsApp (client replies, bot tracks adherence)
- [ ] Dietitian adherence dashboard (see which clients are on track)
- [ ] Evaluation pipeline (does AI plan meet calorie targets? allergen violations? nutritional balance?)
- [ ] Protocol templates (dietitian saves their preferred approaches)
- [ ] Content/blog system — dietitian writes articles in dashboard
- [ ] Branded landing page per dietitian (about, blog, intake form, booking link)
- [ ] WhatsApp broadcast for new articles/tips
- [ ] Grocery list generation (aggregated from weekly plan)

### Nice to Have (Weeks 10-13 / post-launch polish)
- [ ] AI-assisted article drafting (dietitian gives topic, AI writes draft)
- [ ] Consultation booking (calendar integration or simple slot picker)
- [ ] Weekly progress summaries auto-sent to clients via WhatsApp
- [ ] Multi-dietitian / team accounts
- [ ] Revenue tracking
- [ ] AWS deployment (EC2 + RDS + S3)

---

## The Interview Narrative

> *"My wife is a nutritionist who manages clients using Canva, WhatsApp, and Excel — a painful workflow shared by thousands of Indian nutritionists. I built NutriPlan, a B2B SaaS that gives dietitians an AI co-pilot. The dietitian manages clients through a web dashboard where AI drafts structured, personalized Indian meal plans based on each client's health profile. The dietitian reviews and approves, then the plan is delivered to clients via WhatsApp — no app download needed. Clients interact entirely through WhatsApp: they track meals, request substitutions, get grocery lists, and read their nutritionist's published health articles. On the backend, I built the WhatsApp integration using the Business Cloud API with webhook handlers, the plan generation uses LangGraph for multi-step validation (allergen checks, macro balancing, cultural food mapping), and the content system feeds a RAG pipeline so the WhatsApp bot answers questions using the dietitian's own published knowledge."*

This story hits:
- ✅ Real problem (not a toy)
- ✅ Real user (wife tested it)
- ✅ B2B SaaS architecture (multi-tenant, RBAC)
- ✅ AI as productivity tool (not chatbot)
- ✅ WhatsApp API + webhooks (production messaging integration)
- ✅ Conversational AI (structured flows, not just Q&A)
- ✅ Content management + RAG (articles feed the AI knowledge base)
- ✅ Production-grade (Docker, CI/CD, evaluation pipeline)
- ✅ Domain expertise (Indian food, dietary constraints)
- ✅ Full-stack (FastAPI + React + PostgreSQL + LLM)
- ✅ Safety-conscious (validation, human review, allergen checks)
