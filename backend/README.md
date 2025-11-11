# Grocery List Backend API

Python FastAPI backend for document processing and item extraction.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (for image processing):
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`
   - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

4. Download spaCy model:
```bash
python -m spacy download en_core_web_sm
```

5. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

## Run Development Server

```bash
uvicorn api.main:app --reload --port 8000
```

API will be available at http://localhost:8000
Documentation at http://localhost:8000/docs

## Endpoints

### POST /api/documents/parse
Parse document and extract grocery items

**Supported formats:**
- Plain text (.txt)
- Microsoft Word (.docx)
- PDF (.pdf)
- Images (.jpg, .png) - requires Tesseract OCR

### POST /api/documents/extract-text
Extract raw text without item parsing

## Deployment

For serverless deployment (Vercel, AWS Lambda), use the FastAPI app with a serverless adapter.
