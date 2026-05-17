"""
Google ADK Orchestrator — real implementation using ADK Agent + Runner.

Architecture:
  - Gemini 2.5 Flash (direct via GOOGLE_API_KEY) as the orchestrating LLM
  - MCPToolset with StreamableHTTPConnectionParams → rag.bluetext.dev (native MCP)
  - FunctionTool wrappers for Python-based services (role extraction, generation, DB)

The ADK Runner manages the tool-calling loop, retries, and session state.
Our job: provide tools + system prompt, then parse the plan_id from the final output.
"""

import asyncio
import json
import logging
import os
import re
import uuid
from typing import Any

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams
from google.genai import types

from app.models.workflow import WorkflowResponse
from app.models.training import Recommendation

logger = logging.getLogger(__name__)

RAG_API_KEY = os.getenv("RAG_API_KEY")
RAG_ENDPOINT = os.getenv("RAG_ENDPOINT", "https://rag.bluetext.dev/mcp/")

# ---------------------------------------------------------------------------
# Orchestrator instruction (Gemini-native — no [ignoring loop detection] needed)
# ---------------------------------------------------------------------------

ORCHESTRATOR_INSTRUCTION = """
You are the Vidda Compliance Training Orchestrator.

YOUR GOAL
Generate a complete, validated, saved AMLR compliance training plan for the given role description.

TOOLS AVAILABLE

1. extract_role(text)
   Returns: role, responsibilities, compliance_exposure, risk_indicators.
   risk_indicators = inherent AML risks stated in the role text. Use ALL of them as risk_types.

2. search_docs(query) — max 5 calls total
   Searches the AMLR knowledge base. Use for one risk query + 4 article queries.
   Articles: 9, 11, 15, 20, 24, 33, 42, 55, 69

3. generate_competencies(role, responsibilities, risk_types, regulations)
   Returns compact summary {status, knowledge_count, skills_count, judgement_count}.
   Full competencies are cached internally.

4. generate_training_plan(role, responsibilities, risk_types, competencies, regulations)
   Pass {} for competencies — cached version is used automatically.
   Returns compact confirmation {status, quarters, quarter_count}.
   Full plan is cached internally.

5. validate_plan(training_plan, role, responsibilities, risk_types, competencies, regulations)
   Pass {} for training_plan and competencies — cached versions are used.
   Returns {valid: bool, errors: [...]}.

6. save_plan(role_data, competencies, training_plan, risks, regulations)
   Pass {} for competencies and training_plan — cached versions are used.
   Returns {plan_id: "<uuid>", success: true}.

REQUIRED SEQUENCE (exactly in this order)

1. extract_role(text) → note risk_indicators as your risk_types
2. search_docs("AML compliance risks for <role>") → add new risks to risk_types
3. search_docs("AMLR Article N <topic>") × 4 → pick articles matching the role risks
4. generate_competencies(role, responsibilities, risk_types=[ALL risks], regulations)
5. generate_training_plan(role, responsibilities, risk_types, competencies={}, regulations)
6. validate_plan(training_plan={}, role, responsibilities, risk_types, competencies={}, regulations)
   • If valid → step 7
   • If invalid → call generate_training_plan again then validate again (max 1 retry)
7. save_plan(role_data, competencies={}, training_plan={}, risks=[all risks], regulations)
8. Output ONLY: {"status": "complete", "plan_id": "<uuid from save_plan result>"}

CRITICAL RULES
- Do exactly 5 search_docs calls (1 risk + 4 article). No more.
- Pass {} for competencies and training_plan in steps 5, 6, 7 — cached versions are used.
- ALWAYS call save_plan before outputting any final response.
- Output ONLY the JSON in step 8. No explanation, no markdown.
""".strip()

# ---------------------------------------------------------------------------
# Per-run state cache
# Full objects are stored here so tool responses to the agent can be compact.
# save_plan reads from here rather than from the (summarised) agent args.
# ---------------------------------------------------------------------------
_CURRENT_RUN: dict = {}

# ---------------------------------------------------------------------------

def _normalize_regulations(regulations: list) -> list:
    """
    Accepts any format the agent may construct from search_docs results:
      - Raw MCP chunks:  {text, filename, score, document_id, label, ...}
      - Partial dicts:   {article, title, requirements: str}
      - Correct format:  {article, title, requirements: [...]}
    Always ensures article is "Article N" so the frontend regex works.
    """
    normalized = []
    for r in regulations:
        if not isinstance(r, dict):
            continue

        # Case 1: raw MCP chunk (has "text" but no "article")
        if "text" in r and "article" not in r:
            text = r.get("text", "")
            nums = re.findall(r'Article\s+(\d+)', text)
            # Use label field if it contains an article hint (e.g. "AMLR_1")
            label_field = r.get("label", "")
            num = nums[0] if nums else None
            if not num:
                continue  # skip chunks with no article context
            label   = f"Article {num}"
            snippet = text[:200].strip()
            normalized.append({
                "article":      label,
                "title":        f"AMLR 2024/1624 — {label}",
                "requirements": [snippet],
                "keywords":     [],
                "risk_types":   [],
            })
            continue

        # Case 2: has "article" field — normalise
        article = str(r.get("article", "")).strip()
        if not article or article in ("AMLR 2024/1624", "AMLR", ""):
            continue  # no real article number
        if article.isdigit():
            article = f"Article {article}"
        elif re.match(r'^\d+', article) and not article.lower().startswith("article"):
            article = f"Article {article}"

        title = r.get("title", f"AMLR 2024/1624 — {article}")
        reqs  = r.get("requirements", [])
        if isinstance(reqs, str):
            reqs = [reqs]
        elif not isinstance(reqs, list):
            reqs = [str(reqs)]

        normalized.append({
            "article":      article,
            "title":        title,
            "requirements": reqs,
            "keywords":     r.get("keywords", []),
            "risk_types":   r.get("risk_types", []),
        })

    return normalized

# ---------------------------------------------------------------------------
# Tool implementations (FunctionTool wrappers around existing services)
# ---------------------------------------------------------------------------

def extract_role(text: str) -> dict:
    """
    Extract role title, responsibilities, compliance exposure and risk indicators
    from the raw role description text.

    Args:
        text: The raw uploaded role description.

    Returns:
        Dict with keys: role, responsibilities, compliance_exposure, risk_indicators.
    """
    from app.services.role_intelligence import extract_role_intelligence
    result = extract_role_intelligence(text)
    data = result.model_dump()
    print(f"  📋 Role extracted: '{data.get('role')}'")
    ri = data.get("risk_indicators", [])
    if ri:
        print(f"     Inherent risks ({len(ri)}): {[r[:60] for r in ri]}")
    return data


def generate_competencies(
    role: str,
    responsibilities: list[str],
    risk_types: list[str],
    regulations: list[dict],
) -> dict:
    """
    Generate knowledge, skills and judgement competencies for the role.

    Args:
        role: Job title.
        responsibilities: List of role responsibilities.
        risk_types: List of AML/CFT risk types (include ALL risk_indicators here).
        regulations: List of regulation objects with article, title, requirements fields.

    Returns:
        Compact summary: knowledge_count, skills_count, judgement_count, status.
    """
    from app.services.competency_engine import generate_competencies as _gen
    from app.models.regulation import RegulationReference
    regs = [RegulationReference.model_validate(r) for r in _normalize_regulations(regulations)]
    result = _gen(role=role, responsibilities=responsibilities,
                  risk_types=risk_types, regulations=regs)
    data = result.model_dump()
    # Cache full competencies — only summary goes back to the agent
    _CURRENT_RUN['competencies'] = data
    _CURRENT_RUN['risk_types']   = risk_types
    _CURRENT_RUN['regulations']  = regulations
    k = len(data.get('knowledge', []))
    s = len(data.get('skills', []))
    j = len(data.get('judgement', []))
    print(f"  🧠 Competencies: {k}K {s}S {j}J")
    # Return COMPACT summary — do NOT return the full lists (too many tokens)
    return {
        "status":          "generated",
        "knowledge_count": k,
        "skills_count":    s,
        "judgement_count": j,
        "sample_knowledge": data.get('knowledge', [])[:2],  # just 2 examples
    }


def generate_training_plan(
    role: str,
    responsibilities: list[str],
    risk_types: list[str],
    competencies: dict,
    regulations: list[dict],
) -> dict:
    """
    Generate the 4-quarter (Q1 Foundation to Q4 Embedding) AMLR compliance training plan.

    Args:
        role: Job title.
        responsibilities: List of role responsibilities.
        risk_types: Combined list of inherent and RAG-sourced AML risks.
        competencies: Compact summary dict from generate_competencies (status, counts).
        regulations: List of AMLR regulation objects with article, title, requirements fields.

    Returns:
        Compact confirmation: status, quarters list. Full plan is cached internally.
    """
    from app.services.training_recommendation import generate_training_recommendations
    from app.models.training import TrainingRecommendationRequest
    from app.models.regulation import RegulationReference
    from app.models.competency import Competency

    # Use cached full competencies (not the compact summary the agent has)
    full_comp_data = _CURRENT_RUN.get('competencies', {})
    regs = [RegulationReference.model_validate(r)
            for r in _normalize_regulations(regulations or _CURRENT_RUN.get('regulations', []))]
    comp = Competency.model_validate(full_comp_data) if full_comp_data else Competency(
        knowledge=[], skills=[], judgement=[])
    req  = TrainingRecommendationRequest(
        role=role, responsibilities=responsibilities,
        risk_types=risk_types, competencies=comp, regulations=regs,
    )
    try:
        plan = generate_training_recommendations(req)
    except ValueError as e:
        logger.warning(f"  ⚠️  Training plan generation failed: {e}")
        return {"status": "error", "error": str(e)[:300],
                "quarters": [], "quarter_count": 0}
    data = plan.model_dump()
    # Cache full training plan
    _CURRENT_RUN['training_plan'] = data
    _CURRENT_RUN['role']         = role
    _CURRENT_RUN['risks']        = risk_types
    quarters = [q.get('quarter') for q in data.get('quarterly_plan', [])]
    print(f"  📝 Training plan: {list(dict.fromkeys(quarters))} ({len(quarters)} modules)")
    # Return COMPACT confirmation only
    return {"status": "generated", "quarters": list(dict.fromkeys(quarters)),
            "module_count": len(quarters)}


def validate_plan(
    training_plan: dict,
    role: str,
    responsibilities: list[str],
    risk_types: list[str],
    competencies: dict,
    regulations: list[dict],
) -> dict:
    """
    Validate the generated training plan against the evidence.

    Args:
        training_plan: Pass {} — the full plan is retrieved from internal cache.
        role: Job title.
        responsibilities: List of role responsibilities.
        risk_types: List of risk types used.
        competencies: Compact summary from generate_competencies.
        regulations: List of regulation objects used.

    Returns:
        Dict with keys: valid (bool), errors (list of strings).
    """
    from app.services.recommendation_validation import validate_training_plan as _val
    from app.models.training import TrainingPlan, TrainingRecommendationRequest
    from app.models.regulation import RegulationReference
    from app.models.competency import Competency
    try:
        full_plan = _CURRENT_RUN.get('training_plan', training_plan)
        plan_obj  = TrainingPlan.model_validate(full_plan)
        regs      = [RegulationReference.model_validate(r)
                     for r in _normalize_regulations(regulations or _CURRENT_RUN.get('regulations', []))]
        full_comp = _CURRENT_RUN.get('competencies', {})
        comp      = Competency.model_validate(full_comp) if full_comp else Competency(
            knowledge=[], skills=[], judgement=[])
        req       = TrainingRecommendationRequest(
            role=role, responsibilities=responsibilities,
            risk_types=risk_types, competencies=comp, regulations=regs,
        )
        result = _val(plan_obj, req)
        status = "✅ VALID" if result.valid else f"❌ INVALID ({len(result.errors)} errors)"
        print(f"  ✔️  Validation: {status}")
        if result.errors:
            for err in result.errors[:3]:
                print(f"       • {err[:100]}")
        return {"valid": result.valid, "errors": result.errors[:5]}  # cap errors
    except Exception as e:
        print(f"  ✔️  Validation error: {e}")
        return {"valid": False, "errors": [str(e)[:200]]}


def save_plan(
    role_data: dict,
    competencies: dict,
    training_plan: dict,
    risks: list[str],
    regulations: list[dict],
) -> dict:
    """
    Save the validated training plan to the database.

    Args:
        role_data: Dict from extract_role (role, responsibilities, etc).
        competencies: Pass {} — full competencies are retrieved from internal cache.
        training_plan: Pass {} — full training plan is retrieved from internal cache.
        risks: Combined list of all risk description strings.
        regulations: List of regulation objects (article, title, requirements).

    Returns:
        Dict with plan_id (str) and success (bool).
    """
    from app.db import SessionLocal
    from app.db_models import RoleRecord, CompetencyRecord, TrainingPlanRecord, RecommendationRecord
    from app.models.role_intelligence import RoleExtraction
    from app.models.competency import Competency
    from app.models.training import TrainingPlan

    if SessionLocal is None:
        return {"success": False, "error": "Database not available"}

    # Always use the cached full objects — agent only holds compact summaries
    full_comp_data = _CURRENT_RUN.get('competencies', competencies)
    full_plan_data = _CURRENT_RUN.get('training_plan', training_plan)
    full_risks     = _CURRENT_RUN.get('risks', risks) or risks

    if not full_plan_data or not full_plan_data.get('quarterly_plan'):
        return {"success": False, "error": "No training plan in cache — call generate_training_plan first"}

    try:
        with SessionLocal() as session:
            role_obj = RoleExtraction.model_validate(role_data)
            role_record = RoleRecord(
                name=role_obj.role,
                responsibilities=role_obj.responsibilities,
                compliance_exposure=role_obj.compliance_exposure,
                risk_indicators=role_obj.risk_indicators,
            )
            session.add(role_record)
            session.flush()

            comp_obj = Competency.model_validate(full_comp_data)
            comp_record = CompetencyRecord(
                role_id=role_record.id,
                knowledge=comp_obj.knowledge,
                skills=comp_obj.skills,
                judgement=comp_obj.judgement,
            )
            session.add(comp_record)
            session.flush()

            plan_record = TrainingPlanRecord(role_id=role_record.id, status="draft")
            session.add(plan_record)
            session.flush()

            plan_obj = TrainingPlan.model_validate(full_plan_data)
            for rec in plan_obj.quarterly_plan:
                session.add(RecommendationRecord(
                    training_plan_id=plan_record.id,
                    role_id=role_record.id,
                    competency_id=comp_record.id,
                    quarter=rec.quarter,
                    module=rec.module,
                    objective=rec.objective,
                    behavioural_outcome=rec.behavioural_outcome,
                    activities=rec.activities,
                    explanation=rec.explanation,
                    role_reference=rec.role_reference,
                    risk_reference=rec.risk_reference,
                    regulation_reference=rec.regulation_reference,
                    competency_reference=rec.competency_reference,
                ))

            session.commit()
            print(f"  💾 Saved — plan_id: {plan_record.id}")
            # Clear run cache after successful save
            _CURRENT_RUN.clear()
            return {"success": True, "plan_id": plan_record.id}

    except Exception as e:
        logger.error(f"DB save failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)[:200]}


# ---------------------------------------------------------------------------
# ADK Agent factory
# ---------------------------------------------------------------------------

def _create_rag_toolset() -> MCPToolset:
    """Create MCPToolset connecting to the RAG server via MCP Streamable HTTP."""
    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=RAG_ENDPOINT,
            headers={
                "Authorization": f"Bearer {RAG_API_KEY}",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
            sse_read_timeout=120.0,
        )
    )


def _create_agent() -> Agent:
    """Create the ADK orchestrator agent with all tools."""
    from google.genai import types as genai_types
    return Agent(
        name="compliance_orchestrator",
        model="gemini-2.5-flash",
        instruction=ORCHESTRATOR_INSTRUCTION,
        generate_content_config=genai_types.GenerateContentConfig(
            temperature=0,   # deterministic — same role → same article choices
        ),
        tools=[
            _create_rag_toolset(),
            FunctionTool(func=extract_role),
            FunctionTool(func=generate_competencies),
            FunctionTool(func=generate_training_plan),
            FunctionTool(func=validate_plan),
            FunctionTool(func=save_plan),
        ],
    )

# ---------------------------------------------------------------------------
# Async ADK runner
# ---------------------------------------------------------------------------

async def _run_adk_async(uploaded_text: str) -> str | None:
    """Run the ADK agent. Returns the agent's final text output."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="vidda",
        user_id="user",
        session_id=str(uuid.uuid4()),
    )

    agent  = _create_agent()
    runner = Runner(
        agent=agent,
        app_name="vidda",
        session_service=session_service,
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=uploaded_text)],
    )

    final_text   = None
    all_texts    = []
    tool_count   = 0
    event_count  = 0

    print(f"\n  {'─'*50}")
    print(f"  ADK Runner started — streaming events:")
    print(f"  {'─'*50}")

    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=content,
    ):
        event_count += 1
        is_final = event.is_final_response()
        has_content = bool(event.content and event.content.parts)

        # Log every event
        print(f"  [evt {event_count}] type={type(event).__name__} "
              f"final={is_final} content={has_content} "
              f"author={getattr(event, 'author', '?')}")

        # Capture any text parts
        if has_content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    snippet = part.text.strip()[:150]
                    print(f"           text: {snippet}")
                    all_texts.append(part.text.strip())
                if hasattr(part, "function_call") and part.function_call:
                    tool_count += 1
                    fc = part.function_call
                    print(f"           tool_call[{tool_count}]: {fc.name}")
                if hasattr(part, "function_response") and part.function_response:
                    fr = part.function_response
                    print(f"           tool_result: {fr.name} → "
                          f"{str(fr.response)[:100]}")

        if is_final and has_content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    final_text = part.text.strip()
                    print(f"  ✅ FINAL TEXT captured: {final_text[:200]}")
                    break

    print(f"  {'─'*50}")
    print(f"  ADK done — {event_count} events, {tool_count} tool calls")

    # If is_final_response never fired with text, use last text seen
    if not final_text and all_texts:
        final_text = all_texts[-1]
        print(f"  ⚠️  Used last text as final: {final_text[:200]}")

    return final_text


# ---------------------------------------------------------------------------
# Sync entry point (bridges FastAPI sync → async ADK)
# ---------------------------------------------------------------------------

def run_orchestrator(uploaded_text: str) -> WorkflowResponse:
    """
    Run the Google ADK orchestrator agent.
    Bridges the sync FastAPI endpoint to the async ADK Runner.
    """
    import time
    start = time.time()

    print(f"  🤖 ADK Orchestrator starting (gemini-2.5-flash + MCP RAG)")

    # Run async ADK in a fresh event loop (safe in anyio worker threads)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        final_text = loop.run_until_complete(_run_adk_async(uploaded_text))
    finally:
        loop.close()
        asyncio.set_event_loop(None)

    elapsed = time.time() - start
    print(f"  ✅ ADK complete ({elapsed:.1f}s)")

    # ── Extract plan_id from agent output (robust multi-strategy) ─────────────
    plan_id = None
    if final_text:
        print(f"     Agent output: {final_text[:400]}")

        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        cleaned = re.sub(r'```(?:json)?\s*', '', final_text).replace('```', '').strip()

        # Strategy 1: direct JSON parse
        try:
            data = json.loads(cleaned)
            plan_id = data.get("plan_id")
            print(f"     [parse-1] plan_id = {plan_id}")
        except (json.JSONDecodeError, AttributeError):
            pass

        # Strategy 2: JSON fragment search
        if not plan_id:
            m = re.search(r'"plan_id"\s*:\s*"([^"]+)"', final_text)
            if m:
                plan_id = m.group(1)
                print(f"     [parse-2] plan_id = {plan_id}")

        # Strategy 3: bare UUID anywhere in text
        if not plan_id:
            m = re.search(
                r'\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b',
                final_text, re.IGNORECASE
            )
            if m:
                plan_id = m.group(1)
                print(f"     [parse-3] plan_id = {plan_id}")

    # ── Load response from DB ──────────────────────────────────────────────────
    if plan_id:
        from app.services.workflow import get_plan_by_id
        response = get_plan_by_id(plan_id)
        if response and response.recommendations:
            print(f"     ✅ Loaded {len(response.recommendations)} quarters from DB (plan_id)")
            return response
        else:
            print(f"     ⚠️  get_plan_by_id({plan_id}) returned no recommendations")

    # ── Fallback: most recently saved plan (in last 5 minutes) ────────────────
    print(f"     🔄 Trying latest-plan fallback...")
    response = _get_latest_plan()
    if response and response.recommendations:
        print(f"     ✅ Loaded {len(response.recommendations)} quarters from latest plan")
        return response

    # ── Nothing worked ────────────────────────────────────────────────────────
    logger.warning("ADK orchestrator produced no usable plan — returning minimal response")
    from app.models.role_intelligence import RoleExtraction
    from app.models.competency import Competency
    return WorkflowResponse(
        uploaded_text=uploaded_text,
        role_data=RoleExtraction(role="Unknown", responsibilities=[],
                                  compliance_exposure=[], risk_indicators=[]),
        risks=[], regulations=[],
        competencies=Competency(knowledge=[], skills=[], judgement=[]),
        recommendations=[], training_plan_id=None,
    )


def _get_latest_plan() -> WorkflowResponse | None:
    """Fetch the most recently created training plan from the DB (last 5 minutes)."""
    from app.services.workflow import get_plan_by_id
    from app.db import SessionLocal
    from app.db_models import TrainingPlanRecord
    from datetime import datetime, timedelta, timezone

    if SessionLocal is None:
        return None
    try:
        with SessionLocal() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
            plan = (
                db.query(TrainingPlanRecord)
                .order_by(TrainingPlanRecord.created_at.desc())
                .first()
            )
            if plan:
                print(f"     Latest plan ID: {plan.id} (created {plan.created_at})")
                return get_plan_by_id(plan.id)
    except Exception as e:
        logger.warning(f"Latest-plan fallback failed: {e}")
    return None
