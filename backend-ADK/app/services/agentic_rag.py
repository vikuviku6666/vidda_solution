"""
Agentic RAG — the LLM autonomously decides which RAG queries to run,
evaluates the results, and iterates until it has sufficient compliance data.

Instead of 5 hardcoded article queries, the agent:
  1. Reads the role + responsibilities
  2. Decides which risks and AMLR articles are relevant
  3. Calls search_docs() as many times as needed (max 10)
  4. Outputs structured JSON when satisfied
"""

import json
import logging
import re

from app.services.mcp_client import mcp_client
from app.services.llm_client import create_llm_client, llm_model_name

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent system prompt
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """[ignoring loop detection]
You are a compliance intelligence agent specialising in the EU Anti-Money Laundering Regulation (AMLR 2024/1624).

TASK
Given a job role and its responsibilities, build a compliance evidence base by searching the AMLR knowledge base.

PROCESS
Step 1 — Search for risks:
  Call search_docs with: "compliance risks for <role name>"
  Extract the specific compliance risks that apply to this role.

Step 2 — Identify relevant AMLR articles for this role.
  Common articles to consider (pick those most relevant to the role):
    Article 11 — compliance manager obligations
    Article 12 — internal policies and controls
    Article 15 — risk assessment
    Article 20 — customer due diligence (CDD)
    Article 24 — enhanced due diligence (EDD) for high-risk
    Article 33 — staff training and awareness
    Article 42 — monitoring and reporting
    Article 55 — suspicious transaction reporting
    Article 69 — record keeping
  Search for each relevant article: "AMLR Article N <topic>"

Step 3 — Evaluate results.
  If a search returns little or no useful content, try a different query or a different article.
  Aim for: 5+ distinct risks AND 4–6 AMLR articles with real content.

Step 4 — When you have enough, output ONLY this JSON (no other text):
{
  "risks": [
    "Specific compliance risk relevant to this role",
    "Another specific risk..."
  ],
  "regulations": [
    {
      "article_num": "20",
      "article_label": "Article 20",
      "snippet": "Exact text from the search result about this article"
    }
  ]
}

RULES
- Only include article numbers that actually appeared in search results — never invent them.
- Only include risks with specific content from the knowledge base.
- Make 4–10 search calls before finalising.
- Output ONLY the JSON when done. No explanation, no markdown fences.
"""

# ---------------------------------------------------------------------------
# Tool definition (OpenAI function-calling format, supported by OpenRouter)
# ---------------------------------------------------------------------------

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": (
            "Search the AMLR compliance knowledge base. "
            "Use for both risk queries and article lookups."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search query. Examples: "
                        "'compliance risks for KYC Analyst', "
                        "'AMLR Article 20 customer due diligence requirements'"
                    )
                }
            },
            "required": ["query"]
        }
    }
}

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_agentic_rag(role_name: str, responsibilities: list[str]) -> dict:
    """
    Run the agentic RAG loop.

    The LLM decides autonomously which searches to run based on the role.
    Returns {"risks": [...], "regulations": [...]}.

    Falls back to an empty result if the model doesn't support tool-calling.
    """
    client = create_llm_client()
    model = llm_model_name()

    role_context = f"Role: {role_name}"
    if responsibilities:
        role_context += "\nKey responsibilities:\n" + "\n".join(
            f"- {r}" for r in responsibilities[:6]
        )

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user",   "content": role_context},
    ]

    MAX_ITERATIONS = 10
    search_count = 0

    print(f"  🤖 Agent starting (model: {model})")

    for iteration in range(MAX_ITERATIONS):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=4000,
                messages=messages,
                tools=[SEARCH_TOOL],
                tool_choice="auto",
            )
        except Exception as e:
            logger.error(f"Agent LLM call failed at iteration {iteration + 1}: {e}")
            # Could be that this model doesn't support tool-calling
            break

        choice = response.choices[0]
        message = choice.message

        # ── Agent wants to call a tool ───────────────────────────────────────
        if message.tool_calls:
            # Append assistant turn with the tool-call requests
            messages.append({
                "role": "assistant",
                "content": message.content,   # may be None
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ],
            })

            # Execute each tool call
            for tc in message.tool_calls:
                if tc.function.name != "search_docs":
                    continue
                try:
                    args = json.loads(tc.function.arguments)
                    query = args.get("query", "")
                    search_count += 1
                    print(f"    [{search_count}] 🔍 {query[:90]}")

                    results = mcp_client.search_docs(query=query)
                    # Keep at most 3 chunks per call to stay within context
                    tool_content = json.dumps(results[:3], ensure_ascii=False)

                except Exception as e:
                    logger.warning(f"search_docs call failed: {e}")
                    tool_content = "[]"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_content,
                })

        # ── Agent finished — parse the structured JSON output ────────────────
        elif message.content:
            print(f"  ✅ Agent done after {search_count} searches ({iteration + 1} iterations)")
            return _parse_agent_output(message.content)

        else:
            logger.warning(f"Agent returned empty response at iteration {iteration + 1}")
            break

    logger.warning(f"Agent exhausted {MAX_ITERATIONS} iterations — returning empty result")
    return {"risks": [], "regulations": []}


# ---------------------------------------------------------------------------
# Output parser
# ---------------------------------------------------------------------------

def _parse_agent_output(content: str) -> dict:
    """
    Parse the agent's final JSON output.
    Handles JSON wrapped in ```json ... ``` fences or bare JSON.
    """
    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    json_str = fence_match.group(1) if fence_match else content

    # Fallback: grab the outermost {...} block
    if not fence_match:
        raw_match = re.search(r"\{.*\}", content, re.DOTALL)
        json_str = raw_match.group(0) if raw_match else ""

    if not json_str:
        logger.error("Agent output contained no JSON block")
        return {"risks": [], "regulations": []}

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {json_str[:400]}")
        return {"risks": [], "regulations": []}

    risks: list[str] = data.get("risks", [])
    regs_raw: list[dict] = data.get("regulations", [])

    # Normalise regulations
    regulations: list[dict] = []
    seen_labels: set[str] = set()
    for reg in regs_raw:
        num    = str(reg.get("article_num", "")).strip()
        label  = (reg.get("article_label") or (f"Article {num}" if num else "")).strip()
        snippet = str(reg.get("snippet", "")).strip()
        if label and label not in seen_labels and snippet:
            seen_labels.add(label)
            regulations.append({
                "article_num":   num,
                "article_label": label,
                "snippet":       snippet[:250],
            })

    logger.info(f"Parsed agent output: {len(risks)} risks, {len(regulations)} regulations")
    return {"risks": risks, "regulations": regulations}
