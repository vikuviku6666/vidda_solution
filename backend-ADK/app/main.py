import asyncio
import contextlib
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

from app.routes.audit import router as audit_router
from app.routes.competencies import router as competencies_router
from app.routes.regulations import router as regulations_router
from app.routes.risk_mapping import router as risk_mapping_router
from app.routes.role_intelligence import router as role_intelligence_router
from app.routes.training import router as training_router
from app.routes.upload import router as upload_router
from app.routes.workflow import router as workflow_router
from app.routes.approval import router as approval_router

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle manager."""
    # --- Startup ---
    from app.db import create_tables
    try:
        create_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as exc:
        logger.warning(f"DB table creation skipped: {exc}")

    try:
        yield
    except asyncio.CancelledError:
        # Suppress the noisy CancelledError that uvicorn raises during Ctrl+C shutdown.
        # The server has already stopped accepting connections at this point.
        pass
    finally:
        # --- Shutdown ---
        logger.info("Vidda API shutting down cleanly.")


app = FastAPI(title='Vidda API', lifespan=lifespan)

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
