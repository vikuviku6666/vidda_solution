# Vidda Training Plan Generation - Complete Implementation Plan

**Date:** 2026-05-16  
**Status:** Ready for Implementation - Agent-Powered Architecture  
**Estimated Time:** 27-36 hours (Phase A with Agents: 18-24h, Phase B: 9-12h)  
**Architecture:** Hybrid LangGraph + ReAct Agents with MCP RAG Integration

---

## Table of Contents

1. [Architecture Diagrams](#architecture-diagrams) ⭐ NEW
2. [Executive Summary](#executive-summary)
3. [Requirements Overview](#requirements-overview)
4. [System Architecture](#system-architecture)
5. [Phase A: Core RAG Integration with Agents](#phase-a-core-rag-integration-with-agents)
6. [Phase B: AI Regeneration with Feedback](#phase-b-ai-regeneration-with-feedback)
7. [Testing Plan](#testing-plan)
8. [File Manifest](#file-manifest)
9. [Implementation Timeline](#implementation-timeline)
10. [Success Criteria](#success-criteria)
11. [Risk Assessment](#risk-assessment)
12. [Outstanding Questions](#outstanding-questions)

---

## Architecture Diagrams

> **📊 For detailed visual architecture diagrams, see [ARCHITECTURE_DIAGRAMS.md](./backend/ARCHITECTURE_DIAGRAMS.md)**

This implementation uses a **hybrid architecture** combining:
- **LangGraph StateGraph**: Deterministic orchestration backbone
- **ReAct Agents**: Autonomous decision-making for evidence gathering and self-correction
- **MCP RAG Integration**: Real-time regulation retrieval from workshop-rag

### Quick Visual Overview

The architecture diagrams document contains 6 comprehensive diagrams:

1. **High-Level System Architecture** - Complete workflow from input to output
2. **Evidence Gathering Agent Workflow** - 8-iteration autonomous search process
3. **Self-Correcting Training Generator** - Validation and regeneration loop
4. **MCP Client Architecture** - SSE + JSON-RPC 2.0 integration layers
5. **Data Flow with Explainability** - Complete provenance chain
6. **Complete Traceability Chain** - Audit trail from query to activity

### Key Architectural Decisions

**Why Hybrid (LangGraph + Agents)?**
- ✅ **Predictability**: Deterministic steps for critical path
- ✅ **Intelligence**: Agents for complex reasoning (evidence gathering, self-correction)
- ✅ **Auditability**: Complete control flow logging
- ✅ **Performance**: Agents only where value is highest

**Agent Capabilities:**
- **Evidence Gathering Agent**: 5-10 tool calls per invocation, multi-strategy search
- **Training Generation Agent**: Self-correcting with validation loop, max 3 attempts
- **Both Agents**: Full provenance tracking and audit trail integration

**Performance Targets:**
- Simple role (KYC Analyst): 20-30 seconds, 15-20 LLM calls, ~$0.08-0.10/plan
- Complex role (Head of Compliance): 30-45 seconds, 20-30 LLM calls, ~$0.10-0.15/plan

---

## Executive Summary

This implementation plan provides a **hybrid agent-powered system** for generating evidence-driven, explainable, auditable, and traceable compliance training plans using real-time RAG (Retrieval-Augmented Generation), autonomous agents, and human-in-the-loop workflow.

### Architecture Approach

**Hybrid: LangGraph StateGraph + ReAct Agents**
- **Deterministic Steps**: Parse, extract, map (fast, predictable)
- **Agent Step 1**: Evidence Gathering Agent (autonomous MCP RAG queries, 5-10 tool calls)
- **Agent Step 2**: Self-Correcting Training Generator (validation loop, max 3 attempts)
- **Why Hybrid?**: Best of both worlds - predictability + intelligence + auditability

### Key Features

**Phase A - Core System with Agents:**
- 🤖 **Evidence Gathering Agent**: Autonomous multi-strategy search of workshop-rag MCP
  - List available regulations (scope understanding)
  - Role-based search
  - Risk-based search (each risk type separately)
  - Deep dive (retrieve full documents)
  - Cross-reference validation
  - Output: 10-20 regulations with complete provenance
- 🤖 **Self-Correcting Generator Agent**: Intelligent training plan generation
  - Generate plan with explainability (WHY each activity)
  - Validate quality automatically
  - Self-correct on errors (max 3 attempts)
  - Output: 20-28 activities with full traceability
- 📋 **Complete Audit Trail**: Every tool call, timestamp, input/output logged
- 🔍 **Full Provenance**: MCP query → document → regulation → competency → activity
- ✅ **Explainability**: Every activity has regulation_basis, competency, risk, reasoning
- ✅ **Traceability**: Every recommendation traceable back to MCP source

**Phase B - Human-in-Loop:**
- Text input OR file upload (PDF/TXT/DOCX)
- Structured feedback form for AI regeneration
- Selective quarter regeneration (preserve unchanged quarters)
- Iteration limit (max 5-6 attempts)
- Manual editing fallback always available

### User Workflow

```
Upload (text/file) 
  → 🤖 Evidence Gathering Agent (autonomous RAG search)
  → 🤖 Training Generator Agent (self-correcting)
  → Review (with explainability + audit trail)
  → [Approve OR Edit/Regenerate] 
  → (If regenerate: provide feedback → 🤖 agent regenerates → review → repeat up to 5x) 
  → Approve 
  → Published
```

### Performance Targets

**Simple Role (e.g., KYC Analyst):**
- Duration: 20-30 seconds
- Evidence Agent: 5-8 tool calls, 8-12 seconds
- Training Agent: 2-4 tool calls (1-2 attempts), 10-15 seconds
- Output: 20-24 activities, 8-12 regulations
- Cost: ~$0.08-0.10 per plan (GPT-4o-mini)

**Complex Role (e.g., Head of Compliance):**
- Duration: 30-45 seconds
- Evidence Agent: 10-15 tool calls, 15-20 seconds
- Training Agent: 4-6 tool calls (2-3 attempts), 15-20 seconds
- Output: 24-28 activities, 15-25 regulations
- Cost: ~$0.12-0.15 per plan (GPT-4o-mini)

---

## Requirements Overview

### Confirmed Requirements

1. ✅ **Input Methods:** Text input OR file upload (PDF/TXT/DOCX)
2. ✅ **Feedback Approach:** Hybrid (manual editing + AI regeneration)
3. ✅ **Implementation Scope:** Both Phase A (core) and Phase B (regeneration)
4. ✅ **Regeneration Details:**
   - Scope: Regenerate what's needed (selective quarters or full plan)
   - Feedback Format: Structured form
   - Version History: Not needed (keep latest only)
   - Iteration Limit: 5-6 regeneration attempts maximum

### Non-Functional Requirements

- ✅ **Explainable:** Clear reasoning for each activity
- ✅ **Auditable:** Full trace from evidence to recommendations
- ✅ **Traceable:** Every activity linked to role/risk/regulation/competency
- ✅ **Governed:** Documented decision-making process
- ✅ **Real-time:** All data from RAG, no hardcoded content

---

## System Architecture

> **📊 For detailed visual diagrams of agent workflows, MCP integration, and data flow, see [ARCHITECTURE_DIAGRAMS.md](./backend/ARCHITECTURE_DIAGRAMS.md)**

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VIDDA FRONTEND                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Upload Interface                                  │     │
│  │  • Text input box (paste text)                     │     │
│  │  • File upload button (PDF/TXT/DOCX)               │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      ↓                                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Review Interface (After Generation)               │     │
│  │  • Timeline (4 quarters with activities)           │     │
│  │  • Behavioral Outcomes                             │     │
│  │  • Explainability Panel                            │     │
│  │  • Confidence Badges                               │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      ↓                                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Action Buttons                                    │     │
│  │  [Approve] [Edit Manually] [Request Changes]      │     │
│  └──────┬─────────────┬──────────────────┬───────────┘     │
└─────────┼─────────────┼──────────────────┼─────────────────┘
          ↓             ↓                  ↓
    ┌─────────┐   ┌──────────┐   ┌──────────────────┐
    │ APPROVE │   │  EDIT    │   │ REGENERATE       │
    │ (Publish)│   │ (Inline) │   │ (With Feedback)  │
    └────┬────┘   └────┬─────┘   └────┬─────────────┘
         │             │               │
         ↓             ↓               ↓
┌─────────────────────────────────────────────────────────────┐
│                    VIDDA BACKEND                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Core Endpoints (Phase A)                          │     │
│  │  • POST /upload (text or file)                     │     │
│  │  • POST /workflow/run (process document)           │     │
│  │  • PATCH /training/plans/{id} (approve)            │     │
│  │  • PUT /training/recommendations/{id} (edit)       │     │
│  │  • GET /governance/stats                           │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Regeneration Endpoints (Phase B)                  │     │
│  │  • POST /training/regenerate/{plan_id}             │     │
│  │    → Accepts structured feedback                   │     │
│  │    → Regenerates selected quarters                 │     │
│  │    → Returns updated plan                          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  AI Processing Pipeline                            │     │
│  │                                                     │     │
│  │  1. Document Ingestion                             │     │
│  │     ↓                                               │     │
│  │  2. Role Intelligence Extraction                   │     │
│  │     ↓                                               │     │
│  │  3. Risk Mapping                                   │     │
│  │     ↓                                               │     │
│  │  4. RAG Regulation Retrieval ← [MCP Client]       │     │
│  │     ↓                                               │     │
│  │  5. Competency Generation                          │     │
│  │     ↓                                               │     │
│  │  6. Training Recommendation Generation             │     │
│  │     ↓                                               │     │
│  │  7. Evidence-Based Validation                      │     │
│  │     ↓                                               │     │
│  │  8. Database Persistence (draft)                   │     │
│  │     ↓                                               │     │
│  │  9. Audit Trail Logging                            │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  MCP RAG Client                                    │     │
│  │  • Handshake: initialize + notifications          │     │
│  │  • Session Management: Mcp-Session-Id              │     │
│  │  • Tools: search_docs, list_documents              │     │
│  │  • SSE Response Parsing                            │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES                               │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  Workshop RAG        │  │  OpenRouter LLM      │        │
│  │  (MCP Server)        │  │  (gpt-4o-mini)       │        │
│  │  • AMLR Regulations  │  │  • Training Gen      │        │
│  │  • search_docs       │  │  • JSON Schema       │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘

                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite)                         │
│                                                              │
│  • roles                 (extracted role info)              │
│  • competencies          (knowledge/skills/judgement)       │
│  • training_plans        (status, reviewer_notes)           │
│  • recommendations       (quarters, activities, references) │
│  • audit_logs           (full traceability)                 │
└─────────────────────────────────────────────────────────────┘
```

### MCP Connection Details

**Endpoint:** `https://rag.bluetext.dev/mcp/`  
**Protocol:** MCP Streamable HTTP (JSON-RPC 2.0)  
**Transport:** HTTP POST with SSE responses  

**Required Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json, text/event-stream
Mcp-Session-Id: <id>  (after handshake)
```

**Handshake Sequence:**
1. POST `initialize` with protocolVersion "2025-03-26"
2. Extract `Mcp-Session-Id` from response headers
3. POST `notifications/initialized` (notification, no id field)
4. Use session ID in all subsequent requests

**Available Tools:**
- `search_docs` - Search regulations by query
- `list_documents` - List available documents
- `get_document` - Get full document text

---

## Phase A: Core RAG Integration

**Duration:** 8-10 hours  
**Priority:** CRITICAL (Must complete first)

### A1: MCP Client Implementation (2-3 hours)

**File:** `/backend/app/services/mcp_client.py` (NEW)

**Purpose:** Handle MCP protocol, session management, and tool calls

**Key Components:**

```python
class MCPClient:
    """
    Client for MCP streamable HTTP endpoint.
    Handles handshake, session management, and SSE responses.
    """
    
    def __init__(self):
        # Configure endpoint, API key, session
        
    def _get_headers(self, include_session=True):
        # Build required headers
        
    def _parse_response(self, response):
        # Handle both JSON and SSE formats
        
    def _parse_sse(self, sse_text):
        # Parse Server-Sent Events
        
    def initialize(self):
        # Perform MCP handshake
        # 1. Send initialize
        # 2. Extract Mcp-Session-Id
        # 3. Send notifications/initialized
        
    def call_tool(self, tool_name, arguments):
        # Call MCP tool via JSON-RPC
        
    def search_docs(self, query, project_id=None):
        # Search regulations
        
    def list_documents(self):
        # List available documents
        
    def get_document(self, document_id):
        # Get full document
```

**Implementation Notes:**
- Singleton pattern for connection reuse
- Auto-initialize on first tool call
- SSE parsing for event stream responses
- Comprehensive error handling

---

### A2: Real-Time Regulation Retrieval (2 hours)

**File:** `/backend/app/services/regulation_retrieval.py` (MODIFY)

**Changes:**

```python
def retrieve_regulations(query=None, risk_types=None):
    """
    Retrieve regulations in real-time from workshop-rag.
    
    Args:
        query: Optional text query
        risk_types: Optional list of risk types
        
    Returns:
        List of RegulationReference objects
    """
    
    # Build search query
    search_query = build_search_query(query, risk_types)
    
    # Call MCP RAG
    mcp = get_mcp_client()
    hits = mcp.search_docs(query=search_query)
    
    # Parse hits into RegulationReference objects
    regulations = parse_rag_hits(hits, risk_types)
    
    # Filter by risk types if specified
    if risk_types:
        regulations = filter_by_risk_types(regulations, risk_types)
    
    return regulations


def parse_rag_hits(hits, risk_types):
    """Parse RAG search hits into RegulationReference objects."""
    regulations = []
    
    for hit in hits:
        article = extract_article_number(hit['text'], hit['filename'], hit['label'])
        title = extract_title(hit['text'], hit['label'])
        requirements = extract_requirements(hit['text'])
        keywords = extract_keywords(hit['text'], hit['label'])
        
        reg = RegulationReference(
            article=article,
            title=title,
            requirements=requirements,
            keywords=keywords,
            risk_types=risk_types,
            source_document=hit['filename']
        )
        regulations.append(reg)
    
    return regulations
```

**Key Functions:**
- `extract_article_number()` - Regex extraction of "Article XX"
- `extract_title()` - Get title from label or first line
- `extract_requirements()` - Extract sentences with "must", "shall", "required"
- `extract_keywords()` - Extract compliance-related keywords

---

### A3: Evidence-Driven Prompt (30 minutes)

**File:** `/backend/app/prompts/training_generation.py` (MODIFY)

**Key Changes:**
- Remove any hardcoded examples
- Emphasize evidence-driven generation
- Dynamic activity count: 4-8 based on evidence scope
- Strong traceability requirements
- Governance-focused explanation field

**Prompt Structure:**

```python
TRAINING_GENERATION_SYSTEM_PROMPT = """
You are a compliance training recommendation engine.

Generate structured annual training plan based ONLY on evidence provided.

ACTIVITY GENERATION - EVIDENCE-DRIVEN:
- Analyze evidence scope (role, risks, regulations, competencies)
- Generate 4-8 activities per quarter based on evidence complexity
- Each activity must trace to specific evidence item

GOVERNANCE & TRACEABILITY:
- Explanation must reference: responsibility, risk, regulation, competency
- All reference fields must be exact copies from evidence

ACTIVITY FORMATTING:
- Concise noun phrases (3-8 words)
- NOT full sentences
- Progressive: Q1=Foundation → Q4=Embedding

Rules:
- Generate ONLY from provided evidence
- Never invent facts
- Make role-specific
- Return valid JSON
"""
```

---

### A4: Evidence-Based Validation (1-2 hours)

**File:** `/backend/app/services/recommendation_validation.py` (MODIFY)

**Add Function:**

```python
def validate_activities_evidence_driven(training_plan, request):
    """
    Validate activity count matches evidence scope.
    Ensure governance and traceability requirements met.
    """
    errors = []
    
    # Calculate evidence complexity
    evidence = build_evidence(request)
    evidence_count = (
        len(evidence['role_references']) +
        len(evidence['risk_references']) +
        len(evidence['regulation_references']) +
        len(evidence['competency_references'])
    )
    
    # Determine expected activity range
    if evidence_count <= 8:
        min_activities, max_activities = 4, 5
        complexity = "basic"
    elif evidence_count <= 15:
        min_activities, max_activities = 5, 6
        complexity = "medium"
    elif evidence_count <= 25:
        min_activities, max_activities = 6, 7
        complexity = "complex"
    else:
        min_activities, max_activities = 7, 8
        complexity = "highly complex"
    
    for rec in training_plan.quarterly_plan:
        count = len(rec.activities)
        
        # Validate count
        if count < min_activities:
            errors.append(f'{rec.quarter}: Need at least {min_activities} activities')
        elif count > max_activities:
            errors.append(f'{rec.quarter}: Maximum {max_activities} activities')
        
        # Validate traceability
        explanation = rec.explanation.lower()
        required = ['responsibility', 'risk', 'regulation', 'competency']
        missing = [kw for kw in required if kw not in explanation]
        
        if missing:
            errors.append(f'{rec.quarter}: Explanation lacks: {", ".join(missing)}')
        
        # Validate reference fields
        if not rec.role_reference or not rec.role_reference.strip():
            errors.append(f'{rec.quarter}: Missing role_reference')
        # ... similar for other reference fields
    
    return errors
```

**Update validate_training_plan:**

```python
def validate_training_plan(training_plan, request):
    errors = []
    
    # Existing validations...
    
    # ADD: Evidence-driven validation
    errors.extend(validate_activities_evidence_driven(training_plan, request))
    
    # Continue with existing validations...
    
    return ValidationResult(valid=not errors, errors=errors)
```

---

### A5: Enhanced Audit Trail (30 minutes)

**File:** `/backend/app/services/training_recommendation.py` (MODIFY)

**Update audit_log call:**

```python
# Calculate evidence metrics
evidence = build_evidence(request)
evidence_metrics = {
    'role_references_count': len(evidence['role_references']),
    'risk_references_count': len(evidence['risk_references']),
    'regulation_references_count': len(evidence['regulation_references']),
    'competency_references_count': len(evidence['competency_references']),
    'total_evidence_count': sum of all above
}

audit_log(
    'training_recommendation',
    model_used=model_name,
    prompt={...},
    output=training_plan.model_dump(),
    references=build_evidence(request),
    metadata={
        'attempts': attempt + 1,
        'validation_errors': validation_errors,
        'evidence_source': 'real-time RAG (workshop-rag MCP)',  # ADD
        'rag_endpoint': os.getenv('RAG_ENDPOINT'),              # ADD
        'evidence_metrics': evidence_metrics,                   # ADD
        'activity_counts': {...}                                # ADD
    },
)
```

---

### A6: Dependencies & Testing (2 hours)

**Update requirements.txt:**

```txt
httpx  # ADD THIS LINE
```

**Test Script 1:** `/backend/test_mcp.py`

```python
"""Test MCP client connection."""

from app.services.mcp_client import get_mcp_client

def test_mcp_connection():
    print("Testing MCP connection...")
    
    mcp = get_mcp_client()
    init_result = mcp.initialize()
    print(f"✓ MCP initialized: {init_result}")
    print(f"✓ Session ID: {mcp.session_id}")
    
    docs = mcp.list_documents()
    print(f"✓ Available documents: {len(docs)}")
    
    hits = mcp.search_docs(query="AMLR training requirements")
    print(f"✓ Search results: {len(hits)} hits")
    
    print("\n✅ MCP connection test passed!")

if __name__ == '__main__':
    test_mcp_connection()
```

**Test Script 2:** `/backend/test_rag_retrieval.py`

```python
"""Test regulation retrieval from RAG."""

from app.services.regulation_retrieval import retrieve_regulations

def test_regulation_retrieval():
    print("Testing regulation retrieval...")
    
    regs = retrieve_regulations(risk_types=['aml_risk', 'sanctions_risk'])
    print(f"✓ Retrieved {len(regs)} regulations")
    
    for reg in regs[:3]:
        print(f"\n{reg.article}: {reg.title}")
    
    print("\n✅ Regulation retrieval test passed!")

if __name__ == '__main__':
    test_regulation_retrieval()
```

---

## Phase B: AI Regeneration with Feedback

**Duration:** 9-12 hours  
**Priority:** HIGH (Implement after Phase A working)

### B1: Upload Interface Enhancement (1 hour)

**File:** `/backend/app/routes/upload.py` (NEW)

**Endpoints:**

```python
@router.post('/upload/text')
def upload_text(payload: dict):
    """Accept text input."""
    text = payload.get('text', '')
    return run_workflow(WorkflowRequest(uploaded_text=text))

@router.post('/upload/file')
async def upload_file(file: UploadFile):
    """Accept file upload (PDF/TXT/DOCX)."""
    content = await parse_uploaded_file(file)
    return run_workflow(WorkflowRequest(uploaded_text=content))
```

---

### B2: Feedback-Enhanced Prompt (1 hour)

**File:** `/backend/app/prompts/training_generation.py` (MODIFY)

**Add function:**

```python
def build_prompt_with_feedback(evidence, feedback=None):
    """Build prompt, optionally with user feedback."""
    base_prompt = TRAINING_GENERATION_SYSTEM_PROMPT
    
    if feedback:
        feedback_section = f"""
USER FEEDBACK:
Quarters to regenerate: {', '.join(feedback.get('quarters', []))}
Feedback: {feedback.get('comments', '')}

ADDRESS FEEDBACK while maintaining evidence-driven approach.
"""
        base_prompt += feedback_section
    
    return base_prompt
```

---

### B3: Regeneration Service (2-3 hours)

**File:** `/backend/app/services/training_regeneration.py` (NEW)

**Key Components:**

```python
class RegenerationFeedback(BaseModel):
    """Structured feedback for regeneration."""
    quarters_to_regenerate: list[str]
    quarter_feedback: list[QuarterFeedback]
    general_comments: str = ""

class QuarterFeedback(BaseModel):
    """Feedback for specific quarter."""
    quarter: str
    issue_type: str  # too_theoretical, missing_topic, etc.
    specific_comments: str
    suggestions: str = ""


def regenerate_training_plan(plan_id, feedback, session):
    """Regenerate training plan based on feedback."""
    
    # 1. Fetch existing plan and evidence
    plan = get_training_plan(plan_id, session)
    evidence = get_original_evidence(plan_id, session)
    
    # 2. Check attempt limit
    if (plan.regeneration_count or 0) >= 5:
        raise ValueError("Maximum 5 regeneration attempts reached")
    
    # 3. Build feedback-enhanced prompt
    prompt = build_prompt_with_feedback(evidence, feedback)
    
    # 4. Regenerate (selective or full)
    if feedback.quarters_to_regenerate:
        new_plan = regenerate_selected_quarters(plan, evidence, feedback, prompt)
    else:
        new_plan = regenerate_full_plan(evidence, feedback, prompt)
    
    # 5. Validate
    validation = validate_training_plan(new_plan, evidence)
    if not validation.valid:
        raise ValueError(f"Validation failed: {validation.errors}")
    
    # 6. Update database
    update_training_plan(plan_id, new_plan, (plan.regeneration_count or 0) + 1, session)
    
    # 7. Audit
    audit_regeneration(plan_id, feedback, (plan.regeneration_count or 0) + 1)
    
    return new_plan
```

---

### B4: Regeneration Endpoint (1-2 hours)

**File:** `/backend/app/routes/training.py` (MODIFY)

**Endpoint:**

```python
@router.post('/training/regenerate/{plan_id}')
def regenerate_training_plan_endpoint(
    plan_id: str,
    feedback: RegenerationFeedback,
    session: Session = Depends(get_session)
):
    """Regenerate training plan with user feedback."""
    try:
        updated_plan = regenerate_training_plan(plan_id, feedback, session)
        
        return {
            "status": "success",
            "training_plan_id": plan_id,
            "regeneration_attempt": ...,
            "updated_quarters": feedback.quarters_to_regenerate,
            "recommendations": [...]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

### B5: Database Schema Enhancement (30 minutes)

**File:** `/backend/app/db_models.py` (MODIFY)

**Add to TrainingPlanRecord:**

```python
class TrainingPlanRecord(Base):
    __tablename__ = 'training_plans'
    
    # ... existing fields ...
    
    # ADD THESE:
    regeneration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_feedback: Mapped[dict | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)
```

**Migration:**

```bash
sqlite3 backend/vidda.db "ALTER TABLE training_plans ADD COLUMN regeneration_count INTEGER DEFAULT 0;"
sqlite3 backend/vidda.db "ALTER TABLE training_plans ADD COLUMN last_feedback TEXT;"
sqlite3 backend/vidda.db "ALTER TABLE training_plans ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
```

---

### B6: Frontend Feedback UI (2-3 hours)

**Component:** `/frontend/my-app/components/FeedbackForm.tsx` (NEW)

**UI Structure:**

```tsx
<FeedbackForm>
  <h2>Request Changes</h2>
  
  <section>
    <h3>Which quarters need changes?</h3>
    <CheckboxGroup>
      [ ] Q1 Foundation
      [ ] Q2 Application
      [ ] Q3 Deepening
      [ ] Q4 Embedding
    </CheckboxGroup>
  </section>
  
  {selectedQuarters.map(quarter => (
    <section key={quarter}>
      <h3>{quarter}</h3>
      
      <Select label="Issue Type">
        <option>Too theoretical</option>
        <option>Missing specific topic</option>
        <option>Too many activities</option>
        <option>Too few activities</option>
        <option>Activities too generic</option>
        <option>Wrong focus area</option>
        <option>Other</option>
      </Select>
      
      <TextArea label="Specific Comments" />
      <TextArea label="Suggestions" />
    </section>
  ))}
  
  <TextArea label="General Comments (optional)" />
  
  <div className="actions">
    <Button variant="secondary" onClick={onCancel}>Cancel</Button>
    <Button variant="primary" onClick={onSubmit}>Regenerate</Button>
  </div>
  
  {regenerationCount > 0 && (
    <Alert>Attempt {regenerationCount + 1} of 5</Alert>
  )}
</FeedbackForm>
```

---

### B7: Frontend Upload Interface (1 hour)

**Component:** `/frontend/my-app/components/UploadInterface.tsx` (MODIFY)

**UI Structure:**

```tsx
<UploadInterface>
  <Tabs>
    <Tab label="Paste Text">
      <TextArea
        rows={15}
        placeholder="Paste role description here..."
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
      />
      <Button onClick={handleTextSubmit}>
        Generate Training Plan
      </Button>
    </Tab>
    
    <Tab label="Upload File">
      <FileUpload
        accept=".pdf,.txt,.docx"
        onFileSelect={handleFileUpload}
      />
      <p>Accepted: PDF, TXT, DOCX</p>
      {uploadedFile && (
        <div>
          <span>{uploadedFile.name}</span>
          <Button onClick={handleFileSubmit}>
            Generate Training Plan
          </Button>
        </div>
      )}
    </Tab>
  </Tabs>
</UploadInterface>
```

---

### B8: Iteration Limit Handling (30 minutes)

**Backend:**

```python
if attempt_count >= 5:
    raise ValueError("Maximum 5 regeneration attempts reached. Please use manual editing.")
```

**Frontend:**

```tsx
{regenerationCount >= 3 && regenerationCount < 5 && (
  <Alert variant="warning">
    Used {regenerationCount} of 5 attempts.
  </Alert>
)}

{regenerationCount >= 5 && (
  <Alert variant="error">
    Maximum attempts reached (5/5).
    <Button onClick={() => setEditMode(true)}>
      Switch to Manual Editing
    </Button>
  </Alert>
)}
```

---

## Testing Plan

### Phase A Testing

#### Test 1: MCP Connection
```bash
cd backend
source .venv/bin/activate
python test_mcp.py
```
**Expected:** Initialize successful, session ID obtained

#### Test 2: Regulation Retrieval
```bash
python test_rag_retrieval.py
```
**Expected:** Regulations retrieved, RegulationReference objects created

#### Test 3: End-to-End Workflow
```bash
curl -X POST http://localhost:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"uploaded_text": "KYC Analyst..."}'
```
**Expected:** 4 quarters, 5-7 activities each, role-specific

#### Test 4: Database Verification
```sql
SELECT quarter, json_array_length(activities) 
FROM recommendations 
ORDER BY created_at DESC LIMIT 4;
```
**Expected:** All quarters have 5-7 activities

---

### Phase B Testing

#### Test 5: Upload Text
```bash
curl -X POST http://localhost:8000/upload/text \
  -d '{"text": "Role description..."}'
```

#### Test 6: Upload File
```bash
curl -X POST http://localhost:8000/upload/file \
  -F "file=@role.pdf"
```

#### Test 7: Regeneration - Single Quarter
```bash
curl -X POST http://localhost:8000/training/regenerate/{id} \
  -d '{"quarters_to_regenerate": ["Q1 Foundation"], ...}'
```
**Expected:** Only Q1 regenerated

#### Test 8: Iteration Limit
```bash
# Regenerate 6 times
# Expected: 6th attempt fails
```

#### Test 9: Frontend Flow
**Manual test:**
1. Open http://localhost:3000
2. Paste text OR upload file
3. Review plan
4. Request changes
5. Submit feedback
6. Verify updated plan

---

## File Manifest

### Backend - New Files
1. `/backend/app/services/mcp_client.py`
2. `/backend/app/services/training_regeneration.py`
3. `/backend/app/routes/upload.py`
4. `/backend/test_mcp.py`
5. `/backend/test_rag_retrieval.py`

### Backend - Modified Files
6. `/backend/app/services/regulation_retrieval.py`
7. `/backend/app/prompts/training_generation.py`
8. `/backend/app/services/recommendation_validation.py`
9. `/backend/app/services/training_recommendation.py`
10. `/backend/app/routes/training.py`
11. `/backend/app/db_models.py`
12. `/backend/requirements.txt`

### Frontend - New Files
13. `/frontend/my-app/components/FeedbackForm.tsx`
14. `/frontend/my-app/components/RegenerationAlert.tsx`

### Frontend - Modified Files
15. `/frontend/my-app/components/Upload.tsx`
16. `/frontend/my-app/app/page.tsx`

**Total:** 16 files (5 new, 11 modified)

---

## Implementation Timeline

### Phase A: Core RAG Integration

| Task | Time | Dependencies |
|------|------|--------------|
| A1: MCP Client | 2-3h | - |
| A2: RAG Retrieval | 2h | A1 |
| A3: Evidence Prompt | 30m | - |
| A4: Validation | 1-2h | - |
| A5: Audit Trail | 30m | - |
| A6: Testing | 2h | A1-A5 |
| **Phase A Total** | **8-10h** | |

### Phase B: Regeneration

| Task | Time | Dependencies |
|------|------|--------------|
| B1: Upload Interface | 1h | Phase A |
| B2: Feedback Prompt | 1h | A3 |
| B3: Regeneration Service | 2-3h | Phase A |
| B4: Regeneration Endpoint | 1-2h | B3 |
| B5: Database Schema | 30m | - |
| B6: Frontend Feedback | 2-3h | - |
| B7: Frontend Upload | 1h | - |
| B8: Iteration Limits | 30m | B3, B6 |
| **Phase B Total** | **9-12h** | |

### Total: 17-22 hours
**Realistic with testing/debugging: 20-25 hours**

---

## Success Criteria

### Phase A Success
- ✅ MCP client connects to workshop-rag
- ✅ Regulations retrieved in real-time
- ✅ 5-7 activities per quarter (evidence-based)
- ✅ Activities role-specific, not generic
- ✅ Traceability in explanations
- ✅ All validation passes
- ✅ Audit trail complete with RAG source

### Phase B Success
- ✅ Text input OR file upload working
- ✅ Feedback form intuitive
- ✅ Regeneration addresses feedback
- ✅ Selected quarters regenerate, others preserved
- ✅ Iteration limit enforced (max 5)
- ✅ Manual editing available as fallback
- ✅ Smooth UI/UX flow

### Overall Success
- ✅ **Explainable:** Clear reasoning
- ✅ **Auditable:** Full trace
- ✅ **Traceable:** Links to evidence
- ✅ **Governed:** Documented decisions
- ✅ **Real-time:** All from RAG
- ✅ **Human-in-loop:** Iterative refinement

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MCP handshake fails | LOW | HIGH | Error handling, testing |
| RAG data quality poor | MEDIUM | MEDIUM | Parsing tunable |
| AI ignores feedback | MEDIUM | MEDIUM | Structured feedback, max 5 attempts |
| Generic activities | LOW | MEDIUM | Validation detects |
| Missing traceability | LOW | HIGH | Strict validation |
| Database migration issues | LOW | MEDIUM | Test on backup |

---

## Outstanding Questions

### Q1: RAG Data Coverage
- What regulations indexed in workshop-rag?
- Comprehensive AMLR 2024/1624?

**Action:** Test search_docs with various queries

### Q2: Frontend Framework
- State management: Local or Redux/Context?

**Action:** Confirm architecture

### Q3: Deployment
- Production environment?
- Environment variables setup?

**Action:** Define deployment plan

### Q4: User Permissions
- Who can approve plans?
- Who can regenerate?

**Action:** Define permission requirements

### Q5: LMS Integration
- After approval, how to LMS?
- Expected format?

**Action:** Clarify LMS integration

---

## Environment Configuration

### Backend .env.local

```
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=openai/gpt-4o-mini

RAG_API_KEY=rag_yo0JsvSubF2r4vX4AD47NB3xE7TnYqAEYs8SOiKz398
RAG_ENDPOINT=https://rag.bluetext.dev/mcp/

DATABASE_URL=sqlite:///vidda.db
```

### Installation

```bash
# Backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend/my-app
npm install

# Database migration
sqlite3 backend/vidda.db < migration.sql
```

### Running

```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload

# Frontend
cd frontend/my-app
npm run dev
```

---

## Document Version

**Version:** 1.0  
**Last Updated:** 2026-05-16  
**Status:** Ready for Execution

---

**END OF IMPLEMENTATION PLAN**
