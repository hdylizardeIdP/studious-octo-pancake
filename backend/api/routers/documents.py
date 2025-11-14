from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request, Depends
from typing import List, Optional
import tempfile
import os
import magic
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.document_parser import DocumentParser
from services.item_extractor import ItemExtractor
from api.dependencies.auth import verify_supabase_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

document_parser = DocumentParser()
item_extractor = ItemExtractor()

# Rate limiter for document endpoints
limiter = Limiter(key_func=get_remote_address)

# Security: File upload limits (10MB max)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Allowed MIME types and their magic byte signatures
ALLOWED_MIME_TYPES = {
    "text/plain": [b""],  # Text files can start with anything
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK"],  # ZIP-based
    "application/pdf": [b"%PDF"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG"],
}

def validate_file_content(content: bytes, declared_mime: str) -> bool:
    """
    Validate file content using magic bytes to prevent content-type spoofing
    """
    try:
        # Use python-magic to detect actual MIME type
        mime = magic.from_buffer(content, mime=True)

        # For text files, be more lenient
        if declared_mime == "text/plain" and mime.startswith("text/"):
            return True

        # For DOCX files (which are ZIP files)
        if declared_mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return mime in ["application/zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

        # For other types, require exact match or common variations
        if declared_mime == "application/pdf":
            return mime == "application/pdf"

        if declared_mime in ["image/jpeg", "image/jpg"]:
            return mime in ["image/jpeg", "image/jpg"]

        if declared_mime == "image/png":
            return mime == "image/png"

        return False
    except Exception:
        return False

@router.post("/parse")
@limiter.limit("10/minute")
async def parse_document(
    request: Request,
    file: UploadFile = File(...),
    list_id: Optional[str] = Form(None),
    user: dict = Depends(verify_supabase_token)
):
    """
    Parse a document (txt, docx, pdf, or image) and extract grocery items

    Authentication: Required (Bearer token)
    Rate limit: 10 requests per minute per IP
    """
    user_id = user.get("sub")
    logger.info(f"Document parse request from user {user_id}, filename: {file.filename}")

    try:
        # Validate file type
        allowed_types = list(ALLOWED_MIME_TYPES.keys()) + ["image/jpg"]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            )

        # Read file content with size limit
        content = bytearray()
        chunk_size = 1024 * 1024  # 1MB chunks
        total_size = 0

        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="File size exceeds maximum limit of 10MB"
                )
            content.extend(chunk)

        content = bytes(content)

        # Validate file content using magic bytes
        if not validate_file_content(content, file.content_type):
            raise HTTPException(
                status_code=400,
                detail="File content does not match declared type"
            )

        # Save uploaded file temporarily and ensure cleanup
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Parse document based on type
            text = None

            if file.content_type == "text/plain":
                text = document_parser.parse_text(tmp_path)
            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = document_parser.parse_docx(tmp_path)
            elif file.content_type == "application/pdf":
                text = document_parser.parse_pdf(tmp_path)
            elif file.content_type in ["image/jpeg", "image/png", "image/jpg"]:
                text = document_parser.parse_image(tmp_path)

            if not text:
                raise HTTPException(status_code=400, detail="Could not extract text from document")

            # Extract grocery items
            items = item_extractor.extract_items(text)

            logger.info(f"Successfully parsed document for user {user_id}, extracted {len(items)} items")

            return {
                "success": True,
                "filename": file.filename,
                "extracted_text": text,
                "items": items,
                "count": len(items),
                "user_id": user_id
            }

        finally:
            # Clean up temp file
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        # Log the detailed error for debugging
        logger.error(f"Error processing document '{file.filename}': {str(e)}", exc_info=True)
        # Return sanitized error message to user
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the document. Please try again or contact support."
        )

@router.post("/extract-text")
@limiter.limit("10/minute")
async def extract_text_only(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(verify_supabase_token)
):
    """
    Extract raw text from a document without item parsing

    Authentication: Required (Bearer token)
    Rate limit: 10 requests per minute per IP
    """
    user_id = user.get("sub")
    logger.info(f"Text extraction request from user {user_id}, filename: {file.filename}")

    try:
        # Validate file type
        allowed_types = list(ALLOWED_MIME_TYPES.keys()) + ["image/jpg"]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            )

        # Read file content with size limit
        content = bytearray()
        chunk_size = 1024 * 1024  # 1MB chunks
        total_size = 0

        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="File size exceeds maximum limit of 10MB"
                )
            content.extend(chunk)

        content = bytes(content)

        # Validate file content using magic bytes
        if not validate_file_content(content, file.content_type):
            raise HTTPException(
                status_code=400,
                detail="File content does not match declared type"
            )

        # Save uploaded file temporarily and ensure cleanup
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            text = None

            if file.content_type == "text/plain":
                text = document_parser.parse_text(tmp_path)
            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = document_parser.parse_docx(tmp_path)
            elif file.content_type == "application/pdf":
                text = document_parser.parse_pdf(tmp_path)
            elif file.content_type in ["image/jpeg", "image/png", "image/jpg"]:
                text = document_parser.parse_image(tmp_path)

            if not text:
                raise HTTPException(status_code=400, detail="Could not extract text")

            logger.info(f"Successfully extracted text for user {user_id}")

            return {
                "success": True,
                "text": text,
                "user_id": user_id
            }

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        # Log the detailed error for debugging
        logger.error(f"Error extracting text from '{file.filename}': {str(e)}", exc_info=True)
        # Return sanitized error message to user
        raise HTTPException(
            status_code=500,
            detail="An error occurred while extracting text. Please try again or contact support."
        )
