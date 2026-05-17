import re
from app.db import SessionLocal
from app.db_models import TrainingPlanRecord, RoleRecord, RecommendationRecord


def evaluate_plan(plan_id: str) -> dict:
    """
    Score a saved training plan across 5 dimensions (0-100 each).
    Returns per-dimension scores, messages, and an overall score.
    """
    if SessionLocal is None:
        return _error("Database not available")

    with SessionLocal() as db:
        plan = db.query(TrainingPlanRecord).filter(TrainingPlanRecord.id == plan_id).first()
        if not plan:
            return _error(f"Plan {plan_id} not found")

        role = db.query(RoleRecord).filter(RoleRecord.id == plan.role_id).first()
        recs = db.query(RecommendationRecord).filter(
            RecommendationRecord.training_plan_id == plan_id
        ).all()

    role_name = role.name if role else ""
    n = len(recs)

    # ── 1. Coverage ────────────────────────────────────────────────────────
    quarters_present = set(r.quarter for r in recs)
    required = {"Q1 Foundation", "Q2 Application", "Q3 Deepening", "Q4 Embedding"}
    quarters_hit = len(quarters_present & required)

    if n >= 8 and quarters_hit == 4:
        coverage_score = 100
        coverage_msg = f"{n} modules across all 4 quarters"
    elif n >= 4 and quarters_hit == 4:
        coverage_score = 75
        coverage_msg = f"{n} modules — consider adding more per quarter"
    elif quarters_hit >= 3:
        coverage_score = 50
        missing_q = required - quarters_present
        coverage_msg = f"Missing quarters: {', '.join(missing_q)}"
    else:
        coverage_score = max(0, quarters_hit * 20)
        coverage_msg = f"Only {quarters_hit}/4 quarters covered"

    # ── 2. Grounding ───────────────────────────────────────────────────────
    grounded = 0
    for r in recs:
        filled = sum([
            bool(r.role_reference and r.role_reference.strip()),
            bool(r.risk_reference and r.risk_reference.strip()),
            bool(r.regulation_reference and r.regulation_reference.strip()),
            bool(r.competency_reference and r.competency_reference.strip()),
        ])
        grounded += filled / 4  # partial credit per rec

    grounding_score = round((grounded / n) * 100) if n > 0 else 0
    grounding_msg = (
        f"All references populated" if grounding_score == 100
        else f"{grounding_score}% of reference fields populated"
    )

    # ── 3. Regulation Quality ──────────────────────────────────────────────
    article_pattern = re.compile(r"Article\s+\d+", re.IGNORECASE)
    reg_hits = sum(
        1 for r in recs
        if r.regulation_reference and article_pattern.search(r.regulation_reference)
    )
    regulation_score = round((reg_hits / n) * 100) if n > 0 else 0
    regulation_msg = (
        f"All modules cite valid AMLR articles" if regulation_score == 100
        else f"{reg_hits}/{n} modules cite a real AMLR article"
    )

    # ── 4. Role Specificity ────────────────────────────────────────────────
    aml_terms = {
        "aml", "kyc", "cdd", "edd", "pep", "sanctions", "compliance",
        "suspicious", "beneficial", "onboarding", "risk", "monitoring",
        "transaction", "screening", "reporting", "sar",
    }
    role_words = set(role_name.lower().split()) if role_name else set()

    specific = 0
    for r in recs:
        text = f"{r.module} {r.objective}".lower()
        words = set(re.findall(r"\b\w+\b", text))
        if words & aml_terms or words & role_words:
            specific += 1

    specificity_score = round((specific / n) * 100) if n > 0 else 0
    specificity_msg = (
        f"All modules are role-specific" if specificity_score == 100
        else f"{specific}/{n} modules contain role/AML-specific language"
    )

    # ── 5. Progression ─────────────────────────────────────────────────────
    quarter_order = ["Q1 Foundation", "Q2 Application", "Q3 Deepening", "Q4 Embedding"]
    modules_by_quarter = {q: [] for q in quarter_order}
    for r in recs:
        if r.quarter in modules_by_quarter:
            modules_by_quarter[r.quarter].append(r.module.lower() if r.module else "")

    # Check uniqueness across consecutive quarters
    all_module_names = [m for q in quarter_order for m in modules_by_quarter[q]]
    unique_ratio = len(set(all_module_names)) / len(all_module_names) if all_module_names else 1

    # Penalise if any module name appears in more than one quarter
    cross_quarter_dups = sum(
        1 for name in set(all_module_names)
        if sum(1 for q in quarter_order if name in modules_by_quarter[q]) > 1
    )

    progression_score = round(unique_ratio * 100) - (cross_quarter_dups * 10)
    progression_score = max(0, min(100, progression_score))
    progression_msg = (
        "All modules are distinct across quarters" if cross_quarter_dups == 0
        else f"{cross_quarter_dups} module name(s) repeated across quarters"
    )

    # ── Overall ────────────────────────────────────────────────────────────
    weights = {
        "coverage":    0.25,
        "grounding":   0.30,
        "regulation":  0.20,
        "specificity": 0.15,
        "progression": 0.10,
    }
    overall = round(
        coverage_score    * weights["coverage"]    +
        grounding_score   * weights["grounding"]   +
        regulation_score  * weights["regulation"]  +
        specificity_score * weights["specificity"] +
        progression_score * weights["progression"]
    )

    return {
        "plan_id": plan_id,
        "role":    role_name,
        "overall": overall,
        "dimensions": [
            {"name": "Coverage",          "score": coverage_score,    "message": coverage_msg,    "weight": 25},
            {"name": "Grounding",         "score": grounding_score,   "message": grounding_msg,   "weight": 30},
            {"name": "Regulation Quality","score": regulation_score,  "message": regulation_msg,  "weight": 20},
            {"name": "Role Specificity",  "score": specificity_score, "message": specificity_msg, "weight": 15},
            {"name": "Progression",       "score": progression_score, "message": progression_msg, "weight": 10},
        ],
    }


def _error(msg: str) -> dict:
    return {"plan_id": None, "role": "", "overall": 0, "error": msg, "dimensions": []}
