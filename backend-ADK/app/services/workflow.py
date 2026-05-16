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

from app.services.mcp_client import mcp_search_tool

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
    logger.info("Starting Role Extraction...")
    role_start = time.time()
    role_data = extract_role_intelligence(uploaded_text)
    state['role_data'] = role_data.model_dump()
    role_time = time.time() - role_start
    logger.info(f"✅ Role extracted: {role_data.role} ({role_time:.2f}s)")

    # --- 2 & 3. PARALLEL Risk + Regulation Extraction (RAG) ---
    logger.info("Starting PARALLEL RAG extraction (Risk + Regulations)...")
    import concurrent.futures
    import time
    
    parallel_start = time.time()
    
    def extract_risks_parallel(role_name: str):
        """Extract risks via RAG"""
        try:
            risks_raw = mcp_search_tool.func(query=f"compliance risks for {role_name}")
            risks = []
            for r in (risks_raw if isinstance(risks_raw, list) else []):
                risk_text = r.get('text', '')
                clean_risk = risk_text[:150] + '...' if len(risk_text) > 150 else risk_text
                if '. ' in clean_risk:
                    clean_risk = clean_risk.split('. ')[0] + '.'
                risks.append(clean_risk)
            return risks
        except Exception as e:
            logger.error(f"Risk extraction failed: {e}")
            return []
    
    def extract_regulations_parallel():
        """Extract regulations with OPTIMIZED queries (3 instead of 10)"""
        try:
            import re
            
            # OPTIMIZED: Only 3 broad queries instead of 10
            broad_queries = [
                "AMLR Article obligations requirements",
                "AMLR customer due diligence monitoring",
                "AMLR training record keeping"
            ]
            
            all_article_texts = {}
            seen_articles = set()
            
            for query in broad_queries:
                try:
                    regs_raw = mcp_search_tool.func(query=query)
                    # Get 3 results per query
                    for r in (regs_raw if isinstance(regs_raw, list) else [])[:3]:
                        raw_text = r.get('text', '')
                        article_matches = re.findall(r'Article\s+(\d+)', raw_text)
                        
                        for article_num in article_matches:
                            # OPTIMIZATION: Stop early when we have enough
                            if article_num not in seen_articles and len(all_article_texts) < 8:
                                sentences = raw_text.split('.')
                                relevant_sentence = next(
                                    (s.strip() for s in sentences if f'Article {article_num}' in s),
                                    sentences[0].strip() if sentences else ""
                                )
                                if relevant_sentence:
                                    all_article_texts[article_num] = relevant_sentence[:200]
                                    seen_articles.add(article_num)
                                    logger.info(f"Found Article {article_num} from RAG")
                except Exception as e:
                    logger.warning(f"Query '{query}' failed: {e}")
                    continue
            
            # Build regulation list
            regs = []
            for article_num, text in all_article_texts.items():
                regs.append({
                    "article": f"Article {article_num}",
                    "title": "AMLR 2024/1624",
                    "requirements": [text],
                    "keywords": [],
                    "risk_types": []
                })
            
            # Add fallback articles if needed
            if len(regs) < 4:
                logger.warning(f"Only found {len(regs)} articles from RAG, adding fallback")
                common_articles = [
                    ("4", "Customer due diligence requirements"),
                    ("8", "Risk assessment obligations"),
                    ("13", "Training and awareness requirements"),
                    ("16", "Transaction monitoring requirements"),
                ]
                
                for article_num, description in common_articles:
                    if article_num not in seen_articles and len(regs) < 6:
                        seen_articles.add(article_num)
                        regs.append({
                            "article": f"Article {article_num}",
                            "title": "AMLR 2024/1624",
                            "requirements": [description],
                            "keywords": [description],
                            "risk_types": []
                        })
            
            return regs
        except Exception as e:
            logger.error(f"Regulation extraction failed: {e}")
            return []
    
    # PARALLEL EXECUTION - Run both simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_risks = executor.submit(extract_risks_parallel, state['role_data'].get('role', ''))
        future_regs = executor.submit(extract_regulations_parallel)
        
        # Wait for both to complete
        risks = future_risks.result()
        regs = future_regs.result()
    
    parallel_time = time.time() - parallel_start
    logger.info(f"⚡ PARALLEL extraction completed in {parallel_time:.2f}s")
    
    state['risks'] = risks
    state['regulations'] = regs
    
    logger.info(f"✅ Risks: {len(risks)}, Articles: {[r['article'] for r in regs]}")

    # --- 4. Competency Generation ---
    logger.info("Generating competencies...")
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
    logger.info(f"✅ Competencies generated ({comp_time:.2f}s)")

    # --- 5. Training Plan Generation (LLM) ---
    logger.info("Generating training plan with LLM...")
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
    logger.info(f"✅ Training plan generated with {len(training_plan.quarterly_plan)} quarters ({training_time:.2f}s)")
    
    # --- 6. Validation ---
    logger.info("Validating training plan...")
    val_start = time.time()
    enforce_valid_training_plan(TrainingPlan.model_validate(state['training_plan']), training_request)
    val_time = time.time() - val_start
    logger.info(f"✅ Validation passed ({val_time:.2f}s)")
    
    # --- 7. Database Persistence ---
    logger.info("Saving to database...")
    db_start = time.time()
    state = persist_to_db(state)
    db_time = time.time() - db_start
    logger.info(f"✅ Saved to database with plan ID: {state.get('training_plan_id')} ({db_time:.2f}s)")
    
    # --- PERFORMANCE SUMMARY ---
    total_time = time.time() - workflow_start
    logger.info(f"🎯 TOTAL WORKFLOW TIME: {total_time:.2f}s")
    logger.info(f"   └─ Role: {role_time:.1f}s, RAG: {parallel_time:.1f}s, Comp: {comp_time:.1f}s, Training: {training_time:.1f}s, Val: {val_time:.1f}s, DB: {db_time:.1f}s")
    
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
