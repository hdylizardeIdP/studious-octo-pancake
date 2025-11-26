"""
Application configuration and environment variable validation
"""
import os
import sys
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All required variables are validated at startup.
    """

    # Supabase Configuration
    supabase_url: str = Field(
        ...,
        description="Supabase project URL",
        env="SUPABASE_URL"
    )

    supabase_key: str = Field(
        ...,
        description="Supabase service role key",
        env="SUPABASE_KEY"
    )

    supabase_jwt_secret: str = Field(
        ...,
        description="Supabase JWT secret for token verification",
        env="SUPABASE_JWT_SECRET"
    )

    # CORS Configuration
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
        env="ALLOWED_ORIGINS"
    )

    # Optional Configuration
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)",
        env="ENVIRONMENT"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level",
        env="LOG_LEVEL"
    )

    @validator("supabase_url")
    def validate_supabase_url(cls, v):
        """Validate Supabase URL format"""
        if not v.startswith("http"):
            raise ValueError("SUPABASE_URL must be a valid HTTP(S) URL")
        if "supabase.co" not in v and "localhost" not in v:
            logger.warning(f"SUPABASE_URL does not appear to be a valid Supabase URL: {v}")
        return v

    @validator("supabase_key")
    def validate_supabase_key(cls, v):
        """Validate Supabase key format"""
        if len(v) < 20:
            raise ValueError("SUPABASE_KEY appears to be invalid (too short)")
        return v

    @validator("supabase_jwt_secret")
    def validate_jwt_secret(cls, v):
        """Validate JWT secret format"""
        if len(v) < 32:
            raise ValueError("SUPABASE_JWT_SECRET appears to be invalid (too short)")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper

    def get_origins_list(self) -> list[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_settings() -> Settings:
    """
    Load and validate application settings.
    Exits the application if required environment variables are missing.
    """
    try:
        settings = Settings()
        logger.info("✓ Environment variables validated successfully")
        logger.info(f"  Environment: {settings.environment}")
        logger.info(f"  Log Level: {settings.log_level}")
        logger.info(f"  Supabase URL: {settings.supabase_url}")
        logger.info(f"  CORS Origins: {settings.get_origins_list()}")
        return settings
    except Exception as e:
        logger.error("=" * 80)
        logger.error("CONFIGURATION ERROR: Required environment variables are missing or invalid")
        logger.error("=" * 80)
        logger.error(f"\nError: {str(e)}\n")
        logger.error("Please ensure the following environment variables are set:")
        logger.error("  - SUPABASE_URL (required)")
        logger.error("  - SUPABASE_KEY (required)")
        logger.error("  - SUPABASE_JWT_SECRET (required)")
        logger.error("  - ALLOWED_ORIGINS (optional, defaults to localhost)")
        logger.error("\nYou can set these in a .env file in the backend directory")
        logger.error("See .env.example for a template\n")
        logger.error("=" * 80)
        sys.exit(1)


def validate_environment():
    """
    Validate environment configuration at startup.
    This function is called when the application starts.
    """
    logger.info("Validating environment configuration...")
    settings = load_settings()

    # Additional runtime checks
    if settings.environment == "production":
        # Production-specific validation
        if "localhost" in settings.supabase_url:
            logger.warning("⚠ WARNING: Running in production with localhost Supabase URL")

        if "localhost" in settings.allowed_origins:
            logger.warning("⚠ WARNING: CORS allows localhost origins in production")

    return settings


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    If not initialized, validate and load settings.
    """
    global settings
    if settings is None:
        settings = validate_environment()
    return settings
