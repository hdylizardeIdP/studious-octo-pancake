"""
Authentication dependencies for FastAPI endpoints
Validates Supabase JWT tokens
"""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import os
import logging
from functools import lru_cache
import httpx

logger = logging.getLogger(__name__)

security = HTTPBearer()


@lru_cache()
def get_supabase_jwt_secret() -> str:
    """
    Get Supabase JWT secret from environment.
    This should be the JWT secret from your Supabase project settings.
    """
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        logger.warning("SUPABASE_JWT_SECRET not set - authentication will fail")
        raise ValueError("SUPABASE_JWT_SECRET environment variable is required")
    return secret


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Verify Supabase JWT token and return decoded payload.

    This dependency can be used to protect endpoints:

    @router.post("/protected")
    async def protected_endpoint(user: dict = Depends(verify_supabase_token)):
        user_id = user["sub"]
        # ... your logic

    Raises:
        HTTPException: 401 if token is invalid or expired

    Returns:
        dict: Decoded JWT payload containing user information
    """
    token = credentials.credentials

    try:
        # Get JWT secret
        jwt_secret = get_supabase_jwt_secret()

        # Decode and verify the token
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase doesn't always use aud claim
        )

        # Verify the token has required fields
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Authenticated user: {payload.get('sub')}")
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication configuration error",
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False)
) -> Optional[dict]:
    """
    Optional authentication - returns user if token is valid, None otherwise.
    Does not raise an error if no token is provided.

    Useful for endpoints that have different behavior for authenticated vs anonymous users.
    """
    if not credentials:
        return None

    try:
        return await verify_supabase_token(credentials)
    except HTTPException:
        return None
