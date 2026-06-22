# How I Built NutriPlan: An AI-Powered Practice OS for Nutritionists

As a backend engineer, I constantly look for ways to solve real-world problems with code. My wife is a nutritionist, and watching her manage clients across Canva, Excel, and WhatsApp made me realize how fragmented the tooling is for independent health professionals in India. I wanted to build something that not only streamlined her practice but also demonstrated my skills in building full-stack, production-ready AI applications.

Enter **NutriPlan**.

## What is NutriPlan?
NutriPlan is a B2B SaaS designed specifically for Indian nutritionists. It provides a comprehensive web dashboard for dietitians to manage clients, protocols, and content. The standout feature, however, is its AI integration, which automatically drafts highly personalized Indian meal plans based on a client’s health profile, preferences, and dietary restrictions. 

What makes NutriPlan truly special is the client experience: **there is no app to download**. Clients receive their meal plans, track their adherence, and request food substitutions entirely through automated WhatsApp interactions.

## The Tech Stack
I intentionally chose a modern, robust stack without over-engineering:
- **Backend:** FastAPI (Python 3.11) to handle high concurrency, backed by PostgreSQL 16.
- **Frontend:** React 19 with Vite, TypeScript, and Vanilla CSS.
- **AI/ML:** Google Gemini 2.0 Flash via LangGraph and LangChain.
- **Infrastructure:** Docker, Redis, and GitHub Actions for CI/CD.

## The AI Evolution Story
One of my core engineering philosophies is to "start simple and add complexity only when justified." The AI architecture in NutriPlan reflects this perfectly:

### Phase 1: Direct API Calls (The MVP)
I started with simple, direct calls to the Gemini API. By crafting precise prompts and enforcing structured JSON output, the system could successfully draft a basic 7-day meal plan. This was fast to build and cost-effective, but as the dietary rules became more complex (e.g., matching exact macros while avoiding specific allergens), single-shot prompting started to fail.

### Phase 2: Introducing LangChain & RAG
As my wife started writing articles and educational content on her landing page, clients naturally had questions. I integrated **LangChain** and `pgvector` to build a Retrieval-Augmented Generation (RAG) pipeline. This allowed the WhatsApp bot to accurately answer client queries by grounding its responses in the dietitian's own published content. 

### Phase 3: LangGraph for Stateful Workflows
Drafting a medically accurate, personalized meal plan is a multi-step cognitive process. To replicate this, I migrated the plan generation engine to **LangGraph**. The stateful workflow allowed me to break the generation down into isolated nodes:
1. **Retrieve Context:** Pull the client's medical history, allergies, and protocols.
2. **Generate Draft:** The LLM drafts the plan.
3. **Validate:** A deterministic rule engine checks if any allergens slipped in or if the macros are off.
4. **Iterate:** If validation fails, the graph loops back, feeding the exact failure reasons to the LLM to correct its mistakes.

Finally, I added an **LLM-as-a-judge** step that evaluates the final plan for cultural fit and practicality before presenting it to the dietitian for final approval.

## Engineering Challenges
- **Multi-Tenant Isolation:** To ensure strict data privacy, every database query is strictly scoped to the authenticated `dietitian_id`.
- **Resilient Webhooks:** Meta requires a `200 OK` response within 5 seconds for WhatsApp webhooks. I used FastAPI's `BackgroundTasks` to immediately acknowledge receipt while processing the intent and calling the LLM asynchronously.
- **Symmetric Encryption:** Sensitive health profiles are encrypted at rest using AES-128-CBC.

## Conclusion
Building NutriPlan was an incredible journey that allowed me to merge my backend expertise with cutting-edge AI orchestration tools. It’s actively solving a real problem for my wife's practice while serving as a testament to my capabilities as a full-stack product engineer.

If you're interested in the code, feel free to check out the [GitHub repository](#) or reach out to me!
