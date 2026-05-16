from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.db import DATABASE_URL, create_tables


router = APIRouter()


@router.post('/audit/init')
def initialize_audit_tables() -> dict[str, str]:
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='DATABASE_URL is not configured',
        )

    try:
        create_tables()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'Could not initialize audit tables: {exc}',
        ) from exc

    return {'status': 'ok'}
