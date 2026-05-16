from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile

from app.services.audit import audit_log


ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.md', '.txt'}

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


async def ingest_upload(file: UploadFile) -> dict:
    filename = file.filename or ''
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f'Unsupported file type. Allowed extensions: {allowed}')

    with TemporaryDirectory(prefix='vidda-upload-') as temp_dir:
        temp_path = Path(temp_dir) / _safe_filename(filename, extension)
        contents = await file.read()

        if not contents:
            raise ValueError('Uploaded file is empty')

        temp_path.write_bytes(contents)
        plain_text = _extract_text(temp_path, extension)

    if not plain_text.strip():
        raise ValueError('No text could be extracted from the uploaded file')

    chunks = _split_text(plain_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

    result = {
        'filename': filename,
        'content_type': file.content_type,
        'text': plain_text,
        'text_length': len(plain_text),
        'chunk_size': CHUNK_SIZE,
        'chunk_overlap': CHUNK_OVERLAP,
        'chunk_count': len(chunks),
        'chunks': [
            {'index': i, 'text': chunk, 'metadata': {'source': filename}}
            for i, chunk in enumerate(chunks)
        ],
    }

    audit_log(
        'document_uploaded',
        uploaded_docs={
            'filename': filename,
            'content_type': file.content_type,
            'extension': extension,
            'extracted_text': plain_text,
            'text_length': len(plain_text),
            'chunk_count': len(chunks),
            'chunk_size': CHUNK_SIZE,
            'chunk_overlap': CHUNK_OVERLAP,
        },
        output={
            'text_length': len(plain_text),
            'chunk_count': len(chunks),
        },
    )

    return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_text(path: Path, extension: str) -> str:
    """Extract plain text from a file using lightweight, dependency-minimal libs."""
    if extension == '.pdf':
        return _read_pdf(path)
    if extension == '.docx':
        return _read_docx(path)
    # .txt and .md — plain UTF-8
    return path.read_text(encoding='utf-8', errors='replace')


def _read_pdf(path: Path) -> str:
    try:
        import pypdf  # already a direct dep
        reader = pypdf.PdfReader(str(path))
        pages = [page.extract_text() or '' for page in reader.pages]
        return '\n\n'.join(pages)
    except Exception as exc:
        raise ValueError(f'Could not read PDF: {exc}') from exc


def _read_docx(path: Path) -> str:
    try:
        import docx  # python-docx
        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n\n'.join(paragraphs)
    except Exception as exc:
        raise ValueError(f'Could not read DOCX: {exc}') from exc


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Simple character-level sliding-window splitter (no LangChain required)."""
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def _safe_filename(filename: str, extension: str) -> str:
    stem = Path(filename).stem or 'upload'
    safe_stem = ''.join(
        c if c.isalnum() or c in {'-', '_'} else '_'
        for c in stem
    ).strip('_')
    return f'{safe_stem or "upload"}{extension}'
