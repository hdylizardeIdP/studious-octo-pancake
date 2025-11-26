from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List
import logging
from dotenv import load_dotenv

from api.routers import documents
from services.document_parser import DocumentParser
from services.item_extractor import ItemExtractor
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate and load settings at startup
logger.info("Starting Grocery List API...")
settings = get_settings()
logger.setLevel(settings.log_level)

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

app = FastAPI(
    title="Grocery List API",
    description="Document processing API for grocery lists",
    version="1.0.0"
)

# Add rate limiting to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration - restricted to specific methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    return {
        "message": "Grocery List API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
@limiter.limit("60/minute")
async def health(request: Request):
    return {
        "status": "healthy",
        "environment": settings.environment
    }


@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 80)
    logger.info("Grocery List API started successfully!")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Documentation: http://localhost:8000/docs")
    logger.info("=" * 80)
