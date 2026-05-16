# AI-Powered Compliance Training Generation Platform
## Technical Specification Document

Version: 1.0  
Project: Vidda Solutions Hackathon  
Goal: Explainable, Risk-Based, Audit-Ready Compliance Training Generation

---

# 1. Overview

The platform generates role-specific compliance training programs automatically using:

- Role descriptions
- Responsibilities
- Risk exposure
- AMLR obligations
- Competency requirements

The system produces:

- Quarterly training plans
- Explainable recommendations
- Regulation references
- Audit-ready outputs
- LMS-compatible exports

---

# 2. Business Objectives

The platform must:

1. Generate role-specific training plans
2. Map risks to training recommendations
3. Align recommendations with AMLR obligations
4. Provide explainability for every recommendation
5. Maintain auditability and traceability
6. Support human review workflows
7. Export training plans to LMS systems

---

# 3. Core Requirements

## Functional Requirements

### FR-1 Upload Role Documents

The system shall support:

- PDF upload
- DOCX upload
- Markdown upload
- Plain text input
- Multiple file upload

---

### FR-2 Role Extraction

The system shall extract:

- Role name
- Responsibilities
- Customer exposure
- Escalation responsibilities
- Compliance exposure
- Jurisdiction exposure

---

### FR-3 Risk Mapping

The system shall identify:

- AML risk
- Sanctions risk
- Fraud risk
- Documentation risk
- Escalation risk
- Beneficial ownership risk
- Jurisdictional risk

---

### FR-4 Regulation Mapping

The system shall map:

- AMLR obligations
- Risk-based obligations
- Training obligations
- Audit obligations

---

### FR-5 Competency Generation

The system shall generate:

- Knowledge competencies
- Skills competencies
- Judgement competencies

---

### FR-6 Training Plan Generation

The system shall generate:

- Quarterly training plans
- Learning objectives
- Behavioural outcomes
- Competency milestones

Structure:

- Q1 Foundation
- Q2 Application
- Q3 Deepening
- Q4 Embedding

---

### FR-7 Explainability

Every recommendation must contain:

- Role reference
- Risk reference
- AMLR reference
- Competency reference
- Human-readable explanation

---

### FR-8 Auditability

The system shall store:

- Uploaded documents
- Extracted role data
- Risk mappings
- Retrieved regulations
- Prompts
- LLM outputs
- References
- User approvals
- Timestamps

---

### FR-9 Human Review

The system shall support:

- Approve recommendation
- Reject recommendation
- Edit recommendation
- Add reviewer notes

---

### FR-10 LMS Export

The system shall export:

- JSON
- CSV

Future:
- SCORM
- xAPI

---

# 4. Non-Functional Requirements

## NFR-1 Explainability

Every recommendation must be traceable.

---

## NFR-2 Auditability

All outputs must be reproducible.

---

## NFR-3 Regulatory Grounding

The system must avoid hallucinated regulations.

---

## NFR-4 Performance

Initial generation target:
- Under 30 seconds

---

## NFR-5 Security

The system shall support:

- Role-based access
- Secure document upload
- Encrypted storage
- Audit logging

---

# 5. Architecture

```text
Frontend
   ↓
FastAPI Backend
   ↓
LangGraph Workflow Engine
   ↓
Role Intelligence Layer
   ↓
Risk Mapping Layer
   ↓
Regulation Retrieval Layer
   ↓
LLM Recommendation Engine
   ↓
Explainability Engine
   ↓
Audit Layer
   ↓
LMS Export Layer