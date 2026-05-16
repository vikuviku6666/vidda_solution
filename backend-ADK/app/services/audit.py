from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal, create_tables
from app.db_models import AuditLogRecord


def audit_log(
    event_type: str,
    *,
    model_used: str | None = None,
    prompt: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    references: dict[str, Any] | None = None,
    uploaded_docs: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if SessionLocal is None:
        return

    try:
        create_tables()
        with SessionLocal() as session:
            session.add(
                AuditLogRecord(
                    event_type=event_type,
                    model_used=model_used,
                    prompt=prompt,
                    output=output,
                    references=references,
                    uploaded_docs=uploaded_docs,
                    metadata_json=metadata,
                )
            )
            session.commit()
    except SQLAlchemyError:
        return
