# Vidda Training Builder

AI-powered compliance training generator that creates role-based, AMLR 2024/1624-compliant training plans using a multi-agent Google ADK orchestrator, persistent DB tracking, and real-time 5-dimension scorecard evaluation.

![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Orchestration](https://img.shields.io/badge/orchestrator-google--adk-blue)
![Quality Check](https://img.shields.io/badge/evaluator-5--dimension_scorecard-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Google ADK Agentic Orchestration** - Fully autonomous compliance pipeline driven by Gemini 2.5 Flash (`google-adk` framework) with native MCP-based RAG search.
- **Intelligent Role Extraction** - Extracts role details, responsibilities, and up to 18 inherent AML compliance risks from job descriptions.
- **AMLR 2024/1624 RAG Grounding** - Automatically query regulation articles (e.g. Articles 9, 11, 15, 33, 42) directly from a secure compliance MCP server.
- **Comprehensive Multi-Module Plans** - Generates a robust 8-12 module annual path (2-3 distinct modules per quarter) progressing from Foundation (Q1) to Embedding (Q4).
- **Server-Side State Cache (`_CURRENT_RUN`)** - Keeps Gemini's context small by caching massive plan payloads on the server, avoiding 64K token window overflows.
- **5-Dimension Plan Scorecard** - Automatically evaluates each generated plan on *Coverage*, *Grounding*, *Regulation Quality*, *Role Specificity*, and *Progression* (0-100 score).
- **Interactive History Sidebar** - Quickly browse, load, and manage all saved plans with interactive badges (📝 draft, 🔄 revised, ✅ approved).
- **Human-in-the-Loop Revision** - Submit plain-text feedback to autonomously regenerate and refine plans on-the-fly without popup alerts.

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/vikuviku6666/vidda_solution.git
   cd vidda_solution
   ```

2. **Backend Configuration**
   ```bash
   cd backend-ADK
   pip install -r requirements.txt
   
   # Create and configure .env
   cp .env.example .env
   # Add your API keys to the .env file
   ```

3. **Frontend Configuration**
   ```bash
   cd ../frontend/my-app
   npm install
   ```

### Running the Application

1. **Start the Backend**
   ```bash
   cd backend-ADK
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start the Frontend**
   ```bash
   cd frontend/my-app
   npm run dev
   ```

3. **Open the Application**
   Open your browser and navigate to: [http://localhost:3000](http://localhost:3000)

---

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Agent Framework:** Google ADK (Agent Development Kit v1.33+)
- **Orchestration LLM:** Google Gemini 2.5 Flash (`GOOGLE_API_KEY`)
- **Worker LLM:** GPT-4o-Mini via OpenRouter (`OPENROUTER_API_KEY`)
- **RAG Server Integration:** Native ADK `MCPToolset` + `StreamableHTTPConnectionParams`
- **Database Persistence:** SQLAlchemy + SQLite (automatic local fallback, safe multi-thread pooling)

### Frontend
- **Framework:** Next.js 15 (TypeScript)
- **Styling & UI:** Tailwind CSS + custom glassmorphic components
- **State & Routing:** React Hooks + Axios client

---

## Environment Variables

### Backend (`backend-ADK/.env`)

```bash
# --- AI & LLM ---
GOOGLE_API_KEY=AIzaSy...              # Gemini 2.5 Flash orchestrator
OPENROUTER_API_KEY=sk-or-v1-...       # Role extraction & plan generator
LLM_MODEL=openai/gpt-4o-mini          # Worker model selection

# --- MCP RAG Server ---
RAG_API_KEY=your_mcp_api_key          # Bearer token for rag.bluetext.dev
RAG_ENDPOINT=https://rag.bluetext.dev/mcp/

# --- Database ---
DATABASE_URL=sqlite:///./vidda.db    # Auto-created locally if left empty
```

---

## Architecture & Data Flow

For a complete, comprehensive mental model of how the components, memory caches, and database schemas connect together, see the **[MENTAL_MODEL.md](MENTAL_MODEL.md)** documentation.

```
User role text → FastAPI
                   │
                   ▼
       Google ADK Orchestrator (Gemini 2.5 Flash, temp=0)
         ├─ extract_role()           → Inherent AML risks
         ├─ search_docs() × 5        → RAG MCP query
         ├─ generate_competencies()  → (cached)
         ├─ generate_training_plan() → 8-12 modules (cached)
         ├─ validate_plan()          → Set-based quarter checks
         └─ save_plan()              → Commits complete transaction to SQLite DB
                   │
                   ▼
       GET /workflow/plan/{id} ────► Renders main Timeline Grid
                                ├──► Renders Quality Scorecard (overall + 5 dimensions)
                                └──► Renders Approval / Edit Feedback Workflow
```

---

## API Endpoints

### Core Workflow
- `POST /workflow/run` - Generate a new deterministic training plan using the Google ADK runner.
- `GET /workflow/plan/{plan_id}` - Retrieve a saved plan, its role data, competencies, and recommendations.
- `POST /workflow/revise/{plan_id}` - Human-in-the-loop revision: regenerates a plan addressing reviewer feedback.
- `GET /workflow/plans` - Summary list of all saved plans (role, status, module count, timestamp) newest-first.
- `GET /workflow/plan/{plan_id}/evaluate` - Evaluates plan quality across 5 dimensions.

### Health Check
- `GET /workflow/health` - Workflow service health check.

---

## Testing

You can trigger a full pipeline execution directly from the command line:

```bash
curl -X POST http://localhost:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{
    "uploaded_text": "AML Compliance Officer responsible for transaction monitoring, risk triage, sanctions screening, and PEP customer onboarding."
  }'
```

See **[READY_TO_TEST.md](READY_TO_TEST.md)** for a comprehensive testing and validation guide.

---

## Recent Development History

### May 17, 2026 — Google ADK Migration & Quality Scorecard 🚀
- **Orchestration Refactor:** Migrated the custom tool-loop to Google ADK framework (`Agent`, `Runner`, and native `MCPToolset` for RAG).
- **Token Overflow Resolution:** Implemented server-side `_CURRENT_RUN` cache to pass lightweight status objects to Gemini while maintaining full JSON schemas locally.
- **5-Dimension Evaluator:** Added a backend evaluation engine and frontend circular scorecard component to grade coverage, grounding, regulation accuracy, specificity, and progression.
- **Sidebar History Panel:** Created a live saved plans list component in the frontend to quickly load historical runs.
- **Aesthetic Refinements:** Replaced popup alert blocks with inline modern success/error banners.
- **Stability Fixes:** SQLite thread safety pool adjustments and `or` fallback overrides to prevent env var subprocess crashes.

### May 16, 2026 — Performance & Loading UI ⚡
- Optimized RAG pipeline (parallel execution + broad search) to drop end-to-end latency by 30-40%.
- Integrated real-time stage progress loading UI on frontend.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
