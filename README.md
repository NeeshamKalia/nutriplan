# 🥗 NutriPlan

AI-powered practice OS for Indian nutritionists. Dietitians manage clients via a web dashboard, AI drafts personalized meal plans, and clients interact entirely through WhatsApp.

## Tech Stack

- **Backend:** FastAPI (Python 3.11)
- **Frontend:** React + Vite + TypeScript
- **Database:** PostgreSQL 16 + pgvector
- **AI:** Google Gemini 2.0 Flash (free tier) + OpenAI fallback
- **Messaging:** WhatsApp Business Cloud API

## Live Demo

- **Dashboard:** [https://nutriplan.vercel.app](https://nutriplan.vercel.app) *(Pending deployment)*
- **API URL:** [https://nutriplan-api.up.railway.app](https://nutriplan-api.up.railway.app) *(Pending deployment)*
- **WhatsApp Webhook:** Set up with Meta Business Manager to point to `/webhook/whatsapp`

## Architecture

1. **Dashboard:** Built in React for Dietitians.
2. **Backend:** FastAPI handles business logic.
3. **AI Generation:** LLMs generate structured JSON plans.
4. **Delivery & Tracking:** Meta Cloud API manages inbound/outbound messages.

## Quick Start

```bash
# Start PostgreSQL + Backend
docker-compose up -d

# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

### Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
nutriplan/
├── backend/         # FastAPI API server
├── frontend/        # React dashboard
├── docs/            # PRD, specs, plans
└── docker-compose.yml
```

## Documentation

- [Product Requirements](docs/prd.md)
- [Technical Specification](docs/technical_spec.md)
- [Implementation Plan](docs/implementation_plan.md)
- [Task Registry](docs/tasks.md)
