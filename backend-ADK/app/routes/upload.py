from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.document_ingestion import ingest_upload


router = APIRouter()


@router.post('/upload')
async def upload_document(file: UploadFile = File(...)) -> dict:
    try:
        result = await ingest_upload(file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return result
