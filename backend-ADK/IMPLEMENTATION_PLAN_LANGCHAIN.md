# Implementation Plan: LangChain + LangGraph Agent-Powered Architecture

**Date:** 2026-05-16  
**Framework:** LangChain + LangGraph  
**Estimated Time:** 27-36 hours  
**Target:** 80,000 customers production system  
**Cost:** $6,400-9,600 for 80K customers (annual)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Advantages & Disadvantages](#advantages--disadvantages)
3. [Technology Stack](#technology-stack)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Implementation Phases](#detailed-implementation-phases)
6. [File Structure](#file-structure)
7. [Code Examples](#code-examples)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Plan](#deployment-plan)
10. [Cost Analysis](#cost-analysis)
11. [Risk Assessment](#risk-assessment)
12. [Migration from Current System](#migration-from-current-system)
13. [Comparison with ADK](#comparison-with-adk)

---

## Executive Summary

This plan implements an **agent-powered training plan generation system** using LangChain and LangGraph, building on your existing codebase with minimal disruption.

### Key Approach
- **Keep existing LangGraph StateGraph** (80% of code unchanged)
- **Add 2 ReAct agents** for evidence gathering and self-correction
- **Integrate MCP RAG** for real-time regulation retrieval
- **Add full explainability and traceability**

### Why This Approach?
- ✅ Minimal learning curve (your team already uses LangGraph)
- ✅ Fast implementation (familiar tools and patterns)
- ✅ Low risk (incremental enhancement, not complete rewrite)
- ✅ Can use existing OpenRouter setup
- ✅ Easy to debug and maintain

### What You'll Get
- 🤖 Evidence Gathering Agent: Autonomous MCP RAG search (5-10 tool calls)
- 🤖 Training Generation Agent: Self-correcting with validation (max 3 attempts)
- 📋 Complete audit trail: Every decision logged with timestamps
- 🔍 Full provenance: MCP query → document → regulation → activity
- ✅ Production-ready: Handles 80K customers with proper infrastructure

---

## Advantages & Disadvantages

### ✅ **ADVANTAGES**

#### 1. Minimal Disruption (Low Risk) ⭐ CRITICAL
**Your team already uses LangGraph** - no learning curve
- Current codebase: Already has `langgraph.graph.StateGraph`
- Same patterns, same tools, same debugging approach
- **80% of existing code stays unchanged** - only 2 nodes become agents
- Existing models, endpoints, database schema unchanged
- **Can roll back easily** - agents can be replaced with simple functions if needed

**Evidence:**
```python
# Current code - UNCHANGED
from langgraph.graph import StateGraph
workflow = StateGraph(WorkflowState)
workflow.add_node('parse_documents', parse_documents)  # Keep as-is
workflow.add_node('extract_roles', extract_roles)      # Keep as-is
workflow.add_node('map_risks', map_risks)              # Keep as-is
# Only these 2 nodes change:
workflow.add_node('evidence_agent', evidence_agent_node)     # ← NEW AGENT
workflow.add_node('training_agent', training_agent_node)     # ← NEW AGENT
# Rest unchanged:
workflow.add_node('persist_to_db', persist_to_db)      # Keep as-is
```

---

#### 2. Fast Implementation ⚡
**Estimated: 27-36 hours** (vs 35-45 for ADK)
- No framework migration needed
- Familiar debugging tools (LangSmith, standard Python debugger)
- Quick to market - can deploy to production faster
- Less testing needed (most code unchanged)

**Time Breakdown:**
```
MCP Client:          4-5 hours
Tool Wrappers:       3-4 hours
Evidence Agent:      6-8 hours
Training Agent:      5-7 hours
Testing:            4-5 hours
Documentation:       3-4 hours
──────────────────────────────
Total:             27-36 hours
```

---

#### 3. Flexibility & Model Agnostic 🔄
**Can use any LLM provider** without code changes
- Currently: OpenRouter (GPT-4o-mini) ✅ Already configured
- Switch to: OpenAI directly (just change URL)
- Switch to: Anthropic Claude (add langchain-anthropic)
- Switch to: Google Gemini (add langchain-google-genai)
- Switch to: Local models (Ollama)

**No vendor lock-in:**
```python
# Easy to switch models - just change config
# Option 1: Keep OpenRouter
llm = ChatOpenAI(
    model="gpt-4o-mini",
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Option 2: Switch to Claude
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    api_key=ANTHROPIC_API_KEY
)

# Option 3: Switch to Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    api_key=GOOGLE_API_KEY
)

# Agent code stays the same!
agent = create_react_agent(llm, tools=[...])
```

---

#### 4. Community & Support 👥
**Large, active community** - help always available
- **LangChain GitHub:** 85K+ stars, 13K+ forks
- **Stack Overflow:** 5,000+ questions answered
- **Discord:** 40K+ members
- **Documentation:** Extensive tutorials, examples, guides
- **Active development:** Weekly updates, bug fixes

**When you get stuck:**
- Search GitHub issues (likely someone hit same problem)
- Ask on Discord (usually get answer within hours)
- Stack Overflow has solutions for common patterns
- Hundreds of blog posts and YouTube tutorials

---

#### 5. Debugging & Observability 🔍
**LangSmith integration** - powerful debugging
- Visual tracing of agent execution (see every step)
- Input/output inspection (see what agent "thinks")
- Performance metrics (latency, token usage per step)
- Cost tracking (per agent, per run)
- Error replay (reproduce failures)

**Standard Python debugging works:**
```python
# Use breakpoints in agent code
def evidence_agent_node(state):
    import pdb; pdb.set_trace()  # Standard Python debugger
    result = run_evidence_gathering(...)
    return result

# Use print statements (familiar debugging)
print(f"Agent made {result['tool_calls']} tool calls")

# Use logging (standard Python logging)
import logging
logging.info(f"Evidence agent found {len(regulations)} regulations")
```

---

#### 6. Incremental Enhancement 📈
**Start small, prove value, expand gradually**
- **Phase 1:** Just add Evidence Gathering Agent (prove MCP RAG works)
- **Phase 2:** Add Training Generation Agent (prove self-correction works)
- **Phase 3:** Add more agents if needed (expand based on results)

**Easy A/B testing:**
```python
# Run old vs new side-by-side
if USE_AGENTS:
    workflow.add_node('evidence_agent', evidence_agent_node)
else:
    workflow.add_node('retrieve_regulations', old_retrieve_node)  # Fallback

# Compare results
old_result = run_old_workflow(text)
new_result = run_new_workflow(text)
compare_quality(old_result, new_result)
```

**Gradual rollout:**
- Week 1: Deploy to staging (internal testing)
- Week 2: Deploy to 10% of production traffic
- Week 3: Deploy to 50% if metrics good
- Week 4: Deploy to 100% or rollback if issues

---

#### 7. Current Infrastructure Compatible ⚙️
**No infrastructure changes needed**
- Keep OpenRouter (already configured, already paying)
- Keep SQLite for dev (migrate to PostgreSQL when ready)
- Keep existing `.env.local` (no new credentials needed)
- Keep FastAPI backend (no API changes)
- Keep React frontend (no UI changes)

**No new services required:**
- No Google Cloud account needed
- No Vertex AI setup needed
- No new billing to set up
- No new service accounts to create

---

### ❌ **DISADVANTAGES**

#### 1. Higher Cost (SIGNIFICANT for 80K customers) 💰 CRITICAL

**Cost per plan: $0.08-0.12** (vs $0.015-0.025 with ADK+Gemini)

**Breakdown:**
```
Evidence Agent:  7 calls × $0.005 = $0.035
Training Agent:  4 calls × $0.009 = $0.036
Other LLM calls: 3 calls × $0.003 = $0.009
────────────────────────────────────────
Total per plan:                  $0.080

With regenerations (1.3x):       $0.104
With high regeneration (1.5x):   $0.120
```

**For 80,000 customers:**
```
Optimistic:   80,000 × $0.080 = $6,400/year
Realistic:    80,000 × $0.104 = $8,320/year
Pessimistic:  80,000 × $0.120 = $9,600/year
```

**Comparison to ADK + Gemini:**
```
LangChain + GPT-4o-mini:  $6,400-9,600
ADK + Gemini Flash:       $1,200-2,000
────────────────────────────────────────
Difference:               $5,200-7,600 MORE expensive per year
```

**Why is it more expensive?**
- GPT-4o-mini costs: $0.15/1M input tokens (Gemini: $0.075)
- GPT-4o-mini costs: $0.60/1M output tokens (Gemini: $0.30)
- **Gemini Flash is 2x cheaper on both input and output**

**Mitigation strategies:**
- Switch to Gemini via LangChain (but loses some OpenRouter flexibility)
- Aggressive caching of regulation searches (30-50% savings)
- Optimize prompts to reduce token usage
- Set strict iteration limits on agents
- Monitor costs weekly, adjust if exceeding budget

---

#### 2. More Boilerplate Code 📝

**~30-40% more lines of code** than ADK equivalent

**Example: Tool Definition**

**LangChain version (verbose):**
```python
from langchain_core.tools import tool
import json

@tool
def search_workshop_rag(query: str, project_id: str = "default") -> str:
    """
    Search the AMLR regulation database via MCP RAG.
    
    Use this tool to find relevant regulations, articles, and compliance requirements.
    
    Args:
        query: Natural language search query
        project_id: Project identifier (default: "default")
    
    Returns:
        JSON string with list of relevant documents
    
    Example queries:
    - "transaction monitoring requirements"
    - "customer due diligence obligations"
    """
    client = get_mcp_client()
    results = asyncio.run(client.search_docs(query, project_id))
    # Must return string, not dict!
    return json.dumps(results, indent=2)

# Total: 22 lines
```

**ADK version (concise):**
```python
from google.adk.tools import FunctionTool

def search_workshop_rag(query: str, project_id: str = "default") -> dict:
    """Search the AMLR regulation database via MCP RAG."""
    client = get_mcp_client()
    return client.search_docs(query, project_id)  # Return dict directly

# Wrap as tool
tool = FunctionTool(func=search_workshop_rag)

# Total: 8 lines (63% less code!)
```

**Why more code?**
- ❌ Must use `@tool` decorator (extra boilerplate)
- ❌ Must return strings (JSON serialization required)
- ❌ Must write detailed docstrings (agent needs them)
- ❌ Manual async handling (`asyncio.run()` in sync context)

---

#### 3. No Built-in Deployment Tools 🚀

**Manual deployment required** - no one-command deploy

**What you need to do:**
```bash
# 1. Write Dockerfile
cat > Dockerfile <<EOF
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
EOF

# 2. Build image
docker build -t vidda-training:latest .

# 3. Push to registry
docker push gcr.io/your-project/vidda-training:latest

# 4. Deploy to Cloud Run
gcloud run deploy vidda-training \
  --image gcr.io/your-project/vidda-training:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENROUTER_API_KEY=... \
  --memory 2Gi \
  --cpu 2

# 5. Configure IAM, secrets, networking manually
gcloud run services add-iam-policy-binding vidda-training \
  --member="allUsers" \
  --role="roles/run.invoker"
```

**With ADK:**
```bash
# ONE command does everything:
agents-cli deploy --target cloud-run --region us-central1
```

**Maintenance burden:**
- Need to maintain Dockerfile
- Need to maintain deployment scripts
- Need to configure IAM roles manually
- Need to set up CI/CD pipeline
- Need to manage secrets
- Need to handle rollbacks manually

---

#### 4. No Built-in Eval Framework 📊

**Must build custom evaluation infrastructure**

**What you need to create:**
```python
# 1. Create evalset format
{
  "test_cases": [
    {
      "input": "Role: KYC Analyst...",
      "expected": {
        "min_activities": 20,
        "min_regulations": 8
      }
    }
  ]
}

# 2. Write evaluation script
def evaluate_plan(plan, expected):
    # Custom logic to check quality
    pass

# 3. Run evaluations manually
for test_case in test_cases:
    result = run_workflow(test_case["input"])
    score = evaluate_plan(result, test_case["expected"])
    results.append(score)

# 4. Manually track improvements
# No standardized metrics, no automated comparison
```

**With ADK:**
```bash
# Built-in eval framework
agents-cli eval run \
  --evalset tests/eval/evalsets/roles.json \
  --agent-path app/agent.py \
  --output results/run1.json

# Standardized metrics automatically
agents-cli eval report results/run1.json
```

**Implications:**
- ⏱️ More time building test infrastructure (5-10 hours)
- 📊 Harder to track improvements over time
- 🔄 Harder to compare agent vs non-agent approaches
- 📈 No standardized metrics for team communication

---

#### 5. Less Optimized for Agents 🤖

**ReAct pattern requires more setup** - not native to LangChain

**Agent creation is verbose:**
```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

# 1. Create LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://vidda.ai",
        "X-Title": "Vidda Training"
    }
)

# 2. Create agent (helper function)
agent = create_react_agent(
    llm,
    tools=[tool1, tool2, tool3],
    state_modifier="System prompt here..."
)

# 3. Invoke with message objects
result = agent.invoke({
    "messages": [HumanMessage(content="Find regulations")]
})

# 4. Extract output from messages
output = result["messages"][-1].content

# Total: ~25 lines for basic agent
```

**ADK version (native agents):**
```python
from google.adk.agents import Agent

# Everything in one clean object
agent = Agent(
    name="evidence_gatherer",
    model="gemini-2.0-flash-exp",
    instruction="Find regulations for the role",
    tools=[tool1, tool2, tool3],
    output_key="regulations"
)

# Execute (native to ADK)
result = agent.run(session)

# Total: 8 lines (68% less code!)
```

**Challenges:**
- More prompt engineering needed (state_modifier less flexible than instruction)
- Tool calling less polished (sometimes needs retry logic)
- Manual message management (HumanMessage, AIMessage objects)
- State passing through messages (not through session.state)

---

#### 6. Scaling Complexity 📈

**Manual implementation of scaling concerns**

**What you need to build yourself:**

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/workflow/run")
@limiter.limit("10/minute")  # Manual rate limit
async def run_workflow(request: Request):
    # Your code
    pass
```

**Caching:**
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def get_regulations_cached(query):
    # Check cache first
    cached = redis_client.get(f"reg:{query}")
    if cached:
        return json.loads(cached)
    
    # If not cached, fetch and cache
    results = search_workshop_rag(query)
    redis_client.setex(f"reg:{query}", 3600, json.dumps(results))
    return results
```

**Monitoring:**
```python
from prometheus_client import Counter, Histogram

request_count = Counter('workflow_requests_total', 'Total workflow requests')
request_duration = Histogram('workflow_duration_seconds', 'Workflow duration')

@request_duration.time()
def run_training_workflow(text):
    request_count.inc()
    # Your code
```

**With ADK:** Most of this is handled automatically or has built-in patterns.

**Time to implement:**
- Rate limiting: 2-3 hours
- Caching layer: 4-6 hours
- Monitoring: 3-5 hours
- Auto-scaling config: 2-3 hours
- **Total: 11-17 hours extra work**

---

#### 7. Gemini Integration Suboptimal 🔌

**Using Gemini via LangChain** - not as good as native

**Problems:**
- ❌ Adapter layer adds latency (extra HTTP requests)
- ❌ Some Gemini-specific features not available
- ❌ Tool calling less optimized
- ❌ Potential compatibility issues with adapter updates

**Current options for Gemini in LangChain:**

**Option A: Via LangChain Google GenAI**
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=GOOGLE_API_KEY
)
# Loses OpenRouter convenience, need Google Cloud setup
```

**Option B: Via LiteLLM (OpenRouter)**
```python
llm = ChatOpenAI(
    model="google/gemini-2.0-flash-exp",
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)
# Extra hop: LangChain → OpenRouter → Google
# Added latency: ~100-200ms per call
```

**ADK native Gemini:**
```python
agent = Agent(
    model="gemini-2.0-flash-exp"  # Direct, no adapter
)
# Native integration, optimized, no latency overhead
```

---

## Technology Stack

### Core Framework
```python
langgraph==0.2.0+          # Workflow orchestration
langchain-core==0.3.0+     # Core abstractions
langchain-openai==0.2.0+   # OpenAI/OpenRouter integration
langchain-community==0.3.0+ # Community tools
```

### LLM Provider Options
```python
# Option 1: OpenRouter (current, recommended)
openai==1.50.0+            # OpenAI SDK works with OpenRouter
# Base URL: https://openrouter.ai/api/v1
# Model: openai/gpt-4o-mini

# Option 2: Direct OpenAI
openai==1.50.0+
# Model: gpt-4o-mini

# Option 3: Anthropic Claude
langchain-anthropic==0.2.0+
# Model: claude-3-5-sonnet-20241022

# Option 4: Google Gemini
langchain-google-genai==2.0.0+
# Model: gemini-2.0-flash-exp
```

### MCP Integration
```python
httpx==0.24.0+             # Async HTTP client for MCP
sseclient-py==1.7.2+       # Server-Sent Events parsing
```

### Database
```python
sqlalchemy==2.0.0+         # ORM (already installed)
alembic==1.13.0+           # Migrations (already installed)
psycopg2-binary==2.9.0+    # PostgreSQL driver (for production)
# SQLite (dev) → PostgreSQL (production)
```

### Observability
```python
langsmith==0.1.0+          # LangChain tracing & debugging (optional)
sentry-sdk==2.0.0+         # Error tracking (optional)
structlog==24.0.0+         # Structured logging (optional)
```

### Testing
```python
pytest==8.0.0+             # Unit tests
pytest-asyncio==0.23.0+    # Async tests
pytest-mock==3.14.0+       # Mocking
```

### Development
```python
python-dotenv==1.0.0+      # Environment variables (already installed)
pydantic==2.0.0+           # Data validation (already installed)
fastapi==0.110.0+          # API framework (already installed)
uvicorn==0.29.0+           # ASGI server (already installed)
```

---

## Architecture Overview

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER / CLIENT                             │
│  Browser → React Frontend → API Calls                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                               │
│  Endpoints:                                                      │
│  • POST /workflow/run (trigger training generation)             │
│  • GET /training/plans/{id} (retrieve plan)                     │
│  • PATCH /training/plans/{id} (approve/edit)                    │
│  • POST /training/regenerate/{id} (AI regeneration)             │
└────────────────────────┬────────────────────────────────────────┘
                         │ Invokes
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LANGGRAPH STATEGRAPH WORKFLOW                       │
│  (Main Orchestrator - Deterministic Control Flow)               │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Deterministic Nodes (Unchanged)                           │ │
│  │                                                            │ │
│  │  parse_documents → extract_roles → map_risks             │ │
│  │         ↓                                                  │ │
│  │  generate_competencies                                    │ │
│  │         ↓                                                  │ │
│  │  attach_references → persist_to_db                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🤖 AGENT NODE 1: Evidence Gathering                       │ │
│  │                                                            │ │
│  │  LangChain ReAct Agent                                    │ │
│  │  ├─ Tools: [search_workshop_rag,                         │ │
│  │  │          get_regulation_document,                      │ │
│  │  │          list_all_regulations]                         │ │
│  │  │                                                         │ │
│  │  └─ Strategy:                                             │ │
│  │     1. List regulations (scope)                           │ │
│  │     2. Search by role                                     │ │
│  │     3. Search by each risk                                │ │
│  │     4. Get full documents                                 │ │
│  │     5. Cross-reference                                    │ │
│  │     Output: 10-20 regulations + provenance               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🤖 AGENT NODE 2: Training Generation                      │ │
│  │                                                            │ │
│  │  LangChain ReAct Agent                                    │ │
│  │  ├─ Tools: [validate_training_plan]                      │ │
│  │  │                                                         │ │
│  │  └─ Strategy:                                             │ │
│  │     1. Generate plan with explainability                  │ │
│  │     2. Validate using tool                                │ │
│  │     3. If fail: analyze errors                            │ │
│  │     4. Regenerate with fixes                              │ │
│  │     5. Max 3 attempts                                     │ │
│  │     Output: Valid training plan                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ MCP RAG      │ │ OpenRouter   │ │ PostgreSQL   │
│ Client       │ │ (GPT-4o-mini)│ │ Database     │
│              │ │              │ │              │
│ - Session    │ │ - LLM calls  │ │ - Roles      │
│ - Search     │ │ - Embeddings │ │ - Plans      │
│ - Get doc    │ │ - Structured │ │ - Activities │
│ - List       │ │   output     │ │ - Audit logs │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Workflow State Flow

```
Input: Role description text
    ↓
┌───────────────────────────────────────────────────────────┐
│ WorkflowState (TypedDict)                                  │
├───────────────────────────────────────────────────────────┤
│ uploaded_text: str                                         │
│ role_data: dict                                            │
│ risks: list[str]                                           │
│ regulations: list[dict]    ← From Evidence Agent         │
│ competencies: dict                                         │
│ training_plan: dict        ← From Training Agent          │
│ recommendations: list[dict]                                │
│ training_plan_id: str                                      │
│ audit_trail: dict          ← NEW: Complete audit log     │
│ agent_stats: dict          ← NEW: Performance metrics    │
└───────────────────────────────────────────────────────────┘
    ↓
Each node receives full state, returns partial update
LangGraph merges updates automatically
    ↓
Output: WorkflowResponse with training plan + audit trail
```

---

## Detailed Implementation Phases

### **PHASE 1: MCP Client Foundation** (4-5 hours)

#### Task 1.1: Implement MCP Client (2-3 hours)

**File:** `/backend/app/services/mcp_client.py`

**Implementation:**

```python
import asyncio
import json
import time
from typing import Any
import httpx
import os
from sseclient import SSEClient

class MCPClient:
    """
    MCP (Model Context Protocol) client for workshop-rag.
    
    Implements:
    - SSE (Server-Sent Events) connection
    - JSON-RPC 2.0 protocol
    - Session management
    - Retry logic with exponential backoff
    - Timeout handling
    """
    
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.session_id: str | None = None
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
        self._request_id = 0
    
    def _next_request_id(self) -> int:
        """Generate next JSON-RPC request ID"""
        self._request_id += 1
        return self._request_id
    
    async def initialize_session(self) -> str:
        """
        Initialize MCP session.
        
        Steps:
        1. POST initialize request
        2. Extract Mcp-Session-Id from headers
        3. Send notifications/initialized
        4. Return session ID
        """
        # Step 1: Initialize
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "vidda-training",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self.http_client.post(
            f"{self.endpoint}/mcp/",
            json=payload
        )
        response.raise_for_status()
        
        # Step 2: Extract session ID
        self.session_id = response.headers.get("Mcp-Session-Id")
        if not self.session_id:
            raise ValueError("No Mcp-Session-Id in response headers")
        
        # Update headers with session ID
        self.http_client.headers["Mcp-Session-Id"] = self.session_id
        
        # Step 3: Send initialized notification
        await self.http_client.post(
            f"{self.endpoint}/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
        )
        
        return self.session_id
    
    async def _call_tool(
        self,
        tool_name: str,
        arguments: dict,
        max_retries: int = 3
    ) -> Any:
        """
        Call MCP tool with retry logic.
        
        Retry strategy:
        - Attempt 1: Immediate
        - Attempt 2: Wait 1 second
        - Attempt 3: Wait 2 seconds
        """
        if not self.session_id:
            await self.initialize_session()
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                response = await self.http_client.post(
                    f"{self.endpoint}/mcp/",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                if "error" in result:
                    raise ValueError(f"MCP error: {result['error']}")
                
                return result.get("result", {})
            
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"MCP call failed after {max_retries} attempts: {e}")
    
    async def search_docs(
        self,
        query: str,
        project_id: str = "default"
    ) -> list[dict]:
        """
        Search for documents using MCP RAG.
        
        Args:
            query: Natural language search query
            project_id: Project identifier
        
        Returns:
            List of document metadata with relevance scores
        """
        result = await self._call_tool(
            "search_docs",
            {"query": query, "project_id": project_id}
        )
        return result.get("documents", [])
    
    async def get_document(self, document_id: str) -> dict:
        """
        Get full document content by ID.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Full document with content and metadata
        """
        result = await self._call_tool(
            "get_document",
            {"document_id": document_id}
        )
        return result.get("document", {})
    
    async def list_documents(self, project_id: str = "default") -> list[dict]:
        """
        List all available documents.
        
        Args:
            project_id: Project identifier
        
        Returns:
            List of document metadata
        """
        result = await self._call_tool(
            "list_documents",
            {"project_id": project_id}
        )
        return result.get("documents", [])
    
    async def close_session(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Global instance (singleton pattern)
_mcp_client: MCPClient | None = None

def get_mcp_client() -> MCPClient:
    """Get or create global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(
            endpoint=os.getenv("RAG_ENDPOINT", "https://rag.bluetext.dev/mcp/"),
            api_key=os.getenv("RAG_API_KEY", "")
        )
    return _mcp_client
```

**Testing:**
```bash
# Test MCP client
python -m pytest tests/services/test_mcp_client.py -v
```

---

#### Task 1.2: Create Audit Logger (1-2 hours)

**File:** `/backend/app/services/audit_logger.py`

```python
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Literal
import json
import threading
import uuid

@dataclass
class ToolCall:
    """Record of a single tool call"""
    tool: str
    timestamp: str
    input: dict
    output: Any
    duration_ms: int
    success: bool = True
    error: str | None = None

@dataclass
class AuditStep:
    """Record of a workflow step"""
    step_id: str
    step: str
    timestamp: str
    actor: str
    actor_type: Literal["deterministic", "react_agent", "llm"]
    inputs: dict
    outputs: dict = field(default_factory=dict)
    tool_calls: list[ToolCall] = field(default_factory=list)
    duration_ms: int = 0
    metadata: dict = field(default_factory=dict)

class AuditLogger:
    """
    Thread-safe audit trail logger.
    
    Tracks all workflow steps, tool calls, and decisions.
    """
    
    def __init__(self):
        self.steps: list[AuditStep] = []
        self._active_steps: dict[str, AuditStep] = {}
        self._lock = threading.Lock()
    
    def start_step(
        self,
        step: str,
        actor: str,
        actor_type: str,
        inputs: dict
    ) -> str:
        """
        Start tracking a workflow step.
        
        Returns:
            step_id: Unique identifier for this step
        """
        step_id = str(uuid.uuid4())
        
        audit_step = AuditStep(
            step_id=step_id,
            step=step,
            timestamp=datetime.utcnow().isoformat() + "Z",
            actor=actor,
            actor_type=actor_type,
            inputs=inputs
        )
        
        with self._lock:
            self._active_steps[step_id] = audit_step
        
        return step_id
    
    def log_tool_call(
        self,
        step_id: str,
        tool: str,
        input: dict,
        output: Any,
        duration_ms: int,
        success: bool = True,
        error: str | None = None
    ):
        """Log a tool call within a step"""
        tool_call = ToolCall(
            tool=tool,
            timestamp=datetime.utcnow().isoformat() + "Z",
            input=input,
            output=output,
            duration_ms=duration_ms,
            success=success,
            error=error
        )
        
        with self._lock:
            if step_id in self._active_steps:
                self._active_steps[step_id].tool_calls.append(tool_call)
    
    def end_step(
        self,
        step_id: str,
        outputs: dict,
        duration_ms: int,
        metadata: dict | None = None
    ):
        """Complete a step and move to completed list"""
        with self._lock:
            if step_id in self._active_steps:
                step = self._active_steps[step_id]
                step.outputs = outputs
                step.duration_ms = duration_ms
                if metadata:
                    step.metadata.update(metadata)
                
                self.steps.append(step)
                del self._active_steps[step_id]
    
    def export_json(self) -> str:
        """Export complete audit trail as JSON"""
        with self._lock:
            data = {
                "steps": [asdict(step) for step in self.steps],
                "total_steps": len(self.steps),
                "total_duration_ms": sum(s.duration_ms for s in self.steps)
            }
        return json.dumps(data, indent=2)
    
    def get_provenance_for_regulation(self, regulation_article: str) -> dict | None:
        """
        Trace back how a specific regulation was retrieved.
        
        Returns provenance chain for a regulation.
        """
        for step in self.steps:
            if step.step == "evidence_gathering":
                for tool_call in step.tool_calls:
                    if tool_call.tool in ["search_docs", "get_document"]:
                        # Check if this tool call retrieved the regulation
                        output = tool_call.output
                        if isinstance(output, list):
                            for doc in output:
                                if regulation_article in str(doc):
                                    return {
                                        "retrieved_via": tool_call.tool,
                                        "search_query": tool_call.input.get("query"),
                                        "document_id": doc.get("id"),
                                        "timestamp": tool_call.timestamp,
                                        "duration_ms": tool_call.duration_ms
                                    }
        return None
```

**Testing:**
```python
# tests/services/test_audit_logger.py
def test_audit_logger():
    logger = AuditLogger()
    
    # Start step
    step_id = logger.start_step(
        step="test_step",
        actor="test_actor",
        actor_type="deterministic",
        inputs={"key": "value"}
    )
    
    # Log tool call
    logger.log_tool_call(
        step_id=step_id,
        tool="test_tool",
        input={"query": "test"},
        output={"result": "success"},
        duration_ms=100
    )
    
    # End step
    logger.end_step(
        step_id=step_id,
        outputs={"output": "complete"},
        duration_ms=200
    )
    
    # Export
    json_str = logger.export_json()
    data = json.loads(json_str)
    
    assert data["total_steps"] == 1
    assert len(data["steps"][0]["tool_calls"]) == 1
```

---

### **PHASE 2: LangChain Tool Wrappers** (3-4 hours)

#### Task 2.1: Create MCP Tools (2-3 hours)

**File:** `/backend/app/services/agents/mcp_tools.py`

```python
from langchain_core.tools import tool
from app.services.mcp_client import get_mcp_client
from app.services.audit_logger import AuditLogger
import asyncio
import json
import time

# Global audit logger (set by agent nodes)
_audit_logger: AuditLogger | None = None

def set_audit_logger(logger: AuditLogger):
    """Set global audit logger for tool calls"""
    global _audit_logger
    _audit_logger = logger

@tool
def search_workshop_rag(query: str, project_id: str = "default") -> str:
    """
    Search the AMLR regulation database via MCP RAG.
    
    Use this tool to find relevant regulations, articles, and compliance requirements.
    Returns top 10 most relevant documents with metadata.
    
    Args:
        query: Natural language search query describing what regulations you need
        project_id: Project identifier (default: "default")
    
    Returns:
        JSON string with list of documents containing:
        - document_id: Unique ID for retrieving full document
        - title: Document title
        - relevance_score: How relevant to query (0-1)
        - excerpt: Brief preview of content
    
    Example queries:
    - "transaction monitoring requirements for financial institutions"
    - "customer due diligence and identity verification obligations"
    - "sanctions screening procedures and timing requirements"
    - "suspicious activity reporting thresholds and procedures"
    
    After finding relevant documents, use get_regulation_document to retrieve full text.
    """
    start_time = time.time()
    client = get_mcp_client()
    
    try:
        # Call MCP (async in sync context)
        results = asyncio.run(client.search_docs(query, project_id))
        
        # Format for agent consumption (top 10 only)
        formatted = [
            {
                "document_id": doc.get("id", ""),
                "title": doc.get("title", "Untitled"),
                "relevance_score": doc.get("score", 0),
                "excerpt": doc.get("excerpt", "")[:200]  # First 200 chars
            }
            for doc in results[:10]
        ]
        
        # Log tool call
        duration_ms = int((time.time() - start_time) * 1000)
        if _audit_logger:
            _audit_logger.log_tool_call(
                step_id="current",
                tool="search_docs",
                input={"query": query, "project_id": project_id},
                output=formatted,
                duration_ms=duration_ms,
                success=True
            )
        
        return json.dumps(formatted, indent=2)
    
    except Exception as e:
        error_msg = f"Error searching workshop RAG: {str(e)}"
        duration_ms = int((time.time() - start_time) * 1000)
        
        if _audit_logger:
            _audit_logger.log_tool_call(
                step_id="current",
                tool="search_docs",
                input={"query": query, "project_id": project_id},
                output=None,
                duration_ms=duration_ms,
                success=False,
                error=error_msg
            )
        
        return json.dumps({"error": error_msg})

@tool
def get_regulation_document(document_id: str) -> str:
    """
    Retrieve full content of a specific regulation document.
    
    Use this tool after search_workshop_rag to get complete regulation text.
    Essential for extracting specific article numbers, requirements, and obligations.
    
    Args:
        document_id: Document identifier from search results
    
    Returns:
        JSON string with full document:
        - document_id: The ID
        - title: Full regulation title
        - content: Complete regulation text
        - articles: List of article numbers mentioned
        - metadata: Additional document information
    
    When to use:
    - After search_workshop_rag identifies relevant documents
    - When you need exact article text and numbers
    - When extracting specific regulatory requirements
    - When building evidence chain for training activities
    """
    start_time = time.time()
    client = get_mcp_client()
    
    try:
        doc = asyncio.run(client.get_document(document_id))
        
        duration_ms = int((time.time() - start_time) * 1000)
        if _audit_logger:
            _audit_logger.log_tool_call(
                step_id="current",
                tool="get_document",
                input={"document_id": document_id},
                output=doc,
                duration_ms=duration_ms,
                success=True
            )
        
        return json.dumps(doc, indent=2)
    
    except Exception as e:
        error_msg = f"Error retrieving document: {str(e)}"
        duration_ms = int((time.time() - start_time) * 1000)
        
        if _audit_logger:
            _audit_logger.log_tool_call(
                step_id="current",
                tool="get_document",
                input={"document_id": document_id},
                output=None,
                duration_ms=duration_ms,
                success=False,
                error=error_msg
            )
        
        return json.dumps({"error": error_msg})

@tool
def list_all_regulations(project_id: str = "default") -> str:
    """
    List all available regulation documents in the database.
    
    Use this tool at the START to understand what regulations are available.
    Helps you plan your search strategy and identify coverage gaps.
    
    Args:
        project_id: Project identifier (default: "default")
    
    Returns:
        JSON string with list of all documents:
        - document_id: Unique identifier for get_regulation_document
        - title: Document title
        - category: Document type/category
        - last_updated: When document was last updated
    
    When to use:
    - At the beginning to see what's available
    - To understand regulation categories and structure
    - To verify coverage across different compliance areas
    - When search results seem too narrow or incomplete
    """
    start_time = time.time()
    client = get_mcp_client()
    
    try:
        docs = asyncio.run(client.list_documents(project_id))
        
        duration_ms = int((time.time() - start_time) * 1000)
        if _audit_logger:
            _audit_logger.log_tool_call(
                step_id="current",
                tool="list_documents",
                input={"project_id": project_id},
                output=docs,
                duration_ms=duration_ms,
                success=True
            )
        
        return json.dumps(docs, indent=2)
    
    except Exception as e:
        error_msg = f"Error listing documents: {str(e)}"
        return json.dumps({"error": error_msg})
```

---

**Due to message length limits, this is Part 1 of the LangChain implementation plan.**

**Would you like me to:**
1. Continue with the rest of the LangChain plan (Phases 3-12)?
2. Start creating the ADK plan?
3. Create a comparison table first?

Let me know how you'd like to proceed! 🚀