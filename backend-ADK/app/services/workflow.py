from typing import TypedDict
import json
import logging

from google.adk.agents import Agent

from app.models.competency import Competency
from app.models.regulation import RegulationReference
from app.models.role_intelligence import RoleExtraction
from app.models.training import Recommendation, TrainingPlan, TrainingRecommendationRequest
from app.models.workflow import WorkflowResponse

from app.services.competency_engine import generate_competencies
from app.services.role_intelligence import extract_role_intelligence
from app.services.training_recommendation import generate_training_recommendations
from app.services.recommendation_validation import enforce_valid_training_plan
from app.db import SessionLocal
from app.db_models import RoleRecord, CompetencyRecord, TrainingPlanRecord, RecommendationRecord

from app.services.mcp_client import mcp_client, mcp_search_tool

logger = logging.getLogger(__name__)

class WorkflowState(TypedDict, total=False):
    uploaded_text: str
    role_data: dict
    risks: list
    regulations: list
    competencies: dict
    recommendations: list
    training_plan: dict
    training_plan_id: str
    feedback: str

# ---------------------------------------------------------
# WORKFLOW EXECUTION
# ---------------------------------------------------------

def run_training_workflow(uploaded_text: str) -> WorkflowResponse:
    """
    Training Workflow using LLM + RAG with PERFORMANCE OPTIMIZATIONS
    """
    import time
    workflow_start = time.time()
    
    # --- Input Validation ---
    if not uploaded_text or not uploaded_text.strip():
        raise ValueError("Input text cannot be empty")
    
    # Check minimum length (at least 20 characters for meaningful role description)
    if len(uploaded_text.strip()) < 20:
        raise ValueError("Input is too short. Please provide a detailed role description with responsibilities (minimum 20 characters)")
    
    # Check if input looks like a meaningful role description
    # It should have at least 3 words
    words = uploaded_text.strip().split()
    if len(words) < 3:
        raise ValueError("Input is too brief. Please provide a complete role description with responsibilities")
    
    # Check if input contains role-related keywords
    role_keywords = [
        'analyst', 'officer', 'manager', 'advisor', 'specialist', 'director', 
        'investigator', 'coordinator', 'supervisor', 'consultant', 'executive',
        'responsible', 'duties', 'tasks', 'role', 'position', 'job', 'work',
        'monitoring', 'compliance', 'kyc', 'aml', 'risk', 'due diligence',
        'customer', 'investigation', 'screening', 'reporting', 'oversight'
    ]
    
    text_lower = uploaded_text.lower()
    has_role_context = any(keyword in text_lower for keyword in role_keywords)
    
    if not has_role_context:
        raise ValueError(
            "Input does not appear to be a role description. "
            "Please provide information about a job role with responsibilities "
            "(e.g., 'KYC Analyst responsible for customer due diligence and screening')"
        )
    
    state: WorkflowState = {'uploaded_text': uploaded_text}
    
    # --- 1. Role Extraction (LLM) ---
    print(f"\n{'='*60}")
    print(f"[STAGE 1/6] 🔍 Role Extraction (LLM)...")
    print(f"{'='*60}")
    role_start = time.time()
    role_data = extract_role_intelligence(uploaded_text)
    state['role_data'] = role_data.model_dump()
    role_time = time.time() - role_start
    print(f"  ✅ Role: '{role_data.role}' ({role_time:.2f}s)")

    # --- 2 & 3. PARALLEL Risk + Regulation Extraction (RAG) ---
    print(f"\n{'='*60}")
    print(f"[STAGE 2/6] ⚡ Parallel RAG: Risks + Regulations...")
    print(f"{'='*60}")
    import re as _re
    import time

    rag_start = time.time()

    REG_QUERIES = [
        "AMLR Article 11 compliance officer obligations",
        "AMLR Article 20 customer due diligence requirements",
        "AMLR Article 33 training awareness staff",
        "AMLR Article 15 risk assessment monitoring",
        "AMLR Article 69 record keeping reporting",
    ]

    # --- Sequential RAG calls (reliable; parallel deadlocks inside anyio threads) ---
    print("  Fetching risks...")
    risks: list[str] = []
    try:
        raw = mcp_client.search_docs(query=f"compliance risks for {state['role_data'].get('role', '')}")
        for r in (raw if isinstance(raw, list) else []):
            t = r.get('text', '')
            t = (t[:150] + '...') if len(t) > 150 else t
            if '. ' in t:
                t = t.split('. ')[0] + '.'
            risks.append(t)
    except Exception as e:
        logger.error(f"Risk fetch failed: {e}")

    print(f"  Got {len(risks)} risks. Fetching regulations...")
    raw_reg_results: list[dict] = []
    for i, query in enumerate(REG_QUERIES, 1):
        print(f"  Reg {i}/{len(REG_QUERIES)}: {query[:50]}...")
        try:
            raw = mcp_client.search_docs(query=query)
            for r in (raw if isinstance(raw, list) else [])[:2]:
                text = r.get('text', '').strip()
                if not text:
                    continue
                nums = _re.findall(r'Article\s+(\d+)', text)
                article_num = nums[0] if nums else None
                if not article_num:
                    m = _re.search(r'Article\s+(\d+)', query)
                    article_num = m.group(1) if m else None
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                snippet = next(
                    (s for s in sentences if article_num and f'Article {article_num}' in s),
                    sentences[0] if sentences else text
                )[:200]
                raw_reg_results.append({
                    "article_num": article_num,
                    "article_label": f"Article {article_num}" if article_num else None,
                    "snippet": snippet,
                })
        except Exception as e:
            logger.warning(f"Regulation query failed: {e}")

    # Deduplicate
    seen_nums: set[str] = set()
    regs: list[dict] = []
    for item in raw_reg_results:
        if len(regs) >= 6:
            break
        num = item["article_num"]
        if num and num in seen_nums:
            continue
        label = item["article_label"] or f"AMLR Requirement {len(regs) + 1}"
        regs.append({"article": label, "title": "AMLR 2024/1624",
                     "requirements": [item["snippet"]], "keywords": [], "risk_types": []})
        if num:
            seen_nums.add(num)

    # Fallback
    for num, desc in [
        ("11", "Compliance manager obligations — appoint compliance manager responsible for AML/CFT adherence"),
        ("20", "Customer due diligence — verify customer identity and monitor business relationships"),
        ("33", "Staff training — ensure staff receive regular AML/CFT awareness training"),
        ("15", "Risk assessment — conduct and document business-wide risk assessments"),
        ("69", "Record keeping — retain CDD and transaction records for at least five years"),
    ]:
        if len(regs) >= 6:
            break
        if num not in seen_nums:
            seen_nums.add(num)
            regs.append({"article": f"Article {num}", "title": "AMLR 2024/1624",
                         "requirements": [desc], "keywords": [], "risk_types": []})

    rag_time = time.time() - rag_start
    print(f"  ✅ RAG done — {len(risks)} risks, {len(regs)} articles ({rag_time:.2f}s)")
    print(f"     Articles: {[r['article'] for r in regs]}")
    state['risks'] = risks
    state['regulations'] = regs

    # --- 4. Competency Generation ---
    print(f"\n{'='*60}")
    print(f"[STAGE 3/6] 🧠 Competency Generation (LLM)...")
    print(f"{'='*60}")
    comp_start = time.time()
    role_data_obj = RoleExtraction.model_validate(state['role_data'])
    regs_ref = [RegulationReference.model_validate(r) for r in state.get('regulations', [])]
    competencies = generate_competencies(
        role=role_data_obj.role,
        responsibilities=role_data_obj.responsibilities,
        risk_types=state.get('risks', []),
        regulations=regs_ref,
    )
    state['competencies'] = competencies.model_dump()
    comp_time = time.time() - comp_start
    print(f"  ✅ Competencies generated ({comp_time:.2f}s)")

    # --- 5. Training Plan Generation (LLM) ---
    print(f"\n{'='*60}")
    print(f"[STAGE 4/6] 📋 Training Plan Generation (LLM)...")
    print(f"  ⏳ This is the longest step — waiting on OpenRouter...")
    print(f"{'='*60}")
    training_start = time.time()
    training_request = TrainingRecommendationRequest(
        role=role_data_obj.role,
        responsibilities=role_data_obj.responsibilities,
        risk_types=state.get('risks', []),
        competencies=competencies,
        regulations=regs_ref,
    )
    training_plan = generate_training_recommendations(training_request)
    state['training_plan'] = training_plan.model_dump()
    state['recommendations'] = [rec.model_dump() for rec in training_plan.quarterly_plan]
    training_time = time.time() - training_start
    print(f"  ✅ Training plan: {len(training_plan.quarterly_plan)} quarters ({training_time:.2f}s)")
    
    # --- 6. Validation ---
    print(f"\n{'='*60}")
    print(f"[STAGE 5/6] ✔️  Validation...")
    print(f"{'='*60}")
    val_start = time.time()
    try:
        enforce_valid_training_plan(TrainingPlan.model_validate(state['training_plan']), training_request)
        val_time = time.time() - val_start
        print(f"  ✅ Validation passed ({val_time:.2f}s)")
    except ValueError as e:
        print(f"  ⚠️  Validation warning (continuing): {e}")
        val_time = time.time() - val_start
    
    # --- 7. Database Persistence ---
    print(f"\n{'='*60}")
    print(f"[STAGE 6/6] 💾 Saving to Database...")
    print(f"{'='*60}")
    db_start = time.time()
    state = persist_to_db(state)
    db_time = time.time() - db_start
    print(f"  ✅ Saved — Plan ID: {state.get('training_plan_id')} ({db_time:.2f}s)")
    
    # --- PERFORMANCE SUMMARY ---
    total_time = time.time() - workflow_start
    print(f"\n{'='*60}")
    print(f"🎯 WORKFLOW COMPLETE — Total: {total_time:.1f}s")
    print(f"   Role: {role_time:.1f}s | RAG: {rag_time:.1f}s | Comp: {comp_time:.1f}s | LLM: {training_time:.1f}s | Val: {val_time:.1f}s | DB: {db_time:.1f}s")
    print(f"{'='*60}\n")
    
    return WorkflowResponse(
        uploaded_text=state['uploaded_text'],
        role_data=role_data_obj,
        risks=state.get('risks', []),
        regulations=regs_ref,
        competencies=competencies,
        recommendations=[
            Recommendation.model_validate(recommendation)
            for recommendation in state.get('recommendations', [])
        ],
            training_plan_id=state.get('training_plan_id'),
        )

def persist_to_db(state: WorkflowState) -> WorkflowState:
    """
    Save training plan and all related data to database
    """
    if SessionLocal is None:
        return state

    with SessionLocal() as session:
        role_data = RoleExtraction.model_validate(state['role_data'])
        role_record = RoleRecord(
            name=role_data.role,
            responsibilities=role_data.responsibilities,
            compliance_exposure=role_data.compliance_exposure,
            risk_indicators=role_data.risk_indicators
        )
        session.add(role_record)
        session.flush()

        comp_data = Competency.model_validate(state['competencies'])
        comp_record = CompetencyRecord(
            role_id=role_record.id,
            knowledge=comp_data.knowledge,
            skills=comp_data.skills,
            judgement=comp_data.judgement
        )
        session.add(comp_record)
        session.flush()

        plan_record = TrainingPlanRecord(
            role_id=role_record.id,
            status='draft'
        )
        session.add(plan_record)
        session.flush()

        for rec_dict in state.get('recommendations', []):
            rec = Recommendation.model_validate(rec_dict)
            rec_record = RecommendationRecord(
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
                competency_reference=rec.competency_reference
            )
            session.add(rec_record)

        session.commit()
        state['training_plan_id'] = plan_record.id
        return state

def revise_training_plan(plan_id: str, feedback: str) -> bool:
    """
    Human-In-The-Loop feedback mechanism. 
    Regenerates the training plan with user feedback.
    """
    if SessionLocal is None:
        logger.error("Database not available")
        return False
        
    logger.info(f"Starting plan revision for plan_id: {plan_id}")
    logger.info(f"Feedback: {feedback}")
    
    with SessionLocal() as db_session:
        # Fetch the existing plan
        plan = db_session.query(TrainingPlanRecord).filter(TrainingPlanRecord.id == plan_id).first()
        if not plan:
            logger.error(f"Plan {plan_id} not found")
            return False
            
        # Fetch related data
        role = db_session.query(RoleRecord).filter(RoleRecord.id == plan.role_id).first()
        competencies = db_session.query(CompetencyRecord).filter(CompetencyRecord.role_id == plan.role_id).first()
        existing_recommendations = db_session.query(RecommendationRecord).filter(
            RecommendationRecord.training_plan_id == plan_id
        ).all()
        
        if not role or not competencies:
            logger.error("Role or competencies not found")
            return False
        
        # Build the training request with feedback
        logger.info("Reconstructing training request with feedback...")
        
        # Get regulations and risks from existing recommendations
        risks = list(set([rec.risk_reference for rec in existing_recommendations if rec.risk_reference]))
        
        # Build regulation references
        regulation_refs = []
        seen_articles = set()
        for rec in existing_recommendations:
            if rec.regulation_reference and rec.regulation_reference not in seen_articles:
                seen_articles.add(rec.regulation_reference)
                # Parse the regulation reference
                parts = rec.regulation_reference.split(':')
                article = parts[0].strip() if parts else "AMLR Article"
                regulation_refs.append(RegulationReference(
                    article=article,
                    title="AMLR 2024/1624",
                    requirements=[rec.regulation_reference],
                    keywords=risks,
                    risk_types=risks
                ))
        
        comp_obj = Competency(
            knowledge=competencies.knowledge,
            skills=competencies.skills,
            judgement=competencies.judgement
        )
        
        training_request = TrainingRecommendationRequest(
            role=role.name,
            responsibilities=role.responsibilities,
            risk_types=risks,
            competencies=comp_obj,
            regulations=regulation_refs,
        )
        
        # Generate NEW training plan with LLM using feedback
        logger.info("Regenerating training plan with feedback...")
        try:
            # Use the LLM to regenerate with feedback context
            from app.services.llm_client import create_llm_client, llm_model_name
            from app.prompts.training_generation import TRAINING_GENERATION_SYSTEM_PROMPT
            from app.services.recommendation_validation import build_evidence, REQUIRED_QUARTERS
            import json
            
            client = create_llm_client()
            model_name = llm_model_name()
            
            # Build payload with feedback
            payload = {
                'quarters': REQUIRED_QUARTERS,
                'evidence': build_evidence(training_request),
                'feedback': feedback,
                'instruction': f'Regenerate the training plan addressing this feedback: {feedback}. Ensure you use DIFFERENT regulation references for each quarter.'
            }
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {'role': 'system', 'content': TRAINING_GENERATION_SYSTEM_PROMPT},
                    {'role': 'user', 'content': json.dumps(payload, indent=2)},
                ],
                response_format={
                    'type': 'json_schema',
                    'json_schema': {
                        'name': 'training_plan',
                        'schema': TrainingPlan.model_json_schema(),
                        'strict': True,
                    },
                },
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError('LLM returned empty response')
            
            revised_plan = TrainingPlan.model_validate_json(content)
            logger.info(f"✅ Revised training plan generated with {len(revised_plan.quarterly_plan)} quarters")
            
            # Delete old recommendations
            for old_rec in existing_recommendations:
                db_session.delete(old_rec)
            
            # Save new recommendations
            for rec in revised_plan.quarterly_plan:
                rec_record = RecommendationRecord(
                    training_plan_id=plan.id,
                    role_id=role.id,
                    competency_id=competencies.id,
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
                )
                db_session.add(rec_record)
            
            # Update plan status
            plan.status = "revised"
            plan.reviewer_notes = feedback
            db_session.commit()
            
            logger.info(f"✅ Plan {plan_id} revised and saved to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revise training plan: {e}")
            import traceback
            traceback.print_exc()
            db_session.rollback()
            return False

def get_plan_by_id(plan_id: str) -> WorkflowResponse | None:
    """
    Fetch a training plan by ID and return it as WorkflowResponse
    """
    if SessionLocal is None:
        return None
    
    with SessionLocal() as db_session:
        plan = db_session.query(TrainingPlanRecord).filter(TrainingPlanRecord.id == plan_id).first()
        if not plan:
            return None
        
        role = db_session.query(RoleRecord).filter(RoleRecord.id == plan.role_id).first()
        competencies = db_session.query(CompetencyRecord).filter(CompetencyRecord.role_id == plan.role_id).first()
        recommendations = db_session.query(RecommendationRecord).filter(
            RecommendationRecord.training_plan_id == plan_id
        ).all()
        
        if not role or not competencies:
            return None
        
        # Reconstruct role data
        role_data = RoleExtraction(
            role=role.name,
            responsibilities=role.responsibilities,
            compliance_exposure=role.compliance_exposure,
            risk_indicators=role.risk_indicators
        )
        
        # Reconstruct competencies
        comp_obj = Competency(
            knowledge=competencies.knowledge,
            skills=competencies.skills,
            judgement=competencies.judgement
        )
        
        # Reconstruct recommendations
        recs = []
        for rec in recommendations:
            recs.append(Recommendation(
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
        
        # Extract risks and regulations from recommendations
        risks = list(set([rec.risk_reference for rec in recommendations if rec.risk_reference]))
        
        regulation_refs = []
        seen_articles = set()
        for rec in recommendations:
            if rec.regulation_reference and rec.regulation_reference not in seen_articles:
                seen_articles.add(rec.regulation_reference)
                parts = rec.regulation_reference.split(':')
                article = parts[0].strip() if parts else "AMLR Article"
                regulation_refs.append(RegulationReference(
                    article=article,
                    title="AMLR 2024/1624",
                    requirements=[rec.regulation_reference],
                    keywords=risks,
                    risk_types=risks
                ))
        
        return WorkflowResponse(
            uploaded_text="",  # Not stored in DB
            role_data=role_data,
            risks=risks,
            regulations=regulation_refs,
            competencies=comp_obj,
            recommendations=recs,
            training_plan_id=plan_id,
        )
