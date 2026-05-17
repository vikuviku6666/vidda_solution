# Vidda — Mental Model

## The Big Idea

> **Vidda takes a job description → reads EU banking law → generates a personalised compliance training plan → stores it → lets a reviewer approve or edit it.**

---

## Three Layers

```
┌──────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js)                                  │
│  What the user sees and clicks                        │
└──────────────────────────────────────────────────────┘
                        ↕  HTTP  (localhost:3000 ↔ 8000)
┌──────────────────────────────────────────────────────┐
│  BACKEND  (FastAPI + Google ADK)                      │
│  The brain — orchestrates all AI work                 │
└──────────────────────────────────────────────────────┘
                        ↕  MCP over HTTP
┌──────────────────────────────────────────────────────┐
│  RAG SERVER  (rag.bluetext.dev)                       │
│  Searchable AMLR 2024/1624 regulation knowledge base  │
└──────────────────────────────────────────────────────┘
```

---

## Happy Path — Generating a Plan

```
User pastes role description
        │
        ▼
POST /workflow/run
        │
        ▼
┌──────────────────────────────────────────┐
│  Google ADK Runner  (Gemini 2.5 Flash)   │
│  temperature=0 → deterministic           │
│                                          │
│  Step 1 ── extract_role()                │
│            OpenRouter LLM reads the job  │
│            description → extracts:       │
│            • role title                  │
│            • responsibilities            │
│            • 18 inherent AML risks       │
│                                          │
│  Step 2 ── search_docs() × 5            │
│            MCP calls to rag.bluetext.dev │
│            Query 1: "AML risks for role" │
│            Query 2-5: AMLR Article 9,   │
│              11, 33, 42 …               │
│            Returns: regulation text      │
│                                          │
│  Step 3 ── generate_competencies()       │
│            Rule-based mapping:           │
│            risks → knowledge/skills/     │
│            regulations → knowledge       │
│            Returns compact summary       │
│            (full data cached in memory)  │
│                                          │
│  Step 4 ── generate_training_plan()      │
│            OpenRouter LLM generates      │
│            8-12 modules across Q1-Q4     │
│            Reads from memory cache       │
│            Returns compact confirmation  │
│            (full plan cached in memory)  │
│                                          │
│  Step 5 ── validate_plan()               │
│            Checks: all 4 quarters exist? │
│            All references grounded?      │
│                                          │
│  Step 6 ── save_plan()                   │
│            Reads FULL plan from cache    │
│            Writes to SQLite DB:          │
│            • RoleRecord                  │
│            • CompetencyRecord            │
│            • TrainingPlanRecord          │
│            • 8-12 RecommendationRecords  │
│            Returns plan_id (UUID)        │
└──────────────────────────────────────────┘
        │
        ▼
GET /workflow/plan/{plan_id}
Loads from DB → WorkflowResponse
        │
        ▼
Frontend renders the training plan
```

---

## Memory Cache — Why It Exists

Gemini has a **64K output token limit**. Sending 23 knowledge items + 34 skills + a full 4-quarter plan back to the model in every message would overflow it.

```
Tool call result → agent receives   Tool call result → memory cache
────────────────────────────────    ────────────────────────────────
generate_competencies → {           _CURRENT_RUN = {
  status: "generated",                competencies: { ...58 full items... }
  knowledge_count: 24,                risk_types: [...]
  skills_count: 36,                   regulations: [...]
}                                   }

generate_training_plan → {          _CURRENT_RUN = {
  status: "generated",                ...
  quarters: ["Q1", "Q2", "Q3", "Q4"] training_plan: { quarterly_plan: [...] }
}                                   }

save_plan args → { }  ←── agent passes empty dicts
save_plan reads ────────────────────────────────── _CURRENT_RUN (full data)
```

---

## Data Model (SQLite)

```
roles                    competencies
──────────────────       ─────────────────────
id (UUID)                id (UUID)
name                     role_id → roles.id
responsibilities []      knowledge []
compliance_exposure []   skills []
risk_indicators []       judgement []
created_at               created_at

training_plans                    recommendations
──────────────────────────────    ──────────────────────────────
id (UUID)                         id (UUID)
role_id → roles.id                training_plan_id
status: draft/revised/approved    role_id
reviewer_notes                    competency_id
created_at                        quarter   (Q1 Foundation…Q4 Embedding)
                                  module
                                  objective
                                  behavioural_outcome
                                  activities []
                                  explanation
                                  role_reference
                                  risk_reference
                                  regulation_reference
                                  competency_reference
```

---

## Feedback Loop (Edit & Revise)

```
Reviewer sees generated plan
        │
        ├── "Approve" ──────────────────► PATCH /training/plans/{id}
        │                                  status = "approved"
        │                                  ✅ green banner on screen
        │
        └── "Edit" → types feedback
                │
                ▼
            POST /workflow/revise/{id}
                │
                ▼
            Loads original role + competencies from DB
            Injects feedback into training generation prompt
            OpenRouter regenerates all 8-12 modules
            Deletes old recommendations
            Saves new recommendations
            status = "revised"
                │
                ▼
            onPlanUpdated() → page reloads with revised plan
            ✅ green banner on screen (no alert popup)
```

---

## Saved Plans Panel

```
GET /workflow/plans
        │
        ▼
Lists all TrainingPlanRecords newest-first
Each row: { role, status, module_count, created_at }
        │
        ▼
Frontend shows panel below upload box:

  ┌────────────────────────────────────────┐
  │ 🗄️ Saved Training Plans          3     │
  │────────────────────────────────────────│
  │ A  AML/KYC Analyst  10 modules  2m ago │ 📝 draft
  │ C  Chief Compliance  8 modules  1h ago │ ✅ approved
  └────────────────────────────────────────┘
  
Click any row → GET /workflow/plan/{id} → loads into view
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| Google ADK instead of custom loop | Native tool-calling, parallel search, built-in retry |
| MCPToolset for RAG | Standard MCP protocol — no custom HTTP wrapper needed |
| `temperature=0` everywhere | Same role description → identical output every time |
| Cache in `_CURRENT_RUN` | Keeps Gemini's context small, avoids 64K token overflow |
| 2-3 modules per quarter | Richer, more specific training (8-12 total vs 4 before) |
| Set-based quarter validation | Allows multiple modules per quarter without failing checks |
| Inline notifications not alerts | Better UX — no browser popup blocking interaction |

---

## Environment Variables Needed

```
GOOGLE_API_KEY     → Gemini 2.5 Flash (ADK orchestrator)
OPENROUTER_API_KEY → role extraction + training generation
RAG_ENDPOINT       → https://rag.bluetext.dev/mcp/
RAG_API_KEY        → Bearer token for AMLR knowledge base
DATABASE_URL       → SQLite (default) or PostgreSQL
```
