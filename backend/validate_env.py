#!/usr/bin/env python3
"""
Environment validation script
Run this to verify your .env file is configured correctly before starting the application
"""
import sys
from dotenv import load_dotenv
from config import load_settings

def main():
    """Validate environment configuration"""
    print("\n" + "=" * 80)
    print("Environment Configuration Validator")
    print("=" * 80 + "\n")

    # Load .env file
    print("Loading .env file...")
    load_dotenv()

    # Attempt to load and validate settings
    print("Validating environment variables...\n")
    settings = load_settings()

    # If we get here, validation succeeded
    print("\n" + "=" * 80)
    print("✓ SUCCESS: All environment variables are valid!")
    print("=" * 80 + "\n")
    print("Configuration summary:")
    print(f"  Environment: {settings.environment}")
    print(f"  Log Level: {settings.log_level}")
    print(f"  Supabase URL: {settings.supabase_url}")
    print(f"  CORS Origins: {', '.join(settings.get_origins_list())}")
    print("\nYou can now start the application with:")
    print("  uvicorn api.main:app --host 0.0.0.0 --port 8000\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
