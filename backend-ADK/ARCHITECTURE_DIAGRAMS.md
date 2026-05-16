# Architecture Diagrams: Agent-Powered Training System

This document contains comprehensive architecture diagrams for the agent-powered compliance training plan generation system with MCP RAG integration.

---

## Table of Contents

1. [High-Level System Architecture](#diagram-1-high-level-system-architecture)
2. [Evidence Gathering Agent Workflow](#diagram-2-evidence-gathering-agent-workflow)
3. [Self-Correcting Training Generator](#diagram-3-self-correcting-training-generator-workflow)
4. [MCP Client Architecture](#diagram-4-mcp-client-architecture)
5. [Data Flow with Explainability & Provenance](#diagram-5-data-flow-with-explainability--provenance)
6. [Complete Traceability Chain](#diagram-6-complete-traceability-chain)

---

## DIAGRAM 1: High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER INPUT: Role Description                         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LANGGRAPH STATEGRAPH ORCHESTRATOR                        │
│                        (Deterministic Backbone)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│  │ parse_documents │─────▶│ extract_roles   │─────▶│   map_risks     │    │
│  │ (deterministic) │      │     (LLM)       │      │ (deterministic) │    │
│  └─────────────────┘      └─────────────────┘      └────────┬────────┘    │
│                                                                │             │
│                                                                ▼             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              🤖 AGENT NODE 1: EVIDENCE GATHERING                      │  │
│  │                     (ReAct Agent)                                     │  │
│  │                                                                        │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │  Agent Strategy:                                              │   │  │
│  │  │  1. List all regulations (scope understanding)               │   │  │
│  │  │  2. Search role-specific regulations                         │   │  │
│  │  │  3. Search each risk type separately (3-5 searches)          │   │  │
│  │  │  4. Retrieve full documents for top results (3-5 docs)       │   │  │
│  │  │  5. Cross-reference and validate                             │   │  │
│  │  │                                                                │   │  │
│  │  │  Tools:                                                        │   │  │
│  │  │  • search_workshop_rag() ──────┐                             │   │  │
│  │  │  • get_regulation_document() ──┼─▶ MCP RAG Endpoint          │   │  │
│  │  │  • list_all_regulations() ─────┘   (workshop-rag)            │   │  │
│  │  │                                                                │   │  │
│  │  │  Output: 10-20 regulations with provenance                   │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────┐                               │
│  │    generate_competencies                │                               │
│  │    (deterministic mapping)              │                               │
│  └─────────────────┬───────────────────────┘                               │
│                    │                                                         │
│                    ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              🤖 AGENT NODE 2: TRAINING GENERATION                     │  │
│  │                     (ReAct Agent)                                     │  │
│  │                                                                        │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │  Agent Strategy:                                              │   │  │
│  │  │  1. Generate initial training plan (with explainability)     │   │  │
│  │  │  2. Validate plan using validation tool                      │   │  │
│  │  │  3. If validation fails:                                      │   │  │
│  │  │     a. Analyze errors                                         │   │  │
│  │  │     b. Adjust generation strategy                            │   │  │
│  │  │     c. Regenerate (max 3 attempts)                           │   │  │
│  │  │  4. Ensure all activities have provenance                    │   │  │
│  │  │                                                                │   │  │
│  │  │  Tools:                                                        │   │  │
│  │  │  • validate_training_plan()                                   │   │  │
│  │  │                                                                │   │  │
│  │  │  Output: 20-28 activities with full explainability           │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────┬─────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────┐      ┌─────────────────┐                             │
│  │attach_references│─────▶│  persist_to_db  │                             │
│  │ (deterministic) │      │ (deterministic) │                             │
│  └─────────────────┘      └─────────────────┘                             │
│                                                                               │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               OUTPUT                                          │
│  • Training Plan (JSON) with 4 quarters, 20-28 activities                   │
│  • Full Explainability (WHY each activity)                                   │
│  • Complete Audit Trail (all tool calls, timestamps)                         │
│  • Agent Performance Stats (tool calls, duration, attempts)                  │
│  • Provenance Chain (MCP query → document → regulation → activity)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **LangGraph StateGraph**: Orchestrates the entire workflow with deterministic control flow
- **Agent Node 1**: Autonomous evidence gathering with 5-10 tool calls to MCP RAG
- **Agent Node 2**: Self-correcting training plan generator with validation loop
- **Hybrid Architecture**: Mix of deterministic steps (fast, predictable) and agent steps (intelligent, adaptive)

---

## DIAGRAM 2: Evidence Gathering Agent Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🤖 EVIDENCE GATHERING AGENT (ReAct)                       │
└─────────────────────────────────────────────────────────────────────────────┘

INPUT: Role + Responsibilities + Risk Types
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ITERATION 1: Understand Scope                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] I need to understand what regulations exist     │   │
│  │ [Action] list_all_regulations(project_id="default")             │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] MCP → list_documents                                │   │
│  │ [Result] 45 regulation documents available                      │   │
│  │          Categories: KYC, AML, Sanctions, Reporting            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ITERATION 2: Role-Based Search                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Search for regulations related to role title    │   │
│  │ [Action] search_workshop_rag(                                   │   │
│  │            query="KYC Analyst customer due diligence",          │   │
│  │            project_id="default")                                │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] MCP → search_docs                                   │   │
│  │ [Result] 12 documents found                                     │   │
│  │   • doc_amlr_5_2_1 (relevance: 0.94) - CDD Requirements        │   │
│  │   • doc_amlr_5_3_1 (relevance: 0.89) - EDD Requirements        │   │
│  │   • doc_kyc_guide (relevance: 0.85) - KYC Best Practices       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ITERATION 3: Risk-Based Search (Risk 1)                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Search for "transaction_monitoring" risk        │   │
│  │ [Action] search_workshop_rag(                                   │   │
│  │            query="transaction monitoring AML requirements")     │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] MCP → search_docs                                   │   │
│  │ [Result] 8 documents found                                      │   │
│  │   • doc_amlr_7_3 (relevance: 0.96) - Transaction Monitoring    │   │
│  │   • doc_amlr_7_4 (relevance: 0.88) - Alert Management          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ITERATION 4: Risk-Based Search (Risk 2)                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Search for "sanctions_screening" risk           │   │
│  │ [Action] search_workshop_rag(                                   │   │
│  │            query="sanctions screening compliance obligations")  │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] MCP → search_docs                                   │   │
│  │ [Result] 6 documents found                                      │   │
│  │   • doc_sanctions_guide (relevance: 0.93)                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ITERATIONS 5-7: Deep Dive - Get Full Documents                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Get full text for top 3 documents               │   │
│  │ [Action] get_regulation_document(document_id="doc_amlr_5_2_1")  │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] MCP → get_document(doc_amlr_5_2_1)                  │   │
│  │ [Result] Full document content:                                 │   │
│  │   AMLR Article 5.2.1: Customer Due Diligence                    │   │
│  │   Financial institutions shall conduct CDD including:           │   │
│  │   (a) Identifying customer and verifying identity using         │   │
│  │       reliable, independent source documents...                 │   │
│  │   [2,400 words of regulation text]                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  │                                                                       │
│  │ [Repeat for doc_amlr_7_3 and doc_sanctions_guide]                   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ITERATION 8: Cross-Reference                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] CDD requires ongoing monitoring, search that    │   │
│  │ [Action] search_workshop_rag(query="ongoing monitoring")        │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] MCP → search_docs                                   │   │
│  │ [Result] Found related doc_amlr_5_4                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  FINAL: Synthesize                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] I have comprehensive evidence, synthesizing...  │   │
│  │ [Output] Structured list of 14 regulations:                     │   │
│  │                                                                  │   │
│  │  {                                                               │   │
│  │    "regulations": [                                              │   │
│  │      {                                                           │   │
│  │        "article": "AMLR Article 5.2.1",                         │   │
│  │        "title": "Customer Due Diligence",                       │   │
│  │        "document_id": "doc_amlr_5_2_1",                         │   │
│  │        "description": "Requires identity verification...",      │   │
│  │        "provenance": {                                           │   │
│  │          "retrieved_via": "get_document",                       │   │
│  │          "search_query": "KYC Analyst customer due diligence",  │   │
│  │          "relevance_score": 0.94,                               │   │
│  │          "mcp_session_id": "sess_abc123",                       │   │
│  │          "retrieved_at": "2026-05-16T10:23:48Z"                 │   │
│  │        }                                                         │   │
│  │      },                                                          │   │
│  │      ... 13 more regulations                                    │   │
│  │    ]                                                             │   │
│  │  }                                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
AGENT STATS: 
  • 8 tool calls
  • 3 MCP searches
  • 3 document retrievals  
  • 1 list operation
  • 1 cross-reference
  • Duration: 8.2 seconds
```

**Agent Behavior:**
- **Multi-strategy search**: Role-based, risk-based, cross-reference
- **Progressive deepening**: List → Search → Retrieve full documents
- **Autonomous decision-making**: Agent decides when to stop gathering evidence
- **Complete provenance**: Every regulation traced back to MCP query

---

## DIAGRAM 3: Self-Correcting Training Generator Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  🤖 TRAINING GENERATION AGENT (ReAct)                        │
└─────────────────────────────────────────────────────────────────────────────┘

INPUT: Role + Regulations + Competencies
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 1: Initial Generation                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Generate training plan with explainability      │   │
│  │ [Generate] Creating 4 quarters with activities...               │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Generated Plan:                                                  │   │
│  │   Q1: 6 activities (Foundations)                                │   │
│  │   Q2: 4 activities (Practical)     ← PROBLEM: Too few          │   │
│  │   Q3: 7 activities (Advanced)                                   │   │
│  │   Q4: 6 activities (Assessment)                                 │   │
│  │                                                                  │   │
│  │ Total: 23 activities                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  VALIDATION CHECK                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Validate the generated plan                     │   │
│  │ [Action] validate_training_plan(plan_json)                      │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] validate_training_plan()                            │   │
│  │ [Result] {                                                       │   │
│  │   "valid": false,                                                │   │
│  │   "errors": [                                                    │   │
│  │     {                                                            │   │
│  │       "type": "insufficient_activities",                        │   │
│  │       "quarter": 2,                                              │   │
│  │       "message": "Q2 has only 4 activities (minimum 5)"         │   │
│  │     },                                                           │   │
│  │     {                                                            │   │
│  │       "type": "missing_explanation",                            │   │
│  │       "activity": "Risk Assessment Workshop",                   │   │
│  │       "field": "reasoning"                                       │   │
│  │     }                                                            │   │
│  │   ]                                                              │   │
│  │ }                                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ATTEMPT 2: Self-Correction                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Validation failed. Analyzing errors:             │   │
│  │   Error 1: Q2 needs 1 more activity                             │   │
│  │   Error 2: Need to add reasoning to one activity                │   │
│  │ [Agent Thought] Regenerating with fixes...                       │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Regenerated Plan:                                                │   │
│  │   Q1: 6 activities (Foundations)                                │   │
│  │   Q2: 6 activities (Practical) ← FIXED: Added "Practical Case  │   │
│  │                                          Studies in CDD"         │   │
│  │   Q3: 7 activities (Advanced)                                   │   │
│  │   Q4: 6 activities (Assessment)                                 │   │
│  │                                                                  │   │
│  │ Total: 25 activities                                            │   │
│  │ All activities now have complete explainability ✓               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  VALIDATION CHECK (Retry)                                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Thought] Validate the corrected plan                     │   │
│  │ [Action] validate_training_plan(plan_json)                      │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Tool Call] validate_training_plan()                            │   │
│  │ [Result] {                                                       │   │
│  │   "valid": true,                                                 │   │
│  │   "errors": [],                                                  │   │
│  │   "warnings": [                                                  │   │
│  │     "Q3 has more activities than other quarters (consider       │   │
│  │      balancing)"                                                 │   │
│  │   ],                                                             │   │
│  │   "suggestions": []                                              │   │
│  │ }                                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  SUCCESS: Output Final Plan                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [Agent Output] Training plan with full explainability:           │   │
│  │                                                                  │   │
│  │ Example Activity:                                                │   │
│  │ {                                                                │   │
│  │   "title": "AML Transaction Monitoring Workshop",               │   │
│  │   "description": "Hands-on training on monitoring systems...",  │   │
│  │   "type": "workshop",                                            │   │
│  │   "duration_hours": 8,                                           │   │
│  │   "explanation": {                                               │   │
│  │     "regulation_basis": ["AMLR Article 7.3"],                   │   │
│  │     "competency_addressed": "Risk Assessment & Analysis",       │   │
│  │     "risk_mitigated": "Transaction Monitoring",                 │   │
│  │     "reasoning": "This activity addresses AMLR Article 7.3      │   │
│  │        requirements for ongoing transaction monitoring. Given   │   │
│  │        the role's responsibility for 'monitoring customer       │   │
│  │        transactions', this training ensures understanding of    │   │
│  │        system operation, alert investigation, and suspicious    │   │
│  │        activity detection."                                      │   │
│  │   },                                                             │   │
│  │   "provenance": {                                                │   │
│  │     "source_regulation": {                                       │   │
│  │       "article": "AMLR Article 7.3",                            │   │
│  │       "document_id": "doc_amlr_7_3",                            │   │
│  │       "retrieved_at": "2026-05-16T10:23:48Z",                   │   │
│  │       "retrieved_via": "get_document",                          │   │
│  │       "search_query": "transaction monitoring AML requirements", │   │
│  │       "mcp_session_id": "sess_abc123"                           │   │
│  │     },                                                           │   │
│  │     "mapped_competency": {                                       │   │
│  │       "competency_id": "comp_risk_assessment",                  │   │
│  │       "mapping_confidence": 0.92                                │   │
│  │     },                                                           │   │
│  │     "generation_metadata": {                                     │   │
│  │       "generated_by": "training_generation_agent",              │   │
│  │       "generation_attempt": 2,                                  │   │
│  │       "validation_passed": true                                 │   │
│  │     }                                                            │   │
│  │   }                                                              │   │
│  │ }                                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
AGENT STATS:
  • 2 generation attempts
  • 4 tool calls (2× validate_training_plan)
  • Duration: 12.4 seconds
  • Final validation: ✅ PASSED
```

**Self-Correction Loop:**
- **Generate**: Create initial plan with explainability
- **Validate**: Check quality using validation tool
- **Analyze**: Understand WHY validation failed
- **Regenerate**: Fix specific issues
- **Retry**: Maximum 3 attempts before escalation

---

## DIAGRAM 4: MCP Client Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LANGGRAPH AGENT NODE                               │
│                         (Evidence Gathering Agent)                           │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ Calls tool: search_workshop_rag()
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGCHAIN TOOL WRAPPER                               │
│                         (mcp_tools.py)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  @tool                                                                       │
│  def search_workshop_rag(query: str, project_id: str) -> str:              │
│      client = get_mcp_client()                                              │
│      results = asyncio.run(client.search_docs(query, project_id))          │
│      # Log to audit trail                                                    │
│      return json.dumps(results)                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MCP CLIENT                                        │
│                         (mcp_client.py)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  class MCPClient:                                                            │
│                                                                               │
│    Session Management:                                                       │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ 1. initialize_session()                                       │        │
│    │    • POST /mcp/ with JSON-RPC initialize request             │        │
│    │    • Extract Mcp-Session-Id from response headers            │        │
│    │    • Send notifications/initialized                           │        │
│    │    • Store session_id for subsequent calls                    │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                               │
│    Tool Methods:                                                             │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ async def search_docs(query, project_id):                    │        │
│    │   • Build JSON-RPC 2.0 request                               │        │
│    │   • Call MCP tool: tools/call with search_docs               │        │
│    │   • Parse SSE stream for response                            │        │
│    │   • Return structured results                                │        │
│    │                                                               │        │
│    │ async def get_document(document_id):                         │        │
│    │   • Build JSON-RPC 2.0 request                               │        │
│    │   • Call MCP tool: tools/call with get_document              │        │
│    │   • Return full document                                      │        │
│    │                                                               │        │
│    │ async def list_documents(project_id):                        │        │
│    │   • Build JSON-RPC 2.0 request                               │        │
│    │   • Call MCP tool: tools/call with list_documents            │        │
│    │   • Return document list                                      │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                               │
│    Error Handling:                                                           │
│    ┌──────────────────────────────────────────────────────────────┐        │
│    │ • Retry with exponential backoff (3 attempts)                │        │
│    │   - 1st attempt: immediate                                    │        │
│    │   - 2nd attempt: wait 1s                                      │        │
│    │   - 3rd attempt: wait 2s                                      │        │
│    │ • Timeout per request: 30s                                    │        │
│    │ • Fallback: Return empty results + log error                 │        │
│    └──────────────────────────────────────────────────────────────┘        │
│                                                                               │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ HTTP + SSE
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WORKSHOP RAG MCP ENDPOINT                                 │
│                  https://rag.bluetext.dev/mcp/                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Protocol: JSON-RPC 2.0 over Server-Sent Events (SSE)                       │
│                                                                               │
│  Required Headers:                                                           │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │ Authorization: Bearer rag_yo0JsvSubF2r4vX4AD47NB3xE7TnYqAE... │          │
│  │ Content-Type: application/json                                │          │
│  │ Accept: application/json, text/event-stream                   │          │
│  │ Mcp-Session-Id: sess_abc123  (after initialization)           │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                               │
│  Available MCP Tools:                                                        │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │ 1. search_docs(query: str, project_id: str)                  │          │
│  │    → Returns: list[Document] with relevance scores           │          │
│  │                                                               │          │
│  │ 2. get_document(document_id: str)                            │          │
│  │    → Returns: Document with full content                     │          │
│  │                                                               │          │
│  │ 3. list_documents(project_id: str)                           │          │
│  │    → Returns: list[DocumentMetadata]                         │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                               │
│  Data Source:                                                                │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │ AMLR Regulations Database                                     │          │
│  │ • Customer Due Diligence (CDD)                               │          │
│  │ • Enhanced Due Diligence (EDD)                               │          │
│  │ • Transaction Monitoring                                      │          │
│  │ • Sanctions Screening                                         │          │
│  │ • Suspicious Activity Reporting                              │          │
│  │ • Record Keeping                                              │          │
│  │ • Risk Assessment                                             │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**MCP Integration:**
- **JSON-RPC 2.0**: Standard protocol for tool calls
- **Server-Sent Events (SSE)**: Real-time streaming protocol
- **Session Management**: Persistent sessions for performance
- **Error Handling**: Retry logic with exponential backoff

---

## DIAGRAM 5: Data Flow with Explainability & Provenance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INPUT: Role Description                             │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────┐
        │  Role: KYC Analyst                                │
        │  Responsibilities:                                │
        │  - Verify customer identity documents            │
        │  - Conduct customer due diligence                │
        │  - Screen against sanctions lists                │
        └──────────────────┬───────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────────────┐
        │  Risks Identified:                                │
        │  - kyc                                            │
        │  - sanctions_screening                            │
        │  - transaction_monitoring                         │
        └──────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│         🤖 EVIDENCE GATHERING AGENT                                       │
│                                                                           │
│  MCP Tool Calls:                                                         │
│  1. search_docs("KYC customer due diligence") → 12 results              │
│  2. search_docs("transaction monitoring AML") → 8 results               │
│  3. get_document("doc_amlr_5_2_1") → Full CDD regulation                │
│  4. get_document("doc_amlr_7_3") → Full transaction monitoring reg      │
│  5. search_docs("sanctions screening") → 6 results                      │
│  6. get_document("doc_sanctions") → Full sanctions regulation           │
│  7. search_docs("ongoing monitoring") → 5 results (cross-ref)           │
│                                                                           │
└──────────────────────┬────────────────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────────────────────┐
        │  REGULATIONS WITH PROVENANCE:                             │
        │                                                            │
        │  Regulation 1:                                             │
        │  ┌────────────────────────────────────────────────────┐  │
        │  │ article: "AMLR Article 5.2.1"                      │  │
        │  │ title: "Customer Due Diligence"                    │  │
        │  │ provenance:                                         │  │
        │  │   document_id: "doc_amlr_5_2_1"                    │  │
        │  │   retrieved_via: "get_document"                    │  │
        │  │   search_query: "KYC customer due diligence"       │  │
        │  │   mcp_session_id: "sess_abc123"                    │  │
        │  │   retrieved_at: "2026-05-16T10:23:48Z"             │  │
        │  │   relevance_score: 0.94                             │  │
        │  └────────────────────────────────────────────────────┘  │
        │                                                            │
        │  Regulation 2:                                             │
        │  ┌────────────────────────────────────────────────────┐  │
        │  │ article: "AMLR Article 7.3"                        │  │
        │  │ title: "Transaction Monitoring"                    │  │
        │  │ provenance: {...similar structure...}               │  │
        │  └────────────────────────────────────────────────────┘  │
        │                                                            │
        │  ... 10 more regulations ...                              │
        └────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────────────────────┐
        │  COMPETENCIES (mapped from regulations):                  │
        │  - Risk Assessment & Analysis                             │
        │  - Customer Due Diligence                                 │
        │  - Transaction Monitoring                                 │
        │  - Sanctions Compliance                                   │
        └────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│         🤖 TRAINING GENERATION AGENT                                      │
│                                                                           │
│  Generation Process:                                                     │
│  1. Analyze regulations + competencies                                   │
│  2. Generate Q1-Q4 activities with explainability                       │
│  3. Validate → FAIL (Q2 only has 4 activities)                          │
│  4. Self-correct: Add 2 more activities to Q2                           │
│  5. Validate → SUCCESS                                                   │
│                                                                           │
└──────────────────────┬────────────────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  TRAINING PLAN WITH EXPLAINABILITY:                               │
        │                                                                    │
        │  Quarter 1: Foundations (6 activities)                            │
        │  ┌────────────────────────────────────────────────────────────┐  │
        │  │ Activity 1:                                                 │  │
        │  │ ┌──────────────────────────────────────────────────────┐  │  │
        │  │ │ title: "AML Regulatory Framework Overview"           │  │  │
        │  │ │ type: "workshop"                                      │  │  │
        │  │ │ duration_hours: 4                                     │  │  │
        │  │ │                                                        │  │  │
        │  │ │ EXPLAINABILITY:                                       │  │  │
        │  │ │ ┌────────────────────────────────────────────────┐  │  │  │
        │  │ │ │ regulation_basis:                               │  │  │  │
        │  │ │ │   - "AMLR Article 5.2.1"                       │  │  │  │
        │  │ │ │   - "AMLR Article 7.3"                         │  │  │  │
        │  │ │ │                                                 │  │  │  │
        │  │ │ │ competency_addressed:                          │  │  │  │
        │  │ │ │   "Risk Assessment & Analysis"                 │  │  │  │
        │  │ │ │                                                 │  │  │  │
        │  │ │ │ risk_mitigated:                                │  │  │  │
        │  │ │ │   "Transaction Monitoring"                     │  │  │  │
        │  │ │ │                                                 │  │  │  │
        │  │ │ │ reasoning:                                      │  │  │  │
        │  │ │ │   "This activity establishes foundational      │  │  │  │
        │  │ │ │    understanding of AMLR requirements.         │  │  │  │
        │  │ │ │    Given the role's responsibility for         │  │  │  │
        │  │ │ │    transaction monitoring, understanding       │  │  │  │
        │  │ │ │    Article 7.3 requirements is critical        │  │  │  │
        │  │ │ │    for effective system operation."            │  │  │  │
        │  │ │ └────────────────────────────────────────────────┘  │  │  │
        │  │ │                                                        │  │  │
        │  │ │ PROVENANCE (TRACEABILITY):                            │  │  │
        │  │ │ ┌────────────────────────────────────────────────┐  │  │  │
        │  │ │ │ source_regulation:                             │  │  │  │
        │  │ │ │   article: "AMLR Article 7.3"                  │  │  │  │
        │  │ │ │   document_id: "doc_amlr_7_3"                  │  │  │  │
        │  │ │ │   retrieved_at: "2026-05-16T10:23:48Z"         │  │  │  │
        │  │ │ │   retrieved_via: "get_document"                │  │  │  │
        │  │ │ │   search_query: "transaction monitoring..."    │  │  │  │
        │  │ │ │   mcp_session_id: "sess_abc123"                │  │  │  │
        │  │ │ │                                                 │  │  │  │
        │  │ │ │ mapped_competency:                             │  │  │  │
        │  │ │ │   competency_id: "comp_risk_assessment"        │  │  │  │
        │  │ │ │   mapping_confidence: 0.92                     │  │  │  │
        │  │ │ │                                                 │  │  │  │
        │  │ │ │ generation_metadata:                           │  │  │  │
        │  │ │ │   generated_by: "training_generation_agent"    │  │  │  │
        │  │ │ │   generation_attempt: 2                        │  │  │  │
        │  │ │ │   validation_passed: true                      │  │  │  │
        │  │ │ └────────────────────────────────────────────────┘  │  │  │
        │  │ └──────────────────────────────────────────────────────┘  │  │
        │  │                                                             │  │
        │  │ ... 5 more activities in Q1 ...                            │  │
        │  └────────────────────────────────────────────────────────────┘  │
        │                                                                    │
        │  Quarter 2-4: ... similar structure ...                          │
        │                                                                    │
        │  Total: 25 activities with FULL explainability & provenance      │
        └────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │  AUDIT TRAIL (Complete decision log):                             │
        │                                                                    │
        │  Step 1: evidence_gathering                                       │
        │    actor: evidence_gathering_agent (react_agent)                  │
        │    tool_calls: [                                                  │
        │      {tool: "search_docs", input: {...}, output: {...}, 1240ms}, │
        │      {tool: "get_document", input: {...}, output: {...}, 850ms}, │
        │      ... 5 more tool calls ...                                    │
        │    ]                                                              │
        │    duration: 8234ms                                               │
        │                                                                    │
        │  Step 2: training_generation                                      │
        │    actor: training_generation_agent (react_agent)                 │
        │    tool_calls: [                                                  │
        │      {tool: "validate", attempt: 1, result: "failed"},           │
        │      {tool: "validate", attempt: 2, result: "success"}           │
        │    ]                                                              │
        │    duration: 12400ms                                              │
        │                                                                    │
        │  Total workflow duration: 24.6 seconds                            │
        └──────────────────────────────────────────────────────────────────┘
```

**Complete Data Flow:**
- **Input → Risks**: Role responsibilities mapped to compliance risk types
- **Risks → Evidence**: Agent searches MCP RAG for relevant regulations
- **Evidence → Competencies**: Regulations mapped to required skills
- **Competencies → Activities**: Agent generates training with explainability
- **Activities → Audit**: Every decision logged with complete provenance

---

## DIAGRAM 6: Complete Traceability Chain

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTIVITY: "AML Transaction Monitoring Workshop"           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌──────────────────────┐        ┌──────────────────────┐
        │   WHY this activity? │        │   WHERE does it      │
        │   (EXPLAINABILITY)   │        │   come from?         │
        │                      │        │   (PROVENANCE)       │
        └──────────┬───────────┘        └──────────┬───────────┘
                   │                               │
                   ▼                               ▼
    ┌──────────────────────────┐      ┌───────────────────────────┐
    │ Regulation Basis:        │      │ Source Regulation:        │
    │ • AMLR Article 7.3       │◀────▶│ • article: "AMLR 7.3"     │
    │                          │      │ • document_id:            │
    │ Competency Addressed:    │      │   "doc_amlr_7_3"          │
    │ • Risk Assessment        │      │                           │
    │                          │      │ Retrieved via:            │
    │ Risk Mitigated:          │      │ • search_docs             │
    │ • Transaction Monitoring │      │ • query: "transaction     │
    │                          │      │   monitoring AML..."      │
    │ Reasoning:               │      │ • timestamp:              │
    │ "This activity           │      │   2026-05-16T10:23:48Z    │
    │  addresses AMLR 7.3      │      │ • session: sess_abc123    │
    │  requirements for        │      │ • relevance: 0.96         │
    │  ongoing transaction     │      │                           │
    │  monitoring..."          │      │ Mapped Competency:        │
    └──────────────────────────┘      │ • comp_id:                │
                                      │   "comp_risk_assessment"  │
                                      │ • confidence: 0.92        │
                                      │                           │
                                      │ Generation:               │
                                      │ • agent:                  │
                                      │   "training_gen_agent"    │
                                      │ • attempt: 2              │
                                      │ • validated: true         │
                                      └───────────┬───────────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────────┐
                                      │ AUDIT TRAIL:              │
                                      │                           │
                                      │ Evidence Gathering:       │
                                      │ ┌───────────────────────┐ │
                                      │ │ [10:23:46] Tool Call  │ │
                                      │ │ search_docs(          │ │
                                      │ │   "transaction        │ │
                                      │ │    monitoring AML")   │ │
                                      │ │ → 8 results           │ │
                                      │ │                       │ │
                                      │ │ [10:23:48] Tool Call  │ │
                                      │ │ get_document(         │ │
                                      │ │   "doc_amlr_7_3")     │ │
                                      │ │ → Full doc retrieved  │ │
                                      │ └───────────────────────┘ │
                                      │                           │
                                      │ Training Generation:      │
                                      │ ┌───────────────────────┐ │
                                      │ │ [10:24:10] Generated  │ │
                                      │ │ activity              │ │
                                      │ │                       │ │
                                      │ │ [10:24:12] Validated  │ │
                                      │ │ → Passed ✓            │ │
                                      │ └───────────────────────┘ │
                                      └───────────────────────────┘
                                                  │
                                                  ▼
                        ┌─────────────────────────────────────────┐
                        │ COMPLETE TRACEABILITY ESTABLISHED:      │
                        │                                         │
                        │ User Input (Role Description)           │
                        │    ↓                                    │
                        │ Risks Identified                        │
                        │    ↓                                    │
                        │ MCP Search Query                        │
                        │    ↓                                    │
                        │ Document Retrieved (doc_amlr_7_3)       │
                        │    ↓                                    │
                        │ Regulation Extracted (AMLR 7.3)         │
                        │    ↓                                    │
                        │ Competency Mapped                       │
                        │    ↓                                    │
                        │ Activity Generated                      │
                        │    ↓                                    │
                        │ Validation Passed                       │
                        │    ↓                                    │
                        │ Final Training Plan                     │
                        │                                         │
                        │ Every step logged with timestamps       │
                        │ Every decision traceable                │
                        │ Every recommendation explainable        │
                        └─────────────────────────────────────────┘
```

**Traceability Chain:**
1. **User Input**: Role description provided by user
2. **Risk Identification**: System maps responsibilities to risk types
3. **MCP Query**: Agent searches RAG with specific query
4. **Document Retrieval**: Full regulation document fetched from MCP
5. **Regulation Extraction**: Specific article identified
6. **Competency Mapping**: Regulation mapped to required competency
7. **Activity Generation**: Training activity created with reasoning
8. **Validation**: Quality checks passed
9. **Final Output**: Activity included in training plan

**Every link in the chain is logged and traceable for regulatory audit purposes.**

---

## Summary: Key Architectural Components

### 1. Orchestration Layer
- **LangGraph StateGraph**: Deterministic backbone ensuring predictable flow
- **Named state transitions**: Clear visibility of workflow progress
- **Hybrid approach**: Mix of deterministic nodes and agent nodes

### 2. Agent Layer
- **Evidence Gathering Agent**: Advanced ReAct with 5-10 tool calls
- **Training Generation Agent**: Self-correcting with validation loop
- **Both agents**: Full provenance tracking and audit logging

### 3. Integration Layer
- **MCP Client**: SSE + JSON-RPC 2.0 protocol implementation
- **Tool Wrappers**: LangChain @tool decorators for agent consumption
- **Session Management**: Persistent MCP sessions with retry logic

### 4. Explainability Layer
- **WHY**: regulation_basis + competency + risk + reasoning
- **WHAT**: Complete activity specifications
- **HOW**: Generation metadata and validation results

### 5. Auditability Layer
- **Audit Logger**: Thread-safe tracking of all decisions
- **Tool Call Logging**: Every MCP call logged with I/O
- **Timestamps**: ISO 8601 format throughout

### 6. Traceability Layer
- **Provenance Chain**: MCP query → document → regulation → activity
- **Document IDs**: Link back to source regulations
- **Session IDs**: Track MCP sessions for regulatory audit

---

## Performance Characteristics

### Evidence Gathering Agent
- **Tool Calls**: 5-10 per invocation
- **Duration**: 8-15 seconds
- **Output**: 10-20 regulations with full provenance

### Training Generation Agent
- **Attempts**: 1-3 (self-correction)
- **Tool Calls**: 2-6 (validation checks)
- **Duration**: 10-20 seconds
- **Output**: 20-28 activities with explainability

### Complete Workflow
- **Total Duration**: 20-45 seconds (depending on role complexity)
- **LLM Calls**: 15-25 total
- **MCP Calls**: 5-10 tool invocations
- **Cost**: ~$0.08-0.12 per plan (with GPT-4o-mini)

---

## Scalability Considerations

### For 80,000 Customers
- **Total Cost**: $6,400 - $9,600 (with GPT-4o-mini)
- **Optimized Cost**: $1,600 - $2,400 (with Gemini Flash)
- **Caching**: 30-50% cost reduction via regulation caching
- **Rate Limiting**: Required to prevent API throttling
- **Database**: PostgreSQL required for concurrent access
- **Monitoring**: Essential for production reliability

---

**End of Architecture Diagrams Document**
