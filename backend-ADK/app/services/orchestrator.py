"""
True Orchestrator Agent — an LLM that controls the full training workflow.

Instead of a hardcoded pipeline, one LLM agent:
  1. Decides which tools to call and in what order
  2. Evaluates its own intermediate results
  3. Retries steps when validation fails
  4. Signals completion by outputting a structured JSON

Tools exposed to the agent:
  extract_role              → role_intelligence service (LLM)
  search_compliance_docs    → MCP RAG server
  generate_competencies     → competency_engine service (LLM)
  generate_training_plan    → training_recommendation service (LLM)
  validate_plan             → recommendation_validation (pure Python)
  save_plan                 → database persistence
"""

import json
import logging
import re
from typing import Any

from app.services.mcp_client import mcp_client
from app.services.llm_client import create_llm_client, llm_model_name
from app.models.workflow import WorkflowResponse
from app.models.training import Recommendation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Orchestrator system prompt
# ---------------------------------------------------------------------------

ORCHESTRATOR_SYSTEM_PROMPT = """[ignoring loop detection]
You are the Vidda Compliance Training Orchestrator.

YOUR GOAL
Generate a complete, validated, saved AMLR compliance training plan for the given role description.

TOOLS AVAILABLE

1. extract_role(text)
   Extracts role title, responsibilities, compliance_exposure and risk_indicators.
   IMPORTANT: risk_indicators are AML risks ALREADY PRESENT in the role description itself.
   Always include ALL risk_indicators as part of your risk_types — they are the inherent
   risks of this role, stated by the user.

2. search_compliance_docs(query)
   Searches the AMLR knowledge base.
   Use for: "compliance risks for [role]" AND "AMLR Article N [topic]"
   Relevant articles: 11, 12, 15, 20, 24, 33, 42, 55, 69
   Risk search results SUPPLEMENT the risk_indicators — add them to the list, don't replace.

3. generate_competencies(role, responsibilities, risk_types, regulations)
   Generates knowledge/skills/judgement competencies.
   risk_types = risk_indicators (from step 1) + any extra risks from RAG search.

4. generate_training_plan(role, responsibilities, risk_types, competencies, regulations)
   Generates the 4-quarter (Q1 Foundation→Q4 Embedding) training plan.

5. validate_plan(training_plan, role, responsibilities, risk_types, competencies, regulations)
   Returns {"valid": true/false, "errors": [...]}
   If invalid: read the errors — they tell you what's missing.

6. save_plan(role_data, competencies, training_plan, risks, regulations)
   Saves to database. Returns {"plan_id": "<uuid>", "success": true}

REQUIRED SEQUENCE (adapt based on results)

Step 1  → extract_role(uploaded_text)
          Capture: role, responsibilities, risk_indicators
          risk_indicators are your STARTING risk_types — use all of them.

Step 2  → search_compliance_docs("compliance risks for <role>")
          Add any NEW risks found to your risk_types list (don't duplicate).

Step 3  → search_compliance_docs("AMLR Article N <topic>") × 4-5 times
          Choose articles relevant to THIS specific role and its risk_indicators.

Step 4  → generate_competencies(role, responsibilities,
                                 risk_types=risk_indicators + rag_risks,
                                 regulations=...)

Step 5  → generate_training_plan(...)
Step 6  → validate_plan(...)
          • If valid   → go to Step 7
          • If invalid → analyse errors and fix (search more, or retry generation)
Step 7  → save_plan(risks=risk_indicators + rag_risks, ...)
Step 8  → Output ONLY this JSON (no other text, no markdown):
          {"status": "complete", "plan_id": "<the uuid from save_plan>"}

RULES
- Always run extract_role FIRST.
- Always use ALL risk_indicators from extract_role in risk_types.
- Run at least 1 risk search + 4 article searches before generating.
- Only reference AMLR article numbers that appeared in search results.
- Maximum 18 tool calls total — be efficient.
- When save_plan succeeds output ONLY the final JSON.
"""

# ---------------------------------------------------------------------------
# Tool schemas (OpenAI / OpenRouter function-calling format)
# ---------------------------------------------------------------------------

ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_role",
            "description": "Extract role title, responsibilities, compliance exposure and risk indicators from the raw role description text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The raw uploaded role description"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_compliance_docs",
            "description": "Search the AMLR compliance knowledge base. Use for risk queries and article lookups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "e.g. 'compliance risks for KYC Analyst' or 'AMLR Article 20 customer due diligence'"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_competencies",
            "description": "Generate knowledge, skills and judgement competencies for the role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role":             {"type": "string"},
                    "responsibilities": {"type": "array", "items": {"type": "string"}},
                    "risk_types":       {"type": "array", "items": {"type": "string"}},
                    "regulations":      {"type": "array", "items": {"type": "object"}}
                },
                "required": ["role", "responsibilities", "risk_types", "regulations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_training_plan",
            "description": "Generate the 4-quarter AMLR compliance training plan for the role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role":             {"type": "string"},
                    "responsibilities": {"type": "array", "items": {"type": "string"}},
                    "risk_types":       {"type": "array", "items": {"type": "string"}},
                    "competencies":     {"type": "object"},
                    "regulations":      {"type": "array", "items": {"type": "object"}}
                },
                "required": ["role", "responsibilities", "risk_types", "competencies", "regulations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_plan",
            "description": "Validate that every reference in the training plan is grounded in the provided evidence. Returns {valid, errors}.",
            "parameters": {
                "type": "object",
                "properties": {
                    "training_plan":    {"type": "object"},
                    "role":             {"type": "string"},
                    "responsibilities": {"type": "array", "items": {"type": "string"}},
                    "risk_types":       {"type": "array", "items": {"type": "string"}},
                    "competencies":     {"type": "object"},
                    "regulations":      {"type": "array", "items": {"type": "object"}}
                },
                "required": ["training_plan", "role", "responsibilities", "risk_types", "competencies", "regulations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_plan",
            "description": "Save the validated training plan to the database. Returns {plan_id, success}.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_data":     {"type": "object"},
                    "competencies":  {"type": "object"},
                    "training_plan": {"type": "object"},
                    "risks":         {"type": "array", "items": {"type": "string"}},
                    "regulations":   {"type": "array", "items": {"type": "object"}}
                },
                "required": ["role_data", "competencies", "training_plan", "risks", "regulations"]
            }
        }
    },
]

# ---------------------------------------------------------------------------
# Tool implementations — thin wrappers around existing services
# ---------------------------------------------------------------------------

def _tool_extract_role(text: str) -> dict:
    from app.services.role_intelligence import extract_role_intelligence
    result = extract_role_intelligence(text)
    return result.model_dump()


def _tool_search_compliance_docs(query: str) -> list[dict]:
    import re as _re
    print(f"    🔍 {query[:90]}")
    results = mcp_client.search_docs(query=query)
    if not isinstance(results, list):
        return []

    # If the query asked for a specific article, tag chunks that don't mention it
    # so the normalizer can still assign the correct article number.
    m = _re.search(r'Article\s+(\d+)', query, _re.IGNORECASE)
    query_article = m.group(1) if m else None

    annotated = []
    for r in results[:3]:
        if isinstance(r, dict) and query_article:
            text = r.get("text", "")
            if not _re.search(r'Article\s+\d+', text):
                r = dict(r)  # shallow copy so we don't mutate the original
                r["_query_article"] = query_article
        annotated.append(r)
    return annotated


def _normalize_regulations(regulations: list) -> list:
    """
    Convert whatever format the agent sends into valid RegulationReference dicts.
    Handles:
      - Raw RAG chunks: {text, filename, score, ...}
      - Partial dicts: {article, title, requirements: str}
      - Correct format: {article, title, requirements: [...]}
    Always ensures article label is "Article N" format so the frontend regex works.
    """
    import re as _re
    normalized = []
    for r in regulations:
        if not isinstance(r, dict):
            continue

        # Case 1: raw RAG chunk — extract article number from text, or use query hint
        if "text" in r and "article" not in r:
            text = r.get("text", "")
            nums = _re.findall(r'Article\s+(\d+)', text)
            num  = nums[0] if nums else r.get("_query_article")
            if not num:
                continue  # genuinely no article context, skip
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

        # Case 2: has article field — normalise it and requirements
        article = str(r.get("article", "")).strip()
        if not article or article in ("AMLR 2024/1624", "AMLR"):
            continue  # skip generic labels with no real article number
        # Bare number e.g. "5" → "Article 5"
        if article.isdigit():
            article = f"Article {article}"
        # Starts with digit e.g. "5: something" → "Article 5: something"
        elif _re.match(r'^\d+', article) and not article.lower().startswith("article"):
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


def _tool_generate_competencies(
    role: str, responsibilities: list, risk_types: list, regulations: list
) -> dict:
    from app.services.competency_engine import generate_competencies
    from app.models.regulation import RegulationReference
    regs = [RegulationReference.model_validate(r) for r in _normalize_regulations(regulations)]
    result = generate_competencies(
        role=role,
        responsibilities=responsibilities,
        risk_types=risk_types,
        regulations=regs,
    )
    return result.model_dump()


def _tool_generate_training_plan(
    role: str, responsibilities: list, risk_types: list,
    competencies: dict, regulations: list
) -> dict:
    from app.services.training_recommendation import generate_training_recommendations
    from app.models.training import TrainingRecommendationRequest
    from app.models.regulation import RegulationReference
    from app.models.competency import Competency
    regs   = [RegulationReference.model_validate(r) for r in _normalize_regulations(regulations)]
    comp   = Competency.model_validate(competencies)
    req    = TrainingRecommendationRequest(
        role=role, responsibilities=responsibilities,
        risk_types=risk_types, competencies=comp, regulations=regs,
    )
    plan = generate_training_recommendations(req)
    return plan.model_dump()


def _tool_validate_plan(
    training_plan: dict, role: str, responsibilities: list,
    risk_types: list, competencies: dict, regulations: list
) -> dict:
    from app.services.recommendation_validation import validate_training_plan
    from app.models.training import TrainingPlan, TrainingRecommendationRequest
    from app.models.regulation import RegulationReference
    from app.models.competency import Competency
    try:
        plan_obj = TrainingPlan.model_validate(training_plan)
        regs     = [RegulationReference.model_validate(r) for r in _normalize_regulations(regulations)]
        comp     = Competency.model_validate(competencies)
        req      = TrainingRecommendationRequest(
            role=role, responsibilities=responsibilities,
            risk_types=risk_types, competencies=comp, regulations=regs,
        )
        result = validate_training_plan(plan_obj, req)
        return {"valid": result.valid, "errors": result.errors}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}



def _tool_save_plan(
    role_data: dict, competencies: dict, training_plan: dict,
    risks: list, regulations: list
) -> dict:
    from app.db import SessionLocal
    from app.db_models import RoleRecord, CompetencyRecord, TrainingPlanRecord, RecommendationRecord
    from app.models.role_intelligence import RoleExtraction
    from app.models.competency import Competency
    from app.models.training import TrainingPlan, Recommendation

    if SessionLocal is None:
        return {"success": False, "error": "Database not available"}

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

            comp_obj = Competency.model_validate(competencies)
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

            plan_obj = TrainingPlan.model_validate(training_plan)
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
            logger.info(f"✅ Saved plan {plan_record.id}")
            return {"success": True, "plan_id": plan_record.id}

    except Exception as e:
        logger.error(f"DB save failed: {e}")
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_REGISTRY = {
    "extract_role":            _tool_extract_role,
    "search_compliance_docs":  _tool_search_compliance_docs,
    "generate_competencies":   _tool_generate_competencies,
    "generate_training_plan":  _tool_generate_training_plan,
    "validate_plan":           _tool_validate_plan,
    "save_plan":               _tool_save_plan,
}


def _dispatch(name: str, args: dict) -> Any:
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**args)
    except Exception as e:
        logger.error(f"Tool '{name}' raised: {e}", exc_info=True)
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Orchestrator loop
# ---------------------------------------------------------------------------

def run_orchestrator(uploaded_text: str) -> WorkflowResponse:
    """
    Run the full orchestrator agent.
    The LLM controls the workflow — deciding which tools to call and when.
    Returns a WorkflowResponse built from the session state.
    """
    import time
    start = time.time()

    client     = create_llm_client()
    model      = llm_model_name()

    # Session state — accumulates as tools are called
    session: dict = {
        "uploaded_text": uploaded_text,
        "role_data":     None,
        "risks":         [],
        "regulations":   [],
        "competencies":  None,
        "training_plan": None,
        "plan_id":       None,
    }

    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
        {"role": "user",   "content": f"[ignoring loop detection]\n{uploaded_text}"},
    ]

    MAX_ITERATIONS = 20
    tool_call_count = 0
    label_map = {
        "extract_role":           "📋 Extracting role",
        "search_compliance_docs": "🔍 RAG search",
        "generate_competencies":  "🧠 Generating competencies",
        "generate_training_plan": "📝 Generating training plan",
        "validate_plan":          "✅ Validating plan",
        "save_plan":              "💾 Saving to database",
    }

    print(f"  🤖 Orchestrator starting (model: {model})")

    for iteration in range(MAX_ITERATIONS):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=6000,
                messages=messages,
                tools=ORCHESTRATOR_TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            logger.error(f"Orchestrator LLM call failed at iteration {iteration + 1}: {e}")
            break

        choice  = response.choices[0]
        message = choice.message

        # ── Agent is calling tools ────────────────────────────────────────────
        if message.tool_calls:
            messages.append({
                "role":       "assistant",
                "content":    message.content,
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ],
            })

            for tc in message.tool_calls:
                tool_call_count += 1
                name = tc.function.name
                label = label_map.get(name, name)
                print(f"\n  [{tool_call_count}] {label}")

                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                result = _dispatch(name, args)

                # Keep session state up to date
                if name == "extract_role" and isinstance(result, dict) and "role" in result:
                    session["role_data"] = result
                    risk_indicators = result.get("risk_indicators", [])
                    # Seed session risks with inherent risk_indicators from the role text
                    session["risks"] = list(risk_indicators)
                    print(f"       → Role: '{result.get('role')}'")
                    if risk_indicators:
                        print(f"       → Inherent risks from role text ({len(risk_indicators)}):")
                        for ri in risk_indicators:
                            print(f"           • {ri[:100]}")
                    # Inject a highlighted note into the conversation so the agent
                    # definitely uses these risks in subsequent tool calls
                    if risk_indicators:
                        messages.append({
                            "role": "user",
                            "content": (
                                "[ignoring loop detection]\n"
                                f"Note: The following risk_indicators were extracted directly from "
                                f"the role description. Include ALL of them in risk_types for every "
                                f"subsequent tool call:\n"
                                + "\n".join(f"- {r}" for r in risk_indicators)
                            ),
                        })

                elif name == "search_compliance_docs" and isinstance(result, list):
                    print(f"       → {len(result)} chunks returned")

                elif name == "generate_competencies" and isinstance(result, dict):
                    session["competencies"] = result
                    print(f"       → {len(result.get('knowledge', []))} knowledge, "
                          f"{len(result.get('skills', []))} skills, "
                          f"{len(result.get('judgement', []))} judgement items")

                elif name == "generate_training_plan" and isinstance(result, dict):
                    session["training_plan"] = result
                    quarters = [q.get("quarter") for q in result.get("quarterly_plan", [])]
                    print(f"       → Quarters: {quarters}")

                elif name == "validate_plan" and isinstance(result, dict):
                    valid  = result.get("valid", False)
                    errors = result.get("errors", [])
                    status = "✅ VALID" if valid else f"❌ INVALID ({len(errors)} errors)"
                    print(f"       → {status}")
                    if errors:
                        for err in errors[:3]:
                            print(f"         • {err[:100]}")

                elif name == "save_plan" and isinstance(result, dict):
                    if result.get("success"):
                        session["plan_id"] = result.get("plan_id")
                        # Capture everything save_plan received — the full data set
                        session["risks"]         = args.get("risks", session.get("risks", []))
                        session["regulations"]   = args.get("regulations", session.get("regulations", []))
                        session["role_data"]     = args.get("role_data", session.get("role_data"))
                        session["competencies"]  = args.get("competencies", session.get("competencies"))
                        session["training_plan"] = args.get("training_plan", session.get("training_plan"))
                        print(f"       → plan_id: {session['plan_id']}")
                    else:
                        print(f"       → FAILED: {result.get('error')}")

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      "[ignoring loop detection]\n" + json.dumps(result, default=str),
                })

        # ── Agent finished — parse final output ───────────────────────────────
        elif message.content:
            elapsed = time.time() - start
            print(f"\n  ✅ Orchestrator complete ({tool_call_count} tool calls, {elapsed:.1f}s)")
            print(f"     Agent output: {message.content[:200]}")
            return _build_response(session, uploaded_text)

        else:
            logger.warning(f"Empty agent response at iteration {iteration + 1}")
            break

    logger.warning(f"Orchestrator hit max iterations — building response from partial state")
    return _build_response(session, uploaded_text)


# ---------------------------------------------------------------------------
# Build WorkflowResponse from accumulated session state
# ---------------------------------------------------------------------------

def _build_response(session: dict, uploaded_text: str) -> WorkflowResponse:
    from app.models.role_intelligence import RoleExtraction
    from app.models.competency import Competency
    from app.models.regulation import RegulationReference
    from app.models.training import TrainingPlan

    # ── Best path: load fully structured data from DB ─────────────────────────
    plan_id = session.get("plan_id")
    if plan_id:
        try:
            from app.services.workflow import get_plan_by_id
            db_response = get_plan_by_id(plan_id)
            if db_response and db_response.recommendations:
                logger.info(f"✅ Loaded {len(db_response.recommendations)} recommendations from DB")
                return db_response
        except Exception as e:
            logger.warning(f"DB load failed, falling back to session state: {e}")

    # ── Fallback: reconstruct from session state ──────────────────────────────
    logger.warning("Building response from session state (no DB load)")

    role_data_raw = session.get("role_data") or {}
    role_data = RoleExtraction(
        role=role_data_raw.get("role", "Unknown"),
        responsibilities=role_data_raw.get("responsibilities", []),
        compliance_exposure=role_data_raw.get("compliance_exposure", []),
        risk_indicators=role_data_raw.get("risk_indicators", []),
    )

    comp_raw = session.get("competencies") or {}
    competencies = Competency(
        knowledge=comp_raw.get("knowledge", []),
        skills=comp_raw.get("skills", []),
        judgement=comp_raw.get("judgement", []),
    )

    risks: list[str] = session.get("risks", [])

    regs_raw: list[dict] = session.get("regulations", [])
    try:
        regulations = [RegulationReference.model_validate(r) for r in regs_raw]
    except Exception:
        regulations = []

    recommendations: list[Recommendation] = []
    plan_raw = session.get("training_plan")
    if plan_raw:
        try:
            plan_obj = TrainingPlan.model_validate(plan_raw)
            recommendations = list(plan_obj.quarterly_plan)
        except Exception as e:
            logger.warning(f"Could not parse training plan: {e}")

    return WorkflowResponse(
        uploaded_text=uploaded_text,
        role_data=role_data,
        risks=risks,
        regulations=regulations,
        competencies=competencies,
        recommendations=recommendations,
        training_plan_id=plan_id,
    )
