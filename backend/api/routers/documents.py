from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import tempfile
import os

from services.document_parser import DocumentParser
from services.item_extractor import ItemExtractor

router = APIRouter()

document_parser = DocumentParser()
item_extractor = ItemExtractor()

@router.post("/parse")
async def parse_document(
    file: UploadFile = File(...),
    list_id: Optional[str] = Form(None)
):
    """
    Parse a document (txt, docx, pdf, or image) and extract grocery items
    """
    try:
        # Validate file type
        allowed_types = [
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/jpg"
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
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

            return {
                "success": True,
                "filename": file.filename,
                "extracted_text": text,
                "items": items,
                "count": len(items)
            }

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.post("/extract-text")
async def extract_text_only(file: UploadFile = File(...)):
    """
    Extract raw text from a document without item parsing
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
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

            return {
                "success": True,
                "text": text
            }

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
