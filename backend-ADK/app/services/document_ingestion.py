from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.audit import audit_log


ALLOWED_EXTENSIONS = {
    '.pdf': PyPDFLoader,
    '.docx': Docx2txtLoader,
    '.md': TextLoader,
    '.txt': TextLoader,
}

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


async def ingest_upload(file: UploadFile) -> dict:
    filename = file.filename or ''
    extension = Path(filename).suffix.lower()

    loader_class = ALLOWED_EXTENSIONS.get(extension)
    if loader_class is None:
        allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f'Unsupported file type. Allowed extensions: {allowed}')

    with TemporaryDirectory(prefix='vidda-upload-') as temp_dir:
        temp_path = Path(temp_dir) / _safe_filename(filename, extension)
        contents = await file.read()

        if not contents:
            raise ValueError('Uploaded file is empty')

        temp_path.write_bytes(contents)

        documents = loader_class(str(temp_path)).load()
        for document in documents:
            document.metadata['source'] = filename

        plain_text = '\n\n'.join(document.page_content for document in documents)

        if not plain_text.strip():
            raise ValueError('No text could be extracted from the uploaded file')

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(documents)

    result = {
        'filename': filename,
        'content_type': file.content_type,
        'text': plain_text,
        'text_length': len(plain_text),
        'chunk_size': CHUNK_SIZE,
        'chunk_overlap': CHUNK_OVERLAP,
        'chunk_count': len(chunks),
        'chunks': [
            {
                'index': index,
                'text': chunk.page_content,
                'metadata': chunk.metadata,
            }
            for index, chunk in enumerate(chunks)
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


def _safe_filename(filename: str, extension: str) -> str:
    stem = Path(filename).stem or 'upload'
    safe_stem = ''.join(
        character if character.isalnum() or character in {'-', '_'} else '_'
        for character in stem
    ).strip('_')

    return f'{safe_stem or "upload"}{extension}'
