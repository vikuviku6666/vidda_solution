# Vidda Training Builder - System Architecture

## Overview
AI-powered compliance training generator with human-in-the-loop workflow for creating role-based, risk-aligned training plans compliant with AMLR 2024/1624.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                       │
│                          React Components                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Upload     │      │   Display    │      │   Approval   │ │
│  │   Component  │──────▶   Training   │──────▶   Workflow   │ │
│  │              │      │     Plan     │      │              │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                      ▲                      │         │
│         │                      │                      │         │
└─────────┼──────────────────────┼──────────────────────┼─────────┘
          │                      │                      │
          │ POST /workflow/run   │ GET /plan/{id}       │ POST /revise/{id}
          │                      │                      │
          ▼                      │                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND-ADK (FastAPI)                         │
│                     Python Services                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             WORKFLOW ORCHESTRATOR                         │  │
│  │              Sequential Pipeline                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│          │                                                       │
│          ▼                                                       │
│  ┌──────────────┐                                               │
│  │  1. ROLE     │──────────────────┐                           │
│  │  EXTRACTOR   │    Input Text    │                           │
│  │  LLM Service │                  │                           │
│  └──────────────┘                  │                           │
│          │                         │                           │
│          │ Role Data               │                           │
│          ▼                         │                           │
│  ┌──────────────┐                 │                           │
│  │  2. RISK     │◀────────────────┘                           │
│  │  EXTRACTOR   │                                              │
│  │  RAG Search  │──────────┐                                   │
│  └──────────────┘          │                                   │
│          │                 │ Query: "risks for {role}"         │
│          │ Risk List       │                                   │
│          ▼                 │                                   │
│  ┌──────────────┐          │                                   │
│  │  3. REGULATION│◀────────┘                                   │
│  │  EXTRACTOR   │                                              │
│  │  RAG Search  │──────────┐                                   │
│  └──────────────┘          │                                   │
│          │                 │ Query: "AMLR articles"            │
│          │ Articles        │                                   │
│          ▼                 │                                   │
│  ┌──────────────┐          │                                   │
│  │  4. COMPETENCY│◀────────┘                                   │
│  │  GENERATOR   │                                              │
│  │  Rules Engine│                                              │
│  └──────────────┘                                              │
│          │                                                      │
│          │ Knowledge/Skills/Judgment                           │
│          ▼                                                      │
│  ┌──────────────┐                                              │
│  │  5. TRAINING │                                              │
│  │  CREATOR     │                                              │
│  │  LLM Service │                                              │
│  └──────────────┘                                              │
│          │                                                      │
│          │ 4-Quarter Plan                                      │
│          ▼                                                      │
│  ┌──────────────┐                                              │
│  │  6. DATABASE │                                              │
│  │  PERSISTENCE │                                              │
│  │  SQLite Save │                                              │
│  └──────────────┘                                              │
│          │                         │                           │
└──────────┼─────────────────────────┼───────────────────────────┘
           │                         │
           ▼                         ▼
    ┌──────────┐            ┌───────────────┐
    │  LOCAL   │            │  EXTERNAL     │
    │  DATABASE│            │  RAG SERVER   │
    │  SQLite  │            │  MCP Protocol │
    └──────────┘            └───────────────┘
         │                         │
         │                         │
    Store/Retrieve           Search Documents
         │                         │
         ▼                         ▼
   ┌──────────┐            ┌───────────────┐
   │ Training │            │ AMLR 2024/1624│
   │ Plans DB │            │ Role Docs     │
   └──────────┘            └───────────────┘
```

---

## Data Flow - Initial Generation

```
User Input (Role Description)
    │
    ▼
[Upload Component] ────────▶ Input Handler
    │
    │ POST /workflow/run
    ▼
[Backend API] ──────────────▶ Receive Request
    │
    ▼
[Input Validator] ──────────▶ Validate Input
    │ • Min 20 characters
    │ • Min 3 words
    │ • Contains role keywords
    ▼
[Role Extractor] ───────────▶ Extract Role
    │ (LLM: Gemini 2.5 Flash)
    │ Output: role, responsibilities, compliance_exposure
    ▼
[Risk Extractor] ───────────▶ Search Risks
    │ (RAG: MCP via HTTPS)
    │ Query → RAG → Document Chunks
    │ Output: List of compliance risks
    ▼
[Regulation Extractor] ─────▶ Find Articles
    │ (RAG: MCP)
    │ Query → RAG → Extract Article Numbers
    │ Output: Article 3, Article 9, Article 15, etc.
    ▼
[Competency Generator] ─────▶ Build Competencies
    │ (Rules-based Engine)
    │ Output: Knowledge, Skills, Judgment requirements
    ▼
[Training Creator] ─────────▶ Generate Plan
    │ (LLM: Gemini 2.5 Flash)
    │ Input: role + risks + articles + competencies
    │ Output: 4 quarterly modules with activities
    ▼
[Plan Validator] ───────────▶ Validate References
    │ • Check all references grounded
    │ • Ensure 4 quarters present
    │ • Verify different articles used
    ▼
[Database Writer] ──────────▶ Save Plan
    │ (SQLite)
    │ Tables: Role, Competency, TrainingPlan, Recommendation
    │ Output: plan_id (UUID)
    ▼
[API Response] ─────────────▶ Return Data
    │ JSON with role_data, recommendations, plan_id
    ▼
[Frontend Display] ─────────▶ Show Plan
    │ Q1-Q4 quarterly modules with article numbers
```

---

## Data Flow - Edit/Revision

```
User Feedback
    │
    ▼
[Edit Button] ──────────────▶ Show Textbox
    │
    ▼
[User Input] ───────────────▶ Type Feedback
    │ Example: "Add more focus on sanctions screening"
    │
    │ POST /revise/{plan_id}
    ▼
[Backend API] ──────────────▶ Receive Feedback
    │
    ▼
[Database Reader] ──────────▶ Fetch Plan
    │ (SQLite)
    │ Load: RoleRecord, CompetencyRecord, RecommendationRecords
    ▼
[Request Builder] ──────────▶ Reconstruct Context
    │ Extract: risks, regulations, competencies
    │ Add: user feedback
    ▼
[Training Creator] ─────────▶ Regenerate Plan
    │ (LLM: Gemini 2.5 Flash)
    │ Prompt: "Regenerate plan addressing: {feedback}"
    │ Output: New 4 quarterly modules
    ▼
[Database Updater] ─────────▶ Replace Recommendations
    │ (SQLite Transaction)
    │ 1. Delete old RecommendationRecords
    │ 2. Insert new RecommendationRecords
    │ 3. Update TrainingPlan.status = "revised"
    │ 4. Save TrainingPlan.reviewer_notes = feedback
    ▼
[API Response] ─────────────▶ Return Success
    │ {"status": "success", "message": "Plan revised"}
    │
    │ GET /plan/{plan_id}
    ▼
[Frontend Reload] ──────────▶ Fetch Updated
    │ Re-fetch complete plan data
    ▼
[Display Updated] ──────────▶ Show Revised
    │ UI updates with new modules
```

---

## Data Flow - Approval

```
User Action
    │
    ▼
[Approve Button] ───────────▶ Click Approve
    │
    │ PATCH /training/plans/{id}
    │ Body: {"status": "approved", "reviewer_notes": "Approved"}
    ▼
[Backend API] ──────────────▶ Update Status
    │
    ▼
[Database Updater] ─────────▶ Mark Approved
    │ (SQLite)
    │ UPDATE training_plans SET status='approved'
    ▼
[API Response] ─────────────▶ Confirm Success
    │ {"message": "Plan approved and ready for LMS export"}
    ▼
[Frontend Display] ─────────▶ Show Confirmation
    │ "✅ Successfully Approved!"
```

---

## Component Descriptions (2 words each)

### Frontend Components (Next.js 14 / React 18 / TypeScript)
| Component | Description |
|-----------|-------------|
| **Upload.tsx** | Input Handler |
| **page.tsx** | Main Orchestrator |
| **ApprovalWorkflow.tsx** | Decision Interface |

### Backend Services (FastAPI / Python 3.12)
| Service | Description |
|---------|-------------|
| **workflow.py** | Orchestration Logic |
| **role_intelligence.py** | Role Extraction |
| **mcp_client.py** | RAG Interface |
| **training_recommendation.py** | Plan Generation |
| **recommendation_validation.py** | Quality Assurance |
| **competency_engine.py** | Skill Mapping |
| **llm_client.py** | LLM Gateway |

### Database Models (SQLAlchemy / SQLite)
| Model | Description |
|-------|-------------|
| **RoleRecord** | Role Storage |
| **CompetencyRecord** | Skills Storage |
| **TrainingPlanRecord** | Plan Metadata |
| **RecommendationRecord** | Module Details |

### External Services
| Service | Description |
|---------|-------------|
| **RAG Server** | Document Search |
| **LLM API** | Generation Engine |
| **SQLite DB** | Data Persistence |

---

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **HTTP Client**: Axios
- **State Management**: React useState/useEffect

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.12
- **ORM**: SQLAlchemy
- **Database**: SQLite
- **LLM**: Google Gemini 2.5 Flash (via OpenRouter)
- **RAG**: MCP Protocol (HTTPS)
- **Validation**: Pydantic v2

### Infrastructure
- **Backend Server**: Uvicorn (ASGI)
- **Frontend Server**: Next.js Dev Server
- **Database**: SQLite (local file)
- **RAG Endpoint**: https://rag.bluetext.dev/mcp/
- **LLM Endpoint**: OpenRouter API

---

## Key Features

### 1. Input Validation
- Minimum 20 characters
- Minimum 3 words
- Must contain role-related keywords
- Prevents meaningless inputs

### 2. RAG-Powered Article Extraction
- Searches AMLR 2024/1624 document
- Extracts specific article numbers (e.g., Article 3, 9, 15)
- Falls back to common articles if RAG returns insufficient results
- Ensures diverse article references across quarters

### 3. LLM-Powered Training Generation
- Uses Gemini 2.5 Flash for generation
- Generates 4 quarterly modules:
  - Q1: Foundation (Months 1-3)
  - Q2: Application (Months 4-6)
  - Q3: Deepening (Months 7-9)
  - Q4: Embedding (Months 10-12)
- Each module includes:
  - Module name
  - Learning objective
  - Behavioral outcome
  - 5-6 training activities
  - AMLR article reference

### 4. Human-in-the-Loop
- Edit button shows feedback textbox
- User provides feedback (e.g., "Add more on sanctions")
- LLM regenerates plan incorporating feedback
- Database updated with revised recommendations
- Frontend auto-reloads to show changes

### 5. Approval Workflow
- Approve button marks plan as "approved"
- Status saved to database
- Ready for LMS export
- Success confirmation displayed

### 6. Validation & Quality Assurance
- Validates all references are grounded in evidence
- Ensures no hallucinated articles
- Verifies role, risk, regulation, and competency links
- Enforces different articles per quarter
- Retry logic with error feedback to LLM

---

## API Endpoints

### Workflow Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflow/run` | Generate training plan from role description |
| POST | `/workflow/revise/{plan_id}` | Revise plan with user feedback |
| GET | `/workflow/plan/{plan_id}` | Fetch plan by ID |

### Training Plan Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/training/plans/{plan_id}` | Update plan status (approve) |

### Utility Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload document and extract text |

---

## Database Schema

### Tables

#### `roles`
- `id` (UUID, PK)
- `name` (Text)
- `responsibilities` (JSON Array)
- `compliance_exposure` (JSON Array)
- `risk_indicators` (JSON Array)
- `created_at` (Timestamp)

#### `competencies`
- `id` (UUID, PK)
- `role_id` (UUID, FK → roles.id)
- `knowledge` (JSON Array)
- `skills` (JSON Array)
- `judgement` (JSON Array)

#### `training_plans`
- `id` (UUID, PK)
- `role_id` (UUID, FK → roles.id)
- `status` (Text: draft/revised/approved)
- `reviewer_notes` (Text, nullable)
- `created_at` (Timestamp)

#### `recommendations`
- `id` (UUID, PK)
- `training_plan_id` (UUID, FK → training_plans.id)
- `role_id` (UUID, FK → roles.id)
- `competency_id` (UUID, FK → competencies.id)
- `quarter` (Text: Q1/Q2/Q3/Q4)
- `module` (Text)
- `objective` (Text)
- `behavioural_outcome` (Text)
- `activities` (JSON Array)
- `explanation` (Text)
- `role_reference` (Text)
- `risk_reference` (Text)
- `regulation_reference` (Text)
- `competency_reference` (Text)

---

## Environment Variables

### Backend (.env.local)
```bash
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=google/gemini-2.5-flash
RAG_API_KEY=rag_...
RAG_ENDPOINT=https://rag.bluetext.dev/mcp/
DATABASE_URL=sqlite:///vidda.db
```

### Frontend (None required - uses localhost:8000)

---

## Deployment Notes

### Running Locally

**Backend:**
```bash
cd backend-ADK
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend/my-app
npm run dev
```

### Ports
- Backend: http://127.0.0.1:8000
- Frontend: http://localhost:3000
- API Docs: http://127.0.0.1:8000/docs

---

## Future Enhancements

1. **LMS Integration**: Export approved plans to external LMS systems
2. **Multi-language Support**: Generate training plans in multiple languages
3. **Advanced Analytics**: Track completion rates and effectiveness
4. **Role Templates**: Pre-built templates for common compliance roles
5. **Bulk Processing**: Generate plans for multiple roles simultaneously
6. **Custom Article Mapping**: Allow users to specify which articles to use
7. **PDF Export**: Generate PDF versions of training plans

---

## System Requirements

### Backend
- Python 3.12+
- 512MB RAM minimum
- 1GB disk space
- Internet connection (for LLM & RAG)

### Frontend
- Node.js 18+
- 256MB RAM minimum
- Modern web browser (Chrome, Firefox, Safari, Edge)

---

## License & Contact

**Project**: Vidda Training Builder  
**Purpose**: AI-powered compliance training generator  
**Regulation**: AMLR 2024/1624  
**Architecture**: RAG + LLM + Human-in-the-Loop
