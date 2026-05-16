from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.audit import router as audit_router
from app.routes.competencies import router as competencies_router
from app.routes.regulations import router as regulations_router
from app.routes.risk_mapping import router as risk_mapping_router
from app.routes.role_intelligence import router as role_intelligence_router
from app.routes.training import router as training_router
from app.routes.upload import router as upload_router
from app.routes.workflow import router as workflow_router
from app.routes.approval import router as approval_router

app = FastAPI(title='Vidda API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(upload_router)
app.include_router(role_intelligence_router)
app.include_router(risk_mapping_router)
app.include_router(regulations_router)
app.include_router(competencies_router)
app.include_router(training_router)
app.include_router(workflow_router)
app.include_router(audit_router)
app.include_router(approval_router)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
